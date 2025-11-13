"""
Login Dialog for Fabric Roll Management System
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap, QIcon


class LoginDialog(QDialog):
    """Login dialog for user authentication"""
    
    login_successful = Signal(object)  # Emits the authenticated user
    
    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.authenticated_user = None
        self.setup_ui()
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
    
    def setup_ui(self):
        """Set up the login dialog UI"""
        self.setWindowTitle("เข้าสู่ระบบ / Login")
        self.setMinimumWidth(400)
        self.setMaximumWidth(400)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title section
        title_label = QLabel("Fabric Roll Management System")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle_label = QLabel("ระบบจัดการม้วนผ้า")
        subtitle_font = QFont()
        subtitle_font.setPointSize(10)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #666;")
        
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        layout.addSpacing(10)
        
        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)
        layout.addSpacing(10)
        
        # Login form
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)
        
        # Username field
        username_label = QLabel("ชื่อผู้ใช้ / Username:")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setMinimumHeight(35)
        self.username_input.returnPressed.connect(self.on_login)
        
        form_layout.addWidget(username_label)
        form_layout.addWidget(self.username_input)
        
        # Password field
        password_label = QLabel("รหัสผ่าน / Password:")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(35)
        self.password_input.returnPressed.connect(self.on_login)
        
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.password_input)
        
        # Show password checkbox
        self.show_password_checkbox = QCheckBox("แสดงรหัสผ่าน / Show password")
        self.show_password_checkbox.stateChanged.connect(self.toggle_password_visibility)
        form_layout.addWidget(self.show_password_checkbox)
        
        layout.addLayout(form_layout)
        layout.addSpacing(10)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.login_btn = QPushButton("เข้าสู่ระบบ / Login")
        self.login_btn.setMinimumHeight(40)
        self.login_btn.setDefault(True)
        self.login_btn.clicked.connect(self.on_login)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        
        self.cancel_btn = QPushButton("ยกเลิก / Cancel")
        self.cancel_btn.setMinimumHeight(40)
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 12pt;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        
        button_layout.addWidget(self.login_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        # Info label
        info_label = QLabel("")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("color: #999; font-size: 9pt; font-style: italic;")
        layout.addWidget(info_label)
        
        # Set focus to username input
        self.username_input.setFocus()
    
    def toggle_password_visibility(self, state):
        """Toggle password visibility"""
        if state == Qt.CheckState.Checked.value:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
    
    def on_login(self):
        """Handle login button click"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        # Validate input
        if not username:
            QMessageBox.warning(
                self,
                "ข้อมูลไม่ครบถ้วน / Incomplete Data",
                "กรุณากรอกชื่อผู้ใช้\nPlease enter username"
            )
            self.username_input.setFocus()
            return
        
        if not password:
            QMessageBox.warning(
                self,
                "ข้อมูลไม่ครบถ้วน / Incomplete Data",
                "กรุณากรอกรหัสผ่าน\nPlease enter password"
            )
            self.password_input.setFocus()
            return
        
        # Attempt authentication
        if self.auth_manager.authenticate(username, password):
            self.authenticated_user = self.auth_manager.get_current_user()
            
            # Show welcome message
            role_text = "ผู้ดูแลระบบ / Administrator" if self.authenticated_user.is_admin() else "ผู้ใช้ / User"
            QMessageBox.information(
                self,
                "เข้าสู่ระบบสำเร็จ / Login Successful",
                f"ยินดีต้อนรับ / Welcome, {self.authenticated_user.full_name}!\n"
                f"บทบาท / Role: {role_text}"
            )
            
            self.login_successful.emit(self.authenticated_user)
            self.accept()
        else:
            # Show error message
            QMessageBox.critical(
                self,
                "เข้าสู่ระบบล้มเหลว / Login Failed",
                "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง\nInvalid username or password"
            )
            self.password_input.clear()
            self.password_input.setFocus()
    
    def get_authenticated_user(self):
        """Get the authenticated user"""
        return self.authenticated_user
