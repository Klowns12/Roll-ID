from PyInstaller.utils.hooks import collect_submodules

# Include all barcode modules
hiddenimports = collect_submodules('reportlab.graphics.barcode')
