import os
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass, asdict
import threading
import uuid


# --------------------------------------------------------------------
# Data Models
# --------------------------------------------------------------------
@dataclass
class Roll:
    roll_id: str
    sku: str
    lot: str
    current_length: float
    original_length: float
    location: str
    grade: str
    date_received: str
    marks_no: str = ""
    status: str = "active"
    invoice_number: str = ""
    po_number: str = ""
    spl_name: str = ""
    type_of_roll: str = ""
    unit_type: str = "MTS"
    scrap_qty: float = 0.0
    specification: str = ""
    colour: str = ""
    packing_unit: str = ""
    pdt_code: str = ""
    pdt_name: str = ""
    subpart_code: str = ""
    sup_code: str = ""
    width: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MasterProduct:
    sku: str
    description: str
    default_length: float
    default_grade: str = "A"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


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
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "storage.db"
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._connect() as conn:
            cur = conn.cursor()

            # Table: Rolls
            cur.execute("""
            CREATE TABLE IF NOT EXISTS rolls (
                roll_id TEXT PRIMARY KEY,
                sku TEXT,
                lot TEXT,
                current_length REAL,
                original_length REAL,
                location TEXT,
                grade TEXT,
                date_received TEXT,
                marks_no TEXT,
                status TEXT,
                invoice_number TEXT,
                po_number TEXT,
                spl_name TEXT,
                type_of_roll TEXT,
                unit_type TEXT,
                scrap_qty REAL,
                specification TEXT,
                colour TEXT,
                packing_unit TEXT,
                pdt_code TEXT,
                pdt_name TEXT,
                subpart_code TEXT,
                sup_code TEXT,
                width TEXT
            )
            """)

            # Table: Master Products
            cur.execute("""
            CREATE TABLE IF NOT EXISTS master_products (
                sku TEXT PRIMARY KEY,
                description TEXT,
                default_length REAL,
                default_grade TEXT
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
            conn.commit()

    # ----------------------------------------------------------------
    # Roll Operations
    # ----------------------------------------------------------------
    def add_roll(self, roll: Roll) -> bool:
        print('-------- before add roll data ----------')
        print(roll)
        print('-----------------')
        with self._connect() as conn:
            cur = conn.cursor()
            try:
                cur.execute("""
                INSERT INTO rolls VALUES (
                    :roll_id, :sku, :lot, :current_length, :original_length,
                    :location, :grade, :date_received, :marks_no, :status,
                    :invoice_number, :po_number, :spl_name, :type_of_roll,
                    :unit_type, :scrap_qty, :specification, :colour, :packing_unit,
                    :pdt_code, :pdt_name, :subpart_code, :sup_code, :width
                )
                """, roll.to_dict())
                conn.commit()
            except sqlite3.IntegrityError:
                return False

        self.add_log(
            action="roll_created",
            roll_id=roll.roll_id,
            details={
                "sku": roll.sku,
                "lot": roll.lot,
                "length": roll.original_length,
                "location": roll.location,

            }
        )
        return True

    def get_roll(self, roll_id: str) -> Optional[Roll]:
        with self._connect() as conn:
            cur = conn.execute("SELECT * FROM rolls WHERE roll_id = ?", (roll_id,))
            row = cur.fetchone()
        if not row:
            return None
        keys = [desc[0] for desc in cur.description]
        return Roll(**dict(zip(keys, row)))

    def get_roll_by_id(self, roll_id: str) -> Optional[Roll]:
        return self.get_roll(roll_id)
    
    def get_roll_by_code(self, code: str) -> Optional[Roll]:
        """ค้นหาม้วนจาก Code (SKU/PDT_CODE)"""
        with self._connect() as conn:
            cur = conn.execute("SELECT * FROM rolls WHERE sku = ? OR pdt_code = ? LIMIT 1", (code, code))
            row = cur.fetchone()
            if not row:
                return None
        
        keys = [desc[0] for desc in cur.description]
        return Roll(**dict(zip(keys, row)))

    def update_roll(self, roll_id: str, **updates) -> bool:
        if not updates:
            return False
        fields = ", ".join([f"{k}=?" for k in updates.keys()])
        values = list(updates.values()) + [roll_id]
        with self._connect() as conn:
            conn.execute(f"UPDATE rolls SET {fields} WHERE roll_id = ?", values)
            conn.commit()
        return True

    def cut_roll(self, roll_id: str, cut_length: float) -> bool:
        roll = self.get_roll(roll_id)
        if not roll or cut_length <= 0 or cut_length > roll.current_length:
            return False

        roll.current_length -= cut_length
        if roll.current_length <= 0:
            roll.status = "used"

        self.update_roll(roll_id, current_length=roll.current_length, status=roll.status)

        self.add_log(
            action="roll_cut",
            roll_id=roll_id,
            details={
                "cut_length": cut_length,
                "remaining_length": roll.current_length,
                "new_status": roll.status
            }
        )
        return True

    def get_master_data_count(self) -> int:
        """นับจำนวนแถวใน master_products ทั้งหมด"""
        with self._connect() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM master_products")
            count = cur.fetchone()[0]
        return count

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
    def add_master_product(self, product: MasterProduct) -> bool:
        with self._connect() as conn:
            try:
                conn.execute("""
                INSERT INTO master_products VALUES (?, ?, ?, ?)
                """, (product.sku, product.description, product.default_length, product.default_grade))
                conn.commit()
            except sqlite3.IntegrityError:
                return False

        self.add_log("master_product_added", "", {"sku": product.sku, "description": product.description})
        return True

    def get_master_product(self, sku: str) -> Optional[MasterProduct]:
        with self._connect() as conn:
            cur = conn.execute("SELECT * FROM master_products WHERE sku = ?", (sku,))
            row = cur.fetchone()
        if not row:
            return None
        keys = [desc[0] for desc in cur.description]
        return MasterProduct(**dict(zip(keys, row)))

    def get_all_master_products(self) -> List[MasterProduct]:
        with self._connect() as conn:
            cur = conn.execute("SELECT * FROM master_products")
            rows = cur.fetchall()
        keys = [desc[0] for desc in cur.description]
        return [MasterProduct(**dict(zip(keys, row))) for row in rows]

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

    def get_logs(self, limit: int = 100, **filters) -> List[LogEntry]:
        query = "SELECT * FROM logs ORDER BY timestamp DESC LIMIT ?"
        params = [limit]

        with self._connect() as conn:
            cur = conn.execute(query, params)
            rows = cur.fetchall()
            keys = [desc[0] for desc in cur.description]

        logs = []
        for row in rows:
            data = dict(zip(keys, row))
            data["details"] = json.loads(data["details"])
            logs.append(LogEntry(**data))

        # filter in Python (optional)
        if filters:
            def match(log: LogEntry):
                for k, v in filters.items():
                    if getattr(log, k, None) != v and log.details.get(k) != v:
                        return False
                return True
            logs = [log for log in logs if match(log)]
        return logs

    # ----------------------------------------------------------------
    # Search Operations
    # ----------------------------------------------------------------
    def search_rolls(self, **filters) -> List[Roll]:
        query = "SELECT * FROM rolls"
        clauses, params = [], []
        for k, v in filters.items():
            clauses.append(f"{k} LIKE ?")
            params.append(f"%{v}%")
        if clauses:
            query += " WHERE " + " AND ".join(clauses)

        with self._connect() as conn:
            cur = conn.execute(query, params)
            rows = cur.fetchall()
            keys = [desc[0] for desc in cur.description]
        return [Roll(**dict(zip(keys, row))) for row in rows]

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

    def get_rolls_by_date_range(self, start_date: str, end_date: str) -> List[tuple]:
        query = """
        SELECT date_received, sku,
               COALESCE(type_of_roll, 'Standard'),
               current_length, status
        FROM rolls
        WHERE date_received >= ? AND date_received < ?
        ORDER BY date_received DESC
        """
        with self._connect() as conn:
            cur = conn.execute(query, (start_date, end_date))
            rows = cur.fetchall()
        return [
            (d, sku, t, f"{l:.2f}", s.capitalize())
            for d, sku, t, l, s in rows
        ]
