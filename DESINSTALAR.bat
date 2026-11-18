@echo off
cd /d "%~dp0"
del "%USERPROFILE%\Desktop\PC Comforter.lnk" 2>nul
rmdir /s /q .venv 2>nul
rmdir /s /q models 2>nul
echo Se quitaron el entorno, modelo y acceso directo.
echo Tus ajustes config.json y avatar se conservan.
pause
