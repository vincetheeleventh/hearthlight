---
name: hearthlight-selfcheck
description: Health-check the Hearthlight PLUMBING — verify all skills are loaded, scripts run, tools (ffmpeg) exist, keys are present, the Notion and Krea MCPs are wired, and a project's critical generation assets and style block are ready. Returns a green/red checklist that separates MECHANICAL failures (the system's fault) from QUALITY judgments (Vince's call). Run when something feels off, after setup changes, or before a big generation.
metadata:
  hermes:
    tags: [hearthlight, selfcheck, health, validation, debugging]
    category: hearthlight
---

# Hearthlight — Self-Check (is the plumbing working?)

## The core distinction (read first)
There are TWO kinds of failure, and they need different eyes:
- **Mechanical** — a skill didn't load, a script crashed, a key is missing, the MCP is down, the
  style block is still a draft. These fail SILENTLY in normal use (you only find out when something
  downstream produces garbage). **This skill catches these.**
- **Quality** — the shot is technically fine but aesthetically wrong; a crew member gave a bland
  proposal; the pacing is off. **No self-check can catch these — they're Vince's call, always.**
  The system can validate its wiring; it cannot validate taste.

When something feels off, run this FIRST. It tells you whether the problem is the machine
(mechanical → fixable here) or the work (quality → a judgment call). Separating those is most of debugging.

## When to Use
- Something isn't behaving and you don't know if it's broken or just wrong.
- After setup changes (new skill, restart, key added, Notion wired).
- Before a big/expensive generation run — confirm the floor is solid first.
- Vince says "check yourself" / "is everything working" / "self-check".

## How to run
```bash
python3 skills/hearthlight-selfcheck/scripts/selfcheck.py
python3 skills/hearthlight-selfcheck/scripts/selfcheck.py --project mcconaughey-call
```
Output: a checklist sorted FAIL → WARN → OK, with counts and an exit code (0 = all green, 1 = a hard fail).
- **FAIL (red):** a hard mechanical failure — fix before proceeding.
- **WARN (yellow):** a feature isn't wired yet (e.g. no Notion key) — fine if you're not using it.
- **OK (green):** that piece is wired and ready.

## What it checks
- **Skills:** all 17 expected `hearthlight-*` skills present with valid frontmatter; flags tombstones/unnamed.
- **Scripts:** timing.py, build_timeline.py, and the versioned Krea image-pass tool run without a traceback; extract.sh present.
- **Tools:** ffmpeg, ffprobe, python3 available.
- **Secrets (presence only, never prints values):** Telegram / Notion / OpenAI / RunningHub keys in `.env`.
- **Config:** both Story Studio skill directories are loaded; Notion MCP present; Krea OAuth and required read/generate/upload/job tools are present.
- **Per project (--project):** style block blessed (NOT still DRAFT — else generation is blocked),
  project identity exists, 00-source has material, and the Krea first-pass readiness check reports every blocker without spending credits.

## What it deliberately does NOT do
- Judge whether any shot, prompt, or story beat is *good*. That's taste — Vince's, always.
- Run the AI behaviors (crew reasoning, prompt quality) — those are validated by Vince reading the
  output, not by a script. (To validate crew QUALITY: run the crew on one shot in the TUI with
  `/agents` and read whether each member gave a real per-dimension opinion. That's a human check.)
- Touch secrets beyond confirming a key string exists.

## How this fits the validation sequence
The right order to trust the system (none of it is proven until run):
1. **selfcheck** — is the plumbing wired? (this skill; mechanical, cheap, certain)
2. **smoke-test scripts** — `timing.py parse <real.xml>`, cut one clip — do the deterministic pieces give right output?
3. **one crew member in the TUI** — does each have a real distinct voice? (quality, human eye)
4. **one full shot end-to-end** — do the handoffs work? (the seams fail more than the stages)
Build trust from the floor up; don't test "the whole system" — test the smallest unit that can fail.

## Pitfalls
- Treating green as "the art is good." Green = wired, not right.
- Skipping selfcheck and debugging a quality problem that's actually a mechanical one (or vice versa).
- Running it expecting it to validate creative output — it can't, by design.
- **`$HOME` is overridden under the gateway → never resolve paths via `os.path.expanduser("~")`.**
  In a running profile, `$HOME` points at `<profile>/home/` (a dir that doesn't exist), so any
  script anchoring to `~` scans the wrong tree and reports phantom all-RED failures. The selfcheck
  script now anchors STUDIO to its own `__file__` location and PROFILE to `$HERMES_HOME`. If a
  future selfcheck (or ANY hearthlight script) suddenly reports everything missing while the files
  are plainly on disk, suspect this first — it's the checker that's broken, not the plumbing.
  Verify with: `echo $HOME` (profile home/ subdir) vs the real `/home/<user>/.hermes/Story Studio`.

## Verification
- Exit 0 with all-green (minus expected WARNs for features you haven't wired) = plumbing sound.
- Any RED is a real mechanical fault to fix before proceeding.
