@echo off
REM ============================================================
REM  Start real-time face recognition from webcam
REM  Press q to quit, s to save snapshot to snapshots/
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

if not exist "face_db.npz" (
    echo [!] face_db.npz not found. Put photos in known_faces\NAME\
    echo     then run scripts\run_register.bat first.
    pause
    exit /b 1
)

echo Opening camera... (press q to quit, s to snapshot)
echo.
python face_recog.py run --cam 0
endlocal
