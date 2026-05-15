# -*- mode: python ; coding: utf-8 -*-
import os
import base64

# 1. อ่านไฟล์ assets/mobile_scan.html และแปลงเป็น Base64 ฝังลงใน utils/bundled_html.py อัตโนมัติตอน Build
try:
    html_path = os.path.join("assets", "mobile_scan.html")
    bundled_py_path = os.path.join("utils", "bundled_html.py")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        b64_content = base64.b64encode(html_content.encode("utf-8")).decode("utf-8")
        
        with open(bundled_py_path, "w", encoding="utf-8") as f:
            f.write("# Generated automatically during build. Do not modify.\n")
            f.write("import base64\n")
            f.write(f'B64_HTML = "{b64_content}"\n')
            f.write("HTML_CONTENT = base64.b64decode(B64_HTML).decode(\"utf-8\")\n")
        print(">>> Successfully generated utils/bundled_html.py for production!")
except Exception as e:
    print(f">>> Error generating bundled_html.py: {e}")

# 2. กรองไฟล์ใน assets เพื่อไม่ให้ไฟล์ mobile_scan.html ติดไปในโฟลเดอร์ dist (ซ่อนไฟล์จาก User)
assets_datas = []
assets_dir = "assets"
if os.path.exists(assets_dir):
    for filename in os.listdir(assets_dir):
        file_path = os.path.join(assets_dir, filename)
        if filename != "mobile_scan.html" and os.path.isfile(file_path):
            assets_datas.append((file_path, "assets"))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=assets_datas + [('data', 'data'), ('cert', 'cert')],
    hiddenimports=[
        'reportlab.graphics.barcode.code39',
        'reportlab.graphics.barcode.code39Extended',
        'reportlab.graphics.barcode.code93',
        'reportlab.graphics.barcode.code128',
        'reportlab.graphics.barcode.qr',
        'reportlab.graphics.barcode.usps',
        'socketio.async_drivers.threading',
        'engineio.async_drivers.threading',
    ],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='RollID',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\fabric.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='RollID',
)