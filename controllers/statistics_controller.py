import logging
import csv
from PySide6.QtWidgets import QMessageBox, QFileDialog

logger = logging.getLogger(__name__)

class StatisticsController:
    """Class สำหรับจัดการ Logic การเตรียมข้อมูลและกรองข้อมูลรายงาน"""
    def __init__(self, view, storage, suppliers_manager):
        self.view = view
        self.storage = storage
        self.suppliers_manager = suppliers_manager
        self.all_filtered_rows = []
        self.displayed_count = 0
        self.batch_size = 100

    def refresh_data(self):
        """โหลดข้อมูลเริ่มต้น (สต็อก และ ประวัติการเบิก) พร้อมระบบกรองละเอียด"""
        try:
            if not self.view or not hasattr(self.view, 'suppliers_input'):
                return
            
            # อ่านค่าตัวกรอง
            supplier_name = self.view.suppliers_input.text().strip()
            search_query = self.view.search_input.text().strip()
            search_field = self.view.search_field_combo.currentText()
            
            color_filter = self.view.color_input.text().strip()
            min_len = self.view.min_len_input.text().strip()
            max_len = self.view.max_len_input.text().strip()
            
            # แปลงค่าความยาวเป็นตัวเลข
            try: min_val = float(min_len) if min_len else None
            except: min_val = None
            try: max_val = float(max_len) if max_len else None
            except: max_val = None
            
            # 1. จัดการข้อมูลสต็อก (ตารางบน)
            all_rolls = self.storage.search_rolls()
            self.all_filtered_rows = self._process_and_merge(
                all_rolls, supplier_name, search_query, search_field, 
                color_filter, min_val, max_val
            )
            self.displayed_count = 0
            self.load_next_batch()
            
            # 2. จัดการประวัติการเบิก (ตารางล่าง)
            history = self.storage.get_dispatch_history(limit=200)
            filtered_history = self._process_dispatches(
                history, supplier_name, search_query, search_field,
                color_filter, min_val, max_val
            )
            self.view.append_dispatch_to_table(filtered_history, is_first_batch=True)
        except (RuntimeError, AttributeError):
            return

    def _process_dispatches(self, history, s_name, query, field, color_f, min_l, max_l):
        merged = []
        for h in history:
            # กรอง Supplier
            match_supplier = not s_name or s_name.lower() in str(h.get('supplier_name', '')).lower()
            
            # กรองสี
            h_color = str(h.get('color', '')).lower()
            match_color = not color_f or color_f.lower() in h_color
            
            # กรองความยาวเบิก
            h_len = float(h.get('length_dispatched', 0))
            match_len = True
            if min_l is not None and h_len < min_l: match_len = False
            if max_l is not None and h_len > max_l: match_len = False
            
            # กรองค้นหาทั่วไป
            match_search = True
            if query:
                q = query.lower()
                if field == "Code":
                    match_search = q in str(h.get('pdt_code', '')).lower()
                elif field == "Description":
                    match_search = q in str(h.get('description', '')).lower()
                elif field == "Lot" or field == "Lot No.":
                    match_search = q in str(h.get('lot_no', '')).lower()
                elif field == "Roll ID":
                    match_search = q in str(h.get('roll_id', '')).lower()
            
            if match_supplier and match_color and match_len and match_search:
                merged.append({
                    "Timestamp": h.get('timestamp', ''),
                    "Roll ID": h.get('roll_id', ''),
                    "Code": h.get('pdt_code', ''),
                    "Lot No.": h.get('lot_no', ''),
                    "Length": f"{h.get('length_dispatched', 0):.2f}",
                    "Original": f"{h.get('length_original', 0):.2f}",
                    "Remaining": f"{h.get('length_remaining', 0):.2f}",
                    "Customer": h.get('customer_name', ''),
                    "Doc No": h.get('document_no', ''),
                    "User": h.get('user', '')
                })
        return merged

    def _process_and_merge(self, rolls, s_name, query, field, color_f, min_l, max_l):
        merged = []
        for roll in rolls:
            # กรองข้อมูลตามที่ผู้ใช้ระบุในหน้า UI
            s_val = str(roll.supplier_name or "").lower()
            match_supplier = not s_name or s_name.lower() in s_val
            
            # กรองสี
            r_color = str(getattr(roll, 'color', '') or '').lower()
            match_color = not color_f or color_f.lower() in r_color
            
            # กรองช่วงความยาว (Length)
            r_len = float(roll.length or 0)
            match_len = True
            if min_l is not None and r_len < min_l: match_len = False
            if max_l is not None and r_len > max_l: match_len = False
            
            match_search = True
            if query:
                q = query.lower()
                if field == "Code":
                    match_search = q in str(roll.code).lower()
                elif field == "Description":
                    match_search = q in str(getattr(roll, 'description', '') or '').lower()
                elif field == "Lot" or field == "Lot No.":
                    match_search = q in str(roll.lot_no).lower()
                elif field == "Location":
                    match_search = q in str(roll.location).lower()
                elif field == "Roll ID":
                    match_search = q in str(roll.roll_id).lower()
            
            if match_supplier and match_color and match_len and match_search:
                # คำนวณสถานะตามเงื่อนไขใหม่
                status_text = ""
                if roll.status == "used" or roll.length <= 0:
                    status_text = "หมด (Depleted)"
                elif roll.length >= roll.length_original:
                    status_text = "เต็มม้วน (Full)"
                else:
                    status_text = "เศษ (Scrap)"

                merged.append({
                    "Code": roll.code, 
                    "Roll ID": roll.roll_id, 
                    "SubPartCode": roll.sub_part_code,
                    "SupCode": roll.sup_code, 
                    "Supplier Name": roll.supplier_name,
                    "Description": roll.description, 
                    "Lot No.": roll.lot_no,
                    "Location": roll.location, 
                    "Unit": roll.unit,
                    "Length": f"{roll.length:.2f}",
                    "Original": f"{roll.length_original:.2f}",
                    "Status": status_text
                })
        return merged

    def load_next_batch(self):
        """จัดการ Pagination และล้างตารางถ้าไม่มีข้อมูล"""
        try:
            total = len(self.all_filtered_rows)
            
            # ถ้าไม่มีข้อมูลเลย ให้ล้างตารางทิ้งทันที
            if total == 0:
                self.view.append_data_to_table([], is_first_batch=True)
                self.view.update_load_more_btn(0, 0)
                return

            if self.displayed_count >= total: return

            next_count = min(self.displayed_count + self.batch_size, total)
            batch = self.all_filtered_rows[self.displayed_count:next_count]
            
            self.view.append_data_to_table(batch, is_first_batch=(self.displayed_count == 0))
            self.displayed_count = next_count
            self.view.update_load_more_btn(self.displayed_count, total)
        except (RuntimeError, AttributeError):
            return

    def export_data(self):
        """ส่งออกข้อมูล CSV"""
        if not self.all_filtered_rows: return
        
        file_path, _ = QFileDialog.getSaveFileName(self.view, "Export Report", "", "CSV Files (*.csv)")
        if file_path:
            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=self.all_filtered_rows[0].keys())
                writer.writeheader()
                writer.writerows(self.all_filtered_rows)
            QMessageBox.information(self.view, "สำเร็จ", "Export เรียบร้อย")
