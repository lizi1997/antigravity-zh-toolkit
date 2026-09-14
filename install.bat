@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title Antigravity 现代化汉化补丁安装器

echo ========================================================
echo        Antigravity 现代化汉化一键安装器 v3.2
echo ========================================================
echo.

if exist "%~dp0antigravity-zh.exe" (
    "%~dp0antigravity-zh.exe" patch --force
    goto :end
)

set "PYTHON_EXE=python"
where python >nul 2>nul
if %errorlevel% neq 0 (
    if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
        set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    ) else if exist "D:\miniconda3\python.exe" (
        set "PYTHON_EXE=D:\miniconda3\python.exe"
    ) else (
        echo [!] 错误：未检测到 Python 环境或编译版程序。
        echo     请安装 Python 3.10+ 或直接从 GitHub Releases 下载预编译的 antigravity-zh.exe。
        pause
        exit /b 1
    )
)

"%PYTHON_EXE%" "%~dp0scripts\patcher.py" patch --force

:end
echo.
pause
