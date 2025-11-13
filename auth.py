"""
Authentication Module for Fabric Roll Management System
Handles user authentication, role management, and password hashing
"""

import json
import hashlib
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

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
    """Authentication Manager for handling user authentication and management"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.users_file = self.data_dir / "users.json"
        self.users: Dict[str, User] = {}
        self.current_user: Optional[User] = None
        self.load_users()
        
        # Create default admin user if no users exist
        if not self.users:
            self.create_default_admin()
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def load_users(self):
        """Load users from JSON file"""
        if self.users_file.exists():
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.users = {
                        username: User.from_dict(user_data)
                        for username, user_data in data.items()
                    }
            except Exception as e:
                print(f"Error loading users: {e}")
                self.users = {}
    
    def save_users(self):
        """Save users to JSON file"""
        try:
            data = {
                username: user.to_dict()
                for username, user in self.users.items()
            }
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving users: {e}")
    
    def create_default_admin(self):
        """Create default admin user"""
        admin_user = User(
            username='admin',
            password_hash=self._hash_password('admin'),
            role='admin',
            full_name='Administrator'
        )
        self.users['admin'] = admin_user
        self.save_users()
        print("Default admin user created: username='admin', password='admin'")
    
    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate user with username and password"""
        user = self.users.get(username)
        if user and user.password_hash == self._hash_password(password):
            self.current_user = user
            user.last_login = datetime.now().isoformat()
            self.save_users()
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
        if username in self.users:
            return False
        
        user = User(
            username=username,
            password_hash=self._hash_password(password),
            role=role,
            full_name=full_name or username
        )
        self.users[username] = user
        self.save_users()
        return True
    
    def delete_user(self, username: str) -> bool:
        """Delete a user (admin only, cannot delete self)"""
        if username not in self.users:
            return False
        if self.current_user and self.current_user.username == username:
            return False  # Cannot delete self
        
        del self.users[username]
        self.save_users()
        return True
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        user = self.users.get(username)
        if not user:
            return False
        
        # Verify old password
        if user.password_hash != self._hash_password(old_password):
            return False
        
        # Set new password
        user.password_hash = self._hash_password(new_password)
        self.save_users()
        return True
    
    def reset_password(self, username: str, new_password: str) -> bool:
        """Reset user password (admin only)"""
        user = self.users.get(username)
        if not user:
            return False
        
        user.password_hash = self._hash_password(new_password)
        self.save_users()
        return True
    
    def get_all_users(self) -> List[User]:
        """Get all users (admin only)"""
        return list(self.users.values())
    
    def update_user_role(self, username: str, new_role: str) -> bool:
        """Update user role (admin only)"""
        user = self.users.get(username)
        if not user:
            return False
        
        user.role = new_role
        self.save_users()
        return True
