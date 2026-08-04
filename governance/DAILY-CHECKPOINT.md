# Daily checkpoint runbook

*The procedure the scheduled job follows. Versioned here so the schedule prompt stays short and the
procedure can be corrected in Git like anything else.*

Working directory: `C:\Users\vxi\AppData\Local\hermes\Story Studio`

---

## 1. Gather facts

```bash
python governance/checkpoint.py gather
```

If it exits non-zero, **stop.** Report the error and do not commit anything — a failed gather means
the facts are untrustworthy, and a checkpoint built on bad facts is worse than no checkpoint.

Outputs `checkpoints/YYYY-MM-DD.md` (skeleton) and `checkpoints/.facts-YYYY-MM-DD.json`.

## 2. Read the canon

Read `GOALS.md` first — every judgment below is measured against it. Then the parts of
`PRODUCT_SPEC.md`, `ROADMAP.md`, `DECISIONS.md`, and `SKILL-INVENTORY.md` that the day's changes
touch. Read the previous checkpoint so you do not repeat yesterday's findings as if they were new.

## 3. Write the judgment

Replace each `<!-- AGENT:... -->` comment and its `_(not yet written)_` placeholder with real content.
Keep the whole thing **readable in about two minutes** — this is a daily habit, not a report.

| Section | What it must do |
|---|---|
| What changed? | Meaningful development only. Group by agent where attribution exists. Skip noise. |
| Why does it matter? | Connect to a **named** goal, feature, roadmap item, or known problem. If you cannot name one, that is itself the finding. |
| North Star alignment | One verdict — **ALIGNED** / **NEUTRAL-INFRASTRUCTURAL** / **QUESTIONABLE** / **POTENTIAL DRIFT** — then why, against the six criteria in `GOALS.md`. |
| Product-spec discrepancies | Where implementation moved but `PRODUCT_SPEC.md` did not. Cite file and section. |
| Complexity / orphan detection | Unused, redundant, overlapping, undocumented, goal-disconnected, or speculative-with-no-use-case. Include things that were already there, not just new ones. |
| Unfinished work | TODOs, partial features, failing tests, abandoned implementation branches. |
| Recommended next actions | **At most 3**, prioritized, one sentence each. |

**A quiet day gets a short checkpoint.** Do not inflate. "No meaningful changes; system unchanged" is
a valid and useful entry. Manufacturing findings to look busy destroys the signal this exists to give.

### What you may and may not change

**May:** the checkpoint file · `PRODUCT_SPEC.md` (descriptive corrections) · `ROADMAP.md` ·
`SKILL-INVENTORY.md` · a new appended `DECISIONS.md` entry · mechanical fixes to `AGENTS.md` /
`README.md` (a skill added to the index, a corrected count).

**May not — surface as a recommendation instead:** `GOALS.md` in any form · product strategy ·
deleting a feature, skill, or file · speculative refactors · rewriting an existing decision ·
resolving a `⚠️ NEEDS VINCE` marker. Those are Vince's.

## 4. Update the Miro panel

Board and block IDs: `governance/miro.json`.

Update the blocks **in place** with `layout_update` — do not recreate the frame, and **never edit the
pipeline diagram** (`pipeline_diagram_id`); that is Vince's hand-built artwork.

Refresh: `stamp` (today's date) · `roadmap` · `health` · `flags` · `open_questions` when they change.
Leave `north_star` and `non_goals` alone unless `GOALS.md` itself changed — they are the stable part,
and a North Star that visibly moves every day is not a North Star.

If the pipeline in `PRODUCT_SPEC.md` no longer matches the diagram (a stage added, a skill renamed),
say so in the `health` block so Vince can update the art deliberately.

## 5. Validate, commit, push

```bash
python governance/checkpoint.py commit --agent cowork
```

This refuses to commit if any agent section is still unfilled, if the secret scan finds anything, or
if tests are failing. Those refusals are the feature — do not work around them with `--skip-tests`
unless you have read the failure and it is unrelated.

Exit `2` means the commit succeeded but the push failed. The work is safe locally; report it.

## 6. Report to Vince

Short. The alignment verdict, the top 3 next actions, and anything that needs him. If a
`⚠️ NEEDS VINCE` marker has been sitting unanswered for more than a week, mention it once — those
questions block honest alignment judgments.
