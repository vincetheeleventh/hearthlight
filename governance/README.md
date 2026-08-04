# governance/ — the daily alignment checkpoint

The smallest thing that keeps Hearthlight's intent visible as it changes. One script, Python stdlib
only, no dependencies, no framework.

## Why it is split in two

`checkpoint.py` has two commands and they do different kinds of work:

- **`gather`** collects facts. Git activity, skill wiring, doc staleness, TODO markers, tests,
  secret scan. No judgment, no opinions, no network. It can fail loudly.
- **`commit`** validates and commits. It refuses if the agent sections are unfilled, if the secret
  scan finds anything, or if tests are failing.

In between, an agent reads the facts and writes the judgment. That split is the point: the
mechanical half **blocks the commit** when it breaks, so a failed checkpoint never produces a
committed artifact. (`DECISIONS.md` D-011.)

## Running it by hand

```bash
cd "C:\Users\vxi\AppData\Local\hermes\Story Studio"

python governance/checkpoint.py gather          # writes checkpoints/YYYY-MM-DD.md + facts JSON
#   → open the checkpoint, fill each <!-- AGENT:... --> section
python governance/checkpoint.py commit          # validates, commits, pushes
```

Useful flags:

| Flag | Effect |
|---|---|
| `--date 2026-08-01` | Backfill a specific day |
| `--force` | Overwrite an existing checkpoint (gather) |
| `--no-push` | Commit locally only |
| `--agent hermes` | Set the commit's `Agent:` trailer (default `cowork`) |
| `--skip-tests` | Commit despite failing tests — use deliberately |

Just want the facts, no writing? `python governance/checkpoint.py gather` then read
`checkpoints/.facts-YYYY-MM-DD.json`. It is gitignored and regenerable.

## What it will and will not touch

**Commits automatically:** `checkpoints/`, `PRODUCT_SPEC.md`, `ROADMAP.md`, `DECISIONS.md`,
`SKILL-INVENTORY.md`, `AGENTS.md`, `README.md`, `governance/`.

**Never touches:** `GOALS.md` — not staged, not edited, not by any agent. Also never deletes a
feature or a skill, never refactors, never rewrites a decision. Those come back as recommendations
in the checkpoint for Vince to act on.

## Scope

The Hearthlight **system** only. `projects/` is gitignored and deliberately out of scope — it holds
media and rights-constrained work (`DECISIONS.md` D-006, confirmed by Vince 2026-08-03).

## The secret guard

Before any commit, `scan_secrets()` sweeps for common credential shapes and for the known-leaked
RunningHub key — matched by **SHA-256**, so the literal never enters the repository. That literal
living inside the old guard script is precisely why `git-init-commit.sh` could never run
(`DECISIONS.md` D-010).

## Verifying it works

```bash
python governance/checkpoint.py gather --date 2026-01-01   # harmless dry run
git log --oneline --grep="^checkpoint:"                    # checkpoint history
git log -1 --format=%B                                     # confirm the Agent: trailer
git remote -v && git status -sb                            # remote wired? ahead of origin?
```

A red checkpoint is doing its job. Silence for several days is the failure mode to watch for — check
that the scheduled task is still enabled.
