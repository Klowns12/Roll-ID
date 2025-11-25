"""
Reports Tab - ระบบค้นหา Suppliers และข้อมูล Roll
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QGroupBox, QFormLayout,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QComboBox, QMessageBox
)
from PySide6.QtCore import Qt
from typing import List
from storage import Roll
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.suppliers_manager import SuppliersManager


class ReportsTab(QWidget):
    """Tab สำหรับค้นหา Suppliers และข้อมูล Roll"""
    
    def __init__(self, storage):
        super().__init__()
        self.storage = storage
        self.rolls = []
        
        # Initialize suppliers manager
        suppliers_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "Suppliers.csv"
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
            if hasattr(self.storage, 'search_rolls'):
                self.rolls = self.storage.search_rolls()
            elif hasattr(self.storage, 'get_all_rolls'):
                self.rolls = self.storage.get_all_rolls()
            else:
                self.rolls = []
            self.refresh_rolls_table(self.rolls)
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
        self.suppliers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
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
        self.filter_field_combo.addItems([
            "Code",
            "Location",
            "Roll ID",
            "Lot"
        ])
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
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # Results table
        self.rolls_table = QTableWidget()
        self.rolls_table.setColumnCount(12)
        self.rolls_table.setHorizontalHeaderLabels([
            "Roll ID", "SKU", "Lot", "Location", "Grade",
            "Current Length", "Original Length", "Exist_Qty", "RollStatus",
            "Status", "Date Received", "Supplier"
        ])
        self.rolls_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.rolls_table.setAlternatingRowColors(True)
        
        layout.addWidget(QLabel("ผลการค้นหา:"))
        layout.addWidget(self.rolls_table)
        
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
        if not self.rolls:
            self.load_rolls_data()
            return

        keyword = self.filter_input.text().strip().lower()
        if not keyword:
            filtered = self.rolls
        else:
            field = self.filter_field_combo.currentText()
            filtered = []
            for roll in self.rolls:
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

        self.refresh_rolls_table(filtered)

    def clear_roll_filters(self):
        """ล้างตัวกรองและโชว์ข้อมูลทั้งหมด"""
        self.filter_input.clear()
        self.filter_field_combo.setCurrentIndex(0)
        self.refresh_rolls_table(self.rolls)

    def refresh_rolls_table(self, rolls: List[Roll]):
        """อัปเดตตารางม้วนตามรายการที่ให้มา"""
        self.rolls_table.setRowCount(len(rolls))

        for row, roll in enumerate(rolls):
            # ดึงข้อมูล Supplier จาก Suppliers.csv
            supplier = ""
            try:
                supplier_data = self.suppliers_manager.search_by_code(roll.sku)
                if supplier_data:
                    supplier = supplier_data.get(list(supplier_data.keys())[1], "")
            except Exception:
                pass

            exist_qty = roll.current_length
            roll_status = "เต็มม้วน" if roll.current_length >= roll.original_length else "เศษ"

            self.rolls_table.setItem(row, 0, QTableWidgetItem(roll.roll_id))
            self.rolls_table.setItem(row, 1, QTableWidgetItem(roll.sku))
            self.rolls_table.setItem(row, 2, QTableWidgetItem(roll.lot))
            self.rolls_table.setItem(row, 3, QTableWidgetItem(roll.location))
            self.rolls_table.setItem(row, 4, QTableWidgetItem(roll.grade))
            self.rolls_table.setItem(row, 5, QTableWidgetItem(f"{roll.current_length:.2f}"))
            self.rolls_table.setItem(row, 6, QTableWidgetItem(f"{roll.original_length:.2f}"))
            self.rolls_table.setItem(row, 7, QTableWidgetItem(f"{exist_qty:.2f}"))
            self.rolls_table.setItem(row, 8, QTableWidgetItem(roll_status))
            self.rolls_table.setItem(row, 9, QTableWidgetItem(roll.status))
            self.rolls_table.setItem(row, 10, QTableWidgetItem(roll.date_received))
            self.rolls_table.setItem(row, 11, QTableWidgetItem(supplier))

        self.rolls_table.resizeColumnsToContents()