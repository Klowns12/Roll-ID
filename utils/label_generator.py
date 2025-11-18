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
        สร้างฉลากขนาด 10x5 เซนติเมตร (300 DPI)
        
        Args:
            roll_data: dict ข้อมูลม้วนผ้า
            include_qr: bool รวม QR Code หรือไม่
        
        Returns:
            PIL.Image: รูปฉลากขนาดเล็ก
        """
        
        # ใช้ข้อมูลจริง หรือค่า default ถ้าไม่มี
        data = {
            'roll_id': getattr(roll_data,'roll_id',''),
            'sku': getattr(roll_data,'sku',''),
            'product_name': getattr(roll_data, 'spl_name', ''),  
            'lot': getattr(roll_data, 'lot', ''),
            'date_received': getattr(roll_data, 'date_received', datetime.now().strftime('%Y-%m-%d')),
            'specification': getattr(roll_data, 'specificattion', getattr(roll_data, 'pdt_code', '')),
            'colour': getattr(roll_data, 'colour', ''),
            'packing_unit': getattr(roll_data, 'packing_unit', ''),
            'unit_type': getattr(roll_data, 'unit_type', 'MTS'),
            'grade': getattr(roll_data, 'grade', 'A'),
            'type_of_roll': getattr(roll_data, 'type_of_roll', ''),
            'marks_no': getattr(roll_data, 'marks_no', ''),
            'current_length': getattr(roll_data, 'current_length', 0),
            'width': getattr(roll_data, 'width', ''),
            'original_length': getattr(roll_data, 'original_length', 0),
            'location': getattr(roll_data, 'location', ''),
            'status': getattr(roll_data, 'status', ''),
            'invoice_number': getattr(roll_data, 'invoice_number', ''),
            'po_number': getattr(roll_data, 'po_number', '')
        }



        # ขนาดพิกเซล 300 DPI
        width = int(10 * 300 / 2.54)  # 10 cm
        height = int(5 * 300 / 2.54)  # 5 cm

        img = Image.new('RGB', (width, height), self.color_bg)
        draw = ImageDraw.Draw(img)
        
        # วาดขอบ
        draw.rectangle([5, 5, width - 5, height - 5], outline=self.color_border, width=2)
        

        # QR Code ต้องเก็บ SKU (Code) ไม่ใช่ Roll ID เพื่อให้ Dispatch tab ค้นหาได้
        # qr_string = data['roll_id']
        qr_string = f"R001%CODE1%SUB_PART_CODE%SUP_CODE%SUPPLIER_NAME%DESCRIPTION%LOT_NO%LOCATION%STATUS"

 

        # QR Code ขนาดเล็ก
        if include_qr:
            qr_size = 340
            qr_img = self.generate_qr_code(qr_string, size=qr_size)
            qr_x = (width - qr_size) - 20
            qr_y = (height - qr_size) - 20
            img.paste(qr_img, (qr_x, qr_y))
        
        # ข้อมูลทางขวาของ QR Code
        try:
            font_large = ImageFont.truetype("arialbd.ttf", 34)
        except:
            font_large = ImageFont.load_default()

        t_x = 50 
        t_y = 180
        t_gap = 50  # Reduced gap to fit before QR
        max_width = 400  # Max width before QR code

        def truncate_text(text, max_chars=25):
            """ตัดข้อความยาวด้วย ..."""
            if len(text) > max_chars:
                return text[:max_chars-3] + "..."
            return text

        # เลขม้วน
        draw.text((t_x, t_y + (t_gap * 0)), f"ROLL ID : {data['roll_id']}", 
                fill=self.color_text, font=font_large)

        spec_text = truncate_text(data['specification'], 25)
        draw.text((t_x, t_y + (t_gap * 1)), f"SPECIFICAT ON : {spec_text}", 
                fill=self.color_text, font=font_large)
        
        product_text = truncate_text(data['product_name'], 25)
        draw.text((t_x, t_y + (t_gap * 2)), f"PRODUCT : {product_text}", 
                fill=self.color_text, font=font_large)
        
        draw.text((t_x, t_y + (t_gap * 3)), f"COLOR : {data['colour']}", 
                fill=self.color_text, font=font_large)
        
        draw.text((t_x, t_y + (t_gap * 4)), f"PACKING UNIT : {data['packing_unit']}", 
                fill=self.color_text, font=font_large)
        
        draw.text((t_x, t_y + (t_gap * 5)), f"WIDTH : {data.get('width', '')}", 
                fill=self.color_text, font=font_large)
        

        # วันที่
        draw.text((width - 350, t_y - t_gap), f"DATE  {data['date_received']}", 
                fill=self.color_text, font=font_large)

        # Lot No.
        lot_x = width - 400
        lot_y = 70

        draw.text((lot_x, lot_y), "LOT.", 
                fill=self.color_text, font=font_large)

        draw.text((lot_x + 100, lot_y - 20), f'{data['lot']}', 
                fill=self.color_text, font=ImageFont.truetype("arialbd.ttf", 64))

        
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
