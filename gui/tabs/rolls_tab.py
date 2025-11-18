from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QMessageBox, QFileDialog, QInputDialog,
    QLabel, QLineEdit, QDialog, QDialogButtonBox, QFormLayout,
    QComboBox, QGroupBox, QSpinBox, QDoubleSpinBox, QToolBar, QStatusBar
)
from PySide6.QtCore import Qt, QSortFilterProxyModel, QRegularExpression, QDate
from PySide6.QtGui import QRegularExpressionValidator, QAction, QIcon, QPixmap
from datetime import datetime, timedelta
import qrcode
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import mm
from reportlab.graphics.barcode import code128
from reportlab.graphics import renderPDF
from reportlab.lib.colors import black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib import colors
import tempfile
import os
import json
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from gui.dialogs import LabelPreviewDialog

class RollsTab(QWidget):
    def __init__(self, storage):
        super().__init__()
        self.storage = storage
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Set up the Rolls tab UI"""
        layout = QVBoxLayout(self)
        
        # Filter controls
        filter_group = QGroupBox("Filters")
        filter_layout = QHBoxLayout()
        
        # SKU filter
        self.sku_filter = QComboBox()
        self.sku_filter.setEditable(True)
        self.sku_filter.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.sku_filter.setPlaceholderText("Filter by SKU")
        self.sku_filter.currentTextChanged.connect(self.apply_filters)
        
        # Status filter
        self.status_filter = QComboBox()
        self.status_filter.addItem("All Status", "")
        self.status_filter.addItem("Active", "active")
        self.status_filter.addItem("Used", "used")
        self.status_filter.currentIndexChanged.connect(self.apply_filters)
        
        # Location filter
        self.location_filter = QComboBox()
        self.location_filter.setEditable(True)
        self.location_filter.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.location_filter.setPlaceholderText("Filter by Location")
        self.location_filter.currentTextChanged.connect(self.apply_filters)
        
        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by Roll ID, SKU, or Lot...")
        self.search_input.textChanged.connect(self.apply_filters)
        
        # Add to filter layout
        filter_layout.addWidget(QLabel("SKU:"))
        filter_layout.addWidget(self.sku_filter, 1)
        filter_layout.addWidget(QLabel("Status:"))
        filter_layout.addWidget(self.status_filter)
        filter_layout.addWidget(QLabel("Location:"))
        filter_layout.addWidget(self.location_filter, 1)
        filter_layout.addWidget(QLabel("Search:"))
        filter_layout.addWidget(self.search_input, 2)
        
        filter_group.setLayout(filter_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_data)
        
        self.cut_btn = QPushButton("Cut Roll")
        self.cut_btn.clicked.connect(self.cut_roll)
        self.cut_btn.setEnabled(False)
        
        self.print_label_btn = QPushButton("Print Label")
        self.print_label_btn.clicked.connect(self.print_label)
        self.print_label_btn.setEnabled(False)
        
        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self.export_data)
        
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.cut_btn)
        btn_layout.addWidget(self.print_label_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.export_btn)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "",  # For selection
            "Roll ID",
            "Code",
            "SubPartCode",
            "SupCode",
            "Supplier Name",
            "Description",
            "Lot No.",
            "Location",
            "Status"
        ])
        
        # Configure table
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Connect selection changed signal
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        
        # Add widgets to layout
        layout.addWidget(filter_group)
        layout.addLayout(btn_layout)
        layout.addWidget(self.table)
        
        # Set column widths
        self.table.setColumnWidth(0, 30)      # Selector
        self.table.setColumnWidth(1, 150)     # Roll ID
        self.table.setColumnWidth(2, 120)     # SKU
        self.table.setColumnWidth(3, 100)     # Lot
        self.table.setColumnWidth(4, 120)     # Current Length
        self.table.setColumnWidth(5, 120)     # Original Length
        self.table.setColumnWidth(6, 150)     # Location
        self.table.setColumnWidth(7, 100)     # Status
    
    def load_data(self):
        """Load rolls data into the table"""
        # Clear existing data
        self.table.setRowCount(0)
        
        # Get all rolls
        self.rolls = self.storage.search_rolls()
        
        # Update filters
        self.update_filters()
        
        # Add rolls to table
        for roll in self.rolls:
            self.add_roll_to_table(roll)
        
        # Apply any active filters
        self.apply_filters()
    
    def add_new_roll(self, roll_data):
        """Add a new roll from Receive Tab and create QR Code and Label"""
        try:
            from storage import Roll
            
            # Create a new roll object
            roll = Roll(
                roll_id=roll_data['roll_id'],
                sku=roll_data.get('sku', roll_data.get('code', '')),
                lot=roll_data['lot'],
                current_length=float(roll_data.get('length', 0)),
                original_length=float(roll_data.get('length', 0)),
                location=roll_data.get('location', ''),
                grade=roll_data.get('grade', 'A'),
                date_received=roll_data.get('date_received', datetime.now().strftime("%Y-%m-%d")),
                status='active',
                specification=roll_data.get('specifications', roll_data.get('specification', roll_data.get('description', ''))),
                colour=roll_data.get('colour', ''),
                packing_unit=roll_data.get('package_unit', roll_data.get('packing_unit', roll_data.get('unit_type', 'MTS'))),
                unit_type=roll_data.get('unit_type', 'MTS'),
                type_of_roll=roll_data.get('type_of_roll', ''),
                marks_no=roll_data.get('marks_no', ''),
                invoice_number=roll_data.get('invoice_number', ''),
                po_number=roll_data.get('po_number', ''),
                spl_name=roll_data.get('spl_name', roll_data.get('supplier_name', '')),
                pdt_code=roll_data.get('pdt_code', roll_data.get('code', '')),
                pdt_name=roll_data.get('pdt_name', roll_data.get('description', roll_data.get('product', ''))),
                subpart_code=roll_data.get('subpart_code', roll_data.get('spl_part_code', '')),
                sup_code=roll_data.get('sup_code', roll_data.get('spl_code', '')),
                width=roll_data.get('width', '')
            )
            
            # Add to storage
            if self.storage.add_roll(roll):
                # Add log entry
                self.storage.add_log(
                    action="roll_received",
                    roll_id=roll.roll_id,
                    details={
                        'sku': roll.sku,
                        'lot': roll.lot,
                        'length': roll.original_length,
                        'location': roll.location
                    }
                )
                
                # Reload data to show new roll
                self.load_data()
                
                # Ask if user wants to create QR Code and Label
                # reply = QMessageBox.question(
                #     self,
                #     "สร้าง QR Code และฉลาก / Create QR Code and Label",
                #     f"ต้องการสร้าง QR Code และฉลากสำหรับม้วน {roll.roll_id} หรือไม่?\n\n"
                #     f"Do you want to create QR Code and label for roll {roll.roll_id}?",
                #     QMessageBox.Yes | QMessageBox.No,
                #     QMessageBox.Yes
                # )
                
                # if reply == QMessageBox.Yes:
                #     self.create_qr_and_label(roll)
            else:
                QMessageBox.warning(
                    self,
                    "ข้อผิดพลาด / Error",
                    f"ไม่สามารถเพิ่มม้วน {roll_data['roll_id']} ได้\n\n"
                    f"Failed to add roll {roll_data['roll_id']}.\n"
                    f"A roll with this ID may already exist."
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "ข้อผิดพลาด / Error",
                f"เกิดข้อผิดพลาดในการเพิ่มม้วน:\n\nError adding roll:\n{str(e)}"
            )
    
    def create_qr_and_label(self, roll):
        """Create QR Code and Label for the roll"""
        try:
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(roll.roll_id)
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Ask what to do with the QR code and label
            reply = QMessageBox.question(
                self,
                "บันทึกหรือพิมพ์ / Save or Print",
                f"ต้องการพิมพ์ฉลากหรือบันทึกเป็นไฟล์?\n\n"
                f"Do you want to print the label or save it as a file?",
                QMessageBox.StandardButton(0x00000400) |  # Yes (Print)
                QMessageBox.StandardButton(0x00000001) |  # Save
                QMessageBox.Cancel,
                QMessageBox.StandardButton(0x00000400)
            )
            
            if reply == QMessageBox.StandardButton(0x00000400):  # Print
                self.print_label_for_roll(roll, qr_img)
            elif reply == QMessageBox.StandardButton(0x00000001):  # Save
                self.save_qr_code(qr_img, roll.roll_id)
        except Exception as e:
            QMessageBox.critical(
                self,
                "ข้อผิดพลาด / Error",
                f"เกิดข้อผิดพลาดในการสร้าง QR Code:\n\nError creating QR Code:\n{str(e)}"
            )
    
    def print_label_for_roll(self, roll, qr_img):
        """Print label for the roll"""
        try:
            QMessageBox.information(
                self,
                "พิมพ์ / Print",
                f"ฉลากสำหรับม้วน {roll.roll_id} พร้อมที่จะพิมพ์\n\n"
                f"Label for roll {roll.roll_id} is ready to print.\n"
                f"(ฟีเจอร์นี้จะเพิ่มเติมในภายหลัง)"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "ข้อผิดพลาด / Error",
                f"เกิดข้อผิดพลาดในการพิมพ์:\n\nError printing:\n{str(e)}"
            )
    
    def save_qr_code(self, qr_image, roll_id):
        """Save QR code to file"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "บันทึก QR Code / Save QR Code",
                f"QR_{roll_id}.png",
                "PNG Files (*.png);;All Files (*)"
            )
            
            if filename:
                if not filename.lower().endswith('.png'):
                    filename += '.png'
                
                qr_image.save(filename)
                QMessageBox.information(
                    self,
                    "สำเร็จ / Success",
                    f"บันทึก QR Code เป็น {filename} สำเร็จ!\n\n"
                    f"QR Code saved as {filename}"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "ข้อผิดพลาด / Error",
                f"เกิดข้อผิดพลาดในการบันทึก:\n\nError saving:\n{str(e)}"
            )
    
    def update_filters(self):
        """Update filter dropdowns with unique values"""
        # Store current selections
        current_sku = self.sku_filter.currentText()
        current_location = self.location_filter.currentText()
        
        # Clear and update SKU filter
        self.sku_filter.clear()
        self.sku_filter.addItem("")  # Empty option for no filter
        skus = sorted(list(set(roll.sku for roll in self.rolls)))
        self.sku_filter.addItems(skus)
        
        # Restore selection if possible
        if current_sku in skus:
            self.sku_filter.setCurrentText(current_sku)
        
        # Clear and update location filter
        self.location_filter.clear()
        self.location_filter.addItem("")  # Empty option for no filter
        locations = sorted(list(set(roll.location for roll in self.rolls if roll.location)))
        self.location_filter.addItems(locations)
        
        # Restore selection if possible
        if current_location in locations:
            self.location_filter.setCurrentText(current_location)
    
    def add_roll_to_table(self, roll):
        """Add a single roll to the table"""
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Add checkbox for selection
        item = QTableWidgetItem()
        item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
        item.setCheckState(Qt.CheckState.Unchecked)
        self.table.setItem(row, 0, item)
        
        # Add roll data
        self.table.setItem(row, 1, QTableWidgetItem(roll.roll_id))
        self.table.setItem(row, 2, QTableWidgetItem(roll.pdt_code or roll.sku))  # Code
        self.table.setItem(row, 3, QTableWidgetItem(roll.subpart_code or ""))  # SubPartCode
        self.table.setItem(row, 4, QTableWidgetItem(roll.sup_code or ""))  # SupCode
        self.table.setItem(row, 5, QTableWidgetItem(roll.spl_name))  # Supplier Name
        self.table.setItem(row, 6, QTableWidgetItem(roll.pdt_name or roll.specification))  # Description
        self.table.setItem(row, 7, QTableWidgetItem(roll.lot))  # Lot No.
        self.table.setItem(row, 8, QTableWidgetItem(roll.location))  # Location
        
        # Status with color coding
        status_item = QTableWidgetItem(roll.status.capitalize())
        if roll.status == 'active':
            status_item.setForeground(Qt.GlobalColor.darkGreen)
        else:
            status_item.setForeground(Qt.GlobalColor.darkRed)
        self.table.setItem(row, 9, status_item)
    
    def apply_filters(self):
        """Apply filters to the table"""
        sku_filter = self.sku_filter.currentText().lower()
        status_filter = self.status_filter.currentData()
        location_filter = self.location_filter.currentText().lower()
        search_text = self.search_input.text().lower()
        
        for row in range(self.table.rowCount()):
            should_show = True
            
            # Get row data
            sku = self.table.item(row, 2).text().lower()
            status = self.table.item(row, 7).text().lower()
            location = self.table.item(row, 6).text().lower()
            roll_id = self.table.item(row, 1).text().lower()
            lot = self.table.item(row, 3).text().lower()
            
            # Apply filters
            if sku_filter and sku_filter not in sku:
                should_show = False
            
            if status_filter and status != status_filter:
                should_show = False
            
            if location_filter and location_filter not in location:
                should_show = False
            
            if search_text and not (search_text in roll_id or search_text in sku or search_text in lot):
                should_show = False
            
            # Show/hide row
            self.table.setRowHidden(row, not should_show)
    
    def on_selection_changed(self):
        """Handle row selection changes"""
        selected = len(self.table.selectedItems()) > 0
        self.cut_btn.setEnabled(selected)
        self.print_label_btn.setEnabled(selected)
    
    def refresh_data(self):
        """Refresh the table data"""
        self.load_data()
    
    def get_selected_roll_id(self):
        """Get the roll ID of the selected row"""
        selected = self.table.selectedItems()
        if not selected:
            return None
        
        # Return the roll ID from the first selected cell's row
        row = selected[0].row()
        return self.table.item(row, 1).text()
    
    def cut_roll(self):
        """Show dialog to cut a roll"""
        roll_id = self.get_selected_roll_id()
        if not roll_id:
            return
        
        # Get the roll
        roll = self.storage.get_roll(roll_id)
        if not roll:
            QMessageBox.warning(self, "Error", "Selected roll not found!")
            return
        
        # Show cut dialog
        dialog = CutRollDialog(roll, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            cut_length = dialog.get_cut_length()
            
            # Perform the cut
            if self.storage.cut_roll(roll_id, cut_length):
                QMessageBox.information(
                    self,
                    "Success",
                    f"Successfully cut {cut_length:.2f} from roll {roll_id}"
                )
                self.refresh_data()
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to cut roll. Make sure the cut length is valid."
                )
    
    def print_label(self):
        """Print label for selected roll"""
        roll_id = self.get_selected_roll_id()
        if not roll_id:
            return
        
        # Get the roll
        roll = self.storage.get_roll(roll_id)
        if not roll:
            QMessageBox.warning(self, "Error", "Selected roll not found!")
            return
        print("------- role ----")
        print(roll)
        # Convert roll to dict for preview dialog
        # roll_data = {
        #     'roll_id': roll.roll_id,
        #     'sku': roll.sku,
        #     'pdt_code': roll.pdt_code,
        #     'lot': roll.lot,
        #     'date_received': roll.date_received,
        #     'specification': roll.specification,
        #     'pdt_name': roll.pdt_name,
        #     'product_name': roll.pdt_name,
        #     'colour': roll.colour,
        #     'packing_unit': roll.packing_unit,
        #     'package_unit': roll.packing_unit,
        #     'unit_type': roll.unit_type,
        #     'grade': roll.grade,
        #     'type_of_roll': roll.type_of_roll,
        #     'marks_no': roll.marks_no,
        #     'current_length': roll.current_length,
        #     'width': getattr(roll, 'width', ''),
        #     'spl_name': roll.spl_name
        # }
        
        # Generate and show print preview
        preview = LabelPreviewDialog(self, roll_data=roll)
        preview.exec()
    
    def export_data(self):
        """Export rolls data to CSV"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Rolls",
            f"rolls_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            # Get all visible rows
            rows = []
            for row in range(self.table.rowCount()):
                if not self.table.isRowHidden(row):
                    rows.append([
                        self.table.item(row, 1).text(),  # Roll ID
                        self.table.item(row, 2).text(),  # SKU
                        self.table.item(row, 3).text(),  # Lot
                        self.table.item(row, 4).text(),  # Current Length
                        self.table.item(row, 5).text(),  # Original Length
                        self.table.item(row, 6).text(),  # Location
                        self.table.item(row, 7).text()   # Status
                    ])
            
            # Write to CSV
            import csv
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Roll ID', 'SKU', 'Lot', 'Current Length', 
                    'Original Length', 'Location', 'Status'
                ])
                writer.writerows(rows)
            
            QMessageBox.information(
                self,
                "Export Successful",
                f"Successfully exported {len(rows)} rolls to:\n{file_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"An error occurred while exporting to CSV:\n{str(e)}"
            )


class CutRollDialog(QDialog):
    """Dialog for cutting a roll"""
    def __init__(self, roll, parent=None):
        super().__init__(parent)
        self.roll = roll
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the dialog UI"""
        self.setWindowTitle(f"Cut Roll: {self.roll.roll_id}")
        self.setMinimumWidth(300)
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # Current roll info
        self.info_label = QLabel(
            f"<b>Roll ID:</b> {self.roll.roll_id}<br>"
            f"<b>Current Length:</b> {self.roll.current_length:.2f} m"
        )
        
        # Cut length input
        self.cut_length = QDoubleSpinBox()
        self.cut_length.setRange(0.01, self.roll.current_length)
        self.cut_length.setValue(1.0)
        self.cut_length.setSuffix(" m")
        self.cut_length.setDecimals(2)
        self.cut_length.setSingleStep(0.5)
        
        # Remaining length display
        self.remaining_label = QLabel(
            f"Remaining: {self.roll.current_length - self.cut_length.value():.2f} m"
        )
        self.cut_length.valueChanged.connect(
            lambda: self.remaining_label.setText(
                f"Remaining: {self.roll.current_length - self.cut_length.value():.2f} m"
            )
        )
        
        # Notes
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Optional notes...")
        
        # Add to form
        form_layout.addRow(self.info_label)
        form_layout.addRow("Cut Length:", self.cut_length)
        form_layout.addRow(self.remaining_label)
        form_layout.addRow("Notes:", self.notes_input)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # Add to main layout
        layout.addLayout(form_layout)
        layout.addWidget(button_box)
    
    def get_cut_length(self):
        """Get the cut length from the dialog"""
        return self.cut_length.value()
    
    def get_notes(self):
        """Get the notes from the dialog"""
        return self.notes_input.text().strip()
