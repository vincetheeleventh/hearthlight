---
name: hearthlight-dashboard
description: Read-only pipeline dashboard + the gate ledger contract. Use when Vince asks "where are we", "what's next", "dashboard", or when a gate ✅ happens (write status.yml). Also use to update pipeline.json when the pipeline's stages change.
---

# Hearthlight Cockpit — map, intake, and gate ledger

A local web page that answers ONE question in five seconds — **what does Vince
do next** — and takes his INPUTS: dropped assets, typed rants/ideas, new projects.
It never takes his approvals (gates stay in Telegram).

## Parts

- `pipeline.json` — the stage manifest. The ONE place stage structure lives.
  When the pipeline evolves (a new stage like Critique 3.5 or Timing 4.7),
  edit HERE — the UI follows automatically.
- `intake.json` — the drop-zone manifest: which asset kind lands in which folder
  (source, character sheets per-name, environments, props, style refs, panels, timing).
- `scripts/scan.py` — scans `projects/{slug}/` + reads each `status.yml`,
  emits status JSON incl. zone counts. Scanning detects DRAFTED; only the ledger says APPROVED.
- `scripts/serve.py` — stdlib server on :8787; rescans per request. Write endpoints:
  `/api/upload` (streamed, never overwrites — `-v2` on collision), `/api/note`
  (rant → `01-intake/rant-typed-*.md`, idea → `01-intake/ideas-inbox.md`),
  `/api/new-project` (scaffolds folders + status.yml + AGENTS.md stub).
- `index.html` — Library (all projects, progress, next action) + per-project view
  (hero next-action, stage rail, drop zones, rant box, stage cards).
- `start-dashboard.bat` (studio root) — Vince double-clicks this on Windows.
- `05-storyboard/shots.json` ? stable cross-stage shot registry. UI structure edits write here.
- `05-storyboard/shot-changes.jsonl` ? append-only insert/retire/restore audit.
- `05-storyboard/asset-shot-map.json` ? explicit mapping for pre-ID events.
- `references/SHOT-IDENTITY-PROTOCOL.md` ? required identity and reconciliation law.

## The seam with Hermes
The cockpit and the agent NEVER talk directly — they meet in the project folders.
Cockpit writes inputs; agent reads them (check `01-intake/` for unprocessed
rant-typed files and ideas-inbox entries at session start), works, writes artifacts;
cockpit shows them. One filesystem, one truth.

## THE GATE LEDGER CONTRACT (the law this skill adds)

> **Every gate ✅ in Telegram gets a stone on disk.**
> At the moment Vince approves a gate, write it to `projects/{slug}/status.yml`
> in the same breath as the Notion log. No exceptions. A gate that isn't in
> status.yml didn't happen, as far as any tool can know.

Format — flat `key: value`, keys are stage ids from `pipeline.json`:

```yaml
project: mcconaughey-call
distribution_spec: approved 2026-07-30
gate1_outline: pending
critique: done          # support stages: done / n/a
gate3_images: unconfirmed   # work exists but no ✅ ever recorded — ask Vince to ratify
```

States: `approved YYYY-MM-DD` · `pending` · `unconfirmed` · `done` · `n/a`.

- **Ratification:** when Vince says e.g. "gates 0 through 2 are approved on the
  pilot", update the entries with today's date (or his stated date) and confirm
  back in one terse line.
- **New project:** create `status.yml` with all stages `pending` when the
  project folder is created (fold into `hearthlight-conventions` flow).
- **Never** mark `approved` from inference. Only from Vince's explicit ✅.

## PROPOSED AMENDMENT (Vince to ratify)

Add to `hearthlight-conventions` and `hearthlight-notion-log`:
"On every gate ✅, also write `projects/{slug}/status.yml` per the
hearthlight-dashboard ledger contract." Until ratified, this skill's contract
section is the working rule.

## Running

- Windows: double-click `start-dashboard.bat` → http://localhost:8787
- WSL: `python3 skills/hearthlight-dashboard/scripts/serve.py`
- One-shot JSON (debug): `python3 skills/hearthlight-dashboard/scripts/scan.py`

## Boundaries

- Gate approval remains read-only here; sacred gate state still comes only from Vince's explicit approval.
- Asset-stage review, prompt editing, generation requests, and shot-structure edits are explicit user writes.
- UI deletion is reversible retirement. No media, prompt, review, or history record is erased.
- Every structural write must follow `references/SHOT-IDENTITY-PROTOCOL.md`.
- Voice register: mechanics terse. Status answers in chat mirror the
  dashboard's next-action line, nothing more.
