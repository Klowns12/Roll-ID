from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QTabWidget, QFormLayout, QComboBox, QDateEdit, QDoubleSpinBox
)
from PySide6.QtCore import Qt, QDate, Signal as pyqtSignal, QObject, QTimer
from PySide6.QtGui import QPixmap
from http.server import HTTPServer, BaseHTTPRequestHandler


from io import BytesIO
import json
from datetime import datetime

import os

import qrcode

from http.server import HTTPServer, BaseHTTPRequestHandler

import sys
import pandas as pd

from utils.mobile_scan_service.mobile_connection_server import MobileConnectionServer


sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.label_generator import LabelGenerator
from utils.roll_id_generator import RollIDGenerator
from utils.master_suppliers_manager import MasterSuppliersManager
from storage import Roll






class ScanTab(QWidget):
    scan_received = pyqtSignal(dict)
    refresh_reports = pyqtSignal()
    
    def __init__(self, storage):
        super().__init__()
        self.storage = storage
        self.mobile_server = None
        self.label_generator = LabelGenerator()
        
        # Initialize Roll ID Generator
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
        self.roll_id_generator = RollIDGenerator(data_dir)
        
        # Initialize Master Suppliers Manager
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        master_data_path = os.path.join(root_dir, "MasterDATA.csv")
        suppliers_path = os.path.join(root_dir, "Suppliers.csv")
        dispatch_path = os.path.join(root_dir, "Master_Dispatch.csv")
        db_path = os.path.join(root_dir, "data", "storage.db")
        self.suppliers_manager = MasterSuppliersManager(master_data_path, suppliers_path, dispatch_path, db_path)
        
        self.setup_ui()
        
        # Connect signals
        self.scan_received.connect(self.on_scan_received)
        
        # Initialize mobile server
        self.init_mobile_server()
    
    def init_mobile_server(self):
        if self.mobile_server:
            try:
                self.mobile_server.stop()
                self.mobile_server.deleteLater()
            except:
                pass


        
        
        self.mobile_server = MobileConnectionServer()
        self.mobile_server.scan_received.connect(self.on_scan_received)
        self.mobile_server.start()
    
    def closeEvent(self, event):
        if self.mobile_server:
            try:
                self.mobile_server.stop()
                self.mobile_server.deleteLater()
            except:
                pass
        super().closeEvent(event)
    
    def setup_ui(self):
        """Set up the Scan QR tab UI"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Create tabs
        self.device_tab = self.create_device_tab()
        self.master_tab = self.create_master_tab()
        
        # Add tabs
        self.tabs.addTab(self.device_tab, "Scan Device")
        self.tabs.addTab(self.master_tab, "Scan from Master")
        
        # Add tabs to layout
        layout.addWidget(self.tabs)
    
    
    def create_device_tab(self):
        """Create the device scanning tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Connection status group
        status_group = QGroupBox("สถานะการเชื่อมต่อ / Connection Status")
        status_layout = QHBoxLayout()
        
        # Status indicator
        self.device_status_label = QLabel("● ไม่เชื่อมต่อ / Disconnected")
        self.device_status_label.setStyleSheet("color: red; font-weight: bold;")
        
        # Check connection button
        check_btn = QPushButton("ตรวจสอบการเชื่อมต่อ / Check Connection")
        check_btn.clicked.connect(self.check_device_connection)
        
        status_layout.addWidget(self.device_status_label)
        status_layout.addStretch()
        status_layout.addWidget(check_btn)
        status_group.setLayout(status_layout)
        
        # Import instructions
        instructions = QLabel(
            "สแกนเครื่องสแกนเพื่อรับม้วน / Scan device to receive roll. Please use the external scanner to scan the file.\n"
            "ไฟล์ควรมีคอลัมน์ต่อไปนี้ / The file should contain the following columns:\n"
            "- sku (required): Product SKU\n"
            "- lot (required): Lot number\n"
            "- length (required): Roll length in meters\n"
            "- width (optional): Roll width in meters\n"
            "- grade (optional): Quality grade (A, B, C, etc.)\n"
            "- location (optional): Storage location\n"
            "- date_received (optional): Date in YYYY-MM-DD format\n"
            "- notes (optional): Any additional notes"
        )
        instructions.setWordWrap(True)
        
        # Import button
        self.import_btn = QPushButton("สแกนเครื่องสแกน / Scan Device...")
        self.import_btn.clicked.connect(self.scan_device)
        
        # Preview table
        self.import_table = QTableWidget()
        self.import_table.setColumnCount(8)
        self.import_table.setHorizontalHeaderLabels([
            "SKU", "Lot", "Length", "Width", "Grade", "Location", "Date", "Status"
        ])
        self.import_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.import_table.verticalHeader().setVisible(False)
        self.import_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Add to layout
        layout.addWidget(status_group)
        layout.addWidget(instructions)
        layout.addWidget(self.import_btn)
        layout.addWidget(self.import_table)
        
        return tab
    
    def create_master_tab(self):
        """Create the scan from master tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Search group
        search_group = QGroupBox("Search Master Data")
        search_layout = QHBoxLayout()
        
        search_layout.addWidget(QLabel("Code/SKU:"))
        self.master_search_code = QLineEdit()
        self.master_search_code.setPlaceholderText("Enter product code...")
        self.master_search_code.textChanged.connect(self.search_master_data)
        search_layout.addWidget(self.master_search_code)
        
        search_layout.addWidget(QLabel("Supplier:"))
        self.master_search_supplier = QLineEdit()
        self.master_search_supplier.setPlaceholderText("Enter supplier name...")
        self.master_search_supplier.textChanged.connect(self.search_master_data)
        search_layout.addWidget(self.master_search_supplier)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # Master data table
        self.master_data_table = QTableWidget()
        self.master_data_table.setColumnCount(7)
        self.master_data_table.setHorizontalHeaderLabels([
            "Code", "Supplier", "Description", "Location", "Unit", "Select", ""
        ])
        self.master_data_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.master_data_table.verticalHeader().setVisible(False)
        self.master_data_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.master_data_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.master_data_table)
        
        # Form group for roll details
        form_group = QGroupBox("Roll Details")
        form_layout = QFormLayout()
        
        self.master_lot = QLineEdit()
        self.master_lot.setPlaceholderText("e.g., LOT2023-001")
        form_layout.addRow("Lot No.*:", self.master_lot)
        
        self.master_length = QDoubleSpinBox()
        self.master_length.setRange(0.01, 10000.0)
        self.master_length.setValue(100.0)
        self.master_length.setSuffix(" m")
        self.master_length.setDecimals(2)
        form_layout.addRow("Length*:", self.master_length)
        
        self.master_location = QLineEdit()
        self.master_location.setPlaceholderText("e.g., Warehouse A, Rack 1")
        form_layout.addRow("Location:", self.master_location)
        
        self.master_date = QDateEdit()
        self.master_date.setCalendarPopup(True)
        self.master_date.setDate(QDate.currentDate())
        form_layout.addRow("Date Received:", self.master_date)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.master_clear_btn = QPushButton("Clear")
        self.master_clear_btn.clicked.connect(self.clear_master_form)
        
        self.master_submit_btn = QPushButton("Save Roll")
        self.master_submit_btn.clicked.connect(self.submit_master_form)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.master_clear_btn)
        btn_layout.addWidget(self.master_submit_btn)
        
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        return tab
    
    def search_master_data(self):
        """Search master data and display results"""
        code_query = self.master_search_code.text().strip()
        supplier_query = self.master_search_supplier.text().strip()
        
        # Search using suppliers manager
        results = self.suppliers_manager.search_combined(supplier_query, code_query)
        
        # Display results in table
        self.master_data_table.setRowCount(len(results))
        
        for row, item in enumerate(results):
            # Code
            code = item.get('pdt_code') or item.get('Code') or item.get('code') or ''
            self.master_data_table.setItem(row, 0, QTableWidgetItem(str(code)))
            
            # Supplier
            supplier = item.get('spl_name') or ''
            self.master_data_table.setItem(row, 1, QTableWidgetItem(str(supplier)))
            
            # Description
            desc = item.get('Description') or item.get('description') or ''
            self.master_data_table.setItem(row, 2, QTableWidgetItem(str(desc)))
            
            # Location
            location = item.get('Location') or item.get('location') or ''
            self.master_data_table.setItem(row, 3, QTableWidgetItem(str(location)))
            
            # Unit
            unit = item.get('Unit') or item.get('unit') or 'MTS'
            self.master_data_table.setItem(row, 4, QTableWidgetItem(str(unit)))
            
            # Select button
            select_btn = QPushButton("Select")
            select_btn.clicked.connect(lambda checked, r=row: self.select_master_row(r))
            self.master_data_table.setCellWidget(row, 5, select_btn)
    
    def select_master_row(self, row):
        """Select a row from master data"""
        code = self.master_data_table.item(row, 0).text()
        supplier = self.master_data_table.item(row, 1).text()
        
        # You can populate the form with selected data if needed
        QMessageBox.information(self, "Selected", f"Code: {code}\nSupplier: {supplier}")
    
    def clear_master_form(self):
        """Clear the master form"""
        self.master_lot.clear()
        self.master_length.setValue(100.0)
        self.master_location.clear()
        self.master_date.setDate(QDate.currentDate())
    
    def submit_master_form(self):
        """Submit the master form and save roll"""
        lot = self.master_lot.text().strip()
        length = self.master_length.value()
        location = self.master_location.text().strip()
        date_str = self.master_date.date().toString("yyyy-MM-dd")
        
        if not lot:
            QMessageBox.warning(self, "Error", "Please enter Lot No.")
            return
        
        # Create roll data
        roll_data = {
            'sku': 'MASTER',
            'lot': lot,
            'length': length,
            'location': location,
            'grade': 'A',
            'date_received': date_str
        }
        
        self.scan_received.emit(roll_data)
        self.clear_master_form()
    
    def on_scan_received(self, scan_data):
        """Handle a QR code scan from a mobile device"""
        try:
            print("--------on_scan_received----------")
            print(scan_data)
            datas = scan_data.split("%")
            print(datas)

            roll = Roll(
                roll_id=datas[0],
                sku=datas[1],
                lot=datas[6],
                current_length=0.0,
                original_length=0.0,
                width=0.0,
                grade='-',
                location=datas[7],
                date_received=datetime.now().strftime("%Y-%m-%d"),
        
            )
            
            self.storage.add_roll(roll)
            self.add_mobile_record(roll)
           
            QMessageBox.information(
                self,
                "Success",
                f"Roll {1} saved successfully!"
            )
            
            # Emit signal to refresh reports
            self.refresh_reports.emit()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error processing scanned data: {str(e)}"
            )
    
    def extract_roll_data(self, text):
        """Try to extract roll data from text"""
        roll_id_match = re.search(r'ROLL[-_]?\d+', text, re.IGNORECASE)
        
        if not roll_id_match:
            return None
            
        sku_match = re.search(r'SKU[:\s]?([A-Z0-9-]+)', text, re.IGNORECASE)
        lot_match = re.search(r'LOT[:\s]?([A-Z0-9-]+)', text, re.IGNORECASE)
        length_match = re.search(r'LENGTH[:\s]?(\d+(?:\.\d+)?)', text, re.IGNORECASE)
        
        return {
            'roll_id': roll_id_match.group(0).upper(),
            'sku': sku_match.group(1).upper() if sku_match else 'UNKNOWN',
            'lot': lot_match.group(1).upper() if lot_match else 'UNKNOWN',
            'length': float(length_match.group(1)) if length_match else 0.0,
            'location': '',
            'grade': 'A',
            'date_received': datetime.now().strftime("%Y-%m-%d")
        }
    
    def show_mobile_connection_qr(self):
        """Show mobile connection QR code"""
        try:
            qr_url = self.mobile_server.url
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_url)
            qr.make(fit=True)
            
            # Create image
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Create dialog
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton
            from PySide6.QtGui import QPixmap
            from PySide6.QtCore import Qt
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Connect Mobile Device")
            dialog.setMinimumSize(400, 500)
            
            # Create layout
            layout = QVBoxLayout()
            
            # Add connection info
            info_text = f"""
            <h3>เชื่อมต่อมือถือ / Connect Mobile Device</h3>
            <p>สแกน QR Code นี้ด้วยกล้องมือถือ</p>
            <p>Scan this QR code with mobile camera:</p>
            <p><b>URL:</b> {qr_url}</p>
            <p><b>IP Address:</b> {self.mobile_server.local_ip}</p>
            <p><b>Port:</b> {self.mobile_server.port}</p>
            <p style="color: green;"><b>✓ ระบบพร้อม</b></p>
            """
            
            info_label = QLabel(info_text)
            info_label.setTextFormat(Qt.TextFormat.RichText)
            info_label.setWordWrap(True)
            layout.addWidget(info_label)
            
            # Convert QR code to pixmap
            buffer = BytesIO()
            qr_img.save(buffer, format="PNG")
            pixmap = QPixmap()
            pixmap.loadFromData(buffer.getvalue())
            
            # Add QR code to label
            qr_label = QLabel()
            qr_label.setPixmap(pixmap)
            qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(qr_label)
            
            # Add buttons
            btn_layout = QHBoxLayout()
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            
            btn_layout.addStretch()
            btn_layout.addWidget(close_btn)
            
            layout.addLayout(btn_layout)
            dialog.setLayout(layout)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error showing QR code: {str(e)}")
    
    def check_device_connection(self):
        """ตรวจสอบสถานะการเชื่อมต่อเครื่องสแกน / Check scanner device connection status"""
        try:
            # ตรวจสอบพอร์ต COM ที่ใช้บ่อย
            import serial.tools.list_ports
            
            ports = list(serial.tools.list_ports.comports())
            
            if ports:
                # พบเครื่องสแกน
                port_info = ports[0]
                self.device_status_label.setText(f"● เชื่อมต่อแล้ว / Connected: {port_info.device}")
                self.device_status_label.setStyleSheet("color: green; font-weight: bold;")
                self.import_btn.setEnabled(True)
                
                QMessageBox.information(
                    self,
                    "สำเร็จ / Success",
                    f"เชื่อมต่อเครื่องสแกนสำเร็จ\n\nConnected to scanner:\n{port_info.device}\n{port_info.description}"
                )
            else:
                # ไม่พบเครื่องสแกน
                self.device_status_label.setText("● ไม่เชื่อมต่อ / Disconnected")
                self.device_status_label.setStyleSheet("color: red; font-weight: bold;")
                self.import_btn.setEnabled(False)
                
                QMessageBox.warning(
                    self,
                    "ข้อผิดพลาด / Error",
                    "ไม่พบเครื่องสแกน\n\nNo scanner device found.\nPlease connect your scanner device."
                )
        except ImportError:
            # ถ้าไม่มี pyserial ให้แสดงข้อความ
            QMessageBox.warning(
                self,
                "ข้อผิดพลาด / Error",
                "ไม่สามารถตรวจสอบเครื่องสแกนได้\n\nCannot check scanner connection.\nPlease install pyserial: pip install pyserial"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "ข้อผิดพลาด / Error",
                f"เกิดข้อผิดพลาดในการตรวจสอบ:\n\nError checking connection:\n{str(e)}"
            )
    
    def scan_device(self):
        """Scan device to receive roll"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Device File", "", "CSV Files (*.csv)")
        if file_path:
            self.import_from_file(file_path)
    
    def import_from_file(self):
        """Import rolls from a file"""
        import pandas as pd
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Rolls",
            "",
            "CSV Files (*.csv);;Excel Files (*.xlsx *.xls)"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            # Read file based on extension
            if file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                df = pd.read_csv(file_path)
            
            # Normalize column names (lowercase, strip whitespace)
            df.columns = df.columns.str.lower().str.strip()
            
            # Check required columns
            required_columns = ['sku', 'lot', 'length']
            available_columns = [col.lower().strip() for col in df.columns]
            missing_columns = [col for col in required_columns if col not in available_columns]
            
            if missing_columns:
                QMessageBox.critical(
                    self,
                    "Import Error",
                    f"Missing required columns: {', '.join(missing_columns)}\n\n"
                    f"Required columns: roll_id (optional), sku, lot, length\n"
                    f"Optional columns: grade, location, date_received"
                )
                return
            
            # Update preview table
            self.import_table.setRowCount(len(df))
            
            for i, row in df.iterrows():
                # Add data to table
                self.import_table.setItem(i, 0, QTableWidgetItem(str(row.get('sku', ''))))
                self.import_table.setItem(i, 1, QTableWidgetItem(str(row.get('lot', ''))))
                self.import_table.setItem(i, 2, QTableWidgetItem(str(row.get('length', ''))))
                self.import_table.setItem(i, 3, QTableWidgetItem(str(row.get('width', ''))))
                self.import_table.setItem(i, 4, QTableWidgetItem(str(row.get('grade', 'A'))))
                self.import_table.setItem(i, 5, QTableWidgetItem(str(row.get('location', ''))))
                self.import_table.setItem(i, 6, QTableWidgetItem(str(row.get('date_received', ''))))
                
                # Validate row
                is_valid = all(str(row.get(col, '')).strip() for col in required_columns)
                status = "Valid" if is_valid else "Missing required fields"
                
                status_item = QTableWidgetItem(status)
                if is_valid:
                    status_item.setForeground(Qt.GlobalColor.darkGreen)
                else:
                    status_item.setForeground(Qt.GlobalColor.red)
                
                self.import_table.setItem(i, 7, status_item)
            
            # Enable import button if there are valid rows
            valid_rows = sum(
                1 for i in range(self.import_table.rowCount())
                if self.import_table.item(i, 7).text() == "Valid"
            )
            
            if valid_rows > 0:
                if QMessageBox.question(
                    self,
                    "Import Confirmation",
                    f"Import {valid_rows} valid roll(s)?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                ) == QMessageBox.StandardButton.Yes:
                    self.process_import(df[df[required_columns].notna().all(axis=1)])
            else:
                QMessageBox.warning(
                    self,
                    "Import",
                    "No valid rows to import. Please check your file and try again."
                )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Error",
                f"An error occurred while importing the file:\n{str(e)}"
            )
    
    def process_import(self, df):
        """Process the imported data and add rolls to storage"""
        import pandas as pd
        
        success_count = 0
        
        for idx, row in df.iterrows():
            try:
                # Get or generate roll ID
                if 'roll_id' in df.columns and str(row.get('roll_id', '')).strip():
                    roll_id = str(row['roll_id']).strip().upper()
                else:
                    # Generate roll ID automatically
                    roll_id = self.roll_id_generator.get_next_roll_id()
                
                sku = str(row['sku']).strip().upper()
                lot = str(row['lot']).strip().upper()
                
                # Create roll data
                roll_data = {
                    'roll_id': roll_id,
                    'sku': sku,
                    'lot': lot,
                    'length': float(row['length']),
                    'grade': str(row.get('grade', 'A')).upper(),
                    'location': str(row.get('location', '')).strip(),
                    'date_received': str(row.get('date_received', datetime.now().strftime("%Y-%m-%d")))
                }
                
                # Emit signal with roll data
                self.scan_received.emit(roll_data)
                success_count += 1
                
            except Exception as e:
                print(f"Error importing row {idx}: {str(e)}")
        
        # Show results
        QMessageBox.information(
            self,
            "Import Complete",
            f"Successfully imported {success_count} out of {len(df)} rolls."
        )
        
        # Clear the table
        self.import_table.setRowCount(0)
