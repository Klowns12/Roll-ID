from flask import Flask, request, jsonify, has_request_context
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import threading
import logging
import json
import atexit
from datetime import datetime
from typing import Dict, Any, Optional, Callable

# Global variable to store cleanup function
_cleanup_handlers = []

def register_cleanup(handler: Callable[[], None]) -> None:
    """Register a cleanup handler to be called on exit"""
    _cleanup_handlers.append(handler)

def cleanup() -> None:
    """Execute all registered cleanup handlers"""
    for handler in _cleanup_handlers:
        try:
            handler()
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")

# Register cleanup with atexit
atexit.register(cleanup)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIServer:
    def __init__(self, host: str = '0.0.0.0', port: int = 5005, debug: bool = False):
        self.host = host
        self.port = port
        self.debug = debug
        self._running = False
        self._thread = None
        
        # Initialize Flask and SocketIO
        self.app = Flask(__name__)
        self.socketio = SocketIO(
            self.app,
            cors_allowed_origins="*",
            async_mode='threading',
            logger=debug,
            engineio_logger=debug
        )
        CORS(self.app)
        
        # Store connected clients
        self.clients = set()
        
        # Setup routes
        self.setup_routes()
        
        # Setup socket events
        self.setup_socket_events()
        
        # Register cleanup
        register_cleanup(self.stop)
    
    def setup_routes(self):
        """Set up the API routes"""
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'ok',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0'
            })
        
        @self.app.route('/api/scan', methods=['POST'])
        def handle_scan():
            """Handle barcode/QR code scans from mobile devices"""
            data = request.get_json()
            if not data or 'code' not in data:
                return jsonify({'error': 'No code provided'}), 400
            
            logger.info(f"Received scan: {data['code']}")
            
            # Emit socket event for real-time updates
            self.socketio.emit('scan_received', {
                'code': data['code'],
                'timestamp': datetime.now().isoformat(),
                'device': request.remote_addr
            })
            
            return jsonify({
                'status': 'success',
                'message': 'Scan received',
                'code': data['code'],
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/rolls/<roll_id>', methods=['GET'])
        def get_roll(roll_id: str):
            """Get roll information by ID"""
            # This is a placeholder - in a real app, you would fetch from your storage
            return jsonify({
                'status': 'success',
                'roll': {
                    'id': roll_id,
                    'sku': 'SKU-' + roll_id.split('-')[0],
                    'lot': 'LOT-' + roll_id.split('-')[1],
                    'length': 100.0,
                    'location': 'Warehouse A',
                    'status': 'active'
                }
            })
    
    def setup_socket_events(self):
        """Set up Socket.IO event handlers"""
        @self.socketio.on('connect')
        def handle_connect():
            """Handle new client connections"""
            self.clients.add(request.sid)
            logger.info(f"Client connected: {request.sid}")
            emit('connection_response', {'data': 'Connected to scanner server'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnections"""
            if request.sid in self.clients:
                self.clients.remove(request.sid)
            logger.info(f"Client disconnected: {request.sid}")
        
        @self.socketio.on('scan')
        def handle_scan_event(data):
            """Handle scan events from the web interface"""
            logger.info(f"Received scan event: {data}")
            # Broadcast to all connected clients
            emit('scan_update', data, broadcast=True)
    
    def run(self):
        """Run the API server"""
        if self._running:
            logger.warning("API server is already running")
            return
            
        self._running = True
        logger.info(f"Starting API server on {self.host}:{self.port}")
        try:
            self.socketio.run(
                self.app,
                host=self.host,
                port=self.port,
                debug=self.debug,
                use_reloader=False
            )
        except Exception as e:
            logger.error(f"API server error: {e}")
            raise
        finally:
            self._running = False

    def run_in_thread(self):
        """Run the API server in a separate thread"""
        if self._thread and self._thread.is_alive():
            logger.warning("API server thread is already running")
            return self._thread
            
        self._thread = threading.Thread(
            target=self.run,
            name="API-Server-Thread",
            daemon=True
        )
        self._thread.start()
        return self._thread

    def stop(self):
        """Stop the API server safely (no request context error)"""
        if not self._running:
            return

        logger.info("Stopping API server...")
        try:
            # ตรวจสอบก่อนว่ามี request context หรือไม่
            if has_request_context():
                self.socketio.stop()
            else:
                # ไม่มี request context ก็ไม่ต้องเรียก stop ผ่าน Flask
                logger.info("No active request context; skipping Flask shutdown.")
            logger.info("API server stopped")
        except Exception as e:
            logger.warning(f"Error stopping API server (safe mode): {e}")
        finally:
            self._running = False


