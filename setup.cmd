@echo off
rem flycns setup for Windows. Run it from PowerShell or cmd, in the flycns folder:
rem   .\setup.cmd --check    install, then run the regression test on the toy graph (no account needed)
rem   .\setup.cmd            install, then download the connectome (asks for your neuPrint token once)
rem It finds Python 3.10 or newer (3.12 preferred; offers to install 3.12 with winget if there is none),
rem then hands over to scripts\setup.py, which does the rest.
setlocal EnableExtensions
cd /d "%~dp0"
set "PYTHONUTF8=1"
set "PY="

call :try_launcher -3.12
call :try_launcher -3
for /f "delims=" %%P in ('where python 2^>nul') do call :try_exe "%%~P"
call :try_exe "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
call :try_exe "%ProgramFiles%\Python312\python.exe"
if not defined PY goto install_python

:run
%PY% scripts\setup.py %*
exit /b %ERRORLEVEL%

:install_python
echo Python was not found on this computer.
where winget >nul 2>&1 || (
  echo Install Python 3.12 from https://www.python.org/downloads/ and tick "Add python.exe to PATH".
  echo Then run setup.cmd again.
  exit /b 1
)
choice /c YN /m "Install Python 3.12 now with winget"
if errorlevel 2 exit /b 1
winget install -e --id Python.Python.3.12 --scope user
call :try_exe "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if defined PY goto run
echo Python is installed. Close this window, open a new PowerShell in this folder, and run setup.cmd again.
exit /b 1

rem ---- helpers: each sets PY only if nothing has been found yet and the candidate is 3.10 or newer
:try_launcher
if defined PY exit /b 0
where py >nul 2>&1 || exit /b 0
py %1 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1 && set "PY=py %1"
exit /b 0

:try_exe
if defined PY exit /b 0
if not exist "%~1" exit /b 0
rem the Microsoft Store placeholder only opens the Store; skip it
echo %~1 | find /i "WindowsApps" >nul && exit /b 0
"%~1" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1 && set PY="%~1"
exit /b 0
