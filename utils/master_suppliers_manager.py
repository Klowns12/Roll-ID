"""
Master Suppliers Manager - รวมข้อมูลจาก MasterDATA.csv, Suppliers.csv, Master_Dispatch.csv และ storage.db
"""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
import sqlite3
import os

class MasterSuppliersManager:
    """จัดการข้อมูล Suppliers จากไฟล์ MasterDATA.csv, Suppliers.csv, Master_Dispatch.csv และ storage.db"""

    master_data_path = os.path.join(os.getcwd(),"data", "MasterDATA.csv")
    suppliers_path = os.path.join(os.getcwd(),"data", "Suppliers.csv")
    dispatch_path = os.path.join(os.getcwd(),"data", "MasterDispatch.csv")
    db_path = os.path.join(os.getcwd(), "data", "storage.db")


    def __init__(self):
        print("------------- init master suppliers manager ---------")
        print(self.master_data_path)
        print(self.suppliers_path)
        print(self.dispatch_path)
        print(self.db_path)

        self.master_data = None
        self.suppliers_data = None
        self.dispatch_data = None
        self.rolls_data = None
        self.combined_data = None
        self.load_data()
    
    def load_data(self):
        """โหลดข้อมูลจากไฟล์ทั้งหมด"""
        try:
            # โหลด MasterDATA.csv
            if os.path.exists(self.master_data_path):
                self.master_data = pd.read_csv(self.master_data_path, encoding='utf-8')
                print(f"Loaded {len(self.master_data)} rows from MasterDATA.csv")
            
            # โหลด Suppliers.csv
            if os.path.exists(self.suppliers_path):
                self.suppliers_data = pd.read_csv(self.suppliers_path, encoding='utf-8')
                # ลบแถวที่มี 'Item' หรือ 'Suppliers' ในคอลัมน์แรก หรือ NaN
                self.suppliers_data = self.suppliers_data[
                    (self.suppliers_data.iloc[:, 0] != 'Item') & 
                    (self.suppliers_data.iloc[:, 0] != 'Suppliers') &
                    (self.suppliers_data.iloc[:, 0].notna())
                ]
                self.suppliers_data = self.suppliers_data.reset_index(drop=True)
                # เปลี่ยนชื่อคอลัมน์ Unnamed: 1 เป็น Suppliers
                if 'Unnamed: 1' in self.suppliers_data.columns:
                    self.suppliers_data = self.suppliers_data.rename(columns={'Unnamed: 1': 'Suppliers'})
                print(f"Loaded {len(self.suppliers_data)} rows from Suppliers.csv")
            
            # โหลด Master_Dispatch.csv
            if os.path.exists(self.dispatch_path):
                self.dispatch_data = pd.read_csv(self.dispatch_path, encoding='utf-8')
                print(f"Loaded {len(self.dispatch_data)} rows from Master_Dispatch.csv")
            
            # โหลด Rolls จาก storage.db (สำหรับ roll_id และ lot)
            if os.path.exists(self.db_path):
                try:
                    conn = sqlite3.connect(str(self.db_path))
                    self.rolls_data = pd.read_sql_query("SELECT * FROM rolls", conn)
                    conn.close()
                    print(f"Loaded {len(self.rolls_data)} rows from storage.db")
                except Exception as e:
                    print(f"Warning: Could not load rolls from storage.db: {e}")
                    self.rolls_data = None
            
            # รวมข้อมูล
            self.combine_data()
            
        except Exception as e:
            print(f"Error loading data: {e}")
    
    def combine_data(self):
        """รวมข้อมูลจากทั้งสองไฟล์"""
        try:
            if self.master_data is None or self.suppliers_data is None:
                return
            
            # ใช้ pdt_code (MasterDATA) และ Code (Suppliers) เป็น key
            # Rename columns เพื่อให้ง่ายต่อการรวม
            master_renamed = self.master_data.copy()
            suppliers_renamed = self.suppliers_data.copy()
            
            # Rename Code column ใน Suppliers ให้เป็น pdt_code
            if 'Code' in suppliers_renamed.columns:
                suppliers_renamed = suppliers_renamed.rename(columns={'Code': 'pdt_code'})
            
            # Merge โดยใช้ pdt_code
            merged = pd.merge(
                master_renamed,
                suppliers_renamed,
                on='pdt_code',
                how='outer',
                suffixes=('_master', '_suppliers')
            )
            
            # ลบ duplicate columns
            self.combined_data = merged.loc[:, ~merged.columns.duplicated()]
            print(f"Combined data: {len(self.combined_data)} rows")
            
        except Exception as e:
            print(f"Error combining data: {e}")
    
    def search_by_supplier_name(self, supplier_name: str) -> List[Dict]:
        """ค้นหาตาม Supplier Name"""
        if self.combined_data is None or len(self.combined_data) == 0:
            return []
        
        try:
            # ค้นหาใน spl_name (MasterDATA) หรือ Suppliers column (Suppliers.csv)
            results = []
            
            # ค้นหาใน spl_name
            if 'spl_name' in self.combined_data.columns:
                mask = self.combined_data['spl_name'].astype(str).str.contains(
                    supplier_name, case=False, na=False
                )
                results.extend(self.combined_data[mask].to_dict('records'))
            
            # ค้นหาใน Suppliers column (จาก Suppliers.csv)
            if 'Suppliers' in self.combined_data.columns:
                mask = self.combined_data['Suppliers'].astype(str).str.contains(
                    supplier_name, case=False, na=False
                )
                results.extend(self.combined_data[mask].to_dict('records'))
            
            # ลบ duplicates
            unique_results = []
            seen = set()
            for item in results:
                key = item.get('pdt_code', '')
                if key and key not in seen:
                    unique_results.append(item)
                    seen.add(key)
            
            return unique_results
            
        except Exception as e:
            print(f"Error searching by supplier name: {e}")
            return []
    
    def search_by_code(self, code: str) -> Optional[Dict]:
        """ค้นหาตาม Code (pdt_code)"""
        if self.combined_data is None or len(self.combined_data) == 0:
            return None
        
        try:
            result = self.combined_data[
                self.combined_data['pdt_code'].astype(str).str.strip() == code.strip()
            ]
            
            if len(result) > 0:
                return result.iloc[0].to_dict()
            return None
        except Exception as e:
            print(f"Error searching by code: {e}")
            return None
    
    def get_all_suppliers(self) -> List[str]:
        """ดึงรายชื่อ Suppliers ทั้งหมด"""
        if self.combined_data is None or len(self.combined_data) == 0:
            return []
        
        try:
            suppliers = set()
            
            # เก็บจาก spl_name
            if 'spl_name' in self.combined_data.columns:
                for s in self.combined_data['spl_name'].unique():
                    if pd.notna(s) and str(s).strip():
                        suppliers.add(str(s).strip())
            
            # เก็บจาก Suppliers column
            if 'Suppliers' in self.combined_data.columns:
                for s in self.combined_data['Suppliers'].unique():
                    if pd.notna(s) and str(s).strip():
                        suppliers.add(str(s).strip())
            
            return sorted(list(suppliers))
        except Exception as e:
            print(f"Error getting suppliers list: {e}")
            return []
    
    def search_combined(self, supplier_name: str = "", search_query: str = "") -> List[Dict]:
        """ค้นหาพร้อมกันทั้ง Supplier Name และ Code/Location/Roll ID/Lot จากทุกตาราง
        ถ้าไม่มีการค้นหา จะแสดงข้อมูลทั้งหมดจาก Suppliers.csv
        ถ้าค้นหา code ที่ตรงกัน จะแสดงทั้งหมดจากทุกตารางที่มี code นั้น"""
        results = []
        
        try:
            # ถ้าไม่มีการค้นหา ให้แสดงข้อมูลทั้งหมดจาก Suppliers.csv
            if not supplier_name.strip() and not search_query.strip():
                if self.suppliers_data is not None:
                    return self.suppliers_data.to_dict('records')
                return []
            
            # ถ้าค้นหา code ที่ตรงกัน ให้แสดงทั้งหมดจากทุกตาราง
            if search_query.strip() and not supplier_name.strip():
                # ค้นหา Code, Location, Roll ID, Lot จากทุกตาราง
                code_matches = []
                
                # ค้นหาจาก MasterDATA
                if self.master_data is not None:
                    mask = self.master_data['pdt_code'].astype(str).str.contains(search_query, case=False, na=False)
                    if 'Location' in self.master_data.columns:
                        mask = mask | self.master_data['Location'].astype(str).str.contains(search_query, case=False, na=False)
                    master_results = self.master_data[mask]
                    code_matches.extend(master_results.to_dict('records'))
                
                # ค้นหาจาก Suppliers.csv
                if self.suppliers_data is not None:
                    mask = self.suppliers_data['Code'].astype(str).str.contains(search_query, case=False, na=False)
                    if 'Location' in self.suppliers_data.columns:
                        mask = mask | self.suppliers_data['Location'].astype(str).str.contains(search_query, case=False, na=False)
                    suppliers_results = self.suppliers_data[mask]
                    code_matches.extend(suppliers_results.to_dict('records'))
                
                # ค้นหาจาก Master_Dispatch.csv
                if self.dispatch_data is not None:
                    dispatch_results = self.dispatch_data[
                        (self.dispatch_data['code'].astype(str).str.contains(search_query, case=False, na=False)) |
                        (self.dispatch_data['location'].astype(str).str.contains(search_query, case=False, na=False))
                    ]
                    code_matches.extend(dispatch_results.to_dict('records'))
                
                # ค้นหาจาก Rolls (storage.db) - สำหรับ roll_id, lot, location
                if self.rolls_data is not None:
                    rolls_results = self.rolls_data[
                        (self.rolls_data['roll_id'].astype(str).str.contains(search_query, case=False, na=False)) |
                        (self.rolls_data['lot'].astype(str).str.contains(search_query, case=False, na=False)) |
                        (self.rolls_data['sku'].astype(str).str.contains(search_query, case=False, na=False)) |
                        (self.rolls_data['location'].astype(str).str.contains(search_query, case=False, na=False))
                    ]
                    code_matches.extend(rolls_results.to_dict('records'))
                
                return code_matches
            
            # ค้นหาจาก MasterDATA
            if self.master_data is not None:
                master_results = self.master_data.copy()
                
                if supplier_name.strip():
                    mask = master_results['spl_name'].astype(str).str.contains(
                        supplier_name, case=False, na=False
                    )
                    master_results = master_results[mask]
                
                if search_query.strip():
                    # ค้นหา Code, Location, Roll ID, Lot
                    mask = master_results['pdt_code'].astype(str).str.contains(search_query, case=False, na=False)
                    if 'Location' in master_results.columns:
                        mask = mask | master_results['Location'].astype(str).str.contains(search_query, case=False, na=False)
                    master_results = master_results[mask]
                
                results.extend(master_results.to_dict('records'))
            
            # ค้นหาจาก Suppliers.csv
            if self.suppliers_data is not None:
                suppliers_results = self.suppliers_data.copy()
                
                if supplier_name.strip():
                    mask = suppliers_results['Suppliers'].astype(str).str.contains(
                        supplier_name, case=False, na=False
                    )
                    suppliers_results = suppliers_results[mask]
                
                if search_query.strip():
                    # ค้นหา Code, Location
                    mask = suppliers_results['Code'].astype(str).str.contains(search_query, case=False, na=False)
                    if 'Location' in suppliers_results.columns:
                        mask = mask | suppliers_results['Location'].astype(str).str.contains(search_query, case=False, na=False)
                    suppliers_results = suppliers_results[mask]
                
                results.extend(suppliers_results.to_dict('records'))
            
            # ค้นหาจาก Master_Dispatch.csv (สำหรับ Roll ID, Lot)
            if self.dispatch_data is not None:
                dispatch_results = self.dispatch_data.copy()
                
                if supplier_name.strip():
                    mask = dispatch_results['spl_name'].astype(str).str.contains(
                        supplier_name, case=False, na=False
                    )
                    dispatch_results = dispatch_results[mask]
                
                if search_query.strip():
                    # ค้นหา Code, Location, Roll ID, Lot
                    mask = (
                        dispatch_results['code'].astype(str).str.contains(search_query, case=False, na=False) |
                        dispatch_results['location'].astype(str).str.contains(search_query, case=False, na=False) |
                        dispatch_results['roll_id'].astype(str).str.contains(search_query, case=False, na=False) |
                        dispatch_results['lot'].astype(str).str.contains(search_query, case=False, na=False)
                    )
                    dispatch_results = dispatch_results[mask]
                
                results.extend(dispatch_results.to_dict('records'))
            
            # ลบ duplicates โดยใช้ code เป็น key (เฉพาะเมื่อค้นหา Supplier Name)
            if supplier_name.strip():
                unique_results = []
                seen = set()
                for item in results:
                    key = item.get('pdt_code') or item.get('Code') or item.get('code', '')
                    if key and key not in seen:
                        unique_results.append(item)
                        seen.add(key)
                return unique_results
            
            return results
            
        except Exception as e:
            print(f"Error in combined search: {e}")
            return []
    
    def get_row_data(self, row: Dict, search_type: str = "all") -> Dict:
        """
        ดึงข้อมูลแยกจากแต่ละไฟล์ โดยค้นหาจากทุกตารางให้ครบ
        
        search_type:
        - "all": ดึงทั้งหมด
        - "supplier": ดึงเฉพาะเมื่อค้นหาด้วย Suppliers (แสดง Exist. Qty, เศษ.QTY)
        """
        try:
            result = {}
            
            # ดึง code จากแหล่งต่างๆ
            code = row.get('Code') or row.get('pdt_code') or row.get('code') or row.get('sku', '')
            result['Code'] = code
            
            # ค้นหาข้อมูลเพิ่มเติมจากตารางอื่นๆ ถ้า code ตรงกัน
            master_row = None
            suppliers_row = None
            dispatch_row = None
            rolls_row = None
            
            if code:
                # ค้นหาใน MasterDATA
                if self.master_data is not None:
                    master_matches = self.master_data[
                        self.master_data['pdt_code'].astype(str).str.strip() == str(code).strip()
                    ]
                    if len(master_matches) > 0:
                        master_row = master_matches.iloc[0].to_dict()
                
                # ค้นหาใน Suppliers
                if self.suppliers_data is not None:
                    suppliers_matches = self.suppliers_data[
                        self.suppliers_data['Code'].astype(str).str.strip() == str(code).strip()
                    ]
                    if len(suppliers_matches) > 0:
                        suppliers_row = suppliers_matches.iloc[0].to_dict()
                
                # ค้นหาใน Master_Dispatch
                if self.dispatch_data is not None:
                    dispatch_matches = self.dispatch_data[
                        self.dispatch_data['code'].astype(str).str.strip() == str(code).strip()
                    ]
                    if len(dispatch_matches) > 0:
                        dispatch_row = dispatch_matches.iloc[0].to_dict()
                
                # ค้นหาใน Rolls (storage.db) - สำหรับ roll_id และ lot
                if self.rolls_data is not None:
                    rolls_matches = self.rolls_data[
                        self.rolls_data['sku'].astype(str).str.strip() == str(code).strip()
                    ]
                    if len(rolls_matches) > 0:
                        rolls_row = rolls_matches.iloc[0].to_dict()
            
            # SubPartCode: จาก spl_part_code (MasterDATA.csv)
            result['SubPartCode'] = master_row.get('spl_part_code', '') if master_row else row.get('spl_part_code', '')
            
            # SupCode: จาก spl_code (MasterDATA.csv)
            result['SupCode'] = master_row.get('spl_code', '') if master_row else row.get('spl_code', '')
            
            # Supplier Name: จาก Suppliers (Suppliers.csv)
            result['Supplier Name'] = suppliers_row.get('Suppliers', '') if suppliers_row else row.get('Suppliers', '')
            
            # Description: จาก pdt_name (MasterDATA.csv หรือ storage.db)
            result['Description'] = (
                rolls_row.get('pdt_name', '') if rolls_row else
                master_row.get('pdt_name', '') if master_row else 
                row.get('pdt_name', '')
            )
            
            # Location: จาก Location (Suppliers.csv) หรือ location (Master_Dispatch.csv)
            result['Location'] = (
                suppliers_row.get('Location', '') if suppliers_row else 
                dispatch_row.get('location', '') if dispatch_row else 
                row.get('Location', '') or row.get('location', '')
            )
            
            # Unit: จาก unit_type (MasterDATA.csv)
            result['Unit'] = master_row.get('unit_type', '') if master_row else row.get('unit_type', '')
            
            # Lot No.: จาก lot (storage.db หรือ Master_Dispatch.csv)
            result['Lot No.'] = (
                rolls_row.get('lot', '') if rolls_row else
                dispatch_row.get('lot', '') if dispatch_row else 
                row.get('lot', '')
            )
            
            # Roll ID: จาก roll_id (storage.db)
            result['Roll ID'] = rolls_row.get('roll_id', '') if rolls_row else row.get('roll_id', '')
            
            # Exist. Qty: จาก Suppliers.csv (แสดงเฉพาะเมื่อค้นหาด้วย Suppliers)
            if search_type == "supplier":
                result['Exist. Qty'] = suppliers_row.get('QTY', '') if suppliers_row else row.get('QTY', '')
                result['เศษ.QTY'] = suppliers_row.get('เศษ', '') if suppliers_row else row.get('เศษ', '')
            
            return result
            
        except Exception as e:
            print(f"Error getting row data: {e}")
            return {}
