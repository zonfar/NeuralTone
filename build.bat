@echo off
rem Builds dist\NeuralTone.exe (single file, no console window).
rem Custom icon: drop your own icon.ico next to this file before building
rem (delete the generated one, or edit make_icon.py).
setlocal
cd /d "%~dp0"

if not exist .venv (
    python -m venv .venv || goto :fail
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul
pip install -r requirements.txt || goto :fail

if not exist icon.ico (
    python make_icon.py || goto :fail
)

pyinstaller --noconfirm --clean --onefile --noconsole ^
    --name NeuralTone ^
    --icon icon.ico ^
    --add-data "icon.ico;." ^
    --exclude-module PySide6.QtWebEngineCore ^
    --exclude-module PySide6.QtQml ^
    --exclude-module PySide6.QtQuick ^
    main.py || goto :fail

echo.
echo Done: %~dp0dist\NeuralTone.exe
exit /b 0

:fail
echo Build failed.
exit /b 1
