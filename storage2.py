import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import threading
from datetime import datetime
from dataclasses import dataclass, asdict
import uuid

@dataclass
class Roll:
    roll_id: str  # pdt_code_RollID
    sku: str  # pdt_code
    lot: str  # Lot_of_SPL
    current_length: float  # availableqty
    original_length: float  # RollQTY
    location: str  # Location
    grade: str  # grade
    date_received: str  # create_date
    marks_no: str = ""  # MARKS NO.
    status: str = "active"
    # เพิ่มฟิลด์ใหม่ตาม requirement
    invoice_number: str = ""  # Invoice_Number
    po_number: str = ""  # PO_Number
    spl_name: str = ""  # spl_name
    type_of_roll: str = ""  # TypeOfRoll
    unit_type: str = "MTS"  # unit_type
    scrap_qty: float = 0.0  # scrapqty
    specification: str = ""  # SPECIFICATION
    colour: str = ""  # COLOUR
    packing_unit: str = ""  # PACKING UNIT
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Roll':
        # สร้าง Roll object โดยใช้เฉพาะฟิลด์ที่มีใน dataclass
        valid_fields = {
            'roll_id', 'sku', 'lot', 'current_length', 'original_length',
            'location', 'grade', 'date_received', 'marks_no', 'status',
            'invoice_number', 'po_number', 'spl_name', 'type_of_roll',
            'unit_type', 'scrap_qty', 'specification', 'colour', 'packing_unit'
        }
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)

@dataclass
class MasterProduct:
    sku: str
    description: str
    default_length: float
    default_grade: str = "A"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MasterProduct':
        return cls(**data)

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
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogEntry':
        return cls(**data)

class StorageManager:
    def __init__(self, data_dir: Union[str, Path]):
        self.data_dir = Path(data_dir)
        self._lock = threading.Lock()
        
        # Initialize data files
        self.rolls_file = self.data_dir / "rolls.json"
        self.master_file = self.data_dir / "master_products.json"
        self.logs_file = self.data_dir / "logs.json"
        
        # Initialize empty data structures
        self._rolls: Dict[str, Roll] = {}
        self._master_products: Dict[str, MasterProduct] = {}
        self._logs: List[LogEntry] = []
        
        # Load existing data
        self._load_data()
    
    def _load_data(self):
        """Load data from JSON files"""
        with self._lock:
            # Load rolls
            if self.rolls_file.exists():
                with open(self.rolls_file, 'r') as f:
                    rolls_data = json.load(f)
                    self._rolls = {rid: Roll.from_dict(data) for rid, data in rolls_data.items()}
            
            # Load master products
            if self.master_file.exists():
                with open(self.master_file, 'r') as f:
                    master_data = json.load(f)
                    self._master_products = {data['sku']: MasterProduct.from_dict(data) for data in master_data}
            
            # Load logs
            if self.logs_file.exists():
                with open(self.logs_file, 'r') as f:
                    logs_data = json.load(f)
                    self._logs = [LogEntry.from_dict(entry) for entry in logs_data]
    
    def _save_rolls(self):
        """Save rolls to JSON file"""
        with self._lock:
            with open(self.rolls_file, 'w') as f:
                json.dump(
                    {rid: roll.to_dict() for rid, roll in self._rolls.items()},
                    f,
                    indent=2
                )
    
    def _save_master_products(self):
        """Save master products to JSON file"""
        with self._lock:
            with open(self.master_file, 'w') as f:
                json.dump(
                    [product.to_dict() for product in self._master_products.values()],
                    f,
                    indent=2
                )
    
    def _save_logs(self):
        """Save logs to JSON file"""
        with self._lock:
            with open(self.logs_file, 'w') as f:
                json.dump(
                    [log.to_dict() for log in self._logs],
                    f,
                    indent=2,
                    default=str
                )
    
    # Roll operations
    def add_roll(self, roll: Roll) -> bool:
        """Add a new roll to storage"""
        if roll.roll_id in self._rolls:
            return False
        
        self._rolls[roll.roll_id] = roll
        self._save_rolls()
        
        # Log the action
        self.add_log(
            action="roll_created",
            roll_id=roll.roll_id,
            details={
                "sku": roll.sku,
                "lot": roll.lot,
                "length": roll.original_length,
                "location": roll.location
            }
        )
        
        return True
    
    def get_roll(self, roll_id: str) -> Optional[Roll]:
        """Get a roll by ID"""
        return self._rolls.get(roll_id)
    
    def get_roll_by_id(self, roll_id: str) -> Optional[Roll]:
        """Get a roll by ID (alias for get_roll)"""
        return self.get_roll(roll_id)
    
    def update_roll(self, roll_id: str, **updates) -> bool:
        """Update roll attributes"""
        if roll_id not in self._rolls:
            return False
        
        roll = self._rolls[roll_id]
        for key, value in updates.items():
            if hasattr(roll, key):
                setattr(roll, key, value)
        
        self._save_rolls()
        return True
    
    def cut_roll(self, roll_id: str, cut_length: float) -> bool:
        """Cut a roll and update its length"""
        if roll_id not in self._rolls:
            return False
        
        roll = self._rolls[roll_id]
        
        if cut_length <= 0 or cut_length > roll.current_length:
            return False
        
        # Update roll length
        roll.current_length -= cut_length
        
        # If no length left, mark as used
        if roll.current_length <= 0:
            roll.status = "used"
        
        self._save_rolls()
        
        # Log the cut
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
    
    # Master product operations
    def add_master_product(self, product: MasterProduct) -> bool:
        """Add a new master product"""
        if product.sku in self._master_products:
            return False
        
        self._master_products[product.sku] = product
        self._save_master_products()
        
        self.add_log(
            action="master_product_added",
            roll_id="",
            details={"sku": product.sku, "description": product.description}
        )
        
        return True
    
    def get_master_product(self, sku: str) -> Optional[MasterProduct]:
        """Get a master product by SKU"""
        return self._master_products.get(sku)
    
    def get_all_master_products(self) -> List[MasterProduct]:
        """Get all master products"""
        return list(self._master_products.values())
    
    # Log operations
    def add_log(self, action: str, roll_id: str, details: Dict[str, Any], user: str = "system") -> str:
        """Add a new log entry"""
        log_id = str(uuid.uuid4())
        log_entry = LogEntry(
            id=log_id,
            timestamp=datetime.now().isoformat(),
            action=action,
            roll_id=roll_id,
            details=details,
            user=user
        )
        
        self._logs.append(log_entry)
        self._save_logs()
        
        return log_id
    
    def get_logs(self, limit: int = 100, **filters) -> List[LogEntry]:
        """Get logs with optional filtering"""
        logs = self._logs[-limit:]  # Get most recent logs first
        
        # Apply filters
        if filters:
            filtered_logs = []
            for log in logs:
                match = True
                for key, value in filters.items():
                    if hasattr(log, key) and getattr(log, key) != value:
                        match = False
                        break
                    elif key in log.details and log.details[key] != value:
                        match = False
                        break
                
                if match:
                    filtered_logs.append(log)
            
            return filtered_logs
        
        return logs
    
    # Search operations
    def search_rolls(self, **filters) -> List[Roll]:
        """Search rolls with optional filters"""
        results = []
        
        for roll in self._rolls.values():
            match = True
            for key, value in filters.items():
                if hasattr(roll, key):
                    attr_value = getattr(roll, key)
                    if value.lower() not in str(attr_value).lower():
                        match = False
                        break
            
            if match:
                results.append(roll)
        
        return results
    
    # Statistics operations
    def get_roll_types_count(self, start_date: str = None, end_date: str = None) -> Dict[str, int]:
        """Get count of rolls by type (based on type_of_roll field)"""
        query = "SELECT COALESCE(type_of_roll, 'Standard') AS type, COUNT(*) FROM rolls"
        params = []

        if start_date and end_date:
            query += " WHERE date_received >= ? AND date_received < ?"
            params.extend([start_date, end_date])

        query += " GROUP BY type"

        type_counts = {}

        with self._connect() as conn:
            cur = conn.execute(query, params)
            for roll_type, count in cur.fetchall():
                type_counts[roll_type] = count

        if not type_counts:
            # fallback (ในกรณีไม่มีข้อมูลเลย)
            with self._connect() as conn:
                cur = conn.execute("SELECT COUNT(*) FROM rolls")
                total = cur.fetchone()[0]
            type_counts = {"Standard": total}

        return type_counts

    def get_roll_statuses_count(self, start_date: str = None, end_date: str = None) -> Dict[str, int]:
        """Get count of rolls by status"""
        status_counts = {}
        
        for roll in self._rolls.values():
            # Filter by date if provided
            if start_date and end_date:
                if roll.date_received < start_date or roll.date_received >= end_date:
                    continue
            
            status = roll.status.capitalize()
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return status_counts
    
    def get_rolls_by_date_range(self, start_date: str, end_date: str) -> List[tuple]:
        """Get rolls within a date range for detailed table"""
        results = []
        
        for roll in self._rolls.values():
            if roll.date_received >= start_date and roll.date_received < end_date:
                results.append((
                    roll.date_received,
                    roll.sku,
                    roll.type_of_roll if roll.type_of_roll else "Standard",
                    f"{roll.current_length:.2f}",
                    roll.status.capitalize()
                ))
        
        # Sort by date
        results.sort(key=lambda x: x[0], reverse=True)
        
        return results
    
    def save_master_products(self):
        """Public method to save master products"""
        self._save_master_products()
