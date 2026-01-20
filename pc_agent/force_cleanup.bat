@echo off
echo ============================================================
echo Force Cleanup - PyInstaller Cache and Temp Files
echo ============================================================
echo.

echo [1/5] Stopping all Python and CallingAgent processes...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM pythonw.exe 2>nul
taskkill /F /IM CallingAgent.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo [2/5] Cleaning local build files...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__
del /s /q *.pyc 2>nul
del CallingAgent.spec 2>nul

echo.
echo [3/5] Cleaning PyInstaller temp cache from AppData...
set TEMP_DIR=%LOCALAPPDATA%\Temp
echo Cleaning: %TEMP_DIR%\_MEI*
for /d %%d in ("%TEMP_DIR%\_MEI*") do (
    echo Removing: %%d
    rmdir /s /q "%%d" 2>nul
)

echo.
echo [4/5] Cleaning old reports/results folders...
if exist reports rmdir /s /q reports
if exist results rmdir /s /q results

echo.
echo [5/5] Cleaning Windows temp files...
del /q "%TEMP%\tts_output.mp3" 2>nul
del /q "%TEMP%\speech_*.wav" 2>nul

echo.
echo ============================================================
echo CLEANUP COMPLETE!
echo.
echo Ab rebuild_exe.bat run karo
echo ============================================================
pause
