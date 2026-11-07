@echo off
setlocal
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" -Action Install -GameRoot "%~dp0."
set "FVN_RESULT=%ERRORLEVEL%"
if not "%FVN_RESULT%"=="0" echo Installation failed. Read the message above. Preserve the backup directory.
pause
exit /b %FVN_RESULT%
