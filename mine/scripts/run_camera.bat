@echo off
REM ============================================================
REM  Start backend + real-time face recognition from webcam
REM  Press q to quit, s to save snapshot to snapshots/
REM ============================================================
chcp 65001 >nul
setlocal
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

cd /d "%~dp0.."

python -c "import insightface, cv2, onnxruntime, uvicorn" 2>nul
if errorlevel 1 (
    echo [!] Dependencies not found. Please run scripts\setup.bat first.
    pause
    exit /b 1
)

if not exist "face_db.npz" (
    echo [!] face_db.npz not found. Put photos in known_faces\NAME\
    echo     then run scripts\run_register.bat first.
    pause
    exit /b 1
)

echo Starting backend server...
powershell -NoLogo -Command "$p = Start-Process -NoNewWindow -PassThru python '-m uvicorn backend.main:app --host 127.0.0.1 --port 8000'; $p.Id | Out-File -Encoding ascii 'backend\data\backend.pid'"

REM wait for backend to be ready
echo Waiting for backend to be ready...
:wait_loop
timeout /t 1 /nobreak >nul
python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" 2>nul
if errorlevel 1 goto wait_loop

echo Backend ready. Opening camera... (press q to quit, s to snapshot)
echo.
python face_recog.py run --cam 0 --api http://127.0.0.1:8000/api/recognitions

echo Stopping backend server...
set /p BACKEND_PID=<backend\data\backend.pid
if defined BACKEND_PID (
    taskkill /F /PID %BACKEND_PID% 2>nul
    del backend\data\backend.pid 2>nul
)
endlocal
