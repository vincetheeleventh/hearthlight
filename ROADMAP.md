# ROADMAP — what Hearthlight is currently trying to change

*Updated by the daily checkpoint when evidence changes. Items marked **CONFIRMED** came from Vince
or from an explicit statement in the repository. Items marked **INFERRED** were derived from file
activity and may be wrong — correct them freely.*

Last updated: 2026-08-03 · Source: `HANDOFF.md` §5–6 (2026-07-06), file mtimes, `status.yml` ledgers.

---

## Actively under development

**Governance layer — this system.** *(CONFIRMED — Vince, 2026-08-03)*
Canonical docs, skill inventory, daily checkpoint, Miro sync, multi-agent coordination.

**Image generation pass.** *(INFERRED — highest recent churn)*
`hearthlight-image-prompts` carries 6 scripts and 2 test files — by far the most code of any skill
(`image_pass.py`, `two_pass.py`, `krea_style_comp.py`, `check_frame_one.py`). `.test-tmp/image-pass/`
holds 10 temp run directories. This looks like the active engineering front.

**Dashboard + shot identity.** *(INFERRED — most recently touched, 2026-08-03)*
`hearthlight-dashboard` gained a shot registry, a backfill script, and
`references/SHOT-IDENTITY-PROTOCOL.md`. Newest substantial work in the tree.

**Outline and storyboard skills.** *(INFERRED — both modified 2026-08-03)*
Reason unknown; no note in the repository explains the change.

---

## Near-term priorities

From `HANDOFF.md` §5, dated 2026-07-06 — **four weeks old and unverified.** Status below is my
reading of the current tree, not Vince's confirmation.

| # | Item | Apparent status |
|---|---|---|
| 1 | Confirm the Telegram bot responds | Unknown |
| 2 | Remove dangling `profiles\gemma\skills` symlink | Unknown — outside this repo |
| 3 | Finish `gemma → LocalHermes` rename | **Not done** — `start-gemma-model.bat` still present |
| 4 | Stand up local model on the 3090 | Unknown — outside this repo |
| 5 | Retire WSL Hermes | Likely done — `git-init-commit.sh` still assumes WSL paths |
| 6 | Rebuild the STT venv | **Not done** — `.venv-stt` still dead |
| 7 | Rotate + wire the RunningHub key | **Unknown — verify before Stage 6** |
| 8 | Verify the Notion MCP token | Unknown |
| 9 | "Love list" — positive side of `TASTE.md` | **Not done** — `TASTE.md` has Reaches-for / Kills / Rules, no swipe file |
| 10 | Interview skill (question craft for the recording session) | **Not built** |
| 11 | Cold-viewer subagent (fresh-eyes pass on the assembled cut) | **Not built** |

> ⚠️ **NEEDS VINCE** — this list has not been reviewed in four weeks. Which of these are still real?

## The v1 target — CONFIRMED by Vince, 2026-08-03

**v1 = the finished Yu-Gi-Oh! film + version one of the system architecture that finished it.**
Full definition in `GOALS.md`. This supersedes `HANDOFF.md` §6, which named McConaughey as the pilot
to push end to end. **`yugioh` is the active film; `mcconaughey-call` is not the v1 target.**

Current position and the road out:

| Phase | State |
|---|---|
| Storyboard | **Done** — `yugioh/status.yml` shows `gate4_storyboard: approved 2026-07-30` |
| **Image pipeline** | **ACTIVE.** Style/composition compiler + paid runner calibrated on Shots 1–2: exact frame-one prompts, stable IDs, raw K2 parameters, durable resume. Remaining 26 unique setups await recorded batch cost approval. Likeness + final selection follow. |
| Video | **Next.** Turn project documents into a working video-generation prompt, then refine the process against real output |
| Score | **Later.** ElevenLabs pass for the film score |

**The prioritization rule that follows:** work that does not move the Yu-Gi-Oh! film toward
completion, or harden the pipeline carrying it, gets **parked — not built.** Apply this *before* the
four questions in `GOALS.md` § *Keeping features tight*.

**Note on the gate ledger:** `yugioh/status.yml` shows gates 0–3 as `pending` while gate 4 is
approved — the film advanced faster than the ledger was maintained. Worth a ratification pass so the
record matches reality.

## Gaps opened by the revised North Star — 2026-08-03

`GOALS.md` was rewritten to aim at **AI-filmmaking problems** rather than at a competitor. Three of
its stated outcomes have no implementation. These are now roadmap items, not oversights.

| Gap | Stated in | Where it stands |
|---|---|---|
| **The UI correction loop** — point at what is wrong, prompt gets intelligently corrected | Core problem 1 | The dashboard is **read-only**. Corrections go through chat. This is the largest gap between goal and product. |
| **Audio generation** | Primary outcome 3 | Nothing produces audio. ElevenLabs score is a later phase. |
| **Narrative-drift tracking** | Core problem 6 | `hearthlight-critique` does this on demand at one stage. Nothing holds narrative goals continuously across the film. |
| **Cross-platform prompt shaping** | Core problem 2 | Partly present — `hearthlight-image-prompts`, `-video-prompts`, `seedance-prompt-maker`, `zit-prompt-writer` each target a surface. No shared abstraction; each is bespoke. |

## Long term

**A system that outlives its models.** *(CONFIRMED — `GOALS.md` core problem 5, 2026-08-03)*
New models obsolete old workflows. Hearthlight is expected to adopt new ones, **retire skills that no
longer earn their place**, and adapt what remains. Retirement is a goal, not housekeeping — which
makes the `SKILL-INVENTORY.md` pruning list an adaptation backlog rather than a tidy-up.

**Workflows systematized, not remembered.** *(CONFIRMED — `GOALS.md` core problem 4)*
A workflow that worked gets written into the instruction layer; one that failed leaves a lesson.
This is what makes experimentation cheap rather than lossy.

**A repeatable studio.** *(CONFIRMED — `HANDOFF.md` §6, still current in intent)*
Wire Stage 6 properly, template the pipeline so the next film is faster than the first, and prove the
partner behaviours in real use: the offer protocol firing at seams, `TASTE.md` actually shaping
proposals, the crew arguing rather than complying.

---

## Known problems

1. **`git-init-commit.sh` could never succeed.** Its leaked-key guard greps for a key literal that is
   written inside the guard itself, so it always self-aborted — which is why no repository existed
   until 2026-08-03. Superseded by `governance/checkpoint.py` (hash-based). *(Resolved 2026-08-03.)*
2. **`README.md` is stale.** Its layout tree omits 7 of 21 skills and still describes
   `hearthlight-asset-bible/` as a tombstone to delete; that folder no longer exists.
3. **`HANDOFF.md` predates the engine/client split** (2026-07-06) and states Talefeather's grief
   reasoning as engine law — the exact bounded-context leak `AUDIENCE-CONTEXT.md` was written to fix.
   It also says "all 17 skills"; there are 21.
4. **Four pointer stubs cite `AUDIENCE-CONTEXT.md` as "the emotional register"** — that file is now
   only a signpost, so the stubs route agents to a redirect instead of the client profile.
5. **`hearthlight-dashboard` is absent from `AGENTS.md`.** The operating index does not list it, so a
   session that reads only `AGENTS.md` never learns it exists.
6. **The `hearthlight` router skill has no canonical source** in `skills/` — it lives only in the
   Claude skill store, which contradicts the pointer-stub decision it is built on.
7. **`.agents/skills/krea-{animation,generate,marketing}`** — three vendored skill packs, ~484 KB,
   with zero references anywhere in the repository.
8. **`.venv-stt` is dead**, blocking the hand-drawn-board intake path.

## Experiments

- **The shot crew as subagents.** Whether eight roles produce genuinely distinct, arc-aware opinions
  rather than eight paraphrases is untested. `HANDOFF.md` §6 names watching this in the TUI as the
  verification step. Cost per contested shot is unmeasured.
- **Two-pass image generation** (`two_pass.py` + `krea_style_comp.py`) — no note explains whether
  this beat single-pass.
- **The pointer-stub layer.** Solves drift in principle; four stubs already carry a stale reference,
  which is early evidence that stubs still need maintenance.

## Open questions

1. ~~Is the deliverable the film or the engine?~~ ✅ **EFFECTIVELY ANSWERED 2026-08-03** — v1 requires
   **both**: the finished film *and* the architecture that finished it. Neither alone.
2. ~~What does "done" look like for v1?~~ ✅ **ANSWERED 2026-08-03** — see *The v1 target* above.
3. Should `HANDOFF.md` be retired now that `GOALS.md` / `PRODUCT_SPEC.md` / `ROADMAP.md` exist?
   **Sharper now:** its §1 states the *old* problem framing (competitors producing generic memory
   books) that the revised `GOALS.md` replaced with AI-filmmaking problems. It is no longer just
   stale — it contradicts the North Star.
4. Do the three vendored `krea-*` packs stay, or go?
5. ~~Is `hearthlight-dashboard` product or personal utility?~~ ✅ **ANSWERED 2026-08-03** — product
   surface. `GOALS.md` primary outcome 4.
6. **New:** the revised `GOALS.md` dropped the non-goals section and the open North Star questions
   (film-vs-engine, Talefeather-as-only-client, commercial shape). Deliberate, or lost in the edit?
   The non-goals were doing real work — *"not an app that spits out a video"* in particular now sits
   awkwardly against primary outcome 2, which asks for exactly that ease.
