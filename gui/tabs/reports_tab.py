"""
Reports Tab - ระบบค้นหา Suppliers และข้อมูล Roll
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QGroupBox,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
    QComboBox,
    QMessageBox,
    QFileDialog,
)
from PySide6.QtCore import Qt
from typing import List
from storage import Roll
import sys
import os
import pandas as pd
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.suppliers_manager import SuppliersManager


class ReportsTab(QWidget):
    """Tab สำหรับค้นหา Suppliers และข้อมูล Roll"""

    def __init__(self, storage):
        super().__init__()
        self.storage = storage
        self.all_rolls = []
        self.filtered_rolls = []
        self.display_limit = 100

        # Initialize suppliers manager
        suppliers_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "Suppliers.csv",
        )
        self.suppliers_manager = SuppliersManager(suppliers_path)

        self.setup_ui()
        self.load_rolls_data()

    def setup_ui(self):
        """สร้าง UI"""
        layout = QVBoxLayout(self)

        # Create tab widget
        tabs = QTabWidget()

        # Tab 1: Suppliers Search
        suppliers_tab = self.create_suppliers_search_tab()
        tabs.addTab(suppliers_tab, "ค้นหา Suppliers")

        # Tab 2: Roll Search
        rolls_tab = self.create_rolls_search_tab()
        tabs.addTab(rolls_tab, "ค้นหา Roll")
        self.roll_filter_tab = rolls_tab

        layout.addWidget(tabs)

    def load_rolls_data(self):
        """โหลดข้อมูลม้วนทั้งหมดจาก storage"""
        try:
            if hasattr(self.storage, "search_rolls"):
                # Fetch ALL rolls (empty query)
                self.all_rolls = self.storage.search_rolls("")
            elif hasattr(self.storage, "get_all_rolls"):
                self.all_rolls = self.storage.get_all_rolls()
            else:
                self.all_rolls = []

            # Reset filter and limit
            self.display_limit = 100
            self.apply_roll_filters()

        except Exception as e:
            QMessageBox.critical(self, "ข้อผิดพลาด", f"Error loading rolls: {str(e)}")

    def create_suppliers_search_tab(self):
        """สร้าง Tab สำหรับค้นหา Suppliers"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Search group
        search_group = QGroupBox("ค้นหา Suppliers")
        search_layout = QFormLayout()

        # Search by supplier name
        self.supplier_name_input = QLineEdit()
        self.supplier_name_input.setPlaceholderText("ค้นหาตามชื่อ Suppliers...")
        self.supplier_name_input.textChanged.connect(self.search_suppliers_by_name)
        search_layout.addRow("ชื่อ Suppliers:", self.supplier_name_input)

        # Search by code
        search_code_layout = QHBoxLayout()
        self.supplier_code_input = QLineEdit()
        self.supplier_code_input.setPlaceholderText("ค้นหาตามรหัส (Code)...")
        self.supplier_code_btn = QPushButton("ค้นหา")
        self.supplier_code_btn.clicked.connect(self.search_suppliers_by_code)
        search_code_layout.addWidget(self.supplier_code_input)
        search_code_layout.addWidget(self.supplier_code_btn)
        search_layout.addRow("รหัส (Code):", search_code_layout)

        search_group.setLayout(search_layout)
        layout.addWidget(search_group)

        # Results table
        self.suppliers_table = QTableWidget()
        self.suppliers_table.setColumnCount(0)
        self.suppliers_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.suppliers_table.setAlternatingRowColors(True)

        layout.addWidget(QLabel("ผลการค้นหา:"))
        layout.addWidget(self.suppliers_table)

        return tab

    def create_rolls_search_tab(self):
        """สร้าง Tab สำหรับค้นหา Roll"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Search group
        search_group = QGroupBox("ค้นหา Roll")
        search_layout = QFormLayout()

        # Filter dropdown and input
        filter_layout = QHBoxLayout()
        self.filter_field_combo = QComboBox()
        self.filter_field_combo.addItems(["Code", "Location", "Roll ID", "Lot"])
        self.filter_field_combo.currentIndexChanged.connect(self.apply_roll_filters)

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Code / Location / Roll ID / Lot")
        self.filter_input.textChanged.connect(self.apply_roll_filters)

        clear_btn = QPushButton("ล้าง")
        clear_btn.clicked.connect(self.clear_roll_filters)

        filter_layout.addWidget(self.filter_field_combo)
        filter_layout.addWidget(self.filter_input, 1)
        filter_layout.addWidget(clear_btn)

        search_layout.addRow("ค้นหา:", filter_layout)

        # Export button
        export_btn = QPushButton("Export to Excel")
        export_btn.clicked.connect(self.export_to_excel)
        export_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        search_layout.addRow("", export_btn)

        search_group.setLayout(search_layout)
        layout.addWidget(search_group)

        # Results table
        self.rolls_table = QTableWidget()
        self.rolls_table.setColumnCount(12)
        self.rolls_table.setHorizontalHeaderLabels(
            [
                "Roll ID",
                "SKU",
                "Lot",
                "Location",
                "Grade",
                "Current Length",
                "Original Length",
                "Exist_Qty",
                "RollStatus",
                "Status",
                "Date Received",
                "Supplier",
            ]
        )
        self.rolls_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.rolls_table.setAlternatingRowColors(True)

        layout.addWidget(QLabel("ผลการค้นหา:"))
        layout.addWidget(self.rolls_table)

        # Load More button
        self.load_more_btn = QPushButton("Show More (+100)")
        self.load_more_btn.clicked.connect(self.load_more_rolls)
        layout.addWidget(self.load_more_btn)

        return tab

    # ========== Suppliers Search Methods ==========

    def search_suppliers_by_name(self, name):
        """ค้นหา Suppliers ตามชื่อ"""
        if not name.strip():
            self.suppliers_table.setRowCount(0)
            return

        results = self.suppliers_manager.search_by_supplier(name)
        self.display_suppliers_results(results)

    def search_suppliers_by_code(self):
        """ค้นหา Suppliers ตามรหัส"""
        code = self.supplier_code_input.text().strip()
        if not code:
            QMessageBox.warning(self, "ข้อผิดพลาด", "กรุณากรอกรหัส (Code)")
            return

        result = self.suppliers_manager.search_by_code(code)
        if result:
            self.display_suppliers_results([result])
        else:
            QMessageBox.information(self, "ผลการค้นหา", f"ไม่พบรหัส {code}")
            self.suppliers_table.setRowCount(0)

    def display_suppliers_results(self, results):
        """แสดงผลการค้นหา Suppliers"""
        if not results:
            self.suppliers_table.setRowCount(0)
            return

        # ตั้งค่าคอลัมน์
        columns = list(results[0].keys())
        self.suppliers_table.setColumnCount(len(columns))
        self.suppliers_table.setHorizontalHeaderLabels(columns)

        # เพิ่มข้อมูล
        self.suppliers_table.setRowCount(len(results))
        for row, item in enumerate(results):
            for col, key in enumerate(columns):
                value = item.get(key, "")
                self.suppliers_table.setItem(row, col, QTableWidgetItem(str(value)))

        self.suppliers_table.resizeColumnsToContents()

    # ========== Rolls Search Methods ==========

    def apply_roll_filters(self):
        """ใช้ตัวกรองการค้นหาแบบ dropdown + text"""
        if not self.all_rolls:
            self.filtered_rolls = []
            self.refresh_rolls_table([])
            return

        keyword = self.filter_input.text().strip().lower()
        if not keyword:
            self.filtered_rolls = self.all_rolls
        else:
            field = self.filter_field_combo.currentText()
            filtered = []
            for roll in self.all_rolls:
                value = ""
                if field == "Code":
                    value = roll.sku or roll.pdt_code or ""
                elif field == "Location":
                    value = roll.location or ""
                elif field == "Roll ID":
                    value = roll.roll_id or ""
                elif field == "Lot":
                    value = roll.lot or ""

                if keyword in str(value).lower():
                    filtered.append(roll)
            self.filtered_rolls = filtered

        # Reset limit when filter changes
        # self.display_limit = 100 # Optional: keep existing limit or reset
        self.refresh_rolls_table(self.filtered_rolls)

    def clear_roll_filters(self):
        """ล้างตัวกรองและโชว์ข้อมูลทั้งหมด"""
        self.filter_input.clear()
        self.filter_field_combo.setCurrentIndex(0)
        self.display_limit = 100
        self.apply_roll_filters()

    def refresh_rolls_table(self, rolls: List[Roll]):
        """อัปเดตตารางม้วนตามรายการที่ให้มา (พร้อม Pagination)"""

        # Apply pagination
        display_rolls = rolls[: self.display_limit]
        self.rolls_table.setRowCount(len(display_rolls))

        # Update Load More button
        if len(rolls) > self.display_limit:
            self.load_more_btn.setVisible(True)
            self.load_more_btn.setText(
                f"Show More (+100) - Showing {len(display_rolls)} of {len(rolls)}"
            )
        else:
            self.load_more_btn.setVisible(False)

        for row, roll in enumerate(display_rolls):
            # ดึงข้อมูล Supplier และข้อมูลอื่นๆ จาก Suppliers.csv
            supplier = ""
            exist_qty = roll.current_length  # Default value
            roll_status = (
                "เต็มม้วน" if roll.current_length >= roll.original_length else "เศษ"
            )  # Default

            try:
                supplier_data = self.suppliers_manager.search_by_code(roll.sku)
                if supplier_data:
                    # Debug: แสดงชื่อคอลัมน์ทั้งหมด (เฉพาะแถวแรก)
                    if row == 0:
                        print(f"DEBUG: Available columns: {list(supplier_data.keys())}")

                    # Supplier Name
                    if "Suppliers" in supplier_data:
                        supplier = str(supplier_data.get("Suppliers", ""))
                    else:
                        keys = list(supplier_data.keys())
                        if len(keys) > 1:
                            supplier = str(supplier_data.get(keys[1], ""))

                    # Exist_Qty from QTY column (first one, not renamed)
                    # Pandas renames duplicate columns to QTY, QTY.1, QTY.2
                    qty_value = None
                    if "QTY" in supplier_data:
                        qty_value = supplier_data.get("QTY")

                    if (
                        qty_value is not None
                        and str(qty_value).strip()
                        and str(qty_value) != "0"
                    ):
                        try:
                            exist_qty = float(qty_value)
                        except (ValueError, TypeError):
                            pass

                    # RollStatus from ม้วนเต็ม and เศษ columns
                    # These might also be renamed by pandas
                    full_rolls = 0
                    scrap_qty = 0

                    # Try original names first, then .1, .2 versions
                    if "ม้วนเต็ม" in supplier_data:
                        full_value = supplier_data.get("ม้วนเต็ม")
                        if full_value is not None and str(full_value).strip():
                            try:
                                full_rolls = float(full_value)
                            except (ValueError, TypeError):
                                pass

                    if "เศษ" in supplier_data:
                        scrap_value = supplier_data.get("เศษ")
                        if scrap_value is not None and str(scrap_value).strip():
                            try:
                                scrap_qty = float(scrap_value)
                            except (ValueError, TypeError):
                                pass

                    # Debug output for first few rows
                    if row < 3:
                        print(
                            f"DEBUG Row {row}: SKU={roll.sku}, QTY={exist_qty}, ม้วนเต็ม={full_rolls}, เศษ={scrap_qty}"
                        )

                    # Determine status based on ม้วนเต็ม and เศษ
                    if full_rolls > 0:
                        roll_status = "เต็มม้วน"
                    elif scrap_qty > 0:
                        roll_status = "เศษ"

            except Exception as e:
                print(f"Error getting supplier data for {roll.sku}: {e}")
                import traceback

                traceback.print_exc()

            self.rolls_table.setItem(row, 0, QTableWidgetItem(roll.roll_id))
            self.rolls_table.setItem(row, 1, QTableWidgetItem(roll.sku))
            self.rolls_table.setItem(row, 2, QTableWidgetItem(roll.lot))
            self.rolls_table.setItem(row, 3, QTableWidgetItem(roll.location))
            self.rolls_table.setItem(row, 4, QTableWidgetItem(roll.grade))
            self.rolls_table.setItem(
                row, 5, QTableWidgetItem(f"{roll.current_length:.2f}")
            )
            self.rolls_table.setItem(
                row, 6, QTableWidgetItem(f"{roll.original_length:.2f}")
            )
            self.rolls_table.setItem(row, 7, QTableWidgetItem(f"{exist_qty:.2f}"))
            self.rolls_table.setItem(row, 8, QTableWidgetItem(roll_status))
            self.rolls_table.setItem(row, 9, QTableWidgetItem(roll.status))
            self.rolls_table.setItem(row, 10, QTableWidgetItem(roll.date_received))
            self.rolls_table.setItem(row, 11, QTableWidgetItem(supplier))

        self.rolls_table.resizeColumnsToContents()

    def load_more_rolls(self):
        """โหลดข้อมูลเพิ่มอีก 100 รายการ"""
        self.display_limit += 100
        self.refresh_rolls_table(self.filtered_rolls)

    def export_to_excel(self):
        """Export filtered data to Excel"""
        if not self.filtered_rolls:
            QMessageBox.warning(self, "Warning", "No data to export")
            return

        try:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Export to Excel",
                f"Rolls_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                "Excel Files (*.xlsx);;All Files (*)",
            )

            if not filename:
                return

            if not filename.lower().endswith(".xlsx"):
                filename += ".xlsx"

            # Prepare data for DataFrame
            data = []
            for roll in self.filtered_rolls:
                # Get supplier info (similar to table display logic)
                supplier = ""
                exist_qty = roll.current_length
                roll_status = (
                    "เต็มม้วน" if roll.current_length >= roll.original_length else "เศษ"
                )

                try:
                    supplier_data = self.suppliers_manager.search_by_code(roll.sku)
                    if supplier_data:
                        if "Suppliers" in supplier_data:
                            supplier = str(supplier_data.get("Suppliers", ""))
                        else:
                            keys = list(supplier_data.keys())
                            if len(keys) > 1:
                                supplier = str(supplier_data.get(keys[1], ""))

                        # Logic for Exist Qty and Status from Supplier data could be repeated here
                        # For simplicity, using current roll data + supplier name
                except:
                    pass

                data.append(
                    {
                        "Roll ID": roll.roll_id,
                        "SKU": roll.sku,
                        "Lot": roll.lot,
                        "Location": roll.location,
                        "Grade": roll.grade,
                        "Current Length": roll.current_length,
                        "Original Length": roll.original_length,
                        "Status": roll.status,
                        "Date Received": roll.date_received,
                        "Supplier": supplier,
                    }
                )

            df = pd.DataFrame(data)
            df.to_excel(filename, index=False)

            QMessageBox.information(self, "Success", f"Exported to {filename}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")

    def refresh_data(self):
        """Refresh data from storage (called by signal)"""
        self.load_rolls_data()
