import sys
import os
import logging
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QSplashScreen
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QPixmap, QIcon, QFont, QAction

# Add the application directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import local modules
from config import config
from storage import StorageManager
from gui.main_window import MainWindow
from api_server import run_api_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(config.get_log_path(), 'app.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FabricRollApp(QApplication):
    """Main application class for Fabric Roll Management System"""
    
    def __init__(self, sys_argv):
        super().__init__(sys_argv)
        
        # Set application metadata
        self.setApplicationName(config.get('app.name', 'Fabric Roll Management System'))
        self.setApplicationVersion(config.get('app.version', '1.0.0'))
        self.setOrganizationName(config.get('app.organization', 'Your Company'))
        
        # Set application style and font
        self.setStyle('Fusion')
        font = QFont(config.get('ui.font_family', 'Arial'), 
                    config.get('ui.font_size', 10))
        self.setFont(font)
        
        # Initialize components
        self.storage = None
        self.main_window = None
        self.api_server = None
        
        # Set up cleanup on exit
        self.aboutToQuit.connect(self.cleanup)
        
        # Show splash screen
        self.splash = self.create_splash_screen()
        self.splash.show()
        
        # Initialize the application
        QTimer.singleShot(100, self.initialize)
    
    def create_splash_screen(self):
        """Create and return a splash screen"""
        # Try to load splash image
        splash_pix = QPixmap(
            os.path.join(
                os.path.dirname(__file__), 
                'static', 
                'splash.png'
            )
        )
        
        # Create a default splash screen if image not found
        if splash_pix.isNull():
            splash_pix = QPixmap(400, 300)
            splash_pix.fill(Qt.GlobalColor.white)
            
        splash = QSplashScreen(splash_pix)
        splash.setWindowFlags(
            Qt.WindowType.SplashScreen | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.FramelessWindowHint
        )
        
        return splash
    
    def initialize(self):
        """Initialize application components"""
        try:
            # Update splash screen
            self.splash.showMessage(
                "Initializing storage...",
                Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
                Qt.GlobalColor.white
            )
            self.processEvents()
            
            # Initialize storage
            self.storage = StorageManager(config.get('app.data_dir', 'data'))
            
            # Update splash screen
            self.splash.showMessage(
                "Starting API server...",
                Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
                Qt.GlobalColor.white
            )
            self.processEvents()
            
            # Start the API server
            self.api_server = run_api_server(
                host=config.get('api.host', '0.0.0.0'),
                port=config.get('api.port', 5000),
                debug=config.get('api.debug', False)
            )
            logger.info(f"API server started on {self.api_server.host}:{self.api_server.port}")
            
            # Update splash screen
            self.splash.showMessage(
                "Loading user interface...",
                Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
                Qt.GlobalColor.white
            )
            self.processEvents()
            
            # Create and show main window
            self.main_window = MainWindow(self.storage)
            self.main_window.show()
            
            # Close splash screen after a short delay
            QTimer.singleShot(1000, self.splash.close)
            
        except Exception as e:
            logger.error(f"Failed to initialize application: {str(e)}", exc_info=True)
            QMessageBox.critical(
                None,
                "Initialization Error",
                f"Failed to initialize the application:\n{str(e)}\n\n"
                "Please check the application logs for more details."
            )
            self.quit()
    
    def cleanup(self):
        """Clean up resources before application exit"""
        logger.info("Cleaning up application resources...")
        
        # Close main window
        if hasattr(self, 'main_window') and self.main_window:
            try:
                self.main_window.close()
            except Exception as e:
                logger.error(f"Error closing main window: {e}")
        
        # Stop the API server
        if hasattr(self, 'api_server') and self.api_server:
            logger.info("Stopping API server...")
            try:
                self.api_server.stop()
                logger.info("API server stopped")
            except Exception as e:
                logger.error(f"Error stopping API server: {e}")
        
        logger.info("Application cleanup complete")

    def closeEvent(self, event):
        """Handle application close event"""
        # Clean up resources
        if hasattr(self, 'api_server') and self.api_server:
            try:
                self.api_server.stop()
            except Exception as e:
                logger.error(f"Error stopping API server: {e}")
        
        # Save any pending changes
        if hasattr(self, 'storage') and self.storage:
            try:
                self.storage.save_all()
            except Exception as e:
                logger.error(f"Error saving data: {e}")
        
        event.accept()

def main():
    """Main entry point for the application"""
    try:
        # Create application instance
        app = FabricRollApp(sys.argv)
        
        # Set application icon if available
        icon_path = os.path.join(
            os.path.dirname(__file__), 
            'static', 
            'app_icon.png'
        )
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
        
        # Run the application
        sys.exit(app.exec())
        
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}", exc_info=True)
        QMessageBox.critical(
            None,
            "Fatal Error",
            f"A fatal error occurred:\n{str(e)}\n\n"
            "The application will now exit. Please check the logs for more details."
        )
        sys.exit(1)

if __name__ == "__main__":
    main()
