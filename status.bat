@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title Antigravity 汉化状态检查

if exist "%~dp0antigravity-zh.exe" (
    "%~dp0antigravity-zh.exe" status
    goto :end
)

set "PYTHON_EXE="

where python >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_EXE=python"
    goto :run
)

where py >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_EXE=py"
    goto :run
)

for %%v in (313 312 311 310) do (
    if exist "%LOCALAPPDATA%\Programs\Python\Python%%v\python.exe" (
        set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python%%v\python.exe"
        goto :run
    )
    if exist "%ProgramFiles%\Python%%v\python.exe" (
        set "PYTHON_EXE=%ProgramFiles%\Python%%v\python.exe"
        goto :run
    )
)

:run
if defined PYTHON_EXE (
    "%PYTHON_EXE%" "%~dp0scripts\patcher.py" status
) else (
    python "%~dp0scripts\patcher.py" status
)

:end
echo.
pause
