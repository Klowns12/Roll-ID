from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QDateEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QFormLayout, QSizePolicy, QLineEdit,
    QRadioButton, QButtonGroup, QMessageBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtCharts import (
    QChart, QChartView, QBarSet, QBarSeries,
    QBarCategoryAxis, QValueAxis, QPieSeries
)
import sys
import os

from utils.master_suppliers_manager import MasterSuppliersManager

class StatisticsTab(QWidget):

    

    def __init__(self, storage):
        super().__init__()
        self.storage = storage
        
        # Initialize master suppliers manager
        root_dir = os.getcwd()

        
        self.suppliers_manager = MasterSuppliersManager()
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Set up the Statistics tab UI"""
        layout = QVBoxLayout(self)
        
        # ===== FILTER SECTION =====
        filter_group = QGroupBox("ค้นหา / Search")
        filter_layout = QVBoxLayout()
        
        # # Row 1: Group, Category
        # row1_layout = QHBoxLayout()
        # row1_layout.addWidget(QLabel("Group"))
        # self.group_combo = QComboBox()
        # self.group_combo.addItems(["All", "Group 1", "Group 2"])
        # self.group_combo.setMaximumWidth(150)
        # row1_layout.addWidget(self.group_combo)
        
        # row1_layout.addSpacing(20)
        
        # row1_layout.addWidget(QLabel("Category"))
        # self.category_combo = QComboBox()
        # self.category_combo.addItems(["All", "Category 1", "Category 2"])
        # self.category_combo.setMaximumWidth(150)
        # row1_layout.addWidget(self.category_combo)
        
        # row1_layout.addStretch()
        # filter_layout.addLayout(row1_layout)
        
        # Row 2: Suppliers, Code
        row2_layout = QHBoxLayout()
        row2_layout.addWidget(QLabel("Suppliers"))
        self.suppliers_input = QLineEdit()
        self.suppliers_input.setPlaceholderText("ค้นหา Suppliers...")
        self.suppliers_input.setMaximumWidth(250)
        self.suppliers_input.textChanged.connect(self.on_supplier_changed)
        row2_layout.addWidget(self.suppliers_input)
        
        row2_layout.addSpacing(20)
        
        row2_layout.addWidget(QLabel("ค้นหา"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Code / Location / Roll ID / Lot")
        self.search_input.setMaximumWidth(200)
        self.search_input.textChanged.connect(self.on_search_changed)
        row2_layout.addWidget(self.search_input)
        
        row2_layout.addStretch()
        filter_layout.addLayout(row2_layout)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # # ===== CHECK QTY SECTION =====
        # qty_group = QGroupBox("Check QTY")
        # qty_layout = QHBoxLayout()
        
        # self.qty_all_radio = QRadioButton("All")
        # self.qty_all_radio.setChecked(True)
        # self.qty_min_radio = QRadioButton("Min")
        # self.qty_max_radio = QRadioButton("Max")
        
        # qty_layout.addWidget(self.qty_all_radio)
        # qty_layout.addWidget(self.qty_min_radio)
        # qty_layout.addWidget(self.qty_max_radio)
        # qty_layout.addStretch()
        # qty_group.setLayout(qty_layout)
        # layout.addWidget(qty_group)
        
        # # ===== MATERIAL STATUS SECTION =====
        # status_group = QGroupBox("Material status")
        # status_layout = QHBoxLayout()
        
        # self.status_active_radio = QRadioButton("Active")
        # self.status_active_radio.setChecked(True)
        # self.status_inactive_radio = QRadioButton("Inactive")
        # self.status_all_radio = QRadioButton("All")
        
        # status_layout.addWidget(self.status_active_radio)
        # status_layout.addWidget(self.status_inactive_radio)
        # status_layout.addWidget(self.status_all_radio)
        # status_layout.addStretch()
        # status_group.setLayout(status_layout)
        # layout.addWidget(status_group)
        
        # # ===== MATERIAL LIST SECTION =====
        # list_group = QGroupBox("Material list of")
        # list_layout = QHBoxLayout()
        
        # self.list_all_radio = QRadioButton("All")
        # self.list_all_radio.setChecked(True)
        # self.list_existing_radio = QRadioButton("Existing")
        
        # list_layout.addWidget(self.list_all_radio)
        # list_layout.addWidget(self.list_existing_radio)
        # list_layout.addStretch()
        # list_group.setLayout(list_layout)
        # layout.addWidget(list_group)
        
        # ===== BUTTONS SECTION =====
        btn_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setFixedSize(80, 30)
        self.refresh_btn.clicked.connect(self.load_data)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.refresh_btn)
        layout.addLayout(btn_layout)
        
        # ===== DATA TABLE =====
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(10)
        self.data_table.setHorizontalHeaderLabels([
            "Code", "SubPartCode", "SupCode", "Supplier Name", "Description","Lot No.",
            "Location", "Unit", "Exist. Qty", "เศษ.QTY",
        ])
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.data_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.data_table)
    
    def create_chart(self, title):
        """Create a chart with the given title"""
        chart = QChart()
        chart.setTitle(title)
        chart.setAnimationOptions(QChart.SeriesAnimations)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        return chart
    
    def load_data(self):
        """Load and display statistics data"""
        try:    
            self.suppliers_manager = MasterSuppliersManager()
            
            # Get all suppliers data
            self.display_suppliers_data()
        except Exception as e:
            print(f"Error loading statistics: {e}")
    
    def on_supplier_changed(self, supplier_name):
        """Handle supplier search change"""
        self.display_suppliers_data()
    
    def on_search_changed(self, text):
        """Handle code search change"""
        self.display_suppliers_data()
    
    def display_suppliers_data(self):
        """Display suppliers data in table - ค้นหาพร้อมกันทั้ง Supplier และ ค้นหา (Code/Location/Roll ID/Lot)"""
        try:
            # Get filter values
            supplier_name = self.suppliers_input.text().strip()
            search_query = self.search_input.text().strip()
            
            # ค้นหาพร้อมกัน
            results = self.suppliers_manager.search_combined(supplier_name, search_query)
            
            # Determine search type (เพื่อตรวจสอบว่าแสดง Exist. Qty หรือไม่)
            search_type = "supplier" if supplier_name else "all"
            
            # Display in table
            self.display_table_data(results, search_type)
            
        except Exception as e:
            print(f"Error displaying suppliers data: {e}")
    
    def display_table_data(self, results, search_type="all"):
        """Display data in table with separated data from each file"""
        if not results:
            self.data_table.setRowCount(0)
            return
        
        self.data_table.setRowCount(len(results))
        
        # Update table columns based on search type
        if search_type == "supplier":
            # Show Exist. Qty and เศษ.QTY when searching by supplier
            self.data_table.setColumnCount(11)
            self.data_table.setHorizontalHeaderLabels([
                "Code","Roll ID","SubPartCode", "SupCode", "Supplier Name", "Description",
                "Lot No.", "Location", "Unit", "Exist. Qty", "เศษ.QTY", ""
            ])
        else:
            # Hide Exist. Qty and เศษ.QTY when searching by code only
            self.data_table.setColumnCount(9)
            self.data_table.setHorizontalHeaderLabels([
                "Code","Roll ID","SubPartCode", "SupCode", "Supplier Name", "Description","Lot No.", "Location", "Unit",
            ])
        
        # Display data
        for row, item in enumerate(results):
            # Get separated data
            row_data = self.suppliers_manager.get_row_data(item, search_type)
            
            # Display each column
            col_idx = 0
            for col_name in ["Code","Roll ID", "SubPartCode", "SupCode", "Supplier Name", "Description", "Lot No.", "Location", "Unit"]:
                if col_idx >= self.data_table.columnCount():
                    break
                value = row_data.get(col_name, "")
                self.data_table.setItem(row, col_idx, QTableWidgetItem(str(value)))
                col_idx += 1
            
            # Add Exist. Qty and เศษ.QTY if search_type is "supplier"
            if search_type == "supplier" and col_idx < self.data_table.columnCount():
                exist_qty = row_data.get("Exist. Qty", "")
                scrap_qty = row_data.get("เศษ.QTY", "")
                self.data_table.setItem(row, col_idx, QTableWidgetItem(str(exist_qty)))
                col_idx += 1
                if col_idx < self.data_table.columnCount():
                    self.data_table.setItem(row, col_idx, QTableWidgetItem(str(scrap_qty)))
        
        # ปรับขนาด column
        self.data_table.horizontalHeader().setStretchLastSection(False)
        for i in range(self.data_table.columnCount()):
            self.data_table.setColumnWidth(i, 120)
        # ให้ column สุดท้ายยืดเต็มพื้นที่ว่าง
        self.data_table.horizontalHeader().setStretchLastSection(True)
    
    def update_pie_chart(self, chart, data):
        """Update pie chart with data"""
        series = QPieSeries()
        for label, value in data.items():
            series.append(f"{label} ({value})", value)
        
        chart.removeAllSeries()
        chart.addSeries(series)
        chart.setTitle(f"{chart.title()} - Total: {sum(data.values())}")
    
    def update_bar_chart(self, chart, data):
        """Update bar chart with data"""
        series = QBarSeries()
        bar_set = QBarSet("Count")
        
        categories = []
        for label, value in data.items():
            bar_set.append(value)
            categories.append(f"{label}\n({value})")
        
        series.append(bar_set)
        
        chart.removeAllSeries()
        chart.addSeries(series)
        chart.setTitle(f"{chart.title()} - Total: {sum(data.values())}")
        
        # Customize axes
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        chart.createDefaultAxes()
        chart.setAxisX(axis_x, series)
    
    def update_data_table(self, start_date, end_date):
        """Update the data table with detailed information"""
        try:
            # TODO: Fetch detailed data from storage
            # This is a placeholder - replace with actual data fetching
            data = self.storage.get_rolls_by_date_range(start_date, end_date)
            
            self.data_table.setRowCount(len(data))
            for row, item in enumerate(data):
                for col, value in enumerate(item):
                    self.data_table.setItem(row, col, QTableWidgetItem(str(value)))
            
            self.data_table.resizeColumnsToContents()
            
        except Exception as e:
            print(f"Error updating data table: {e}")
