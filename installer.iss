; سكريبت Inno Setup لبناء برنامج تثبيت (Installer) لنظام أرشفة الكتب الرسمية
; لبناء المثبت: افتح هذا الملف ببرنامج Inno Setup Compiler (على ويندوز) واضغط Build
; أو استخدمه تلقائيًا عبر GitHub Actions الموجود في .github/workflows/build-windows.yml

#define MyAppName "نظام الأرشيف الرسمي"
#define MyAppVersion "1.0"
#define MyAppExeName "الأرشيف_الرسمي.exe"

[Setup]
AppId={{B7B0B9C4-4E1E-4C6E-9C6B-ARCHIVE00001}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=تثبيت_الارشيف_الرسمي
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "إنشاء اختصار على سطح المكتب"; GroupDescription: "اختصارات إضافية:"

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\إلغاء التثبيت"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "تشغيل البرنامج الآن"; Flags: nowait postinstall skipifsilent
