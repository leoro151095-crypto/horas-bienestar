@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] No se encontro .venv\Scripts\python.exe
  echo Crea el entorno con: py -m venv .venv
  pause
  exit /b 1
)

set "PY=.venv\Scripts\python.exe"
echo [INFO] Python: %PY%
echo [INFO] DATABASE_URL=sqlite:///%~dp0instance\app.db

echo.
echo [1/2] init-db...
%PY% -m flask --app app.py init-db
if errorlevel 1 (
  echo [ERROR] Fallo init-db. Revisa la salida de arriba.
  pause
  exit /b 1
)

echo [2/2] run --debug...
%PY% -m flask --app app.py run --debug --port 5000

pause

