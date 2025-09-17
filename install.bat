@echo off
setlocal

:: URL for Python installer
set "PYURL=https://www.python.org/ftp/python/3.13.7/python-3.13.7-amd64.exe"
set "PYEXE=%TEMP%\python-3.13.7-amd64.exe"

:: Base dir (same folder as the .bat)
set "BASEDIR=%~dp0"
set "ONTOPSETUP=%BASEDIR%setup.exe"

echo Downloading Python installer...
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -Command ^
 "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;`n" ^
 "Invoke-WebRequest -Uri '%PYURL%' -OutFile '%PYEXE%' -UseBasicParsing"

:: Launch Python installer
if exist "%PYEXE%" (
  echo Launching Python installer...
  start "" "%PYEXE%"
) else (
  echo Python installer failed to download.
)

:: Launch OnTopReplica setup.exe
if exist "%ONTOPSETUP%" (
  echo Launching OnTopReplica setup.exe...
  start "" "%ONTOPSETUP%"
) else (
  echo setup.exe not found in %BASEDIR%
)

endlocal
