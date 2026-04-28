@echo off
setlocal

set "APP_HOME=%~dp0"
set "PYTHON=C:\Users\Vrajkumar\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
set "SCRIPT=%APP_HOME%server.py"

if not exist "%PYTHON%" (
  echo Bundled Python runtime was not found.
  exit /b 1
)

if not exist "%SCRIPT%" (
  echo server.py was not found in this folder.
  exit /b 1
)

if "%~1"=="" (
  set "PORT=3000"
) else (
  set "PORT=%~1"
)

if not "%~2"=="" (
  set "TRADE_JOURNAL_HOME=%~2"
)

if "%TRADE_JOURNAL_HOME%"=="" (
  set "TRADE_JOURNAL_HOME=%APP_HOME%"
)

cd /d "%APP_HOME%"
set "PORT=%PORT%"
echo Starting Trade Journal from: %APP_HOME%
echo Saving data and images in: %TRADE_JOURNAL_HOME%
"%PYTHON%" "%SCRIPT%"
