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
        self.master_df = pd.DataFrame(columns=self.column_keys)
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.master_data_path = os.path.join(root_dir, "MasterDATA.csv")
        if not os.path.exists(self.master_data_path):
            self.master_df.to_csv(self.master_data_path, index=False, encoding='utf-8-sig')
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
        
        # Add widgets to layout
        layout.addLayout(search_layout)
        layout.addLayout(btn_layout)
        layout.addWidget(self.table)
        
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
        """Load master data from CSV and populate the table"""
        self.master_df = self._read_master_dataframe()
        self._refresh_table()

    def _read_master_dataframe(self):
        """Return normalized dataframe from MasterDATA.csv"""
        if not os.path.exists(self.master_data_path):
            QMessageBox.warning(self, "Missing Master Data", f"ไม่พบไฟล์ MasterDATA.csv ที่\n{self.master_data_path}")
            return pd.DataFrame(columns=self.column_keys)

        try:
            df = pd.read_csv(self.master_data_path, encoding='utf-8-sig')
        except UnicodeDecodeError:
            df = pd.read_csv(self.master_data_path, encoding='windows-1252')
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"ไม่สามารถอ่านไฟล์ MasterDATA.csv ได้:\n{e}")
            return pd.DataFrame(columns=self.column_keys)

        return self._normalize_dataframe(df)

    def _normalize_dataframe(self, df):
        df = df.copy()
        df.columns = df.columns.str.strip().str.lower()
        for key in self.column_keys:
            if key not in df.columns:
                df[key] = ""
        return df[self.column_keys].reset_index(drop=True)

    def _save_master_data(self):
        try:
            save_df = self.master_df[self.column_keys].copy()
            save_df.to_csv(self.master_data_path, index=False, encoding='utf-8-sig')
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"ไม่สามารถบันทึกไฟล์ MasterDATA.csv ได้:\n{e}")

    def _refresh_table(self):
        self.table.setRowCount(0)
        for idx, row in self.master_df.iterrows():
            table_row = self.table.rowCount()
            self.table.insertRow(table_row)
            for col_idx, (_, column_key) in enumerate(self.columns):
                value = row.get(column_key, "")
                if pd.isna(value):
                    value = ""
                item = QTableWidgetItem(str(value))
                if col_idx == 0:
                    item.setData(Qt.ItemDataRole.UserRole, idx)
                self.table.setItem(table_row, col_idx, item)

    def _get_selected_df_index(self):
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
    
    def add_product(self):
        """Add new master data row"""
        dialog = MasterDataDialog(self.columns, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_record = dialog.get_data()
            pdt_code = new_record.get('pdt_code', '').strip()
            if pdt_code and not self.master_df[self.master_df['pdt_code'] == pdt_code].empty:
                QMessageBox.warning(self, "Duplicate", f"พบ pdt_code ซ้ำ: {pdt_code}")
                return

            row = {key: new_record.get(key, "") for key in self.column_keys}
            self.master_df = pd.concat([
                self.master_df,
                pd.DataFrame([row])
            ], ignore_index=True)
            self.master_df = self.master_df.reset_index(drop=True)
            self._save_master_data()
            self._refresh_table()
            QMessageBox.information(self, "Success", "เพิ่มข้อมูลสำเร็จ")
    
    def edit_product(self):
        """Edit selected product"""
        df_index = self._get_selected_df_index()
        if df_index is None:
            QMessageBox.warning(self, "No Selection", "Please select a product to edit.")
            return
        current_data = self.master_df.loc[df_index, self.column_keys].to_dict()
        dialog = MasterDataDialog(self.columns, parent=self, data=current_data, edit_mode=True)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_record = dialog.get_data()
            new_code = updated_record.get('pdt_code', '').strip()
            if new_code != current_data.get('pdt_code') and not self.master_df[self.master_df['pdt_code'] == new_code].empty:
                QMessageBox.warning(self, "Duplicate", f"พบ pdt_code ซ้ำ: {new_code}")
                return

            for key in self.column_keys:
                self.master_df.at[df_index, key] = updated_record.get(key, "")
            self.master_df = self.master_df.reset_index(drop=True)
            self._save_master_data()
            self._refresh_table()
            QMessageBox.information(self, "Success", "แก้ไขข้อมูลสำเร็จ")
    
    def delete_product(self):
        """Delete selected product"""
        df_index = self._get_selected_df_index()
        if df_index is None:
            QMessageBox.warning(self, "No Selection", "Please select a product to delete.")
            return
        pdt_code = self.master_df.at[df_index, 'pdt_code'] if df_index < len(self.master_df) else ""
        reply = QMessageBox.question(
            self,
            'Confirm Deletion',
            f'แน่ใจหรือไม่ว่าจะลบข้อมูล {pdt_code}?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.master_df = self.master_df.drop(df_index).reset_index(drop=True)
            self._save_master_data()
            self._refresh_table()
            QMessageBox.information(self, "Success", "ลบข้อมูลสำเร็จ")
    
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

            df = self._normalize_dataframe(df)
            self.master_df = df
            self._save_master_data()
            self._refresh_table()
            QMessageBox.information(self, "Import Results", "นำเข้าข้อมูลสำเร็จ")

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
            export_df = self.master_df[self.column_keys].copy()
            export_df.to_csv(file_path, index=False, encoding='utf-8-sig')
            QMessageBox.information(
                self,
                "Export Successful",
                f"Successfully exported {len(export_df)} rows to:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"An error occurred while exporting to CSV:\n{str(e)}"
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
