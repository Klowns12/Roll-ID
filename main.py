import sys
import os
import json
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTabWidget, QStatusBar, QMessageBox
from PySide6.QtCore import Qt, QThread, Signal as pyqtSignal
from gui.main_window import MainWindow
from storage import StorageManager
from api_server import run_api_server

class FabricRollApp(QApplication):
    def __init__(self, sys_argv):
        super().__init__(sys_argv)
        self.setApplicationName("Fabric Roll Management System")
        self.setStyle('Fusion')
        
        # Create data directory if it doesn't exist
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize storage
        self.storage = StorageManager(self.data_dir)
        
        # Start API server in a separate thread
        self.api_thread = QThread()
        self.api_worker = APIServerWorker()
        self.api_worker.moveToThread(self.api_thread)
        self.api_thread.started.connect(self.api_worker.run)
        self.api_thread.start()
        
        # Create and show main window
        self.main_window = MainWindow(self.storage)
        self.main_window.show()

class APIServerWorker(QThread):
    """Worker class to run the API server in a separate thread"""
    def __init__(self):
        super().__init__()
        
    def run(self):
        run_api_server()

def main():
    # Initialize the application
    app = FabricRollApp(sys.argv)
    
    # Set up error handling
    def handle_exception(exc_type, exc_value, exc_traceback):
        import traceback
        error_msg = "\n".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        QMessageBox.critical(
            None,
            "Unexpected Error",
            f"An unexpected error occurred:\n\n{error_msg}"
        )
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    sys.excepthook = handle_exception
    
    # Start the application event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
