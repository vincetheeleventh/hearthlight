#!/usr/bin/env bash
# ─── Hearthlight Dashboard — macOS / Linux ───────────────────────────────────
# Double-click on macOS. First run only:  chmod +x start-dashboard.command
#
# Read-only: shows where each story is and what YOU do next.
# Counterpart of start-dashboard.bat. Stdlib Python only — no dependencies.
# Close this window to stop the dashboard.
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT/skills/hearthlight-dashboard/scripts"

PORT="${HEARTHLIGHT_DASHBOARD_PORT:-8787}"
URL="http://localhost:${PORT}"

PY="$(command -v python3 || true)"
if [ -z "$PY" ]; then
  echo "Python 3 not found. Install it:  brew install python@3.12"
  read -r -p "Press return to close."
  exit 1
fi

# Open the browser once the server is actually listening.
(
  for _ in $(seq 1 40); do
    sleep 0.25
    if curl -sf -o /dev/null --max-time 1 "$URL"; then break; fi
  done
  if [ "$(uname -s)" = "Darwin" ]; then open "$URL"; else xdg-open "$URL" >/dev/null 2>&1 || true; fi
) &

echo "Hearthlight Dashboard → $URL"
echo "Close this window to stop it."
echo
"$PY" serve.py "$PORT"

echo
echo "Dashboard stopped."
read -r -p "Press return to close."
