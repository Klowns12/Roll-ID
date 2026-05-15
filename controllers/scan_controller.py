import logging
import pandas as pd
from PySide6.QtWidgets import QMessageBox, QFileDialog

try:
    import serial.tools.list_ports
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False

logger = logging.getLogger(__name__)

class ScanController:
    """Class สำหรับจัดการ Logic การสแกนจากอุปกรณ์และการนำเข้าไฟล์"""
    def __init__(self, view, storage, roll_id_generator, suppliers_manager):
        self.view = view
        self.storage = storage
        self.roll_id_generator = roll_id_generator
        self.suppliers_manager = suppliers_manager
        self.selected_master_item = None

    def check_device_connection(self):
        """ตรวจสอบพอร์ตเครื่องสแกน"""
        if not HAS_SERIAL:
            self.view.update_connection_status(False)
            return False
        try:
            ports = list(serial.tools.list_ports.comports())
            if ports:
                self.view.update_connection_status(True, ports[0].device)
                return True
            else:
                self.view.update_connection_status(False)
                return False
        except Exception as e:
            logger.error(f"Error checking device: {e}")
            return False

    def handle_file_import(self):
        """จัดการการเลือกไฟล์และอ่านข้อมูล"""
        file_path, _ = QFileDialog.getOpenFileName(self.view, "เลือกไฟล์ข้อมูลม้วนผ้า", "", "CSV Files (*.csv);;Excel Files (*.xlsx)")
        if not file_path: return

        try:
            df = pd.read_excel(file_path) if file_path.endswith('.xlsx') else pd.read_csv(file_path)
            df.columns = df.columns.str.lower().str.strip()
            
            required = ["sku", "lot", "length"]
            if not all(col in df.columns for col in required):
                QMessageBox.critical(self.view, "ผิดพลาด", f"ไฟล์ต้องมีคอลัมน์: {', '.join(required)}")
                return

            self.view.display_preview(df)
        except Exception as e:
            QMessageBox.critical(self.view, "ผิดพลาด", f"ไม่สามารถอ่านไฟล์ได้: {str(e)}")

    def submit_imported_data(self, df):
        """บันทึกข้อมูลที่นำเข้าลงฐานข้อมูล SQLite"""
        success = 0
        for _, row in df.iterrows():
            try:
                sku = str(row.get('sku', row.get('code', ''))).upper()
                roll_id = self.roll_id_generator.get_next_roll_id()
                
                # ดึงข้อมูลสินค้าเพื่อเอาชื่อ Supplier
                product = self.storage.get_master_product(sku)
                supplier_name = ""
                if product:
                    supplier_name = product.get('spl_name', product.get('Supplier Name', ""))
                
                data = {
                    "roll_id": roll_id,
                    "code": sku,
                    "supplier_name": supplier_name,
                    "lot_no": str(row.get('lot', row.get('lot_no', ''))).upper(),
                    "length": float(row.get('length', 0)),
                    "length_original": float(row.get('length', 0)),
                    "location": str(row.get('location', '')),
                    "status": "active"
                }
                
                # ดึงชื่อผู้ใช้งาน
                username = "system"
                if hasattr(self.view, 'current_user') and self.view.current_user:
                    username = self.view.current_user.full_name
                    
                # ใช้ storage โดยตรงเพื่อความสะอาด
                if self.storage.add_roll(data, user=username):
                    self.storage.add_log("receive_import", roll_id, data, user=username)
                    success += 1
            except Exception as e:
                logger.error(f"Error importing row: {e}")
                continue
        
        QMessageBox.information(self.view, "สำเร็จ", f"นำเข้าข้อมูลสำเร็จ {success} ม้วน")
        self.view.preview_table.setRowCount(0)
        self.view.refresh_reports.emit()

    def select_master_item(self, item):
        """เมื่อเลือกสินค้าจากตาราง ให้เอาข้อมูลไปใส่ในฟอร์ม"""
        self.selected_master_item = item
        self.view.form_group.setEnabled(True)
        self.view.master_lot.setFocus()
        
        # แสดงข้อมูลเบื้องต้น (ถ้ามี)
        desc = item.get('Description', item.get('description', ''))
        self.view.form_group.setTitle(f"📌 สร้างม้วนผ้าสำหรับ: {item.get('pdt_code', 'Unknown')} ({desc})")

    def submit_master_roll(self):
        """บันทึกม้วนผ้าใหม่จากฟอร์ม Master Lookup"""
        if not self.selected_master_item:
            QMessageBox.warning(self.view, "Warning", "กรุณาเลือกสินค้าจากตารางก่อนครับ")
            return
            
        try:
            lot = self.view.master_lot.text().strip().upper()
            length = float(self.view.master_length.text() or 0)
            location = self.view.master_location.text().strip().upper()
            
            if not lot or length <= 0:
                QMessageBox.warning(self.view, "Warning", "กรุณากรอก Lot และ ความยาวให้ครบถ้วน")
                return
                
            roll_id = self.roll_id_generator.get_next_roll_id()
            
            # ดึงชื่อผู้ใช้งาน
            username = "system"
            if hasattr(self.view, 'current_user') and self.view.current_user:
                username = self.view.current_user.full_name
                
            data = {
                "roll_id": roll_id,
                "code": self.selected_master_item.get('pdt_code', ""),
                "sub_part_code": self.selected_master_item.get('spl_part_code', ""),
                "sup_code": self.selected_master_item.get('spl_code', ""),
                "supplier_name": self.selected_master_item.get('spl_name', ""),
                "description": self.selected_master_item.get('pdt_name', ""),
                "unit": self.selected_master_item.get('unit_type', "MTS"),
                "lot_no": lot,
                "length": length,
                "length_original": length,
                "location": location,
                "status": "active"
            }
            
            if self.storage.add_roll(data, user=username):
                self.storage.add_log("receive_scan", roll_id, data, user=username)
                QMessageBox.information(self.view, "Success", f"บันทึกม้วนผ้า {roll_id} เรียบร้อยแล้ว!")
                # ล้างฟอร์ม (ใช้ฟังก์ชันใน View)
                self.view.clear_master_form()
                self.selected_master_item = None
                self.view.refresh_reports.emit()
            else:
                QMessageBox.critical(self.view, "Error", "ไม่สามารถบันทึกข้อมูลลงฐานข้อมูลได้")
        except Exception as e:
            QMessageBox.critical(self.view, "Error", f"เกิดข้อผิดพลาด: {str(e)}")

    def handle_mobile_scan(self, scan_data: str):
        """จัดการข้อมูลที่สแกนจากมือถือ (ฟอร์แมต: ROLL_ID%SKU%...%LOT%LOCATION)"""
        try:
            logger.info(f"Processing mobile scan: {scan_data}")
            # แบ่งข้อมูลด้วย % เหมือนตัวเก่า
            parts = scan_data.split("%")
            
            if len(parts) < 3:
                logger.warning("Invalid scan format from mobile")
                return

            # ในตัวเก่า: 0=roll_id, 1=sku, 6=lot, 7=location (อ้างอิงจากโค้ด RollOld)
            # แต่เราจะปรับให้ยืดหยุ่นขึ้น
            sku = parts[1] if len(parts) > 1 else "UNKNOWN"
            lot = parts[6] if len(parts) > 6 else (parts[2] if len(parts) > 2 else "UNKNOWN")
            location = parts[7] if len(parts) > 7 else ""
            
            # ตรวจสอบว่ามีม้วนนี้อยู่แล้วหรือยัง
            roll_id = parts[0]
            existing = self.storage.get_roll_by_id(roll_id)
            if existing:
                QMessageBox.warning(self.view, "Duplicate", f"ม้วนเลขที่ {roll_id} มีอยู่ในระบบแล้ว")
                return

            # ดึงชื่อผู้ใช้งาน
            username = "system"
            if hasattr(self.view, 'current_user') and self.view.current_user:
                username = self.view.current_user.full_name

            data = {
                "roll_id": roll_id,
                "code": sku.upper(),
                "lot_no": lot.upper(),
                "length": 0.0, # ปกติแสกนรับเข้าอาจจะยังไม่ระบุความยาว หรือระบุมาใน parts
                "location": location,
                "status": "active"
            }
            
            if self.storage.add_roll(data, user=username):
                self.storage.add_log("receive_mobile", roll_id, data, user=username)
                logger.info(f"Mobile scan saved: {roll_id}")
                self.view.refresh_reports.emit()
                # แจ้งเตือนในหน้าจอหลัก (ถ้า Tab Scan เปิดอยู่)
                QMessageBox.information(self.view, "Mobile Scan", f"รับม้วนผ้า {roll_id} จากมือถือเรียบร้อย!")
        except Exception as e:
            logger.error(f"Error handling mobile scan: {e}")
