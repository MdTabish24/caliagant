@echo off
echo ========================================
echo    AI CALLING AGENT - STARTING
echo ========================================
echo.

:: Check if Ollama is running
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Starting Ollama server...
    start /min ollama serve
    timeout /t 5 >nul
)

echo [OK] Ollama running
echo.
echo [INFO] Starting Calling Agent...
echo.

python main.py

pause
