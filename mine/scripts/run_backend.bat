@echo off
REM ============================================================
REM  Start the recognition backend API server
REM  Visit http://127.0.0.1:8000/ for the dashboard
REM ============================================================
chcp 65001 >nul
setlocal
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

cd /d "%~dp0.."

python -c "import fastapi, uvicorn, multipart, pydantic" 2>nul
if errorlevel 1 (
    echo [!] Backend dependencies not found. Please run scripts\setup.bat first.
    pause
    exit /b 1
)

echo Starting backend...
echo   Dashboard : http://127.0.0.1:8000/
echo   API docs  : http://127.0.0.1:8000/docs
echo   Press CTRL+C to stop
echo.

python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

endlocal
