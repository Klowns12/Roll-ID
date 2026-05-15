"""
Unified Suppliers Manager - รวมความสามารถของ SuppliersManager และ MasterSuppliersManager
จัดการข้อมูลจากฐานข้อมูล SQLite (storage.db) เป็นหลัก
"""
import pandas as pd
import sqlite3
import os
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class SuppliersManager:
    """จัดการข้อมูลสินค้าหลักและ Supplier จากฐานข้อมูล SQLite"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            self.db_path = os.path.join(os.getcwd(), "data", "storage.db")
        else:
            self.db_path = db_path
            
        self.master_data = None
        self.suppliers_data = None
        self.combined_data = None
        self.load_data()
    
    def load_data(self):
        """โหลดข้อมูลจาก SQLite"""
        try:
            if not os.path.exists(self.db_path):
                logger.warning(f"Database not found: {self.db_path}")
                return

            conn = sqlite3.connect(self.db_path)
            
            # 1. โหลด Master Products
            self.master_data = pd.read_sql_query("SELECT * FROM master_products", conn)
            
            # 2. โหลด Supplier Stock
            self.suppliers_data = pd.read_sql_query("SELECT * FROM supplier_stock", conn)
            # ปรับชื่อคอลัมน์ให้ตรงกับ Logic เดิมที่โปรแกรมคาดหวัง
            self.suppliers_data = self.suppliers_data.rename(columns={
                'pdt_code': 'Code',
                'supplier_name': 'Suppliers',
                'location': 'Location',
                'qty': 'QTY',
                'full_rolls': 'ม้วนเต็ม',
                'scrap_qty': 'เศษ'
            })
            
            conn.close()
            
            # 3. รวมข้อมูล (Combine)
            self.combine_data()
            
            logger.debug(f"Loaded {len(self.master_data)} products and {len(self.suppliers_data)} supplier records")
        except Exception as e:
            logger.error(f"Error loading data: {e}")

    def combine_data(self):
        """รวมข้อมูล Master และ Supplier Stock"""
        try:
            if self.master_data is None or self.suppliers_data is None:
                return
            
            m_df = self.master_data.copy()
            s_df = self.suppliers_data.copy()
            
            # เปลี่ยนชื่อให้ตรงกันก่อน Merge
            if 'Code' in s_df.columns:
                s_df = s_df.rename(columns={'Code': 'pdt_code'})
            
            self.combined_data = pd.merge(
                m_df, s_df, on='pdt_code', how='left'
            )
        except Exception as e:
            logger.error(f"Error combining data: {e}")

    # --- Methods สำหรับความเข้ากันได้ย้อนหลัง (Backward Compatibility) ---
    
    def search_by_supplier(self, supplier_name: str) -> List[Dict]:
        """Alias สำหรับ search_by_supplier_name (ใช้ใน ReportsTab)"""
        return self.search_by_supplier_name(supplier_name)

    def search_by_supplier_name(self, supplier_name: str) -> List[Dict]:
        """ค้นหาตามชื่อ Supplier"""
        if self.combined_data is None or self.combined_data.empty:
            return []
        
        try:
            # ค้นหาทั้งจาก spl_name และ Suppliers column
            mask = self.combined_data['spl_name'].astype(str).str.contains(supplier_name, case=False, na=False)
            if 'Suppliers' in self.combined_data.columns:
                mask = mask | self.combined_data['Suppliers'].astype(str).str.contains(supplier_name, case=False, na=False)
            
            return self.combined_data[mask].to_dict('records')
        except Exception as e:
            logger.error(f"Error searching by supplier name: {e}")
            return []

    def search_by_code(self, code: str) -> Optional[Dict]:
        """ค้นหาตามรหัส Code"""
        if self.combined_data is None or self.combined_data.empty:
            return None
        
        try:
            result = self.combined_data[self.combined_data['pdt_code'].astype(str).str.strip() == str(code).strip()]
            if not result.empty:
                return result.iloc[0].to_dict()
            return None
        except Exception as e:
            logger.error(f"Error searching by code: {e}")
            return None

    def get_all_suppliers(self) -> List[str]:
        """ดึงรายชื่อ Supplier ทั้งหมด"""
        suppliers = set()
        if self.master_data is not None:
            suppliers.update(self.master_data['spl_name'].dropna().unique())
        if self.suppliers_data is not None:
            suppliers.update(self.suppliers_data['Suppliers'].dropna().unique())
        return sorted([str(s).strip() for s in suppliers if str(s).strip()])

    def search_combined(self, supplier_name: str = "", search_query: str = "") -> List[Dict]:
        """ค้นหาแบบรวมหลายเงื่อนไข (ใช้ใน ScanTab)"""
        if not supplier_name.strip() and not search_query.strip():
            return self.suppliers_data.to_dict('records') if self.suppliers_data is not None else []
            
        results = self.search_by_supplier_name(supplier_name)
        if search_query.strip():
            # กรองเพิ่มด้วย search_query
            filtered = []
            for r in results:
                if any(search_query.lower() in str(val).lower() for val in r.values()):
                    filtered.append(r)
            return filtered
        return results

    def get_row_by_code(self, code: str) -> Optional[Dict]:
        """ดึงข้อมูลทั้ง Row ตามรหัส (สำหรับ ReportsTab)"""
        return self.search_by_code(code)

    def get_row_data(self, row: Dict, search_type: str = "all") -> Dict:
        """แปลงข้อมูล Row ให้มีโครงสร้างที่ UI คาดหวัง (สำหรับ StatisticsTab)"""
        try:
            code = row.get('Code') or row.get('pdt_code') or ''
            master = self.search_by_code(code) or {}
            
            result = {
                'Code': code,
                'SubPartCode': master.get('spl_part_code', row.get('spl_part_code', '')),
                'SupCode': master.get('spl_code', row.get('spl_code', '')),
                'Supplier Name': master.get('Suppliers', row.get('Suppliers', master.get('spl_name', ''))),
                'Description': master.get('pdt_name', row.get('Description', '')),
                'Location': master.get('Location', row.get('Location', '')),
                'Unit': master.get('unit_type', row.get('Unit', 'MTS')),
                'Lot No.': row.get('lot_no', ''),
                'QTY': row.get('QTY', ''),
                'ม้วนเต็ม': row.get('ม้วนเต็ม', ''),
                'เศษ': row.get('เศษ', '')
            }
            
            if search_type == "supplier":
                result['Exist. Qty'] = result['QTY']
                result['เศษ.QTY'] = result['เศษ']
                
            return result
        except Exception as e:
            logger.error(f"Error getting row data: {e}")
            return row
