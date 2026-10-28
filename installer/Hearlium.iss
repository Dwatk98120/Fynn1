#define MyAppName "Hearlium Parent PC"
#define MyAppVersion "0.4.21"
#define MyAppPublisher "Hearlium"
#define MyAppExeName "HearliumParentPC.exe"
; The prerequisite is downloaded by BUILD_HEARLIUM_INSTALLER.bat before ISCC runs.
#define BundledVCRedistVersion GetVersionNumbersString(AddBackslash(SourcePath) + "prereqs\vc_redist.x64.exe")

[Setup]
AppId={{2B39176E-9287-4B42-AC70-58A48F6A7A11}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Hearlium
DefaultGroupName=Hearlium
OutputDir=output
OutputBaseFilename=HearliumSetup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
DisableProgramGroupPage=yes
UninstallDisplayName=Hearlium Parent PC

; The batch builder outputs dist\HearliumParentPC\HearliumParentPC.exe
; and dist\HearliumParentPC\_internal. Copy CONTENTS, not parent folder.
[Files]
Source: "..\dist\HearliumParentPC\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

; Bundle Microsoft Visual C++ runtime required by PyTorch.
Source: "prereqs\vc_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"
Name: "autostart"; Description: "Start Hearlium when I sign in"; GroupDescription: "Startup:"
Name: "installvcruntime"; Description: "Install/update Microsoft Visual C++ x64 runtime (needed on this PC)"; GroupDescription: "Required runtime:"; Check: NeedsVCRuntime

[Icons]
Name: "{autoprograms}\Hearlium Parent PC"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Hearlium Parent PC"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{commonstartup}\Hearlium Parent PC"; Filename: "{app}\{#MyAppExeName}"; Tasks: autostart

[Run]
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall add rule name=""Hearlium Parent PC - managed port 8000"" dir=in action=allow protocol=TCP localport=8000"; Flags: runhidden
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Hearlium Parent PC"; Flags: nowait postinstall skipifsilent; Check: CanLaunchHearlium

[Code]
const
  VCRuntimeKey = 'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64';

var
  VCRuntimeNeedsRestart: Boolean;
  VCRuntimeSkipped: Boolean;

function CompatibleVCRuntimeInstalled: Boolean;
var
  Installed: Cardinal;
  Major, Minor, Bld, Rbld: Cardinal;
  InstalledVersion, BundledVersion: Int64;
begin
  Result := False;
  if not RegQueryDWordValue(HKLM64, VCRuntimeKey, 'Installed', Installed) then Exit;
  if Installed <> 1 then Exit;
  if not RegQueryDWordValue(HKLM64, VCRuntimeKey, 'Major', Major) then Exit;
  if not RegQueryDWordValue(HKLM64, VCRuntimeKey, 'Minor', Minor) then Exit;
  if not RegQueryDWordValue(HKLM64, VCRuntimeKey, 'Bld', Bld) then Exit;
  if not RegQueryDWordValue(HKLM64, VCRuntimeKey, 'Rbld', Rbld) then Exit;
  if (Major > 65535) or (Minor > 65535) or (Bld > 65535) or (Rbld > 65535) then Exit;
  if not StrToVersion('{#BundledVCRedistVersion}', BundledVersion) then Exit;
  InstalledVersion := PackVersionComponents(Word(Major), Word(Minor), Word(Bld), Word(Rbld));
  Result := ComparePackedVersion(InstalledVersion, BundledVersion) >= 0;
end;

function NeedsVCRuntime: Boolean;
begin
  Result := not CompatibleVCRuntimeInstalled;
end;

function CanLaunchHearlium: Boolean;
begin
  Result := not VCRuntimeSkipped and not VCRuntimeNeedsRestart and CompatibleVCRuntimeInstalled;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ExitCode: Integer;
  ExePath: String;
begin
  if CurStep <> ssPostInstall then Exit;
  if not NeedsVCRuntime then Exit;
  if not WizardIsTaskSelected('installvcruntime') then
  begin
    VCRuntimeSkipped := True;
    MsgBox('Hearlium is installed, but the Microsoft Visual C++ x64 runtime is missing or outdated.' + #13#10 +
           'You chose not to install it, so Hearlium will not start automatically.' + #13#10 +
           'Install the official runtime before starting Hearlium.', mbInformation, MB_OK);
    Exit;
  end;
  ExePath := ExpandConstant('{tmp}\vc_redist.x64.exe');
  if not FileExists(ExePath) then
    RaiseException('The bundled Microsoft Visual C++ x64 installer is missing.');
  Log('Installing Visual C++ x64 prerequisite (existing compatible installations are preserved).');
  if not Exec(ExePath, '/install /quiet /norestart', '', SW_HIDE, ewWaitUntilTerminated, ExitCode) then
    RaiseException('Could not start the Microsoft Visual C++ x64 installer.');
  if (ExitCode = 3010) or (ExitCode = 1641) then
  begin
    VCRuntimeNeedsRestart := True;
    Log('Visual C++ runtime requests restart. Exit code: ' + IntToStr(ExitCode));
  end
  else if ExitCode <> 0 then
    RaiseException('Microsoft Visual C++ x64 setup failed (exit code ' + IntToStr(ExitCode) + ').' + #13#10 +
                   'Hearlium cannot be launched until the prerequisite is available.');
  if not VCRuntimeNeedsRestart and not CompatibleVCRuntimeInstalled then
    RaiseException('Visual C++ setup returned success, but a compatible x64 runtime was not detected.' + #13#10 +
                   'Please check the runtime installation before using Hearlium.');
end;

function NeedRestart: Boolean;
begin
  Result := VCRuntimeNeedsRestart;
end;

[UninstallRun]
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall delete rule name=""Hearlium Parent PC - managed port 8000"""; Flags: runhidden; RunOnceId: "HearliumFirewallRule"

