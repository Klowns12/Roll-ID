from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout, QWidget, QStatusBar,
    QLabel, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QAction, QPixmap

from .tabs.dashboard_tab import DashboardTab
from .tabs.master_tab import MasterTab
from .tabs.receive_tab import ReceiveTab
from .tabs.rolls_tab import RollsTab
from .tabs.logs_tab import LogsTab

class MainWindow(QMainWindow):
    def __init__(self, storage):
        super().__init__()
        self.storage = storage
        self.setWindowTitle("Fabric Roll Management System")
        self.setMinimumSize(1024, 768)
        
        # Set window icon
        try:
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
        self.master_tab = MasterTab(self.storage)
        self.receive_tab = ReceiveTab(self.storage)
        self.rolls_tab = RollsTab(self.storage)
        self.logs_tab = LogsTab(self.storage)
        
        self.tab_widget.addTab(self.dashboard_tab, "Dashboard")
        self.tab_widget.addTab(self.master_tab, "Master Data")
        self.tab_widget.addTab(self.receive_tab, "Receive Rolls")
        self.tab_widget.addTab(self.rolls_tab, "Roll Management")
        self.tab_widget.addTab(self.logs_tab, "Logs")
        
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
