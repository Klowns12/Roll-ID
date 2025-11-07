from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QPushButton, QMessageBox, QLabel, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal as pyqtSignal
from PySide6.QtGui import QDoubleValidator
from datetime import datetime

class DispatchQuantityDialog(QDialog):
    """Dialog สำหรับกรอกจำนวนที่ต้องการเบิกออก"""
    
    def __init__(self, roll_id, available_length, parent=None):
        super().__init__(parent)
        self.roll_id = roll_id
        self.available_length = available_length
        self.dispatch_length = 0.0
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("เบิกออก - Dispatch")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Info group
        info_group = QGroupBox("ข้อมูลม้วนผ้า")
        info_layout = QFormLayout()
        
        self.roll_id_label = QLabel(self.roll_id)
        self.roll_id_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        info_layout.addRow("เลขม้วน:", self.roll_id_label)
        
        self.available_label = QLabel(f"{self.available_length:.2f} cm")
        self.available_label.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")
        info_layout.addRow("ความยาวคงเหลือ:", self.available_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Dispatch group
        dispatch_group = QGroupBox("จำนวนที่ต้องการเบิก")
        dispatch_layout = QFormLayout()
        
        self.length_input = QDoubleSpinBox()
        self.length_input.setRange(0.01, self.available_length)
        self.length_input.setDecimals(2)
        self.length_input.setSuffix(" cm")
        self.length_input.setValue(self.available_length)
        self.length_input.setMinimumWidth(200)
        self.length_input.valueChanged.connect(self.update_remaining)
        dispatch_layout.addRow("ความยาวที่เบิก:", self.length_input)
        
        self.remaining_label = QLabel("0.00 cm")
        self.remaining_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        dispatch_layout.addRow("คงเหลือหลังเบิก:", self.remaining_label)
        
        dispatch_group.setLayout(dispatch_layout)
        layout.addWidget(dispatch_group)
        
        # Quick select buttons
        quick_layout = QHBoxLayout()
        quick_layout.addWidget(QLabel("เลือกด่วน:"))
        
        for percent in [25, 50, 75, 100]:
            btn = QPushButton(f"{percent}%")
            btn.clicked.connect(lambda checked, p=percent: self.set_percentage(p))
            quick_layout.addWidget(btn)
        
        layout.addLayout(quick_layout)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Initial update
        self.update_remaining()
    
    def set_percentage(self, percent):
        """ตั้งค่าเปอร์เซ็นต์ที่ต้องการเบิก"""
        value = self.available_length * (percent / 100.0)
        self.length_input.setValue(value)
    
    def update_remaining(self):
        """อัพเดทจำนวนคงเหลือ"""
        dispatch = self.length_input.value()
        remaining = self.available_length - dispatch
        self.remaining_label.setText(f"{remaining:.2f} cm")
        
        if remaining < 0:
            self.remaining_label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
        elif remaining == 0:
            self.remaining_label.setStyleSheet("color: orange; font-weight: bold; font-size: 14px;")
        else:
            self.remaining_label.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")
    
    def get_dispatch_length(self):
        """ดึงค่าความยาวที่เบิก"""
        return self.length_input.value()


class DispatchTab(QWidget):
    """Tab สำหรับการเบิกออก (Dispatch) ของม้วนผ้า"""
    
    dispatch_completed = pyqtSignal(dict)
    
    def __init__(self, storage):
        super().__init__()
        self.storage = storage
        self.setup_ui()
    
    def setup_ui(self):
        """สร้าง UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("เบิกออก / Dispatch")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # Scan section
        scan_group = QGroupBox("สแกน QR Code")
        scan_layout = QVBoxLayout()
        
        # Scan input
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("เลขม้วน:"))
        
        self.roll_id_input = QLineEdit()
        self.roll_id_input.setPlaceholderText("สแกนหรือพิมพ์เลขม้วน (เช่น RM2061406001)")
        self.roll_id_input.returnPressed.connect(self.process_scan)
        input_layout.addWidget(self.roll_id_input)
        
        self.scan_btn = QPushButton("ประมวลผล")
        self.scan_btn.clicked.connect(self.process_scan)
        self.scan_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px;")
        input_layout.addWidget(self.scan_btn)
        
        scan_layout.addLayout(input_layout)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        self.status_label.setWordWrap(True)
        scan_layout.addWidget(self.status_label)
        
        scan_group.setLayout(scan_layout)
        layout.addWidget(scan_group)
        
        # Recent dispatches
        history_group = QGroupBox("ประวัติการเบิกล่าสุด")
        history_layout = QVBoxLayout()
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "เวลา", "เลขม้วน", "SKU", "เบิกออก (cm)", "คงเหลือ (cm)", "สถานะ"
        ])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        history_layout.addWidget(self.history_table)
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)
        
        # Load recent history
        self.load_recent_history()
    
    def process_scan(self):
        """ประมวลผลการสแกน"""
        roll_id = self.roll_id_input.text().strip()
        
        if not roll_id:
            QMessageBox.warning(self, "ข้อผิดพลาด", "กรุณากรอกเลขม้วน")
            return
        
        # ตรวจสอบว่ามีม้วนนี้ในระบบหรือไม่
        roll = self.storage.get_roll_by_id(roll_id)
        
        if not roll:
            self.status_label.setText(f"❌ ไม่พบม้วนเลข {roll_id} ในระบบ")
            self.status_label.setStyleSheet("padding: 10px; background-color: #ffebee; border-radius: 5px; color: red;")
            QMessageBox.warning(
                self,
                "ไม่พบข้อมูล",
                f"ไม่พบม้วนเลข {roll_id} ในระบบ\n\nกรุณาตรวจสอบเลขม้วนหรือรับเข้าก่อน"
            )
            return
        
        # ตรวจสอบสถานะม้วน
        if roll.status != 'active':
            self.status_label.setText(f"❌ ม้วนเลข {roll_id} ถูกใช้งานหมดแล้ว")
            self.status_label.setStyleSheet("padding: 10px; background-color: #ffebee; border-radius: 5px; color: red;")
            QMessageBox.warning(
                self,
                "ไม่สามารถเบิกได้",
                f"ม้วนเลข {roll_id} ถูกใช้งานหมดแล้ว (สถานะ: {roll.status})"
            )
            return
        
        # แสดงข้อมูลม้วน
        self.status_label.setText(
            f"✓ พบม้วน: {roll_id}\n"
            f"SKU: {roll.sku} | Lot: {roll.lot}\n"
            f"ความยาวคงเหลือ: {roll.current_length:.2f} cm"
        )
        self.status_label.setStyleSheet("padding: 10px; background-color: #e8f5e9; border-radius: 5px; color: green;")
        
        # เปิด Dialog สำหรับกรอกจำนวนที่เบิก
        dialog = DispatchQuantityDialog(roll_id, roll.current_length, self)
        
        if dialog.exec() == QDialog.Accepted:
            dispatch_length = dialog.get_dispatch_length()
            self.dispatch_roll(roll, dispatch_length)
    
    def dispatch_roll(self, roll, dispatch_length):
        """เบิกออกม้วนผ้า"""
        try:
            # คำนวณความยาวคงเหลือ
            new_length = roll.current_length - dispatch_length
            
            # อัพเดทความยาวคงเหลือ
            roll.current_length = new_length
            
            # อัพเดทสถานะถ้าใช้หมด
            if new_length <= 0:
                roll.status = 'depleted'
                roll.current_length = 0
            
            # บันทึกการเปลี่ยนแปลง
            self.storage.update_roll(
                roll.roll_id,
                current_length=roll.current_length,
                status=roll.status
            )
            
            # บันทึก log
            self.storage.add_log(
                action="dispatch",
                roll_id=roll.roll_id,
                details={
                    'sku': roll.sku,
                    'lot': roll.lot,
                    'dispatch_length': dispatch_length,
                    'remaining_length': roll.current_length,
                    'status': roll.status
                }
            )
            
            # แสดงผลลัพธ์
            if roll.status == 'depleted':
                result_msg = (
                    f"✓ เบิกออกสำเร็จ!\n"
                    f"เลขม้วน: {roll.roll_id}\n"
                    f"เบิกออก: {dispatch_length:.2f} cm\n"
                    f"⚠️ ม้วนนี้ถูกใช้หมดแล้ว"
                )
            else:
                result_msg = (
                    f"✓ เบิกออกสำเร็จ!\n"
                    f"เลขม้วน: {roll.roll_id}\n"
                    f"เบิกออก: {dispatch_length:.2f} cm\n"
                    f"คงเหลือ: {roll.current_length:.2f} cm"
                )
            
            self.status_label.setText(result_msg)
            self.status_label.setStyleSheet("padding: 10px; background-color: #e3f2fd; border-radius: 5px; color: blue;")
            
            QMessageBox.information(
                self,
                "สำเร็จ",
                result_msg
            )
            
            # ล้างฟอร์ม
            self.roll_id_input.clear()
            self.roll_id_input.setFocus()
            
            # อัพเดทประวัติ
            self.load_recent_history()
            
            # ส่ง signal
            self.dispatch_completed.emit({
                'roll_id': roll.roll_id,
                'sku': roll.sku,
                'dispatch_length': dispatch_length,
                'remaining_length': roll.current_length,
                'status': roll.status
            })
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "ข้อผิดพลาด",
                f"เกิดข้อผิดพลาดในการเบิกออก:\n{str(e)}"
            )
    
    def load_recent_history(self):
        """โหลดประวัติการเบิกล่าสุด"""
        try:
            # ดึง log ที่เป็น dispatch
            logs = self.storage.get_logs()
            dispatch_logs = [log for log in logs if log.action == 'dispatch']
            
            # เรียงตามเวลาล่าสุด
            dispatch_logs.sort(key=lambda x: x.timestamp, reverse=True)
            
            # แสดงแค่ 20 รายการล่าสุด
            dispatch_logs = dispatch_logs[:20]
            
            # อัพเดทตาราง
            self.history_table.setRowCount(len(dispatch_logs))
            
            for row, log in enumerate(dispatch_logs):
                details = log.details
                
                # เวลา
                # Handle both string and datetime timestamp
                if isinstance(log.timestamp, str):
                    timestamp_str = log.timestamp
                else:
                    timestamp_str = log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                time_item = QTableWidgetItem(timestamp_str)
                self.history_table.setItem(row, 0, time_item)
                
                # เลขม้วน
                roll_id_item = QTableWidgetItem(log.roll_id)
                self.history_table.setItem(row, 1, roll_id_item)
                
                # SKU
                sku_item = QTableWidgetItem(details.get('sku', ''))
                self.history_table.setItem(row, 2, sku_item)
                
                # จำนวนที่เบิก
                dispatch_item = QTableWidgetItem(f"{details.get('dispatch_length', 0):.2f}")
                self.history_table.setItem(row, 3, dispatch_item)
                
                # คงเหลือ
                remaining_item = QTableWidgetItem(f"{details.get('remaining_length', 0):.2f}")
                self.history_table.setItem(row, 4, remaining_item)
                
                # สถานะ
                status = details.get('status', 'active')
                status_text = "ใช้หมด" if status == 'depleted' else "ยังใช้ได้"
                status_item = QTableWidgetItem(status_text)
                if status == 'depleted':
                    status_item.setForeground(Qt.red)
                else:
                    status_item.setForeground(Qt.green)
                self.history_table.setItem(row, 5, status_item)
            
            # ปรับขนาดคอลัมน์
            self.history_table.resizeColumnsToContents()
            
        except Exception as e:
            print(f"Error loading dispatch history: {e}")
