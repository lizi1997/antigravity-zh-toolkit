@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title Antigravity 现代化汉化补丁安装器

echo ========================================================
echo        Antigravity 现代化汉化一键安装器 v1.0.0
echo ========================================================
echo.

if exist "%~dp0antigravity-zh.exe" (
    "%~dp0antigravity-zh.exe" patch --force
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
echo     请安装 Python 3.10+ 或直接从 GitHub Releases 下载预编译的 antigravity-zh.exe：
echo     https://github.com/lizi1997/antigravity-zh-toolkit/releases
pause
exit /b 1

:run
"%PYTHON_EXE%" "%~dp0scripts\patcher.py" patch --force

:end
echo.
pause
