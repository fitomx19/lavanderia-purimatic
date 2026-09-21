# -*- mode: python ; coding: utf-8 -*-
# Empaqueta el microservicio NFC + puente ESP32 (incluye pyscard/smartcard).
#
# El backend y este puente ambos se llaman "app". Si PyInstaller corre desde
# la raíz del repo, congela el Flask principal (product_routes) y el .exe
# arranca mal. Este spec cambia el cwd a nfc-service y saca la raíz del path.
#
#   pip install -r nfc-service/requirements.txt
# Desde nfc-service (recomendado):
#   pyinstaller --noconfirm --clean --distpath dist --workpath build nfc-service.spec
# Desde la raíz del repo:
#   pyinstaller --noconfirm --clean --distpath nfc-service\dist --workpath nfc-service\build nfc-service\nfc-service.spec
#
# Salida: nfc-service/dist/PurimaticNFC/PurimaticNFC.exe
# NO ejecutes dist\PurimaticNFC de la raíz (eso es otro build) ni un .exe viejo.

import os
import sys
import glob
import smartcard
from PyInstaller.utils.hooks import collect_all, collect_submodules

SPEC_ROOT = os.path.dirname(os.path.abspath(SPEC))
REPO_ROOT = os.path.dirname(SPEC_ROOT)

os.chdir(SPEC_ROOT)

try:
    import PyInstaller.config
    PyInstaller.config.CONF['distpath'] = os.path.join(SPEC_ROOT, 'dist')
    PyInstaller.config.CONF['workpath'] = os.path.join(SPEC_ROOT, 'build')
except Exception:
    pass

_repo_norm = os.path.normcase(os.path.abspath(REPO_ROOT))
_filtered = []
for p in sys.path:
    try:
        resolved = os.path.normcase(os.path.abspath(p))
    except Exception:
        _filtered.append(p)
        continue
    if resolved != _repo_norm:
        _filtered.append(p)
sys.path[:] = _filtered
if SPEC_ROOT not in sys.path:
    sys.path.insert(0, SPEC_ROOT)

datas = []
binaries = []
hiddenimports = [
    'flask',
    'flask_cors',
    'dotenv',
    'requests',
    'urllib3',
    'certifi',
    'charset_normalizer',
    'idna',
    'colorama',
    'app',
    'app.config',
    'app.nfc_manager',
    'app.esp32_manager',
    'app.routes',
    'app.routes.nfc_routes',
    'app.routes.esp32_routes',
    'app.utils',
    'app.utils.logger',
    'app.utils.response_utils',
    'app.exceptions',
    'app.exceptions.nfc_exceptions',
    'smartcard',
    'smartcard.scard',
    'smartcard.scard._scard',
    'smartcard.System',
    'smartcard.CardMonitoring',
    'smartcard.util',
    'smartcard.Exceptions',
    'smartcard.CardConnection',
    'smartcard.CardRequest',
    'smartcard.Observer',
    'smartcard.ExclusiveConnectCardConnection',
    'smartcard.pcsc',
    'smartcard.reader',
    'smartcard.guid',
    'smartcard.ulist',
]

for pkg in ('flask', 'flask_cors', 'requests', 'colorama', 'dotenv', 'smartcard'):
    collected_datas, collected_binaries, collected_hidden = collect_all(pkg)
    datas += collected_datas
    binaries += collected_binaries
    hiddenimports += collected_hidden

hiddenimports += collect_submodules('smartcard')

_smartcard_dir = os.path.dirname(smartcard.__file__)
_site_packages = os.path.dirname(_smartcard_dir)
datas.append((_smartcard_dir, 'smartcard'))
datas.append((os.path.join(SPEC_ROOT, 'app'), 'app'))

for path in glob.glob(os.path.join(_smartcard_dir, '**', '*.pyd'), recursive=True):
    dest = os.path.relpath(os.path.dirname(path), _site_packages)
    binaries.append((path, dest))
for path in glob.glob(os.path.join(_smartcard_dir, '**', '*.dll'), recursive=True):
    dest = os.path.relpath(os.path.dirname(path), _site_packages)
    binaries.append((path, dest))

print('SPEC_ROOT:', SPEC_ROOT)
print('cwd de PyInstaller:', os.getcwd())
print('pyscard/smartcard en:', _smartcard_dir)
print('binarios nativos pyscard:', [b[0] for b in binaries if 'scard' in b[0].lower()])

a = Analysis(
    [os.path.join(SPEC_ROOT, 'main.py')],
    pathex=[SPEC_ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['IPython', 'jupyter', 'notebook'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PurimaticNFC',
    debug=False,
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
    name='PurimaticNFC',
)
