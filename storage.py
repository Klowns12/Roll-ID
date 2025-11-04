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
    roll_id: str
    sku: str
    lot: str
    current_length: float
    original_length: float
    location: str
    grade: str
    marks_no: str
    date_received: str
    status: str = "active"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Roll':
        return cls(**data)

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
