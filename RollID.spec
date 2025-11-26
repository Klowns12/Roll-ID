# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets'), ('data', 'data')],
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
    hookspath=['.'],
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