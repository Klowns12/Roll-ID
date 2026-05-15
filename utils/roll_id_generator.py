"""
Roll ID Generator - สร้าง Roll ID อัตโนมัติ
"""
import sqlite3
from pathlib import Path
from typing import Optional
from datetime import datetime


class RollIDGenerator:
    """สร้าง Roll ID อัตโนมัติในรูปแบบ R000001, R000002, ..."""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.db_path = self.data_dir / "storage.db"
    
    def get_next_roll_id(self) -> str:
        """ดึง Roll ID ถัดไปในรูปแบบ RYYXXXXXX (เช่น R26000001)"""
        year_prefix = datetime.now().strftime("%y") # "26" สำหรับปี 2026
        prefix = f"R{year_prefix}"
        
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            # ดึง Roll ID ที่ขึ้นต้นด้วย R + ปีปัจจุบัน
            cur.execute(f"SELECT roll_id FROM rolls WHERE roll_id LIKE '{prefix}%'")
            results = cur.fetchall()
            conn.close()
            
            max_seq = 0
            for result in results:
                roll_id = result[0]
                try:
                    # ตัด RYY ออกแล้วแปลงเลข 6 หลักที่เหลือเป็น int
                    seq = int(roll_id[3:])
                    if seq > max_seq:
                        max_seq = seq
                except (ValueError, IndexError):
                    pass
            
            # สร้าง Roll ID ถัดไป
            next_seq = max_seq + 1
            return f"{prefix}{next_seq:06d}"
            
        except Exception as e:
            print(f"Error getting next roll ID: {e}")
            return f"{prefix}000001"
    
    def get_next_roll_ids(self, count: int) -> list[str]:
        """ดึง Roll IDs ถัดไปหลายๆ ตัวตามรูปแบบใหม่"""
        year_prefix = datetime.now().strftime("%y")
        prefix = f"R{year_prefix}"
        
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            cur.execute(f"SELECT roll_id FROM rolls WHERE roll_id LIKE '{prefix}%'")
            results = cur.fetchall()
            conn.close()
            
            max_seq = 0
            for result in results:
                roll_id = result[0]
                try:
                    seq = int(roll_id[3:])
                    if seq > max_seq:
                        max_seq = seq
                except (ValueError, IndexError):
                    pass
            
            next_seqs = range(max_seq + 1, max_seq + count + 1)
            return [f"{prefix}{num:06d}" for num in next_seqs]
            
        except Exception as e:
            print(f"Error getting next roll IDs: {e}")
            return [f"{prefix}{num:06d}" for num in range(1, count + 1)]
    
    def validate_roll_id(self, roll_id: str) -> bool:
        """ตรวจสอบว่า Roll ID มีรูปแบบถูกต้อง"""
        if not roll_id.startswith('R'):
            return False
        try:
            int(roll_id[1:])
            return True
        except ValueError:
            return False
