from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QComboBox, QPushButton, QMessageBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QDoubleSpinBox,
    QDateEdit, QCheckBox, QFileDialog, QInputDialog
)
from PySide6.QtCore import Qt, QDate, Signal as pyqtSignal
from PySide6.QtGui import QIntValidator, QDoubleValidator
import qrcode
from io import BytesIO
import json
from datetime import datetime
import tempfile
import os

class ReceiveTab(QWidget):
    # Signal emitted when a new roll is received
    roll_received = pyqtSignal(dict)
    
    def __init__(self, storage):
        super().__init__()
        self.storage = storage
        self.setup_ui()
        self.load_master_data()
        
        # Connect signals
        self.roll_received.connect(self.on_roll_received)
    
    def setup_ui(self):
        """Set up the Receive tab UI"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Create tabs
        self.manual_tab = self.create_manual_tab()
        self.master_tab = self.create_master_tab()
        self.import_tab = self.create_import_tab()
        
        # Add tabs
        self.tabs.addTab(self.manual_tab, "Manual Entry")
        self.tabs.addTab(self.master_tab, "From Master")
        self.tabs.addTab(self.import_tab, "Import from File")
        
        # Add tabs to layout
        layout.addWidget(self.tabs)
    
    def create_manual_tab(self):
        """Create the manual entry tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Form group
        form_group = QGroupBox("Roll Information")
        form_layout = QFormLayout()
        
        # SKU
        self.manual_sku = QLineEdit()
        self.manual_sku.setPlaceholderText("e.g., FAB-001")
        
        # Lot
        self.manual_lot = QLineEdit()
        self.manual_lot.setPlaceholderText("e.g., LOT2023-001")
        
        # Length
        self.manual_length = QDoubleSpinBox()
        self.manual_length.setRange(0.01, 10000.0)
        self.manual_length.setValue(100.0)
        self.manual_length.setSuffix(" m")
        self.manual_length.setDecimals(2)
        
        # Width (optional)
        self.manual_width = QDoubleSpinBox()
        self.manual_width.setRange(0.0, 100.0)
        self.manual_width.setValue(1.5)
        self.manual_width.setSuffix(" m")
        self.manual_width.setDecimals(2)
        
        # Grade
        self.manual_grade = QComboBox()
        self.manual_grade.addItems(["A", "B", "C", "D"])
        
        # Location
        self.manual_location = QLineEdit()
        self.manual_location.setPlaceholderText("e.g., Warehouse A, Rack 1")
        
        # Date received
        self.manual_date = QDateEdit()
        self.manual_date.setCalendarPopup(True)
        self.manual_date.setDate(QDate.currentDate())
        
        # Notes
        self.manual_notes = QLineEdit()
        self.manual_notes.setPlaceholderText("Optional notes...")
        
        # Add fields to form
        form_layout.addRow("SKU*:", self.manual_sku)
        form_layout.addRow("Lot*:", self.manual_lot)
        form_layout.addRow("Length*:", self.manual_length)
        form_layout.addRow("Width:", self.manual_width)
        form_layout.addRow("Grade:", self.manual_grade)
        form_layout.addRow("Location:", self.manual_location)
        form_layout.addRow("Date Received:", self.manual_date)
        form_layout.addRow("Notes:", self.manual_notes)
        
        form_group.setLayout(form_layout)
        
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
    
    def create_master_tab(self):
        """Create the 'From Master' tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Master product selection
        master_group = QGroupBox("Select Master Product")
        master_layout = QVBoxLayout()
        
        # Product filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        
        self.master_filter = QLineEdit()
        self.master_filter.setPlaceholderText("Filter by SKU or description...")
        self.master_filter.textChanged.connect(self.filter_master_products)
        
        filter_layout.addWidget(self.master_filter)
        master_layout.addLayout(filter_layout)
        
        # Master products table
        self.master_table = QTableWidget()
        self.master_table.setColumnCount(4)
        self.master_table.setHorizontalHeaderLabels(["", "SKU", "Description", "Default Length"])
        self.master_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.master_table.verticalHeader().setVisible(False)
        self.master_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.master_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.master_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        master_layout.addWidget(self.master_table)
        master_group.setLayout(master_layout)
        
        # Form for roll details
        form_group = QGroupBox("Roll Details")
        form_layout = QFormLayout()
        
        # Lot
        self.master_lot = QLineEdit()
        self.master_lot.setPlaceholderText("e.g., LOT2023-001")
        
        # Length (can override default)
        self.master_length = QDoubleSpinBox()
        self.master_length.setRange(0.01, 10000.0)
        self.master_length.setValue(100.0)
        self.master_length.setSuffix(" m")
        self.master_length.setDecimals(2)
        
        # Use default length checkbox
        self.use_default_length = QCheckBox("Use default length")
        self.use_default_length.setChecked(True)
        self.use_default_length.toggled.connect(self.toggle_use_default_length)
        
        # Location
        self.master_location = QLineEdit()
        self.master_location.setPlaceholderText("e.g., Warehouse A, Rack 1")
        
        # Date received
        self.master_date = QDateEdit()
        self.master_date.setCalendarPopup(True)
        self.master_date.setDate(QDate.currentDate())
        
        # Notes
        self.master_notes = QLineEdit()
        self.master_notes.setPlaceholderText("Optional notes...")
        
        # Add fields to form
        form_layout.addRow("Lot*:", self.master_lot)
        form_layout.addRow("Length*:", self.master_length)
        form_layout.addRow("", self.use_default_length)
        form_layout.addRow("Location:", self.master_location)
        form_layout.addRow("Date Received:", self.master_date)
        form_layout.addRow("Notes:", self.master_notes)
        
        form_group.setLayout(form_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.master_clear_btn = QPushButton("Clear")
        self.master_clear_btn.clicked.connect(self.clear_master_form)
        
        self.master_submit_btn = QPushButton("Save Roll")
        self.master_submit_btn.clicked.connect(self.submit_master_form)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.master_clear_btn)
        btn_layout.addWidget(self.master_submit_btn)
        
        # Add to layout
        layout.addWidget(master_group, 2)
        layout.addWidget(form_group, 1)
        layout.addLayout(btn_layout)
        
        return tab
    
    def create_import_tab(self):
        """Create the import from file tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Import instructions
        instructions = QLabel(
            "Import rolls from a CSV or Excel file. The file should contain the following columns:\n"
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
        self.import_btn = QPushButton("Select File to Import...")
        self.import_btn.clicked.connect(self.import_from_file)
        
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
        layout.addWidget(instructions)
        layout.addWidget(self.import_btn)
        layout.addWidget(self.import_table)
        
        return tab
    
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
        self.manual_sku.clear()
        self.manual_lot.clear()
        self.manual_length.setValue(100.0)
        self.manual_width.setValue(1.5)
        self.manual_grade.setCurrentIndex(0)
        self.manual_location.clear()
        self.manual_date.setDate(QDate.currentDate())
        self.manual_notes.clear()
    
    def clear_master_form(self):
        """Clear the master entry form"""
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
        if not self.manual_sku.text().strip():
            QMessageBox.warning(self, "Validation Error", "SKU is required!")
            self.manual_sku.setFocus()
            return
        
        if not self.manual_lot.text().strip():
            QMessageBox.warning(self, "Validation Error", "Lot number is required!")
            self.manual_lot.setFocus()
            return
        
        # Generate roll ID (format: SKU-LOT-001)
        sku = self.manual_sku.text().strip().upper()
        lot = self.manual_lot.text().strip().upper()
        roll_id = f"{sku}-{lot}-001"  # Simple implementation - in a real app, you'd check for existing IDs
        
        # Create roll data
        roll_data = {
            'roll_id': roll_id,
            'sku': sku,
            'lot': lot,
            'length': self.manual_length.value(),
            'default_length': self.manual_length.value(),  # Add default_length
            'width': self.manual_width.value(),
            'grade': self.manual_grade.currentText(),
            'location': self.manual_location.text().strip(),
            'date_received': self.manual_date.date().toString("yyyy-MM-dd"),
            'notes': self.manual_notes.text().strip()
        }
        
        # Emit signal with roll data
        self.roll_received.emit(roll_data)
    
    def submit_master_form(self):
        """Submit the master entry form"""
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
        
        # Generate roll ID (format: SKU-LOT-001)
        lot = self.master_lot.text().strip().upper()
        roll_id = f"{sku}-{lot}-001"  # Simple implementation - in a real app, you'd check for existing IDs
        
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
    
    def import_from_file(self):
        """Import rolls from a file"""
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
            
            # Check required columns
            required_columns = ['sku', 'lot', 'length']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                QMessageBox.critical(
                    self,
                    "Import Error",
                    f"Missing required columns: {', '.join(missing_columns)}"
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
        success_count = 0
        
        for _, row in df.iterrows():
            try:
                # Generate roll ID (format: SKU-LOT-001)
                sku = str(row['sku']).strip().upper()
                lot = str(row['lot']).strip().upper()
                roll_id = f"{sku}-{lot}-001"  # Simple implementation
                
                # Create roll data
                roll_data = {
                    'roll_id': roll_id,
                    'sku': sku,
                    'lot': lot,
                    'length': float(row['length']),
                    'width': float(row.get('width', 1.5)),
                    'grade': str(row.get('grade', 'A')).upper(),
                    'location': str(row.get('location', '')).strip(),
                    'date_received': str(row.get('date_received', datetime.now().strftime("%Y-%m-%d"))),
                    'notes': str(row.get('notes', '')).strip()
                }
                
                # Emit signal with roll data
                self.roll_received.emit(roll_data)
                success_count += 1
                
            except Exception as e:
                print(f"Error importing row {_}: {str(e)}")
        
        # Show results
        QMessageBox.information(
            self,
            "Import Complete",
            f"Successfully imported {success_count} out of {len(df)} rolls."
        )
        
        # Clear the table
        self.import_table.setRowCount(0)
    
    def on_roll_received(self, roll_data):
        """Handle a new roll being received"""
        try:
            # Create a new roll
            roll = self.storage.Roll(
                roll_id=roll_data['roll_id'],
                sku=roll_data['sku'],
                lot=roll_data['lot'],
                current_length=float(roll_data['length']),
                original_length=float(roll_data['length']),
                location=roll_data.get('location', ''),
                grade=roll_data.get('grade', 'A'),
                date_received=roll_data.get('date_received', datetime.now().strftime("%Y-%m-%d")),
                status='active'
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
                
                # Show success message
                QMessageBox.information(
                    self,
                    "Success",
                    f"Roll {roll.roll_id} has been added successfully!"
                )
                
                # Clear the form
                if self.tabs.currentWidget() == self.manual_tab:
                    self.clear_manual_form()
                else:
                    self.clear_master_form()
                
                # Switch to the rolls tab in the main window
                main_window = self.window()
                if hasattr(main_window, 'tab_widget'):
                    main_window.tab_widget.setCurrentIndex(3)  # Assuming rolls tab is at index 3
                
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to add roll. A roll with ID {roll_data['roll_id']} may already exist."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while adding the roll:\n{str(e)}"
            )
