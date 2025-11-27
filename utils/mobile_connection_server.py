from PySide6.QtCore import QTimer, Signal as pyqtSignal, QObject
from http.server import HTTPServer, BaseHTTPRequestHandler

import json
import ssl
import os
import socket
import threading
import queue
import subprocess
import glob


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

            html_path = os.path.join(os.getcwd(), "utils", "mobile_scan.html")
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

        self._find_cert_files()

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
        
        print(f"Detected IP Address: {self.local_ip}")

        cert_folder = "cert"
        os.makedirs(cert_folder, exist_ok=True)

        cmd = f'cgen.exe -install "{self.local_ip}"'
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            errors="ignore",
            cwd=cert_folder
        )

        print(result.stdout)
        print(result.stderr)

    def _find_cert_files(self):
        cert_folder = os.path.join(os.getcwd(), "cert")

        pem_files = glob.glob(os.path.join(cert_folder, "*.pem"))
        cert_files = [f for f in pem_files if not f.endswith("-key.pem")]
        key_files = glob.glob(os.path.join(cert_folder, "*-key.pem"))

        if cert_files:
            self.cert_file = cert_files[0]
        else:
            print(f"ไม่พบไฟล์ใบรับรอง (.pem) ในโฟลเดอร์: {cert_folder}")

        if key_files:
            self.key_file = key_files[0]
        else:
            print(f"ไม่พบไฟล์คีย์ (-key.pem) ในโฟลเดอร์: {cert_folder}")

        if hasattr(self, "cert_file") and hasattr(self, "key_file"):
            print(f"พบไฟล์ใบรับรอง: {os.path.basename(self.cert_file)}")
            print(f"พบไฟล์คีย์: {os.path.basename(self.key_file)}")

    def start(self):

        def run():
            print(">> Creating HTTPServer...")
            # Bind to 0.0.0.0 เพื่อรับ connection จากทุก network interface
            httpd = HTTPServer(("0.0.0.0", self.port), MobileConnectionHandler)
            httpd.request_queue = self.request_queue
            httpd.client_open_queue = self.client_open_queue

            print(">> Creating SSLContext...")
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(certfile=self.cert_file, keyfile=self.key_file)

            print(">> Wrapping socket with SSLContext...")
            httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

            print(f"HTTPS server running at https://{self.local_ip}:{self.port}")
            print(f"Server is listening on all network interfaces (0.0.0.0:{self.port})")
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
                    print("SCAN =", value)
                    self.scan_received.emit(value)
            except queue.Empty:
                pass

        # -------- Event: ผู้ใช้เปิดเว็บ -----------
        if self.client_open_queue:
            try:
                while True:
                    _ = self.client_open_queue.get_nowait()
                    print("CLIENT OPENED")
                    self.client_opened.emit()
            except queue.Empty:
                pass
