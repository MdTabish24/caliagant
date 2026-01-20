@echo off
echo ============================================================
echo Calling Agent - New PC Setup
echo ============================================================
echo.

cd /d "%~dp0\pc_agent"

echo [1/5] Installing Python dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)

echo.
echo [2/5] Installing PyInstaller...
python -m pip install pyinstaller
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller!
    pause
    exit /b 1
)

echo.
echo [3/5] Setting up API key...
if not exist "api_key.txt" (
    echo.
    echo ⚠️  API key not found!
    echo Please create api_key.txt with your OpenAI API key
    echo.
    set /p API_KEY="Enter your OpenAI API key: "
    echo !API_KEY! > api_key.txt
    echo ✅ API key saved!
)

echo.
echo [4/5] Downloading ADB...
python download_adb.py
if errorlevel 1 (
    echo WARNING: ADB download failed. Will try to use system ADB.
)

echo.
echo [5/5] Building portable EXE...
call build_portable.bat

echo.
echo ============================================================
echo SETUP COMPLETE!
echo.
echo EXE Location: pc_agent\dist\CallingAgent.exe
echo.
echo To run:
echo   1. Double-click CallingAgent.exe
echo   2. Select audio file
echo   3. Choose mode (AI or Audio Only)
echo   4. Connect phone via USB
echo   5. Start calling!
echo ============================================================
pause
