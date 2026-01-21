@echo off
echo ============================================================
echo Calling Agent - Complete PC Setup (One Command)
echo ============================================================
echo.
echo This will setup everything on new PC:
echo - Install Python dependencies
echo - Build PC Agent EXE
echo - Setup folders
echo - Copy ADB files
echo.
echo Requirements:
echo - Python 3.8+ installed
echo - Internet connection
echo.
pause

cd pc_agent

echo.
echo [1/6] Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Install Python from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo [2/6] Installing Python dependencies...
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)

echo.
echo [3/6] Cleaning old build files...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__
del /s /q *.pyc 2>nul
del CallingAgent.spec 2>nul

echo.
echo [4/6] Creating results folder...
if not exist results mkdir results

echo.
echo [5/6] Building PC Agent EXE...
pyinstaller --onefile --windowed --name=CallingAgent --icon=NONE --add-data=".;." --hidden-import=openpyxl --hidden-import=sounddevice --hidden-import=soundfile --hidden-import=edge_tts --hidden-import=speech_recognition --hidden-import=openai --clean gui_app.py

if errorlevel 1 (
    echo ERROR: Failed to build EXE!
    echo.
    echo You can still run without EXE:
    echo   python gui_app.py
    pause
    exit /b 1
)

echo.
echo [6/6] Copying ADB files to dist folder...
copy adb.exe dist\ 2>nul
copy AdbWinApi.dll dist\ 2>nul
copy AdbWinUsbApi.dll dist\ 2>nul

echo.
echo ============================================================
echo SETUP COMPLETE!
echo ============================================================
echo.
echo PC Agent is ready to use!
echo.
echo Next Steps:
echo 1. Setup OpenAI API Key:
echo    - Copy: pc_agent\api_key.txt.example to api_key.txt
echo    - Edit api_key.txt and add your OpenAI API key
echo.
echo 2. Run PC Agent:
echo    - EXE: pc_agent\dist\CallingAgent.exe
echo    - OR Python: cd pc_agent ^&^& python gui_app.py
echo.
echo 3. Android App:
echo    - APK already in: app\base.apk
echo    - Install: pc_agent\adb.exe install -r app\base.apk
echo.
echo 4. Usage:
echo    - Connect phone via USB (USB debugging ON)
echo    - Run PC Agent
echo    - Select audio file
echo    - Choose mode (AI or Audio Only)
echo    - Start calling from phone app
echo.
echo Results will be saved in: pc_agent\dist\results\
echo ============================================================
pause
