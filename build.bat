@echo off
chcp 65001 >nul
echo ========================================================
echo   Antigravity-ZH Local Build Utility
echo ========================================================
echo.
python scripts\build.py
if errorlevel 1 (
    echo.
    echo [!] Build failed. Please ensure Python and PyInstaller are installed:
    echo     pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)
echo.
pause
