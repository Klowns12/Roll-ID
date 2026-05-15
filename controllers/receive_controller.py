import logging
import random
from datetime import datetime
from PySide6.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)

class ReceiveController:
    """Class สำหรับจัดการ Logic การทำงานของหน้ารับสินค้า (Receive)"""
    def __init__(self, view, storage, roll_id_generator):
        self.view = view
        self.storage = storage
        self.roll_id_generator = roll_id_generator

    def get_sku_list(self):
        """ดึงรายการ SKU ทั้งหมดจาก Master Data เพื่อทำ AutoComplete"""
        try:
            data = self.storage.get_master_autocomplete_data()
            return data.get('skus', [])
        except Exception as e:
            logger.error(f"Error getting SKU list: {e}")
            return []

    def handle_sku_change(self, text):
        """Auto-fill เมื่อมีการกรอก SKU หรือล้างข้อมูลเมื่อไม่พบ"""
        sku = text.strip().upper()
        
        if not sku:
            self.view.clear_product_fields()
            return
            
        product = self.storage.get_master_product(sku)
        if product:
            self.view.fill_form_from_master({
                'sub_part': product.get('spl_part_code', ""),
                'sup_code': product.get('spl_code', ""),
                'supplier': product.get('spl_name', ""),
                'desc': product.get('pdt_name', ""),
                'unit': product.get('unit_type', "MTS")
            })
        else:
            self.view.clear_product_fields()

    def handle_random_fill(self):
        """สุ่มข้อมูลสำหรับทดสอบระบบ (แบบฉลาด: ไม่ทับข้อมูลสินค้าถ้ามีการกรอกไว้แล้ว)"""
        colours = ["Red", "Navy Blue", "Deep Black", "Charcoal Gray", "Pure White"]
        locations = [f"WH-{r}-{random.randint(1,10)}" for r in ['A', 'B', 'C']]
        
        # ดึงข้อมูลปัจจุบันจากหน้าจอ
        current_data = self.view.get_form_data()
        has_code = bool(current_data.get('code'))

        # ข้อมูลที่จะสุ่ม (เฉพาะส่วนของม้วนผ้า)
        roll_random_data = {
            'lot': f"LOT{datetime.now().strftime('%Y%m%d')}-{random.randint(1, 99)}",
            'color': random.choice(colours),
            'width': f"{random.choice([1.4, 1.5, 1.8, 2.0]):.2f}",
            'location': random.choice(locations),
            'length': f"{random.uniform(50.0, 150.0):.2f}",
            'qty': 1 # เปลี่ยนจากสุ่มเป็น 1
        }

        if has_code:
            # ถ้ามี Code แล้ว ให้สุ่มเฉพาะข้อมูลม้วน โดยเรียกฟังก์ชันใหม่ใน View
            self.view.fill_roll_fields_only(roll_random_data)
        else:
            # ถ้าไม่มี Code ให้สุ่มใหม่ทั้งหมดเหมือนเดิม
            suppliers = ["Aurelic Textiles", "Global Fabrics Co.", "Premium Yarn Ltd"]
            full_random_data = {
                'code': f"RM{random.randint(100000, 999999)}",
                'sub_part': f"SUB-{random.randint(100, 999)}",
                'sup_code': f"SUP-{random.randint(10, 99)}",
                'supplier': random.choice(suppliers),
                'desc': "Random Generated Product",
                'unit': "MTS",
                **roll_random_data
            }
            self.view.fill_entire_form(full_random_data)

    def handle_submit(self):
        """ตรวจสอบความถูกต้องและสั่งบันทึก"""
        data = self.view.get_form_data()
        
        # 1. ตรวจสอบฟิลด์ที่จำเป็น (Required Fields)
        if not data['code'].strip():
            QMessageBox.warning(self.view, "ข้อมูลไม่ครบ", "กรุณาระบุรหัสสินค้า (Code)")
            return
        
        if not data['lot_no'].strip():
            QMessageBox.warning(self.view, "ข้อมูลไม่ครบ", "กรุณาระบุเลข Lot No.")
            return

        # 2. ตรวจสอบรหัสสินค้าใน Master Data
        product = self.storage.get_master_product(data['code'].strip().upper())
        if not product:
            reply = QMessageBox.question(
                self.view, "ไม่พบรหัสสินค้า", 
                f"ไม่พบรหัส '{data['code']}' ใน Master Data\nคุณต้องการบันทึกต่อไปโดยไม่ใช้ข้อมูล Master หรือไม่?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        # 3. ตรวจสอบความถูกต้องของตัวเลข
        try:
            length = float(data['length'])
            if length <= 0:
                QMessageBox.warning(self.view, "ข้อมูลไม่ถูกต้อง", "ความยาว (Length) ต้องมากกว่า 0")
                return
        except ValueError:
            QMessageBox.warning(self.view, "ข้อมูลไม่ถูกต้อง", "ความยาวต้องเป็นตัวเลขเท่านั้น")
            return

        if data['quantity'] < 1:
            QMessageBox.warning(self.view, "ข้อมูลไม่ถูกต้อง", "จำนวนม้วน (Quantity) ต้องอย่างน้อย 1 ม้วน")
            return

        # 4. ดำเนินการบันทึก (สร้างม้วนตามจำนวนที่ระบุ)
        success_count = 0
        main_win = self.view.window()
        
        for _ in range(data['quantity']):
            roll_id = self.roll_id_generator.get_next_roll_id()
            roll_data = {
                **data, 
                'roll_id': roll_id,
                'length_original': data.get('length', 0)
            }
            
            # สั่งบันทึกผ่านหน้า Rolls (เพื่อความสอดคล้องของระบบ)
            if hasattr(main_win, 'rolls_tab'):
                if main_win.rolls_tab.add_new_roll(roll_data):
                    success_count += 1
        
        if success_count > 0:
            QMessageBox.information(self.view, "สำเร็จ", f"บันทึกม้วนผ้าสำเร็จ {success_count} ม้วน")
            self.view.clear_form()
            # ส่งสัญญาณรีเฟรชหน้าอื่นๆ
            if hasattr(main_win, 'statistics_tab'):
                main_win.statistics_tab.controller.refresh_data()
            
            # เปลี่ยนไปหน้า Rolls ทันทีหลังบันทึกสำเร็จ
            self.view.switch_to_rolls_tab()
        else:
            QMessageBox.critical(self.view, "ผิดพลาด", "ไม่สามารถบันทึกข้อมูลได้")
