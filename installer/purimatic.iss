; Inno Setup 6 — instalador para máquinas de tienda (sin Python).
;
; Antes de compilar este script:
;   1) En la raíz del repo:  pyinstaller --noconfirm --clean purimatic.spec
;   2) Abre este archivo con Inno Setup Compiler y pulsa Build.
;
; El instalador se escribe en dist-installer\Purimatic-Setup.exe
; Instala en %LOCALAPPDATA%\Purimatic (no necesita administrador)
; para que el asistente pueda guardar el .env de esa tienda.

#define MyAppName "Lavanderia Purimatic"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Purimatic"
#define MyAppExeName "Purimatic.exe"

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

[Files]
; Carpeta generada por PyInstaller (onedir)
Source: "..\dist\Purimatic\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\.env.example"; DestDir: "{app}"; Flags: ignoreversion
; El .env real NO se instala: lo crea el asistente al primer arranque.

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Reconfigurar MongoDB Atlas"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--setup"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Iniciar Purimatic y configurar MongoDB Atlas de esta tienda"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Borra el .env de esta máquina al desinstalar
Type: files; Name: "{app}\.env"
