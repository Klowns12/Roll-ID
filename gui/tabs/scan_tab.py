import os
from io import BytesIO
import qrcode
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QTabWidget, QMessageBox,
    QHeaderView, QFormLayout, QDoubleSpinBox, QDateEdit, QDialog
)
from PySide6.QtCore import Signal as pyqtSignal, QDate
from utils.roll_id_generator import RollIDGenerator
from utils.suppliers_manager import SuppliersManager

# Import Controller
from controllers.scan_controller import ScanController

class ScanTab(QWidget):
    refresh_reports = pyqtSignal()

    def __init__(self, storage, current_user=None):
        super().__init__()
        self.storage = storage
        self.current_user = current_user
        
        data_dir = os.path.join(os.getcwd(), "data")
        self.roll_id_generator = RollIDGenerator(data_dir)
        self.suppliers_manager = SuppliersManager()
        self.controller = ScanController(self, storage, self.roll_id_generator, self.suppliers_manager)
        
        self.setup_ui()

    def setup_ui(self):
        """Set up the Scan QR tab UI - 100% Mirroring RollOld"""
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        
        # --- Tab 1: Scan Device ---
        self.device_tab = QWidget()
        dev_layout = QVBoxLayout(self.device_tab)
        
        status_group = QGroupBox("สถานะการเชื่อมต่อ / Connection Status")
        status_layout = QHBoxLayout()
        self.status_label = QLabel("● ไม่เชื่อมต่อ / Disconnected")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        
        self.check_btn = QPushButton("ตรวจสอบการเชื่อมต่อ / Check Connection")
        self.check_btn.clicked.connect(self.controller.check_device_connection)
        
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.check_btn)
        status_group.setLayout(status_layout)
        
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
        instructions.setStyleSheet("color: #555; background-color: #f0f0f0; padding: 10px; border-radius: 5px;")

        self.mobile_btn = QPushButton("📱 Connect Mobile Scanner (สแกนผ่านมือถือ)")
        self.mobile_btn.clicked.connect(self.show_mobile_connection_qr)
        self.mobile_btn.setStyleSheet("height: 40px; background-color: #1976d2; color: white; font-weight: bold;")
        
        self.import_btn = QPushButton("สแกนเครื่องสแกน / Scan Device...")
        self.import_btn.clicked.connect(self.controller.handle_file_import)
        self.import_btn.setStyleSheet("height: 40px; font-weight: bold;")
        
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(8)
        self.preview_table.setHorizontalHeaderLabels(
            ["SKU", "Lot", "Length", "Width", "Grade", "Location", "Date", "Status"]
        )
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.preview_table.verticalHeader().setVisible(False)
        self.preview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        dev_layout.addWidget(status_group)
        dev_layout.addWidget(instructions)
        dev_layout.addWidget(self.mobile_btn)
        dev_layout.addWidget(self.import_btn)
        dev_layout.addWidget(self.preview_table)
        
        # --- Tab 2: Scan from Master ---
        self.master_tab = QWidget()
        master_layout = QVBoxLayout(self.master_tab)
        
        search_group = QGroupBox("Search Master Data")
        search_layout = QHBoxLayout()
        
        search_layout.addWidget(QLabel("Code/SKU:"))
        self.master_search_code = QLineEdit()
        self.master_search_code.setPlaceholderText("Enter product code...")
        self.master_search_code.textChanged.connect(self.on_search)
        search_layout.addWidget(self.master_search_code)
        
        search_layout.addWidget(QLabel("Supplier:"))
        self.master_search_supplier = QLineEdit()
        self.master_search_supplier.setPlaceholderText("Enter supplier name...")
        self.master_search_supplier.textChanged.connect(self.on_search)
        search_layout.addWidget(self.master_search_supplier)
        
        search_group.setLayout(search_layout)
        master_layout.addWidget(search_group)
        
        self.master_table = QTableWidget()
        self.master_table.setColumnCount(7)
        self.master_table.setHorizontalHeaderLabels(
            ["Code", "Supplier", "Description", "Location", "Unit", "Select", ""]
        )
        self.master_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.master_table.verticalHeader().setVisible(False)
        self.master_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.master_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        master_layout.addWidget(self.master_table, 1)
        
        self.form_group = QGroupBox("Roll Details")
        self.form_group.setEnabled(False)
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
        
        self.form_group.setLayout(form_layout)
        master_layout.addWidget(self.form_group)
        
        btn_layout = QHBoxLayout()
        self.master_clear_btn = QPushButton("Clear")
        self.master_clear_btn.clicked.connect(self.clear_master_form)
        self.master_clear_btn.setStyleSheet("height: 40px; width: 100px;")
        
        self.master_submit_btn = QPushButton("Save Roll")
        self.master_submit_btn.clicked.connect(self.controller.submit_master_roll)
        self.master_submit_btn.setStyleSheet("height: 40px; width: 150px; background-color: #2e7d32; color: white; font-weight: bold;")
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.master_clear_btn)
        btn_layout.addWidget(self.master_submit_btn)
        master_layout.addLayout(btn_layout)
        
        self.tabs.addTab(self.device_tab, "Scan Device")
        self.tabs.addTab(self.master_tab, "Scan from Master")
        layout.addWidget(self.tabs)

    def on_search(self):
        code_query = self.master_search_code.text().strip()
        supplier_query = self.master_search_supplier.text().strip()
        results = self.suppliers_manager.search_combined(supplier_query, code_query)
        self.master_table.setRowCount(0)
        for item in results:
            r = self.master_table.rowCount()
            self.master_table.insertRow(r)
            self.master_table.setItem(r, 0, QTableWidgetItem(str(item.get('Code', item.get('pdt_code', '')))))
            self.master_table.setItem(r, 1, QTableWidgetItem(str(item.get('Supplier Name', item.get('spl_name', '')))))
            self.master_table.setItem(r, 2, QTableWidgetItem(str(item.get('Description', item.get('pdt_name', '')))))
            self.master_table.setItem(r, 3, QTableWidgetItem(str(item.get('Location', ''))))
            self.master_table.setItem(r, 4, QTableWidgetItem(str(item.get('Unit', 'MTS'))))
            
            btn = QPushButton("Select")
            btn.clicked.connect(lambda checked, i=item: self.controller.select_master_item(i))
            self.master_table.setCellWidget(r, 5, btn)

    def clear_master_form(self):
        self.master_lot.clear()
        self.master_length.setValue(100.0)
        self.master_location.clear()
        self.master_date.setDate(QDate.currentDate())
        self.form_group.setEnabled(False)

    def update_connection_status(self, connected, device=""):
        if connected:
            self.status_label.setText(f"● เชื่อมต่อแล้ว / Connected: {device}")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.status_label.setText("● ไม่เชื่อมต่อ / Disconnected")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")

    def display_preview(self, df):
        self.preview_table.setRowCount(len(df))
        for i, row in df.iterrows():
            self.preview_table.setItem(i, 0, QTableWidgetItem(str(row.get('sku', ''))))
            self.preview_table.setItem(i, 1, QTableWidgetItem(str(row.get('lot', ''))))
            self.preview_table.setItem(i, 2, QTableWidgetItem(str(row.get('length', ''))))
            self.preview_table.setItem(i, 3, QTableWidgetItem(str(row.get('width', ''))))
            self.preview_table.setItem(i, 4, QTableWidgetItem(str(row.get('grade', 'A'))))
            self.preview_table.setItem(i, 5, QTableWidgetItem(str(row.get('location', ''))))
            self.preview_table.setItem(i, 6, QTableWidgetItem(str(row.get('date_received', ''))))
            self.preview_table.setItem(i, 7, QTableWidgetItem("Valid"))
        
        if QMessageBox.question(self, "ยืนยัน", f"Import {len(df)} rolls?") == QMessageBox.StandardButton.Yes:
            self.controller.submit_imported_data(df)

    def show_mobile_connection_qr(self):
        main_win = self.window()
        if not hasattr(main_win, 'mobile_server'):
            QMessageBox.critical(self, "Error", "Mobile Server not found")
            return
        qr_url = main_win.mobile_server.url
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        qr_img.save(buffer, format="PNG")
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue())
        dialog = QDialog(self)
        dialog.setWindowTitle("Connect Mobile Scanner")
        l = QVBoxLayout(dialog)
        l.addWidget(QLabel(f"Scan this URL: {qr_url}"))
        img_label = QLabel()
        img_label.setPixmap(pixmap)
        l.addWidget(img_label)
        dialog.exec()
