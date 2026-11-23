@echo off
REM ======================================================================
REM  build_windows.bat  -  ONE command that builds the Windows installer.
REM
REM      build_windows.bat
REM
REM  Output:  Installers\SuperSearch-<version>-Windows-Setup.exe   <- share this
REM  The user double-clicks it, clicks Next, and the app is installed.
REM
REM  Run this on a WINDOWS PC, in the project folder. Needs:
REM    - Python 3.11 (python.org, "Add to PATH")           -> creates the build venv
REM    - Inno Setup 6   (winget install JRSoftware.InnoSetup)
REM    - the face model downloaded once: run the app once so
REM      %USERPROFILE%\.insightface\models\buffalo_l exists
REM ======================================================================
setlocal enableextensions
cd /d "%~dp0"
set /p VERSION=<VERSION
set STAGE=Installers\_stage

echo ==> Building Super Search Desktop %VERSION% for Windows

if not exist .venv\Scripts\python.exe (
  echo ==> Creating build environment...
  py -3.11 -m venv .venv || python -m venv .venv || goto :fail
  .venv\Scripts\python -m pip install --upgrade pip || goto :fail
  .venv\Scripts\python -m pip install -r requirements_desktop.txt || goto :fail
)
set VPY=.venv\Scripts\python.exe
for /f "delims=" %%i in ('%VPY% -c "import sys;print(sys.base_prefix)"') do set CPY=%%i
for /f "delims=" %%i in ('%VPY% -c "import sysconfig;print(sysconfig.get_paths()['purelib'])"') do set SP=%%i
set IF=%USERPROFILE%\.insightface\models\buffalo_l
if not exist "%IF%" ( echo ERROR: face model not found at %IF% - run the app once. & goto :fail )

set ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe
if not exist "%ISCC%" set ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe
if not exist "%ISCC%" ( echo ERROR: Inno Setup 6 not found. Install: winget install JRSoftware.InnoSetup & goto :fail )

echo ==> Icon
%VPY% -c "from PIL import Image; Image.open('webui/logo.png').convert('RGBA').save('packaging/icon.ico', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])" || goto :fail

echo ==> Staging
if exist "%STAGE%" rmdir /s /q "%STAGE%"
mkdir "%STAGE%\app" "%STAGE%\runtime"
robocopy . "%STAGE%\app" /E /NFL /NDL /NJH /NJS /XD .venv .git .appwindow Installers packaging cache __pycache__ inputs output bin temp_frames temp_annotated "Mac Exif Tools" /XF *.db *.db-wal *.db-shm *.log app_state.json *.zip *.command *.sh build_windows.bat .env README.txt "Player Recognition Model V1.joblib" "Player Recognition Model V2.joblib" "Player Recognition Model V3*.joblib" "Correction Model V*.joblib" face_corrections.npz >nul
if errorlevel 8 goto :fail
copy /y .env.template "%STAGE%\app\.env.template" >nul
powershell -NoProfile -Command "(Get-Content .env.template) -replace '^GEMINI_API_KEYS=.*','GEMINI_API_KEYS=' | Set-Content '%STAGE%\app\.env'"

echo ==> Bundling Python + libraries (this takes a few minutes)
robocopy "%CPY%" "%STAGE%\runtime\cpython" /E /NFL /NDL /NJH /NJS /XD __pycache__ >nul
if errorlevel 8 goto :fail
robocopy "%SP%" "%STAGE%\runtime\site-packages" /E /NFL /NDL /NJH /NJS /XD __pycache__ pip >nul
if errorlevel 8 goto :fail
robocopy "%IF%" "%STAGE%\app\models\insightface\models\buffalo_l" /E /NFL /NDL /NJH /NJS >nul
if errorlevel 8 goto :fail
copy /y packaging\launcher.vbs "%STAGE%\launcher.vbs" >nul

echo ==> Building installer
"%ISCC%" /Qp /DAppVersion=%VERSION% packaging\installer.iss || goto :fail
rmdir /s /q "%STAGE%"
echo.
echo DONE  -^>  Installers\SuperSearch-%VERSION%-Windows-Setup.exe
exit /b 0

:fail
echo.
echo BUILD FAILED
exit /b 1
