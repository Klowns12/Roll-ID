import qrcode
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter, inch, mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle, Image as RLImage
from reportlab.graphics.barcode import code128, qr
from reportlab.graphics import renderPDF
from reportlab.lib.utils import ImageReader
import tempfile
import os
from datetime import datetime

class LabelGenerator:
    """Class for generating fabric roll labels with QR codes and barcodes"""
    
    @staticmethod
    def generate_qr_code(roll_data, size=300):
        """
        Generate a QR code image from roll data
        
        Args:
            roll_data (dict): Dictionary containing roll information
            size (int): Size of the QR code image (width and height in pixels)
            
        Returns:
            QPixmap: QR code as a QPixmap
        """
        try:
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            
            # Add data to QR code
            qr_data = {
                'roll_id': roll_data.get('roll_id', ''),
                'sku': roll_data.get('sku', ''),
                'lot': roll_data.get('lot', ''),
                'length': roll_data.get('length', ''),
                'date': roll_data.get('date_received', '')
            }
            qr.add_data(json.dumps(qr_data, indent=2))
            qr.make(fit=True)
            
            # Create QR code image
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to bytes
            buffer = BytesIO()
            qr_img.save(buffer, format='PNG')
            
            # Create QPixmap from image data
            pixmap = QPixmap()
            pixmap.loadFromData(buffer.getvalue(), 'PNG')
            
            # Scale to desired size while maintaining aspect ratio
            return pixmap.scaled(size, size, 
                               Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
            
        except Exception as e:
            print(f"Error generating QR code: {str(e)}")
            # Return a blank pixmap on error
            return QPixmap(size, size)
    
    @staticmethod
    def generate_barcode(roll_id, width=400, height=100):
        """
        Generate a barcode image from roll ID
        
        Args:
            roll_id (str): The roll ID to encode in the barcode
            width (int): Width of the barcode image
            height (int): Height of the barcode image
            
        Returns:
            QPixmap: Barcode as a QPixmap
        """
        try:
            # Create barcode using code128
            code = code128.Code128(roll_id, barHeight=height, barWidth=1.0)
            
            # Create a drawing object
            from reportlab.graphics.shapes import Drawing
            d = Drawing(100, 100)
            d.add(code)
            
            # Render to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                renderPDF.drawToFile(d, tmp_file.name)
                
                # Convert to QPixmap
                pixmap = QPixmap(tmp_file.name)
                
                # Clean up
                os.unlink(tmp_file.name)
                
                # Scale to desired size
                return pixmap.scaled(width, height, 
                                   Qt.AspectRatioMode.IgnoreAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
                
        except Exception as e:
            print(f"Error generating barcode: {str(e)}")
            # Return a blank pixmap on error
            return QPixmap(width, height)
    
    @staticmethod
    def generate_pdf_label(roll_data, output_path=None):
        """
        Generate a PDF label for a fabric roll
        
        Args:
            roll_data (dict): Dictionary containing roll information
            output_path (str, optional): Path to save the PDF. If None, returns PDF data as bytes.
            
        Returns:
            bytes or None: PDF data if output_path is None, otherwise None
        """
        try:
            # Create a buffer to store PDF data if no output path is provided
            if output_path is None:
                buffer = BytesIO()
                c = canvas.Canvas(buffer, pagesize=A4)
            else:
                c = canvas.Canvas(output_path, pagesize=A4)
            
            # Set up page dimensions
            width, height = A4
            margin = 10 * mm
            
            # Title
            c.setFont("Helvetica-Bold", 16)
            c.drawCentredString(width/2, height - 20*mm, "FABRIC ROLL LABEL")
            
            # Draw a border
            c.rect(margin, margin, width - 2*margin, height - 2*margin)
            
            # Roll information
            c.setFont("Helvetica-Bold", 12)
            c.drawString(20*mm, height - 40*mm, "ROLL INFORMATION")
            c.line(20*mm, height - 42*mm, 60*mm, height - 42*mm)
            
            # Roll details
            c.setFont("Helvetica", 10)
            y_pos = height - 55*mm
            c.drawString(25*mm, y_pos, f"Roll ID: {roll_data.get('roll_id', 'N/A')}")
            y_pos -= 6*mm
            c.drawString(25*mm, y_pos, f"SKU: {roll_data.get('sku', 'N/A')}")
            y_pos -= 6*mm
            c.drawString(25*mm, y_pos, f"Lot: {roll_data.get('lot', 'N/A')}")
            y_pos -= 6*mm
            c.drawString(25*mm, y_pos, f"Length: {roll_data.get('length', 0):.2f} m")
            y_pos -= 6*mm
            c.drawString(25*mm, y_pos, f"Width: {roll_data.get('width', 1.5):.2f} m")
            y_pos -= 6*mm
            c.drawString(25*mm, y_pos, f"Grade: {roll_data.get('grade', 'A')}")
            y_pos -= 6*mm
            c.drawString(25*mm, y_pos, f"Location: {roll_data.get('location', 'N/A')}")
            y_pos -= 6*mm
            c.drawString(25*mm, y_pos, f"Date: {roll_data.get('date_received', datetime.now().strftime('%Y-%m-%d'))}")
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=4,
                border=2,
            )
            
            # Add data to QR code
            qr_data = {
                'roll_id': roll_data.get('roll_id', ''),
                'sku': roll_data.get('sku', ''),
                'lot': roll_data.get('lot', ''),
                'length': roll_data.get('length', ''),
                'date': roll_data.get('date_received', '')
            }
            qr.add_data(json.dumps(qr_data, indent=2))
            qr.make(fit=True)
            
            # Create QR code image
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Save QR code to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                qr_img.save(tmp_file)
                tmp_file_path = tmp_file.name
            
            # Add QR code to PDF
            qr_width = 40*mm
            qr_height = 40*mm
            c.drawImage(
                tmp_file_path,
                width - 60*mm,
                height - 60*mm,
                width=qr_width,
                height=qr_height
            )
            
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
            # Add barcode
            barcode_value = roll_data.get('roll_id', 'N/A')
            barcode = code128.Code128(
                barcode_value,
                barHeight=15*mm,
                barWidth=1.0
            )
            
            # Draw barcode
            barcode.drawOn(c, 25*mm, 30*mm)
            
            # Add barcode text
            c.setFont("Helvetica", 8)
            c.drawCenteredString(
                width/2,
                25*mm,
                barcode_value
            )
            
            # Add company logo (placeholder - replace with actual logo path)
            # try:
            #     logo_path = "path/to/logo.png"
            #     if os.path.exists(logo_path):
            #         c.drawImage(logo_path, 25*mm, height-25*mm, width=30*mm, height=15*mm, preserveAspectRatio=True)
            # except:
            #     pass  # Skip if logo not found
            
            # Add footer
            c.setFont("Helvetica-Oblique", 8)
            c.drawCentredString(
                width/2,
                10*mm,
                f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            # Save the PDF
            c.showPage()
            c.save()
            
            # Return the PDF data if no output path was provided
            if output_path is None:
                buffer.seek(0)
                return buffer.getvalue()
                
        except Exception as e:
            print(f"Error generating PDF label: {str(e)}")
            raise
    
    @staticmethod
    def generate_pdf_sheet(rolls, output_path=None, rows=5, cols=2):
        """
        Generate a PDF sheet with multiple labels
        
        Args:
            rolls (list): List of roll data dictionaries
            output_path (str, optional): Path to save the PDF. If None, returns PDF data as bytes.
            rows (int): Number of rows of labels per page
            cols (int): Number of columns of labels per page
            
        Returns:
            bytes or None: PDF data if output_path is None, otherwise None
        """
        try:
            # Create a buffer to store PDF data if no output path is provided
            if output_path is None:
                buffer = BytesIO()
                c = canvas.Canvas(buffer, pagesize=A4)
            else:
                c = canvas.Canvas(output_path, pagesize=A4)
            
            # Set up page dimensions
            width, height = A4
            margin = 10 * mm
            
            # Calculate label dimensions
            label_width = (width - 2*margin) / cols
            label_height = (height - 2*margin) / rows
            
            # Process each roll
            for i, roll in enumerate(rolls):
                # Calculate position
                row = (i // cols) % rows
                col = i % cols
                
                # Start a new page if needed
                if i > 0 and i % (rows * cols) == 0:
                    c.showPage()
                    row = 0
                    col = 0
                
                # Calculate position
                x = margin + col * label_width
                y = height - margin - (row + 1) * label_height
                
                # Draw label border
                c.rect(x, y, label_width, label_height)
                
                # Add roll information
                c.setFont("Helvetica-Bold", 10)
                c.drawString(x + 5*mm, y + label_height - 5*mm, f"ID: {roll.get('roll_id', 'N/A')}")
                
                c.setFont("Helvetica", 8)
                c.drawString(x + 5*mm, y + label_height - 10*mm, f"SKU: {roll.get('sku', 'N/A')}")
                c.drawString(x + 5*mm, y + label_height - 13*mm, f"Lot: {roll.get('lot', 'N/A')}")
                c.drawString(x + 5*mm, y + label_height - 16*mm, f"Length: {roll.get('length', 0):.2f} m")
                
                # Generate and add QR code
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=2,
                    border=1,
                )
                
                # Add data to QR code
                qr_data = {
                    'roll_id': roll.get('roll_id', ''),
                    'sku': roll.get('sku', ''),
                    'lot': roll.get('lot', ''),
                    'length': roll.get('length', ''),
                    'date': roll.get('date_received', '')
                }
                qr.add_data(json.dumps(qr_data, indent=2))
                qr.make(fit=True)
                
                # Create QR code image
                qr_img = qr.make_image(fill_color="black", back_color="white")
                
                # Save QR code to a temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                    qr_img.save(tmp_file)
                    tmp_file_path = tmp_file.name
                
                # Add QR code to PDF
                qr_size = 20*mm
                c.drawImage(
                    tmp_file_path,
                    x + label_width - qr_size - 2*mm,
                    y + label_height - qr_size - 2*mm,
                    width=qr_size,
                    height=qr_size
                )
                
                # Clean up temporary file
                os.unlink(tmp_file_path)
                
                # Add barcode
                barcode_value = roll.get('roll_id', 'N/A')
                barcode = code128.Code128(
                    barcode_value,
                    barHeight=5*mm,
                    barWidth=0.8
                )
                
                # Draw barcode
                barcode.drawOn(c, x + 5*mm, y + 5*mm)
                
                # Add barcode text
                c.setFont("Helvetica", 6)
                c.drawString(
                    x + 5*mm,
                    y + 2*mm,
                    barcode_value
                )
            
            # Save the PDF
            c.showPage()
            c.save()
            
            # Return the PDF data if no output path was provided
            if output_path is None:
                buffer.seek(0)
                return buffer.getvalue()
                
        except Exception as e:
            print(f"Error generating PDF sheet: {str(e)}")
            raise
