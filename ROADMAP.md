---
doc: ROADMAP
role: current-work
authority: canon
owner: agents
updated: 2026-08-04
answers:
  - what is being built right now
  - what stands between here and v1
  - which stated goals have no implementation
  - what is known to be broken
not_here:
  what is already built: PRODUCT_SPEC.md
  why a rule exists: DECISIONS.md
  which components exist: SKILL-INVENTORY.md
  what is proposed but undecided: PROPOSALS.md
archive: archive/roadmap.md
---

# ROADMAP — what Hearthlight is trying to change

**CONFIRMED** = Vince said it. **INFERRED** = an agent derived it from the tree and it may be wrong;
correct it freely.

---

## The v1 target *(CONFIRMED)*

**v1 = the finished Yu-Gi-Oh! film + version one of the architecture that finished it.** Both
halves. Full definition in `GOALS.md`. `yugioh` is the active film.

| Phase | State |
|---|---|
| Storyboard | **Done** — boards drawn, photographed and linked to the shot record |
| **Board intake** | **BUILT 2026-08-06, STARVED.** `shots.json` is canonical, the workbook is a one-way export, and `panel_reader.py` reads the drawings. But **2 of 28 `yugioh` shots have a panel on disk** — 18 name missing files, 8 have none. The route is `workflows/board-intake.md` and it is idempotent; it needs boards, not code. |
| **Image pipeline** | **ACTIVE.** Studio Shot Vision and the visibility-aware Krea compiler are built. The Film Brief's 16:9 widescreen master governs Stage A. Prompt Board approval precedes the remaining composition batch; likeness and final selection follow. `set_shot_image.py` overrides a shot's chosen still and writes the ledger row. |
| **Video** | **STARTED 2026-08-05.** Generator is **local ComfyUI MiniMax H3** (`minimax_h3_i2v_int8`), confirmed on Shot 1; RunningHub Seedance parked. Two routes run in parallel — `workflows/`. Prompt packets written for shots 2 and 8. Refining the process against real output is the work. |
| Score | **Later.** ElevenLabs pass. |

**The prioritization rule:** work that does not move this film toward completion, or harden the
pipeline carrying it, is **parked — not built.** Apply it *before* the four questions in `GOALS.md`
§ *Keeping features tight*.

## Actively under development

**Prompt quality per shot** *(CONFIRMED — Vince, 2026-08-04)*
The craft problem, not the plumbing: language that makes a model render what he actually saw. A
focused Shot Prompt Author guide now turns the research into active LLM context; Python grounds and
lints the result; an independent Hermes semantic reviewer blocks weak or unsupported prompts and
permits one repair. Local author/reviewer contract tests pass. Real OpenRouter forward-testing awaits
Vince's explicit approval to send the project source bundle to that external provider.

**Image generation pass** *(INFERRED — highest churn)*
`hearthlight-image-prompts` carries 6 scripts and 4 test files. Stage A uses `prompt_authoring.py`
(Shot Vision → production object), `krea_style_comp.py` (approved packet plan), and
`krea_style_comp_run.py` (paid durable run).

**Hearthlight Studio** *(CONFIRMED)*
The production cockpit. Shot-first project view, editable/versioned Shot Vision, technical storyboard
source, Prompt Board approval, review controls, and durable generation queueing. It lives in the
separate Film Study Tool repository and runs on port 8765. Project-stage reporting has been removed;
the active state model is per-shot Design / Production / Inputs.

**The shot2video / board2video trial** *(CONFIRMED — Vince, 2026-08-05, D-022)*
Two routes from storyboard to clip run in parallel. **shot2video** approves a conditioning still per
shot then does i2v; **board2video** skips the still and conditions on asset sheets plus a board
sheet. The selection guide in `workflows/README.md` states where each *should* win, written before
the trial so the trial can falsify it. **The comparison ledger is empty** — until it has rows, the
question is settled by memory, which is what D-022 exists to prevent. Two skills support it:
`hearthlight-acting` (performance, cross-cutting) and `hearthlight-board-sheet` (EXPERIMENTAL, and
its generator surface — `MiniMaxH3ReferenceToVideo` — is mapped but untried).

**Medium as a spec-level law** *(CONFIRMED — Vince, 2026-08-05)*
`medium: illustrated | live-action` in `project.json`. Illustrated bans photographic
vocabulary from prompts — bokeh, focus plane, shutter blur, pore-level skin, the `Photoreal` tag.
Every current project is illustrated; the photoreal material is parked in
`hearthlight-video-prompts/references/live-action/` behind a README explaining why not to open it.

**Portability** *(CONFIRMED — D-021)*
Code moves by git, creative work by Syncthing (`governance/syncthing/`). Story Studio's root resolves
per-OS. **Open risk:** `hermes` on macOS is unverified — without it, Telegram approvals and
`production_generation_worker.py` fail. Also live: the Film Study Tool sits inside OneDrive on
Windows, and OneDrive plus Syncthing over the same files will produce conflict storms.

**Governance layer** *(CONFIRMED)*
Canon docs, checkpoint, weekly workshop, Miro sync, multi-agent attribution.

## Gaps between stated goal and built product

| Gap | Stated in | Where it stands |
|---|---|---|
| **Voice-rant review parsing** — turn whole-board spoken critique into confirmed shot revisions | Core problem 1 | Shot Vision, compilation, prompt approval, generation history, and revert are built. Automatic parsing/confirmation of a whole-sequence rant remains. |
| **Cross-platform prompt shaping** | Core problem 2 | Four bespoke translators (`image-prompts`, `video-prompts`, `seedance-prompt-maker`, `zit-prompt-writer`) with no shared abstraction between them. The **medium law** (2026-08-05) closes one axis of it — the vocabulary a whole medium may not use — at the spec layer rather than per prompt. |
| **Narrative-drift tracking** | Core problem 6 | `hearthlight-critique` does this on demand at one stage. Nothing holds the narrative goals continuously across the film. |
| **Audio generation** | Primary outcome 3 | Nothing produces audio. |

## Long term

**A system that outlives its models** *(CONFIRMED — `GOALS.md` core problem 5)*
New models obsolete old workflows. Hearthlight adopts new ones, **retires skills that stop earning
their place**, and adapts the rest. Retirement is a goal, which makes the `SKILL-INVENTORY.md`
pruning list an adaptation backlog rather than a tidy-up.

**Workflows systematized, not remembered** *(CONFIRMED — core problem 4)*
A workflow that worked gets written into the instruction layer; one that failed leaves a lesson.

**A repeatable studio** *(CONFIRMED)*
Wire Stage 6 properly, template the pipeline so the second film is faster than the first, and prove
the partner behaviours in real use: the offer protocol firing at seams, `TASTE.md` shaping
proposals, the crew arguing rather than complying.

## Known problems

1. **`.agents/skills/krea-{animation,generate,marketing}`** — three vendored packs, ~484 KB, zero
   references anywhere in the repository. (P-001)
2. **The `hearthlight` router has no canonical source** in `skills/` — it exists only in the Claude
   skill store, the one place D-002 is not followed. (P-002)
3. **Four pointer stubs cite `AUDIENCE-CONTEXT.md` as "the emotional register"** — a root path that
   does not resolve. Point them at `profile/clients/talefeather/AUDIENCE-CONTEXT.md`, and only for
   projects declaring `client: talefeather`.
4. **`.venv-stt` is dead**, blocking the hand-drawn-board intake path.
5. **`.gitignore`'s `*.png` matches every PNG at any depth**, not just the root as its comment
   claims. Reference images cannot be tracked without `-f`.
6. **The image-prompt tests read live `projects/yugioh` data** — exact counts and cell addresses —
   so editing the shot list fails the suite and can block a checkpoint commit.
7. **The image ledger is write-only.** `yugioh/04-images/` holds 68 PNGs; `generations.jsonl` knows
    30, and all 30 read `selected_final: false`. Which still is the approved base for a shot is
    answerable only by folder name — the row-number failure D-009 exists to prevent, one level up.
    *Partly addressed 2026-08-05:* `set_shot_image.py` now writes a paired `generation` +
    `selection` row when a still is chosen, so shots overridden through it are answerable. Shots
    selected before it are not.
10. **`hermes` on macOS is unverified** (D-021). Without it the UIs run but Telegram approvals
    and `production_generation_worker.py` fail — the one open risk in the port.

*Both found by the structure audit: `governance/audits/2026-08-04-yugioh-structure.md`. The
directory restructure that would fix the first is parked until `yugioh` ships (P-007).*

## Experiments

- **The shot crew as subagents.** Whether eight roles produce genuinely distinct, arc-aware opinions
  rather than eight paraphrases is untested. Cost per contested shot is unmeasured.
- **Two-pass image generation** — compile then run. No note records whether it beat single-pass.
- **The pointer-stub layer.** Solves drift in principle; four stubs already carry a stale reference,
  which is early evidence that stubs still need maintenance.

## Open questions

> ⚠️ **NEEDS VINCE** — these block honest alignment judgments.

1. Do the three vendored `krea-*` packs stay or go?
2. Is Talefeather the only client, or the first of several? The client layer is built for many and
   serves exactly one.
3. Does Hearthlight have a commercial shape?
4. `GOALS.md` dropped its non-goals list. Deliberate? *"Not an app that spits out a video"* was
   doing real work and now sits awkwardly against primary outcome 2, which asks for exactly that ease.
5. The near-term list inherited from `HANDOFF.md` §5 — Telegram bot check, `gemma → LocalHermes`
   rename, local model on the 3090, STT venv rebuild, RunningHub key rotation, Notion token, the
   `TASTE.md` love list, an interview skill, a cold-viewer subagent — has not been reviewed in five
   weeks. Which are still real? *(Full list: `archive/roadmap.md`.)*
