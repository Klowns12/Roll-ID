from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QMessageBox, QFileDialog,
    QLabel, QLineEdit, QDialog, QDialogButtonBox, QFormLayout
)
from PySide6.QtCore import Qt
import pandas as pd
import os

class MasterTab(QWidget):
    def __init__(self, storage):
        super().__init__()
        self.storage = storage
        self.columns = [
            ("pdt_code", "pdt_code"),
            ("pdt_name", "pdt_name"),
            ("unit_type", "unit_type"),
            ("spl_part_code", "spl_part_code"),
            ("scrapqty", "scrapqty"),
            ("create_name", "create_name"),
            ("create_date", "create_date"),
            ("update_name", "update_name"),
            ("update_date", "update_date"),
            ("last_buy_date", "last_buy_date"),
            ("lastdate", "lastdate"),
            ("pg_name", "pg_name"),
            ("cate_name", "cate_name"),
            ("spl_name", "spl_name"),
            ("spl_code", "spl_code"),
        ]
        self.column_keys = [key for _, key in self.columns]
        # Remove pandas-based internal storage, use list of MasterProduct
        self.master_products = [] 
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Set up the Master Data tab UI"""
        layout = QVBoxLayout(self)
        
        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search master data...")
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
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels([label for label, _ in self.columns])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
        
        # Status label for counts
        self.count_label = QLabel("Total: 0 items")
        self.count_label.setStyleSheet("font-weight: bold; color: #555; margin-top: 5px;")
        
        # Add widgets to layout
        layout.addLayout(search_layout)
        layout.addLayout(btn_layout)
        layout.addWidget(self.table)
        layout.addWidget(self.count_label)
        
        # Set column widths
        default_widths = {
            "pdt_code": 140,
            "pdt_name": 220,
            "unit_type": 90,
            "spl_part_code": 120,
            "scrapqty": 90,
            "create_name": 140,
            "create_date": 130,
            "update_name": 140,
            "update_date": 130,
            "last_buy_date": 130,
            "lastdate": 130,
            "pg_name": 140,
            "cate_name": 140,
            "spl_name": 160,
            "spl_code": 120,
        }
        for idx, (label, _) in enumerate(self.columns):
            self.table.setColumnWidth(idx, default_widths.get(label, 120))
    
    def load_data(self):
        """Load master data from database and populate the table"""
        try:
            self.master_products = self.storage.get_all_master_products()
            self._refresh_table()
        except Exception as e:
            QMessageBox.critical(self, "Load Error", f"ไม่สามารถโหลดข้อมูลจากฐานข้อมูลได้:\n{e}")

    def _refresh_table(self):
        self.table.setSortingEnabled(False)  # ปิดชั่วคราวขณะโหลดข้อมูล
        self.table.setRowCount(0)
        
        # เรียงลำดับเริ่มต้นตาม pdt_code
        sorted_products = sorted(self.master_products, key=lambda x: x.pdt_code)
        
        for product in sorted_products:
            table_row = self.table.rowCount()
            self.table.insertRow(table_row)
            
            product_dict = product.to_dict()
            
            for col_idx, (_, column_key) in enumerate(self.columns):
                value = product_dict.get(column_key, "")
                item = QTableWidgetItem()
                
                # ถ้าเป็นคอลัมน์ตัวเลข ให้เก็บข้อมูลเป็นตัวเลขเพื่อให้ Sort ถูกต้อง
                if column_key == "scrapqty":
                    try:
                        num_val = float(value) if value is not None and str(value).strip() != "" else 0.0
                        item.setData(Qt.ItemDataRole.EditRole, num_val)
                    except:
                        item.setText(str(value))
                else:
                    item.setText(str(value))
                
                if col_idx == 0:
                    item.setData(Qt.ItemDataRole.UserRole, product.pdt_code)
                
                self.table.setItem(table_row, col_idx, item)
        
        self.table.setSortingEnabled(True)  # เปิดใช้งาน Sort หลังจากโหลดเสร็จ
        self.count_label.setText(f"Total: {len(sorted_products)} items")

    def _get_selected_pdt_code(self):
        selected = self.table.selectedItems()
        if not selected:
            return None
        row = selected[0].row()
        idx_item = self.table.item(row, 0)
        if not idx_item:
            return None
        return idx_item.data(Qt.ItemDataRole.UserRole)
    
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
        
        # Update count label for filtered results
        visible_rows = sum(1 for row in range(self.table.rowCount()) if not self.table.isRowHidden(row))
        total_rows = self.table.rowCount()
        if search_text:
            self.count_label.setText(f"Showing: {visible_rows} of {total_rows} items")
        else:
            self.count_label.setText(f"Total: {total_rows} items")
    
    def add_product(self):
        """Add new master data to database"""
        dialog = MasterDataDialog(self.columns, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_record = dialog.get_data()
            pdt_code = new_record.get('pdt_code', '').strip()
            
            # Check for duplicate in current list
            if any(p.pdt_code == pdt_code for p in self.master_products):
                QMessageBox.warning(self, "Duplicate", f"พบ pdt_code ซ้ำในระบบ: {pdt_code}")
                return

            if self.storage.add_master_product(new_record):
                self.load_data() # Reload from DB
                QMessageBox.information(self, "Success", "เพิ่มข้อมูลสำเร็จ")
            else:
                QMessageBox.warning(self, "Error", "ไม่สามารถเพิ่มข้อมูลลงฐานข้อมูลได้")
    
    def edit_product(self):
        """Edit selected product in database"""
        pdt_code = self._get_selected_pdt_code()
        if pdt_code is None:
            QMessageBox.warning(self, "No Selection", "Please select a product to edit.")
            return
            
        # Get product data
        product = next((p for p in self.master_products if p.pdt_code == pdt_code), None)
        if not product:
            return
            
        current_data = product.to_dict()
        dialog = MasterDataDialog(self.columns, parent=self, data=current_data, edit_mode=True)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_record = dialog.get_data()
            new_code = updated_record.get('pdt_code', '').strip()
            
            # Check for duplicate if pdt_code changed
            if new_code != pdt_code and any(p.pdt_code == new_code for p in self.master_products):
                QMessageBox.warning(self, "Duplicate", f"พบ pdt_code ซ้ำ: {new_code}")
                return

            if self.storage.update_master_product(pdt_code, **updated_record):
                self.load_data()
                QMessageBox.information(self, "Success", "แก้ไขข้อมูลสำเร็จ")
            else:
                QMessageBox.warning(self, "Error", "ไม่สามารถแก้ไขข้อมูลในฐานข้อมูลได้")
    
    def delete_product(self):
        """Delete selected product from database"""
        pdt_code = self._get_selected_pdt_code()
        if pdt_code is None:
            QMessageBox.warning(self, "No Selection", "Please select a product to delete.")
            return
            
        reply = QMessageBox.question(
            self,
            'Confirm Deletion',
            f'แน่ใจหรือไม่ว่าจะลบข้อมูล {pdt_code}?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.storage.delete_master_product(pdt_code):
                self.load_data()
                QMessageBox.information(self, "Success", "ลบข้อมูลสำเร็จ")
            else:
                QMessageBox.warning(self, "Error", "ไม่สามารถลบข้อมูลได้")
    
    def import_from_file(self):
        """Import products from CSV or Excel file into database"""
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
                try:
                    df = pd.read_csv(file_path, encoding='utf-8-sig')
                except UnicodeDecodeError:
                    df = pd.read_csv(file_path, encoding='windows-1252')
            
            # Normalize and convert to list of dicts
            df.columns = df.columns.str.strip().str.lower()
            import_count = 0
            for _, row in df.iterrows():
                product_data = {key: str(row.get(key, "")) if not pd.isna(row.get(key)) else "" for key in self.column_keys}
                if product_data['pdt_code']:
                    self.storage.add_master_product(product_data)
                    import_count += 1
            
            self.load_data()
            QMessageBox.information(self, "Import Results", f"นำเข้าข้อมูลสำเร็จ {import_count} รายการ")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Error",
                f"เกิดข้อผิดพลาดในการนำเข้าไฟล์:\n{str(e)}"
            )
    
    def export_to_csv(self):
        """Export products from database to CSV file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Products",
            "products_export.csv",
            "CSV Files (*.csv)"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            # Get all from DB
            products = self.storage.get_all_master_products()
            data = [p.to_dict() for p in products]
            export_df = pd.DataFrame(data)
            
            if not export_df.empty:
                export_df = export_df[self.column_keys]
                export_df.to_csv(file_path, index=False, encoding='utf-8-sig')
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"ส่งออกข้อมูล {len(export_df)} รายการสำเร็จไปยัง:\n{file_path}"
                )
            else:
                QMessageBox.warning(self, "Export", "ไม่มีข้อมูลสำหรับส่งออก")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"เกิดข้อผิดพลาดในการส่งออกไฟล์:\n{str(e)}"
            )


class MasterDataDialog(QDialog):
    def __init__(self, columns, parent=None, data=None, edit_mode=False):
        super().__init__(parent)
        self.columns = columns
        self.data = data or {}
        self.edit_mode = edit_mode
        self.inputs = {}
        self.required_fields = {"pdt_code", "pdt_name"}
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Edit Master Data" if self.edit_mode else "Add Master Data")
        self.setMinimumWidth(450)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        for label, key in self.columns:
            input_field = QLineEdit()
            input_field.setText(str(self.data.get(key, "")))
            nice_label = label.replace('_', ' ').title()
            if key in self.required_fields:
                nice_label = f"{nice_label}*"
            form_layout.addRow(f"{nice_label}:", input_field)
            self.inputs[key] = input_field

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)

        layout.addLayout(form_layout)
        layout.addWidget(QLabel("* Required fields"))
        layout.addWidget(button_box)

        if self.edit_mode:
            self.inputs['pdt_code'].setReadOnly(False)

    def get_data(self):
        return {key: field.text().strip() for key, field in self.inputs.items()}

    def validate_and_accept(self):
        data = self.get_data()
        for key in self.required_fields:
            if not data.get(key):
                QMessageBox.warning(self, "Validation Error", f"{key} is required")
                self.inputs[key].setFocus()
                return
        self.accept()
