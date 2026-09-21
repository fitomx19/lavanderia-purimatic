; Inno Setup 6 — instalador completo para máquinas de tienda (sin Python).
;
; Antes de compilar este script, en la máquina de desarrollo:
;   0) cd frontend\lavanderia-frontend && npm install && npm run build
;   1) En la raíz del repo:     pyinstaller --noconfirm --clean purimatic.spec
;   2) En nfc-service (con pyscard instalado en ese Python):
;         pip install -r nfc-service\requirements.txt
;         cd nfc-service
;         pyinstaller --noconfirm --clean --distpath dist --workpath build nfc-service.spec
;   3) Abre este archivo con Inno Setup Compiler y pulsa Build.
;
; El instalador se escribe en dist-installer\Purimatic-Setup.exe
; Instala en %LOCALAPPDATA%\Purimatic (no necesita administrador)
; para que el asistente pueda guardar el .env de esa tienda.
;
; Incluye:
;   - API principal (puerto 5000) + frontend React + asistente de MongoDB Atlas
;   - Puente NFC ACR122U + ESP32 (puerto 5001, POST /send-to-esp32)

#define MyAppName "Lavanderia Purimatic"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Purimatic"
#define MyAppExeName "Purimatic.exe"
#define MyNfcExeName "PurimaticNFC.exe"

[Setup]
AppId={{8F3A2B91-4C6E-4D17-A9B2-7E1C5D8F0A33}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Purimatic
DefaultGroupName={#MyAppName}
PrivilegesRequired=lowest
OutputDir=..\dist-installer
OutputBaseFilename=Purimatic-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=no
UninstallDisplayName={#MyAppName}
SetupLogging=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear icono en el escritorio"; GroupDescription: "Accesos directos:"
Name: "autostart"; Description: "Iniciar Purimatic al iniciar sesión de Windows"; GroupDescription: "Inicio automático:"; Flags: checkedonce

[Files]
; API principal (PyInstaller onedir)
Source: "..\dist\Purimatic\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Puente NFC + ESP32 (PyInstaller onedir)
Source: "..\nfc-service\dist\PurimaticNFC\*"; DestDir: "{app}\nfc-service"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\.env.example"; DestDir: "{app}"; Flags: ignoreversion
; El .env real NO se instala: lo crea el asistente al primer arranque.

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Puente NFC y ESP32"; Filename: "{app}\nfc-service\{#MyNfcExeName}"
Name: "{group}\Reconfigurar MongoDB Atlas"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--setup"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\Purimatic API"; Filename: "{app}\{#MyAppExeName}"; Tasks: autostart
Name: "{userstartup}\Purimatic NFC ESP32"; Filename: "{app}\nfc-service\{#MyNfcExeName}"; Tasks: autostart

[Run]
Filename: "{app}\nfc-service\{#MyNfcExeName}"; Description: "Iniciar puente NFC y ESP32"; Flags: nowait postinstall skipifsilent
Filename: "{app}\{#MyAppExeName}"; Description: "Iniciar Purimatic y configurar MongoDB Atlas de esta tienda"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Borra el .env de esta máquina al desinstalar
Type: files; Name: "{app}\.env"
Type: files; Name: "{app}\nfc-service\.env"
