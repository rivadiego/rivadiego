@echo off
rem Avvia Coach Connect su Windows trovando Python da solo, anche se non e' nel PATH.
rem Doppio clic, oppure da PowerShell: .\coach-connect\start.cmd --demo  (o --tunnel)
setlocal
set "PY="
for %%V in (3.14 3.13 3.12) do for %%K in (HKCU HKLM) do for /f "tokens=2,*" %%A in ('reg query "%%K\Software\Python\PythonCore\%%V\InstallPath" /v ExecutablePath 2^>nul ^| findstr /i "ExecutablePath"') do if not defined PY set "PY=%%B"
for %%P in ("%LOCALAPPDATA%\Programs\Python\Python314\python.exe" "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" "%ProgramFiles%\Python314\python.exe" "%ProgramFiles%\Python313\python.exe" "%ProgramFiles%\Python312\python.exe" "%LOCALAPPDATA%\Microsoft\WindowsApps\python3.13.exe" "%LOCALAPPDATA%\Microsoft\WindowsApps\python3.12.exe") do if not defined PY if exist "%%~P" set "PY=%%~P"
if not defined PY (
  echo Non trovo Python 3.12 o piu' recente: installalo da https://www.python.org/downloads/ oppure dal Microsoft Store.
  pause
  exit /b 1
)
echo Uso Python: %PY%
"%PY%" "%~dp0start.py" %*
if errorlevel 1 pause
