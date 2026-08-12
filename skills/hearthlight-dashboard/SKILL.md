---
name: hearthlight-dashboard
description: Read the current Hearthlight film state, inspect Design/Production/Inputs per shot, manage stable Shot IDs, or use the lightweight intake cockpit for dropped assets and typed notes. Use when Vince asks where production stands, what needs attention, what is current for a shot, or when shot identity must be reconciled.
---

# Hearthlight production state and intake

Hearthlight Studio on `http://127.0.0.1:8765` is the canonical visual surface. It computes three independent shot axes:

- **Design:** Exploring · Designed · Locked. Only Vince confirms the current Shot Vision.
- **Production:** Not started · In progress · Needs fix · Candidate ready · Approved. Only Vince selects and accepts assets.
- **Inputs:** Ready · Stale · Broken. Computed; Broken blocks the affected generation action.

Do not infer approval from files, stage order, or recency. A newer candidate never replaces a selected hero unless Vince selects it.

## Parts

- `scripts/scan.py` — reads canonical shot state from the Studio API and adds intake-zone counts. It does not recompute production state.
- `scripts/serve.py` — optional intake server on `:8787`; owns uploads, typed notes, and project scaffolding only.
- `intake.json` — maps dropped asset kinds to project folders.
- `05-storyboard/shots.json` — stable cross-stage shot registry.
- `05-storyboard/shot-changes.jsonl` — append-only insert/retire/restore history.
- `05-storyboard/asset-shot-map.json` — explicit mapping for pre-ID events.
- `references/SHOT-IDENTITY-PROTOCOL.md` — identity and reconciliation law.

## Operating rules

- Read current state from Studio. Do not introduce another progress ledger.
- The machine never approves its own work. Agents draft, run, and report; Vince locks designs and approves shots.
- Asset review, prompt edits, generation requests, hero selections, and structure edits are explicit writes with durable history.
- Deletion in the UI means reversible shot retirement. Never erase media, prompts, reviews, or history.
- Every structural write follows `references/SHOT-IDENTITY-PROTOCOL.md`.
- Mechanics terse. Report the small number of shots that need attention, not an invented linear next stage.

## Running

```bash
python skills/hearthlight-dashboard/scripts/scan.py --project yugioh
python skills/hearthlight-dashboard/scripts/serve.py
```

The scanner requires the main Studio server on port `8765`. Override its address with `HEARTHLIGHT_STUDIO_URL` only when the Studio is deliberately running elsewhere.

## Overriding a shot's chosen image

Prefer **Use as hero** in Studio. For a scripted repair, use `scripts/set_shot_image.py`; it writes a stable-ID `selection` event and preserves prior history.

```bash
python skills/hearthlight-dashboard/scripts/set_shot_image.py \
  --project yugioh --shot 2 --image 04-images/some-image.png --note "why"
```

`--shot` accepts a display number, `shot_id`, or legacy label. Nothing is overwritten. Reverting is another selection event.
