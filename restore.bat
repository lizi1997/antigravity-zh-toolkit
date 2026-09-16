@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title Antigravity 官方原版一键还原器

echo ========================================================
echo         Antigravity 官方原版一键还原器
echo ========================================================
echo.

if exist "%~dp0antigravity-zh.exe" (
    "%~dp0antigravity-zh.exe" restore
    set "RESULT=!errorlevel!"
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
    if exist "C:\Python%%v\python.exe" (
        set "PYTHON_EXE=C:\Python%%v\python.exe"
        goto :run
    )
)

echo [!] 错误：未检测到 Python 环境或编译版程序。
pause
exit /b 1

:run
"%PYTHON_EXE%" "%~dp0scripts\patcher.py" restore
set "RESULT=%errorlevel%"

:end
echo.
pause
exit /b %RESULT%
