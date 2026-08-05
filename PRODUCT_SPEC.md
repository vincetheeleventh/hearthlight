---
doc: PRODUCT_SPEC
role: current-state
authority: canon
owner: agents
updated: 2026-08-04
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

A **single-operator filmmaking pipeline** that turns a spoken story (voice note, interview, recording)
into illustrated narrative media: ink-and-watercolour conditioning stills plus short animated clips,
usually cut to a real recorded voice.

It is implemented **as an instruction layer, not an application.** There is no server, no build step,
and no compiled artifact. The product is ~21 Markdown skill files plus a small number of Python
helper scripts, executed by an LLM agent that reads them.

**Runtime surfaces** (all three drive the same files):

| Surface | How it runs | Notes |
|---|---|---|
| Hermes + Telegram | Hermes gateway, own profile, own bot | Vince's primary point of contact; each skill is a slash command |
| Claude Cowork | This desktop app, folder-mounted | Uses pointer stubs (see §5) |
| ChatGPT | Manual, file-level | No tool integration; contributes by editing files directly |

## 2. Major features

- **Gate-driven pipeline.** Nine ordered stages, six of them gates requiring Vince's explicit ✅.
- **Aesthetic single-source-of-truth.** The mise-en-scène holds a LOCKED style tier and a COMPOSED
  world tier; every prompt is assembled from it verbatim.
- **Batch render execution with a durable ledger.** Fresh subagent per shot, two-stage review, and a
  progress ledger so a crashed session never re-pays for a completed generation.
- **Agent-authored, visibility-aware Krea style/composition execution.** Versioned Shot Vision and
  source-grounded visual context feed a focused, tool-restricted Hermes Shot Prompt Author. The LLM
  writes the intelligent shot-specific prompt body; Python enforces identity, visibility, ownership,
  one-instant, provider-language, source-hash, and request-control invariants, then adds fixed text
  verbatim. An independent Hermes semantic reviewer may block incoherent or unsupported prompts and
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
  review versions, and insert, retire, or restore shots without changing permanent identity. Compiled
  Stage-A prompts are read-only outputs; likeness prompts remain manual. These controls do not approve
  Hearthlight gates.
  Studio Shot Vision plus the permanent-ID shot registry are the live authority. Imported hand-drawn
  board workbooks are immutable archived references; current spreadsheets are generated handoff exports
  and never silently replace Studio state or block image-prompt compilation.
  Source: `staging/overview-ui/`.
- **Plumbing self-check.** Separates mechanical failure (the system's fault, fixable) from quality
  judgment (Vince's call, unautomatable).

## 3. The pipeline — stages and owning skills

| # | Stage | Gate | Owning skill |
|---|---|---|---|
| 0 | Distribution spec (format, client, charged register, aspect) | — | `hearthlight-distribution-spec` |
| 1 | Intake / transcription | — | `hearthlight-conventions` |
| 1.5 | Ideation → Vision Brief | **Gate 0** | `hearthlight-consolidate` |
| 2 | Story Arc → Beat Sheet → A/V Script | **Gate 1** | `hearthlight-outline` |
| 2.5 | Story pressure-test | — | `hearthlight-critique` |
| 3 | Mise-en-scène / Aesthetic Bible | **Gate 2** | `hearthlight-mise-en-scene` |
| 3.5 | Character dossiers + turnaround sheets | — | `hearthlight-character` |
| 3.7 | Timing intake / timeline export | — | `hearthlight-timing-intake` |
| 3.9 | Clip prep for storyboarding | — | `hearthlight-clip-extractor` |
| 4 | Conditioning stills | **Gate 3** | `hearthlight-image-prompts` |
| 4.5 | Shot design by crew | — | `hearthlight-shot-crew` |
| 5 | Storyboard: motion, duration, transitions | **Gate 4** | `hearthlight-storyboard` |
| 6 | Seedance i2v clips | **Gate 5** | `hearthlight-video-prompts` + `hearthlight-comfyui-graph` |
| — | Batch execution at stages 4 and 6 | — | `hearthlight-shot-runner` |

Cross-cutting: `hearthlight-terse` (voice register), `hearthlight-research` +
`hearthlight-reference-report` (world research), `hearthlight-notion-log` (surfacing),
`hearthlight-dashboard` (status), `hearthlight-selfcheck` (health).

Full per-skill responsibilities, usage evidence, and classification: **`SKILL-INVENTORY.md`**.

## 4. Rules and constraints actually enforced

**Engine laws** (from `AGENTS.md`, true of every project):

- Gates are sacred — nothing advances without Vince's explicit ✅ in Telegram.
- No drift — style and signature blocks are copied verbatim into prompts, never paraphrased.
- Nothing exists only in chat — every artifact lands in `projects/{slug}/`.
- The distribution spec is read before framing; aspect ratio is a composition law, not an export setting.
- The spec declares, the engine obeys — `format`, `client`, `charged_register` are never assumed.
- Image provider priority: OpenAI Codex OAuth → Krea MCP → OpenAI API key, unless a stage pins a surface.
- Rights discipline — the McConaughey pilot is private use only, stylized resemblance, never photoreal.

**Enforcement is shared between instruction and code.** Five areas are machine-checked:
`hearthlight-selfcheck` checks style/composition prompt readiness; the prompt-author compiler validates
source hashes, visibility, ownership, temporal state, provider vocabulary, controls, and semantic-review
pass state; the Krea packet compiler blocks stale approval and dispatch drift; the runner fingerprints
each complete request and resumes recorded jobs; and the shot registry refuses to move assets by row
number when a regenerated workbook cannot prove a `Shot ID` match. Everything else depends on the
agent having read the skill.

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

**The gate ledger.** Each project keeps `status.yml` with one line per gate, valued
`approved YYYY-MM-DD` / `pending` / `unconfirmed` / `done` / `n/a`. `unconfirmed` means work exists
but no ✅ was recorded — it must be ratified, not assumed.

## 6. Known limitations

- **LLM prompt quality cannot be proven by deterministic tests.** The image-prompt suite has 25
  helper tests, including seven focused author-contract and visibility golden tests. They verify source
  grounding, rendering boundaries, blocking, and reviewer wiring—not whether the configured external
  model makes a strong visual judgment on every raw shot. Real OpenRouter forward-testing requires
  explicit approval because it sends project material to that provider.
- **The image-prompt tests read live `projects/yugioh` data.** They assert exact generation counts,
  shared-setup pairs, and workbook cell addresses, so editing the film's shot list fails the suite
  and can block a checkpoint commit. A creative decision should not trip a code guard.
- **`pytest` must be present for the checkpoint to verify tests.** Without it the checkpoint reports
  `not run` rather than falsely passing, and `commit` will not block on failures it could not
  observe.
- **Laws are advisory to any agent that skips the read.** Nothing prevents an agent from generating
  an image without loading the mise-en-scène.
- **No shared state between the three agent surfaces.** Cowork, Hermes, and ChatGPT coordinate only
  through the files themselves. See `AGENTS.md` § Multi-agent working agreement.
- **`.venv-stt` is dead.** The faster-whisper environment was a Linux venv and did not survive the
  WSL → Windows migration; the hand-drawn-board intake path depends on it.
- **Stage 6 is unproven end to end.** The RunningHub key was leaked and needs rotating; no full
  film has passed every gate.
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
