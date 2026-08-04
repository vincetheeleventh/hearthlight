@echo off
REM ── Start the Hearthlight gateway (foreground, no service, no admin) ──
REM Double-click this to bring the Hearthlight Telegram bot online.
REM Leave this window OPEN while you work; close it to stop the gateway.
REM
REM If "--foreground" errors as an unknown flag on your build, open a
REM terminal and run:  hermes -p hearthlight gateway --help
REM to find the run-without-service flag (some builds call it `run`).

echo Starting Hearthlight gateway (foreground)...
echo Leave this window open. Close it to stop.
echo.
hermes -p hearthlight gateway start --foreground

echo.
echo Gateway stopped. Press any key to close.
pause >nul
