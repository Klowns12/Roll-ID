"""
Label Generator for Fabric Rolls
สร้างฉลาก QR Code พร้อมข้อมูลม้วนผ้า
"""

from PIL import Image, ImageDraw, ImageFont
import qrcode
from io import BytesIO
from datetime import datetime


class LabelGenerator:
    """สร้างและจัดการฉลาก QR Code สำหรับม้วนผ้า"""
    
    def __init__(self):
        # ขนาดฉลากมาตรฐาน (พิกเซล) - A6 size at 300 DPI
        self.label_width = 1240
        self.label_height = 1748
        
        # สีที่ใช้
        self.color_bg = (255, 255, 255)  # สีพื้นหลัง
        self.color_border = (0, 0, 0)  # สีขอบ
        self.color_text = (0, 0, 0)  # สีตัวอักษร
        self.color_header_bg = (33, 150, 243)  # สีพื้นหลังหัวเรื่อง
        self.color_header_text = (255, 255, 255)  # สีตัวอักษรหัวเรื่อง
    
    def create_label(self, roll_data, include_qr=True):
        """
        สร้างฉลากม้วนผ้า
        
        Args:
            roll_data: dict ข้อมูลม้วนผ้า
                - roll_id: เลขม้วน
                - sku: รหัสสินค้า
                - lot: เลข lot
                - length: ความยาว (cm)
                - grade: เกรด (A, B, C)
                - date_received: วันที่รับเข้า
                - location: สถานที่จัดเก็บ
            include_qr: bool รวม QR Code หรือไม่
        
        Returns:
            PIL.Image: รูปฉลาก
        """
        # สร้าง image พื้นหลัง
        img = Image.new('RGB', (self.label_width, self.label_height), self.color_bg)
        draw = ImageDraw.Draw(img)
        
        # วาดขอบ
        border_width = 10
        draw.rectangle(
            [border_width, border_width, 
             self.label_width - border_width, 
             self.label_height - border_width],
            outline=self.color_border,
            width=5
        )
        
        y_position = 30
        
        # Header
        header_height = 120
        draw.rectangle(
            [border_width + 10, y_position, 
             self.label_width - border_width - 10, 
             y_position + header_height],
            fill=self.color_header_bg
        )
        
        # ชื่อระบบ
        try:
            header_font = ImageFont.truetype("arial.ttf", 48)
        except:
            header_font = ImageFont.load_default()
        
        header_text = "FABRIC ROLL"
        header_bbox = draw.textbbox((0, 0), header_text, font=header_font)
        header_width = header_bbox[2] - header_bbox[0]
        draw.text(
            ((self.label_width - header_width) / 2, y_position + 35),
            header_text,
            fill=self.color_header_text,
            font=header_font
        )
        
        y_position += header_height + 40
        
        # QR Code (ถ้าต้องการ)
        if include_qr:
            qr_data = roll_data.get('roll_id', '')
            qr_img = self.generate_qr_code(qr_data, size=400)
            
            # วาง QR Code ตรงกลาง
            qr_x = (self.label_width - qr_img.width) // 2
            img.paste(qr_img, (qr_x, y_position))
            y_position += qr_img.height + 30
        
        # ข้อมูลม้วนผ้า
        try:
            data_font_large = ImageFont.truetype("arialbd.ttf", 56)
            data_font_medium = ImageFont.truetype("arial.ttf", 40)
            data_font_small = ImageFont.truetype("arial.ttf", 32)
        except:
            data_font_large = ImageFont.load_default()
            data_font_medium = ImageFont.load_default()
            data_font_small = ImageFont.load_default()
        
        # เลขม้วน (ขนาดใหญ่)
        roll_id = roll_data.get('roll_id', 'N/A')
        self._draw_centered_text(
            draw, roll_id, y_position, 
            data_font_large, self.label_width, bold=True
        )
        y_position += 80
        
        # เส้นแบ่ง
        self._draw_separator(draw, y_position)
        y_position += 30
        
        # ข้อมูลในรูปแบบตาราง
        padding_left = 100
        line_spacing = 70
        
        data_fields = [
            ("SKU:", roll_data.get('sku', 'N/A')),
            ("LOT:", roll_data.get('lot', 'N/A')),
            ("LENGTH:", f"{roll_data.get('length', 0):.2f} cm"),
            ("GRADE:", roll_data.get('grade', 'A')),
            ("DATE:", roll_data.get('date_received', datetime.now().strftime("%Y-%m-%d"))),
            ("LOCATION:", roll_data.get('location', '-'))
        ]
        
        for label, value in data_fields:
            # วาด label
            draw.text(
                (padding_left, y_position),
                label,
                fill=self.color_text,
                font=data_font_medium
            )
            
            # วาด value (ขยับไปทางขวา)
            draw.text(
                (padding_left + 300, y_position),
                str(value),
                fill=self.color_text,
                font=data_font_large if label in ["SKU:", "LENGTH:"] else data_font_medium
            )
            
            y_position += line_spacing
        
        # Footer
        y_position = self.label_height - 150
        self._draw_separator(draw, y_position)
        y_position += 20
        
        footer_text = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        self._draw_centered_text(
            draw, footer_text, y_position,
            data_font_small, self.label_width
        )
        
        return img
    
    def generate_qr_code(self, data, size=300):
        """
        สร้าง QR Code
        
        Args:
            data: ข้อมูลที่จะเข้ารหัส
            size: ขนาดของ QR Code (พิกเซล)
        
        Returns:
            PIL.Image: QR Code image
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img = qr_img.resize((size, size), Image.Resampling.LANCZOS)
        
        return qr_img
    
    def _draw_centered_text(self, draw, text, y, font, width, bold=False):
        """วาดข้อความตรงกลาง"""
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) / 2
        draw.text((x, y), text, fill=self.color_text, font=font)
    
    def _draw_separator(self, draw, y):
        """วาดเส้นแบ่ง"""
        margin = 80
        draw.line(
            [(margin, y), (self.label_width - margin, y)],
            fill=self.color_border,
            width=2
        )
    
    def create_mini_label(self, roll_data):
        """
        สร้างฉลากขนาดเล็ก (สำหรับติดม้วน)
        
        Args:
            roll_data: dict ข้อมูลม้วนผ้า
        
        Returns:
            PIL.Image: รูปฉลากขนาดเล็ก
        """
        # ขนาดเล็กลง (4x3 นิ้ว ที่ 300 DPI)
        width = 1200
        height = 900
        
        img = Image.new('RGB', (width, height), self.color_bg)
        draw = ImageDraw.Draw(img)
        
        # วาดขอบ
        draw.rectangle([10, 10, width - 10, height - 10], outline=self.color_border, width=3)
        
        # QR Code ขนาดเล็ก
        qr_size = 250
        qr_data = roll_data.get('roll_id', '')
        qr_img = self.generate_qr_code(qr_data, size=qr_size)
        
        # วาง QR Code ทางซ้าย
        qr_margin = 40
        img.paste(qr_img, (qr_margin, qr_margin))
        
        # ข้อมูลทางขวา
        try:
            font_large = ImageFont.truetype("arialbd.ttf", 40)
            font_medium = ImageFont.truetype("arial.ttf", 32)
            font_small = ImageFont.truetype("arial.ttf", 24)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        text_x = qr_margin + qr_size + 50
        y = 50
        line_height = 60
        
        # เลขม้วน
        draw.text((text_x, y), roll_data.get('roll_id', 'N/A'), 
                 fill=self.color_text, font=font_large)
        y += line_height
        
        # SKU
        draw.text((text_x, y), f"SKU: {roll_data.get('sku', 'N/A')}", 
                 fill=self.color_text, font=font_medium)
        y += line_height
        
        # Length
        draw.text((text_x, y), f"{roll_data.get('length', 0):.2f} cm", 
                 fill=self.color_text, font=font_large)
        y += line_height
        
        # Grade
        draw.text((text_x, y), f"Grade: {roll_data.get('grade', 'A')}", 
                 fill=self.color_text, font=font_medium)
        y += line_height
        
        # Date (ด้านล่าง)
        date_text = roll_data.get('date_received', datetime.now().strftime("%Y-%m-%d"))
        draw.text((qr_margin, height - 50), date_text, 
                 fill=self.color_text, font=font_small)
        
        return img
    
    def save_label(self, image, filename, format='PNG'):
        """
        บันทึกฉลากเป็นไฟล์
        
        Args:
            image: PIL.Image ฉลาก
            filename: ชื่อไฟล์
            format: รูปแบบไฟล์ (PNG, PDF, JPEG)
        """
        if format.upper() == 'PDF':
            image.save(filename, format='PDF', resolution=300.0)
        else:
            image.save(filename, format=format)
    
    def get_label_as_bytes(self, image, format='PNG'):
        """
        แปลงฉลากเป็น bytes สำหรับแสดงผลหรือส่งข้อมูล
        
        Args:
            image: PIL.Image ฉลาก
            format: รูปแบบไฟล์
        
        Returns:
            BytesIO: ข้อมูล bytes ของฉลาก
        """
        buffer = BytesIO()
        image.save(buffer, format=format)
        buffer.seek(0)
        return buffer
