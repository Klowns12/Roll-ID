from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QMessageBox, QFileDialog, QInputDialog,
    QLabel, QLineEdit, QDialog, QDialogButtonBox, QFormLayout
)
from PySide6.QtCore import Qt, QSortFilterProxyModel, QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator
import pandas as pd
import os
from storage import MasterProduct

class MasterTab(QWidget):
    def __init__(self, storage):
        super().__init__()
        self.storage = storage
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Set up the Master Data tab UI"""
        layout = QVBoxLayout(self)
        
        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by SKU or description...")
        self.search_input.textChanged.connect(self.filter_table)
        
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("Add Product")
        self.add_btn.clicked.connect(self.add_product)
        
        self.edit_btn = QPushButton("Edit Selected")
        self.edit_btn.clicked.connect(self.edit_product)
        
        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self.delete_product)
        
        self.import_btn = QPushButton("Import from File")
        self.import_btn.clicked.connect(self.import_from_file)
        
        self.export_btn = QPushButton("Export to CSV")
        self.export_btn.clicked.connect(self.export_to_csv)
        
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.import_btn)
        btn_layout.addWidget(self.export_btn)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["SKU", "Description", "Default Length", "Default Grade"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Add widgets to layout
        layout.addLayout(search_layout)
        layout.addLayout(btn_layout)
        layout.addWidget(self.table)
        
        # Set column widths
        self.table.setColumnWidth(0, 150)  # SKU
        self.table.setColumnWidth(1, 400)  # Description
        self.table.setColumnWidth(2, 150)  # Default Length
        self.table.setColumnWidth(3, 150)  # Default Grade
    
    def load_data(self):
        """Load master products into the table"""
        self.table.setRowCount(0)
        
        # Get all master products
        products = self.storage.get_all_master_products()
        
        # Add products to table
        for product in products:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(product.sku))
            self.table.setItem(row, 1, QTableWidgetItem(product.description))
            self.table.setItem(row, 2, QTableWidgetItem(f"{product.default_length:.2f}"))
            self.table.setItem(row, 3, QTableWidgetItem(product.default_grade))
    
    def filter_table(self):
        """Filter the table based on search text"""
        search_text = self.search_input.text().lower()
        
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and search_text in item.text().lower():
                    match = True
                    break
            
            self.table.setRowHidden(row, not match)
    
    def add_product(self):
        """Show add product dialog"""
        dialog = ProductDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            product_data = dialog.get_product_data()
            
            # Create new product
            product = MasterProduct(
                sku=product_data['sku'],
                description=product_data['description'],
                default_length=float(product_data['default_length']),
                default_grade=product_data['default_grade']
            )
            
            # Add to storage
            if self.storage.add_master_product(product):
                self.load_data()
                QMessageBox.information(self, "Success", "Product added successfully!")
            else:
                QMessageBox.warning(self, "Error", "A product with this SKU already exists!")
    
    def edit_product(self):
        """Edit selected product"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a product to edit.")
            return
        
        row = selected[0].row()
        sku = self.table.item(row, 0).text()
        
        # Get current product data
        product = self.storage.get_master_product(sku)
        if not product:
            QMessageBox.warning(self, "Error", "Selected product not found!")
            return
        
        # Show edit dialog
        dialog = ProductDialog(self, edit_mode=True)
        dialog.set_product_data({
            'sku': product.sku,
            'description': product.description,
            'default_length': str(product.default_length),
            'default_grade': product.default_grade
        })
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            product_data = dialog.get_product_data()
            
            # Update product (in a real app, you would have an update method in storage)
            # For now, we'll delete and re-add
            # In a real implementation, you should have an update_master_product method
            
            # This is a workaround since we don't have an update method
            # In a real app, you would call storage.update_master_product()
            
            # For now, we'll just show a message
            QMessageBox.information(
                self,
                "Edit Product",
                f"In a full implementation, the product {product_data['sku']} would be updated here."
            )
    
    def delete_product(self):
        """Delete selected product"""
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a product to delete.")
            return
        
        row = selected[0].row()
        sku = self.table.item(row, 0).text()
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            'Confirm Deletion',
            f'Are you sure you want to delete product {sku}?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # In a real app, you would call storage.delete_master_product(sku)
            # For now, we'll just show a message
            QMessageBox.information(
                self,
                "Delete Product",
                f"In a full implementation, the product {sku} would be deleted here."
            )
            # self.load_data()  # Refresh the table
    
    def import_from_file(self):
        """Import products from CSV or Excel file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Products",
            "",
            "CSV Files (*.csv);;Excel Files (*.xlsx *.xls)"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            if file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                df = pd.read_csv(file_path)
            
            # Normalize column names (lowercase, strip whitespace)
            df.columns = df.columns.str.lower().str.strip()
            
            # Map column names (support multiple naming conventions)
            column_mapping = {
                'pdt_code': 'sku',
                'pdt_name': 'description1',
                'pdt_name_en': 'description2',
                'unit_cost': 'default_length',
                'pdt_color': 'color',
                'pdt_size': 'size',
                'location': 'location'
            }
            
            # Rename columns based on mapping
            df = df.rename(columns=column_mapping)
            
            # Check required columns
            required_columns = ['sku', 'description1']
            available_columns = df.columns.tolist()
            missing_columns = [col for col in required_columns if col not in available_columns]
            
            if missing_columns:
                QMessageBox.critical(
                    self,
                    "Import Error",
                    f"Missing required columns: {', '.join(missing_columns)}\n\n"
                    f"Required: sku (or pdt_code), description (or pdt_name)\n"
                    f"Optional: default_length (or unit_cost), default_grade"
                )
                return
            
            # Process each row
            success_count = 0
            error_count = 0
            
            for idx, row in df.iterrows():
                try:
                    sku = str(row['sku']).strip()
            
                    description = str(row['description1']).strip()
                    # Use default_length if available, otherwise use unit_cost
                    default_length = -1
                    default_grade = "-"
                    
                    # Skip if SKU is empty
                    if not sku:
                        error_count += 1
                        continue
                    
                
                    # Create product
                    product = MasterProduct(
                        sku=sku,
                        description=description,
                        default_length=default_length,
                        default_grade=default_grade
                    )
                    
                    # Add to storage
                    if self.storage.add_master_product(product):
                        success_count += 1
                    else:
                        error_count += 1
                
                except Exception as e:
                    error_count += 1
                    print(f"Error importing row {idx}: {str(e)}")
            
            # Show results
            msg = f"Import complete!\n\n" \
                  f"Successfully imported: {success_count}\n" \
                  f"Failed: {error_count}"
            
            QMessageBox.information(self, "Import Results", msg)
            
            # Refresh the table
            self.load_data()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Error",
                f"An error occurred while importing the file:\n{str(e)}"
            )
    
    def export_to_csv(self):
        """Export products to CSV file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Products",
            "products_export.csv",
            "CSV Files (*.csv)"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            # Get all products
            products = self.storage.get_all_master_products()
            
            # Convert to DataFrame
            data = []
            for product in products:
                data.append({
                    'sku': product.sku,
                    'description': product.description,
                    'default_length': product.default_length,
                    'default_grade': product.default_grade
                })
            
            df = pd.DataFrame(data)
            
            # Save to CSV with utf-8-sig encoding (รองรับภาษาไทย)
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            
            QMessageBox.information(
                self,
                "Export Successful",
                f"Successfully exported {len(products)} products to:\n{file_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"An error occurred while exporting to CSV:\n{str(e)}"
            )


class ProductDialog(QDialog):
    """Dialog for adding/editing products"""
    def __init__(self, parent=None, edit_mode=False):
        super().__init__(parent)
        self.edit_mode = edit_mode
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the dialog UI"""
        self.setWindowTitle("Add New Product" if not self.edit_mode else "Edit Product")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # SKU
        self.sku_input = QLineEdit()
        self.sku_input.setPlaceholderText("e.g., FAB-001")
        
        # Description
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("e.g., Cotton Fabric - Blue")
        
        # Default Length
        self.length_input = QLineEdit()
        self.length_input.setPlaceholderText("e.g., 100.0")
        
        # Only allow numbers and decimal point
        float_validator = QRegularExpressionValidator(QRegularExpression(r"^\d*\.?\d+$"))
        self.length_input.setValidator(float_validator)
        
        # Default Grade
        self.grade_input = QLineEdit()
        self.grade_input.setPlaceholderText("e.g., A")
        self.grade_input.setMaxLength(1)
        
        # Add fields to form
        form_layout.addRow("SKU*:", self.sku_input)
        form_layout.addRow("Description*:", self.desc_input)
        form_layout.addRow("Default Length (m)*:", self.length_input)
        form_layout.addRow("Default Grade:", self.grade_input)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        
        # Add to main layout
        layout.addLayout(form_layout)
        layout.addWidget(QLabel("* Required fields"))
        layout.addWidget(button_box)
        
        # Disable SKU field in edit mode
        if self.edit_mode:
            self.sku_input.setReadOnly(True)
    
    def set_product_data(self, data):
        """Set the form fields with product data"""
        self.sku_input.setText(data.get('sku', ''))
        self.desc_input.setText(data.get('description', ''))
        self.length_input.setText(str(data.get('default_length', '')))
        self.grade_input.setText(data.get('default_grade', 'A'))
    
    def get_product_data(self):
        """Get the product data from form fields"""
        return {
            'sku': self.sku_input.text().strip(),
            'description': self.desc_input.text().strip(),
            'default_length': self.length_input.text().strip() or '0',
            'default_grade': self.grade_input.text().strip() or 'A'
        }
    
    def validate_and_accept(self):
        """Validate the form before accepting"""
        data = self.get_product_data()
        
        # Validate required fields
        if not data['sku']:
            QMessageBox.warning(self, "Validation Error", "SKU is required!")
            self.sku_input.setFocus()
            return
        
        if not data['description']:
            QMessageBox.warning(self, "Validation Error", "Description is required!")
            self.desc_input.setFocus()
            return
        
        if not data['default_length'] or float(data['default_length']) <= 0:
            QMessageBox.warning(self, "Validation Error", "Please enter a valid length greater than 0!")
            self.length_input.setFocus()
            return
        
        # If we got here, all validations passed
        self.accept()
