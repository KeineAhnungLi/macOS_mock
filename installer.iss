#define AppName "TEM8 Practice"
#define AppVersion "2026.03.07"
#define AppPublisher "HW"
#define AppExeName "TEM8Practice.exe"

[Setup]
AppId={{0A0C30F0-39A1-4B40-9A4B-335F9F4D77E5}}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={localappdata}\TEM8Practice
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=setup
OutputBaseFilename=TEM8Practice-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#AppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务:"

[Files]
Source: "dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\data\questions.json"; DestDir: "{app}\data"; Flags: ignoreversion
Source: "dist\data\answer_key.json"; DestDir: "{app}\data"; Flags: ignoreversion
Source: "dist\data\answer_key.template.json"; DestDir: "{app}\data"; Flags: ignoreversion
Source: "dist\data\ai_review.template.json"; DestDir: "{app}\data"; Flags: ignoreversion
Source: "dist\data\user_progress.json"; DestDir: "{app}\data"; Flags: ignoreversion onlyifdoesntexist

[Dirs]
Name: "{app}\logs"

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "启动 {#AppName}"; Flags: nowait postinstall skipifsilent
