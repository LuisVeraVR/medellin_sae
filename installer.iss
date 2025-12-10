; Script de instalación Inno Setup para MedellinSAE
; Para compilar este script, necesitas Inno Setup instalado:
; https://jrsoftware.org/isinfo.php

#define MyAppName "Medellin SAE"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "MedellinSAE"
#define MyAppExeName "MedellinSAE.exe"
#define MyAppAssocName MyAppName + " File"
#define MyAppAssocExt ".sae"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt

[Setup]
; Información de la aplicación
AppId={{8F3B5D2E-1A4C-4B7E-9D2F-6C8E5A3B7D9F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Archivos de salida
OutputDir=installer_output
OutputBaseFilename=MedellinSAE_Setup_v{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

; Privilegios
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; Icono del instalador (si existe)
;SetupIconFile=icon.ico

; Información de versión
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} Installer
VersionInfoCopyright=Copyright (C) 2024 {#MyAppPublisher}

; Licencia (opcional)
;LicenseFile=LICENSE.txt

; Información adicional
;InfoBeforeFile=README.txt
;InfoAfterFile=CHANGES.txt

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Ejecutable principal
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Archivos de configuración (se crearán en la primera ejecución)
; Los archivos config se copiarán al directorio de datos del usuario

; Documentación
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion; DestName: "LEAME.txt"
Source: "version.txt"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
; Crear directorios necesarios en el directorio de la aplicación
Name: "{app}\config"; Permissions: users-modify
Name: "{app}\data"; Permissions: users-modify
Name: "{app}\output"; Permissions: users-modify
Name: "{app}\logs"; Permissions: users-modify

; Directorios en el perfil del usuario
Name: "{userappdata}\{#MyAppName}"; Permissions: users-modify
Name: "{userappdata}\{#MyAppName}\config"; Permissions: users-modify
Name: "{userappdata}\{#MyAppName}\data"; Permissions: users-modify
Name: "{userappdata}\{#MyAppName}\output"; Permissions: users-modify
Name: "{userappdata}\{#MyAppName}\logs"; Permissions: users-modify

[Icons]
; Accesos directos en el menú de inicio
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Acceso directo en el escritorio
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; Acceso directo en inicio rápido
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

; Accesos directos a carpetas útiles
Name: "{group}\Carpeta de Salida (Output)"; Filename: "{app}\output"
Name: "{group}\Carpeta de Configuración"; Filename: "{app}\config"
Name: "{group}\Logs"; Filename: "{app}\logs"

[Run]
; Ejecutar la aplicación después de la instalación
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Limpiar archivos generados durante el uso
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\data"
Type: filesandordirs; Name: "{app}\output"

[Code]
// Función para verificar si la aplicación está en ejecución
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  // Intentar cerrar la aplicación si está en ejecución
  if CheckForMutexes('MedellinSAE_SingleInstance') then
  begin
    if MsgBox('MedellinSAE está actualmente en ejecución. ¿Desea cerrarlo y continuar con la instalación?',
              mbConfirmation, MB_YESNO) = IDYES then
    begin
      // Aquí podrías agregar código para cerrar la aplicación
      Result := True;
    end
    else
    begin
      Result := False;
    end;
  end
  else
  begin
    Result := True;
  end;
end;

// Función que se ejecuta después de la instalación
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Copiar archivos de configuración por defecto si no existen
    if not FileExists(ExpandConstant('{app}\config\clients.json')) then
    begin
      // Los archivos de configuración se copiarán desde el directorio config incluido
      // en el ejecutable PyInstaller
    end;
  end;
end;
