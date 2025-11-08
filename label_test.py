from utils.label_generator import LabelGenerator
import cv2
import numpy as np

if __name__ == "__main__":
    generator = LabelGenerator()

    # ข้อมูลทดสอบ
    roll_data = {
        "roll_id": "ROLL-12345",
        "sku": "FAB001",
        "lot": "LOT-567",
        "length": 124.56,
        "grade": "A",
        "date_received": "2025-11-08",
        "location": "Warehouse A"
    }

    # สร้าง label
    label_img = generator.create_mini_label(roll_data)

    # แปลงจาก PIL → OpenCV
    label_cv = cv2.cvtColor(np.array(label_img), cv2.COLOR_RGB2BGR)

    # ปรับขนาดให้พอดีหน้าจอ (สูงสุด 800x600)
    max_width, max_height = 800, 600
    h, w = label_cv.shape[:2]
    scale = min(max_width / w, max_height / h, 1.0)
    new_w, new_h = int(w * scale), int(h * scale)
    label_resized = cv2.resize(label_cv, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # แสดงผลด้วย OpenCV
    cv2.imshow("Fabric Roll Label", label_resized)

    # รอจนกดปุ่มใด ๆ เพื่อปิด
    cv2.waitKey(0)
    cv2.destroyAllWindows()
