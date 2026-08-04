#!/usr/bin/env bash
# ─── SUPERSEDED — do not run ─────────────────────────────────────────────────
#
# Written 2026-07-01 to initialize the Story Studio repository. It never
# succeeded, so Hearthlight had no version history for a month.
#
# WHY IT ALWAYS FAILED
#   It aborted if a known-leaked RunningHub API key appeared anywhere in the
#   working tree — but the key literal was written inside this script itself,
#   so its own `grep -r` always matched and it always aborted. The guard could
#   never pass. (See DECISIONS.md D-010.)
#
# WHAT REPLACED IT
#   Git was initialized 2026-08-03. The secret guard now lives in
#   governance/checkpoint.py and matches a SHA-256 of the key, so the literal
#   never enters the repository. It runs before every automated commit.
#
#     python governance/checkpoint.py gather
#     python governance/checkpoint.py commit
#
# The original body is removed: it contained the raw key and assumed WSL paths
# that no longer exist. Kept as a record only — safe to delete.
# ─────────────────────────────────────────────────────────────────────────────
echo "Superseded. See governance/checkpoint.py and DECISIONS.md D-010."
exit 1
