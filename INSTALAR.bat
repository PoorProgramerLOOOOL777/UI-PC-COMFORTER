@echo off
setlocal
cd /d "%~dp0"
title Instalador PC Comforter
echo ===========================================
echo       INSTALADOR - UI-PC-COMFORTER
echo ===========================================
where py >nul 2>nul
if errorlevel 1 (
 echo No se encontro Python. Instala Python 3.10-3.12 desde python.org
 echo y marca "Add Python to PATH".
 pause
 exit /b 1
)
py -3.12 -V >nul 2>nul
if errorlevel 1 (
 py -3.11 -V >nul 2>nul
 if errorlevel 1 (
  py -3.10 -V >nul 2>nul
  if errorlevel 1 (
   echo Se requiere Python 3.10, 3.11 o 3.12.
   pause
   exit /b 1
  )
 )
)
if not exist ".venv" (
 echo Creando entorno...
 py -3.12 -m venv .venv 2>nul
 if errorlevel 1 py -3.11 -m venv .venv 2>nul
 if errorlevel 1 py -3.10 -m venv .venv
)
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
 echo Fallo al instalar dependencias.
 pause
 exit /b 1
)
if not exist "models\vosk-model-small-es-0.42" (
 if not exist "models" mkdir models
 echo Descargando modelo de reconocimiento de voz en espanol...
 powershell -NoProfile -ExecutionPolicy Bypass -Command "$u='https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip'; Invoke-WebRequest -Uri $u -OutFile 'models\vosk-es.zip'"
 if errorlevel 1 (
  echo No se pudo descargar el modelo. Comprueba tu conexion.
  pause
  exit /b 1
 )
 powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Force 'models\vosk-es.zip' 'models'"
 del "models\vosk-es.zip"
)
if not exist "config.json" copy "config.example.json" "config.json" >nul
powershell -NoProfile -ExecutionPolicy Bypass -Command "$p=Join-Path $env:USERPROFILE 'Desktop\PC Comforter.lnk'; $s=(New-Object -ComObject WScript.Shell).CreateShortcut($p); $s.TargetPath='%~dp0.venv\Scripts\pythonw.exe'; $s.Arguments='app.py'; $s.WorkingDirectory='%~dp0'; $s.IconLocation='%~dp0assets\comforter.ico'; $s.Save()"
echo.
echo Instalacion finalizada. Abre el acceso directo del escritorio.
pause
