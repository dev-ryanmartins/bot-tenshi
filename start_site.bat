@echo off
setlocal
if exist ".env" (
  for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    if not "%%A"=="" if not "%%A:~0,1%"=="#" if not defined %%A set "%%A=%%B"
  )
)
if "%SITE_PORT%"=="" set SITE_PORT=8081
if "%SITE_HOST%"=="" set SITE_HOST=127.0.0.1
python .\artifacts\tenshi-bot\site_server.py
