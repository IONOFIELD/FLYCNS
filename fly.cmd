@echo off
rem One-word launch: the flycns menu, in this folder's environment. Run setup.cmd first.
setlocal
cd /d "%~dp0"
set "PYTHONUTF8=1"
if not exist ".venv\Scripts\python.exe" (
  echo No environment here yet. Run setup.cmd first.
  exit /b 1
)
".venv\Scripts\python.exe" fly.py %*
exit /b %ERRORLEVEL%
