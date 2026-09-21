# -*- mode: python ; coding: utf-8 -*-
# Empaqueta la API Flask + SocketIO + frontend React en un .exe sin Python.
#
# En la máquina de desarrollo:
#   cd frontend/lavanderia-frontend && npm install && npm run build
#   pip install pyinstaller
#   pyinstaller --noconfirm --clean purimatic.spec
#
# El resultado queda en dist\Purimatic\

import os
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

# Frontend React (npm run build en frontend/lavanderia-frontend)
frontend_dist = os.path.join('frontend', 'lavanderia-frontend', 'dist')
if os.path.isdir(frontend_dist) and os.path.isfile(os.path.join(frontend_dist, 'index.html')):
    datas.append((frontend_dist, 'frontend'))
else:
    print(
        'AVISO: no está frontend/lavanderia-frontend/dist. '
        'Antes de pyinstaller: cd frontend/lavanderia-frontend && npm install && npm run build'
    )

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['gevent', 'geventwebsocket', 'eventlet'],
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
