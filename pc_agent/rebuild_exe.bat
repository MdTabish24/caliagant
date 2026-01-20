@echo off
echo ============================================================
echo Rebuilding Calling Agent EXE
echo ============================================================
echo.

echo [1/2] Cleaning old build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist CallingAgent.spec del CallingAgent.spec

echo.
echo [2/2] Building new EXE...
pyinstaller --onefile --windowed --name=CallingAgent --icon=NONE --add-data=".;." --hidden-import=openpyxl --hidden-import=sounddevice --hidden-import=soundfile --hidden-import=edge_tts --hidden-import=speech_recognition --hidden-import=openai gui_app.py

echo.
echo ============================================================
echo BUILD COMPLETE!
echo.
echo EXE location: dist\CallingAgent.exe
echo.
echo Ab CallingAgent.exe double-click karo!
echo ============================================================
pause
