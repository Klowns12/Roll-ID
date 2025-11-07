from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QComboBox, QPushButton, QMessageBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QDoubleSpinBox,
    QDateEdit, QCheckBox, QFileDialog, QInputDialog, QStyle, QDialog
)
from PySide6.QtCore import Qt, QDate, Signal as pyqtSignal, QObject
from PySide6.QtGui import QIntValidator, QDoubleValidator, QPixmap
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
import qrcode
from io import BytesIO
import json
from datetime import datetime
import tempfile
import os
import socket
import webbrowser
from PySide6.QtCore import QTimer
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import queue
import sys
import pandas as pd
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.label_generator import LabelGenerator
from storage import Roll

class MobileConnectionHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """Suppress logging messages"""
        pass
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            
            # Simple HTML page with QR scanner
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
                <title>Roll ID Scanner</title>
                <script src="https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js"></script>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 20px;
                        text-align: center;
                    }
                    #reader {
                        width: 100%;
                        max-width: 500px;
                        margin: 20px auto;
                        border: 2px solid #ccc;
                        border-radius: 8px;
                        overflow: hidden;
                    }
                    #result {
                        margin-top: 20px;
                        padding: 10px;
                        border-radius: 5px;
                    }
                    .success {
                        background-color: #dff0d8;
                        color: #3c763d;
                    }
                    .error {
                        background-color: #f2dede;
                        color: #a94442;
                    }
                    button {
                        background-color: #337ab7;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        text-align: center;
                        text-decoration: none;
                        display: inline-block;
                        font-size: 16px;
                        margin: 10px 5px;
                        cursor: pointer;
                        border-radius: 4px;
                    }
                </style>
            </head>
            <body>
                <h2>Roll ID Scanner</h2>
                <div id="camera-container" style="text-align: center;">
                    <div id="reader" style="margin: 0 auto;"></div>
                    <div style="margin: 10px 0;">
                        <button id="stopButton" style="display: none; background-color: #d9534f;">หยุดกล้อง</button>
                    </div>
                </div>
                <div id="result"></div>
                <div id="instructions" style="margin-top: 20px; padding: 10px; background-color: #f8f9fa; border-radius: 5px;">
                    <h3>คำแนะนำการใช้งาน</h3>
                    <ol>
                        <li>อนุญาตให้เว็บไซต์ใช้กล้องเมื่อมีข้อความแจ้งเตือน</li>
                        <li>นำกล้องไปที่ QR Code ที่ต้องการสแกน</li>
                        <li>ระบบจะประมวลผลข้อมูลโดยอัตโนมัติ</li>
                    </ol>
                </div>

                <script>
                    const html5QrCode = new Html5Qrcode("reader");
                    const resultContainer = document.getElementById('result');
                    const cameraContainer = document.getElementById('camera-container');
                    const stopButton = document.getElementById('stopButton');
                    let isScanning = false;
                    
                    // Show initial message
                    resultContainer.innerHTML = '<p>กำลังเริ่มต้นกล้อง กรุณารอสักครู่...</p>';

                    function onScanSuccess(decodedText, decodedResult) {
                        resultContainer.innerHTML = `
                            <p class="success">
                                <strong>Scanned:</strong> ${decodedText}
                            </p>
                            <p>Processing data...</p>
                        `;
                        
                        // Send the scanned data to the server
                        fetch('/process_scan', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ data: decodedText })
                        })
                        .then(response => response.json())
                        .then(data => {
                            resultContainer.innerHTML += `
                                <p class="success">
                                    <strong>Status:</strong> ${data.status}
                                </p>
                                <p>${data.message || ''}</p>
                            `;
                        })
                        .catch(error => {
                            resultContainer.innerHTML += `
                                <p class="error">
                                    Error: ${error.message}
                                </p>
                            `;
                        });
                    }

                    function onScanFailure(error) {
                        // Handle scan failure
                    }

                    // Start camera automatically when page loads
                    function startScanner() {
                        if (!isScanning) {
                            resultContainer.innerHTML = '<p>กำลังเริ่มต้นกล้อง กรุณาอนุญาตการเข้าถึงกล้อง...</p>';
                            
                            html5QrCode.start(
                                { 
                                    facingMode: "environment",
                                    aspectRatio: 1.0
                                },
                                {
                                    fps: 10,
                                    qrbox: { width: 200, height: 200 },
                                    disableFlip: false
                                },
                                onScanSuccess,
                                onScanFailure
                            ).then(() => {
                                isScanning = true;
                                stopButton.style.display = 'inline-block';
                                resultContainer.innerHTML = '<p class="success">กำลังสแกน... นำกล้องไปที่ QR Code</p>';
                            }).catch(err => {
                                console.error("Camera error:", err);
                                let errorMessage = 'ไม่สามารถเริ่มต้นกล้องได้';
                                
                                if (err.name === 'NotAllowedError') {
                                    errorMessage = 'กรุณาอนุญาตการเข้าถึงกล้องเพื่อใช้งานฟังก์ชันนี้';
                                } else if (err.name === 'NotFoundError') {
                                    errorMessage = 'ไม่พบกล้องในอุปกรณ์ของคุณ';
                                } else if (err.name === 'NotReadableError') {
                                    errorMessage = 'ไม่สามารถเข้าถึงกล้องได้ อาจมีแอปพลิเคชันอื่นกำลังใช้งานอยู่';
                                }
                                
                                resultContainer.innerHTML = `
                                    <p class="error">${errorMessage}</p>
                                    <button onclick="window.location.reload()" style="margin-top: 10px;">ลองอีกครั้ง</button>
                                `;
                            });
                        }
                    }
                    
                    // Start the scanner when page loads (with a small delay)
                    document.addEventListener('DOMContentLoaded', () => {
                        setTimeout(() => {
                            console.log('Page loaded, starting scanner...');
                            startScanner();
                        }, 500);
                    });

                    stopButton.addEventListener('click', () => {
                        if (isScanning) {
                            html5QrCode.stop().then(() => {
                                isScanning = false;
                                stopButton.style.display = 'none';
                                resultContainer.innerHTML = `
                                    <p>กล้องถูกปิดแล้ว</p>
                                    <button onclick="startScanner()" style="margin-top: 10px;">เปิดกล้องอีกครั้ง</button>
                                `;
                            }).catch(err => {
                                console.error("Error stopping scanner:", err);
                                resultContainer.innerHTML = `
                                    <p class="error">เกิดข้อผิดพลาดในการปิดกล้อง: ${err}</p>
                                    <button onclick="window.location.reload()" style="margin-top: 10px;">ลองอีกครั้ง</button>
                                `;
                            });
                        }
                    });
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
            
        elif self.path == '/process_scan' and self.server.request_queue is not None:
            # This will be handled by the do_POST method
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 'success',
                'message': 'Scan received and processed'
            }).encode('utf-8'))
            
        else:
            self.send_error(404, "Not Found")
    
    def do_OPTIONS(self):
        """Handle preflight OPTIONS request"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
            
    def do_POST(self):
        if self.path == '/process_scan':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    
                    # Add the scanned data to the queue for the main application
                    if hasattr(self.server, 'request_queue') and self.server.request_queue:
                        self.server.request_queue.put(data.get('data', ''))
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'status': 'success',
                        'message': 'Scan processed successfully'
                    }).encode('utf-8'))
                else:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'status': 'error',
                        'message': 'No content'
                    }).encode('utf-8'))
                
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'status': 'error',
                    'message': str(e)
                }).encode('utf-8'))
        else:
            self.send_error(404, "Not Found")

class MobileConnectionServer(QObject):
    scan_received = pyqtSignal(str)  # Signal to emit when a scan is received
    
    def __init__(self, port=8000):
        super().__init__()
        self.port = port
        self.server = None
        self.thread = None
        self.request_queue = None
    
    def start(self):
        def run():
            server_address = ('', self.port)
            self.server = HTTPServer(server_address, MobileConnectionHandler)
            # Share the request queue with the request handler
            self.server.request_queue = self.request_queue
            print(f"Starting mobile connection server on port {self.port}")
            self.server.serve_forever()
        
        # Create a queue to receive scan results
        self.request_queue = queue.Queue()
        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()
        
        # Start a timer to check for new scan results
        self.scan_timer = QTimer()
        self.scan_timer.timeout.connect(self.process_scan_results)
        self.scan_timer.start(500)  # Check every 500ms
    
    def stop(self):
        if hasattr(self, 'scan_timer') and self.scan_timer.isActive():
            self.scan_timer.stop()
            
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
    
    def process_scan_results(self):
        if not self.request_queue:
            return
            
        try:
            while True:
                # Get the next scan result without waiting
                scan_data = self.request_queue.get_nowait()
                print(f"Processing scan data: {scan_data}")
                # Emit the signal with the scanned data
                self.scan_received.emit(scan_data)
                
        except queue.Empty:
            # No more scan results in the queue
            pass

class ReceiveTab(QWidget):
    # Signal emitted when a new roll is received
    roll_received = pyqtSignal(dict)
    
    def __init__(self, storage):
        super().__init__()
        self.storage = storage
        self.mobile_server = None
        self.label_generator = LabelGenerator()
        self.setup_ui()
        self.load_master_data()
        
        # Connect signals
        self.roll_received.connect(self.on_roll_received)
        
        # Initialize mobile server
        self.init_mobile_server()
    
    def init_mobile_server(self):
        # Clean up existing server if any
        if self.mobile_server:
            try:
                self.mobile_server.stop()
                self.mobile_server.deleteLater()
            except:
                pass
        
        # Create new server
        self.mobile_server = MobileConnectionServer()
        self.mobile_server.scan_received.connect(self.on_scan_received)
        self.mobile_server.start()
    
    def closeEvent(self, event):
        # Clean up resources when the tab is closed
        if self.mobile_server:
            try:
                self.mobile_server.stop()
                self.mobile_server.deleteLater()
            except:
                pass
        super().closeEvent(event)
    
    def on_scan_received(self, scan_data):
        """Handle a QR code scan from a mobile device"""
        try:
            # Try to parse the scan data as JSON
            try:
                data = json.loads(scan_data)
                # If it's a roll data object
                if all(key in data for key in ['roll_id', 'sku', 'lot', 'length']):
                    self.roll_received.emit(data)
                    return
            except json.JSONDecodeError:
                # Not a JSON string, treat as raw data
                pass
                
            # If we get here, it's not a complete roll data object
            # Try to extract roll data from the string
            roll_data = self.extract_roll_data(scan_data)
            if roll_data:
                self.roll_received.emit(roll_data)
            else:
                QMessageBox.warning(
                    self,
                    "Invalid Scan",
                    "The scanned QR code doesn't contain valid roll data."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Scan Error",
                f"Error processing scanned data: {str(e)}"
            )
    
    def extract_roll_data(self, text):
        """Try to extract roll data from text"""
        # Try to find roll ID pattern (e.g., ROLL-1234)
        import re
        roll_id_match = re.search(r'ROLL[-_]?\d+', text, re.IGNORECASE)
        
        if not roll_id_match:
            return None
            
        # Try to extract other fields using common patterns
        sku_match = re.search(r'SKU[:\s]?([A-Z0-9-]+)', text, re.IGNORECASE)
        lot_match = re.search(r'LOT[:\s]?([A-Z0-9-]+)', text, re.IGNORECASE)
        length_match = re.search(r'LENGTH[:\s]?(\d+(?:\.\d+)?)', text, re.IGNORECASE)
        
        return {
            'roll_id': roll_id_match.group(0).upper(),
            'sku': sku_match.group(1).upper() if sku_match else 'UNKNOWN',
            'lot': lot_match.group(1).upper() if lot_match else 'UNKNOWN',
            'length': float(length_match.group(1)) if length_match else 0.0,
            'location': '',
            'grade': 'A',
            'date_received': datetime.now().strftime("%Y-%m-%d")
        }
    
    def setup_ui(self):
        """Set up the Receive tab UI"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Create tabs
        self.manual_tab = self.create_manual_tab()
        self.master_tab = self.create_master_tab()
        self.import_tab = self.create_import_tab()
        
        # Add tabs
        self.tabs.addTab(self.manual_tab, "Manual Entry")
        self.tabs.addTab(self.master_tab, "From Master")
        self.tabs.addTab(self.import_tab, "Import from File")
        
        # Add tabs to layout
        layout.addWidget(self.tabs)
    
    def create_manual_tab(self):
        """Create the manual entry tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Form group
        form_group = QGroupBox("Roll Information")
        form_layout = QFormLayout()
        
        # SKU
        self.manual_sku = QLineEdit()
        self.manual_sku.setPlaceholderText("e.g., FAB-001")
        
        # Lot
        self.manual_lot = QLineEdit()
        self.manual_lot.setPlaceholderText("e.g., LOT2023-001")
        
        # Length
        self.manual_length = QDoubleSpinBox()
        self.manual_length.setRange(0.01, 10000.0)
        self.manual_length.setValue(100.0)
        self.manual_length.setSuffix(" m")
        self.manual_length.setDecimals(2)
        
        # Width (optional)
        self.manual_width = QDoubleSpinBox()
        self.manual_width.setRange(0.0, 100.0)
        self.manual_width.setValue(1.5)
        self.manual_width.setSuffix(" m")
        self.manual_width.setDecimals(2)
        
        # Grade
        self.manual_grade = QComboBox()
        self.manual_grade.addItems(["A", "B", "C", "D"])
        
        # Location
        self.manual_location = QLineEdit()
        self.manual_location.setPlaceholderText("e.g., Warehouse A, Rack 1")
        
        # Date received
        self.manual_date = QDateEdit()
        self.manual_date.setCalendarPopup(True)
        self.manual_date.setDate(QDate.currentDate())
        
        # Notes
        self.manual_notes = QLineEdit()
        self.manual_notes.setPlaceholderText("Optional notes...")
        
        # Add mobile connection button
        self.mobile_connect_btn = QPushButton("Connect Mobile Device")
        self.mobile_connect_btn.setIcon(self.style().standardIcon(getattr(QStyle.StandardPixmap, 'SP_ComputerIcon')))
        self.mobile_connect_btn.clicked.connect(self.show_mobile_connection_dialog)
        
        # Add fields to form
        form_layout.addRow("SKU*:", self.manual_sku)
        form_layout.addRow("Lot*:", self.manual_lot)
        form_layout.addRow("Length*:", self.manual_length)
        form_layout.addRow("", self.mobile_connect_btn)
        form_layout.addRow("Width:", self.manual_width)
        form_layout.addRow("Grade:", self.manual_grade)
        form_layout.addRow("Location:", self.manual_location)
        form_layout.addRow("Date Received:", self.manual_date)
        form_layout.addRow("Notes:", self.manual_notes)
        
        form_group.setLayout(form_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.manual_clear_btn = QPushButton("Clear")
        self.manual_clear_btn.clicked.connect(self.clear_manual_form)
        
        self.manual_submit_btn = QPushButton("Save Roll")
        self.manual_submit_btn.clicked.connect(self.submit_manual_form)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.manual_clear_btn)
        btn_layout.addWidget(self.manual_submit_btn)
        
        # Add to layout
        layout.addWidget(form_group)
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        return tab
    
    def create_master_tab(self):
        """Create the 'From Master' tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Master product selection
        master_group = QGroupBox("Select Master Product")
        master_layout = QVBoxLayout()
        
        # Product filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        
        self.master_filter = QLineEdit()
        self.master_filter.setPlaceholderText("Filter by SKU or description...")
        self.master_filter.textChanged.connect(self.filter_master_products)
        
        filter_layout.addWidget(self.master_filter)
        master_layout.addLayout(filter_layout)
        
        # Master products table
        self.master_table = QTableWidget()
        self.master_table.setColumnCount(4)
        self.master_table.setHorizontalHeaderLabels(["", "SKU", "Description", "Default Length"])
        self.master_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.master_table.verticalHeader().setVisible(False)
        self.master_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.master_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.master_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        master_layout.addWidget(self.master_table)
        master_group.setLayout(master_layout)
        
        # Form for roll details
        form_group = QGroupBox("Roll Details")
        form_layout = QFormLayout()
        
        # Lot
        self.master_lot = QLineEdit()
        self.master_lot.setPlaceholderText("e.g., LOT2023-001")
        
        # Length (can override default)
        self.master_length = QDoubleSpinBox()
        self.master_length.setRange(0.01, 10000.0)
        self.master_length.setValue(100.0)
        self.master_length.setSuffix(" m")
        self.master_length.setDecimals(2)
        
        # Use default length checkbox
        self.use_default_length = QCheckBox("Use default length")
        self.use_default_length.setChecked(True)
        self.use_default_length.toggled.connect(self.toggle_use_default_length)
        
        # Location
        self.master_location = QLineEdit()
        self.master_location.setPlaceholderText("e.g., Warehouse A, Rack 1")
        
        # Date received
        self.master_date = QDateEdit()
        self.master_date.setCalendarPopup(True)
        self.master_date.setDate(QDate.currentDate())
        
        # Notes
        self.master_notes = QLineEdit()
        self.master_notes.setPlaceholderText("Optional notes...")
        
        # Add fields to form
        form_layout.addRow("Lot*:", self.master_lot)
        form_layout.addRow("Length*:", self.master_length)
        form_layout.addRow("", self.use_default_length)
        form_layout.addRow("Location:", self.master_location)
        form_layout.addRow("Date Received:", self.master_date)
        form_layout.addRow("Notes:", self.master_notes)
        
        form_group.setLayout(form_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.master_clear_btn = QPushButton("Clear")
        self.master_clear_btn.clicked.connect(self.clear_master_form)
        
        self.master_submit_btn = QPushButton("Save Roll")
        self.master_submit_btn.clicked.connect(self.submit_master_form)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.master_clear_btn)
        btn_layout.addWidget(self.master_submit_btn)
        
        # Add to layout
        layout.addWidget(master_group, 2)
        layout.addWidget(form_group, 1)
        layout.addLayout(btn_layout)
        
        return tab
    
    def create_import_tab(self):
        """Create the import from file tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Import instructions
        instructions = QLabel(
            "Import rolls from a CSV or Excel file. The file should contain the following columns:\n"
            "- sku (required): Product SKU\n"
            "- lot (required): Lot number\n"
            "- length (required): Roll length in meters\n"
            "- width (optional): Roll width in meters\n"
            "- grade (optional): Quality grade (A, B, C, etc.)\n"
            "- location (optional): Storage location\n"
            "- date_received (optional): Date in YYYY-MM-DD format\n"
            "- notes (optional): Any additional notes"
        )
        instructions.setWordWrap(True)
        
        # Import button
        self.import_btn = QPushButton("Select File to Import...")
        self.import_btn.clicked.connect(self.import_from_file)
        
        # Preview table
        self.import_table = QTableWidget()
        self.import_table.setColumnCount(8)
        self.import_table.setHorizontalHeaderLabels([
            "SKU", "Lot", "Length", "Width", "Grade", "Location", "Date", "Status"
        ])
        self.import_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.import_table.verticalHeader().setVisible(False)
        self.import_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Add to layout
        layout.addWidget(instructions)
        layout.addWidget(self.import_btn)
        layout.addWidget(self.import_table)
        
        return tab
    
    def load_master_data(self):
        """Load master products into the table"""
        self.master_products = self.storage.get_all_master_products()
        self.update_master_table()
    
    def update_master_table(self, filter_text=""):
        """Update the master products table with optional filtering"""
        self.master_table.setRowCount(0)
        
        filter_text = filter_text.lower()
        
        # Add products to table
        for product in self.master_products:
            # Skip if doesn't match filter
            if (filter_text and 
                filter_text not in product.sku.lower() and 
                filter_text not in product.description.lower()):
                continue
            
            row = self.master_table.rowCount()
            self.master_table.insertRow(row)
            
            # Add radio button
            radio_btn = QTableWidgetItem()
            radio_btn.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            radio_btn.setCheckState(Qt.CheckState.Unchecked)
            self.master_table.setItem(row, 0, radio_btn)
            
            # Add product data
            self.master_table.setItem(row, 1, QTableWidgetItem(product.sku))
            self.master_table.setItem(row, 2, QTableWidgetItem(product.description))
            self.master_table.setItem(row, 3, QTableWidgetItem(f"{product.default_length:.2f} m"))
    
    def filter_master_products(self):
        """Filter master products based on search text"""
        filter_text = self.master_filter.text()
        self.update_master_table(filter_text)
    
    def toggle_use_default_length(self, checked):
        """Enable/disable length input based on checkbox"""
        self.master_length.setEnabled(not checked)
        
        # If checked, set length to the selected product's default
        if checked and self.master_table.selectedItems():
            row = self.master_table.selectedItems()[0].row()
            sku = self.master_table.item(row, 1).text()
            product = next((p for p in self.master_products if p.sku == sku), None)
            if product:
                self.master_length.setValue(product.default_length)
    
    def clear_manual_form(self):
        """Clear the manual entry form"""
        self.manual_sku.clear()
        self.manual_lot.clear()
        self.manual_length.setValue(100.0)
        self.manual_width.setValue(1.5)
        self.manual_grade.setCurrentIndex(0)
        self.manual_location.clear()
        self.manual_date.setDate(QDate.currentDate())
        self.manual_notes.clear()
    
    def clear_master_form(self):
        """Clear the master entry form"""
        self.master_lot.clear()
        self.master_length.setValue(100.0)
        self.use_default_length.setChecked(True)
        self.master_location.clear()
        self.master_date.setDate(QDate.currentDate())
        self.master_notes.clear()
        
        # Clear selection in table
        for row in range(self.master_table.rowCount()):
            self.master_table.item(row, 0).setCheckState(Qt.CheckState.Unchecked)
    
    def submit_manual_form(self):
        """Submit the manual entry form"""
        # Validate required fields
        if not self.manual_sku.text().strip():
            QMessageBox.warning(self, "Validation Error", "SKU is required!")
            self.manual_sku.setFocus()
            return
        
        if not self.manual_lot.text().strip():
            QMessageBox.warning(self, "Validation Error", "Lot number is required!")
            self.manual_lot.setFocus()
            return
        
        # Generate roll ID (format: SKU-LOT-001)
        sku = self.manual_sku.text().strip().upper()
        lot = self.manual_lot.text().strip().upper()
        roll_id = f"{sku}-{lot}-001"  # Simple implementation - in a real app, you'd check for existing IDs
        
        # Create roll data
        roll_data = {
            'roll_id': roll_id,
            'sku': sku,
            'lot': lot,
            'length': self.manual_length.value(),
            'default_length': self.manual_length.value(),  # Add default_length
            'width': self.manual_width.value(),
            'grade': self.manual_grade.currentText(),
            'location': self.manual_location.text().strip(),
            'date_received': self.manual_date.date().toString("yyyy-MM-dd"),
            'notes': self.manual_notes.text().strip()
        }
        
        # Emit signal with roll data
        self.roll_received.emit(roll_data)
    
    def submit_master_form(self):
        """Submit the master entry form"""
        # Check if a product is selected
        selected_row = -1
        for row in range(self.master_table.rowCount()):
            if self.master_table.item(row, 0).checkState() == Qt.CheckState.Checked:
                selected_row = row
                break
        
        if selected_row == -1:
            QMessageBox.warning(self, "Validation Error", "Please select a product from the list!")
            return
        
        # Validate required fields
        if not self.master_lot.text().strip():
            QMessageBox.warning(self, "Validation Error", "Lot number is required!")
            self.master_lot.setFocus()
            return
        
        # Get selected product
        sku = self.master_table.item(selected_row, 1).text()
        product = next((p for p in self.master_products if p.sku == sku), None)
        
        if not product:
            QMessageBox.warning(self, "Error", "Selected product not found!")
            return
        
        # Generate roll ID (format: SKU-LOT-001)
        lot = self.master_lot.text().strip().upper()
        roll_id = f"{sku}-{lot}-001"  # Simple implementation - in a real app, you'd check for existing IDs
        
        # Create roll data
        length = product.default_length if self.use_default_length.isChecked() else self.master_length.value()
        roll_data = {
            'roll_id': roll_id,
            'sku': sku,
            'lot': lot,
            'length': length,
            'default_length': length,  # Add default_length
            'grade': product.default_grade,
            'location': self.master_location.text().strip(),
            'date_received': self.master_date.date().toString("yyyy-MM-dd"),
            'notes': self.master_notes.text().strip()
        }
        
        # Emit signal with roll data
        self.roll_received.emit(roll_data)
    
    def import_from_file(self):
        """Import rolls from a file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Rolls",
            "",
            "CSV Files (*.csv);;Excel Files (*.xlsx *.xls)"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            # Read file based on extension
            if file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                df = pd.read_csv(file_path)
            
            # Normalize column names (lowercase, strip whitespace)
            df.columns = df.columns.str.lower().str.strip()
            
            # Check required columns
            required_columns = ['sku', 'lot', 'length']
            available_columns = [col.lower().strip() for col in df.columns]
            missing_columns = [col for col in required_columns if col not in available_columns]
            
            if missing_columns:
                QMessageBox.critical(
                    self,
                    "Import Error",
                    f"Missing required columns: {', '.join(missing_columns)}\n\n"
                    f"Required columns: roll_id (optional), sku, lot, length\n"
                    f"Optional columns: grade, location, date_received"
                )
                return
            
            # Update preview table
            self.import_table.setRowCount(len(df))
            
            for i, row in df.iterrows():
                # Add data to table
                self.import_table.setItem(i, 0, QTableWidgetItem(str(row.get('sku', ''))))
                self.import_table.setItem(i, 1, QTableWidgetItem(str(row.get('lot', ''))))
                self.import_table.setItem(i, 2, QTableWidgetItem(str(row.get('length', ''))))
                self.import_table.setItem(i, 3, QTableWidgetItem(str(row.get('width', ''))))
                self.import_table.setItem(i, 4, QTableWidgetItem(str(row.get('grade', 'A'))))
                self.import_table.setItem(i, 5, QTableWidgetItem(str(row.get('location', ''))))
                self.import_table.setItem(i, 6, QTableWidgetItem(str(row.get('date_received', ''))))
                
                # Validate row
                is_valid = all(str(row.get(col, '')).strip() for col in required_columns)
                status = "Valid" if is_valid else "Missing required fields"
                
                status_item = QTableWidgetItem(status)
                if is_valid:
                    status_item.setForeground(Qt.GlobalColor.darkGreen)
                else:
                    status_item.setForeground(Qt.GlobalColor.red)
                
                self.import_table.setItem(i, 7, status_item)
            
            # Enable import button if there are valid rows
            valid_rows = sum(
                1 for i in range(self.import_table.rowCount())
                if self.import_table.item(i, 7).text() == "Valid"
            )
            
            if valid_rows > 0:
                if QMessageBox.question(
                    self,
                    "Import Confirmation",
                    f"Import {valid_rows} valid roll(s)?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                ) == QMessageBox.StandardButton.Yes:
                    self.process_import(df[df[required_columns].notna().all(axis=1)])
            else:
                QMessageBox.warning(
                    self,
                    "Import",
                    "No valid rows to import. Please check your file and try again."
                )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Error",
                f"An error occurred while importing the file:\n{str(e)}"
            )
    
    def process_import(self, df):
        """Process the imported data and add rolls to storage"""
        success_count = 0
        
        for idx, row in df.iterrows():
            try:
                # Get or generate roll ID
                if 'roll_id' in df.columns and str(row.get('roll_id', '')).strip():
                    roll_id = str(row['roll_id']).strip().upper()
                else:
                    # Generate roll ID (format: SKU-LOT-TIMESTAMP)
                    sku = str(row['sku']).strip().upper()
                    lot = str(row['lot']).strip().upper()
                    import time
                    timestamp = int(time.time() * 1000) % 10000
                    roll_id = f"{sku}-{lot}-{timestamp:04d}"
                
                sku = str(row['sku']).strip().upper()
                lot = str(row['lot']).strip().upper()
                
                # Create roll data
                roll_data = {
                    'roll_id': roll_id,
                    'sku': sku,
                    'lot': lot,
                    'length': float(row['length']),
                    'grade': str(row.get('grade', 'A')).upper(),
                    'location': str(row.get('location', '')).strip(),
                    'date_received': str(row.get('date_received', datetime.now().strftime("%Y-%m-%d")))
                }
                
                # Emit signal with roll data
                self.roll_received.emit(roll_data)
                success_count += 1
                
            except Exception as e:
                print(f"Error importing row {idx}: {str(e)}")
        
        # Show results
        QMessageBox.information(
            self,
            "Import Complete",
            f"Successfully imported {success_count} out of {len(df)} rolls."
        )
        
        # Clear the table
        self.import_table.setRowCount(0)
    
    def on_roll_received(self, roll_data):
        """Handle a new roll being received"""
        try:
            # Create a new roll
            roll = Roll(
                roll_id=roll_data['roll_id'],
                sku=roll_data['sku'],
                lot=roll_data['lot'],
                current_length=float(roll_data['length']),
                original_length=float(roll_data['length']),
                location=roll_data.get('location', ''),
                grade=roll_data.get('grade', 'A'),
                date_received=roll_data.get('date_received', datetime.now().strftime("%Y-%m-%d")),
                status='active'
            )
            
            # Add to storage
            if self.storage.add_roll(roll):
                # Add log entry
                self.storage.add_log(
                    action="roll_received",
                    roll_id=roll.roll_id,
                    details={
                        'sku': roll.sku,
                        'lot': roll.lot,
                        'length': roll.original_length,
                        'location': roll.location
                    }
                )
                
                # Show success message with option to print label
                reply = QMessageBox.question(
                    self,
                    "สำเร็จ / Success",
                    f"เพิ่มม้วน {roll.roll_id} สำเร็จแล้ว!\n\nต้องการพิมพ์ฉลากเลยหรือไม่?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    self.print_label(roll)
                
                # Clear the form
                if self.tabs.currentWidget() == self.manual_tab:
                    self.clear_manual_form()
                else:
                    self.clear_master_form()
                
                # Switch to the rolls tab in the main window
                main_window = self.window()
                if hasattr(main_window, 'tab_widget'):
                    main_window.tab_widget.setCurrentIndex(4)  # Updated index for rolls tab
                
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to add roll. A roll with ID {roll_data['roll_id']} may already exist."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while adding the roll:\n{str(e)}"
            )
    
    def show_mobile_connection_dialog(self):
        """Show dialog for connecting mobile devices"""
        try:
            # Get local IP address
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            
            # Create connection URL for mobile device
            # This URL will be opened directly by the QR code scanner
            connection_url = f"http://{local_ip}:8000/"
            
            # Generate QR code with direct URL
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(connection_url)
            qr.make(fit=True)
            
            # Create image
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Create dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Connect Mobile Device")
            dialog.setMinimumSize(400, 500)
            
            # Create layout
            layout = QVBoxLayout()
            
            # Add connection info
            info_text = f"""
            <h3>เชื่อมต่อมือถือ / Connect Mobile Device</h3>
            <p>สแกน QR Code นี้ด้วยกล้องมือถือ</p>
            <p>Scan this QR code with mobile camera:</p>
            <p><b>URL:</b> {connection_url}</p>
            <p><b>IP Address:</b> {local_ip}</p>
            <p><b>Port:</b> 8000</p>
            <p style="color: green;"><b>✓ ระบบพร้อม</b></p>
            """
            
            info_label = QLabel(info_text)
            info_label.setTextFormat(Qt.RichText)
            info_label.setWordWrap(True)
            layout.addWidget(info_label)
            
            # Convert QR code to pixmap
            buffer = BytesIO()
            qr_img.save(buffer, format="PNG")
            pixmap = QPixmap()
            pixmap.loadFromData(buffer.getvalue())
            
            # Add QR code to label
            qr_label = QLabel()
            qr_label.setPixmap(pixmap)
            qr_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(qr_label)
            
            # Add buttons
            btn_layout = QHBoxLayout()
            
            save_btn = QPushButton("Save QR Code")
            save_btn.clicked.connect(lambda: self.save_qr_code(qr_img))
            
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            
            btn_layout.addWidget(save_btn)
            btn_layout.addStretch()
            btn_layout.addWidget(close_btn)
            
            layout.addLayout(btn_layout)
            dialog.setLayout(layout)
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to show connection dialog: {str(e)}")
    
    def save_qr_code(self, qr_image, filename=None):
        """Save QR code to file"""
        if qr_image is None:
            return
            
        if filename is None:
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Save QR Code",
                "",
                "PNG Files (*.png);;All Files (*)"
            )
            
            if not filename:
                return
                
            if not filename.lower().endswith('.png'):
                filename += '.png'
        
        try:
            qr_image.save(filename)
            QMessageBox.information(self, "Success", f"QR code saved as {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving QR code: {str(e)}")
    
    def print_label(self, roll):
        """พิมพ์ฉลากสำหรับม้วนผ้า"""
        try:
            # ถามว่าต้องการฉลากแบบไหน
            label_types = ["ฉลากมาตรฐาน (A6)", "ฉลากขนาดเล็ก (4x3 นิ้ว)"]
            label_type, ok = QInputDialog.getItem(
                self,
                "เลือกประเภทฉลาก",
                "ประเภทฉลาก:",
                label_types,
                0,
                False
            )
            
            if not ok:
                return
            
            # สร้างข้อมูลสำหรับฉลาก
            roll_data = {
                'roll_id': roll.roll_id,
                'sku': roll.sku,
                'lot': roll.lot,
                'length': roll.current_length,
                'grade': roll.grade,
                'date_received': roll.date_received,
                'location': roll.location
            }
            
            # สร้างฉลาก
            if "เล็ก" in label_type:
                label_img = self.label_generator.create_mini_label(roll_data)
            else:
                label_img = self.label_generator.create_label(roll_data)
            
            # แปลงเป็น QPixmap
            buffer = self.label_generator.get_label_as_bytes(label_img)
            qpixmap = QPixmap()
            qpixmap.loadFromData(buffer.read())
            
            # ถามว่าต้องการพิมพ์หรือบันทึก
            reply = QMessageBox.question(
                self,
                "พิมพ์ฉลาก",
                "ต้องการพิมพ์เลยหรือบันทึกเป็นไฟล์?",
                QMessageBox.StandardButton(0x00000001) |  # Save
                QMessageBox.StandardButton(0x00000400) |  # Yes (Print)
                QMessageBox.Cancel,
                QMessageBox.StandardButton(0x00000400)
            )
            
            if reply == QMessageBox.StandardButton(0x00000400):  # Print
                self._print_pixmap(qpixmap)
            elif reply == QMessageBox.StandardButton(0x00000001):  # Save
                self._save_label_file(label_img, roll.roll_id)
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "ข้อผิดพลาด",
                f"เกิดข้อผิดพลาดในการสร้างฉลาก:\n{str(e)}"
            )
    
    def _print_pixmap(self, pixmap):
        """พิมพ์ pixmap"""
        try:
            printer = QPrinter(QPrinter.HighResolution)
            print_dialog = QPrintDialog(printer, self)
            
            if print_dialog.exec() == QDialog.Accepted:
                from PySide6.QtGui import QPainter
                painter = QPainter(printer)
                
                # คำนวณขนาดให้พอดีกับหน้ากระดาษ
                rect = painter.viewport()
                size = pixmap.size()
                size.scale(rect.size(), Qt.KeepAspectRatio)
                
                painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
                painter.setWindow(pixmap.rect())
                painter.drawPixmap(0, 0, pixmap)
                painter.end()
                
                QMessageBox.information(self, "สำเร็จ", "พิมพ์ฉลากสำเร็จ!")
        except Exception as e:
            QMessageBox.critical(
                self,
                "ข้อผิดพลาด",
                f"เกิดข้อผิดพลาดในการพิมพ์:\n{str(e)}"
            )
    
    def _save_label_file(self, image, roll_id):
        """บันทึกฉลากเป็นไฟล์"""
        try:
            default_filename = f"Label_{roll_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "บันทึกฉลาก",
                default_filename,
                "PNG Files (*.png);;PDF Files (*.pdf);;All Files (*)"
            )
            
            if filename:
                # ตรวจสอบนามสกุลไฟล์
                if filename.lower().endswith('.pdf'):
                    self.label_generator.save_label(image, filename, format='PDF')
                else:
                    if not filename.lower().endswith('.png'):
                        filename += '.png'
                    self.label_generator.save_label(image, filename, format='PNG')
                
                QMessageBox.information(
                    self,
                    "สำเร็จ",
                    f"บันทึกฉลากเป็น {filename} สำเร็จ!"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "ข้อผิดพลาด",
                f"เกิดข้อผิดพลาดในการบันทึก:\n{str(e)}"
            )
