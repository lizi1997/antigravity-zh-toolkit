@echo off
chcp 65001 >nul
echo ========================================================
echo   Antigravity-ZH Local Build Utility
echo ========================================================
echo.
set "PYTHON_EXE=python"
where python >nul 2>nul
if %errorlevel% neq 0 (
    where py >nul 2>nul
    if %errorlevel% equ 0 (
        set "PYTHON_EXE=py"
    ) else (
        echo [!] Error: no Python found. Install Python 3.10+ first.
        pause
        exit /b 1
    )
)

%PYTHON_EXE% scripts\build.py
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
