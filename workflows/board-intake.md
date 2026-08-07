---
doc: BOARD-INTAKE
role: workflow
authority: canon
owner: vince
updated: 2026-08-07
status: active
answers:
  - how a photographed storyboard becomes a canonical, agent-readable shot record
  - what to run, in what order, when a project is onboarded or boards are redrawn
not_here:
  what the drawing is authoritative for: skills/hearthlight-image-prompts/references/PANEL-READING.md
  how prompts are then written: skills/hearthlight-image-prompts/references/PROMPT-AUTHOR.md
---

# Board intake — from photographed boards to a canonical shot record

**The onboarding route.** Not a route to a clip — a route to the *state* that
[shot2video](shot2video.md) and [board2video](board2video.md) both assume exists.

Run it when a project starts, when boards are redrawn, or when a workbook is re-pasted. It is
**idempotent**: every step reports "nothing to change" on a second run.

---

## What it produces

| End state | Why it matters |
|---|---|
| `shots.json` carries `prompt.still` and `prompt.action` per shot | The compiler reads the record, not a spreadsheet |
| `shots.json` carries `panel.path` per shot | The drawing is found by lookup, not by guessing a filename |
| `storyboard-panels/shot-{nn}-board.png` on disk | An agent can actually open the drawing |
| The workbook is a **derived export only** | Nothing in production reads it |

`hearthlight-selfcheck` verifies this end state per project and WARNs when a project still depends
on the spreadsheet.

---

## The route

Vince draws boards on paper, photographs them, chops the photo into panels, and pastes each panel
into the Storyboard column of the shot-list workbook. Everything below turns that into a record.

### 1. Build the shot registry

```bash
python skills/hearthlight-dashboard/scripts/build_shot_registry.py --project {slug}
```

Creates `05-storyboard/shots.json` with **stable shot IDs** — permanent identity that survives
renumbering (`DECISIONS.md` D-009). Run once; re-running preserves established IDs.

### 2. Migrate the prompts into the record

```bash
python skills/hearthlight-dashboard/scripts/shot_record.py migrate \
    --project {slug} --workbook 05-storyboard/{workbook}.xlsx --dry-run
python skills/hearthlight-dashboard/scripts/shot_record.py migrate \
    --project {slug} --workbook 05-storyboard/{workbook}.xlsx
```

Copies `Still (frame one)` and `Action` into `prompt.still` / `prompt.action`, and strips the locked
style block — **style is a moodboard parameter, never prompt text**, and the compiler rejects a
prompt containing it.

### 3. Repair anything already imported

```bash
python .../shot_record.py repair --project {slug}
```

Only needed if prompts were migrated before the style-strip existed. Reports `0` otherwise.

### 4. Extract the drawings out of the workbook

```bash
python skills/hearthlight-image-prompts/scripts/panel_reader.py extract \
    --project {slug} --dry-run
python .../panel_reader.py extract --project {slug}
```

Reads each image's **anchor row**, takes the shot number from that row's `Shot` cell, and writes
`shot-{nn}-board.png`. Named for the shot it belongs to, not a panel index — so a panel shared by two
shots is saved under both and the ambiguity disappears.

### 5. Link the drawings to the record

```bash
python .../panel_reader.py link --project {slug}
```

Writes `panel.path` onto each shot. **Also clears stale links** whose file has vanished, so the
record never points at nothing. Re-run after adding a board by hand.

### 6. Verify

```bash
python .../panel_reader.py status --project {slug}
python .../shot_record.py verify --project {slug} --workbook 05-storyboard/{workbook}.xlsx
hearthlight-selfcheck
```

Expect: every shot canonical, panels linked, selfcheck green for the project.

> **`verify` compares the record against the workbook using the same reader that imported it.** It
> proves the import was faithful — it does **not** prove the text is valid for the compiler. That is
> what the compiler's own validation is for. A verifier that shares a bug with the thing it verifies
> proves nothing; this one nearly did.

### 7. Retire the workbook

From here the workbook is an **export**, regenerated on demand:

```bash
python skills/hearthlight-dashboard/scripts/export_shotlist.py --project {slug} --vision
```

Editing that CSV changes nothing. Edits go through the Studio UI or
`shot_record.py set`, both of which write the record and log an attributable event.

---

## Then the drawings can be read

Board intake makes the panel *openable*. Reading it is the vision pass:

```bash
python .../panel_reader.py packet --project {slug} --shot N --out packet.json
#   → an LLM reads the drawing under references/PANEL-READING.md
python .../panel_reader.py record --project {slug} --shot N --reading reading.json
```

The packet carries the drawing, the latest Shot Vision, the storyboard text, and the **adjacent
shots** — which is what makes "adjacent-shot continuity" checkable rather than aspirational.

---

## Known failure modes

- **Panels listed but no drawing.** `board_panels` names a panel that was never pasted, or the paste
  did not take. `link` reports these; they are not blockers, and the author works from text.
- **HEIC panels.** A vision model cannot read them. `packet` flags `needs_conversion`; convert before
  sending.
- **A re-purposed panel.** `storyboard_reference` may say the drawing no longer matches the shot.
  Read it anyway and let the Vision govern — the panel is tier 3 evidence, never a vote against it.
- **Re-pasted workbook.** Extraction is **derived**: re-run `extract` then `link` after any re-paste,
  or the record points at the old drawings.
- **Shot numbers that are not integers** (`18B`). Handled — the filename falls back to the literal
  label — but check the extract output names look right.

## What this cost to learn

Every step above was run by hand on `yugioh` before it existed as a procedure, and two things only
surfaced because of it:

**The drawings were invisible.** Before extraction, 2 of 28 shots appeared to have a panel. After,
20 did. **A drawing the system cannot open does not exist to it** — and shot 8's panel turned out to
read *"Single on Boy → 2-shot · Dad kneels"*, confirming a live blocker that had been argued from
prose alone.

**The imported prompts were invalid.** Every workbook cell ends with the locked style block, which
the compiler correctly refuses. Faithful migration is not the same as correct migration.
