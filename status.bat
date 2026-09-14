@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title Antigravity 汉化状态检查

if exist "%~dp0antigravity-zh.exe" (
    "%~dp0antigravity-zh.exe" status
    goto :end
)

set "PYTHON_EXE=python"
where python >nul 2>nul
if %errorlevel% neq 0 (
    if exist "D:\miniconda3\python.exe" (
        set "PYTHON_EXE=D:\miniconda3\python.exe"
    )
)

"%PYTHON_EXE%" "%~dp0scripts\patcher.py" status

:end
echo.
pause
