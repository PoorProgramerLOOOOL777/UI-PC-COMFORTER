@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
pyinstaller --noconfirm --windowed --name "PC Comforter" --add-data "assets;assets" app.py
echo Ejecutable creado en dist\PC Comforter
pause
