@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

echo ============================================================
echo Hearlium Phase 3 - Inno Setup Only - Short Path Retry
echo ============================================================
echo This uses the existing dist folder. It does NOT rebuild Python,
echo redownload models, or change saved caregiver decisions.
echo.

if not exist "dist\HearliumParentPC\HearliumParentPC.exe" (
  echo ERROR: The frozen Parent PC executable was not found.
  echo Expected: dist\HearliumParentPC\HearliumParentPC.exe
  echo Run BUILD_HEARLIUM_INSTALLER.bat first if the executable is missing.
  pause
  exit /b 1
)
if not exist "installer\prereqs\vc_redist.x64.exe" (
  echo ERROR: Bundled VC++ prerequisite is missing.
  echo Run the full installer builder to stage this file.
  pause
  exit /b 1
)

set "ISCC="
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC (
  where iscc >nul 2>&1
  if not errorlevel 1 set "ISCC=iscc"
)
if not defined ISCC (
  echo ERROR: Inno Setup 6 compiler not found.
  pause
  exit /b 1
)

REM Shorten the *compiler's* source paths. Deep PyTorch include filenames
REM can exceed traditional Windows path limits if the ZIP was extracted
REM into a long directory name. Use an unused temporary SUBST drive.
set "SHORTDRIVE="
for %%D in (H Q R S T W X Y Z) do (
  if not defined SHORTDRIVE (
    if not exist "%%D:\" (
      subst %%D: "%CD%" >nul 2>&1
      if not errorlevel 1 set "SHORTDRIVE=%%D:"
    )
  )
)

if not defined SHORTDRIVE (
  echo ERROR: Could not create a short temporary drive path with SUBST.
  echo Move the entire extracted project to a short folder such as C:\H3
  echo and run this script from there.
  pause
  exit /b 1
)

echo Using temporary short build drive !SHORTDRIVE!\
echo Original project: %CD%
echo Building installer from existing executable...
echo.

REM Run in the mapped drive so even the compiler's working directory is short.
pushd "!SHORTDRIVE!\" >nul 2>&1
if errorlevel 1 (
  echo ERROR: Cannot enter temporary drive !SHORTDRIVE!
  subst !SHORTDRIVE! /D >nul 2>&1
  pause
  exit /b 1
)
"%ISCC%" "!SHORTDRIVE!\installer\Hearlium.iss"
set "COMPILER_RC=!ERRORLEVEL!"
popd

REM Always remove our temporary mapping once the compiler has finished.
subst !SHORTDRIVE! /D >nul 2>&1

if not "!COMPILER_RC!"=="0" (
  echo.
  echo ERROR: Inno Setup compilation failed with exit code !COMPILER_RC!.
  echo If a short path did not fix it, capture the full red error line.
  echo The existing application build is preserved in dist\HearliumParentPC.
  pause
  exit /b !COMPILER_RC!
)

if not exist "installer\output\HearliumSetup.exe" (
  echo ERROR: Inno returned success but installer\output\HearliumSetup.exe is missing.
  pause
  exit /b 1
)

echo.
echo ============================================================
echo INSTALLER BUILD COMPLETE
 echo ============================================================
echo installer\output\HearliumSetup.exe
 echo The temporary SUBST drive has been removed.
echo.
pause
exit /b 0
