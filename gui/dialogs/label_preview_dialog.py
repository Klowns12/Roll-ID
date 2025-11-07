"""
Label Preview Dialog
แสดง preview ของฉลาก QR Code ก่อนสั่งปริ้น
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox, QScrollArea
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QImage
from PIL import Image, ImageDraw, ImageFont
import qrcode
from io import BytesIO


class LabelPreviewDialog(QDialog):
    """Dialog to preview and print roll labels"""
    
    def __init__(self, parent, roll_data):
        super().__init__(parent)
        self.roll_data = roll_data
        self.label_image = None
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
        """Generate label image"""
        try:
            # Create label image (A6 size: 105x148mm at 300 DPI = 1240x1748 pixels)
            # But we'll scale it down for preview
            label_width = 620
            label_height = 874
            
            img = Image.new('RGB', (label_width, label_height), color='white')
            draw = ImageDraw.Draw(img)
            
            # Get fonts
            try:
                font_large = ImageFont.truetype("arial.ttf", 28)
                font_medium = ImageFont.truetype("arial.ttf", 20)
                font_small = ImageFont.truetype("arial.ttf", 16)
            except:
                font_large = font_medium = font_small = ImageFont.load_default()
            
            # Draw border
            border_width = 3
            draw.rectangle(
                [0, 0, label_width - 1, label_height - 1],
                outline='black',
                width=border_width
            )
            
            # Generate QR Code (only Roll ID)
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=5,
                border=2,
            )
            qr.add_data(self.roll_data['roll_id'])
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_img = qr_img.resize((200, 200))
            
            # Place QR code on the right
            qr_x = label_width - 200 - 20
            qr_y = (label_height - 200) // 2
            img.paste(qr_img, (qr_x, qr_y))
            
            # Text layout
            x_start = 20
            y = 20
            line_height_large = 40
            line_height_medium = 30
            line_height_small = 25
            max_width = qr_x - x_start - 20
            
            # LOT
            lot_text = f"LOT. {self.roll_data.get('lot', '')}"
            draw.text((x_start, y), lot_text, fill='black', font=font_large)
            y += line_height_large + 10
            
            # DATE
            date_text = f"DATE {self.roll_data.get('date_received', '')}"
            draw.text((x_start, y), date_text, fill='black', font=font_medium)
            y += line_height_medium
            
            # SPECIFICATION
            spec = self.roll_data.get('specification', '')
            if spec:
                spec_text = f"SPECIFICATION: {spec}"
                spec_lines = self._wrap_text(spec_text, max_width, 16)
                for line in spec_lines:
                    draw.text((x_start, y), line, fill='black', font=font_small)
                    y += line_height_small
            
            # PRODUCT
            product_text = f"PRODUCT: {self.roll_data.get('sku', '')} ({self.roll_data.get('roll_id', '')})"
            product_lines = self._wrap_text(product_text, max_width, 16)
            for line in product_lines:
                draw.text((x_start, y), line, fill='black', font=font_small)
                y += line_height_small
            
            # COLOUR
            colour = self.roll_data.get('colour', '')
            if colour and colour != 'nan':
                colour_text = f"COLOUR: {colour}"
                draw.text((x_start, y), colour_text, fill='black', font=font_small)
                y += line_height_small
            
            # PACKING UNIT
            packing = self.roll_data.get('packing_unit', '')
            unit_type = self.roll_data.get('unit_type', 'm')
            if packing:
                packing_text = f"PACKING UNIT: {packing} {unit_type}"
                draw.text((x_start, y), packing_text, fill='black', font=font_small)
                y += line_height_small
            
            # GRADE + TYPE
            grade = self.roll_data.get('grade', 'A')
            type_of_roll = self.roll_data.get('type_of_roll', '')
            grade_text = f"GRADE {grade}"
            if type_of_roll:
                grade_text += f" {type_of_roll}"
            draw.text((x_start, y), grade_text, fill='black', font=font_medium)
            y += line_height_medium
            
            # MARKS NO.
            marks = self.roll_data.get('marks_no', '')
            if marks:
                marks_text = f"MARKS NO. {marks}"
                draw.text((x_start, y), marks_text, fill='black', font=font_small)
            
            self.label_image = img
            
            # Display preview
            self.display_preview()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error generating label: {str(e)}")
    
    def _wrap_text(self, text, max_width, font_size):
        """Wrap text to fit width"""
        # Simple wrapping - split by spaces
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            if len(test_line) * (font_size // 2) > max_width:
                if current_line:
                    lines.append(current_line)
                current_line = word
            else:
                current_line = test_line
        
        if current_line:
            lines.append(current_line)
        
        return lines if lines else [text]
    
    def display_preview(self):
        """Display the label image in the preview"""
        if self.label_image:
            # Convert PIL image to QPixmap
            buffer = BytesIO()
            self.label_image.save(buffer, format='PNG')
            buffer.seek(0)
            
            pixmap = QPixmap()
            pixmap.loadFromData(buffer.getvalue())
            
            # Scale for display
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
            
            if file_path:
                if self.label_image:
                    self.label_image.save(file_path, dpi=(300, 300))
                    QMessageBox.information(self, "Success", f"Label saved to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Save error: {str(e)}")
