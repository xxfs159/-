@echo off
setlocal
cd /d "%~dp0"

where node >nul 2>nul
if errorlevel 1 (
  echo Node.js was not found in PATH.
  echo Please install Node.js or run the demo by opening index.html directly.
  pause
  exit /b 1
)

set "PORT=4173"
set "URL=http://localhost:%PORT%"

start "Project 39 Demo Server" cmd /k "node server.mjs"
echo Waiting for local server at %URL% ...

for /l %%I in (1,1,30) do (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $r = Invoke-WebRequest -UseBasicParsing -TimeoutSec 1 '%URL%'; if ($r.StatusCode -ge 200) { exit 0 } } catch { exit 1 }"
  if not errorlevel 1 goto open_browser
  timeout /t 1 /nobreak >nul
)

echo The local server did not respond. Please check the server window for details.
pause
exit /b 1

:open_browser
start "" "%URL%"
echo Demo started at %URL%.
