from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QScrollArea, QFrame, QGridLayout, QSplitter
)
from PySide6.QtGui import QColor, QBrush
from utils.suppliers_manager import SuppliersManager

# Import Controller
from controllers.statistics_controller import StatisticsController

class StatisticsTab(QWidget):
    def __init__(self, storage, current_user=None):
        super().__init__()
        self.storage = storage
        self.current_user = current_user
        self.suppliers_manager = SuppliersManager()
        self.controller = StatisticsController(self, storage, self.suppliers_manager)
        self.setup_ui()
        self.controller.refresh_data()

    def setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # 1. Filter Area (Fixed at top)
        filter_group = QGroupBox("ตัวกรองรายงานแบบละเอียด / Advanced Filters")
        grid_layout = QGridLayout()
        
        # Row 1: Supplier & Basic Search
        self.suppliers_input = QLineEdit()
        self.suppliers_input.setPlaceholderText("ชื่อ Supplier...")
        self.suppliers_input.textChanged.connect(self.controller.refresh_data)
        
        self.search_field_combo = QComboBox()
        self.search_field_combo.addItems(["Code", "Description", "Location", "Roll ID", "Lot"])
        self.search_field_combo.currentIndexChanged.connect(self.controller.refresh_data)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ค้นหาข้อมูลสินค้า...")
        self.search_input.textChanged.connect(self.controller.refresh_data)
        
        grid_layout.addWidget(QLabel("Supplier:"), 0, 0)
        grid_layout.addWidget(self.suppliers_input, 0, 1)
        grid_layout.addWidget(QLabel("ค้นหาโดย:"), 0, 2)
        grid_layout.addWidget(self.search_field_combo, 0, 3)
        grid_layout.addWidget(self.search_input, 0, 4)
        
        # Row 2: Color & Length Range
        self.color_input = QLineEdit()
        self.color_input.setPlaceholderText("ระบุสี...")
        self.color_input.textChanged.connect(self.controller.refresh_data)
        
        self.min_len_input = QLineEdit()
        self.min_len_input.setPlaceholderText("Min...")
        self.min_len_input.setFixedWidth(60)
        self.min_len_input.textChanged.connect(self.controller.refresh_data)
        
        self.max_len_input = QLineEdit()
        self.max_len_input.setPlaceholderText("Max...")
        self.max_len_input.setFixedWidth(60)
        self.max_len_input.textChanged.connect(self.controller.refresh_data)
        
        grid_layout.addWidget(QLabel("สีผ้า (Color):"), 1, 0)
        grid_layout.addWidget(self.color_input, 1, 1)
        
        len_range_layout = QHBoxLayout()
        len_range_layout.addWidget(QLabel("ความยาว (เมตร):"))
        len_range_layout.addWidget(self.min_len_input)
        len_range_layout.addWidget(QLabel("-"))
        len_range_layout.addWidget(self.max_len_input)
        len_range_layout.addStretch()
        grid_layout.addLayout(len_range_layout, 1, 2, 1, 3)
        
        filter_group.setLayout(grid_layout)
        main_layout.addWidget(filter_group)
        
        # 2. Action Buttons (Fixed at top)
        btn_layout = QHBoxLayout()
        self.export_btn = QPushButton("Export to CSV")
        self.refresh_btn = QPushButton("Refresh")
        self.export_btn.clicked.connect(self.controller.export_data)
        self.refresh_btn.clicked.connect(self.controller.refresh_data)
        btn_layout.addStretch()
        btn_layout.addWidget(self.export_btn)
        btn_layout.addWidget(self.refresh_btn)
        main_layout.addLayout(btn_layout)

        # 3. Splitter for independent scrolling tables
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # --- Section 1: Current Stock ---
        stock_container = QWidget()
        stock_layout = QVBoxLayout(stock_container)
        stock_layout.setContentsMargins(0, 5, 0, 0)
        stock_layout.addWidget(QLabel("📊 <b>สต็อกคงเหลือ (Current Stock)</b>"))
        
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(11)
        self.data_table.setHorizontalHeaderLabels([
            "Code", "Roll ID", "SubPartCode", "SupCode", "Supplier Name", 
            "Description", "Lot No.", "Location", "Unit", "Length", "Status"
        ])
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.data_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.data_table.setSortingEnabled(True)
        stock_layout.addWidget(self.data_table)
        
        # Count Label
        self.stock_count_label = QLabel("แสดงผล: 0 จากทั้งหมด 0 ม้วน")
        self.stock_count_label.setStyleSheet("font-weight: bold; color: #555; margin-top: 2px;")
        stock_layout.addWidget(self.stock_count_label)
        
        # Load More
        self.load_more_btn = QPushButton("Load More Stock...")
        self.load_more_btn.clicked.connect(self.controller.load_next_batch)
        self.load_more_btn.hide()
        stock_layout.addWidget(self.load_more_btn)
        
        splitter.addWidget(stock_container)

        # --- Section 2: Dispatch History ---
        dispatch_container = QWidget()
        dispatch_layout = QVBoxLayout(dispatch_container)
        dispatch_layout.setContentsMargins(0, 5, 0, 0)
        dispatch_layout.addWidget(QLabel("📜 <b>ประวัติการเบิกจ่าย (Dispatch History)</b>"))
        
        self.dispatch_table = QTableWidget()
        self.dispatch_table.setColumnCount(8)
        self.dispatch_table.setHorizontalHeaderLabels([
            "วันเวลาที่เบิก", "เลขที่ม้วนผ้า", "รหัสสินค้า", "เลขล็อต (Lot)", 
            "ชื่อลูกค้า", "เลขที่เอกสาร", "ผู้ทำรายการ",
            "ความยาวที่เบิก (ม.)"
        ])
        self.dispatch_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.dispatch_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.dispatch_table.setSortingEnabled(True)
        dispatch_layout.addWidget(self.dispatch_table)
        
        # Count Label
        self.dispatch_count_label = QLabel("ทั้งหมด: 0 รายการ")
        self.dispatch_count_label.setStyleSheet("font-weight: bold; color: #555; margin-top: 2px;")
        dispatch_layout.addWidget(self.dispatch_count_label)
        
        splitter.addWidget(dispatch_container)
        
        # Set initial sizes for splitter (50/50)
        main_layout.addWidget(splitter)
        splitter.setSizes([500, 500])

    def append_data_to_table(self, batch, is_first_batch=False):
        # ปิดการเรียงลำดับชั่วคราวเพื่อประสิทธิภาพและความถูกต้องขณะเพิ่มข้อมูล
        self.data_table.setSortingEnabled(False)
        
        if is_first_batch: self.data_table.setRowCount(0)
        for data in batch:
            row = self.data_table.rowCount()
            self.data_table.insertRow(row)
            self.data_table.setItem(row, 0, QTableWidgetItem(str(data.get("Code", ""))))
            self.data_table.setItem(row, 1, QTableWidgetItem(str(data.get("Roll ID", ""))))
            self.data_table.setItem(row, 2, QTableWidgetItem(str(data.get("SubPartCode", ""))))
            self.data_table.setItem(row, 3, QTableWidgetItem(str(data.get("SupCode", ""))))
            self.data_table.setItem(row, 4, QTableWidgetItem(str(data.get("Supplier Name", ""))))
            self.data_table.setItem(row, 5, QTableWidgetItem(str(data.get("Description", ""))))
            self.data_table.setItem(row, 6, QTableWidgetItem(str(data.get("Lot No.", ""))))
            self.data_table.setItem(row, 7, QTableWidgetItem(str(data.get("Location", ""))))
            self.data_table.setItem(row, 8, QTableWidgetItem(str(data.get("Unit", ""))))
            
            # แปลงเป็นตัวเลขสำหรับเรียงลำดับที่ถูกต้อง
            len_val = data.get("Length", "0.00")
            
            item_len = QTableWidgetItem()
            item_len.setData(Qt.ItemDataRole.DisplayRole, float(len_val))
            self.data_table.setItem(row, 9, item_len)
            
            status = data.get("Status", "")
            status_item = QTableWidgetItem(str(status))
            
            # ใส่สีตามสถานะ
            if "เต็มม้วน" in status:
                status_item.setBackground(QBrush(QColor("#c8e6c9"))) # เขียวอ่อน
            elif "เศษ" in status:
                status_item.setBackground(QBrush(QColor("#fff9c4"))) # เหลืองอ่อน
            elif "หมด" in status:
                status_item.setBackground(QBrush(QColor("#ffcdd2"))) # แดงอ่อน
                
            self.data_table.setItem(row, 10, status_item)
            
        # เปิดการเรียงลำดับกลับมา
        self.data_table.setSortingEnabled(True)
        self.data_table.resizeColumnsToContents()

    def append_dispatch_to_table(self, batch, is_first_batch=False):
        # ปิดการเรียงลำดับชั่วคราว
        self.dispatch_table.setSortingEnabled(False)
        
        if is_first_batch: self.dispatch_table.setRowCount(0)
        for data in batch:
            row = self.dispatch_table.rowCount()
            self.dispatch_table.insertRow(row)
            
            # 0. วันเวลาที่เบิก
            self.dispatch_table.setItem(row, 0, QTableWidgetItem(str(data.get("Timestamp", ""))))
            # 1. เลขที่ม้วนผ้า
            self.dispatch_table.setItem(row, 1, QTableWidgetItem(str(data.get("Roll ID", ""))))
            # 2. รหัสสินค้า
            self.dispatch_table.setItem(row, 2, QTableWidgetItem(str(data.get("Code", ""))))
            # 3. เลขล็อต (Lot)
            self.dispatch_table.setItem(row, 3, QTableWidgetItem(str(data.get("Lot No.", ""))))
            # 4. ชื่อลูกค้า
            self.dispatch_table.setItem(row, 4, QTableWidgetItem(str(data.get("Customer", ""))))
            # 5. เลขที่เอกสาร
            self.dispatch_table.setItem(row, 5, QTableWidgetItem(str(data.get("Doc No", ""))))
            # 6. ผู้ทำรายการ
            self.dispatch_table.setItem(row, 6, QTableWidgetItem(str(data.get("User", ""))))
            
            # 7. ความยาวที่เบิก (ม.) [ตัวเลขสำหรับเรียงลำดับ]
            item_len = QTableWidgetItem()
            item_len.setData(Qt.ItemDataRole.DisplayRole, float(data.get("Length", 0)))
            self.dispatch_table.setItem(row, 7, item_len)
            
        # เปิดการเรียงลำดับกลับมา
        self.dispatch_table.setSortingEnabled(True)
        self.dispatch_table.resizeColumnsToContents()
        self.dispatch_count_label.setText(f"ทั้งหมด: {self.dispatch_table.rowCount()} รายการ")

    def update_load_more_btn(self, current, total):
        if current < total:
            self.load_more_btn.setText(f"Load More ({current}/{total})")
            self.load_more_btn.show()
        else:
            self.load_more_btn.hide()
        self.stock_count_label.setText(f"แสดงผล: {current} จากทั้งหมด {total} ม้วน")
