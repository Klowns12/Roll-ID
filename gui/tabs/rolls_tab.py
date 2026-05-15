import os
import sys
import getpass
import subprocess
from io import BytesIO
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QMessageBox, QLabel, QLineEdit, QDialog, 
    QDialogButtonBox, QFormLayout, QComboBox, QGroupBox, QDoubleSpinBox,
    QFileDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPixmap, QImage

# Import Controller
from controllers.rolls_controller import RollsController
from utils.label_generator import LabelGenerator

class RollsTab(QWidget):
    """Class สำหรับจัดการหน้าตา (GUI) ของหน้า Rolls"""
    dispatch_requested = Signal(str) # ส่ง Roll ID ไปยัง MainWindow
    def __init__(self, storage, current_user=None):
        super().__init__()
        self.storage = storage
        self.current_user = current_user
        self.label_generator = LabelGenerator()
        self.controller = RollsController(self, storage)
        self.setup_ui()
        self.controller.load_initial_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Filter Section
        filter_group = QGroupBox("ตัวกรอง / Filters")
        filter_layout = QHBoxLayout()
        
        self.code_filter = QComboBox()
        self.code_filter.setEditable(True)
        self.code_filter.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.code_filter.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        self.code_filter.currentTextChanged.connect(self.apply_ui_filters)
        
        self.location_filter = QComboBox()
        self.location_filter.setEditable(True)
        self.location_filter.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.location_filter.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        self.location_filter.currentTextChanged.connect(self.apply_ui_filters)
        
        self.status_filter = QComboBox()
        self.status_filter.setEditable(True)
        self.status_filter.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.status_filter.completer().setFilterMode(Qt.MatchFlag.MatchContains)
        self.status_filter.currentTextChanged.connect(self.apply_ui_filters)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ค้นหา Roll ID, Code, หรือ Lot...")
        self.search_input.textChanged.connect(self.apply_ui_filters)
        
        filter_layout.addWidget(QLabel("รหัสสินค้า:"))
        filter_layout.addWidget(self.code_filter, 1)
        filter_layout.addWidget(QLabel("ตำแหน่ง:"))
        filter_layout.addWidget(self.location_filter, 1)
        filter_layout.addWidget(QLabel("สถานะ:"))
        filter_layout.addWidget(self.status_filter, 1)
        filter_layout.addWidget(QLabel("ค้นหา:"))
        filter_layout.addWidget(self.search_input, 2)
        filter_group.setLayout(filter_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh")
        self.edit_btn = QPushButton("Edit Roll")  # เพิ่มปุ่ม Edit
        self.print_btn = QPushButton("Print Label")
        self.export_btn = QPushButton("Export")
        
        self.refresh_btn.clicked.connect(self.controller.refresh_data)
        self.edit_btn.clicked.connect(self.handle_edit_roll) # เชื่อมต่อ Edit
        self.print_btn.clicked.connect(lambda: self.controller.handle_print_label())
        self.export_btn.clicked.connect(self.controller.handle_export)
        
        self.dispatch_btn = QPushButton("🚀 Dispatch (เบิก)")
        self.dispatch_btn.clicked.connect(self.handle_dispatch)
        self.dispatch_btn.setStyleSheet("background-color: #e8f5e9; font-weight: bold;")
        
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.print_btn)
        btn_layout.addWidget(self.dispatch_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.export_btn)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "Roll ID", "Date Created", "Code", "SubPartCode", "SupCode", 
            "Supplier Name", "Description", "Lot", "Location", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Status label for counts
        self.count_label = QLabel("Total: 0 rolls")
        self.count_label.setStyleSheet("font-weight: bold; color: #555; margin-top: 5px;")
        
        self.table.setSortingEnabled(True)
        
        # Table title
        self.table_title = QLabel("📦 รายการม้วนผ้าในคลังสินค้า (Current Stock List)")
        self.table_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; margin-top: 10px;")
        
        layout.addWidget(filter_group)
        layout.addLayout(btn_layout)
        layout.addWidget(self.table_title)
        layout.addWidget(self.table)
        layout.addWidget(self.count_label)

    # --- External Interface (Methods called by other tabs) ---
    def add_new_roll(self, roll_data):
        """Proxy สำหรับเพิ่มม้วนผ้าใหม่จากแท็บอื่น"""
        return self.controller.add_new_roll(roll_data)

    def print_roll_label(self, roll):
        """สร้างฉลากและแสดง Preview ก่อนสั่งพิมพ์"""
        try:
            # 1. ดึงชื่อผู้ใช้งานระบบ (จาก Login หรือ System)
            if self.current_user:
                printed_by = self.current_user.username
            else:
                printed_by = getpass.getuser()
            
            # 2. สร้างรูปฉลากจากข้อมูลม้วน
            img = self.label_generator.create_label(roll, user=printed_by)
            
            # 3. แสดง Preview Dialog
            preview_dialog = LabelPreviewDialog(img, parent=self)
            if preview_dialog.exec() == QDialog.DialogCode.Accepted:
                # 3. ถ้ากดยืนยัน (Confirm Print) ให้ทำการพิมพ์
                # บันทึกเป็นไฟล์ชั่วคราว
                temp_path = os.path.join(os.getcwd(), "temp_label.png")
                img.save(temp_path)
                
                # สั่งพิมพ์ผ่าน Windows Shell
                if sys.platform == "win32":
                    os.startfile(temp_path, "print")
                else:
                    subprocess.run(["lp", temp_path])
                return True
            return False # User ยกเลิกการพิมพ์
        except Exception as e:
            QMessageBox.critical(self, "Error", f"ไม่สามารถแสดงผลฉลากได้: {str(e)}")
            return False

    def handle_dispatch(self):
        """ส่ง Roll ID ที่เลือกไปยังหน้า Dispatch"""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Warning", "กรุณาเลือกม้วนผ้าที่ต้องการเบิกจากตารางก่อนครับ")
            return
            
        # คอลัมน์ที่ 0 คือ Roll ID
        roll_id = self.table.item(selected_row, 0).text()
        self.dispatch_requested.emit(roll_id)

    # --- UI Helpers ---
    def update_table(self, rolls):
        self.table.setSortingEnabled(False) # ปิดชั่วคราวขณะโหลด
        self.table.setRowCount(0)
        for roll in rolls:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # ดึงค่าสีพื้นหลังตามสถานะ
            bg_color = None
            status_lower = str(roll.status).lower()
            if status_lower == "active":
                bg_color = QColor("#c8e6c9") # เขียวอ่อน
            elif status_lower == "used":
                bg_color = QColor("#ffcdd2") # แดงอ่อน
                
            items = []
            
            # 0. Roll ID
            items.append(QTableWidgetItem(str(roll.roll_id)))
            # 1. Date Created
            items.append(QTableWidgetItem(str(roll.date_received)))
            # 2. Code
            items.append(QTableWidgetItem(str(roll.code)))
            # 3. SubPartCode
            items.append(QTableWidgetItem(str(getattr(roll, 'sub_part_code', ""))))
            # 4. SupCode
            items.append(QTableWidgetItem(str(getattr(roll, 'sup_code', ""))))
            # 5. Supplier Name
            items.append(QTableWidgetItem(str(getattr(roll, 'supplier_name', ""))))
            # 6. Description
            items.append(QTableWidgetItem(str(getattr(roll, 'description', ""))))
            # 7. Lot
            items.append(QTableWidgetItem(str(roll.lot_no)))
            # 8. Location
            items.append(QTableWidgetItem(str(roll.location)))
            # 9. Status
            items.append(QTableWidgetItem(str(roll.status)))
            
            # ตั้งค่าสีพื้นหลังและเพิ่มลงตาราง
            for col, item in enumerate(items):
                if bg_color:
                    item.setBackground(QBrush(bg_color))
                self.table.setItem(row, col, item)
        
        self.table.setSortingEnabled(True) # เปิดใช้งาน Sort
        self.table.resizeColumnsToContents() # ปรับขนาดคอลัมน์ให้พอดีกับข้อมูลอัตโนมัติเพื่อให้เลื่อน Scroll X ได้เมื่อเนื้อหาเกิน
        self.count_label.setText(f"Total: {len(rolls)} rolls")

    def update_filter_options(self, rolls):
        # 1. Update Code Filter
        self.code_filter.blockSignals(True)
        current_code = self.code_filter.currentText()
        self.code_filter.clear()
        self.code_filter.addItem("ทั้งหมด")
        codes = sorted(list(set(r.code for r in rolls if r.code)))
        self.code_filter.addItems(codes)
        idx = self.code_filter.findText(current_code)
        if idx >= 0:
            self.code_filter.setCurrentIndex(idx)
        self.code_filter.blockSignals(False)

        # 2. Update Location Filter
        self.location_filter.blockSignals(True)
        current_loc = self.location_filter.currentText()
        self.location_filter.clear()
        self.location_filter.addItem("ทั้งหมด")
        locations = sorted(list(set(r.location for r in rolls if r.location)))
        self.location_filter.addItems(locations)
        idx = self.location_filter.findText(current_loc)
        if idx >= 0:
            self.location_filter.setCurrentIndex(idx)
        self.location_filter.blockSignals(False)

        # 3. Update Status Filter
        self.status_filter.blockSignals(True)
        current_status = self.status_filter.currentText()
        self.status_filter.clear()
        self.status_filter.addItem("ทั้งหมด")
        statuses = sorted(list(set(r.status for r in rolls if r.status)))
        self.status_filter.addItems(statuses)
        idx = self.status_filter.findText(current_status)
        if idx >= 0:
            self.status_filter.setCurrentIndex(idx)
        self.status_filter.blockSignals(False)

    def get_selected_roll_id(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "คำเตือน", "กรุณาเลือกม้วนผ้าในตาราง")
            return None
        return self.table.item(selected[0].row(), 0).text()

    def apply_ui_filters(self):
        search_text = self.search_input.text().lower()
        code_text = self.code_filter.currentText()
        location_text = self.location_filter.currentText()
        status_text = self.status_filter.currentText()
        
        for row in range(self.table.rowCount()):
            roll_id = self.table.item(row, 0).text().lower()
            code = self.table.item(row, 2).text()
            lot = self.table.item(row, 7).text().lower()
            location = self.table.item(row, 8).text()
            status = self.table.item(row, 9).text()
            
            show = (code_text == "ทั้งหมด" or not code_text or code_text.lower() in code.lower()) and \
                   (location_text == "ทั้งหมด" or not location_text or location_text.lower() in location.lower()) and \
                   (status_text == "ทั้งหมด" or not status_text or status_text.lower() in status.lower()) and \
                   (not search_text or search_text in roll_id or search_text in lot)
                   
            self.table.setRowHidden(row, not show)
            
        # Update count label for filtered results
        visible_rows = sum(1 for row in range(self.table.rowCount()) if not self.table.isRowHidden(row))
        total_rows = self.table.rowCount()
        
        if search_text or code_text != "ทั้งหมด" or location_text != "ทั้งหมด" or status_text != "ทั้งหมด":
            self.count_label.setText(f"Showing: {visible_rows} of {total_rows} rolls")
        else:
            self.count_label.setText(f"Total: {total_rows} rolls")

    def handle_edit_roll(self):
        """จัดการการแก้ไขข้อมูลม้วนผ้า"""
        roll_id = self.get_selected_roll_id()
        if not roll_id: return

        roll = self.storage.get_roll(roll_id)
        if not roll: return

        dialog = EditRollDialog(roll, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_data()
            
            # ดึงชื่อผู้ใช้งาน
            username = "system"
            if self.current_user:
                username = self.current_user.full_name
                
            if self.storage.update_roll(roll_id, **new_data):
                self.storage.add_log("edit", roll_id, {"old": roll.__dict__, "new": new_data}, user=username)
                QMessageBox.information(self, "สำเร็จ", f"แก้ไขม้วน {roll_id} เรียบร้อย")
                self.controller.refresh_data()
            else:
                QMessageBox.critical(self, "ผิดพลาด", "ไม่สามารถบันทึกข้อมูลได้")

class CutRollDialog(QDialog):
    def __init__(self, roll, parent=None):
        super().__init__(parent)
        self.roll = roll
        self.setWindowTitle(f"Cut Roll: {roll.roll_id}")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.cut_input = QDoubleSpinBox()
        self.cut_input.setRange(0.01, roll.length)
        self.cut_input.setValue(roll.length / 2)
        form.addRow("ความยาวที่จะตัดออก:", self.cut_input)
        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_cut_length(self):
        return self.cut_input.value()

class LabelPreviewDialog(QDialog):
    """หน้าต่างสำหรับดูตัวอย่างฉลากก่อนพิมพ์"""
    def __init__(self, pil_image, parent=None):
        super().__init__(parent)
        self.pil_image = pil_image # เก็บไว้สำหรับเซฟ
        self.setWindowTitle("Label Preview (ตัวอย่างก่อนพิมพ์)")
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        # แปลง PIL Image เป็น QPixmap
        # บันทึกลง Buffer ก่อนเพื่อความชัวร์ในการแปลง
        buffer = BytesIO()
        pil_image.save(buffer, format="PNG")
        qimage = QImage.fromData(buffer.getvalue())
        pixmap = QPixmap.fromImage(qimage)
        
        # แสดงรูปภาพใน Label
        self.preview_label = QLabel()
        # ปรับขนาดให้พอดีหน้าจอ preview (แต่คงสัดส่วนเดิม)
        scaled_pixmap = pixmap.scaled(700, 350, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.preview_label.setPixmap(scaled_pixmap)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("border: 1px solid #ccc; background: white; padding: 10px;")
        
        layout.addWidget(QLabel("กรุณาตรวจสอบความถูกต้องของข้อมูลก่อนยืนยันการพิมพ์:"))
        layout.addWidget(self.preview_label)
        
        # ปุ่มยืนยัน/เซฟ/ยกเลิก
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save Image (เซฟรูป)")
        self.save_btn.clicked.connect(self.handle_save_image)
        
        self.print_btn = QPushButton("Confirm Print (พิมพ์ฉลาก)")
        self.print_btn.clicked.connect(self.accept)
        self.print_btn.setStyleSheet("background-color: #e3f2fd; font-weight: bold;")
        
        self.cancel_btn = QPushButton("Cancel (ยกเลิก)")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.print_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)

    def handle_save_image(self):
        """บันทึกรูปฉลากลงเครื่อง"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Label Image",
            "label_preview.png",
            "PNG Files (*.png);;All Files (*)"
        )
        
        if file_path:
            try:
                self.pil_image.save(file_path)
                QMessageBox.information(self, "Success", f"บันทึกรูปภาพเรียบร้อยแล้วที่:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"ไม่สามารถบันทึกรูปภาพได้: {str(e)}")

class EditRollDialog(QDialog):
    """Dialog สำหรับแก้ไขข้อมูลม้วนผ้า (GUI Only)"""
    def __init__(self, roll, parent=None):
        super().__init__(parent)
        self.roll = roll
        self.setWindowTitle(f"Edit Roll: {roll.roll_id}")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        # 1. Roll ID (Locked)
        self.roll_id_input = QLineEdit(roll.roll_id)
        self.roll_id_input.setReadOnly(True)
        self.roll_id_input.setStyleSheet("background-color: #f0f0f0;")
        
        # 2. Date Created (Locked)
        self.date_input = QLineEdit(getattr(roll, 'date_received', ""))
        self.date_input.setReadOnly(True)
        self.date_input.setStyleSheet("background-color: #f0f0f0;")
        
        # 3. Product Info
        self.code_input = QLineEdit(roll.code)
        self.sub_part_input = QLineEdit(getattr(roll, 'sub_part_code', ""))
        self.sup_code_input = QLineEdit(getattr(roll, 'sup_code', ""))
        self.supplier_input = QLineEdit(getattr(roll, 'supplier_name', ""))
        self.desc_input = QLineEdit(getattr(roll, 'description', ""))
        self.lot_input = QLineEdit(roll.lot_no)
        self.location_input = QLineEdit(roll.location)
        
        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Active", "Used"])
        self.status_combo.setCurrentText(roll.status)

        # เพิ่มฟิลด์อื่นๆ ไว้ท้าย (Width, Length, Color, Unit)
        self.colour_input = QLineEdit(getattr(roll, 'color', ""))
        self.width_input = QDoubleSpinBox()
        self.width_input.setRange(0, 9999.99)
        self.width_input.setDecimals(2)
        self.width_input.setSuffix(" m")
        try:
            self.width_input.setValue(float(getattr(roll, 'width', 0.0)))
        except:
            self.width_input.setValue(0.0)
            
        self.length_input = QDoubleSpinBox()
        self.length_input.setRange(0, 99999.99)
        self.length_input.setValue(roll.length)
        self.length_input.setSuffix(" m")
        self.unit_input = QLineEdit(roll.unit)
        
        # เรียงตามลำดับที่ต้องการ
        form.addRow("Roll ID (ล็อค):", self.roll_id_input)
        form.addRow("Date Created (วันที่รับเข้า):", self.date_input)
        form.addRow("Code (รหัสสินค้า):", self.code_input)
        form.addRow("SubPartCode (รหัสย่อย):", self.sub_part_input)
        form.addRow("SupCode (รหัสผู้ผลิต):", self.sup_code_input)
        form.addRow("Supplier Name (ชื่อผู้ผลิต):", self.supplier_input)
        form.addRow("Description (รายละเอียด):", self.desc_input)
        form.addRow("Lot No. (เลขล็อต):", self.lot_input)
        form.addRow("Location (ที่เก็บ):", self.location_input)
        form.addRow("Status (สถานะ):", self.status_combo)
        
        # เพิ่มที่เหลือ
        form.addRow("Colour (สี):", self.colour_input)
        form.addRow("Width (หน้ากว้าง):", self.width_input)
        form.addRow("Length (ความยาว):", self.length_input)
        form.addRow("Unit (หน่วย):", self.unit_input)
        
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        
        layout.addLayout(form)
        layout.addWidget(btns)

    def get_data(self):
        return {
            "code": self.code_input.text(),
            "sub_part_code": self.sub_part_input.text(),
            "sup_code": self.sup_code_input.text(),
            "supplier_name": self.supplier_input.text(),
            "description": self.desc_input.text(),
            "lot_no": self.lot_input.text(),
            "location": self.location_input.text(),
            "status": self.status_combo.currentText(),
            "color": self.colour_input.text(),
            "width": self.width_input.value(),
            "length": self.length_input.value(),
            "unit": self.unit_input.text()
        }
