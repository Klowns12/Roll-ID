"""
Suppliers Manager - จัดการข้อมูล Suppliers จากไฟล์ CSV
"""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional


class SuppliersManager:
    """จัดการข้อมูล Suppliers จากไฟล์ CSV"""
    
    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        self.data = None
        self.load_data()
    
    def load_data(self):
        """โหลดข้อมูลจากไฟล์ CSV"""
        try:
            if self.csv_path.exists():
                # อ่านไฟล์ CSV
                self.data = pd.read_csv(self.csv_path, encoding='utf-8')
                # ลบแถว "Suppliers" ถ้ามี
                self.data = self.data[self.data.iloc[:, 1] != 'Suppliers']
                self.data = self.data.reset_index(drop=True)
                print(f"Loaded {len(self.data)} suppliers from {self.csv_path}")
            else:
                print(f"Suppliers file not found: {self.csv_path}")
                self.data = pd.DataFrame()
        except Exception as e:
            print(f"Error loading suppliers data: {e}")
            self.data = pd.DataFrame()
    
    def search_by_supplier(self, supplier_name: str) -> List[Dict]:
        """ค้นหา Suppliers ตามชื่อ"""
        if self.data is None or len(self.data) == 0:
            return []
        
        try:
            # ค้นหาในคอลัมน์ที่ 1 (Suppliers)
            supplier_col = self.data.columns[1]
            results = self.data[
                self.data[supplier_col].str.contains(supplier_name, case=False, na=False)
            ]
            
            # แปลงเป็น list of dictionaries
            return results.to_dict('records')
        except Exception as e:
            print(f"Error searching suppliers: {e}")
            return []
    
    def search_by_code(self, code: str) -> Optional[Dict]:
        """ค้นหา Suppliers ตามรหัส (Code)"""
        if self.data is None or len(self.data) == 0:
            return None
        
        try:
            # ค้นหาในคอลัมน์ที่ 2 (Code)
            code_col = self.data.columns[2]
            result = self.data[self.data[code_col].astype(str).str.strip() == code.strip()]
            
            if len(result) > 0:
                return result.iloc[0].to_dict()
            return None
        except Exception as e:
            print(f"Error searching by code: {e}")
            return None
    
    def get_all_suppliers(self) -> List[str]:
        """ดึงรายชื่อ Suppliers ทั้งหมด"""
        if self.data is None or len(self.data) == 0:
            return []
        
        try:
            supplier_col = self.data.columns[1]
            suppliers = self.data[supplier_col].unique().tolist()
            return [s for s in suppliers if pd.notna(s) and s != 'Suppliers']
        except Exception as e:
            print(f"Error getting suppliers list: {e}")
            return []
    
    def get_row_by_code(self, code: str) -> Optional[Dict]:
        """ดึงข้อมูลทั้ง Row ตามรหัส"""
        return self.search_by_code(code)
