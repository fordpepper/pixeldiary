# diary.spec
import sys

block_cipher = None

a = Analysis(
    ['diary.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets')],
    hiddenimports=['tkinter', '_tkinter'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PixelDiary',
    debug=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon=None,
)

# macOS: wrap in a .app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='PixelDiary.app',
        bundle_identifier='com.pixeldiary',
    )
