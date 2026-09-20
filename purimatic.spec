# -*- mode: python ; coding: utf-8 -*-
# Empaqueta la API Flask + SocketIO en un .exe que no necesita Python.
#
# En la máquina de desarrollo (sí tiene Python):
#   pip install pyinstaller
#   pyinstaller --noconfirm --clean purimatic.spec
#
# El resultado queda en dist\Purimatic\  (carpeta, no un solo archivo:
# así Flask/SocketIO y dnspython fallan menos que en modo onefile).

from PyInstaller.utils.hooks import collect_all, collect_submodules

datas = []
binaries = []
hiddenimports = [
    'engineio.async_drivers.threading',
    'flask_socketio',
    'socketio',
    'engineio',
    'pymongo',
    'dns',
    'dns.resolver',
    'apscheduler',
    'apscheduler.schedulers.background',
    'apscheduler.triggers.interval',
    'bcrypt',
    'flask_jwt_extended',
    'flask_cors',
    'marshmallow',
    'dotenv',
    'setup_wizard',
    'config',
]

for pkg in ('flask', 'flask_socketio', 'engineio', 'socketio', 'pymongo', 'dns', 'apscheduler'):
    try:
        collected_datas, collected_binaries, collected_hidden = collect_all(pkg)
        datas += collected_datas
        binaries += collected_binaries
        hiddenimports += collected_hidden
    except Exception:
        pass

hiddenimports += collect_submodules('app')

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='Purimatic',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
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
    upx=True,
    upx_exclude=[],
    name='Purimatic',
)
