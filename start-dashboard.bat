@echo off
REM ── Hearthlight Dashboard ──
REM Double-click to open the pipeline dashboard in your browser.
REM Read-only: it shows where each story is and what YOU do next.
REM Leave this window open; close it to stop the dashboard.

cd /d "%~dp0skills\hearthlight-dashboard\scripts"

start "" http://localhost:8787

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 serve.py
) else (
  python serve.py
)

echo.
echo Dashboard stopped. Press any key to close.
pause >nul
