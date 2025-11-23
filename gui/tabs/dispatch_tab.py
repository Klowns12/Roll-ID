from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QPushButton, QMessageBox, QLabel, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal as pyqtSignal
from PySide6.QtGui import QDoubleValidator, QPixmap
from datetime import datetime
from io import BytesIO
import socket
import qrcode

from utils.mobile_connection_server import MobileConnectionServer

class DispatchQuantityDialog(QDialog):
    """Dialog สำหรับกรอกจำนวนที่ต้องการเบิกออก"""
    
    def __init__(self, roll_id, available_length, width="", parent=None):
        super().__init__(parent)
        self.roll_id = roll_id
        try:
            self.available_length = float(available_length)
        except (TypeError, ValueError):
            self.available_length = 0.0
        self.width = width
        self.dispatch_width = ""
        self.setup_ui()

        self.mobile_qr_dialog = None
    
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
        
        self.width_label = QLabel(self.width)
        self.width_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        info_layout.addRow("Width ปัจจุบัน:", self.width_label)
        self.length_label = QLabel(f"{self.available_length:.2f} cm" if self.available_length else "-")
        self.length_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        info_layout.addRow("Length ปัจจุบัน:", self.length_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Dispatch group
        dispatch_group = QGroupBox("จำนวนที่ต้องการเบิก")
        dispatch_layout = QFormLayout()
        
        self.dispatch_input = QLineEdit()
        self.dispatch_input.setPlaceholderText(f"เช่น 25")
        self.dispatch_input.setMinimumWidth(200)
        self.dispatch_input.textChanged.connect(self.update_remaining)
        dispatch_layout.addRow("Width ที่เบิก:", self.dispatch_input)
        
        self.remaining_width_label = QLabel("")
        self.remaining_width_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        dispatch_layout.addRow("Width คงเหลือ:", self.remaining_width_label)

        self.dispatch_length_input = QLineEdit()
        self.dispatch_length_input.setPlaceholderText("เช่น 120 (cm)")
        self.dispatch_length_input.textChanged.connect(self.update_remaining)
        dispatch_layout.addRow("Length ที่เบิก (cm):", self.dispatch_length_input)

        self.remaining_length_label = QLabel("")
        self.remaining_length_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        dispatch_layout.addRow("Length คงเหลือ (cm):", self.remaining_length_label)
        
        dispatch_group.setLayout(dispatch_layout)
        layout.addWidget(dispatch_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Initial update
        self.update_remaining()
    
    def update_remaining(self):
        """คำนวน Width/Length คงเหลือ"""
        self._update_width_remaining()
        self._update_length_remaining()

    def _update_width_remaining(self):
        try:
            dispatch_text = self.dispatch_input.text().strip()
            if not dispatch_text:
                self.remaining_width_label.setText("")
                self.remaining_width_label.setStyleSheet("font-weight: bold; font-size: 14px;")
                return
            
            current_width_str = (self.width or "").replace('m', '').replace('M', '').strip()
            current_width = float(current_width_str) if current_width_str else 0
            dispatch_width = float(dispatch_text)
            remaining_width = current_width - dispatch_width
            
            if remaining_width < 0:
                self.remaining_width_label.setText(f"{remaining_width:.2f}m (ติดลบ!)")
                self.remaining_width_label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
            else:
                self.remaining_width_label.setText(f"{remaining_width:.2f}m")
                self.remaining_width_label.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")
        except ValueError:
            self.remaining_width_label.setText("ข้อมูลไม่ถูกต้อง")
            self.remaining_width_label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")

    def _update_length_remaining(self):
        try:
            dispatch_text = self.dispatch_length_input.text().strip()
            if not dispatch_text:
                self.remaining_length_label.setText("")
                self.remaining_length_label.setStyleSheet("font-weight: bold; font-size: 14px;")
                return
            dispatch_length = float(dispatch_text)
            remaining_length = self.available_length - dispatch_length
            if remaining_length < 0:
                self.remaining_length_label.setText(f"{remaining_length:.2f} cm (ติดลบ!)")
                self.remaining_length_label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
            else:
                self.remaining_length_label.setText(f"{remaining_length:.2f} cm")
                self.remaining_length_label.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")
        except ValueError:
            self.remaining_length_label.setText("ข้อมูลไม่ถูกต้อง")
            self.remaining_length_label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
    
    def get_dispatch_width(self):
        """ดึงค่า Width ที่เบิก"""
        return self.dispatch_input.text().strip()

    def get_dispatch_length(self):
        """ดึงค่า Length ที่เบิก"""
        return self.dispatch_length_input.text().strip()


class DispatchTab(QWidget):
    """Tab สำหรับการเบิกออก (Dispatch) ของม้วนผ้า"""
    
    dispatch_completed = pyqtSignal(dict)
    
    def __init__(self, storage):
        super().__init__()
        self.storage = storage
        self.mobile_server = None
        self.init_mobile_server()
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

        self.connect_mobile_btn = QPushButton("Connect Mobile Device")
        self.connect_mobile_btn.clicked.connect(self.show_mobile_connection_qr)
        scan_layout.addWidget(self.connect_mobile_btn)
        
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
            "เวลา", "เลขม้วน", "SKU", "Width ที่เบิก", "Length ที่เบิก", "สถานะ"
        ])
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        history_layout.addWidget(self.history_table)
        history_group.setLayout(history_layout)
        layout.addWidget(history_group)
        
        # Load recent history
        self.load_recent_history()
    
    def init_mobile_server(self):
        if self.mobile_server:
            try:
                self.mobile_server.stop()
            except Exception:
                pass
        self.mobile_server = MobileConnectionServer()
        self.mobile_server.client_opened.connect(self.on_mobile_scan)
        self.mobile_server.scan_received.connect(self.on_mobile_scan_received)
        self.mobile_server.start()

    def show_mobile_connection_qr(self):
        try:
            if not self.mobile_server:
                QMessageBox.warning(self, "Error", "Mobile server is not available")
                return
            qr_url = self.mobile_server.url
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_url)
            qr.make(fit=True)

            qr_img = qr.make_image(fill_color="black", back_color="white")

            dialog = QDialog(self)
            self.mobile_qr_dialog = dialog
            dialog.setWindowTitle("Connect Mobile Device")
            dialog.setMinimumSize(400, 500)

            layout = QVBoxLayout()

            info_text = f"""
            <h3>เชื่อมต่อมือถือ / Connect Mobile Device</h3>
            <p>สแกน QR Code นี้ด้วยกล้องมือถือ</p>
            <p>Scan this QR code with mobile camera:</p>
            <p><b>URL:</b> {qr_url}</p>
            <p><b>IP Address:</b> {self.mobile_server.local_ip}</p>
            <p><b>Port:</b> {self.mobile_server.port}</p>
            <p style=\"color: green;\"><b>✓ ระบบพร้อม</b></p>
            """

            info_label = QLabel(info_text)
            info_label.setTextFormat(Qt.TextFormat.RichText)
            info_label.setWordWrap(True)
            layout.addWidget(info_label)

            buffer = BytesIO()
            qr_img.save(buffer, format="PNG")
            pixmap = QPixmap()
            pixmap.loadFromData(buffer.getvalue())

            qr_label = QLabel()
            qr_label.setPixmap(pixmap)
            qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(qr_label)

            btn_layout = QHBoxLayout()
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            btn_layout.addStretch()
            btn_layout.addWidget(close_btn)
            layout.addLayout(btn_layout)

            dialog.setLayout(layout)
            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error showing QR code: {str(e)}")

    def on_mobile_scan(self):
        print("client opening")
        self.mobile_qr_dialog.accept()
        
    def on_mobile_scan_received(self, scan_data):
        try:
            print(f"recieve : {scan_data}")
    

            self.dispatch(scan_data)
        except Exception as e:
            print(f"Error handling mobile scan: {e}")
    
    def dispatch(self,code):
        # ตรวจสอบว่ามีม้วนนี้ในระบบหรือไม่
        # ลองค้นหาจาก Roll ID ก่อน (เช่น R001)
        roll = self.storage.get_roll_by_id(code)
        
        # ถ้าไม่เจอ ลองค้นหาจาก Code (เช่น RM2061506007)
        if not roll:
            roll = self.storage.get_roll_by_code(code)
        
        if not roll:
            self.status_label.setText(f"❌ ไม่พบม้วนเลข {code} ในระบบ")
            self.status_label.setStyleSheet("padding: 10px; background-color: #ffebee; border-radius: 5px; color: red;")
            QMessageBox.warning(
                self,
                "ไม่พบข้อมูล",
                f"ไม่พบม้วนเลข {code} ในระบบ\n\nกรุณาตรวจสอบเลขม้วนหรือรับเข้าก่อน"
            )
            return
        
        # ตรวจสอบสถานะม้วน
        if roll.status != 'active':
            self.status_label.setText(f"❌ ม้วนเลข {roll.roll_id} ถูกใช้งานหมดแล้ว")
            self.status_label.setStyleSheet("padding: 10px; background-color: #ffebee; border-radius: 5px; color: red;")
            QMessageBox.warning(
                self,
                "ไม่สามารถเบิกได้",
                f"ม้วนเลข {roll.roll_id} ถูกใช้งานหมดแล้ว (สถานะ: {roll.status})"
            )
            return
        
        # แสดงข้อมูลม้วน
        self.status_label.setText(
            f"✓ พบม้วน: {roll.roll_id}\n"
            f"SKU: {roll.sku} | Lot: {roll.lot}\n"
            f"ความยาวคงเหลือ: {roll.current_length:.2f} cm"
        )
        self.status_label.setStyleSheet("padding: 10px; background-color: #e8f5e9; border-radius: 5px; color: green;")
        
        # เปิด Dialog สำหรับกรอกจำนวนที่เบิก
        dialog = DispatchQuantityDialog(roll.roll_id, roll.current_length, roll.width, self)
        
        if dialog.exec() == QDialog.Accepted:
            dispatch_width = dialog.get_dispatch_width()
            dispatch_length = dialog.get_dispatch_length()
            self.dispatch_roll(roll, dispatch_width, dispatch_length)
    
    def process_scan(self):
        """ประมวลผลการสแกน"""
        scan_input = self.roll_id_input.text().strip()
        
        if not scan_input:
            QMessageBox.warning(self, "ข้อผิดพลาด", "กรุณากรอกเลขม้วนหรือสแกน QR Code")
            return
        
        self.dispatch(scan_input)
        
        
    
    def dispatch_roll(self, roll, dispatch_width, dispatch_length):
        """เบิกออกม้วนผ้า"""
        try:
            # คำนวน width คงเหลือ
            current_width_str = roll.width.replace('m', '').replace('M', '').strip()
            current_width = float(current_width_str) if current_width_str else 0
            dispatch_value = float(dispatch_width)
            remaining_width = current_width - dispatch_value
            
            # สร้าง width string สำหรับบันทึก
            remaining_width_str = f"{remaining_width:.2f}m" if remaining_width > 0 else "0m"
            # คำนวน length คงเหลือ (cm)
            dispatch_length_value = None
            remaining_length_value = roll.current_length
            dispatch_length_str = dispatch_length.strip()
            if dispatch_length_str:
                dispatch_length_value = float(dispatch_length_str)
                remaining_length_value = roll.current_length - dispatch_length_value
                if remaining_length_value < 0:
                    remaining_length_value = 0
            remaining_length_str = f"{remaining_length_value:.2f} cm"
            status = 'active'
            if remaining_width <= 0 or remaining_length_value <= 0:
                status = 'used'
            
            # บันทึกการเปลี่ยนแปลง
            update_fields = {
                'width': remaining_width_str,
                'status': status
            }
            if dispatch_length_value is not None:
                update_fields['current_length'] = remaining_length_value
            self.storage.update_roll(roll.roll_id, **update_fields)
            
            # บันทึก log
            self.storage.add_log(
                action="dispatch",
                roll_id=roll.roll_id,
                details={
                    'sku': roll.sku,
                    'lot': roll.lot,
                    'dispatch_width': dispatch_width,
                    'dispatch_length': dispatch_length_str,
                    'remaining_width': remaining_width_str,
                    'remaining_length': remaining_length_str,
                    'status': status
                }
            )
            
            # แสดงผลลัพธ์
            result_msg = (
                f"✓ เบิกออกสำเร็จ!\n"
                f"เลขม้วน: {roll.roll_id}\n"
                f"Width ที่เบิก: {dispatch_width}\n"
                f"Width คงเหลือ: {remaining_width_str}"
            )
            if dispatch_length_str:
                result_msg += ("\n"
                                f"Length ที่เบิก: {dispatch_length_str} cm\n"
                                f"Length คงเหลือ: {remaining_length_str}")
            
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
                'dispatch_width': dispatch_width,
                'status': 'active'
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

                # Width ที่เบิก
                dispatch_width = details.get('dispatch_width', '')
                width_item = QTableWidgetItem(dispatch_width)
                self.history_table.setItem(row, 3, width_item)

                # Length ที่เบิก
                dispatch_length = details.get('dispatch_length', '')
                length_item = QTableWidgetItem(dispatch_length)
                self.history_table.setItem(row, 4, length_item)

                # สถานะ - อ้างอิง width/length ที่เหลือ
                remaining_width_str = details.get('remaining_width', '0m')
                remaining_width_value = float(remaining_width_str.replace('m', '').replace('M', '').strip() or 0)
                remaining_length_str = details.get('remaining_length', '0 cm')
                remaining_length_value = float(remaining_length_str.replace('cm', '').strip() or 0)

                if remaining_width_value <= 0 or remaining_length_value <= 0:
                    status_text = "ใช้หมด"
                    status_color = Qt.red
                else:
                    status_text = "ยังใช้ได้"
                    status_color = Qt.green

                status_item = QTableWidgetItem(status_text)
                status_item.setForeground(status_color)
                self.history_table.setItem(row, 5, status_item)
        
            # ปรับขนาดคอลัมน์
            self.history_table.resizeColumnsToContents()
        
        except Exception as e:
            print(f"Error loading dispatch history: {e}")
