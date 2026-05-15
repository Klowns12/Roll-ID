from PySide6.QtCore import QTimer, Signal as pyqtSignal, QObject
from http.server import HTTPServer, BaseHTTPRequestHandler

import json
import ssl
import os
import sys
import shutil
import socket
import threading
import queue
import subprocess
import glob

# Try loading bundled HTML content for production (.exe mode)
try:
    from utils.bundled_html import HTML_CONTENT
except ImportError:
    HTML_CONTENT = None


class MobileConnectionHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/":

            # ============ EVENT: ผู้ใช้เปิดหน้าเว็บ ============
            if hasattr(self.server, "client_open_queue"):
                self.server.client_open_queue.put("OPEN")
            # ====================================================

            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            if getattr(sys, 'frozen', False) and HTML_CONTENT is not None:
                # โหมด Production (รันจากไฟล์ .exe) -> โหลด HTML จาก Module ที่ฝังตัวแปร Base64 เอาไว้
                html = HTML_CONTENT
            else:
                # โหมด Development -> อ่านตรงจากไฟล์ assets/mobile_scan.html เพื่อให้เห็นการเปลี่ยนแปลงทันทีเมื่อแก้ไข
                html_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "mobile_scan.html")
                with open(html_path, "r", encoding="utf-8") as f:
                    html = f.read()

            self.wfile.write(html.encode("utf-8"))
        else:
            self.send_error(404, "Not Found")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        if self.path == "/process_scan":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(content_length)
                data = json.loads(raw.decode("utf-8"))

                if hasattr(self.server, "request_queue"):
                    self.server.request_queue.put(data.get("data", ""))

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()

                self.wfile.write(json.dumps({
                    "status": "success",
                    "message": "Scan OK"
                }).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "status": "error",
                    "message": str(e)
                }).encode("utf-8"))
        else:
            self.send_error(404, "Not Found")


class MobileConnectionServer(QObject):
    scan_received = pyqtSignal(str)
    client_opened = pyqtSignal()   # EVENT ใหม่

    def __init__(self, port=8000):
        super().__init__()

        # ใช้ IP ที่เชื่อมต่อกับ router (WiFi) แทนการใช้ hostname
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # เชื่อมต่อไปที่ Google DNS เพื่อหา IP ที่ใช้งานจริง
            s.connect(('8.8.8.8', 80))
            self.local_ip = s.getsockname()[0]
        except Exception:
            # ถ้าไม่ได้ ใช้วิธีเดิม
            hostname = socket.gethostname()
            self.local_ip = socket.gethostbyname(hostname)
        finally:
            s.close()
        
        self.port = port
        self.server = None
        self.thread = None
        self.request_queue = None
        self.client_open_queue = None
        self.url = f"https://{self.local_ip}:{self.port}"

        cert_folder = "cert"
        os.makedirs(cert_folder, exist_ok=True)
        
        # คัดลอก cgen.exe จาก bundle (ถ้าถูกแพ็คด้วย PyInstaller) ไปยังโฟลเดอร์รันไทม์เพื่อใช้สร้างใบรับรอง SSL
        local_cgen = os.path.join(cert_folder, "cgen.exe")
        if not os.path.exists(local_cgen) and getattr(sys, 'frozen', False):
            bundled_cgen = os.path.join(getattr(sys, '_MEIPASS', ''), "cert", "cgen.exe")
            if os.path.exists(bundled_cgen):
                try:
                    shutil.copy(bundled_cgen, local_cgen)
                except Exception as e:
                    print(f"Failed to copy cgen.exe from bundle: {e}")
        
        cmd = f'cgen.exe -install "{self.local_ip}"'
        subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            errors="ignore",
            cwd=cert_folder
        )

        # สแกนหาไฟล์ Certificate หลังจากรัน cgen.exe เพื่อสร้างไฟล์เสร็จเรียบร้อยแล้ว
        self._find_cert_files()

    def _find_cert_files(self):
        cert_folder = os.path.join(os.getcwd(), "cert")

        pem_files = glob.glob(os.path.join(cert_folder, "*.pem"))
        cert_files = [f for f in pem_files if not f.endswith("-key.pem")]
        key_files = glob.glob(os.path.join(cert_folder, "*-key.pem"))

        if cert_files:
            self.cert_file = cert_files[0]
        if key_files:
            self.key_file = key_files[0]

    def start(self):

        def run():
            # Bind to 0.0.0.0 เพื่อรับ connection จากทุก network interface
            httpd = HTTPServer(("0.0.0.0", self.port), MobileConnectionHandler)
            httpd.request_queue = self.request_queue
            httpd.client_open_queue = self.client_open_queue

            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(certfile=self.cert_file, keyfile=self.key_file)

            httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
            httpd.serve_forever()

        self.request_queue = queue.Queue()
        self.client_open_queue = queue.Queue()  # ใหม่

        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()

        self.scan_timer = QTimer()
        self.scan_timer.timeout.connect(self.process_queue)
        self.scan_timer.start(400)

    def stop(self):
        if hasattr(self, 'scan_timer') and self.scan_timer.isActive():
            self.scan_timer.stop()
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None

    def process_queue(self):

        # -------- Event: รับค่าที่สแกน -----------
        if self.request_queue:
            try:
                while True:
                    value = self.request_queue.get_nowait()
                    self.scan_received.emit(value)
            except queue.Empty:
                pass

        # -------- Event: ผู้ใช้เปิดเว็บ -----------
        if self.client_open_queue:
            try:
                while True:
                    _ = self.client_open_queue.get_nowait()
                    self.client_opened.emit()
            except queue.Empty:
                pass
