import sys
import os
import json
import logging
import socket
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt, QThread, Signal, QLocale
from PySide6.QtGui import QIcon
from gui.main_window import MainWindow
from gui.dialogs.login_dialog import LoginDialog
from core.storage import StorageManager
from core.api_server import APIServer
from core.auth import AuthManager

# Silence Werkzeug (Flask) logging
logging.getLogger('werkzeug').setLevel(logging.ERROR)

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
        
        # Set application icon
        try:
            icon_path = os.path.join(os.path.dirname(__file__),"assets", "fabric.png")
            if os.path.exists(icon_path):
                # Note: setApplicationIcon is not available in PySide6, icon will be set on main window
                logger.info(f"Application icon path: {icon_path}")
        except Exception as e:
            logger.warning(f"Failed to load application icon: {e}")
        
        # Set up cleanup on exit
        self.aboutToQuit.connect(self.cleanup)
        
        # Create data directory if it doesn't exist
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Collect status for summary
        self.status_summary = []
        
        # 0. Environment Info
        import platform
        import getpass
        self.status_summary.append(("Environment", "OK", f"{platform.system()} {platform.release()} (User: {getpass.getuser()})"))
        
        try:
            # 1. Assets Check
            icon_path = os.path.join(os.path.dirname(__file__),"assets", "fabric.png")
            if os.path.exists(icon_path):
                self.status_summary.append(("Assets", "OK", "Icon & UI assets found"))
            else:
                self.status_summary.append(("Assets", "WARN", "Icon missing"))

            # 2. Storage & Database Stats
            self.storage = StorageManager(os.path.join(os.getcwd(), "data"))
            roll_count = self.storage.get_total_rolls_count()
            master_count = self.storage.get_total_master_count()
            self.status_summary.append(("Database", "OK", f"{roll_count} Rolls, {master_count} Products loaded"))

            # 3. Authentication
            self.auth_manager = AuthManager(self.storage)
            self.status_summary.append(("Auth Manager", "OK", "Security system ready"))
            
            # 4. Network Info
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(('8.8.8.8', 80))
                local_ip = s.getsockname()[0]
            except Exception:
                local_ip = "127.0.0.1"
            finally:
                s.close()
            self.status_summary.append(("Network", "OK", f"Local IP: {local_ip}"))

            # 5. API Server
            try:
                self.start_api_server()
                self.status_summary.append(("API Server", "OK", f"http://{self.api_server.host}:{self.api_server.port}"))
            except Exception as e:
                self.status_summary.append(("API Server", "FAIL", f"Failed to start API Server: {str(e)}"))
            
            # 6. Mobile Server (URL Info)
            from utils.mobile_connection_server import MobileConnectionServer
            try:
                self.mobile_server = MobileConnectionServer()
                if not hasattr(self.mobile_server, 'cert_file') or not hasattr(self.mobile_server, 'key_file'):
                    raise Exception("SSL Certificate files (.pem) not found. Please check cgen.exe in cert folder.")
                self.mobile_server.start()
                mobile_url = f"https://{local_ip}:8000"
                self.status_summary.append(("Mobile Server", "OK", f"Listening at {mobile_url}"))
            except Exception as e:
                self.mobile_server = None
                self.status_summary.append(("Mobile Server", "WARN", f"Failed to start Mobile Server: {str(e)}"))
            
            # Print Summary before showing window
            self.print_system_summary()
            
            # ตรวจสอบว่าระบบใดใช้งานไม่ได้ (WARN หรือ FAIL) แล้วแจ้งเตือนผู้ใช้งานแบบเด้งป๊อปอัป
            failed_systems = [f"• {item}: {detail}" for item, status, detail in self.status_summary if status in ("WARN", "FAIL")]
            if failed_systems:
                warning_message = (
                    "⚠️ ระบบตรวจพบข้อผิดพลาดหรือคำเตือนบางประการ:\n\n"
                    + "\n".join(failed_systems) + "\n\n"
                    "ระบบบางฟังก์ชันอาจไม่สามารถใช้งานได้ (เช่น ระบบสแกนด้วยกล้องมือถือหาก Mobile Server มีปัญหา)"
                )
                QMessageBox.warning(None, "รายงานสถานะระบบ / System Status Report", warning_message)
            
            # Show main window without login
            self.main_window = None
            self.show_main_window_without_login()
            
        except Exception as e:
            logger.critical(f"Failed to initialize application: {e}")
            self.status_summary.append(("System", "FAIL", str(e)))
            self.print_system_summary()
            QMessageBox.critical(None, "Error", f"Failed to initialize application:\n{str(e)}")
            self.quit()

    def print_system_summary(self):
        """แสดงตารางสรุปสถานะการเริ่มต้นระบบแบบสะอาดตา"""
        print("\n" + "="*60)
        print("      Fabric Roll Management System - Startup Summary")
        print("="*60)
        for item, status, detail in self.status_summary:
            print(f" [{status}] {item:<15} : {detail}")
        print("="*60)
        print(" Status: System Ready\n")
    
    def show_main_window_without_login(self):
        """Show main window without login (Reports tab visible first)"""
        try:
            logger.info("Showing main window without login")
            
            # Create and show main window without authenticated user
            if self.main_window:
                self.main_window.close()
            
            self.main_window = MainWindow(
                self.storage, 
                self.auth_manager, 
                current_user=None,
                app=self
            )
            self.main_window.show()
            
        except Exception as e:
            logger.error(f"Error in show_main_window_without_login: {e}")
            self.quit()
    
    def show_login_dialog(self):
        """Show login dialog from main window"""
        login_dialog = LoginDialog(self.auth_manager)
        
        if login_dialog.exec() == LoginDialog.DialogCode.Accepted:
            authenticated_user = login_dialog.get_authenticated_user()
            if authenticated_user:
                logger.info(f"User {authenticated_user.username} logged in successfully")
                
                # Update main window with authenticated user
                if self.main_window:
                    self.main_window.set_current_user(authenticated_user)
            else:
                logger.info("Login failed")
        else:
            logger.info("Login cancelled by user")
    
    def show_login(self):
        """Show login dialog"""
        login_dialog = LoginDialog(self.auth_manager)
        
        if login_dialog.exec() == LoginDialog.DialogCode.Accepted:
            authenticated_user = login_dialog.get_authenticated_user()
            if authenticated_user:
                logger.info(f"User {authenticated_user.username} logged in successfully")
                
                # Create and show main window with authenticated user
                if self.main_window:
                    self.main_window.close()
                
                self.main_window = MainWindow(
                    self.storage, 
                    self.auth_manager, 
                    authenticated_user
                )
                self.main_window.show()
            else:
                self.quit()
        else:
            # User cancelled login
            logger.info("Login cancelled by user")
            self.quit()
    
    def is_port_available(self, host: str, port: int) -> bool:
        """Check if a port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex((host, port))
                return result != 0  # Port is available if connection fails
        except Exception:
            return False

    def start_api_server(self):
        """Start the API server in a separate thread"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            host = os.getenv("API_HOST", "0.0.0.0")
            env_port = os.getenv("API_PORT")
            
            if env_port:
                available_port = int(env_port)
            else:
                ports_to_try = [5000, 5001, 5002, 5003, 5004]
                available_port = None
                for port in ports_to_try:
                    if self.is_port_available(host, port):
                        available_port = port
                        break
                if not available_port:
                    logger.warning("No available ports found in range 5000-5004, using 5000 anyway")
                    available_port = 5000

            debug_mode = os.getenv("API_DEBUG", "False").lower() in ("true", "1", "t")

            # Start API server with available port
            self.api_server = APIServer(
                host=host,
                port=available_port,
                debug=debug_mode
            )
            # Run in a separate thread
            self.api_server.run_in_thread()
            # Status will be updated in the main summary

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
        # บังคับให้ใช้ตัวเลขแบบสากล (แก้ปัญหาเลขไทย)
        QLocale.setDefault(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))
        
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
