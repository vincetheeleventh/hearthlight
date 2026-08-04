# Shot identity and structural-change protocol

This protocol applies from first shot list through final delivery. Shots may be inserted,
retired, restored, split, merged, reordered, or retitled at any production stage.

## Identity law

- `shot_id` is immutable identity. Generate once. Never reuse.
- `display_number` is a human label. It may change.
- `order` is current sequence position. It may change.
- Filenames, spreadsheet rows, timestamps, titles, and panel numbers are evidence, never identity.
- Every prompt, generation, review, selection, comment, image, clip, audio cue, and approval event stores `shot_id`.
- Existing numeric records remain readable only through an explicit revision-aware map.
- Ambiguity produces `needs_reconciliation`. No process may guess.

Canonical registry: `projects/{slug}/05-storyboard/shots.json`.
Legacy asset map: `projects/{slug}/05-storyboard/asset-shot-map.json`.
Structural audit log: `projects/{slug}/05-storyboard/shot-changes.jsonl`.
Narrative sidecar: `projects/{slug}/05-storyboard/shot-narrative.json` (see below).

## Registry fields

Project level:

- `schema_version`
- `registry_revision` and `registry_revision_id`
- `source` and `source_revision_hash`
- `source_sync_state`: `source-aligned` or `studio-edited`
- `status`: `ready` or `needs_reconciliation`
- `shots`: active ordered records
- `retired_shots`: complete tombstones
- `validation_findings`

Shot level:

- `shot_id`
- `display_number`
- `order`
- `legacy_numbers`
- `legacy_labels`: revision-scoped aliases such as `{"label":"14","revision":"v3"}`
- title, timing, story, image direction, and video motion
- shared-setup owner by `shared_setup_owner_shot_id`
- origin and creation timestamp
- optional split/merge lineage

## Narrative sidecar (the human WHY, rebuild-proof)

`shot-narrative.json` holds the human-side narrative layer, keyed by `shot_id`:

- `one_liner` — the single sentence the shot answers to. Born at outline/crew time, not backfilled.
  A shot that cannot get a one-liner is a story problem surfacing early.
- `expanded` — deeper narrative: emotions, character progression, the charge it serves.
- `open_loops` — questions the shot opens or advances.
- `why_this_shot` — justification of the visual approach (why framed/held/angled this way).
- `staging.surfaced` — what the viewer consciously registers: `shot_type`, `camera_move`,
  `character_actions`, `setting`.
- `staging.ambient` — what they feel but never notice: `props`, `lighting`, `sound`.
- `beat` — which beat of the film brief the shot serves (label verbatim from the brief).
- `charge` — one line: where the shot sits on the project's declared value axis
  (file-level `value_axis`, from the FILM-BRIEF's charged value pair).
- `motifs` — the brief's visual-system devices in play for this shot.
- `never` — the brief's never-list constraints that bind this shot. Reviewers check these
  before anything else; a render violating a `never` is a spec FAIL regardless of beauty.

Rules:

- **Sidecar, never registry.** `build_shot_registry.py` reconstructs shot rows from the source
  workbook; extra fields written into `shots.json` are dropped on rebuild. The sidecar is joined
  by `shot_id` at read time (Hearthlight Studio does this), so rebuilds cannot destroy it.
- A missing `shot_id` entry means *not yet authored*, never "no narrative".
- Split/merge: children/merged shots start unauthored; the parent's entry stays under the retired
  ID as history. Copy forward only deliberately.
- Retirement does not delete the entry (tombstone rule applies).

## Allowed structural operations

### Insert

1. User chooses position.
2. System creates a new UUID.
3. Existing IDs remain unchanged.
4. Only `order` changes for later shots.
5. Suggested display label is editable and must be unique.
6. Insert event lands in `shot-changes.jsonl`.

### Delete in the UI

Deletion means retirement, never erasure.

1. Shot leaves the active sequence.
2. Complete shot record moves to `retired_shots`.
3. Media, prompts, reviews, approvals, and generation records remain untouched.
4. ID is never reused.
5. Shared-setup owners cannot be retired while active dependants reference them.
6. Restore returns the same ID and history.

### Reorder or renumber

Only `order` or `display_number` changes. Assets do not move and IDs do not change.

### Split

Create new child IDs with `split_from_shot_id`. Retire the original only after explicit confirmation.
Assets stay with the original unless individually reassigned.

### Merge

Create one new ID with `merged_from_shot_ids`. Retire sources only after explicit confirmation.
Never silently choose which source asset becomes the merged hero.

## Spreadsheet round trip

Every exported or regenerated shot-list workbook must include a `Shot ID` column.

Import matching order:

1. Exact `Shot ID`.
2. Exact registered source/panel identity.
3. Unique legacy ID.
4. Unique normalized title plus board panels.
5. Otherwise `needs_reconciliation`.

A missing prior shot is a proposed retirement, not an automatic deletion. Review it explicitly.
Placeholder legacy values such as `new`, `?`, and `n/a` are never accepted as identifiers.

When the UI has changed structure, `source_sync_state` becomes `studio-edited`. The next
spreadsheet revision must be exported from that registry with its `Shot ID` column intact.
Do not independently rebuild a number-only workbook and treat it as authoritative.

If an older workbook supplied labels used by old ledgers, declare it during reconciliation:

`python skills/hearthlight-dashboard/scripts/build_shot_registry.py --project {slug} --source 05-storyboard/{new}.xlsx --legacy-source 05-storyboard/{old-v3}.xlsx --dry-run`

The builder records those aliases with their source revision, so a V3 ?Shot 14? can never collide
with a different V4 ?Shot 14.?

Preview:

`python skills/hearthlight-dashboard/scripts/build_shot_registry.py --project {slug} --source 05-storyboard/{workbook}.xlsx --dry-run`

Apply a clean revision:

`python skills/hearthlight-dashboard/scripts/build_shot_registry.py --project {slug} --source 05-storyboard/{workbook}.xlsx`

Accept source removals only after review:

`python skills/hearthlight-dashboard/scripts/build_shot_registry.py --project {slug} --source 05-storyboard/{workbook}.xlsx --accept-retirements`

Backfill old event mappings:

`python skills/hearthlight-dashboard/scripts/backfill_shot_asset_map.py --project {slug} --apply`

Numbered loose files are never attached by current display number once a stable registry exists.
Confirm the label space explicitly for any historical folder:

`python skills/hearthlight-dashboard/scripts/backfill_shot_asset_map.py --project {slug} --map-legacy-directory 04-images/v3-out --apply`

`python skills/hearthlight-dashboard/scripts/backfill_shot_asset_map.py --project {slug} --map-current-display-directory 04-images/v4-out --apply`

All new UI generations store `shot_id` in their event and embed its first eight characters in the
filename. They need no numeric inference.

## Stage-independent rule

Structural edits may occur during outline, storyboard, image generation, video generation, or edit.
After any edit:

1. Registry revision increments.
2. UI refreshes from the registry.
3. Existing assets follow `shot_id`.
4. New shots show explicit missing requirements.
5. Retired-shot jobs cannot launch.
6. Descendant clips remain attached to their parent asset and shot; stale-lineage rules still apply.
7. Gate state does not change automatically.

## Reconciliation stop conditions

Stop writes and show a reconciliation finding when:

- duplicate IDs appear;
- one legacy label resolves to multiple shots;
- a source omits an existing shot without explicit retirement;
- an asset points to an unknown or retired ID;
- a shared-setup owner is missing;
- a workbook is newer than the registered source;
- image direction and story rows resolve to different IDs.

The UI may read an unresolved project, but structure edits, approvals, and generation must remain blocked
for affected shots until identity is repaired.
