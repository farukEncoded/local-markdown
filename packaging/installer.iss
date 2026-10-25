; Inno Setup 6 script for Local Markdown
; Per-user non-elevated offline Windows installer

#define MyAppName "Local Markdown"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Local Markdown"
#define MyAppURL "https://github.com/local-markdown/local-markdown"
#define MyAppExeName "LocalMarkdown.exe"

[Setup]
; Stable unique GUID for upgrade tracking
AppId={{8FE72EC7-7B0D-48E6-8744-19A32D6E9873}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\Programs\LocalMarkdown
DisableProgramGroupPage=yes
; Per-user install without administrator prompt
PrivilegesRequired=lowest
OutputDir=..\dist_release
OutputBaseFilename=LocalMarkdown-Setup-1.0.0-x64
SetupIconFile=..\src\local_markdown\resources\app.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/normal
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\LocalMarkdown\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
