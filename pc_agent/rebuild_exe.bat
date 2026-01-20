@echo off
echo ============================================================
echo Rebuilding Calling Agent EXE (Complete Clean Build)
echo ============================================================
echo.

echo [1/4] Cleaning old build files...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist CallingAgent.spec del CallingAgent.spec
if exist __pycache__ rmdir /s /q __pycache__

echo.
echo [2/4] Cleaning Python cache files...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
del /s /q *.pyc 2>nul

echo.
echo [3/4] Cleaning old reports/results folders...
if exist reports rmdir /s /q reports
if exist results rmdir /s /q results

echo.
echo [4/4] Building new EXE with fresh code...
pyinstaller --onefile --windowed --name=CallingAgent --icon=NONE --add-data=".;." --hidden-import=openpyxl --hidden-import=sounddevice --hidden-import=soundfile --hidden-import=edge_tts --hidden-import=speech_recognition --hidden-import=openai --clean gui_app.py

echo.
echo ============================================================
echo BUILD COMPLETE!
echo.
echo EXE location: dist\CallingAgent.exe
echo.
echo Ab CallingAgent.exe double-click karo!
echo Results folder automatically create hoga jab call hogi.
echo ============================================================
pause
