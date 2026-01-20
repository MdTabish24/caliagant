@echo off
echo ============================================================
echo Cleaning Unnecessary Files
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/5] Removing build artifacts...
if exist "pc_agent\build" rmdir /s /q "pc_agent\build"
if exist "pc_agent\dist" rmdir /s /q "pc_agent\dist"
if exist "pc_agent\*.spec" del /q "pc_agent\*.spec"
if exist "pc_agent\__pycache__" rmdir /s /q "pc_agent\__pycache__"

echo [2/5] Removing logs...
if exist "pc_agent\*.log" del /q "pc_agent\*.log"
if exist "*.log" del /q "*.log"

echo [3/5] Removing reports...
if exist "pc_agent\reports" rmdir /s /q "pc_agent\reports"

echo [4/5] Removing temp files...
if exist "pc_agent\platform-tools" rmdir /s /q "pc_agent\platform-tools"
if exist "pc_agent\adb.exe" del /q "pc_agent\adb.exe"
if exist "pc_agent\AdbWinApi.dll" del /q "pc_agent\AdbWinApi.dll"
if exist "pc_agent\AdbWinUsbApi.dll" del /q "pc_agent\AdbWinUsbApi.dll"
if exist "gradle-temp" rmdir /s /q "gradle-temp"
if exist "gradle-temp.zip" del /q "gradle-temp.zip"
if exist "gradle-8.2-bin.zip" del /q "gradle-8.2-bin.zip"

echo [5/5] Removing test files...
if exist "pc_agent\test_*.py" del /q "pc_agent\test_*.py"
if exist "pc_agent\*_test.py" del /q "pc_agent\*_test.py"
if exist "pc_agent\edge_test.mp3" del /q "pc_agent\edge_test.mp3"
if exist "pc_agent\gtts_test.mp3" del /q "pc_agent\gtts_test.mp3"
if exist "edge_test.mp3" del /q "edge_test.mp3"
if exist "pyttsx3_test.mp3" del /q "pyttsx3_test.mp3"
if exist "test_pyttsx3.py" del /q "test_pyttsx3.py"
if exist "debug_output.txt" del /q "debug_output.txt"

echo.
echo ============================================================
echo CLEANUP COMPLETE!
echo.
echo Deleted:
echo   - Build artifacts (dist, build, __pycache__)
echo   - Logs (*.log)
echo   - Reports (Excel files)
echo   - Temp files (ADB, gradle)
echo   - Test files
echo.
echo Ready for Git push!
echo ============================================================
pause
