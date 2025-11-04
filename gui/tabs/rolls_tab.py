from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QMessageBox, QFileDialog, QInputDialog,
    QLabel, QLineEdit, QDialog, QDialogButtonBox, QFormLayout,
    QComboBox, QGroupBox, QSpinBox, QDoubleSpinBox, QToolBar, QStatusBar
)
from PySide6.QtCore import Qt, QSortFilterProxyModel, QRegularExpression, QDate
from PySide6.QtGui import QRegularExpressionValidator, QAction, QIcon
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
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "",  # For selection
            "Roll ID",
            "SKU",
            "Lot",
            "Current Length",
            "Original Length",
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
        self.table.setItem(row, 2, QTableWidgetItem(roll.sku))
        self.table.setItem(row, 3, QTableWidgetItem(roll.lot))
        self.table.setItem(row, 4, QTableWidgetItem(f"{roll.current_length:.2f}"))
        self.table.setItem(row, 5, QTableWidgetItem(f"{roll.original_length:.2f}"))
        self.table.setItem(row, 6, QTableWidgetItem(roll.location))
        
        # Status with color coding
        status_item = QTableWidgetItem(roll.status.capitalize())
        if roll.status == 'active':
            status_item.setForeground(Qt.GlobalColor.darkGreen)
        else:
            status_item.setForeground(Qt.GlobalColor.darkRed)
        self.table.setItem(row, 7, status_item)
    
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
        
        # Generate and show print preview
        preview = LabelPreviewDialog(roll, self)
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


class LabelPreviewDialog(QDialog):
    """Dialog for previewing and printing labels"""
    def __init__(self, roll, parent=None):
        super().__init__(parent)
        self.roll = roll
        self.setup_ui()
        self.generate_preview()
    
    def setup_ui(self):
        """Set up the dialog UI"""
        self.setWindowTitle(f"Label Preview: {self.roll.roll_id}")
        self.setMinimumSize(600, 800)
        
        layout = QVBoxLayout(self)
        
        # Preview area
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("background-color: white;")
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.print_btn = QPushButton("Print Label")
        self.print_btn.clicked.connect(self.print_label)
        
        self.save_pdf_btn = QPushButton("Save as PDF")
        self.save_pdf_btn.clicked.connect(self.save_as_pdf)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.print_btn)
        btn_layout.addWidget(self.save_pdf_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.close_btn)
        
        # Add to layout
        layout.addWidget(self.preview_label)
        layout.addLayout(btn_layout)
    
    def generate_preview(self):
        """Generate a preview of the label"""
        # Create a temporary file for the preview
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=4,
                border=2,
            )
            
            # Create QR code data
            qr_data = {
                'id': self.roll.roll_id,
                'sku': self.roll.sku,
                'lot': self.roll.lot,
                'length': self.roll.current_length,
                'date': self.roll.date_received
            }
            qr.add_data(json.dumps(qr_data, indent=2))
            qr.make(fit=True)
            
            # Create QR code image
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_img.save(tmp_file.name)
            
            # Load the image and scale it for preview
            pixmap = QPixmap(tmp_file.name)
            scaled_pixmap = pixmap.scaled(
                300, 300,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Set the preview image
            self.preview_label.setPixmap(scaled_pixmap)
            
            # Clean up
            os.unlink(tmp_file.name)
    
    def print_label(self):
        """Print the label"""
        # In a real implementation, this would send the label to a printer
        QMessageBox.information(
            self,
            "Print Label",
            f"In a full implementation, this would print the label for {self.roll.roll_id}"
        )
    
    def save_as_pdf(self):
        """Save the label as a PDF file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Label as PDF",
            f"label_{self.roll.roll_id}.pdf",
            "PDF Files (*.pdf)"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            # Create PDF
            c = canvas.Canvas(file_path, pagesize=A4)
            width, height = A4
            
            # Draw border
            c.setLineWidth(1)
            c.rect(20*mm, 20*mm, width-40*mm, height-40*mm)
            
            # Add title
            c.setFont("Helvetica-Bold", 16)
            c.drawCentredString(width/2, height-30*mm, "Fabric Roll Label")
            
            # Add roll info
            c.setFont("Helvetica", 12)
            y_pos = height - 50*mm
            c.drawString(30*mm, y_pos, f"Roll ID: {self.roll.roll_id}")
            y_pos -= 8*mm
            c.drawString(30*mm, y_pos, f"SKU: {self.roll.sku}")
            y_pos -= 8*mm
            c.drawString(30*mm, y_pos, f"Lot: {self.roll.lot}")
            y_pos -= 8*mm
            c.drawString(30*mm, y_pos, f"Length: {self.roll.current_length:.2f} m")
            y_pos -= 8*mm
            c.drawString(30*mm, y_pos, f"Date: {self.roll.date_received}")
            
            # Add QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=4,
                border=2,
            )
            
            # Create QR code data
            qr_data = {
                'id': self.roll.roll_id,
                'sku': self.roll.sku,
                'lot': self.roll.lot,
                'length': self.roll.current_length,
                'date': self.roll.date_received
            }
            qr.add_data(json.dumps(qr_data, indent=2))
            qr.make(fit=True)
            
            # Create QR code image in memory
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Save QR code to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                qr_img.save(tmp_file.name)
                # Add QR code to PDF
                c.drawImage(
                    tmp_file.name,
                    width - 70*mm,
                    height - 100*mm,
                    width=40*mm,
                    height=40*mm,
                    preserveAspectRatio=True
                )
                # Clean up
                os.unlink(tmp_file.name)
            
            # Add barcode
            barcode_value = self.roll.roll_id
            barcode = code128.Code128(
                barcode_value,
                barHeight=20*mm,
                barWidth=1.2
            )
            
            # Draw barcode
            barcode.drawOn(c, 30*mm, 30*mm)
            c.setFont("Helvetica", 10)
            c.drawCentredString(
                width/2,
                25*mm,
                barcode_value
            )
            
            # Save the PDF
            c.save()
            
            QMessageBox.information(
                self,
                "PDF Saved",
                f"Label saved as:\n{file_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save PDF:\n{str(e)}"
            )
