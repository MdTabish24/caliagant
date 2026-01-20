@echo off
echo ============================================================
echo Calling Agent - Complete Setup for New PC
echo ============================================================
echo.

echo [1/5] Installing Python dependencies...
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install dependencies!
    echo Make sure Python is installed and added to PATH.
    pause
    exit /b 1
)

echo.
echo [2/5] Cleaning old build files...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__
del /s /q *.pyc 2>nul
del CallingAgent.spec 2>nul

echo.
echo [3/5] Creating results folder...
if not exist results mkdir results

echo.
echo [4/5] Building EXE...
pyinstaller --onefile --windowed --name=CallingAgent --icon=NONE --add-data=".;." --hidden-import=openpyxl --hidden-import=sounddevice --hidden-import=soundfile --hidden-import=edge_tts --hidden-import=speech_recognition --hidden-import=openai --clean gui_app.py

if errorlevel 1 (
    echo.
    echo ERROR: Failed to build EXE!
    pause
    exit /b 1
)

echo.
echo [5/5] Copying ADB files to dist folder...
copy adb.exe dist\ 2>nul
copy AdbWinApi.dll dist\ 2>nul
copy AdbWinUsbApi.dll dist\ 2>nul

echo.
echo ============================================================
echo SETUP COMPLETE!
echo ============================================================
echo.
echo Next Steps:
echo 1. Copy api_key.txt.example to api_key.txt
echo 2. Add your OpenAI API key in api_key.txt
echo 3. Run: dist\CallingAgent.exe
echo.
echo EXE Location: dist\CallingAgent.exe
echo Results will be saved in: dist\results\
echo ============================================================
pause
