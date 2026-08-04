# Structure audit — `projects/yugioh`

*Where the system meets a real film. Read against `skills/hearthlight-conventions/SKILL.md`.*
Nothing has been moved. Every fix below is a proposal.

Three categories, deliberately separated: **remnant** (dead, harmless, sweep whenever),
**misplaced** (live, something reads it, fix carefully), **unnamed** (the convention never said
where this goes — the system's failure, not the mess's).

---

## 1. The one that is actually costing you — aspect ratio

`D-008` calls aspect ratio a **composition law, not an export setting**. This project states it
twice, differently, and the generator is obeying the wrong one.

| Says **4:3 Academy** | Says **16:9** |
|---|---|
| `02-outline/FILM-BRIEF.md` § 3 — *"period-true to a 2003–04 domestic space… a composition law"* | `03-bible/assets.json` → `master_aspect_ratio` |
| `03-bible/mise-en-scene.md` (the Gate-2 aesthetic canon) | `04-images/shot-specs.json`, `04-images/image-workflow.json` |
| all three `03-bible/characters/*/character.json` | `distribution-spec.md` (the superseded file) |
| `06-video/METHODS.md` | **every packet the compiler emits** |

`krea_style_comp.py` reads `assets.json`, so **all 28 conditioning setups are being framed 16:9
against a 4:3 master.** The brief says 16:9 is a *derivative* — "trim top/bottom of the 4:3 master."
Generating the derivative first inverts the law.

This is not a naming problem. It is one fact with two homes, which is the exact failure mode
`GOALS.md` core problem 2 names.

**Needs you:** which is the master? Everything downstream keys off the answer.

## 2. The structural cause — `FILM-BRIEF.md` has no home, so nothing reads it

`FILM-BRIEF.md` announces itself as **"The central document"** and explicitly **supersedes**
`distribution-spec.md`. It carries the distribution spec, the charged value pair, the score map,
the audio law, the hook, the never-list.

**No code in the system reads it.** One reference doc mentions it
(`hearthlight-dashboard/references/SHOT-IDENTITY-PROTOCOL.md`, whose new `beat` / `charge` /
`motifs` / `never` fields are told to draw from "the FILM-BRIEF's charged value pair").

Meanwhile eight code paths read `projects/{slug}/distribution-spec.md` — `build_shot_registry.py`,
`serve.py`, `image_pass.py`, `two_pass.py`, `pipeline.json`, `requirements.json`,
`hearthlight-distribution-spec/SKILL.md`, and `CLAUDE.md`'s standing instruction *"Read the live
file — never trust a cached list in a skill."* That live file opens with:

> `# SUPERSEDED 2026-08-01` … **do not prompt from it**

So the documented path returns a tombstone, and the authoritative document sits in `02-outline/`,
which the conventions define as *story-arc.md, beat-sheet.md, av-script.md* — a slot that does not
include a brief.

**The convention has no name for "the central document."** Gate 0 and Gate 1 were skipped when this
project started at the storyboard, `FILM-BRIEF.md` retro-fills both, and the structure has no shelf
for that. Every agent since has had to guess.

**Proposed:** `distribution-spec.md` becomes a real file again — either the brief moves to that path,
or `distribution-spec.md` becomes a thin machine-readable header (`format`, `client`,
`charged_register`, `master_aspect`, `runtime`) that the brief owns and code reads. Conventions gain
the slot. Nothing else in the tree changes.

## 3. The ledger is write-only — 36 paid images it does not know about

`04-images/generations.jsonl` holds 30 generation records. `04-images/**` holds **68 PNGs.**

| Location | Files | Status |
|---|---|---|
| `04-images/shot-NN-v01.png` | 26 | ledgered (schema v2) |
| `04-images/style-composition-v4/` | 4 | ledgered (schema v3, carries `shot_id` + `request_sha256`) |
| `04-images/imports/job-shotNN*.png` | 26 | **not in the ledger** |
| `04-images/v4-out/shot-N.png` | 10 | **not in the ledger** |
| contact sheets at `04-images/` root | 2 | not in the ledger |

And **every one of the 30 ledgered records reads `review_status: pending-review`,
`selected_final: false`.** Not one image has ever been marked chosen.

So "which still is the approved base for shot 17?" cannot be answered from the record. It is
answerable only by knowing which *folder* is the current one — `v4-out` beats `imports` beats root —
which is identity by directory name. That is D-009's row-number failure moved up one level.

The runner's fingerprint/resume guarantee is real but only covers what it wrote. The 36 unledgered
files are the ones a future batch cannot prove it already paid for.

**Proposed:** one backfill pass writing `import` events for the 36 (path, sha256, and `prompt_known:
false` where the prompt is genuinely unrecoverable — never invented), then selection recorded as an
event so `selected_final` means something.

## 4. Four naming schemes for one class of asset

Conventions declare `shot-{nn}-v{nn}`. On disk:

| Pattern | Count | Era |
|---|---|---|
| `shot-01-v01.png` | 26 | v2, zero-padded, matches the convention |
| `job-shot01-krea.png` / `job-shot08.png` | 26 | import-era, provider-named |
| `shot-15.png`, `shot-23B.png` | 10 | v4-out, **no version suffix at all** |
| `shot-1-43712975-v02.png` | 4 | v3, unpadded + `shot_id` fragment |

The v3 form is the only one that survives a renumber, because it carries the shot ID. It is also the
only one that breaks the zero-padding rule. The convention and the best practice disagree — worth
resolving in the convention rather than per-project.

## 5. Remnants — sweep whenever, no urgency

- **`03-bible/projects/yugioh/06-video/method-{a,b,c,d}/{images,videos}/`** — a full project path
  recreated *inside* `03-bible`. **Zero files.** Something ran with the wrong working directory.
- **`06-video/method-{a,b,c,d}/`** — the four experiment folders from `METHODS.md`. **All empty.**
  The outputs went to `06-video/stills/` and `06-video/*.mp4` instead.
- **`06-video/_worker_shot01..10.md`, `_modtest_*.md`, `_job_shot01_A.md`** — 20 scratch dispatch
  files at a stage root. Agent working notes, not deliverables. No convention names them.
- **`06-video/ledger.jsonl`** — one line, a header, no events.
- **`04-images/review-proposals/`** — empty.
- **`03-bible/refs/props/lotr_poster.jpg`** — violates the Reference Naming Law
  (`prop-{subject}-{detail}-{nn}`) and has no manifest row. The only breach; the rest of `refs/`
  is compliant.
- **`00-source/`, `01-intake/`, `07-final/`** — empty. Correct for a project that entered at the
  storyboard, but a fresh agent reads it as an unstarted film.

## 6. What is working — do not disturb it

- **The locked style clause has not drifted.** 263 copies across `03-bible`, `04-images`,
  `05-storyboard`, `06-video`, and the spec file. **One variant, byte-identical, everywhere.**
  Consistency-by-verbatim-copy is holding under four agents and three surfaces.
- **`refs/` obeys the Reference Naming Law** apart from one file, and carries its
  `REFERENCE-MANIFEST.md`.
- **`shots.json` ↔ `asset-shot-map.json`** reconcile cleanly: 31 shots, 35 mappings, `unresolved: 0`,
  all IDs stable across the v3 → v4 workbook change. The identity layer is doing its job.
- **Character records are complete** — `CHARACTER.md` + `character.json` + a `candidates/_rejected/`
  slot for all three.

## 7. One live inconsistency worth a minute

`06-video/METHODS.md` hosts the character sheets at
`github.com/vincetheeleventh/hearthlight_assets` (a separate public repo) because Krea rejects
Krea's own asset URLs. This morning's merge brought a byte-identical copy of both sheets into the
**`hearthlight`** repo at top-level `yugioh/`. Two GitHub homes for one asset; the pipeline
references the other one. Harmless today, a trap later.

---

## Ranked

1. **Decide the master aspect.** 28 setups are queued against the answer.
2. **Give the brief a home the code reads.** Everything in §2 follows from that one gap.
3. **Backfill the ledger and start recording selection.** Cheap now, unrecoverable later.
4. Resolve the still-naming convention (`shot_id` in the filename, or not).
5. Sweep the remnants in §5.
