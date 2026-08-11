---
doc: PRODUCT_SPEC
role: current-state
authority: canon
owner: agents
updated: 2026-08-11
note: "§1 What the product is — written by Vince 2026-08-11. Definition of record (D-025)."
answers:
  - what is actually built and working today
  - which stage each skill owns
  - which rules are machine-enforced rather than advisory
  - what the known limitations are
not_here:
  what is being built next: ROADMAP.md
  why a rule exists: DECISIONS.md
  how to operate it: USER-GUIDE.md
archive: archive/product-spec.md
---

# PRODUCT_SPEC — Hearthlight as it actually exists

*Descriptive, not aspirational. If it is not built, it does not belong here — it belongs in
`ROADMAP.md`.*

---

## 1. What the product is

Hearthlight is a **single-operator ai filmmaking tool** that makes it easy to go from story vision to ai-generated image and video assets. It helps organize and transform the director's input (storyboards, verbal expression of vision, narrative beats, etc) into a format that's ready for ai generation (prompts, generation settings, etc). 

This is combined with "Film Study Tool" user interface to be a visual shot tracker and production dashboard. The user iterates on their film using Hearthlight, so It's secondary role is visualize the current state of the film.

Hearthlight itself is being iterated on as the user makes films, (improving the agent instructions and skills, adding features to reduce friction points, etc) improving the user-hearthlight dynamic.

**Nothing about a project is assumed.** `format`, `client` and `charged_register` are declared in
each project's distribution spec and obeyed; guessing one is a defect (`DECISIONS.md` D-025).
Talefeather — grief / living-legacy — is one *client*, loaded only when a project asks for it.
`client: none` is the normal value.

**Runtime surfaces**:

| Surface | How it runs | Role |
|---|---|---|
| **Film Study Tool** (Hearthlight Studio) | Local Python HTTP server, browser UI. Separate repository. | Vince's primary point of contact. Shot tracker and production dashboard: the film's current state, and the controls that move it |
| **Hermes + Telegram** | Hermes gateway, own profile, own bot | Dictating a Shot Vision, approving a shot, running a stage from the phone |
| **Claude Cowork / ChatGPT** | Agent sessions over the same files | Building and improving the tool itself |

The three share no memory. **The files are the only coordination medium** — see `AGENTS.md`
§ *Multi-agent working agreement*.

## 2. Major features

- **Aesthetic single-source-of-truth.** The mise-en-scène holds a LOCKED style tier and a COMPOSED
  world tier; every prompt is assembled from it verbatim.
- **Batch render execution with a durable ledger.** Fresh subagent per shot, two-stage review, and a
  progress ledger so a crashed session never re-pays for a completed generation.
- **Agent-authored, visibility-aware Krea style/composition execution.** Versioned Shot Vision and
  source-grounded visual context feed a focused, tool-restricted Hermes Shot Prompt Author. The LLM
  writes the intelligent shot-specific prompt body; Python enforces identity, visibility, ownership,
  one-instant, provider-language, source-hash, and request-control invariants, then passes the prose
  through without appending aspect, style, or acceptance checklists. An independent Hermes semantic reviewer may block incoherent or unsupported prompts and
  allows one source-preserving author repair before the Prompt Board. Exact approval and request
  fingerprints make spend and resume safe.
- **A deliberating shot crew.** Eight illustration roles negotiate contested shots as subagents.
- **Timing round-trip with real editors.** Storyboard Pro Final Cut XML in; DaVinci Resolve FCP XML out.
- **Persistent taste memory.** `profile/TASTE.md` records what Vince kills and reaches for, read by
  the critique, outline, and mise-en-scène stages.
- **A visual production cockpit (Hearthlight Studio).** The Film Study Tool and live Hearthlight
  projects share one URL-backed shell. The default project view is shot-first: stage-coloured hero
  thumbnails, stable Shot IDs, compact review controls, a collapsible requirements/assets drawer,
  and a direct opener for the registered shot-list workbook. From the overview or shot page, Vince
  can edit/dictate and individually save versioned Shot Vision inside each shot page. Each save versions
  only that shot and compiles its current Krea prompt. Vince can inspect compiled prompts, references,
  warnings and spend estimates on the collapsed Prompt Board, approve the exact batch, queue generation,
  review versions, and insert, retire, or restore shots without changing permanent identity.
  Stage-A prompts compile from the Vision and are editable in place; saving one writes the canonical
  record, so the edit is what the next compile and the next generation both read. Likeness prompts
  remain manual. Approving a shot is Vince's, always.
  Studio Shot Vision plus the permanent-ID shot registry are the live authority. Imported hand-drawn
  board workbooks are immutable archived references; current spreadsheets are generated handoff exports
  and never silently replace Studio state or block image-prompt compilation. This is mechanical, not
  aspirational: `shots.json` is canonical, `shot_record.py` writes it and logs the applied revision to
  `shot-edits.jsonl`, and `export_shotlist.py` regenerates the workbook one-way.
  **Source: the `Film Study Tool` repository** (`film_study_tool/`), not this one. `staging/overview-ui/`
  holds a frozen copy from 2026-08-04 that no longer matches the running UI — see § 6.

- **The shot page is a spine plus three tabs.** Storybreaking leads with the beat strip — every shot
  in the beat, panels large — because "does this shot earn its place" is a comparative question. Shot
  Design holds the board, the Vision editor and frame-one. Production shows renders only, the hero
  paired with the prompt that made it and the generator beside it. A persistent spine carries intent,
  three status axes and the `never` list; everything else collapses behind labelled drawers.
- **Three status axes, not one done/not-done.** `Design` (Exploring / Designed / Locked) and
  `Production` (Not started → Approved) are independent, so *Design: LOCKED · Production: NEEDS FIX*
  says fix the image rather than reconsider the shot. **`Inputs` (Ready / Stale / Broken)** is
  machine-computed and blocks generation: it catches a registry binding by number, an unlinked panel,
  a missing canonical prompt. Design and Production describe what Vince thinks; Inputs describes
  whether the machine is being fed correctly.
- **The hand-drawn board is machine-readable.** `panel_reader.py` resolves `board_panels` to files,
  extracts panels embedded in the workbook, attaches the current Shot Vision and adjacent shots, and
  records readings to `panel-readings.jsonl`. The authority order is fixed in
  `hearthlight-image-prompts/references/PANEL-READING.md`: a panel is **TIER 3 baseline evidence,
  never above the current Shot Vision**; it is authoritative for framing, blocking, screen geography,
  eyeline, scale and exclusion, and never for wardrobe, colour, light, texture, likeness or period.
  Absence of detail is never an instruction. Conflicts are reported, never resolved.
- **A film-level continuity pass.** The author, the panel reader and the reviewer each see one shot,
  which makes cross-shot disagreement structurally invisible — shot 1 said *"Yu-Gi-Oh trading cards"*
  and shot 5, its declared setup echo, said *"trading cards"*, and every single-shot reviewer passed
  both. `continuity_pass.py run --project {slug}` reads the whole record before a batch and **reports
  without resolving**. Contract: `hearthlight-image-prompts/references/CONTINUITY-PASS.md`.
- **Asset bindings survive renumbering.** A number-bound registry does not fail loudly — it hands the
  author the wrong character sheets. `rekey_assets.py` migrates existing number bindings to
  `shot_id`. The law and its enforcement are in §4.
- **Plumbing self-check.** Separates mechanical failure (the system's fault, fixable) from quality
  judgment (Vince's call, unautomatable).

## 3. The pipeline — stages and owning skills

| #    | Stage                                                                                                                 | Owning skill                                              |
| ---- | --------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| 0    | Distribution spec (format, client, charged register, aspect)                                                          | `hearthlight-distribution-spec`                           |
| 1    | Intake / transcription                                                                                                | `hearthlight-conventions`                                 |
| 1.5  | Ideation → Vision Brief                                                                                               | `hearthlight-consolidate`                                 |
| 2    | Story Arc → Beat Sheet → A/V Script                                                                                   | `hearthlight-outline`                                     |
| 2.5  | Story pressure-test                                                                                                   | `hearthlight-critique`                                    |
| 3    | Mise-en-scène / Aesthetic Bible                                                                                       | `hearthlight-mise-en-scene`                               |
| 3.5  | Character dossiers + turnaround sheets                                                                                | `hearthlight-character`                                   |
| 3.7  | Timing intake / timeline export                                                                                       | `hearthlight-timing-intake`                               |
| 3.9  | Clip prep for storyboarding                                                                                           | `hearthlight-clip-extractor`                              |
| 3.95 | Board intake — panels to files, `shots.json` canonical                                                                | `workflows/board-intake.md` + `hearthlight-dashboard`     |
| 3.98 | Film-level continuity pass — one agent with every shot in view, reports cross-shot disagreement and never resolves it | `hearthlight-image-prompts` (`continuity_pass.py`)        |
| 4    | Conditioning stills                                                                                                   | `hearthlight-image-prompts`                               |
| 4.5  | Shot design by crew                                                                                                   | `hearthlight-shot-crew`                                   |
| 5    | Storyboard: motion, duration, transitions                                                                             | `hearthlight-storyboard`                                  |
| 6    | i2v clips — local ComfyUI MiniMax H3 (RunningHub Seedance parked)                                                     | `hearthlight-video-prompts` + `hearthlight-comfyui-graph` |
| 6b   | Board sheet for board2video — 10–15s sequence as one image                                                            | `hearthlight-board-sheet` *(EXPERIMENTAL)*                |
| —    | Batch execution at stages 4 and 6                                                                                     | `hearthlight-shot-runner`                                 |

Cross-cutting: `hearthlight-terse` (voice register), `hearthlight-acting` (performance writing,
both routes), `hearthlight-research` + `hearthlight-reference-report` (world research),
`hearthlight-notion-log` (surfacing), `hearthlight-dashboard` (status), `hearthlight-selfcheck`
(health).

### Two routes from storyboard to clip

Stages 4–6 are not a single path. Two workflows run in parallel, catalogued in `workflows/`:

| Route                                     | How a clip is made                                                                                                                         | Status                        |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------- |
| **shot2video** Shot-Image → Video         | One approved conditioning still per shot, then i2v from that still                                                                | Active — carrying the v1 film |
| **board2video** Storyboard → Video Direct | No still. Asset sheets + style reference condition the clip. **B1** = board image + plain instruction; **B2** = per-shot structured prompt | Active — parallel trial       |

They fail differently, which is why both run. shot2video settles framing in a cheap medium and costs two
review loops; board2video costs one loop but gives the model control of framing and puts the entire load on
the asset sheets. A comparison ledger in `workflows/README.md` records attempts-to-approval per shot
type; the trial concludes on that evidence, not on preference.

Both routes are written down twice, on purpose: `workflows/` holds them as specifications (inputs,
costs, failure modes, the ledger) for agents; `guides/` holds them in plain language for Vince at the
bench, with `guides/assets.md` first because both routes stand on the sheets.

Full per-skill responsibilities, usage evidence, and classification: **`SKILL-INVENTORY.md`**.

## 4. Rules and constraints actually enforced

**Laws** (from `AGENTS.md`, true of every project):

- The machine never approves its own work. Agents draft, run and report; only Vince marks a design
  **Locked** or a shot **Approved**. Approval is per shot on two independent axes — there are no
  gates (D-026).
- No drift — provider conditioning carries the locked aesthetic: Krea Stage A uses its approved moodboard and strength outside prose; stages requiring textual style or signature blocks copy them verbatim.
- Nothing exists only in chat — every artifact lands in `projects/{slug}/`.
- The distribution spec is read before framing; aspect ratio is a composition law, not an export setting.
- The spec declares, the tool obeys — `format`, `client`, `charged_register` are never assumed.
- Image provider priority: OpenAI Codex OAuth → Krea MCP → OpenAI API key, unless a stage pins a surface.
- Rights discipline — the McConaughey pilot is private use only, stylized resemblance, never photoreal.
- Registries bind by `shot_id`, never by shot number. Prop identity lives in `03-bible/props.json`
  and is binding on the prompt author; it is never left to survive as a phrase in storyboard prose.

**Enforcement is shared between instruction and code.** Six areas are machine-checked:
`hearthlight-selfcheck` checks style/composition prompt readiness; the prompt-author compiler validates
source hashes, visibility, ownership, temporal state, provider vocabulary, controls, and semantic-review
pass state; the Krea packet compiler blocks stale approval and dispatch drift; the runner fingerprints
each complete request and resumes recorded jobs; the shot registry refuses to move assets by row
number when a regenerated workbook cannot prove a `Shot ID` match; and `prompt_authoring` refuses a
number-bound registry outright, with a matching selfcheck **RED** per project. Everything else
depends on the agent having read the skill.

**Reported, not enforced.** `continuity_pass.py` is the only pass that sees the whole film, and it
deliberately reports cross-shot disagreement without resolving it — resolution is Vince's. Running it
before a batch is instruction, not code.

## 5. Notable system behaviours

**The pointer-stub layer.** Claude's skill store holds ~1.4 KB stubs named `hearthlight-*` that
contain no instructions — only a pointer to the canonical `SKILL.md` under `Story Studio/skills/`.
This is deliberate: copying contents would create a second version that silently drifts. See
`DECISIONS.md` D-002.

**The router skill.** A skill named `hearthlight` (no suffix) is the session entry point. It exists
**only in the Claude skill store, not in `skills/`** — the sole component with no canonical source
in the repository. See `SKILL-INVENTORY.md` and `ROADMAP.md`.

**Voice register is stated in three places.** `CLAUDE.md` (always-on switch), `AGENTS.md` (summary),
and `skills/hearthlight-terse/SKILL.md` (authoritative). The first two defer to the third explicitly.

**Per-shot approval state.** `Design` (Exploring / Designed / Locked) and `Production` (Not started
/ In progress / Needs fix / Candidate ready / Approved) are computed independently from the shot
record, so *Design: LOCKED · Production: NEEDS FIX* says fix the image, not the shot. `Inputs`
(Ready / Stale / Broken) is machine-computed and is the only state that blocks generation.
Migration off the retired gate ledger: `governance/GATE-REMOVAL.md`.

## 6. Known limitations

- **LLM prompt quality cannot be proven by deterministic tests.** The image-prompt suite carries
  author-contract and visibility golden tests. They verify source
  grounding, rendering boundaries, blocking, and reviewer wiring—not whether the configured external
  model makes a strong visual judgment on every raw shot. Real OpenRouter forward-testing requires
  explicit approval because it sends project material to that provider.
- **The image-prompt tests read live `projects/yugioh` data.** They assert exact generation counts,
  shared-setup pairs, and workbook cell addresses, so editing the film's shot list fails the suite
  and can block a checkpoint commit. A creative decision should not trip a code guard.
- **`pytest` must be present for the checkpoint to verify tests.** Without it the checkpoint reports
  `not run` rather than falsely passing, and `commit` will not block on failures it could not
  observe. It is absent by default from the Cowork sandbox and must be installed per session.
- **Test state: 39 pass in this repository; 154 in the Film Study Tool.** Both suites are green.
  Collection from the repository root depends on a root `conftest.py` that skips
  `staging/overview-ui/test_productions.py` when `film_study_tool` is not importable — without it
  `pytest` aborts during collection and returns no results at all rather than failures, which reads
  as success to anything that only checks for a traceback.
- **`staging/overview-ui/` is a stale duplicate of the Studio UI**, frozen 2026-08-04 at 1826 lines
  of `productions.js` against the running 2419. It is a second source of truth for the same files —
  the thing `GOALS.md` § *Keeping features tight* question 1 exists to prevent. It should be deleted
  and the test that imports from it repointed; until then, read the `Film Study Tool` repository for
  anything about the UI.
- **Laws are advisory to any agent that skips the read.** Nothing prevents an agent from generating
  an image without loading the mise-en-scène.
- **No shared state between the three agent surfaces.** Cowork, Hermes, and ChatGPT coordinate only
  through the files themselves. See `AGENTS.md` § Multi-agent working agreement.
- **`.venv-stt` is dead.** The faster-whisper environment was a Linux venv and did not survive the
  WSL → Windows migration; the hand-drawn-board intake path depends on it.
- **Stage 6 is unproven end to end.** No film has been carried from board to finished cut. The generator is now local
  ComfyUI MiniMax H3, confirmed on `yugioh` Shot 1 (2026-08-05), so the stage is no longer metered or
  remote — but only single shots have been run. The leaked RunningHub key still wants rotating; it is
  no longer on the critical path.
- **Three goals in `GOALS.md` still have no implementation:** audio generation, cross-platform
  prompt shaping, and continuous narrative-drift tracking. Intelligent prompt correction now exists
  before generation through semantic review and one repair; converting image-review feedback into a
  targeted prompt correction remains partial. Detail in ROADMAP.md § *Gaps between stated goal and
  built product*.

## 7. Edge cases worth knowing

- **`client: none` is the normal value,** not a missing value. A project with no client profile is
  correct, not broken.
- **Shot deletion is retirement, not removal.** Media, prompts, comments, approvals, and versions
  stay attached; visible shot numbers may change, permanent Shot IDs never do.
- **Declined ideation offers never return.** A "no" during Stage 1.5 is permanent for the project.
- **Killed ideas go to the boneyard,** never deleted.
- **Two-strike parking.** A shot that fails twice in a batch is parked so it cannot stall the run.
- **Audio is deliberately unsystematized.** Real vs. generated VO is decided per project and must
  never be silently flipped mid-project.
