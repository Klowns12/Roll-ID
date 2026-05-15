import csv
from datetime import datetime
from PySide6.QtWidgets import QMessageBox, QFileDialog, QDialog
from core.storage import Roll

class RollsController:
    """Class สำหรับจัดการ Logic การทำงานของหน้า Rolls"""
    def __init__(self, view, storage):
        self.view = view
        self.storage = storage
        self.rolls = []

    def load_initial_data(self):
        self.refresh_data()

    def refresh_data(self):
        """โหลดข้อมูลและอัปเดตตาราง (แสดงเฉพาะม้วนที่มีอยู่จริง)"""
        self.rolls = self.storage.search_rolls(status="active")
        self.view.update_table(self.rolls)
        self.view.update_filter_options(self.rolls)

    def add_new_roll(self, roll_data):
        """Logic สำหรับการเพิ่มม้วนผ้าใหม่ (เรียกจากหน้า Receive หรือ Scan)"""
        try:
            roll = Roll(
                roll_id=roll_data['roll_id'],
                code=roll_data['code'],
                sub_part_code=roll_data.get('sub_part_code', ""),
                sup_code=roll_data.get('sup_code', ""),
                supplier_name=roll_data.get('supplier_name', ""),
                description=roll_data.get('description', ""),
                lot_no=roll_data['lot_no'],
                length=float(roll_data['length']),
                length_original=float(roll_data.get('length_original', roll_data['length'])),
                width=roll_data.get('width', ""),  # เพิ่ม width
                color=roll_data.get('color', ""),  # เพิ่ม color
                location=roll_data.get('location', ""),
                unit=roll_data.get('unit', "MTS"),
                status="active"
            )
            
            # ดึงชื่อผู้ใช้งาน
            username = "system"
            if hasattr(self.view, 'current_user') and self.view.current_user:
                username = self.view.current_user.full_name
            
            if self.storage.add_roll(roll, user=username):
                self.storage.add_log("receive", roll.roll_id, roll_data, user=username)
                self.refresh_data()
                return True
            return False
        except Exception as e:
            QMessageBox.critical(self.view, "Error", f"ไม่สามารถเพิ่มม้วนได้: {str(e)}")
            return False

    def handle_print_label(self, roll_id=None):
        """Logic การพิมพ์ฉลาก"""
        if not roll_id:
            roll_id = self.view.get_selected_roll_id()
        if not roll_id: return
        
        roll = self.storage.get_roll(roll_id)
        if roll:
            self.view.print_roll_label(roll)

    def handle_export(self):
        """จัดการการส่งออกข้อมูล"""
        file_path, _ = QFileDialog.getSaveFileName(
            self.view, "Export Rolls", 
            f"rolls_{datetime.now().strftime('%Y%m%d')}.csv", "CSV Files (*.csv)"
        )
        if not file_path: return

        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['Roll ID', 'Code', 'Lot No.', 'Length', 'Location', 'Status'])
                for roll in self.rolls:
                    writer.writerow([roll.roll_id, roll.code, roll.lot_no, roll.length, roll.location, roll.status])
            QMessageBox.information(self.view, "สำเร็จ", "ส่งออกข้อมูลเรียบร้อยแล้ว")
        except Exception as e:
            QMessageBox.critical(self.view, "ผิดพลาด", f"ไม่สามารถส่งออกข้อมูลได้: {str(e)}")
