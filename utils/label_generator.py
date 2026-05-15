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

    def create_label(self, roll_data, include_qr=True, user="system"):
        """
        สร้างฉลากขนาด 10x5 เซนติเมตร (300 DPI)

        Args:
            roll_data: dict ข้อมูลม้วนผ้า
            include_qr: bool รวม QR Code หรือไม่
            user: ชื่อผู้ที่สั่งพิมพ์ฉลาก
            PIL.Image: รูปฉลากขนาดเล็ก
        """

        is_dict = isinstance(roll_data, dict)

        def _is_empty(value):
            if value is None:
                return True
            if isinstance(value, str):
                return value.strip() == ""
            return False

        def _get_value(*keys, default=""):
            for key in keys:
                if is_dict and key in roll_data and not _is_empty(roll_data[key]):
                    return roll_data[key]
                if hasattr(roll_data, key):
                    value = getattr(roll_data, key)
                    if not _is_empty(value):
                        return value
            return default

        def _format_number(value):
            if isinstance(value, (int, float)):
                return (f"{value:.2f}").rstrip("0").rstrip(".")
            return str(value)

        length_value = _get_value("length", "current_length", "original_length")
        length_text = ""
        if not _is_empty(length_value):
            if isinstance(length_value, (int, float)):
                length_text = _format_number(length_value)
                if length_text:
                    length_text = f"{length_text}m"
            else:
                length_text = str(length_value).strip()

        # ใช้ข้อมูลจริง หรือค่า default ถ้าไม่มี
        data = {
            "roll_id": _get_value("roll_id"),
            "sku": _get_value("sku", "code", "pdt_code"),
            "product_name": _get_value(
                "code", "sku", "pdt_code", "product_name", "pdt_name", "description"
            ),
            "lot": _get_value("lot", "lot_no"),
            "date_received": _get_value(
                "date_received", default=datetime.now().strftime("%Y-%m-%d")
            ),
            "specification": _get_value(
                "specification",
                "specificattion",
                "pdt_name",
                "product_name",
                "pdt_code",
                "sku",
                "code",
            ),
            "colour": _get_value("colour", "color"),
            "packing_unit": _get_value("packing_unit", "package_unit", "unit_type", "unit"),
            "unit_type": _get_value("unit_type", default="MTS"),
            "grade": _get_value("grade", default="A"),
            "type_of_roll": _get_value("type_of_roll"),
            "marks_no": _get_value("marks_no"),
            "current_length": _get_value("current_length"),
            "width": _get_value("width"),
            "length": length_text,
            "original_length": _get_value("original_length"),
            "location": _get_value("location"),
            "status": _get_value("status"),
            "invoice_number": _get_value("invoice_number"),
            "po_number": _get_value("po_number"),
        }

        # ขนาดพิกเซล 300 DPI
        width = int(10 * 300 / 2.54)  # 10 cm
        height = int(5 * 300 / 2.54)  # 5 cm
        
        # กำหนดระยะขอบที่ปลอดภัย (Safe Margin)
        margin = 40 

        img = Image.new("RGB", (width, height), self.color_bg)
        draw = ImageDraw.Draw(img)

        # วาดขอบที่เลื่อนเข้ามาด้านใน
        draw.rectangle(
            [margin // 2, margin // 2, width - (margin // 2), height - (margin // 2)], 
            outline=self.color_border, width=2
        )

        # QR Code ต้องเก็บ Roll ID เพื่อให้ Dispatch tab ค้นหาได้ง่าย
        qr_string = f"{data['roll_id']}"

        # QR Code ขนาดเล็กลงเล็กน้อยเพื่อความปลอดภัย
        if include_qr:
            qr_size = 300 # ลดจาก 340
            qr_img = self.generate_qr_code(qr_string, size=qr_size)
            qr_x = (width - qr_size) - margin
            qr_y = (height - qr_size) - margin
            img.paste(qr_img, (qr_x, qr_y))

        # ข้อมูลทางขวาของ QR Code
        # Try to load Thai font with multiple fallbacks
        thai_font_paths = [
            "C:/Windows/Fonts/THSarabunNew-Bold.ttf",  # Common Windows path
            "C:/Windows/Fonts/THSarabunNew.ttf",  # Regular version
            "C:/Windows/Fonts/THSarabun.ttf",  # Older version
            "C:/Windows/Fonts/TH Niramit AS.ttf",  # Another common Thai font
            "C:/Windows/Fonts/LeelawUI.ttf",  # Windows 10+ Thai font
            "C:/Windows/Fonts/leelawad.ttf",  # Windows legacy Thai font
            "THSarabunNew-Bold.ttf",  # Local directory
            "arialuni.ttf",  # Windows Unicode font with Thai support
            "ArialUni.ttf",
            "C:/Windows/Fonts/arial.ttf",  # Regular Arial
            "arial.ttf",
        ]

        # Function to load font with multiple fallbacks
        def load_font(paths, size):
            for path in paths:
                try:
                    return ImageFont.truetype(path, size)
                except (IOError, OSError):
                    continue
            try:
                return ImageFont.truetype("arialbd.ttf", size)
            except:
                return ImageFont.load_default()

        # Load large font for most text
        font_large = load_font(thai_font_paths, 34)

        # Try to load a specific Thai font for the specification text
        thai_font = None
        for path in thai_font_paths:
            try:
                thai_font = ImageFont.truetype(path, 34)
                break
            except (IOError, OSError):
                continue

        # If no Thai font found, use the main large font
        if thai_font is None:
            thai_font = font_large

        # ตำแหน่งข้อความหลัก
        t_x = margin + 20
        t_y = 185 # ขยับขึ้นเล็กน้อย
        t_gap = 42 # ลดระยะห่างระหว่างบรรทัดเพื่อให้ 8 บรรทัดไม่ทับขอบ

        # คำนวณพื้นที่ความกว้างสำหรับข้อความ (เพื่อไม่ให้ทับ QR)
        qr_start_x = (width - 300) - margin
        max_text_width = qr_start_x - t_x - 30 

        # แสดงข้อมูลทีละบรรทัด พร้อมระบบตัดข้อความอัตโนมัติ
        # รวม Width และ Length ไว้ในบรรทัดเดียวกันเพื่อประหยัดพื้นที่
        w_l_text = f"{data.get('width', '')}  |  {data.get('length', '')}"
        
        fields = [
            ("ROLL ID", data['roll_id']),
            ("SPECIFICATION", data['specification']),
            ("PRODUCT", data['product_name']),
            ("COLOR", data['colour']),
            ("PACKING UNIT", data['packing_unit']),
            ("DIMENSION", w_l_text),
            ("LOCATION", data['location']),
            ("PRINTED BY", user)
        ]

        for i, (label, val) in enumerate(fields):
            prefix = f"{label} : "
            prefix_w = draw.textlength(prefix, font=font_large)
            avail_w = max_text_width - prefix_w
            
            # ใช้ฟอนต์ไทยสำหรับข้อมูล
            display_val = self._truncate_text_by_width(draw, str(val), thai_font, avail_w)
            
            draw.text(
                (t_x, t_y + (t_gap * i)),
                f"{prefix}{display_val}",
                fill=self.color_text,
                font=font_large if label != "SPECIFICATION" else thai_font
            )

        # ------------------------------------------------------------
        # โซนขวาบน (Header Stack: LOT -> DATE)
        # ------------------------------------------------------------
        
        # 1. LOT (บนสุด - ตัวหนาใหญ่)
        lot_val = str(data['lot'])
        lot_label = "LOT."
        lot_val_font = ImageFont.truetype("arialbd.ttf", 60)
        lot_val_w = draw.textlength(lot_val, font=lot_val_font)
        
        # วาด "LOT." เล็กๆ ข้างหน้าเลขล็อต
        draw.text((width - lot_val_w - margin - 100, margin + 25), lot_label, fill=self.color_text, font=font_large)
        # วาดเลขล็อต
        draw.text((width - lot_val_w - margin - 20, margin + 5), lot_val, fill=self.color_text, font=lot_val_font)

        # 2. DATE (ใต้ LOT)
        date_text = f"DATE: {data['date_received']}"
        date_w = draw.textlength(date_text, font=font_large)
        draw.text(
            (width - date_w - margin - 20, margin + 75),
            date_text,
            fill=self.color_text,
            font=font_large,
        )

        # Lot No. ถูกย้ายไปด้านบนขวาแล้ว

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

    def _truncate_text_by_width(self, draw, text, font, max_width):
        """ตัดข้อความตามความกว้างพิกเซล"""
        if not text:
            return ""

        # Check if full text fits
        if draw.textlength(text, font=font) <= max_width:
            return text

        current_text = str(text)
        while len(current_text) > 0:
            test_text = current_text + "..."
            if draw.textlength(test_text, font=font) <= max_width:
                return test_text
            current_text = current_text[:-1]

        return "..."

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
            width=2,
        )

    def save_label(self, image, filename, format="PNG"):
        """
        บันทึกฉลากเป็นไฟล์

        Args:
            image: PIL.Image ฉลาก
            filename: ชื่อไฟล์
            format: รูปแบบไฟล์ (PNG, PDF, JPEG)
        """
        if format.upper() == "PDF":
            image.save(filename, format="PDF", resolution=300.0)
        else:
            image.save(filename, format=format)

    def get_label_as_bytes(self, image, format="PNG"):
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
