@echo off
echo ============================================================
echo Preparing Portable CallingAgent with ADB
echo ============================================================
echo.

REM Check if ADB files already exist
if exist "adb.exe" (
    echo ADB files found!
    goto BUILD
)

echo ADB not found. Downloading...
echo.
python download_adb.py
if errorlevel 1 (
    echo.
    echo ERROR: Failed to download ADB!
    echo Please download manually from:
    echo https://developer.android.com/studio/releases/platform-tools
    echo.
    echo Extract and copy these 3 files to pc_agent folder:
    echo   - adb.exe
    echo   - AdbWinApi.dll
    echo   - AdbWinUsbApi.dll
    pause
    exit /b 1
)

:BUILD
echo.
echo [1/4] Installing PyInstaller...
python -m pip install pyinstaller
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller!
    pause
    exit /b 1
)

echo.
echo [2/4] Stopping any running CallingAgent...
taskkill /F /IM CallingAgent.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo [3/4] Cleaning old build...
if exist build rmdir /s /q build 2>nul
if exist dist rmdir /s /q dist 2>nul
if exist CallingAgent.spec del CallingAgent.spec 2>nul

echo.
echo [4/4] Building portable EXE with bundled ADB...
pyinstaller --onefile --windowed --name=CallingAgent --icon=NONE ^
    --add-data="adb.exe;." ^
    --add-data="AdbWinApi.dll;." ^
    --add-data="AdbWinUsbApi.dll;." ^
    --hidden-import=openpyxl ^
    --hidden-import=sounddevice ^
    --hidden-import=soundfile ^
    --hidden-import=edge_tts ^
    --hidden-import=speech_recognition ^
    --hidden-import=openai ^
    gui_app.py

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo BUILD COMPLETE!
echo.
echo Portable EXE created: dist\CallingAgent.exe
echo.
echo This EXE can run on ANY Windows PC without ADB installation!
echo ============================================================
pause
