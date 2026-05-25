from io import BytesIO
import qrcode
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal as pyqtSignal
from PySide6.QtGui import QPixmap
from utils.mobile_connection_server import MobileConnectionServer

# Import Controller
from controllers.dispatch_controller import DispatchController

class DispatchTab(QWidget):
    dispatch_completed = pyqtSignal(dict)

    def __init__(self, storage, current_user=None):
        super().__init__()
        self.storage = storage
        self.current_user = current_user
        self.controller = DispatchController(self, storage)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        scan_group = QGroupBox("เบิกออกม้วนผ้า (Scan / Dispatch)")
        scan_layout = QVBoxLayout()
        
        input_layout = QHBoxLayout()
        self.roll_id_input = QLineEdit()
        self.roll_id_input.setPlaceholderText("สแกน QR หรือระบุเลขม้วน...")
        self.roll_id_input.returnPressed.connect(self.process_scan_input)
        
        self.scan_btn = QPushButton("ประมวลผล / Process")
        self.scan_btn.clicked.connect(self.process_scan_input)
        
        input_layout.addWidget(self.roll_id_input)
        input_layout.addWidget(self.scan_btn)
        
        self.mobile_btn = QPushButton("Connect Mobile Device")
        self.mobile_btn.clicked.connect(self.show_mobile_connection_qr)
        
        self.status_label = QLabel("พร้อมทำงาน")
        self.status_label.setStyleSheet("padding: 10px; background-color: #f9f9f9; border: 1px solid #ddd;")
        
        scan_layout.addLayout(input_layout)
        scan_layout.addWidget(self.mobile_btn)
        scan_layout.addWidget(self.status_label)
        scan_group.setLayout(scan_layout)
        
        history_group = QGroupBox("📜 ประวัติและบันทึกการเบิกจ่ายสินค้า (Dispatch History)")
        history_layout = QVBoxLayout()
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setSortingEnabled(True)
        self.history_table.setHorizontalHeaderLabels([
            "เวลา", "เลขม้วน", "Code", "เบิกออก", "เลขที่เอกสาร", "ลูกค้า"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        history_layout.addWidget(self.history_table)
        history_group.setLayout(history_layout)
        
        # Status label for counts
        self.count_label = QLabel("Total: 0 records")
        self.count_label.setStyleSheet("font-weight: bold; color: #555; margin-top: 5px;")
        
        layout.addWidget(scan_group)
        layout.addWidget(history_group)
        layout.addWidget(self.count_label)
        self.load_history()

    def show_status(self, message, color_type):
        colors = {"red": "#ffebee", "green": "#e8f5e9", "blue": "#e3f2fd"}
        text_colors = {"red": "red", "green": "green", "blue": "blue"}
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"padding: 10px; background-color: {colors.get(color_type, '#f9f9f9')}; color: {text_colors.get(color_type, 'black')};")

    def refresh_ui(self):
        self.roll_id_input.clear()
        self.roll_id_input.setFocus()
        self.load_history()

    def set_roll_id(self, roll_id):
        """กรอกเลขม้วนและเริ่มประมวลผลทันที"""
        self.roll_id_input.setText(roll_id)
        self.process_scan_input()

    def process_scan_input(self):
        roll_id = self.roll_id_input.text()
        roll = self.controller.get_and_validate_roll(roll_id)
        if not roll:
            return
        
        dialog = DispatchQuantityDialog(roll, self)
        if dialog.exec() == QDialog.Accepted:
            dispatch_data = dialog.get_dispatch_data()
            self.controller.execute_dispatch(roll, dispatch_data)

    def load_history(self):
        self.history_table.setSortingEnabled(False) # ปิดชั่วคราว
        # ดึงข้อมูลจากตาราง dispatch โดยตรง
        history = self.storage.get_dispatch_history(limit=15)
        self.history_table.setRowCount(0)
        for item in history:
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)
            self.history_table.setItem(row, 0, QTableWidgetItem(str(item.get('timestamp', ""))))
            self.history_table.setItem(row, 1, QTableWidgetItem(str(item.get('roll_id', ""))))
            self.history_table.setItem(row, 2, QTableWidgetItem(str(item.get('pdt_code', ""))))
            
            # จัดการตัวเลขความยาวเบิกเพื่อให้ Sort ได้ถูกต้อง
            len_item = QTableWidgetItem()
            len_val = item.get('length_dispatched', 0)
            len_item.setData(Qt.ItemDataRole.EditRole, float(len_val if len_val is not None else 0))
            self.history_table.setItem(row, 3, len_item)
            
            self.history_table.setItem(row, 4, QTableWidgetItem(str(item.get('document_no', "-"))))
            
            # รวมชื่อและรหัสลูกค้า
            cus_code = item.get('customer_code', '')
            cus_name = item.get('customer_name', '')
            customer = f"{cus_code} {cus_name}".strip()
            self.history_table.setItem(row, 5, QTableWidgetItem(customer or "-"))
            
        self.history_table.setSortingEnabled(True) # เปิดใช้งาน Sort
        self.count_label.setText(f"Showing: {len(history)} recent records")

    def show_mobile_connection_qr(self):
        # ใช้ server จาก MainWindow
        main_win = self.window()
        if not hasattr(main_win, 'mobile_server'):
            QMessageBox.critical(self, "Error", "Mobile server not initialized")
            return
            
        qr_url = main_win.mobile_server.url
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        qr_img.save(buffer, format="PNG")
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.getvalue())
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Connect Mobile (Centralized)")
        l = QVBoxLayout(dialog)
        img_label = QLabel()
        img_label.setPixmap(pixmap)
        l.addWidget(QLabel(f"Scan this URL to connect: {qr_url}"))
        l.addWidget(img_label)
        dialog.exec()

class DispatchQuantityDialog(QDialog):
    def __init__(self, roll, parent=None):
        super().__init__(parent)
        self.roll = roll
        self.setWindowTitle(f"เบิกออกม้วนผ้า: {roll.roll_id}")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # 1. ข้อมูลม้วนผ้าที่กำลังเบิก
        info_group = QGroupBox("ข้อมูลม้วนผ้า (Roll Info)")
        info_layout = QFormLayout()
        info_layout.addRow("Roll ID:", QLabel(f"<b>{roll.roll_id}</b>"))
        info_layout.addRow("Code:", QLabel(roll.code))
        info_layout.addRow("Lot No.:", QLabel(roll.lot_no))
        info_layout.addRow("Color/Width:", QLabel(f"{roll.color} / {roll.width} m"))
        info_layout.addRow("ความยาวคงเหลือเดิม:", QLabel(f"{roll.length:.2f} m"))
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # 2. ข้อมูลการเบิกจ่าย
        dispatch_group = QGroupBox("รายละเอียดการเบิก (Dispatch Details)")
        f = QFormLayout()
        
        self.dispatch_input = QLineEdit()
        self.dispatch_input.setPlaceholderText("ระบุความยาวที่ต้องการเบิก...")
        self.dispatch_input.textChanged.connect(self.update_remaining)
        
        self.doc_input = QLineEdit()
        self.doc_input.setPlaceholderText("เช่น IV66001...")
        self.doc_input.textChanged.connect(self.update_remaining)
        
        self.cus_code_input = QLineEdit()
        self.cus_code_input.textChanged.connect(self.update_remaining)
        self.cus_code_input.editingFinished.connect(self.fetch_customer_name)
        
        self.cus_name_input = QLineEdit()
        self.cus_name_input.setReadOnly(True)
        self.cus_name_input.setPlaceholderText("จะแสดงชื่อลูกค้าเมื่อค้นหาด้วยรหัสสำเร็จ...")
        self.cus_name_input.textChanged.connect(self.update_remaining)
        
        self.remaining_label = QLabel(f"{roll.length:.2f} m")
        self.remaining_label.setStyleSheet("font-weight: bold; color: blue;")
        
        f.addRow("จำนวนที่ต้องการเบิก (Length)*:", self.dispatch_input)
        f.addRow("เลขที่จ่ายสินค้า (Doc No.):", self.doc_input)
        f.addRow("รหัสลูกค้า (Customer Code):", self.cus_code_input)
        f.addRow("ชื่อลูกค้า (Customer Name):", self.cus_name_input)
        f.addRow("คงเหลือหลังเบิก (Remaining):", self.remaining_label)
        
        dispatch_group.setLayout(f)
        layout.addWidget(dispatch_group)
        
        self.btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.btns.accepted.connect(self.accept)
        self.btns.rejected.connect(self.reject)
        self.ok_button = self.btns.button(QDialogButtonBox.Ok)
        layout.addWidget(self.btns)

    def fetch_customer_name(self):
        code = self.cus_code_input.text().strip()
        if code:
            from core.customer import fetch_customer_by_id
            result = fetch_customer_by_id(code)
            if result:
                _, name = result
                self.cus_name_input.setText(name)
                self.update_remaining()

    def update_remaining(self):
        try:
            val = float(self.dispatch_input.text() or 0)
            rem = self.roll.length - val
            
            # ตรวจสอบว่าฟิลด์อื่นๆ ว่างหรือไม่
            has_all_info = all([
                self.doc_input.text().strip(),
                self.cus_code_input.text().strip(),
                self.cus_name_input.text().strip()
            ])
            
            if val <= 0:
                self.ok_button.setEnabled(False)
                self.remaining_label.setText(f"{self.roll.length:.2f} {self.roll.unit}")
                self.remaining_label.setStyleSheet("font-weight: bold; color: blue;")
            elif rem < 0:
                self.remaining_label.setText("เบิกเกินจำนวนที่มี!")
                self.remaining_label.setStyleSheet("font-weight: bold; color: red;")
                self.ok_button.setEnabled(False)
            elif not has_all_info:
                self.remaining_label.setText("กรุณากรอกข้อมูลให้ครบทุกช่อง*")
                self.remaining_label.setStyleSheet("font-weight: bold; color: orange;")
                self.ok_button.setEnabled(False)
            else:
                self.remaining_label.setText(f"{rem:.2f} {self.roll.unit}")
                self.ok_button.setEnabled(True)
                if rem == 0:
                    self.remaining_label.setStyleSheet("font-weight: bold; color: orange;")
                else:
                    self.remaining_label.setStyleSheet("font-weight: bold; color: blue;")
        except:
            self.remaining_label.setText(f"{self.roll.length:.2f} {self.roll.unit}")
            self.ok_button.setEnabled(False)

    def get_dispatch_data(self):
        return {
            "length": self.dispatch_input.text(),
            "doc_no": self.doc_input.text(),
            "cus_code": self.cus_code_input.text(),
            "cus_name": self.cus_name_input.text()
        }
