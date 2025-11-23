from pathlib import Path



class PathConfig:
    # โฟลเดอร์ไฟล์นี้อยู่ที่ไหน
    BASE_DIR = Path(__file__).resolve().parent.parent

    # สร้างโฟลเดอร์ data
    DATA_DIR = BASE_DIR / "data"

    # ตัวอย่าง path อื่น ๆ
    LOG_DIR = BASE_DIR / "logs"
    CONFIG_DIR = BASE_DIR / "config"
