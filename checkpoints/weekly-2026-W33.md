# Weekly workshop — 2026-W33

*Generated 2026-08-10. Improvement pass: read the week, audit coherence, propose.*

---

## The week's pattern

<!-- AGENT:pattern — What the last 7 checkpoints show TOGETHER that no single day showed. Direction of travel. -->

**The pipeline is running several stages ahead of the film's material, and each day's work widened
the gap rather than closing it.**

Read day by day, this was an excellent week. 08-04 built the Stage-A compiler and runner. 08-05
unblocked Stage A and landed D-017's machine-checkable canon. 08-06 swapped in a local generator and
closed a whole vocabulary of drift with the medium law. 08-07 made the hand-drawn board readable and
made `shots.json` canonical. The weekend added a film-level continuity pass, a props canon, and
`shot_id`-bound registries. Every one of those is real, well-argued, and aimed at a named problem.
Four of five daily verdicts read ALIGNED.

Read as a week, one number reframes all of it: **26 of 28 `yugioh` shots have no drawing on disk.**
`panel_reader.py` is built and has almost nothing to read. `continuity_pass.py` reads a record whose
shots have no panels. The props canon binds an author who is not being run. The system got materially
better at consuming input that does not exist yet, five days running.

The 08-07 checkpoint saw the leading edge of this — *"pipeline, not film, two days in a row is the
ratio to watch"* — and the weekend made it four. The last thing that moved the film itself was the
shot-02 hero selection on 08-06.

**The second pattern is corrective churn, and it is now structural rather than incidental.**
D-018 → D-019 → D-020 governed one seam in 36 hours. `hearthlight-asset-sheets` was written and
deleted 21 minutes later. The imported outside practice was corrected 35 minutes after landing. This
week's `PRD-SHOT-WORKSPACE.md` opens with a section titled *"The correction that reorganizes this
document"* and spends its first page establishing that most of what its own prior draft proposed is
already built. **Every one of those corrections was right, and every one was caught by a human
reading within the hour.** The velocity is not the problem; the dependence on Vince being at the desk
during the window is. That is the failure mode to design against, not the speed.

**The third pattern is the one nobody acted on.** *"Push from Windows"* has been the top recommended
action on 08-04, 08-05, 08-06 and 08-07. It is now **20 unpushed commits and seven days**. Every
artifact named above exists on exactly one disk.

## Distance to v1

<!-- AGENT:v1-progress — Where the Yu-Gi-Oh! film and the pipeline actually are against GOALS.md's v1 definition. What moved, what did not, what is now the binding constraint. -->

v1 = **the finished Yu-Gi-Oh! film + the architecture that finished it.** Both halves.

**The architecture half moved a long way.** Stage A went from blocked-by-hash to
awaiting-Vince's-approval. Stage 6 has a local, unmetered, working generator. The board is
machine-readable with a defensible authority order. The shot record is canonical and the workbook is
a one-way export. Cross-shot continuity has an agent. Asset bindings survive renumbering. Canon
conformance is machine-checked. Judged alone, this half is close to a defensible v1.

**The film half did not move.** No still approved this week, no clip generated, no gate advanced.
`status.yml` still claims gates 0–3 never happened.

**The binding constraint is no longer code. It is boards on disk.** Eighteen shots name panel files
that do not exist; eight name none. Until those are photographed and dropped in, every stage built
this week idles. Nothing in `PROPOSALS.md`, and nothing this workshop could build, changes that — it
is a half hour with a camera and `workflows/board-intake.md`, which is idempotent and already
written.

**The honest risk:** the second-most-likely thing to happen next is another excellent week of
architecture. `PRD-SHOT-WORKSPACE.md` — 636 lines, `authority: draft`, added over the weekend — is a
proposal to rework the Shot Workspace, which is the surface the film is currently sitting still on.
It deserves the prior question from `GOALS.md` asked out loud before any of it is built.

## Architecture coherence

<!-- AGENT:coherence — Read the mechanical findings below as questions, not verdicts. Duplication, rot, components with no v1 justification, accumulating debt. -->

**The suite could not be collected. Nobody knew, because nobody could run it.**
`pytest` is absent from the Cowork sandbox, so seven consecutive checkpoints reported `not run`.
Installed it this run and found that `pytest` from the repository root **aborted during collection**:
`staging/overview-ui/test_productions.py` imports `film_study_tool.*`, a sibling repository not
vendored here, so the run returned *no results at all* — not failures. Every claim about the suite's
pass rate since 08-04 (`PRODUCT_SPEC.md` §6's "25 helper tests", "all 17 tests pass") was made
without running it. Fixed with a root `conftest.py`; real state now recorded: **39 collected, 32
pass, 7 fail, all 7 environmental** (the sandbox cannot `rmtree` a `TemporaryDirectory` on a mounted
Windows folder). This is `GOALS.md` core problem 4 one level up — a check that was systematized but
never actually executed is not a check.

**Five of those seven failures test retired code.** `test_image_pass.py` covers `image_pass.py`,
disabled in the skill text since 08-04. See P-012.

**Oversized SKILL.md is not the finding the heuristic thinks it is.** Six files over 12 KB, with
`hearthlight-image-prompts` at 19.8 KB. But D-023 (2026-08-06) chose *distribution over splitting* on
purpose — asset-sheet material went into the skills that already owned those asset types rather than
into a new skill. Growth in these files is the direct consequence of a law that is working. The one
worth watching is `hearthlight-image-prompts`, which now carries 12 scripts, 7 references and 4 test
files and is doing the work of a subsystem inside a skill — but splitting it would re-create exactly
the second-source-of-truth D-023 deleted. **No action. Not a defect.**

**`guides/` and `workflows/` describe the same two routes, and the inversion is worth watching.**
Both READMEs cross-link and declare distinct roles — specifications for agents, plain language for
Vince — so the duplication is deliberate and defensible. But `guides/shot2video.md` is **172 lines
against the specification's 84**. The document declared secondary is now twice the length of the
authority. That is the shape that precedes divergence, and the next time one is edited without the
other it will have diverged. Naming it this week; proposing a merge if the gap widens. **Not yet a
proposal.**

**The unfinished-marker count was measuring itself.** Seven of ten hits were `governance/` files
*defining* the markers, including `checkpoint.py` matching its own regex. Excluded `governance/` from
that scan; the count is now **2**, of which **1 is real** (`ROADMAP.md` § Open questions).

**Concurrent edits confirmed, D-012 holding.** `PRODUCT_SPEC.md` changed underneath this run —
another surface added the continuity-pass pipeline row and the `shot_id` engine law while this
workshop was editing the same file. Nothing was lost; this run trimmed its own overlapping paragraph
rather than restating. Worth recording that the working agreement survived a genuine collision.

**The tests write into the repository.** The dashboard and image-prompt suites build their
`TemporaryDirectory` inside the tests folder rather than the system temp dir. On a mounted Windows
folder, cleanup fails and the directories are left behind — and cannot be removed from the sandbox.
Six were created by this run's test execution and are now gitignored, but they need deleting from
Windows. Root cause is a test-hygiene defect, not the mount.

## New proposals

<!-- AGENT:proposals — Ideas generated this week. Each names the v1 blocker it removes, or it is parked. Respect the WIP limit -- a new idea must displace a worse one, not just be added. -->

**Two.** 5 open + 2 = 7, at the limit and nothing displaced. Both are written in full in
`PROPOSALS.md`.

**P-012 — retire `image_pass.py`, `two_pass.py`, `test_image_pass.py`.** *(RED — deletion, so
permanently a proposal.)* Disabled in the skill text since 08-04, flagged as a retirement candidate
on four consecutive checkpoints, and now provably harmful: 5 of the suite's 7 failures come from a
path nobody runs, so a genuine Stage-A regression would arrive as "7 failures instead of 7 failures."
The commit guard for the stage v1 sits on has its signal owned by dead code.

**P-013 — P-004 has no tier that can execute it.** It is marked **GREEN** ("execute, commit, report
after") but ratifying `yugioh/status.yml` means writing inside `projects/`, which D-006 forbids to
the checkpoint and this workshop absolutely. The tier says *no approval needed*; the law says *you may
not go there*. It has sat 7 days not because it is hard or contested but because it is addressed to
nobody. Proposal: add a fourth status, **`vince-only`** — mechanically trivial, zero product
judgment, lives where no agent may write — and have the checkpoint surface those rows as a two-minute
to-do list rather than a decision queue.

**Considered and not proposed,** so the reasoning is on the record:

- *A film-material coverage metric in the checkpoint* (how many shots have panels). It would make the
  starvation visible weekly instead of by audit — but it requires reading `projects/`, which D-006
  forbids, and it adds surface area to solve a problem one honest sentence in this report solves.
- *Merging `guides/` into `workflows/`.* Real risk, not yet realised. See § coherence.
- *Filing `PRD-SHOT-WORKSPACE.md` into `PROPOSALS.md`.* It is `owner: vince` and it is his active
  thinking. Filing his own document for him is process for its own sake. Raised under § What needs
  Vince as a decision he owes, not as a row.

## Pruning candidates

<!-- AGENT:pruning — What should go. Never delete -- surface with the evidence and let Vince decide. -->

| Candidate | Evidence | Where it stands |
|---|---|---|
| `image_pass.py`, `two_pass.py`, `test_image_pass.py` | Disabled in skill text since 08-04; owns 5 of 7 test failures | **P-012**, this run |
| `.agents/skills/krea-{animation,generate,marketing}` | ~484 KB, 18+ scripts, **zero** references anywhere in the repo. Flagged every checkpoint since 08-03 | **P-001**, open 7 days |
| `HANDOFF.md` | States Talefeather's grief reasoning as *engine* law — the exact leak D-003 exists to prevent — and a fresh agent reads it | **P-006**, open 7 days |
| `recovery/` | 17 untracked files, unchanged since 08-06 22:16, no README, no attribution. Flagged 5 consecutive checkpoints | **Left alone**, per the runbook — probably another agent's in-flight work. Wants a README or a delete, and only Vince knows which |
| `hearthlight-shot-crew`, `hearthlight-reference-report` | Both EXPERIMENTAL, no evidence of real use on either project | Watching. Neither costs anything sitting still; `shot-crew` is the most expensive component per shot *if invoked* |
| `staging/overview-ui/productions.js` + `.mjs` | Both 1826 lines, committed together | Watching — Studio's final home is undecided (`ROADMAP.md`), and that decision should settle this |

**The count that matters for this section:** this workshop's GREEN pass added one file (`conftest.py`)
and removed none. It corrected six documents and one scanner. That is an acceptable ratio for a first
workshop, but the runbook's warning applies from here — if next month's workshops have added more
surface than they removed, the workshop is the problem.

## What needs Vince

<!-- AGENT:ask — Amber proposals awaiting approval, and any unanswered NEEDS VINCE marker over a week old. -->

**Blocking v1 directly:**

1. **Photograph the boards.** 26 of 28 shots have no drawing on disk. `workflows/board-intake.md` is
   written, idempotent and waiting. This is the binding constraint — nothing built this week runs
   without it.
2. **Push.** 20 commits, 7 days, one disk. Recommended first on four consecutive checkpoints.

**Decisions owed, oldest first:**

| Item | Age | What it costs while open |
|---|---|---|
| **P-011** — headless front figure on the character sheet | 5 days | The sheet is `image2` on *every* video job; the smeared-face failure is inherited by every clip |
| **P-004** — ratify `yugioh/status.yml` | 7 days | Video prompts are being written against a ledger claiming the image gate never happened. See **P-013** — this one is stuck by construction |
| **P-001** — fate of the three `krea-*` packs | 7 days | 484 KB of ambiguity every agent must resolve, at the exact stage v1 is at |
| **P-002** — canonical source for the `hearthlight` router | 7 days | The first file every agent reads is the one place D-002 is not followed |
| **P-006** — move `HANDOFF.md` to `archive/` | 7 days | A fresh agent inherits the wrong North Star |
| **P-012, P-013** | new | See above |
| **`PRD-SHOT-WORKSPACE.md`** | 3 days | 636 lines, `authority: draft`, proposing a rework of the surface the film is currently sitting still on. It needs the prior question asked out loud — *does this move the film, or harden the pipeline carrying it?* — before any of it is built |

**Open longer than a week, mentioned once per the runbook:**

- `ROADMAP.md` open questions 1, 3, 4 — unanswered since 2026-08-03.
- Question 5's inherited near-term list — **six weeks** without review.
- `GOALS.md` Product principle 2 still reads *"the locked style block … those **are** the
  deliverable"*, while D-020 reworded that law to *"apply through the stage's declared
  conditioning."* Flagged 08-05. `GOALS.md` is RED and was not touched; the principle wants one
  sentence from you, or the law is narrower in practice than it reads.
- `DECISIONS.md` still has no row for **D-016**, whose frame-one and no-motion protections `D-018.md`
  says remain in force. Fourth consecutive flag. Rewriting a decision is RED.

**Housekeeping only you can do (Windows):** delete
`skills/hearthlight-dashboard/tests/tmp*/` — six directories this run's test execution created and
the sandbox cannot remove. They are gitignored, so nothing is at risk; they are just litter.

---

## Mechanical findings

<!-- Generated by governance/checkpoint.py. Heuristics, not verdicts. -->

- Proposals: **5 open** of 7 allowed
- Large SKILL.md (split/merge candidates): hearthlight-character (12KB), hearthlight-comfyui-graph (12KB), hearthlight-conventions (14KB), hearthlight-image-prompts (19KB), hearthlight-mise-en-scene (15KB), hearthlight-shot-runner (12KB)
- Scripts with no test: hearthlight-clip-extractor (1), hearthlight-selfcheck (1), hearthlight-timing-intake (4)
- ⚠ Stale skill counts: HANDOFF.md says 17, actual 23
- Commits in window: 31 (UNATTRIBUTED: 5, chatgpt: 1, cowork: 25)

*Facts: `checkpoints/.facts-2026-08-10.json`*
