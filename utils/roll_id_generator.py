"""
Roll ID Generator - สร้าง Roll ID อัตโนมัติ
"""
import sqlite3
from pathlib import Path
from typing import Optional


class RollIDGenerator:
    """สร้าง Roll ID อัตโนมัติในรูปแบบ R000001, R000002, ..."""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.db_path = self.data_dir / "storage.db"
    
    def get_next_roll_id(self) -> str:
        """ดึง Roll ID ถัดไป"""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            # ดึง Roll ID ทั้งหมดและหาตัวเลขสูงสุด
            cur.execute("SELECT roll_id FROM rolls WHERE roll_id LIKE 'R%'")
            results = cur.fetchall()
            conn.close()
            
            max_number = 0
            for result in results:
                roll_id = result[0]
                if roll_id.startswith('R'):
                    try:
                        number = int(roll_id[1:])
                        if number > max_number:
                            max_number = number
                    except ValueError:
                        pass
            
            # สร้าง Roll ID ถัดไป (6 หลัก)
            next_number = max_number + 1
            return f"R{next_number:06d}"
            
        except Exception as e:
            print(f"Error getting next roll ID: {e}")
            return "R001"
    
    def get_next_roll_ids(self, count: int) -> list[str]:
        """
        ดึง Roll IDs ถัดไปหลายๆ ตัว
        
        Args:
            count: จำนวน Roll IDs ที่ต้องการ
            
        Returns:
            list[str]: รายการ Roll IDs ถัดไปตามจำนวนที่ระบุ
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            # ดึง Roll ID ทั้งหมดและหาตัวเลขสูงสุด
            cur.execute("SELECT roll_id FROM rolls WHERE roll_id LIKE 'R%'")
            results = cur.fetchall()
            conn.close()
            
            max_number = 0
            for result in results:
                roll_id = result[0]
                if roll_id.startswith('R'):
                    try:
                        number = int(roll_id[1:])
                        if number > max_number:
                            max_number = number
                    except ValueError:
                        pass
            
            # สร้าง Roll IDs ถัดไปตามจำนวนที่ต้องการ (6 หลัก)
            next_numbers = range(max_number + 1, max_number + count + 1)
            return [f"R{num:06d}" for num in next_numbers]
            
        except Exception as e:
            print(f"Error getting next roll IDs: {e}")
            # ถ้าเกิดข้อผิดพลาด สร้าง ID เริ่มต้น
            return [f"R{num:06d}" for num in range(1, count + 1)]
    
    def validate_roll_id(self, roll_id: str) -> bool:
        """ตรวจสอบว่า Roll ID มีรูปแบบถูกต้อง"""
        if not roll_id.startswith('R'):
            return False
        try:
            int(roll_id[1:])
            return True
        except ValueError:
            return False
