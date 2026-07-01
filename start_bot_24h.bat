@echo off
setlocal

if exist ".env" (
  for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    if not "%%A"=="" if not "%%A:~0,1%"=="#" if not defined %%A set "%%A=%%B"
  )
)

if "%DISCORD_TOKEN%"=="" (
  echo DISCORD_TOKEN nao configurado.
  exit /b 1
)

if "%SITE_PORT%"=="" set SITE_PORT=8081
if "%SITE_HOST%"=="" set SITE_HOST=127.0.0.1
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
if not exist logs mkdir logs
set LOG_FILE=logs\tenshi-bot-%RANDOM%.log

:loop
echo Iniciando Tenshi Bot...
echo [%date% %time%] Iniciando Tenshi Bot...>> "%LOG_FILE%"
python .\main.py >> "%LOG_FILE%" 2>&1
echo Bot encerrou. Reiniciando em 10 segundos...
echo [%date% %time%] Bot encerrou. Reiniciando em 10 segundos...>> "%LOG_FILE%"
timeout /t 10 /nobreak >nul
goto loop
