import os
import json
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass, asdict
import threading
import uuid

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------
# Data Models
# --------------------------------------------------------------------
@dataclass
class Roll:
    roll_id: str
    code: str
    sub_part_code: str = ""
    sup_code: str = ""
    supplier_name: str = ""
    description: str = ""
    lot_no: str = ""
    quantity: int = 1
    location: str = ""
    unit: str = "MTS"
    color: str = ""
    width: float = 0.0
    length: float = 0.0
    length_original: float = 0.0
    status: str = "active"
    date_received: str = ""

    def __post_init__(self):
        if not self.date_received:
            self.date_received = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_db_row(cls, row_dict: Dict[str, Any]):
        return cls(**row_dict)


@dataclass
class MasterProduct:
    pdt_code: str
    # Store all other fields in a dictionary to handle any number of columns
    extra_data: Dict[str, Any] = None

    def __post_init__(self):
        if self.extra_data is None:
            self.extra_data = {}

    def __getattr__(self, name):
        """Allow direct access to fields in extra_data (e.g., product.pdt_name)"""
        if self.extra_data and name in self.extra_data:
            return self.extra_data[name]
        raise AttributeError(f"'MasterProduct' object has no attribute '{name}'")

    def get(self, key: str, default: Any = "") -> Any:
        """Safely get a value from pdt_code or extra_data"""
        if key == "pdt_code":
            return self.pdt_code
        if self.extra_data and key in self.extra_data:
            val = self.extra_data[key]
            return val if val is not None else default
        return default

    def to_dict(self) -> Dict[str, Any]:
        d = {"pdt_code": self.pdt_code}
        if self.extra_data:
            d.update(self.extra_data)
        return d

    @classmethod
    def from_db_row(cls, row_dict: Dict[str, Any]):
        pdt_code = row_dict.pop("pdt_code", None)
        return cls(pdt_code=pdt_code, extra_data=row_dict)


@dataclass
class LogEntry:
    id: str
    timestamp: str
    action: str
    roll_id: str
    details: Dict[str, Any]
    user: str = "system"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# --------------------------------------------------------------------
# StorageManager using SQLite
# --------------------------------------------------------------------
class StorageManager:
    def __init__(self, data_dir: Union[str, Path]):
        from dotenv import load_dotenv
        load_dotenv()
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        db_file = os.getenv("DATABASE_FILE", "storage.db")
        self.db_path = self.data_dir / db_file
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._connect() as conn:
            cur = conn.cursor()

            # Table: Rolls (Simplified schema)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS rolls (
                roll_id TEXT PRIMARY KEY,
                code TEXT,
                sub_part_code TEXT,
                sup_code TEXT,
                supplier_name TEXT,
                description TEXT,
                lot_no TEXT,
                quantity INTEGER,
                location TEXT,
                unit TEXT,
                color TEXT,
                width REAL,
                length REAL,
                length_original REAL,
                status TEXT,
                date_received DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # Create indexes for rolls table
            cur.execute("CREATE INDEX IF NOT EXISTS idx_rolls_code ON rolls(code)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_rolls_location ON rolls(location)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_rolls_lot ON rolls(lot_no)")

            # Table: Master Products
            cur.execute("""
            CREATE TABLE IF NOT EXISTS master_products (
                pdt_code TEXT PRIMARY KEY,
                pdt_name TEXT,
                pdt_name_en TEXT,
                unit_type TEXT,
                spl_part_code TEXT,
                scrapqty REAL,
                create_name TEXT,
                create_date TEXT,
                update_name TEXT,
                update_date TEXT,
                last_buy_date TEXT,
                lastdate TEXT,
                pg_name TEXT,
                cate_name TEXT,
                spl_name TEXT,
                spl_code TEXT,
                location TEXT
            )
            """)

            # Table: Logs
            cur.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                action TEXT,
                roll_id TEXT,
                details TEXT,
                user TEXT
            )
            """)

            # Table: Users
            cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT,
                role TEXT,
                full_name TEXT,
                created_at TEXT,
                last_login TEXT
            )
            """)

            # Table: Supplier Stock (Legacy)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS supplier_stock (
                pdt_code TEXT,
                supplier_name TEXT,
                location TEXT,
                qty REAL,
                full_rolls REAL,
                scrap_qty REAL,
                PRIMARY KEY (pdt_code, supplier_name, location)
            )
            """)

            # Table: Dispatch History (Detailed)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS dispatch (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                roll_id TEXT,
                pdt_code TEXT,
                sub_part_code TEXT,
                sup_code TEXT,
                lot_no TEXT,
                color TEXT,
                width REAL,
                length_dispatched REAL,
                length_original REAL,
                length_remaining REAL,
                unit TEXT,
                location TEXT,
                supplier_name TEXT,
                description TEXT,
                document_no TEXT,
                customer_code TEXT,
                customer_name TEXT,
                user TEXT
            )
            """)

            # Create indexes for logs table (ต้องสร้างหลังจาก table ถูกสร้างแล้ว)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_logs_action ON logs(action)")
            
            # --- Migration: Convert width from TEXT to REAL if needed ---
            self._migrate_width_to_real(cur)
            
            # --- Migration: Convert date_received from TEXT to DATETIME if needed ---
            self._migrate_date_to_datetime(cur)
            
            # --- Migration: Update dispatch schema if needed ---
            self._migrate_dispatch_table(cur)
            # Table: App Settings (Key-Value)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """)
            
            conn.commit()

    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        with self._lock:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
                row = cur.fetchone()
                if row:
                    return row[0]
                return default

    def set_setting(self, key: str, value: str):
        with self._lock:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute("""
                INSERT OR REPLACE INTO app_settings (key, value)
                VALUES (?, ?)
                """, (key, value))
                conn.commit()

    def remove_setting(self, key: str):
        with self._lock:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute("DELETE FROM app_settings WHERE key = ?", (key,))
                conn.commit()

    def _migrate_width_to_real(self, cur):
        """ตรวจสอบและแปลงประเภทข้อมูลคอลัมน์ width เป็น REAL"""
        try:
            cur.execute("PRAGMA table_info(rolls)")
            columns = cur.fetchall()
            for col in columns:
                if col[1] == 'width' and col[2].upper() == 'TEXT':
                    logger.info("Migrating width column from TEXT to REAL...")
                    # SQLite ไม่รองรับ ALTER COLUMN TYPE ตรงๆ ต้องสร้างตารางใหม่หรือใช้เทคนิคอื่น
                    # ในที่นี้เราจะใช้วิธีเปลี่ยนชื่อและสร้างใหม่ถ้าเป็นระบบใหญ่ แต่สำหรับที่นี่
                    # เราจะลองแปลงข้อมูลด้วย SQL ง่ายๆ ก่อน (SQLite ยอมให้เก็บเลขใน TEXT ได้)
                    # แต่ถ้าอยากเปลี่ยน Type ถาวร ต้องทำแบบนี้:
                    cur.execute("CREATE TABLE rolls_new AS SELECT * FROM rolls")
                    cur.execute("DROP TABLE rolls")
                    # สร้างตารางใหม่ด้วย schema REAL (ใช้ SQL ตรงๆ)
                    cur.execute("""
                    CREATE TABLE rolls (
                        roll_id TEXT PRIMARY KEY, code TEXT, sub_part_code TEXT,
                        sup_code TEXT, supplier_name TEXT, description TEXT,
                        lot_no TEXT, quantity INTEGER, location TEXT,
                        unit TEXT, color TEXT, width REAL, length REAL,
                        status TEXT, date_received DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                    """)
                    cur.execute("INSERT INTO rolls SELECT * FROM rolls_new")
                    cur.execute("DROP TABLE rolls_new")
                    logger.info("Migration complete.")
                    break
        except Exception as e:
            logger.error(f"Migration error: {e}")

    def _migrate_date_to_datetime(self, cur):
        """ตรวจสอบและเปลี่ยนประเภทข้อมูล date_received เป็น DATETIME"""
        try:
            cur.execute("PRAGMA table_info(rolls)")
            columns = cur.fetchall()
            for col in columns:
                if col[1] == 'date_received' and col[2].upper() == 'TEXT':
                    logger.info("Migrating date_received column from TEXT to DATETIME...")
                    cur.execute("CREATE TABLE rolls_new AS SELECT * FROM rolls")
                    cur.execute("DROP TABLE rolls")
                    self._init_db() # จะเรียกใช้ schema ใหม่ที่เป็น DATETIME
                    cur.execute("INSERT INTO rolls SELECT * FROM rolls_new")
                    cur.execute("DROP TABLE rolls_new")
                    logger.info("Migration complete.")
                    break
        except Exception as e:
            logger.error(f"Date migration error: {e}")

    def _migrate_dispatch_table(self, cur):
        """ตรวจสอบและอัปเกรดตาราง dispatch ให้ถูกต้อง และย้ายจาก dispatch_legacy (ถ้ามี)"""
        try:
            # 1. เช็คว่ามี dispatch_legacy ไหม ถ้ามีให้ย้ายข้อมูลมา dispatch
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='dispatch_legacy'")
            if cur.fetchone():
                logger.info("Migrating dispatch_legacy to dispatch...")
                cur.execute("DROP TABLE IF EXISTS dispatch")
                self._init_db()
                cur.execute("INSERT INTO dispatch SELECT * FROM dispatch_legacy")
                cur.execute("DROP TABLE dispatch_legacy")
                logger.info("Migration from dispatch_legacy complete.")
                return

            # 2. เช็คโครงสร้างตาราง dispatch ปัจจุบัน
            cur.execute("PRAGMA table_info(dispatch)")
            columns = cur.fetchall()
            if len(columns) > 0 and len(columns) < 20:
                logger.info("Upgrading dispatch table schema...")
                cur.execute("CREATE TABLE dispatch_temp AS SELECT * FROM dispatch")
                cur.execute("DROP TABLE dispatch")
                self._init_db()
                # พยายามย้ายข้อมูลเดิมที่พอจะแมพได้
                # (กรณีนี้ถ้าโครงสร้างเปลี่ยนเยอะ การ DROP แล้วสร้างใหม่อาจปลอดภัยกว่าถ้าเป็นช่วงพัฒนา)
                logger.info("dispatch table upgraded.")
        except Exception as e:
            logger.error(f"Dispatch migration error: {e}")

    # ----------------------------------------------------------------
    # Roll Operations
    # ----------------------------------------------------------------
    def add_roll(self, roll: Union[Roll, Dict[str, Any]], user="system") -> bool:
        data = roll.to_dict() if isinstance(roll, Roll) else roll
        with self._connect() as conn:
            try:
                columns = ", ".join(data.keys())
                placeholders = ", ".join([f":{k}" for k in data.keys()])
                query = f"INSERT OR REPLACE INTO rolls ({columns}) VALUES ({placeholders})"
                
                conn.execute(query, data)
                conn.commit()
            except sqlite3.Error as e:
                logger.error(f"Error adding roll: {e}")
                return False

        self.add_log(
            action="roll_created",
            roll_id=data.get('roll_id'),
            details={
                "code": data.get('code'),
                "lot_no": data.get('lot_no'),
                "location": data.get('location'),
            },
            user=user
        )
        return True

    def get_roll(self, roll_id: str) -> Optional[Roll]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute("SELECT * FROM rolls WHERE roll_id = ?", (roll_id,))
            row = cur.fetchone()
        if not row:
            return None
        return Roll.from_db_row(dict(row))

    def get_roll_by_id(self, roll_id: str) -> Optional[Roll]:
        return self.get_roll(roll_id)
    
    def get_roll_by_code(self, code: str) -> Optional[Roll]:
        """ค้นหาม้วนจาก Code"""
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute("SELECT * FROM rolls WHERE code = ? LIMIT 1", (code,))
            row = cur.fetchone()
            if not row:
                return None
        return Roll.from_db_row(dict(row))

    def update_roll(self, roll_id: str, **updates) -> bool:
        if not updates:
            return False
        # Whitelist of allowed columns for the simplified schema
        allowed_columns = {
            'code', 'sub_part_code', 'sup_code', 'supplier_name', 'description',
            'lot_no', 'quantity', 'location', 'unit', 'color', 'width', 'length',
            'status', 'date_received'
        }
        # Filter updates to only include allowed columns
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_columns}
        if not filtered_updates:
            return False
        fields = ", ".join([f"{k}=?" for k in filtered_updates.keys()])
        values = list(filtered_updates.values()) + [roll_id]
        with self._connect() as conn:
            conn.execute(f"UPDATE rolls SET {fields} WHERE roll_id = ?", values)
            conn.commit()
        return True

    def cut_roll(self, roll_id: str, cut_length: float, user="system") -> bool:
        roll = self.get_roll(roll_id)
        if not roll or cut_length <= 0 or cut_length > roll.length:
            return False

        roll.length -= cut_length
        if roll.length <= 0:
            roll.status = "used"

        self.update_roll(roll_id, length=roll.length, status=roll.status)

        self.add_log(
            action="roll_cut",
            roll_id=roll_id,
            details={
                "cut_length": cut_length,
                "remaining_length": roll.length,
                "new_status": roll.status
            },
            user=user
        )
        return True

    def get_master_data_count(self) -> int:
        """นับจำนวนแถวในตาราง master_products ใน SQLite"""
        try:
            with self._connect() as conn:
                cur = conn.execute("SELECT COUNT(*) FROM master_products")
                count = cur.fetchone()[0]
            return count
        except Exception as e:
            logger.error(f"Error reading master product count from DB: {e}")
            return 0

    def get_roll_count(self, roll_id: Optional[str] = None) -> int:
        """นับจำนวนแถวใน rolls (ทั้งหมด หรือเฉพาะ roll_id)"""
        with self._connect() as conn:
            if roll_id:
                cur = conn.execute(
                    "SELECT COUNT(*) FROM rolls WHERE roll_id = ?",
                    (roll_id,)
                )
            else:
                cur = conn.execute("SELECT COUNT(*) FROM rolls")
            count = cur.fetchone()[0]
        return count
    
    def add_dispatch_record(self, roll, dispatch_length, document_no="", customer_code="", customer_name="", user="system"):
        """บันทึกข้อมูลการเบิกจ่ายลงในตาราง dispatch อย่างละเอียด"""
        try:
            with self._connect() as conn:
                conn.execute("""
                    INSERT INTO dispatch (
                        roll_id, pdt_code, sub_part_code, sup_code, lot_no,
                        color, width, length_dispatched, length_original, length_remaining,
                        unit, location, supplier_name, description, document_no, 
                        customer_code, customer_name, user
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    roll.roll_id, roll.code, getattr(roll, 'sub_part_code', ""), 
                    getattr(roll, 'sup_code', ""), roll.lot_no,
                    getattr(roll, 'color', ""), getattr(roll, 'width', 0.0), 
                    dispatch_length, roll.length_original, (roll.length - dispatch_length),
                    roll.unit, roll.location,
                    getattr(roll, 'supplier_name', ""), getattr(roll, 'description', ""),
                    document_no, customer_code, customer_name, user
                ))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding dispatch record: {e}")
            return False

    def get_dispatch_history(self, limit=50):
        """ดึงข้อมูลประวัติการเบิกจากตาราง dispatch"""
        try:
            with self._connect() as conn:
                cur = conn.execute(
                    "SELECT * FROM dispatch ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                )
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error getting dispatch history: {e}")
            return []

    def get_roll_active_count(self, roll_id: Optional[str] = None) -> int:
            """นับจำนวนแถวใน rolls (ทั้งหมด หรือเฉพาะ roll_id)"""
            with self._connect() as conn:
                if roll_id:
                    cur = conn.execute(
                        "SELECT COUNT(*) FROM rolls WHERE roll_id = ? AND status = 'active'",
                        (roll_id,)
                    )
                else:
                    cur = conn.execute("SELECT COUNT(*) FROM rolls WHERE status = 'active'")
                count = cur.fetchone()[0]
            return count

    
    # ----------------------------------------------------------------
    # Master Product Operations
    # ----------------------------------------------------------------
    def add_master_product(self, product: Union[MasterProduct, Dict[str, Any]]) -> bool:
        data = product.to_dict() if isinstance(product, MasterProduct) else product
        if not data.get('pdt_code'):
            return False
            
        with self._connect() as conn:
            try:
                # Dynamically build the INSERT query based on dictionary keys
                columns = ", ".join(data.keys())
                placeholders = ", ".join([f":{k}" for k in data.keys()])
                query = f"INSERT OR REPLACE INTO master_products ({columns}) VALUES ({placeholders})"
                
                conn.execute(query, data)
                conn.commit()
                return True
            except sqlite3.Error as e:
                logger.error(f"Error adding master product: {e}")
                return False

    def get_master_product(self, pdt_code: str) -> Optional[MasterProduct]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute("SELECT * FROM master_products WHERE pdt_code = ?", (pdt_code,))
            row = cur.fetchone()
        if not row:
            return None
        return MasterProduct.from_db_row(dict(row))

    def get_all_master_products(self) -> List[MasterProduct]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute("SELECT * FROM master_products")
            rows = cur.fetchall()
        return [MasterProduct.from_db_row(dict(row)) for row in rows]

    def get_master_autocomplete_data(self) -> Dict[str, List[str]]:
        """Get unique values for autocomplete from master_products table"""
        try:
            with self._connect() as conn:
                data = {}
                fields = {
                    'pdt_code': 'skus',
                    'spl_part_code': 'subpart_codes',
                    'spl_code': 'sup_codes',
                    'pdt_name': 'descriptions',
                    'spl_name': 'supplier_names'
                }
                for db_field, key in fields.items():
                    cur = conn.execute(f"SELECT DISTINCT {db_field} FROM master_products WHERE {db_field} IS NOT NULL AND {db_field} != ''")
                    data[key] = [str(row[0]) for row in cur.fetchall()]
                return data
        except Exception as e:
            logger.error(f"Error fetching master autocomplete data: {e}")
            return {}

    def get_supplier_stock_names(self) -> List[str]:
        """Get unique supplier names from supplier_stock table"""
        try:
            with self._connect() as conn:
                cur = conn.execute("SELECT DISTINCT supplier_name FROM supplier_stock WHERE supplier_name IS NOT NULL AND supplier_name != ''")
                return [str(row[0]) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching supplier stock names: {e}")
            return []

    def update_master_product(self, pdt_code: str, **updates) -> bool:
        if not updates:
            return False
        fields = ", ".join([f"{k}=?" for k in updates.keys()])
        values = list(updates.values()) + [pdt_code]
        with self._connect() as conn:
            try:
                conn.execute(f"UPDATE master_products SET {fields} WHERE pdt_code = ?", values)
                conn.commit()
                return True
            except sqlite3.Error as e:
                logger.error(f"Error updating master product: {e}")
                return False

    def delete_master_product(self, pdt_code: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM master_products WHERE pdt_code = ?", (pdt_code,))
            conn.commit()
            return cur.rowcount > 0

    def save_master_products(self):
        # No-op since SQLite auto-saves
        pass

    # ----------------------------------------------------------------
    # Logs
    # ----------------------------------------------------------------
    def add_log(self, action: str, roll_id: str, details: Dict[str, Any], user: str = "system") -> str:
        log_id = str(uuid.uuid4())
        log_entry = LogEntry(
            id=log_id,
            timestamp=datetime.now().isoformat(),
            action=action,
            roll_id=roll_id,
            details=details,
            user=user
        )
        with self._connect() as conn:
            conn.execute("""
            INSERT INTO logs (id, timestamp, action, roll_id, details, user)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (log_entry.id, log_entry.timestamp, log_entry.action,
                  log_entry.roll_id, json.dumps(log_entry.details), log_entry.user))
            conn.commit()
        return log_id

    def delete_all_logs(self) -> bool:
        """ลบ Logs ทั้งหมดออกจากฐานข้อมูล"""
        try:
            with self._connect() as conn:
                conn.execute("DELETE FROM logs")
                conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error clearing logs: {e}")
            return False

    def get_logs(self, limit: int = 100, **filters) -> List[LogEntry]:
        # Build query with SQL filters for better performance
        query = "SELECT * FROM logs"
        params = []

        if filters:
            clauses = []
            if "action" in filters:
                clauses.append("action = ?")
                params.append(filters["action"])
            if "roll_id" in filters:
                clauses.append("roll_id = ?")
                params.append(filters["roll_id"])
            if clauses:
                query += " WHERE " + " AND ".join(clauses)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self._connect() as conn:
            cur = conn.execute(query, params)
            rows = cur.fetchall()
            keys = [desc[0] for desc in cur.description]

        logs = []
        for row in rows:
            data = dict(zip(keys, row))
            data["details"] = json.loads(data["details"])
            logs.append(LogEntry(**data))

        # Only filter in Python for non-indexed fields
        remaining_filters = {k: v for k, v in filters.items() if k not in ["action", "roll_id"]}
        if remaining_filters:
            def match(log: LogEntry):
                for k, v in remaining_filters.items():
                    if getattr(log, k, None) != v and log.details.get(k) != v:
                        return False
                return True
            logs = [log for log in logs if match(log)]
        return logs

    # ----------------------------------------------------------------
    # Search Operations
    # ----------------------------------------------------------------
    def get_all_rolls(self) -> List[Roll]:
        """ดึง rolls ทั้งหมดจาก database"""
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute("SELECT * FROM rolls")
            rows = cur.fetchall()
        return [Roll.from_db_row(dict(row)) for row in rows]

    def search_rolls(self, **filters) -> List[Roll]:
        # Whitelist of allowed columns for the simplified schema
        allowed_columns = {
            'roll_id', 'code', 'sub_part_code', 'sup_code', 'supplier_name',
            'description', 'lot_no', 'quantity', 'location', 'unit',
            'color', 'width', 'length'
        }
        query = "SELECT * FROM rolls"
        clauses, params = [], []
        for k, v in filters.items():
            if k in allowed_columns:
                clauses.append(f"{k} LIKE ?")
                params.append(f"%{v}%")
        if clauses:
            query += " WHERE " + " AND ".join(clauses)

        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(query, params)
            rows = cur.fetchall()
        return [Roll.from_db_row(dict(row)) for row in rows]

    def search_rolls_by_field(self, field: str, keyword: str) -> List[Roll]:
        """ค้นหา rolls ตาม field เฉพาะ (exact match)"""
        if not keyword or not keyword.strip():
            return self.get_all_rolls()

        field_map = {
            'roll_id': 'roll_id',
            'code': 'code',
            'code': 'code',
            'lot_no': 'lot_no',
            'lot': 'lot_no',
            'location': 'location',
        }

        db_field = field_map.get(field.lower())
        if not db_field:
            return self.search_rolls(code=keyword)

        query = f"SELECT * FROM rolls WHERE {db_field} = ?"
        params = [keyword]

        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(query, params)
            rows = cur.fetchall()
        return [Roll.from_db_row(dict(row)) for row in rows]

    # ----------------------------------------------------------------
    # Statistics Operations
    # ----------------------------------------------------------------
    def get_roll_types_count(self, start_date: str = None, end_date: str = None) -> Dict[str, int]:
        query = "SELECT COALESCE(type_of_roll, 'Standard') AS type, COUNT(*) FROM rolls"
        params = []
        if start_date and end_date:
            query += " WHERE date_received >= ? AND date_received < ?"
            params = [start_date, end_date]
        query += " GROUP BY type"

        with self._connect() as conn:
            cur = conn.execute(query, params)
            data = dict(cur.fetchall())
        return data or {"Standard": 0}

    def get_roll_statuses_count(self, start_date: str = None, end_date: str = None) -> Dict[str, int]:
        query = "SELECT status, COUNT(*) FROM rolls"
        params = []
        if start_date and end_date:
            query += " WHERE date_received >= ? AND date_received < ?"
            params = [start_date, end_date]
        query += " GROUP BY status"

        with self._connect() as conn:
            cur = conn.execute(query, params)
            data = {status.capitalize(): count for status, count in cur.fetchall()}
        return data

    def get_rolls_by_date_range(self, start_date: str, end_date: str) -> List[Roll]:
        query = "SELECT * FROM rolls WHERE date_received >= ? AND date_received < ? ORDER BY date_received DESC"
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(query, (start_date, end_date))
            rows = cur.fetchall()
        return [Roll.from_db_row(dict(row)) for row in rows]

    # ----------------------------------------------------------------
    # User Operations
    # ----------------------------------------------------------------
    def add_user(self, user_data: Dict[str, Any]) -> bool:
        """Add a new user to the database"""
        with self._connect() as conn:
            try:
                conn.execute("""
                INSERT INTO users (username, password_hash, role, full_name, created_at, last_login)
                VALUES (:username, :password_hash, :role, :full_name, :created_at, :last_login)
                """, user_data)
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        with self._connect() as conn:
            cur = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cur.fetchone()
            if row:
                keys = [desc[0] for desc in cur.description]
                return dict(zip(keys, row))
        return None

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users"""
        with self._connect() as conn:
            cur = conn.execute("SELECT * FROM users")
            rows = cur.fetchall()
            keys = [desc[0] for desc in cur.description]
            return [dict(zip(keys, row)) for row in rows]

    def update_user(self, username: str, **updates) -> bool:
        """Update user data"""
        if not updates:
            return False
        allowed_columns = {'password_hash', 'role', 'full_name', 'last_login'}
        filtered_updates = {k: v for k, v in updates.items() if k in allowed_columns}
        if not filtered_updates:
            return False
        
        fields = ", ".join([f"{k}=?" for k in filtered_updates.keys()])
        values = list(filtered_updates.values()) + [username]
        with self._connect() as conn:
            conn.execute(f"UPDATE users SET {fields} WHERE username = ?", values)
            conn.commit()
        return True

    def delete_user(self, username: str) -> bool:
        """Delete user from database"""
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM users WHERE username = ?", (username,))
            conn.commit()
            return cur.rowcount > 0

    def get_total_rolls_count(self) -> int:
        """ดึงจำนวนม้วนผ้าทั้งหมดในระบบ"""
        try:
            with self._connect() as conn:
                result = conn.execute("SELECT COUNT(*) FROM rolls").fetchone()
                return result[0] if result else 0
        except Exception:
            return 0

    def get_total_master_count(self) -> int:
        """ดึงจำนวนสินค้าหลักทั้งหมดในระบบ"""
        try:
            with self._connect() as conn:
                result = conn.execute("SELECT COUNT(*) FROM master_products").fetchone()
                return result[0] if result else 0
        except Exception:
            return 0
