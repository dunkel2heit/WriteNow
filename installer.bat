@echo off
title Notch Installer
echo.
echo  Installing Notch...
echo  -------------------
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  Python not found. Please install Python from https://www.python.org/downloads/
    echo  Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo  Python found.
echo.
echo  Installing dependencies...
pip install PyQt5 --quiet
if %errorlevel% neq 0 (
    echo  Failed to install PyQt5. Try running as administrator.
    pause
    exit /b 1
)

echo  Dependencies installed.
echo.
echo  Creating shortcut on Desktop...

set SCRIPT_DIR=%~dp0
set DESKTOP=%USERPROFILE%\Desktop
set SHORTCUT=%DESKTOP%\Notch.lnk

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = 'pythonw.exe'; $s.Arguments = '\"%SCRIPT_DIR%notch.py\"'; $s.WorkingDirectory = '%SCRIPT_DIR%'; $s.IconLocation = '%SCRIPT_DIR%assets\logo.ico'; $s.Save()"

echo  Shortcut created on Desktop.
echo.
echo  ----------------------------------------
echo   Notch installed successfully!
echo   Launch it from your Desktop shortcut.
echo  ----------------------------------------
echo.
pause