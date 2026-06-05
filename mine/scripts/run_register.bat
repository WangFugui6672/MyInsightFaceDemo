@echo off
REM ============================================================
REM  Register face database from known_faces\ folder
REM  Run this on first use, or after adding/removing people
REM ============================================================
chcp 65001 >nul
setlocal
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

cd /d "%~dp0.."

python -c "import insightface, cv2, onnxruntime" 2>nul
if errorlevel 1 (
    echo [!] Dependencies not installed. Please run scripts\setup.bat first.
    pause
    exit /b 1
)

echo Registering faces from known_faces\ ...
echo.
python face_recog.py register
echo.
pause
endlocal
