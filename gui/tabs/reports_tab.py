"""
Reports Tab - ระบบค้นหา Suppliers และข้อมูล Roll
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QGroupBox, QFormLayout,
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QComboBox, QMessageBox
)
from PySide6.QtCore import Qt
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
        
        # Initialize suppliers manager
        suppliers_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "Suppliers.csv"
        )
        self.suppliers_manager = SuppliersManager(suppliers_path)
        
        self.setup_ui()
    
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
        
        layout.addWidget(tabs)
    
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
        
        # Search by Location
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("ค้นหาตามสถานที่เก็บ...")
        self.location_input.textChanged.connect(self.search_rolls_by_location)
        search_layout.addRow("สถานที่เก็บ (Location):", self.location_input)
        
        # Search by Code (pdt_code)
        search_code_layout = QHBoxLayout()
        self.roll_code_input = QLineEdit()
        self.roll_code_input.setPlaceholderText("ค้นหาตามรหัสสินค้า (Code)...")
        self.roll_code_btn = QPushButton("ค้นหา")
        self.roll_code_btn.clicked.connect(self.search_rolls_by_code)
        search_code_layout.addWidget(self.roll_code_input)
        search_code_layout.addWidget(self.roll_code_btn)
        search_layout.addRow("รหัสสินค้า (Code):", search_code_layout)
        
        # Search by Roll ID
        search_roll_id_layout = QHBoxLayout()
        self.roll_id_input = QLineEdit()
        self.roll_id_input.setPlaceholderText("ค้นหาตาม Roll ID (เช่น R001)...")
        self.roll_id_btn = QPushButton("ค้นหา")
        self.roll_id_btn.clicked.connect(self.search_rolls_by_roll_id)
        search_roll_id_layout.addWidget(self.roll_id_input)
        search_roll_id_layout.addWidget(self.roll_id_btn)
        search_layout.addRow("Roll ID:", search_roll_id_layout)
        
        # Search by Lot
        search_lot_layout = QHBoxLayout()
        self.lot_input = QLineEdit()
        self.lot_input.setPlaceholderText("ค้นหาตาม Lot...")
        self.lot_btn = QPushButton("ค้นหา")
        self.lot_btn.clicked.connect(self.search_rolls_by_lot)
        search_lot_layout.addWidget(self.lot_input)
        search_lot_layout.addWidget(self.lot_btn)
        search_layout.addRow("Lot:", search_lot_layout)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # Results table
        self.rolls_table = QTableWidget()
        self.rolls_table.setColumnCount(10)
        self.rolls_table.setHorizontalHeaderLabels([
            "Roll ID", "SKU", "Lot", "Location", "Grade", 
            "Current Length", "Original Length", "Status", "Date Received", "Supplier"
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
    
    def search_rolls_by_location(self, location):
        """ค้นหา Roll ตามสถานที่เก็บ"""
        if not location.strip():
            self.rolls_table.setRowCount(0)
            return
        
        try:
            rolls = self.storage.get_all_rolls()
            results = [r for r in rolls if location.lower() in r.location.lower()]
            self.display_rolls_results(results)
        except Exception as e:
            QMessageBox.critical(self, "ข้อผิดพลาด", f"Error: {str(e)}")
    
    def search_rolls_by_code(self):
        """ค้นหา Roll ตามรหัสสินค้า (SKU)"""
        code = self.roll_code_input.text().strip()
        if not code:
            QMessageBox.warning(self, "ข้อผิดพลาด", "กรุณากรอกรหัสสินค้า")
            return
        
        try:
            rolls = self.storage.get_all_rolls()
            results = [r for r in rolls if code.lower() in r.sku.lower()]
            self.display_rolls_results(results)
        except Exception as e:
            QMessageBox.critical(self, "ข้อผิดพลาด", f"Error: {str(e)}")
    
    def search_rolls_by_roll_id(self):
        """ค้นหา Roll ตาม Roll ID"""
        roll_id = self.roll_id_input.text().strip()
        if not roll_id:
            QMessageBox.warning(self, "ข้อผิดพลาด", "กรุณากรอก Roll ID")
            return
        
        try:
            roll = self.storage.get_roll(roll_id)
            if roll:
                self.display_rolls_results([roll])
            else:
                QMessageBox.information(self, "ผลการค้นหา", f"ไม่พบ Roll ID {roll_id}")
                self.rolls_table.setRowCount(0)
        except Exception as e:
            QMessageBox.critical(self, "ข้อผิดพลาด", f"Error: {str(e)}")
    
    def search_rolls_by_lot(self):
        """ค้นหา Roll ตาม Lot"""
        lot = self.lot_input.text().strip()
        if not lot:
            QMessageBox.warning(self, "ข้อผิดพลาด", "กรุณากรอก Lot")
            return
        
        try:
            rolls = self.storage.get_all_rolls()
            results = [r for r in rolls if lot.lower() in r.lot.lower()]
            self.display_rolls_results(results)
        except Exception as e:
            QMessageBox.critical(self, "ข้อผิดพลาด", f"Error: {str(e)}")
    
    def display_rolls_results(self, results):
        """แสดงผลการค้นหา Roll"""
        self.rolls_table.setRowCount(len(results))
        
        for row, roll in enumerate(results):
            # ดึงข้อมูล Supplier จาก Suppliers.csv
            supplier = ""
            try:
                supplier_data = self.suppliers_manager.search_by_code(roll.sku)
                if supplier_data:
                    supplier = supplier_data.get(supplier_data.columns[1], "")
            except:
                pass
            
            # แสดงข้อมูล
            self.rolls_table.setItem(row, 0, QTableWidgetItem(roll.roll_id))
            self.rolls_table.setItem(row, 1, QTableWidgetItem(roll.sku))
            self.rolls_table.setItem(row, 2, QTableWidgetItem(roll.lot))
            self.rolls_table.setItem(row, 3, QTableWidgetItem(roll.location))
            self.rolls_table.setItem(row, 4, QTableWidgetItem(roll.grade))
            self.rolls_table.setItem(row, 5, QTableWidgetItem(f"{roll.current_length:.2f}"))
            self.rolls_table.setItem(row, 6, QTableWidgetItem(f"{roll.original_length:.2f}"))
            self.rolls_table.setItem(row, 7, QTableWidgetItem(roll.status))
            self.rolls_table.setItem(row, 8, QTableWidgetItem(roll.date_received))
            self.rolls_table.setItem(row, 9, QTableWidgetItem(supplier))
        
        self.rolls_table.resizeColumnsToContents()
