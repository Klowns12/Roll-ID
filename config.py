import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

class Config:
    """Application configuration manager"""
    
    # Default configuration
    _DEFAULT_CONFIG = {
        "app": {
            "name": "Fabric Roll Management System",
            "version": "1.0.0",
            "organization": "Your Company",
            "data_dir": "data",
            "log_dir": "logs"
        },
        "database": {
            "file": "fabric_rolls.db",
            "backup_dir": "backups",
            "backup_count": 5
        },
        "api": {
            "host": "0.0.0.0",
            "port": 5000,
            "debug": False,
            "secret_key": "your-secret-key-here"
        },
        "scanning": {
            "auto_scan_interval": 5,  # seconds
            "default_scanner": "builtin"
        },
        "printing": {
            "default_printer": "",
            "paper_size": "A4",
            "orientation": "portrait",
            "margin_top": 10,  # mm
            "margin_bottom": 10,
            "margin_left": 10,
            "margin_right": 10
        },
        "ui": {
            "theme": "light",
            "font_family": "Arial",
            "font_size": 10,
            "table_rows_per_page": 50
        },
        "labels": {
            "template": "default",
            "show_qr_code": True,
            "show_barcode": True,
            "qr_code_size": 40,  # mm
            "barcode_height": 15,  # mm
            "include_company_logo": False,
            "logo_path": ""
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the configuration manager
        
        Args:
            config_file: Path to a custom configuration file. If not provided,
                        looks for 'config.json' in the application directory.
        """
        self.config_file = config_file or os.path.join(os.path.dirname(__file__), 'config.json')
        self._config = self._load_config()
        self._ensure_directories()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default if not exists"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                return self._merge_configs(self._DEFAULT_CONFIG, config)
            else:
                # Create default config file
                self._save_config(self._DEFAULT_CONFIG)
                return self._DEFAULT_CONFIG
        except Exception as e:
            print(f"Error loading config: {e}")
            return self._DEFAULT_CONFIG
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def _merge_configs(self, default: Dict[str, Any], custom: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge default and custom configurations"""
        result = default.copy()
        
        for key, value in custom.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
                
        return result
    
    def _ensure_directories(self) -> None:
        """Ensure that all required directories exist"""
        # Data directory
        data_dir = self.get('app.data_dir')
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
        
        # Log directory
        log_dir = self.get('app.log_dir')
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Backup directory
        backup_dir = self.get_database_path('backup_dir')
        if backup_dir and not os.path.exists(backup_dir):
            os.makedirs(backup_dir, exist_ok=True)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by dot notation key
        
        Args:
            key: Dot-notation key (e.g., 'app.name')
            default: Default value if key not found
            
        Returns:
            The configuration value or default if not found
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value by dot notation key
        
        Args:
            key: Dot-notation key (e.g., 'app.name')
            value: Value to set
        """
        keys = key.split('.')
        config = self._config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        
        # Save the updated configuration
        self._save_config(self._config)
    
    def get_database_path(self, *args) -> str:
        """
        Get a path relative to the database directory
        
        Args:
            *args: Path components to join
            
        Returns:
            Absolute path as a string
        """
        data_dir = self.get('app.data_dir', 'data')
        db_file = self.get('database.file', 'fabric_rolls.db')
        base_path = os.path.join(data_dir, db_file)
        
        if args:
            return os.path.join(os.path.dirname(base_path), *args)
        return base_path
    
    def get_log_path(self, *args) -> str:
        """
        Get a path relative to the log directory
        
        Args:
            *args: Path components to join
            
        Returns:
            Absolute path as a string
        """
        log_dir = self.get('app.log_dir', 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        if args:
            return os.path.join(log_dir, *args)
        return log_dir
    
    def get_backup_path(self, *args) -> str:
        """
        Get a path relative to the backup directory
        
        Args:
            *args: Path components to join
            
        Returns:
            Absolute path as a string
        """
        backup_dir = self.get_database_path('backup_dir')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir, exist_ok=True)
        
        if args:
            return os.path.join(backup_dir, *args)
        return backup_dir

# Global configuration instance
config = Config()
