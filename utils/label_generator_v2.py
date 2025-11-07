"""
Label Generator V2 for Fabric Rolls
สร้างฉลาก QR Code แบบใหม่ตามรูปแบบที่กำหนด
"""

from PIL import Image, ImageDraw, ImageFont
import qrcode
from io import BytesIO
from datetime import datetime
import os


class LabelGeneratorV2:
    """สร้างและจัดการฉลาก QR Code สำหรับม้วนผ้า (รุ่นที่ 2)"""
    
    def __init__(self):
        # ขนาดฉลาก (พิกเซล) - 10x6 cm at 300 DPI = 1181x709 pixels
        self.label_width = 1181
        self.label_height = 709
        
        # สีที่ใช้
        self.color_bg = (255, 255, 255)  # สีพื้นหลัง
        self.color_border = (0, 0, 0)  # สีขอบ
        self.color_text = (0, 0, 0)  # สีตัวอักษร
        
        # QR Code size
        self.qr_size = 200
    
    def _get_font(self, size=12):
        """Get font with fallback"""
        try:
            # Try Arial font (Windows)
            return ImageFont.truetype("arial.ttf", size)
        except:
            try:
                # Try alternative fonts
                return ImageFont.truetype("DejaVuSans.ttf", size)
            except:
                # Fallback to default
                return ImageFont.load_default()
    
    def create_compact_label(self, roll_data):
        """
        สร้างฉลากแบบกะทัดรัดตามรูปแบบใหม่
        
        Args:
            roll_data: dict ข้อมูลม้วนผ้า
                - roll_id: เลขม้วน (pdt_code_RollID)
                - sku: รหัสสินค้า (pdt_code)  
                - lot: เลข lot (Lot_of_SPL)
                - original_length: ความยาว (RollQTY)
                - grade: เกรด (A, B, C)
                - date_received: วันที่รับเข้า
                - marks_no: เลข marks
                - specification: รายละเอียดสินค้า
                - colour: สี
                - packing_unit: หน่วยบรรจุ
                - type_of_roll: ประเภทม้วน (เศษ, เต็ม)
        
        Returns:
            PIL.Image: รูปฉลาก
        """
        # สร้าง image พื้นหลัง
        img = Image.new('RGB', (self.label_width, self.label_height), self.color_bg)
        draw = ImageDraw.Draw(img)
        
        # วาดขอบ
        border_width = 3
        draw.rectangle(
            [0, 0, self.label_width - 1, self.label_height - 1],
            outline=self.color_border,
            width=border_width
        )
        
        # สร้าง QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=5,
            border=2,
        )
        qr.add_data(roll_data.get('roll_id', ''))
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img = qr_img.resize((self.qr_size, self.qr_size))
        
        # วาง QR Code ทางขวา
        qr_x = self.label_width - self.qr_size - 20
        qr_y = (self.label_height - self.qr_size) // 2
        img.paste(qr_img, (qr_x, qr_y))
        
        # เตรียม fonts
        font_large = self._get_font(24)
        font_medium = self._get_font(18)
        font_small = self._get_font(14)
        
        # เขียนข้อความ
        x_start = 20
        y = 20
        line_height_large = 35
        line_height_medium = 28
        line_height_small = 22
        
        # LOT
        lot_text = f"LOT. {roll_data.get('lot', '')}"
        draw.text((x_start, y), lot_text, fill=self.color_text, font=font_large)
        y += line_height_large + 10
        
        # DATE
        date_text = f"DATE {roll_data.get('date_received', '')}"
        draw.text((x_start, y), date_text, fill=self.color_text, font=font_medium)
        y += line_height_medium
        
        # SPECIFICATION
        spec_text = f"SPECIFICATION : {roll_data.get('specification', '')}"
        # แบ่งข้อความถ้ายาวเกิน
        max_width = qr_x - x_start - 20
        spec_lines = self._wrap_text(spec_text, font_small, max_width, draw)
        for line in spec_lines:
            draw.text((x_start, y), line, fill=self.color_text, font=font_small)
            y += line_height_small
        
        # PRODUCT
        product_text = f"PRODUCT: {roll_data.get('sku', '')} ({roll_data.get('roll_id', '')})"
        product_lines = self._wrap_text(product_text, font_small, max_width, draw)
        for line in product_lines:
            draw.text((x_start, y), line, fill=self.color_text, font=font_small)
            y += line_height_small
        
        # COLOUR
        colour_text = f"COLOUR : {roll_data.get('colour', '')}"
        draw.text((x_start, y), colour_text, fill=self.color_text, font=font_small)
        y += line_height_small
        
        # PACKING UNIT
        packing_text = f"PACKING UNIT : {roll_data.get('packing_unit', '')} {roll_data.get('unit_type', 'm')}"
        draw.text((x_start, y), packing_text, fill=self.color_text, font=font_small)
        y += line_height_small
        
        # GRADE + type_of_roll
        type_of_roll = roll_data.get('type_of_roll', '')
        grade_text = f"GRADE {roll_data.get('grade', 'A')}"
        if type_of_roll:
            grade_text += f" {type_of_roll}"
        draw.text((x_start, y), grade_text, fill=self.color_text, font=font_medium)
        y += line_height_medium
        
        # MARKS NO.
        if roll_data.get('marks_no'):
            marks_text = f"MARKS NO. {roll_data.get('marks_no', '')}"
            draw.text((x_start, y), marks_text, fill=self.color_text, font=font_small)
        
        return img
    
    def _wrap_text(self, text, font, max_width, draw):
        """แบ่งข้อความเมื่อยาวเกิน"""
        lines = []
        words = text.split()
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            bbox = draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]
            
            if width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines if lines else [text]
    
    def save_label(self, img, filename):
        """
        บันทึกฉลากเป็นไฟล์
        
        Args:
            img: PIL.Image รูปฉลาก
            filename: str ชื่อไฟล์ (รวม path และ extension)
        """
        # สร้างโฟลเดอร์ถ้ายังไม่มี
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
        
        # บันทึกไฟล์
        img.save(filename, dpi=(300, 300))
        
        return filename
    
    def get_label_bytes(self, img, format='PNG'):
        """
        แปลงฉลากเป็น bytes สำหรับพิมพ์หรือส่ง
        
        Args:
            img: PIL.Image รูปฉลาก
            format: str รูปแบบไฟล์ (PNG, JPEG, PDF)
        
        Returns:
            bytes: ข้อมูลรูปภาพ
        """
        buffer = BytesIO()
        img.save(buffer, format=format, dpi=(300, 300))
        buffer.seek(0)
        return buffer.getvalue()
