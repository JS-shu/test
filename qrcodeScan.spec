# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['start.py'],
    pathex=[],
    binaries=[],
    datas=[('libiconv.dll', '.'), ('libzbar-64.dll', '.'), ('C:\\\\Users\\\\Shu73\\\\AppData\\\\Local\\\\Programs\\\\Python\\\\Python312\\\\Lib\\\\site-packages\\\\escpos\\\\capabilities.json', 'escpos\\\\capabilities\\\\'), ('c:\\\\USERS\\\\SHU73\\\\APPDATA\\\\LOCAL\\\\MICROSOFT\\\\WINDOWS\\\\FONTS\\\\GENSENROUNDED-H.TTC','fonts'),('c:\\\\USERS\\\\SHU73\\\\APPDATA\\\\LOCAL\\\\MICROSOFT\\\\WINDOWS\\\\FONTS\\\\GENSENROUNDED-L.TTC','fonts'),('c:\\\\USERS\\\\SHU73\\\\APPDATA\\\\LOCAL\\\\MICROSOFT\\\\WINDOWS\\\\FONTS\\\\GENSENROUNDED-M.TTC','fonts'),('c:\\\\USERS\\\\SHU73\\\\APPDATA\\\\LOCAL\\\\MICROSOFT\\\\WINDOWS\\\\FONTS\\\\GENSENROUNDED-R.TTC','fonts'),('c:\\\\USERS\\\\SHU73\\\\APPDATA\\\\LOCAL\\\\MICROSOFT\\\\WINDOWS\\\\FONTS\\\\GENSENROUNDED-B.TTC','fonts'),('c:\\\\USERS\\\\SHU73\\\\APPDATA\\\\LOCAL\\\\MICROSOFT\\\\WINDOWS\\\\FONTS\\\\GENSENROUNDED-EL.TTC','fonts')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='QRcodeScan',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='QRcodeScan',
)