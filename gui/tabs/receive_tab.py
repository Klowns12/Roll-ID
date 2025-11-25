from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QComboBox, QPushButton, QMessageBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QDoubleSpinBox,
    QDateEdit, QCheckBox, QFileDialog, QInputDialog, QStyle, QDialog, QSpinBox
)
from PySide6.QtCore import Qt, QDate, Signal as pyqtSignal, QObject
from PySide6.QtGui import QIntValidator, QDoubleValidator, QPixmap
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
import qrcode
from io import BytesIO
import json
from datetime import datetime
import tempfile
import os
import socket
import webbrowser
from PySide6.QtCore import QTimer
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import queue
import sys
import pandas as pd
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.label_generator import LabelGenerator
from utils.roll_id_generator import RollIDGenerator
from storage import Roll

class ReceiveTab(QWidget):
    # Signal emitted when a new roll is received
    roll_received = pyqtSignal(dict)
    # Signal emitted to refresh reports tab
    refresh_reports = pyqtSignal()
    
    def __init__(self, storage):
        super().__init__()
        self.storage = storage
        self.label_generator = LabelGenerator()
        
        # Initialize Roll ID Generator
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
        self.roll_id_generator = RollIDGenerator(data_dir)
        
        self.setup_ui()
        # self.load_master_data()  # Commented out because master_tab is not created
        
        # Connect signals
        self.roll_received.connect(self.on_roll_received)
    
    def setup_ui(self):
        """Set up the Receive tab UI"""
        layout = QVBoxLayout(self)
        
        # Create manual entry form directly (no tabs)
        self.manual_tab = self.create_manual_tab()
        layout.addWidget(self.manual_tab)
    
    def create_manual_tab(self):
        """Create the manual entry tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Form group
        form_group = QGroupBox("Roll Information")
        form_layout = QFormLayout()

        # Roll ID (Auto-generated, read-only)
        self.manual_roll_id_label = QLabel("(Auto-generated)")
        self.manual_roll_id_label.setStyleSheet("color: #666; font-style: italic;")
        form_layout.addRow("Roll ID:", self.manual_roll_id_label)        
        
        # Code (SKU)
        self.manual_code = QLineEdit()
        self.manual_code.setPlaceholderText("e.g., RM2061406001")
        form_layout.addRow("Code*:", self.manual_code)
        
        # SubPartCode
        self.manual_subpart_code = QLineEdit()
        self.manual_subpart_code.setPlaceholderText("e.g., SUB001")
        form_layout.addRow("SubPartCode:", self.manual_subpart_code)
        
        # SupCode
        self.manual_sup_code = QLineEdit()
        self.manual_sup_code.setPlaceholderText("e.g., SUP001")
        form_layout.addRow("SupCode:", self.manual_sup_code)
        
        # Supplier Name
        self.manual_supplier_name = QLineEdit()
        self.manual_supplier_name.setPlaceholderText("e.g., Supplier Name")
        form_layout.addRow("Supplier Name:", self.manual_supplier_name)
        
        # Description
        self.manual_description = QLineEdit()
        self.manual_description.setPlaceholderText("e.g., Product Description")
        form_layout.addRow("Description:", self.manual_description)
        
        # Lot No.
        self.manual_lot = QLineEdit()
        self.manual_lot.setPlaceholderText("e.g., LOT2023-001")
        form_layout.addRow("Lot No.*:", self.manual_lot)
        
        # Quantity
        self.manual_quantity = QSpinBox()
        self.manual_quantity.setMinimum(1)
        self.manual_quantity.setMaximum(999)
        self.manual_quantity.setValue(1)
        form_layout.addRow("Quantity*:", self.manual_quantity)
        
        # Location
        self.manual_location = QLineEdit()
        self.manual_location.setPlaceholderText("e.g., Warehouse A, Rack 1")
        form_layout.addRow("Location:", self.manual_location)
        
        # Unit (Packing Unit)
        self.manual_unit = QLineEdit()
        self.manual_unit.setPlaceholderText("e.g., MTS")
        self.manual_unit.setText("MTS")
        form_layout.addRow("Unit (Packing Unit):", self.manual_unit)
        
        # Colour
        self.manual_colour = QLineEdit()
        self.manual_colour.setPlaceholderText("e.g., Red, Blue, Green")
        form_layout.addRow("Colour:", self.manual_colour)
        
        # Width
        self.manual_width = QLineEdit()
        self.manual_width.setPlaceholderText("e.g., 3.00 m")
        form_layout.addRow("Width:", self.manual_width)

        # Length
        self.manual_length = QLineEdit()
        self.manual_length.setPlaceholderText("e.g., 100.00 m")
        form_layout.addRow("Length:", self.manual_length)
        
        form_group.setLayout(form_layout)
        
        # Keep old fields for internal use
        self.manual_sku = self.manual_code  # Alias for backward compatibility
        self.manual_specifications = self.manual_description  # Alias
        self.manual_product = self.manual_description  # Alias
        self.manual_package_unit = self.manual_unit  # Alias
        self.manual_grade = QComboBox()  # Hidden
        self.manual_grade.addItems(["A", "B", "C", "D"])
        self.manual_date = QDateEdit()  # Hidden
        self.manual_date.setCalendarPopup(True)
        self.manual_date.setDate(QDate.currentDate())
        self.manual_notes = QLineEdit()  # Hidden
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.manual_clear_btn = QPushButton("Clear")
        self.manual_clear_btn.clicked.connect(self.clear_manual_form)
        
        self.manual_submit_btn = QPushButton("Save Roll")
        self.manual_submit_btn.clicked.connect(self.submit_manual_form)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.manual_clear_btn)
        btn_layout.addWidget(self.manual_submit_btn)
        
        # Add to layout
        layout.addWidget(form_group)
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        return tab
    
    # def create_master_tab(self):
    #     """Create the 'From Master' tab"""
    #     tab = QWidget()
    #     layout = QVBoxLayout(tab)
        
    #     # Master product selection
    #     master_group = QGroupBox("Select Master Product")
    #     master_layout = QVBoxLayout()
        
    #     # Product filter
    #     filter_layout = QHBoxLayout()
    #     filter_layout.addWidget(QLabel("Filter:"))
        
    #     self.master_filter = QLineEdit()
    #     self.master_filter.setPlaceholderText("Filter by SKU or description...")
    #     self.master_filter.textChanged.connect(self.filter_master_products)
        
    #     filter_layout.addWidget(self.master_filter)
    #     master_layout.addLayout(filter_layout)
        
    #     # Master products table
    #     self.master_table = QTableWidget()
    #     self.master_table.setColumnCount(4)
    #     self.master_table.setHorizontalHeaderLabels(["", "SKU", "Description", "Default Length"])
    #     self.master_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    #     self.master_table.verticalHeader().setVisible(False)
    #     self.master_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    #     self.master_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
    #     self.master_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
    #     master_layout.addWidget(self.master_table)
    #     master_group.setLayout(master_layout)
        
    #     # Form for roll details
    #     form_group = QGroupBox("Roll Details")
    #     form_layout = QFormLayout()
        
    #     # Lot
    #     self.master_lot = QLineEdit()
    #     self.master_lot.setPlaceholderText("e.g., LOT2023-001")
        
    #     # Length (can override default)
    #     self.master_length = QDoubleSpinBox()
    #     self.master_length.setRange(0.01, 10000.0)
    #     self.master_length.setValue(100.0)
    #     self.master_length.setSuffix(" m")
    #     self.master_length.setDecimals(2)
        
    #     # Use default length checkbox
    #     self.use_default_length = QCheckBox("Use default length")
    #     self.use_default_length.setChecked(True)
    #     self.use_default_length.toggled.connect(self.toggle_use_default_length)
        
    #     # Location
    #     self.master_location = QLineEdit()
    #     self.master_location.setPlaceholderText("e.g., Warehouse A, Rack 1")
        
    #     # Date received
    #     self.master_date = QDateEdit()
    #     self.master_date.setCalendarPopup(True)
    #     self.master_date.setDate(QDate.currentDate())
        
    #     # Notes
    #     self.master_notes = QLineEdit()
    #     self.master_notes.setPlaceholderText("Optional notes...")
        
    #     # Add fields to form
    #     form_layout.addRow("Lot*:", self.master_lot)
    #     form_layout.addRow("Length*:", self.master_length)
    #     form_layout.addRow("", self.use_default_length)
    #     form_layout.addRow("Location:", self.master_location)
    #     form_layout.addRow("Date Received:", self.master_date)
    #     form_layout.addRow("Notes:", self.master_notes)
        
    #     form_group.setLayout(form_layout)
        
    #     # Buttons
    #     btn_layout = QHBoxLayout()
        
    #     self.master_clear_btn = QPushButton("Clear")
    #     self.master_clear_btn.clicked.connect(self.clear_master_form)
        
    #     self.master_submit_btn = QPushButton("Save Roll")
    #     self.master_submit_btn.clicked.connect(self.submit_master_form)
        
    #     btn_layout.addStretch()
    #     btn_layout.addWidget(self.master_clear_btn)
    #     btn_layout.addWidget(self.master_submit_btn)
        
    #     # Add to layout
    #     layout.addWidget(master_group, 2)
    #     layout.addWidget(form_group, 1)
    #     layout.addLayout(btn_layout)
        
    #     return tab
    
    
    def load_master_data(self):
        """Load master products into the table"""
        self.master_products = self.storage.get_all_master_products()
        self.update_master_table()
    
    def update_master_table(self, filter_text=""):
        """Update the master products table with optional filtering"""
        self.master_table.setRowCount(0)
        
        filter_text = filter_text.lower()
        
        # Add products to table
        for product in self.master_products:
            # Skip if doesn't match filter
            if (filter_text and 
                filter_text not in product.sku.lower() and 
                filter_text not in product.description.lower()):
                continue
            
            row = self.master_table.rowCount()
            self.master_table.insertRow(row)
            
            # Add radio button
            radio_btn = QTableWidgetItem()
            radio_btn.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            radio_btn.setCheckState(Qt.CheckState.Unchecked)
            self.master_table.setItem(row, 0, radio_btn)
            
            # Add product data
            self.master_table.setItem(row, 1, QTableWidgetItem(product.sku))
            self.master_table.setItem(row, 2, QTableWidgetItem(product.description))
            self.master_table.setItem(row, 3, QTableWidgetItem(f"{product.default_length:.2f} m"))
    
    def filter_master_products(self):
        """Filter master products based on search text"""
        filter_text = self.master_filter.text()
        self.update_master_table(filter_text)
    
    def toggle_use_default_length(self, checked):
        """Enable/disable length input based on checkbox"""
        self.master_length.setEnabled(not checked)
        
        # If checked, set length to the selected product's default
        if checked and self.master_table.selectedItems():
            row = self.master_table.selectedItems()[0].row()
            sku = self.master_table.item(row, 1).text()
            product = next((p for p in self.master_products if p.sku == sku), None)
            if product:
                self.master_length.setValue(product.default_length)
    
    def clear_manual_form(self):
        """Clear the manual entry form"""
        self.manual_roll_id_label.setText("(Auto-generated)")
        self.manual_code.clear()
        self.manual_subpart_code.clear()
        self.manual_sup_code.clear()
        self.manual_supplier_name.clear()
        self.manual_description.clear()
        self.manual_lot.clear()
        self.manual_location.clear()
        self.manual_colour.clear()
        self.manual_package_unit.clear()
        self.manual_width.clear()
        self.manual_length.clear()
        self.manual_date.setDate(QDate.currentDate())
    
    def clear_master_form(self):
        """Clear the master entry form"""
        self.master_roll_id.clear()
        self.master_lot.clear()
        self.master_length.setValue(100.0)
        self.use_default_length.setChecked(True)
        self.master_location.clear()
        self.master_date.setDate(QDate.currentDate())
        self.master_notes.clear()
        
        # Clear selection in table
        for row in range(self.master_table.rowCount()):
            self.master_table.item(row, 0).setCheckState(Qt.CheckState.Unchecked)
    
    def submit_manual_form(self):
        """Submit the manual entry form"""
        
        # Validate required fields
        if not self.manual_code.text().strip():
            QMessageBox.warning(self, "Validation Error", "Code is required!")
            self.manual_code.setFocus()
            return
        
        if not self.manual_lot.text().strip():
            QMessageBox.warning(self, "Validation Error", "Lot No. is required!")
            self.manual_lot.setFocus()
            return
        
        # Get quantity
        quantity = self.manual_quantity.value()
        if quantity < 1:
            QMessageBox.warning(self, "Validation Error", "Quantity must be at least 1!")
            return
        
        # Generate base roll data
        code = self.manual_code.text().strip().upper()
        lot = self.manual_lot.text().strip().upper()
        length_text = self.manual_length.text().strip()
        subpart_code = self.manual_subpart_code.text().strip()
        sup_code = self.manual_sup_code.text().strip()
        supplier_name = self.manual_supplier_name.text().strip()
        description = self.manual_description.text().strip()
        location = self.manual_location.text().strip()
        unit_value = self.manual_unit.text().strip() or 'MTS'
        colour = self.manual_colour.text().strip()
        width = self.manual_width.text().strip()
        if length_text:
            try:
                length_value = float(length_text)
            except ValueError:
                QMessageBox.warning(self, "Validation Error", "Length must be a number!")
                self.manual_length.setFocus()
                return
        else:
            length_value = 0.0
        
        # Generate roll IDs for all quantities at once
        roll_ids = self.roll_id_generator.get_next_roll_ids(quantity)
        
        # Create and emit roll data for each roll
        for i in range(quantity):
            roll_id = roll_ids[i]
            roll_data = {
                'roll_id': roll_id,
                'sku': code,
                'pdt_code': code,
                'code': code,
                'subpart_code': subpart_code,
                'spl_part_code': subpart_code,
                'sup_code': sup_code,
                'spl_code': sup_code,
                'supplier_name': supplier_name,
                'Suppliers': supplier_name,
                'description': description,
                'pdt_name': description,
                'lot': lot,
                'location': location,
                'unit_type': unit_value,
                'packing_unit': unit_value,
                'colour': colour,
                'width': width,
                'length': length_value,
                'date_received': self.manual_date.date().toString("yyyy-MM-dd")
            }
            
            # Emit signal with roll data
            self.roll_received.emit(roll_data)
            
        # Show success message for multiple rolls
        if quantity > 1:
            QMessageBox.information(
                self,
                "Success",
                f"Successfully created {quantity} rolls with IDs: {', '.join(roll_ids)}"
            )
    
    def submit_master_form(self):
        """Submit the master entry form"""

        if not self.master_roll_id.text().strip():
            QMessageBox.warning(self, "Validation Error", "Roll ID is required!")
            self.master_roll_id.setFocus()
            return
        
        # Check if a product is selected
        selected_row = -1
        for row in range(self.master_table.rowCount()):
            if self.master_table.item(row, 0).checkState() == Qt.CheckState.Checked:
                selected_row = row
                break
        
        if selected_row == -1:
            QMessageBox.warning(self, "Validation Error", "Please select a product from the list!")
            return
        
        # Validate required fields
        if not self.master_lot.text().strip():
            QMessageBox.warning(self, "Validation Error", "Lot number is required!")
            self.master_lot.setFocus()
            return
        
        # Get selected product
        sku = self.master_table.item(selected_row, 1).text()
        product = next((p for p in self.master_products if p.sku == sku), None)
        
        if not product:
            QMessageBox.warning(self, "Error", "Selected product not found!")
            return
        
        # Get roll ID from input
        roll_id = self.master_roll_id.text().strip().upper()
        lot = self.master_lot.text().strip().upper()
        
        # Create roll data
        length = product.default_length if self.use_default_length.isChecked() else self.master_length.value()
        roll_data = {
            'roll_id': roll_id,
            'sku': sku,
            'lot': lot,
            'length': length,
            'default_length': length,  # Add default_length
            'grade': product.default_grade,
            'location': self.master_location.text().strip(),
            'date_received': self.master_date.date().toString("yyyy-MM-dd"),
            'notes': self.master_notes.text().strip()
        }
        
        # Emit signal with roll data
        self.roll_received.emit(roll_data)
    
    
    def on_roll_received(self, roll_data):
        """Handle a new roll being received - send data to Rolls Tab for processing"""
        try:
            # Show success message
            QMessageBox.information(
                self,
                "สำเร็จ / Success",
                f"ข้อมูลม้วน {roll_data['roll_id']} ได้รับเข้าแล้ว!\n\n"
                f"Data received for roll {roll_data['roll_id']}!\n\n"
                f"ไปที่แท็บ 'จัดการม้วน / Rolls' เพื่อสร้าง QR Code และฉลาก\n"
                f"Go to 'Rolls' tab to create QR Code and label"
            )
            
            # Clear the form
            self.clear_manual_form()
            
            # Get main window and emit signal to Rolls Tab
            main_window = self.window()
            if hasattr(main_window, 'rolls_tab'):
                # Send roll data to Rolls Tab for processing
                if hasattr(main_window.rolls_tab, 'add_new_roll'):
                    main_window.rolls_tab.add_new_roll(roll_data)
            
            # Emit signal to refresh Reports tab
            self.refresh_reports.emit()
            
            # Switch to the rolls tab in the main window
            if hasattr(main_window, 'tab_widget'):
                main_window.tab_widget.setCurrentIndex(3)  # Updated index for rolls tab
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "ข้อผิดพลาด / Error",
                f"An error occurred while processing the roll:\n{str(e)}"
            )
    
    def save_qr_code(self, qr_image, filename=None):
        """Save QR code to file"""
        if qr_image is None:
            return
            
        if filename is None:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Save QR Code",
                "",
                "PNG Files (*.png);;All Files (*)"
            )
            
            if not filename:
                return
                
            if not filename.lower().endswith('.png'):
                filename += '.png'
        
        try:
            qr_image.save(filename)
            QMessageBox.information(self, "Success", f"QR code saved as {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving QR code: {str(e)}")
    
    def print_label(self, roll):
        """พิมพ์ฉลากสำหรับม้วนผ้า"""
        try:
            # ถามว่าต้องการฉลากแบบไหน
            label_types = ["ฉลากมาตรฐาน (A6)", "ฉลากขนาดเล็ก (4x3 นิ้ว)"]
            label_type, ok = QInputDialog.getItem(
                self,
                "เลือกประเภทฉลาก",
                "ประเภทฉลาก:",
                label_types,
                0,
                False
            )
            
            if not ok:
                return
            
            # สร้างข้อมูลสำหรับฉลาก
            roll_data = {
                'roll_id': roll.roll_id,
                'sku': roll.sku,
                'lot': roll.lot,
                'length': roll.current_length,
                'grade': roll.grade,
                'date_received': roll.date_received,
                'location': roll.location
            }
            
            # สร้างฉลาก
            label_img = self.label_generator.create_label(roll_data)

            
            # แปลงเป็น QPixmap
            buffer = self.label_generator.get_label_as_bytes(label_img)
            qpixmap = QPixmap()
            qpixmap.loadFromData(buffer.read())
            
            # ถามว่าต้องการพิมพ์หรือบันทึก
            reply = QMessageBox.question(
                self,
                "พิมพ์ฉลาก",
                "ต้องการพิมพ์เลยหรือบันทึกเป็นไฟล์?",
                QMessageBox.StandardButton(0x00000001) |  # Save
                QMessageBox.StandardButton(0x00000400) |  # Yes (Print)
                QMessageBox.Cancel,
                QMessageBox.StandardButton(0x00000400)
            )
            
            if reply == QMessageBox.StandardButton(0x00000400):  # Print
                self._print_pixmap(qpixmap)
            elif reply == QMessageBox.StandardButton(0x00000001):  # Save
                self._save_label_file(label_img, roll.roll_id)
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "ข้อผิดพลาด",
                f"เกิดข้อผิดพลาดในการสร้างฉลาก:\n{str(e)}"
            )
    
    def _print_pixmap(self, pixmap):
        """พิมพ์ pixmap"""
        try:
            printer = QPrinter(QPrinter.HighResolution)
            print_dialog = QPrintDialog(printer, self)
            
            if print_dialog.exec() == QDialog.Accepted:
                from PySide6.QtGui import QPainter
                painter = QPainter(printer)
                
                # คำนวณขนาดให้พอดีกับหน้ากระดาษ
                rect = painter.viewport()
                size = pixmap.size()
                size.scale(rect.size(), Qt.KeepAspectRatio)
                
                painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
                painter.setWindow(pixmap.rect())
                painter.drawPixmap(0, 0, pixmap)
                painter.end()
                
                QMessageBox.information(self, "สำเร็จ", "พิมพ์ฉลากสำเร็จ!")
        except Exception as e:
            QMessageBox.critical(
                self,
                "ข้อผิดพลาด",
                f"เกิดข้อผิดพลาดในการพิมพ์:\n{str(e)}"
            )
    
    def _save_label_file(self, image, roll_id):
        """บันทึกฉลากเป็นไฟล์"""
        try:
            default_filename = f"Label_{roll_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "บันทึกฉลาก",
                default_filename,
                "PNG Files (*.png);;PDF Files (*.pdf);;All Files (*)"
            )
            
            if filename:
                # ตรวจสอบนามสกุลไฟล์
                if filename.lower().endswith('.pdf'):
                    self.label_generator.save_label(image, filename, format='PDF')
                else:
                    if not filename.lower().endswith('.png'):
                        filename += '.png'
                    self.label_generator.save_label(image, filename, format='PNG')
                
                QMessageBox.information(
                    self,
                    "สำเร็จ",
                    f"บันทึกฉลากเป็น {filename} สำเร็จ!"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "ข้อผิดพลาด",
                f"เกิดข้อผิดพลาดในการบันทึก:\n{str(e)}"
            )
