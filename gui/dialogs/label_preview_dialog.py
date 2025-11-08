"""
Label Preview Dialog
แสดง preview ของฉลาก QR Code ก่อนสั่งปริ้น
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox, QScrollArea, QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from io import BytesIO
from utils.label_generator import LabelGenerator


class LabelPreviewDialog(QDialog):
    """Dialog to preview and print roll labels"""
    
    def __init__(self, parent, roll_data, mini=True):
        super().__init__(parent)
        self.roll_data = roll_data
        self.label_image = None
        self.generator = LabelGenerator()  # ใช้ LabelGenerator
        self.setWindowTitle(f"Label Preview - {roll_data['roll_id']}")
        self.setGeometry(100, 100, 800, 600)
        self.setup_ui()
        self.generate_label()
    
    def setup_ui(self):
        """Set up the dialog UI"""
        layout = QVBoxLayout()

        # Title
        title = QLabel(f"Preview: {self.roll_data['roll_id']}")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Label preview area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("background-color: white; padding: 10px;")
        scroll.setWidget(self.preview_label)
        
        layout.addWidget(scroll)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.print_btn = QPushButton("Print Label")
        self.print_btn.clicked.connect(self.print_label)
        btn_layout.addWidget(self.print_btn)
        
        self.save_btn = QPushButton("Save as Image")
        self.save_btn.clicked.connect(self.save_label)
        btn_layout.addWidget(self.save_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def generate_label(self):
        """Generate label using LabelGenerator"""
        try:
            self.label_image = self.generator.create_label(self.roll_data)
            
            self.display_preview()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error generating label: {str(e)}")
    
    def display_preview(self):
        """Display the label image in the preview"""
        if self.label_image:
            # Convert PIL image to QPixmap
            buffer = BytesIO()
            self.label_image.save(buffer, format='PNG')
            buffer.seek(0)
            
            pixmap = QPixmap()
            pixmap.loadFromData(buffer.getvalue())
            
            # Scale for display (สูงสุด 600px)
            scaled_pixmap = pixmap.scaledToWidth(600, Qt.SmoothTransformation)
            self.preview_label.setPixmap(scaled_pixmap)
    
    def print_label(self):
        """Print the label"""
        try:
            from PySide6.QtPrintSupport import QPrinter, QPrintDialog
            from PySide6.QtGui import QPainter
            
            printer = QPrinter(QPrinter.HighResolution)
            dialog = QPrintDialog(printer, self)
            
            if dialog.exec() == QDialog.Accepted:
                painter = QPainter()
                painter.begin(printer)
                
                # Draw the label image
                if self.label_image:
                    buffer = BytesIO()
                    self.label_image.save(buffer, format='PNG')
                    buffer.seek(0)
                    
                    pixmap = QPixmap()
                    pixmap.loadFromData(buffer.getvalue())
                    
                    # Draw on printer
                    painter.drawPixmap(0, 0, pixmap)
                
                painter.end()
                QMessageBox.information(self, "Success", "Label sent to printer!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Print error: {str(e)}")
    
    def save_label(self):
        """Save label as image"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Label",
                f"{self.roll_data['roll_id']}_label.png",
                "PNG Image (*.png);;JPEG Image (*.jpg)"
            )
            
            if file_path and self.label_image:
                self.label_image.save(file_path, dpi=(300, 300))
                QMessageBox.information(self, "Success", f"Label saved to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Save error: {str(e)}")
