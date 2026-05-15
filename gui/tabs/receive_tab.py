import os
import logging
logger = logging.getLogger(__name__)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QPushButton, QLabel, QSpinBox, QCompleter, QDoubleSpinBox
)
from PySide6.QtCore import Qt, Signal as pyqtSignal

# Import Controller
from controllers.receive_controller import ReceiveController
from utils.roll_id_generator import RollIDGenerator

class ReceiveTab(QWidget):
    refresh_reports = pyqtSignal()

    def __init__(self, storage, current_user=None):
        super().__init__()
        self.storage = storage
        self.current_user = current_user
        
        data_dir = os.path.join(os.getcwd(), "data")
        self.controller = ReceiveController(self, storage, RollIDGenerator(data_dir))
        
        self.setup_ui()
        self.setup_autocomplete()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_group = QGroupBox("ข้อมูลการรับม้วนผ้า / Receive Roll Information")
        self.form_layout = QFormLayout()

        self.manual_roll_id_label = QLabel("(ระบบจะสร้างให้อัตโนมัติ)")
        self.manual_code = QLineEdit()
        self.manual_subpart_code = QLineEdit()
        self.manual_sup_code = QLineEdit()
        self.manual_supplier_name = QLineEdit()
        self.manual_description = QLineEdit()
        self.manual_lot = QLineEdit()
        self.manual_quantity = QSpinBox()
        self.manual_quantity.setRange(1, 999)
        self.manual_location = QLineEdit()
        self.manual_unit = QLineEdit()
        self.manual_unit.setText("MTS")
        self.manual_length = QDoubleSpinBox()
        self.manual_length.setRange(0, 99999.99)
        self.manual_length.setDecimals(2)
        self.manual_length.setSuffix(" m")
        self.manual_length.setValue(0.0)
        self.manual_width = QDoubleSpinBox()
        self.manual_width.setRange(0, 9999.99)
        self.manual_width.setDecimals(2)
        self.manual_width.setSuffix(" m")
        self.manual_width.setValue(0.0)
        self.manual_colour = QLineEdit() # เพิ่ม Colour

        self.manual_code.textChanged.connect(self.controller.handle_sku_change)

        self.form_layout.addRow("Roll ID (เลขม้วนอัตโนมัติ):", self.manual_roll_id_label)
        self.form_layout.addRow("Code (รหัสสินค้า)*:", self.manual_code)
        self.form_layout.addRow("SubPartCode (รหัสผ้าย่อย):", self.manual_subpart_code)
        self.form_layout.addRow("SupCode (รหัสซัพพลายเออร์):", self.manual_sup_code)
        self.form_layout.addRow("Supplier Name (ชื่อผู้ผลิต/ผู้ขาย):", self.manual_supplier_name)
        self.form_layout.addRow("Description (รายละเอียดสินค้า):", self.manual_description)
        self.form_layout.addRow("Lot No. (เลขล็อตสินค้า)*:", self.manual_lot)
        self.form_layout.addRow("Colour (สี):", self.manual_colour)
        self.form_layout.addRow("Width (หน้ากว้าง):", self.manual_width)
        self.form_layout.addRow("Quantity (จำนวนม้วนที่รับเข้า):", self.manual_quantity)
        self.form_layout.addRow("Location (ที่เก็บสินค้า):", self.manual_location)
        self.form_layout.addRow("Unit (หน่วย):", self.manual_unit)
        self.form_layout.addRow("Length (ความยาวผ้า)*:", self.manual_length)
        
        form_group.setLayout(self.form_layout)

        btn_layout = QHBoxLayout()
        self.clear_btn = QPushButton("Clear")
        self.random_btn = QPushButton("Random (Test)")
        self.random_btn.hide()  # ซ่อนปุ่มชั่วคราว
        self.save_btn = QPushButton("Save Roll")
        self.save_btn.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold; height: 30px;")

        self.clear_btn.clicked.connect(self.clear_form)
        self.random_btn.clicked.connect(self.controller.handle_random_fill)
        self.save_btn.clicked.connect(self.controller.handle_submit)

        btn_layout.addStretch()
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addWidget(self.random_btn)
        btn_layout.addWidget(self.save_btn)

        layout.addWidget(form_group)
        layout.addLayout(btn_layout)
        layout.addStretch()

    def setup_autocomplete(self):
        """ตั้งค่า Auto Complete ให้กับช่องรหัสสินค้า"""
        skus = self.controller.get_sku_list()
        if skus:
            completer = QCompleter(skus)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains) # ค้นหาแบบมีส่วนใดส่วนหนึ่งตรงกัน
            self.manual_code.setCompleter(completer)
            # logger.info(f"Auto-complete set up with {len(skus)} SKUs")

    def get_form_data(self):
        return {
            'code': self.manual_code.text().strip().upper(),
            'sub_part_code': self.manual_subpart_code.text().strip(),
            'sup_code': self.manual_sup_code.text().strip(),
            'supplier_name': self.manual_supplier_name.text().strip(),
            'description': self.manual_description.text().strip(),
            'lot_no': self.manual_lot.text().strip().upper(),
            'quantity': self.manual_quantity.value(),
            'location': self.manual_location.text().strip(),
            'unit': self.manual_unit.text().strip(),
            'length': self.manual_length.value(),
            'width': self.manual_width.value(),
            'color': self.manual_colour.text().strip()
        }

    def fill_form_from_master(self, data):
        self.manual_subpart_code.blockSignals(True)
        self.manual_sup_code.blockSignals(True)
        self.manual_supplier_name.blockSignals(True)
        self.manual_description.blockSignals(True)
        self.manual_unit.blockSignals(True)
        
        self.manual_subpart_code.setText(data['sub_part'])
        self.manual_sup_code.setText(data['sup_code'])
        self.manual_supplier_name.setText(data['supplier'])
        self.manual_description.setText(data['desc'])
        self.manual_unit.setText(data.get('unit', "MTS"))
        if 'lot' in data: self.manual_lot.setText(data['lot'])
        if 'color' in data: self.manual_colour.setText(data['color'])
        if 'width' in data: 
            try:
                self.manual_width.setValue(float(data['width']))
            except:
                self.manual_width.setValue(0.0)
        if 'location' in data: self.manual_location.setText(data['location'])
        if 'length' in data: 
            try:
                self.manual_length.setValue(float(data['length']))
            except:
                self.manual_length.setValue(0.0)
        if 'qty' in data: self.manual_quantity.setValue(data['qty'])
        
        self.manual_subpart_code.blockSignals(False)
        self.manual_sup_code.blockSignals(False)
        self.manual_supplier_name.blockSignals(False)
        self.manual_description.blockSignals(False)
        self.manual_unit.blockSignals(False)

    def clear_product_fields(self):
        """ล้างเฉพาะข้อมูลที่ดึงมาจาก Master Data"""
        self.manual_subpart_code.clear()
        self.manual_sup_code.clear()
        self.manual_supplier_name.clear()
        self.manual_description.clear()
        self.manual_unit.setText("MTS")

    def fill_entire_form(self, data):
        self.manual_code.setText(data['code'])
        self.manual_subpart_code.setText(data['sub_part'])
        self.manual_sup_code.setText(data['sup_code'])
        self.manual_supplier_name.setText(data['supplier'])
        self.manual_description.setText(data['desc'])
        self.manual_lot.setText(data['lot'])
        self.manual_colour.setText(data.get('color', ""))
        try:
            self.manual_width.setValue(float(data.get('width', 0.0)))
        except:
            self.manual_width.setValue(0.0)
        self.manual_location.setText(data['location'])
        try:
            self.manual_length.setValue(float(data.get('length', 0.0)))
        except:
            self.manual_length.setValue(0.0)
        self.manual_quantity.setValue(data['qty'])

    def fill_roll_fields_only(self, data):
        """เติมเฉพาะข้อมูลที่เกี่ยวกับม้วน (ไม่ทับข้อมูลสินค้า)"""
        self.manual_lot.setText(data['lot'])
        self.manual_colour.setText(data.get('color', ""))
        try:
            self.manual_width.setValue(float(data.get('width', 0.0)))
        except:
            self.manual_width.setValue(0.0)
        self.manual_location.setText(data['location'])
        try:
            self.manual_length.setValue(float(data.get('length', 0.0)))
        except:
            self.manual_length.setValue(0.0)
        self.manual_quantity.setValue(data['qty'])

    def clear_form(self):
        for i in range(self.form_layout.count()):
            widget = self.form_layout.itemAt(i).widget()
            if isinstance(widget, QLineEdit):
                widget.clear()
        
        self.manual_width.setValue(0.0)
        self.manual_length.setValue(0.0)
        self.manual_quantity.setValue(1)
        self.manual_unit.setText("MTS")

    def switch_to_rolls_tab(self):
        main_window = self.window()
        if hasattr(main_window, 'tab_widget'):
            for i in range(main_window.tab_widget.count()):
                if "Rolls" in main_window.tab_widget.tabText(i) or "ม้วน" in main_window.tab_widget.tabText(i):
                    main_window.tab_widget.setCurrentIndex(i)
                    break
