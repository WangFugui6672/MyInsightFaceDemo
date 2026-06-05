@echo off
REM ============================================================
REM  Face recognition demo - first-time dependency install
REM  Run this once, then use run_*.bat
REM ============================================================
chcp 65001 >nul
setlocal

echo.
echo ============================================================
echo  Face Recognition Demo - Installing dependencies
echo ============================================================
echo.

REM 1) Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [X] Python not found. Please install Python 3.10+ first.
    echo     Download: https://www.python.org/downloads/
    echo     Important: check "Add Python to PATH" during install
    pause
    exit /b 1
)
echo [OK] Python detected
python --version
echo.

REM 2) Upgrade pip
echo [1/2] Upgrading pip ...
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet
if errorlevel 1 (
    echo [!] Tsinghua mirror failed, trying default PyPI ...
    python -m pip install --upgrade pip --quiet
)
echo.

REM 3) Install dependencies
echo [2/2] Installing dependencies (insightface / opencv / onnxruntime-directml / numpy)...
python -m pip install -r "%~dp0..\requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo.
    echo [!] Tsinghua mirror failed, trying default PyPI ...
    python -m pip install -r "%~dp0..\requirements.txt"
)
if errorlevel 1 (
    echo.
    echo [X] Install failed. Please check your network and try again.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  [OK] Installation complete
echo  Next step: double-click scripts\run_camera.bat to start camera
echo ============================================================
pause
endlocal
