import logging
from PySide6.QtWidgets import QMessageBox, QDialog

logger = logging.getLogger(__name__)

class DispatchController:
    """Class สำหรับจัดการ Logic การเบิกออก (Dispatch)"""
    def __init__(self, view, storage):
        self.view = view
        self.storage = storage

    def get_and_validate_roll(self, roll_id_text):
        """ตรวจสอบและประมวลผลข้อมูลที่ได้จากการสแกน"""
        code = roll_id_text.strip()
        if not code:
            QMessageBox.warning(self.view, "ข้อผิดพลาด", "กรุณากรอกเลขม้วนหรือสแกน QR Code")
            return None

        roll = self.storage.get_roll_by_id(code) or self.storage.get_roll_by_code(code)
        
        if not roll:
            self.view.show_status(f"❌ ไม่พบม้วนเลข {code} ในระบบ", "red")
            return None

        if roll.status != "active":
            self.view.show_status(f"❌ ม้วนเลข {roll.roll_id} ถูกใช้งานหมดแล้ว", "red")
            return None

        self.view.show_status(f"✓ พบม้วน: {roll.roll_id} | คงเหลือ: {roll.length:.2f}", "green")
        return roll

    def execute_dispatch(self, roll, dispatch_data):
        """คำนวณและบันทึกลงฐานข้อมูลพร้อมข้อมูลลูกค้า"""
        try:
            dispatch_val = float(dispatch_data.get('length') or 0)
            doc_no = dispatch_data.get('doc_no', "")
            cus_code = dispatch_data.get('cus_code', "")
            cus_name = dispatch_data.get('cus_name', "")
            
            # ตรวจสอบว่าเบิกเกินจำนวนที่มีหรือไม่
            if dispatch_val > roll.length:
                QMessageBox.warning(
                    self.view, 
                    "เกินจำนวนที่มี", 
                    f"ไม่สามารถเบิกได้เนื่องจากจำนวนที่ระบุ ({dispatch_val:.2f}) \n"
                    f"มากกว่าความยาวที่มีอยู่จริง ({roll.length:.2f})"
                )
                return

            remaining = max(0, roll.length - dispatch_val)
            status = "active" if remaining > 0.01 else "used"

            # 1. อัปเดตตารางหลัก
            self.storage.update_roll(roll.roll_id, length=remaining, status=status)
            
            # ดึงชื่อผู้ใช้งานที่ล็อกอิน
            username = "system"
            if hasattr(self.view, 'current_user') and self.view.current_user:
                username = self.view.current_user.full_name
            
            # 2. บันทึกประวัติการเบิกอย่างละเอียด (รวมข้อมูลลูกค้า)
            self.storage.add_dispatch_record(
                roll, dispatch_val, 
                document_no=doc_no, 
                customer_code=cus_code, 
                customer_name=cus_name,
                user=username
            )

            # 3. บันทึก Log กิจกรรม
            self.storage.add_log(
                action="dispatch",
                roll_id=roll.roll_id,
                details={
                    "code": roll.code,
                    "dispatch_length": f"{dispatch_val:.2f}",
                    "remaining_length": f"{remaining:.2f}",
                    "document_no": doc_no,
                    "customer": f"{cus_code} {cus_name}".strip(),
                    "status": status
                },
                user=username
            )

            result_msg = f"✓ เบิกออกสำเร็จ!\nเลขม้วน: {roll.roll_id}\nคงเหลือ: {remaining:.2f}"
            self.view.show_status(result_msg, "blue")
            QMessageBox.information(self.view, "สำเร็จ", result_msg)
            self.view.refresh_ui()

        except Exception as e:
            QMessageBox.critical(self.view, "ผิดพลาด", f"เกิดข้อผิดพลาด: {str(e)}")
