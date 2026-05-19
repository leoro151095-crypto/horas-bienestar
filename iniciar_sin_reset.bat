@echo off
setlocal

cd /d "%~dp0"

set "DATABASE_URL=sqlite:///%~dp0instance\app.db"
echo [INFO] DATABASE_URL=%DATABASE_URL%

if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] No se encontro .venv\Scripts\python.exe
  echo Crea el entorno con: py -m venv .venv
  pause
  exit /b 1
)

echo Iniciando servidor Flask (sin reset de BD)...
echo Abre: http://127.0.0.1:5000/login
".venv\Scripts\python.exe" -m flask --app app.py run --debug

pause
