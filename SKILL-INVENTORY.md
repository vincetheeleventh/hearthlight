---
doc: SKILL-INVENTORY
role: inventory
authority: canon
owner: agents
updated: 2026-08-04
answers:
  - which components exist and what class each is
  - what justifies a component's existence
  - what has no inbound references and may be dead
not_here:
  what each skill does: skills/{name}/SKILL.md
  what is being built: ROADMAP.md
  whether to delete something: PROPOSALS.md
archive: archive/skill-inventory.md
---

# SKILL-INVENTORY — what exists, what justifies it, what deserves review

*Derived from the working tree. **Nothing here has been deleted.** This document surfaces components
for Vince's review; the kill decision is his.* Refreshed by the daily checkpoint when the skill set
changes. Usage evidence is necessarily weak — see the caveat in §4.

## Classification key

| Class | Meaning |
|---|---|
| **CORE** | A pipeline stage or a law-bearing component. Removing it breaks the product. |
| **SUPPORTING** | Real capability, referenced and justified, but the pipeline survives without it. |
| **EXPERIMENTAL** | Built and wired, but the approach is unproven in real use. |
| **ORPHANED** | Present with no inbound references and no evidence of use. |
| **DEPRECATED** | Superseded. Kept only as a record. |
| **UNCLEAR** | Cannot be classified from the repository. Needs Vince. |

---

## 1. Summary

| Class | Count |
|---|---|
| CORE | 12 |
| SUPPORTING | 6 |
| EXPERIMENTAL | 3 |
| UNCLEAR | 0 |
| ORPHANED (non-skill components) | 4 |
| DEPRECATED (non-skill components) | 2 |

**23 skills** in `skills/`, plus **1 router** that exists only in the Claude skill store.
No `hearthlight-*` skill is orphaned — every one is referenced by `AGENTS.md`. The genuine
complexity problems are **outside** `skills/`.

---

## 2. The skills

Columns: **AG** = mentions in `AGENTS.md` · **UG** = `USER-GUIDE.md` · **RM** = `README.md` ·
**Peer** = other skills referencing it · **Scr** = helper scripts.

| Skill | AG | UG | RM | Peer | Scr | Class | Justified by | Notes |
|---|:--:|:--:|:--:|:--:|:--:|---|---|---|
| `hearthlight-terse` | 2 | 0 | 1 | 2 | 0 | **CORE** | Principle 8 / D-005 | Load-first law. Governs subagent dispatch. |
| `hearthlight-conventions` | 1 | 1 | 1 | 5 | 0 | **CORE** | "Nothing exists only in chat" | Most-referenced by peers. Foundation. |
| `hearthlight-distribution-spec` | 2 | 1 | 1 | 1 | 0 | **CORE** | D-003, D-008 | Owns `format`/`client`/`charged_register`. |
| `hearthlight-consolidate` | 1 | 0 | 2 | 2 | 0 | **CORE** | Gate 0 | Bounded ideation + no-smuggling law. |
| `hearthlight-outline` | 1 | 0 | 1 | 0 | 0 | **CORE** | Gate 1 | Zero peer refs — normal for a linear stage. Modified 2026-08-03, reason unrecorded. |
| `hearthlight-mise-en-scene` | 1 | 0 | 1 | 1 | 0 | **CORE** | Principle 2 | The anti-drift keystone. Largest SKILL.md (14 KB). |
| `hearthlight-image-prompts` | 1 | 0 | 1 | 4 | 6 | **CORE** | Gate 3 | 4 test files. Stage A = focused LLM Shot Prompt Author + independent semantic reviewer, Python source/visibility lint, approved Krea packet plan, durable runner; `two_pass.py` Stage A remains disabled. |
| `hearthlight-storyboard` | 1 | 0 | 1 | 0 | 0 | **CORE** | Gate 4 | Modified 2026-08-03, reason unrecorded. |
| `hearthlight-video-prompts` | 1 | 0 | 1 | 6 | 0 | **CORE** | Gate 5 | Highest peer-reference count. |
| `hearthlight-comfyui-graph` | 1 | 0 | 1 | 3 | 0 | **CORE** | Gate 5 plumbing | Grounded in a real working RunningHub graph. |
| `hearthlight-shot-runner` | 2 | 0 | 1 | 2 | 0 | **CORE** | D-007 | Owns the ledger that prevents re-paying for renders. |
| `hearthlight-board-sheet` | 0 | 0 | 1 | 1 | 0 | **EXPERIMENTAL** | board2video | Composes the storyboard-spreadsheet image board2video feeds a video model: clusters shots into 10–15s sequences, crops panels, renders sheet + header. Built 2026-08-05 on Vince's proven board test. **Untried as a skill, and the active generator has no surface for it** — see the generator gap in `workflows/board2video.md`. |
| `hearthlight-acting` | 1 | 0 | 1 | 1 | 0 | **CORE** | Core problem 3 | Performance writing — behaviour instead of emotion, the locked master profile, eye life. **Cross-cutting: both shot2video and board2video depend on it.** Adapted 2026-08-05 from an outside production practice, proprietary references removed. Untested against a real generation batch. |
| `hearthlight-character` | 1 | 0 | 1 | 1 | 0 | **SUPPORTING** | Principle 2 | Owns identity, meaning, and the character sheet. Holds the believable-over-beautiful and catch-light selection criteria. Its § Contents (three full-body views) conflicts with the headless-front finding — P-011 open. |
| `hearthlight-critique` | 2 | 1 | 0 | 2 | 0 | **SUPPORTING** | Principle 3 | The "partner not intern" behaviour made concrete. |
| `hearthlight-research` | 1 | 1 | 1 | 2 | 0 | **SUPPORTING** | Feeds Gate 2 | "Research populates the world, never the story." |
| `hearthlight-clip-extractor` | 2 | 0 | 1 | 4 | 1 | **SUPPORTING** | Storyboard prep | Thin ffmpeg wrapper, well referenced. |
| `hearthlight-notion-log` | 2 | 1 | 0 | 4 | 0 | **SUPPORTING** | Vince's point of contact | Absent from README. |
| `hearthlight-selfcheck` | 2 | 0 | 0 | 1 | 1 | **SUPPORTING** | Limitation triage | Absent from README and USER-GUIDE. Enforces the DRAFT→LOCKED block — one of only three machine-enforced laws. |
| `hearthlight-timing-intake` | 3 | 1 | 0 | 5 | 4 | **SUPPORTING** | Editor round-trip | Most `AGENTS.md` mentions and 4 scripts. **Partly blocked** — `transcribe.py` needs the dead `.venv-stt`. |
| `hearthlight-reference-report` | 2 | 1 | 1 | 2 | 0 | **EXPERIMENTAL** | Review ergonomics | Convenience layer over research output. No evidence it has been used on a real project. |
| `hearthlight-shot-crew` | 2 | 1 | 0 | 2 | 0 | **EXPERIMENTAL** | Principle 3 | 8 subagent roles. `HANDOFF.md` §6 names *verifying the roles give distinct opinions* as still-pending. Highest cost-per-shot in the system, least evidence it pays. Absent from README. |
| `hearthlight-dashboard` | 1 | 1 | 1 | 1 | 5 | **CORE** | **Primary outcome 4** | The surface the iterate-and-correct loop runs on, not a status utility. Largest sub-app: `index.html`, `serve.py`, `pipeline.json`, shot registry, backfill script, a test. Owns D-009. |

### The router
| Component | Class | Notes |
|---|---|---|
| `hearthlight` (session entry point) | **CORE** | Exists **only in the Claude skill store**, with no canonical source in `skills/`. This is the one place D-002 is not followed — it *is* a copy, so it can drift with nothing to reconcile against. It also cites `AUDIENCE-CONTEXT.md` as "the emotional register", which is now only a signpost. **Recommend: create `skills/hearthlight/SKILL.md` and reduce the store copy to a stub.** |

---

## 3. Components outside `skills/` — where the real complexity is

| Component | Size | Class | Evidence |
|---|---|---|---|
| `.agents/skills/krea-animation/` | ~30 files | **ORPHANED** | A complete parallel pipeline — templates, references, 8 Python scripts (`assemble_edit.py`, `submit_video_jobs.py`, `scaffold_project.py`…). **Zero references anywhere.** Substantially overlaps `hearthlight-storyboard`, `-shot-runner`, `-mise-en-scene`, `-conventions`. Likely a vendored precursor Hearthlight replaced. |
| `.agents/skills/krea-generate/` | ~10 files | **ORPHANED** | Model catalogue, budget tracking, cost preflight, async polling. **Zero references.** Overlaps `hearthlight-image-prompts` and `-comfyui-graph`. Contains a `seedance-2.md` reference that may still hold useful vocabulary. |
| `.agents/skills/krea-marketing/` | — | **ORPHANED** | **Zero references.** No apparent relationship to any Hearthlight goal. |
| `.artifact-work/` | 944 KB | **ORPHANED** | `inspect.mjs`, `inspect-shot-25.mjs`, two PNGs, and a `node_modules` tree — the only Node dependency in the repository. Scratch from a one-off investigation. Now gitignored. |
| `git-init-commit.sh` | 1.3 KB | **DEPRECATED** | Superseded by `governance/checkpoint.py` (D-010). Never ran successfully. Still contains the raw leaked key and assumes WSL paths. **Recommend deleting** — it is the only file in the tree containing the key literal. |
| `start-gemma-model.bat` | 2.5 KB | **DEPRECATED** | The `gemma → LocalHermes` rename (`HANDOFF.md` §5 item 3) was started and abandoned. |
| `HANDOFF.md` | 19.6 KB | **DEPRECATED (contested)** | Dated 2026-07-06. Largest doc; the richest record of *why*, and the single biggest source of stale claims — says "all 17 skills" (there are 21), and states Talefeather's grief reasoning as engine law, the exact leak D-003 fixed. Its §1 and §6 have been mined into `GOALS.md` and `ROADMAP.md`. **Recommend: retire, or add a header marking it a historical snapshot superseded by the four canonical docs.** |
| `.venv-stt/` | — | **DEPRECATED** | Dead Linux venv from the WSL→Windows migration. Blocks `timing-intake/scripts/transcribe.py`. Rebuild or remove. |
| `_git/GITHUB-SETUP.md` | 2.6 KB | **SUPPORTING** | Setup notes in a folder named to avoid colliding with `.git`. Verify still accurate now that a real repository exists. |

---

## 4. Overlap and duplication

**Voice register stated three times** — `CLAUDE.md`, `AGENTS.md`, `skills/hearthlight-terse/`.
*Not a defect:* the first two explicitly name the third as authoritative. Worth watching; if the
summaries ever contradict the skill, the deferral has stopped working.

**Pipeline described three times** — `AGENTS.md` (stages + laws), `README.md` (layout tree),
`USER-GUIDE.md` (Vince's walkthrough). Legitimately different audiences, but `README.md` has already
drifted: it omits several of the 22 skills and still describes a deleted `hearthlight-asset-bible/` tombstone.

**`krea-*` vs `hearthlight-*`** — genuine functional duplication, described above.

**Stage 6 split across two skills** — `hearthlight-video-prompts` (the words) and
`-comfyui-graph` (the wire). Deliberate and documented. Not duplication.

> **Caveat on "usage" evidence.** Because skills are instructions rather than code (D-001), there is
> no call graph. "Used" here means *referenced in prose*. A skill could be referenced everywhere and
> never actually invoked, or invoked constantly with few mentions. Only Vince knows which he has
> actually run. Treat every classification below CORE as a question, not a verdict.

---

## 5. "We might need this later" — candidates for review

Ordered by complexity added relative to demonstrated need.

**Retiring what no longer earns its place is a stated goal** (`GOALS.md` core problem 5), not
housekeeping. New models obsolete workflows; a system that only accumulates cannot keep pace. Read
this list as the adaptation backlog, not a tidy-up.

1. **`.agents/skills/krea-*` (3 packs, ~484 KB, 18+ scripts).** Zero references, direct functional
   overlap with the Hearthlight pipeline. **Highest-value cleanup in the repository.**
   *Question: are these a precursor you replaced, or something you still intend to harvest?*
2. **`hearthlight-shot-crew`.** The most conceptually ambitious component and the most expensive per
   shot. Core problem 3 now explicitly endorses *a crew of agents supplying research and richness* —
   so its **purpose** is goal-backed. What remains unverified is this **implementation**: that eight
   roles produce genuinely distinct, arc-aware opinions rather than eight paraphrases. Stays
   EXPERIMENTAL until a contested shot has actually run through it.
3. **`hearthlight-reference-report`.** A presentation layer on research output. Plausible, but no
   evidence of real use. *Question: have you ever read one?*
4. **The engine/client abstraction itself.** Built to support many clients; exactly one exists.
   `GOALS.md` is framed around **AI-filmmaking problems** rather than client service, so the
   abstraction's justification is thin. *Not a recommendation to remove — a flag.*
5. **`hearthlight-character`.** Owns the turnaround law inherited by every generated clip, yet has
   zero peer references and no README entry. The risk here is the opposite of the others: not too
   much complexity, but too little integration for how much it affects.

**Resolved 2026-08-03:** *"Is `hearthlight-dashboard` a product surface or a personal utility?"* —
it is a product surface. Primary outcome 4 settles it.
