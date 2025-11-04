import sys
import os
import json
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt, QThread, Signal
from gui.main_window import MainWindow
from storage import StorageManager
from api_server import APIServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FabricRollApp(QApplication):
    def __init__(self, sys_argv):
        super().__init__(sys_argv)
        self.setApplicationName("Fabric Roll Management System")
        self.setStyle('Fusion')
        
        # Set up cleanup on exit
        self.aboutToQuit.connect(self.cleanup)
        
        # Create data directory if it doesn't exist
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        try:
            # Initialize storage
            self.storage = StorageManager(self.data_dir)
            logger.info("Storage initialized successfully")
            
            # Start API server
            self.start_api_server()
            
            # Create and show main window
            self.main_window = MainWindow(self.storage)
            self.main_window.show()
            
        except Exception as e:
            logger.critical(f"Failed to initialize application: {e}", exc_info=True)
            QMessageBox.critical(
                None,
                "Initialization Error",
                f"Failed to initialize application:\n{str(e)}\n\n"
                "Please check the logs for more details."
            )
            self.quit()
    
    def start_api_server(self):
        """Start the API server in a separate thread"""
        try:
            # Start API server with default settings
            self.api_server = APIServer(
                host='0.0.0.0',
                port=5000,
                debug=False
            )
            # Run in a separate thread
            self.api_server.run_in_thread()
            logger.info(f"API server started on {self.api_server.host}:{self.api_server.port}")
            
        except Exception as e:
            logger.error(f"Failed to start API server: {e}")
            raise
    
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

def handle_exception(exc_type, exc_value, exc_traceback):
    """Handle uncaught exceptions"""
    import traceback
    error_msg = "\n".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logger.critical(f"Unhandled exception: {error_msg}")
    QMessageBox.critical(
        None,
        "Unhandled Exception",
        f"An unhandled exception occurred:\n\n{str(exc_value)}\n\n"
        "Please check the logs for more details."
    )

def main():
    # Set up global exception handling
    import sys
    sys.excepthook = handle_exception
    
    try:
        # Initialize the application
        app = FabricRollApp(sys.argv)
        
        # Run the application
        sys.exit(app.exec())
        
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        QMessageBox.critical(
            None,
            "Fatal Error",
            f"A fatal error occurred:\n{str(e)}\n\n"
            "The application will now exit. Please check the logs for more details."
        )
        sys.exit(1)

if __name__ == "__main__":
    main()
