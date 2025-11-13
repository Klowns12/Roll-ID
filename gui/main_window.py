from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout, QHBoxLayout, QWidget, QStatusBar,
    QLabel, QPushButton, QMessageBox, QInputDialog, QTableWidgetItem
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QAction, QPixmap
import os

from .tabs.dashboard_tab import DashboardTab
from .tabs.master_tab import MasterTab
from .tabs.receive_tab import ReceiveTab
from .tabs.dispatch_tab import DispatchTab
from .tabs.rolls_tab import RollsTab
from .tabs.logs_tab import LogsTab
from .tabs.statistics_tab import StatisticsTab

class MainWindow(QMainWindow):
    def __init__(self, storage, auth_manager=None, current_user=None):
        super().__init__()
        self.storage = storage
        self.auth_manager = auth_manager
        self.current_user = current_user
        
        # Set window title with user info
        title = "Fabric Roll Management System"
        if self.current_user:
            role = "Admin" if self.current_user.is_admin() else "User"
            title += f" - {self.current_user.full_name} ({role})"
        self.setWindowTitle(title)
        self.setMinimumSize(1024, 768)
        
        # Set window icon
        try:
            # Try to load icon from fabric.png in the root directory
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "fabric.png")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
            else:
                # Fallback to resource icon
                self.setWindowIcon(QIcon(":/icons/app_icon.png"))
        except:
            pass  # Icon not found, use default
        
        self.setup_ui()
        self.setup_menu()
        self.setup_status_bar()
    
    def setup_ui(self):
        """Set up the main UI components"""
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Add tabs
        self.dashboard_tab = DashboardTab(self.storage)
        self.receive_tab = ReceiveTab(self.storage)
        self.dispatch_tab = DispatchTab(self.storage)
        self.rolls_tab = RollsTab(self.storage)
        self.logs_tab = LogsTab(self.storage)
        self.statistics_tab = StatisticsTab(self.storage)
        
        # Add common tabs
        self.tab_widget.addTab(self.dashboard_tab, "Dashboard")
        
        # Add Master Data tab only for admin users
        if self.current_user and self.current_user.is_admin():
            self.master_tab = MasterTab(self.storage)
            self.tab_widget.addTab(self.master_tab, "Master Data")
            self.tab_widget.addTab(self.receive_tab, "รับเข้า / Receive")
            self.tab_widget.addTab(self.rolls_tab, "จัดการม้วน / Rolls")
            self.tab_widget.addTab(self.dispatch_tab, "เบิกออก / Dispatch")
        else:
            self.master_tab = None
        
        # self.tab_widget.addTab(self.receive_tab, "รับเข้า / Receive")
        # self.tab_widget.addTab(self.rolls_tab, "จัดการม้วน / Rolls")
        # self.tab_widget.addTab(self.dispatch_tab, "เบิกออก / Dispatch")
        self.tab_widget.addTab(self.logs_tab, "Logs")
        self.tab_widget.addTab(self.statistics_tab, "รายงาน / Reports")
        
        layout.addWidget(self.tab_widget)
    
    def setup_menu(self):
        """Set up the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # Import action
        import_action = QAction("&Import...", self)
        import_action.setStatusTip("Import data from file")
        import_action.triggered.connect(self.import_data)
        file_menu.addAction(import_action)
        
        # Export action
        export_action = QAction("&Export...", self)
        export_action.setStatusTip("Export data to file")
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        # Settings action
        settings_action = QAction("&Settings", self)
        settings_action.setStatusTip("Application settings")
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        # User menu
        user_menu = menubar.addMenu("&User")
        
        # Change password action
        change_password_action = QAction("Change &Password", self)
        change_password_action.setStatusTip("Change your password")
        change_password_action.triggered.connect(self.change_password)
        user_menu.addAction(change_password_action)
        
        # User management action (admin only)
        if self.current_user and self.current_user.is_admin():
            manage_users_action = QAction("&Manage Users", self)
            manage_users_action.setStatusTip("Manage user accounts")
            manage_users_action.triggered.connect(self.manage_users)
            user_menu.addAction(manage_users_action)
        
        user_menu.addSeparator()
        
        # Logout action
        logout_action = QAction("&Logout", self)
        logout_action.setShortcut("Ctrl+L")
        logout_action.setStatusTip("Logout from the system")
        logout_action.triggered.connect(self.logout)
        user_menu.addAction(logout_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        # About action
        about_action = QAction("&About", self)
        about_action.setStatusTip("Show the application's About box")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_status_bar(self):
        """Set up the status bar"""
        status = QStatusBar()
        self.setStatusBar(status)
        
        # Add status label
        self.status_label = QLabel("Ready")
        status.addWidget(self.status_label, 1)
        
        # Add connection status
        self.connection_status = QLabel("Scanner: Disconnected")
        status.addPermanentWidget(self.connection_status)
    
    def update_status(self, message):
        """Update the status bar message"""
        self.status_label.setText(message)
    
    def update_connection_status(self, connected):
        """Update the scanner connection status"""
        if connected:
            self.connection_status.setText("Scanner: Connected")
            self.connection_status.setStyleSheet("color: green;")
        else:
            self.connection_status.setText("Scanner: Disconnected")
            self.connection_status.setStyleSheet("")
    
    def import_data(self):
        """Handle import data action"""
        # TODO: Implement import functionality
        QMessageBox.information(self, "Import", "Import functionality will be implemented here")
    
    def export_data(self):
        """Handle export data action"""
        # TODO: Implement export functionality
        QMessageBox.information(self, "Export", "Export functionality will be implemented here")
    
    def show_settings(self):
        """Show settings dialog"""
        # TODO: Implement settings dialog
        QMessageBox.information(self, "Settings", "Settings dialog will be implemented here")
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
        <h2>Fabric Roll Management System</h2>
        <p>Version 1.0.0</p>
        <p>A desktop application for managing fabric rolls, generating QR labels, 
        and tracking roll usage.</p>
        <p>© 2025 Your Company Name</p>
        """
        QMessageBox.about(self, "About Fabric Roll Management System", about_text)
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Ask for confirmation before closing
        reply = QMessageBox.question(
            self,
            'Confirm Exit',
            'Are you sure you want to exit?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Save any unsaved data
            self.save_settings()
            event.accept()
        else:
            event.ignore()
    
    def save_settings(self):
        """Save application settings"""
        # TODO: Implement settings save
        pass
    
    def change_password(self):
        """Show change password dialog"""
        from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("เปลี่ยนรหัสผ่าน / Change Password")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        
        old_password = QLineEdit()
        old_password.setEchoMode(QLineEdit.EchoMode.Password)
        old_password.setPlaceholderText("Enter current password")
        
        new_password = QLineEdit()
        new_password.setEchoMode(QLineEdit.EchoMode.Password)
        new_password.setPlaceholderText("Enter new password")
        
        confirm_password = QLineEdit()
        confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        confirm_password.setPlaceholderText("Confirm new password")
        
        form.addRow("รหัสผ่านเดิม / Current:", old_password)
        form.addRow("รหัสผ่านใหม่ / New:", new_password)
        form.addRow("ยืนยัน / Confirm:", confirm_password)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        layout.addLayout(form)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            old_pwd = old_password.text()
            new_pwd = new_password.text()
            confirm_pwd = confirm_password.text()
            
            if not old_pwd or not new_pwd or not confirm_pwd:
                QMessageBox.warning(self, "Error", "กรุณากรอกข้อมูลให้ครบถ้วน / Please fill all fields")
                return
            
            if new_pwd != confirm_pwd:
                QMessageBox.warning(self, "Error", "รหัสผ่านใหม่ไม่ตรงกัน / Passwords do not match")
                return
            
            if len(new_pwd) < 4:
                QMessageBox.warning(self, "Error", "รหัสผ่านต้องมีอย่างน้อย 4 ตัวอักษร / Password must be at least 4 characters")
                return
            
            if self.auth_manager and self.current_user:
                if self.auth_manager.change_password(self.current_user.username, old_pwd, new_pwd):
                    QMessageBox.information(self, "Success", "เปลี่ยนรหัสผ่านสำเร็จ / Password changed successfully")
                else:
                    QMessageBox.warning(self, "Error", "รหัสผ่านเดิมไม่ถูกต้อง / Current password is incorrect")
    
    def manage_users(self):
        """Show user management dialog (admin only)"""
        if not self.current_user or not self.current_user.is_admin():
            QMessageBox.warning(self, "Access Denied", "คุณไม่มีสิทธิ์เข้าถึง / You don't have permission")
            return
        
        from PySide6.QtWidgets import QDialog, QTableWidget, QHeaderView
        
        dialog = QDialog(self)
        dialog.setWindowTitle("จัดการผู้ใช้ / User Management")
        dialog.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        # Buttons
        btn_layout = QHBoxLayout()
        add_user_btn = QPushButton("เพิ่มผู้ใช้ / Add User")
        delete_user_btn = QPushButton("ลบผู้ใช้ / Delete User")
        reset_password_btn = QPushButton("รีเซ็ตรหัสผ่าน / Reset Password")
        
        add_user_btn.clicked.connect(lambda: self.add_new_user(dialog, user_table))
        delete_user_btn.clicked.connect(lambda: self.delete_user(user_table))
        reset_password_btn.clicked.connect(lambda: self.reset_user_password(user_table))
        
        btn_layout.addWidget(add_user_btn)
        btn_layout.addWidget(delete_user_btn)
        btn_layout.addWidget(reset_password_btn)
        btn_layout.addStretch()
        
        # User table
        user_table = QTableWidget()
        user_table.setColumnCount(4)
        user_table.setHorizontalHeaderLabels(["Username", "Full Name", "Role", "Last Login"])
        user_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        user_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        user_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        user_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Load users
        self.load_users_table(user_table)
        
        close_btn = QPushButton("ปิด / Close")
        close_btn.clicked.connect(dialog.accept)
        
        layout.addLayout(btn_layout)
        layout.addWidget(user_table)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def load_users_table(self, table):
        """Load users into the table"""
        table.setRowCount(0)
        if not self.auth_manager:
            return
        
        users = self.auth_manager.get_all_users()
        for user in users:
            row = table.rowCount()
            table.insertRow(row)
            
            table.setItem(row, 0, QTableWidgetItem(user.username))
            table.setItem(row, 1, QTableWidgetItem(user.full_name))
            table.setItem(row, 2, QTableWidgetItem(user.role))
            table.setItem(row, 3, QTableWidgetItem(user.last_login or "Never"))
    
    def add_new_user(self, parent, table):
        """Add new user dialog"""
        from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit, QComboBox, QDialogButtonBox
        
        dialog = QDialog(parent)
        dialog.setWindowTitle("เพิ่มผู้ใช้ใหม่ / Add New User")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        
        username = QLineEdit()
        username.setPlaceholderText("Username")
        
        full_name = QLineEdit()
        full_name.setPlaceholderText("Full Name")
        
        password = QLineEdit()
        password.setEchoMode(QLineEdit.EchoMode.Password)
        password.setPlaceholderText("Password")
        
        role = QComboBox()
        role.addItems(["user", "admin"])
        
        form.addRow("Username*:", username)
        form.addRow("Full Name*:", full_name)
        form.addRow("Password*:", password)
        form.addRow("Role*:", role)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        layout.addLayout(form)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            uname = username.text().strip()
            fname = full_name.text().strip()
            pwd = password.text()
            urole = role.currentText()
            
            if not uname or not fname or not pwd:
                QMessageBox.warning(parent, "Error", "กรุณากรอกข้อมูลให้ครบถ้วน / Please fill all fields")
                return
            
            if self.auth_manager.add_user(uname, pwd, urole, fname):
                QMessageBox.information(parent, "Success", "เพิ่มผู้ใช้สำเร็จ / User added successfully")
                self.load_users_table(table)
            else:
                QMessageBox.warning(parent, "Error", "ชื่อผู้ใช้นี้มีอยู่แล้ว / Username already exists")
    
    def delete_user(self, table):
        """Delete selected user"""
        selected = table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "กรุณาเลือกผู้ใช้ที่ต้องการลบ / Please select a user to delete")
            return
        
        row = selected[0].row()
        username = table.item(row, 0).text()
        
        if username == self.current_user.username:
            QMessageBox.warning(self, "Error", "ไม่สามารถลบตัวเองได้ / Cannot delete yourself")
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"คุณแน่ใจหรือไม่ที่จะลบผู้ใช้ {username}?\nAre you sure you want to delete user {username}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.auth_manager.delete_user(username):
                QMessageBox.information(self, "Success", "ลบผู้ใช้สำเร็จ / User deleted successfully")
                self.load_users_table(table)
            else:
                QMessageBox.warning(self, "Error", "ไม่สามารถลบผู้ใช้ได้ / Failed to delete user")
    
    def reset_user_password(self, table):
        """Reset password for selected user"""
        selected = table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No Selection", "กรุณาเลือกผู้ใช้ที่ต้องการรีเซ็ตรหัสผ่าน / Please select a user")
            return
        
        row = selected[0].row()
        username = table.item(row, 0).text()
        
        new_password, ok = QInputDialog.getText(
            self,
            "รีเซ็ตรหัสผ่าน / Reset Password",
            f"กรุณากรอกรหัสผ่านใหม่สำหรับ {username}:\nEnter new password for {username}:",
            QLineEdit.EchoMode.Password
        )
        
        if ok and new_password:
            if len(new_password) < 4:
                QMessageBox.warning(self, "Error", "รหัสผ่านต้องมีอย่างน้อย 4 ตัวอักษร / Password must be at least 4 characters")
                return
            
            if self.auth_manager.reset_password(username, new_password):
                QMessageBox.information(self, "Success", "รีเซ็ตรหัสผ่านสำเร็จ / Password reset successfully")
            else:
                QMessageBox.warning(self, "Error", "ไม่สามารถรีเซ็ตรหัสผ่านได้ / Failed to reset password")
    
    def logout(self):
        """Logout and close application"""
        reply = QMessageBox.question(
            self,
            'ออกจากระบบ / Logout',
            'คุณแน่ใจหรือไม่ที่จะออกจากระบบ?\nAre you sure you want to logout?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.auth_manager:
                self.auth_manager.logout()
            self.close()
            # Signal the app to show login again
            if hasattr(self.parent(), 'show_login'):
                self.parent().show_login()
