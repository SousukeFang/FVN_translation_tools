@echo off
setlocal
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" -Action Uninstall -GameRoot "%~dp0."
set "FVN_RESULT=%ERRORLEVEL%"
if not "%FVN_RESULT%"=="0" echo Restore was refused or interrupted. Preserve the backup directory and read the message above.
pause
exit /b %FVN_RESULT%
