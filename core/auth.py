"""
Authentication Module for Fabric Roll Management System
Handles user authentication, role management, and password hashing using SQLite storage
"""

import hashlib
import logging
from datetime import datetime
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

class User:
    """User class representing a system user"""
    def __init__(self, username: str, password_hash: str, role: str, full_name: str = ""):
        self.username = username
        self.password_hash = password_hash
        self.role = role  # 'admin' or 'user'
        self.full_name = full_name or username
        self.created_at = datetime.now().isoformat()
        self.last_login = None
    
    def to_dict(self) -> Dict:
        """Convert user object to dictionary"""
        return {
            'username': self.username,
            'password_hash': self.password_hash,
            'role': self.role,
            'full_name': self.full_name,
            'created_at': self.created_at,
            'last_login': self.last_login
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'User':
        """Create user object from dictionary"""
        user = User(
            username=data['username'],
            password_hash=data['password_hash'],
            role=data['role'],
            full_name=data.get('full_name', data['username'])
        )
        user.created_at = data.get('created_at', datetime.now().isoformat())
        user.last_login = data.get('last_login')
        return user
    
    def is_admin(self) -> bool:
        """Check if user has admin role"""
        return self.role == 'admin'


class AuthManager:
    """Authentication Manager for handling user authentication and management via StorageManager"""
    
    def __init__(self, storage_manager):
        self.storage = storage_manager
        self.current_user: Optional[User] = None
        
        # Create default admin user if no users exist in database
        if not self.storage.get_all_users():
            self.create_default_admin()
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_default_admin(self):
        """Create default admin user"""
        admin_data = {
            'username': 'admin',
            'password_hash': self._hash_password('admin'),
            'role': 'admin',
            'full_name': 'Administrator',
            'created_at': datetime.now().isoformat(),
            'last_login': None
        }
        self.storage.add_user(admin_data)
        logger.warning("Default admin user created in database: username='admin', password='admin'")
    
    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate user with username and password"""
        user_data = self.storage.get_user(username)
        if user_data and user_data['password_hash'] == self._hash_password(password):
            user = User.from_dict(user_data)
            self.current_user = user
            # Update last login
            last_login = datetime.now().isoformat()
            self.storage.update_user(username, last_login=last_login)
            user.last_login = last_login
            return True
        return False
    
    def logout(self):
        """Logout current user"""
        self.current_user = None
    
    def get_current_user(self) -> Optional[User]:
        """Get currently logged in user"""
        return self.current_user
    
    def is_logged_in(self) -> bool:
        """Check if a user is currently logged in"""
        return self.current_user is not None
    
    def is_admin(self) -> bool:
        """Check if current user is admin"""
        return self.current_user and self.current_user.is_admin()
    
    def add_user(self, username: str, password: str, role: str, full_name: str = "") -> bool:
        """Add a new user (admin only)"""
        user_data = {
            'username': username,
            'password_hash': self._hash_password(password),
            'role': role,
            'full_name': full_name or username,
            'created_at': datetime.now().isoformat(),
            'last_login': None
        }
        return self.storage.add_user(user_data)
    
    def delete_user(self, username: str) -> bool:
        """Delete a user (admin only, cannot delete self)"""
        if self.current_user and self.current_user.username == username:
            return False  # Cannot delete self
        
        return self.storage.delete_user(username)
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        user_data = self.storage.get_user(username)
        if not user_data:
            return False
        
        # Verify old password
        if user_data['password_hash'] != self._hash_password(old_password):
            return False
        
        # Set new password
        return self.storage.update_user(username, password_hash=self._hash_password(new_password))
    
    def reset_password(self, username: str, new_password: str) -> bool:
        """Reset user password (admin only)"""
        return self.storage.update_user(username, password_hash=self._hash_password(new_password))
    
    def get_user(self, username: str) -> Optional[User]:
        """Get user by username"""
        user_data = self.storage.get_user(username)
        if user_data:
            return User.from_dict(user_data)
        return None
    
    def get_all_users(self) -> List[User]:
        """Get all users (admin only)"""
        users_data = self.storage.get_all_users()
        return [User.from_dict(data) for data in users_data]
    
    def update_user_role(self, username: str, new_role: str) -> bool:
        """Update user role (admin only)"""
        return self.storage.update_user(username, role=new_role)
