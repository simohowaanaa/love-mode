@echo off
chcp 65001 >nul

python "%~dp0love_mode.py"

echo.
echo (En cas de souci : python love_mode.py --restore)
pause
