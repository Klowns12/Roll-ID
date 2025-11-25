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
import math

from typing import List, Dict
from storage import Roll
from utils.master_suppliers_manager import MasterSuppliersManager

class StatisticsTab(QWidget):

    

    def __init__(self, storage):
        super().__init__()
        self.storage = storage
        
        # Initialize master suppliers manager
        root_dir = os.getcwd()

        
        self.rolls: List[Roll] = []
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
        self.suppliers_input.textChanged.connect(self.on_filters_changed)
        row2_layout.addWidget(self.suppliers_input)
        
        row2_layout.addSpacing(20)
        
        row2_layout.addWidget(QLabel("ค้นหา"))
        self.search_field_combo = QComboBox()
        self.search_field_combo.addItems(["Code", "Location", "Roll ID", "Lot"])
        self.search_field_combo.setMaximumWidth(140)
        self.search_field_combo.currentIndexChanged.connect(self.on_filters_changed)
        row2_layout.addWidget(self.search_field_combo)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Code / Location / Roll ID / Lot")
        self.search_input.setMaximumWidth(200)
        self.search_input.textChanged.connect(self.on_filters_changed)
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
        self.data_table.setColumnCount(11)
        self.data_table.setHorizontalHeaderLabels([
            "Code", "Roll ID", "SubPartCode", "SupCode", "Supplier Name", "Description", "Lot No.",
            "Location", "Unit", "Exist_Qty", "RollStatus"
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
            if hasattr(self.storage, "search_rolls"):
                self.rolls = self.storage.search_rolls()
            elif hasattr(self.storage, "get_all_rolls"):
                self.rolls = self.storage.get_all_rolls()
            else:
                self.rolls = []
            self.display_suppliers_data()
        except Exception as e:
            QMessageBox.critical(self, "ข้อผิดพลาด", f"Error loading statistics: {e}")
    
    def on_filters_changed(self, *_):
        """Handle any filter change"""
        self.display_suppliers_data()
    
    def display_suppliers_data(self):
        """Display combined supplier and roll data in table"""
        try:
            supplier_name = self.suppliers_input.text().strip()
            search_query = self.search_input.text().strip()
            search_field = self.search_field_combo.currentText()

            supplier_records = self.suppliers_manager.search_combined(supplier_name, search_query)

            # Prepare roll lookups
            roll_by_id: Dict[str, Roll] = {}
            rolls_by_code: Dict[str, List[Roll]] = {}
            if self.rolls:
                for roll in self.rolls:
                    roll_by_id[roll.roll_id] = roll
                    code_key = roll.sku or roll.pdt_code or ""
                    if code_key:
                        rolls_by_code.setdefault(code_key, []).append(roll)

            def matches_roll_filters(roll: Roll) -> bool:
                if supplier_name and supplier_name.lower() not in (roll.spl_name or "").lower():
                    return False
                if not search_query:
                    return True
                target = ""
                if search_field == "Code":
                    target = roll.sku or roll.pdt_code or ""
                elif search_field == "Location":
                    target = roll.location or ""
                elif search_field == "Roll ID":
                    target = roll.roll_id or ""
                elif search_field == "Lot":
                    target = roll.lot or ""
                return search_query.lower() in str(target).lower()

            def matches_row_filters(row_data: Dict[str, str]) -> bool:
                if supplier_name:
                    supplier_text = str(row_data.get("Supplier Name", row_data.get("Suppliers", ""))).lower()
                    if supplier_name.lower() not in supplier_text:
                        return False
                if not search_query:
                    return True
                if search_field == "Code":
                    target = row_data.get("Code", "")
                elif search_field == "Location":
                    target = row_data.get("Location", "")
                elif search_field == "Roll ID":
                    target = row_data.get("Roll ID", "")
                else:  # Lot
                    target = row_data.get("Lot No.", row_data.get("lot", ""))
                return search_query.lower() in str(target).lower()

            table_rows: List[Dict[str, str]] = []
            used_roll_ids: set[str] = set()

            search_type = "supplier" if supplier_name else "all"

            for record in supplier_records:
                row_data = self.suppliers_manager.get_row_data(record, search_type)
                if not matches_row_filters(row_data):
                    continue

                code_value = row_data.get("Code", "")
                roll_id_value = row_data.get("Roll ID", "")

                matching_rolls: List[Roll] = []
                if roll_id_value:
                    roll_match = roll_by_id.get(roll_id_value)
                    if roll_match and matches_roll_filters(roll_match):
                        matching_rolls.append(roll_match)
                if not matching_rolls and code_value:
                    for roll in rolls_by_code.get(code_value, []):
                        if matches_roll_filters(roll):
                            matching_rolls.append(roll)

                exist_qty_value = 0.0
                roll_status_value = ""
                if matching_rolls:
                    exist_qty_value = sum((roll.current_length or 0.0) for roll in matching_rolls)
                    original_total = sum((roll.original_length or 0.0) for roll in matching_rolls)
                    roll_status_value = "เต็มม้วน" if exist_qty_value >= original_total else "เศษ"
                    for roll in matching_rolls:
                        used_roll_ids.add(roll.roll_id)
                else:
                    exist_text = row_data.get("Exist. Qty")
                    if isinstance(exist_text, (int, float)) and not math.isnan(exist_text):
                        exist_qty_value = float(exist_text)
                    else:
                        exist_qty_value = 0.0

                table_rows.append({
                    "Code": row_data.get("Code", ""),
                    "Roll ID": row_data.get("Roll ID", ""),
                    "SubPartCode": row_data.get("SubPartCode", ""),
                    "SupCode": row_data.get("SupCode", ""),
                    "Supplier Name": row_data.get("Supplier Name", row_data.get("Suppliers", "")),
                    "Description": row_data.get("Description", ""),
                    "Lot No.": row_data.get("Lot No.", row_data.get("lot", "")),
                    "Location": row_data.get("Location", ""),
                    "Unit": row_data.get("Unit", ""),
                    "Exist_Qty": f"{exist_qty_value:.2f}" if exist_qty_value else "",
                    "RollStatus": roll_status_value
                })

            # Include rolls not represented in supplier data (e.g., new entries)
            if self.rolls:
                for roll in self.rolls:
                    if roll.roll_id in used_roll_ids:
                        continue
                    if not matches_roll_filters(roll):
                        continue
                    code_value = roll.sku or roll.pdt_code or ""
                    table_rows.append({
                        "Code": code_value,
                        "Roll ID": roll.roll_id,
                        "SubPartCode": roll.subpart_code or "",
                        "SupCode": roll.sup_code or "",
                        "Supplier Name": roll.spl_name or "",
                        "Description": roll.pdt_name or roll.specification or "",
                        "Lot No.": roll.lot or "",
                        "Location": roll.location or "",
                        "Unit": roll.unit_type or roll.packing_unit or "",
                        "Exist_Qty": f"{(roll.current_length or 0.0):.2f}" if roll.current_length is not None else "",
                        "RollStatus": "เต็มม้วน" if roll.current_length >= (roll.original_length or 0.0) else "เศษ"
                    })

            self.display_table_data(table_rows)

        except Exception as e:
            QMessageBox.critical(self, "ข้อผิดพลาด", f"Error displaying reports: {e}")
    
    def display_table_data(self, rows: List[Dict[str, str]]):
        """Display rows in the table, preserving legacy columns and new metrics"""
        headers = [
            "Code", "Roll ID", "SubPartCode", "SupCode", "Supplier Name", "Description",
            "Lot No.", "Location", "Unit", "Exist_Qty", "RollStatus"
        ]
        self.data_table.setColumnCount(len(headers))
        self.data_table.setHorizontalHeaderLabels(headers)

        self.data_table.setRowCount(len(rows))
        for row_idx, data in enumerate(rows):
            for col_idx, header in enumerate(headers):
                value = data.get(header, "")
                item = QTableWidgetItem(str(value))
                if header == "RollStatus":
                    status_text = str(value).strip()
                    if status_text == "เต็มม้วน":
                        item.setForeground(Qt.darkGreen)
                    elif status_text:
                        item.setForeground(Qt.darkRed)
                self.data_table.setItem(row_idx, col_idx, item)

        self.data_table.resizeColumnsToContents()
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
