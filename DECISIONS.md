# DECISIONS — why Hearthlight is built the way it is

*Append-only. Newest last. One entry per decision that would otherwise have to be rediscovered.*

**Rules for agents:** add an entry when a choice closes off an alternative someone would plausibly
reconsider. Do **not** invent reasoning — if the *why* cannot be recovered from the repository, write
`Reason: NOT RECOVERABLE` and say what evidence exists. Never rewrite or delete an existing entry; if
a decision is reversed, add a new one that supersedes it.

Format: **Date · Decision · Context · Reason · Consequences**

---

## D-001 · Skills are the constitution, not utilities
**Date:** ~2026-07-01 (first skills written) · **Source:** `README.md`, `HANDOFF.md` §2

**Context:** The pipeline could have been built as code with prompts as data, or as instructions the
agent reads at each stage.

**Reason:** *"The skills ARE the pipeline… they're not utilities the agent might call; together they
are the assistant filmmaker's method."* A general correction gets written back into the relevant
SKILL.md, so the instruction layer compounds across projects.

**Consequences:** The product is editable by anyone who can write Markdown, and improves without a
release. But **almost nothing is machine-enforced** — a law only holds if the agent read the file.
It also makes "is this component used?" unanswerable by static analysis, which is why
`SKILL-INVENTORY.md` has to exist.

---

## D-002 · The Claude skill store holds pointer stubs, not copies
**Date:** unknown (stubs present 2026-08-03) · **Source:** every stub's "Why a stub" section

**Context:** Claude's skill store needs a `SKILL.md` per skill. Copying each Hearthlight skill in
would produce two versions of every instruction.

**Reason:** Stated verbatim in the stubs: *"the Hermes SKILL.md is the single source of truth.
Copying its contents here would create a second version that silently drifts."*

**Consequences:** One canonical file per skill. Costs an extra file read per skill invocation, and
the stubs still need maintenance — four of them already cite the moved `AUDIENCE-CONTEXT.md`. Also
leaves an inconsistency: the `hearthlight` router skill exists *only* as a store skill with no
canonical source, which is the one place this decision is not followed.

---

## D-003 · Hearthlight is the engine; Talefeather is a client on it
**Date:** ~2026-08-01 · **Source:** `AUDIENCE-CONTEXT.md` (rewritten as a signpost)

**Context:** Talefeather's grief / living-legacy audience research sat at the root of Story Studio,
so *every* session inherited a grieving audience whether the project had one or not.

**Reason:** Named explicitly as a **bounded-context leak** — *"client assumptions living in the
engine's constitution."* Craft laws (gates, no-drift, verbatim style blocks) do not assume who is
watching; audience psychology does.

**Consequences:** Every project must declare `format`, `client`, `charged_register`. `client: none`
became the normal value. Client material moved to `profile/clients/{client}/`.
**Not fully propagated:** `HANDOFF.md` still states grief-cohort reasoning as engine law, and four
pointer stubs still route agents to the old root file.

---

## D-004 · The charged register is per project, never defaulted
**Date:** ~2026-08-01 · **Source:** `hearthlight-terse`, `AUDIENCE-CONTEXT.md`

**Context:** The voice register needs to know which content is emotionally load-bearing and must
never be compressed.

**Reason:** Follows from D-003. A register hard-coded to grief would re-introduce the leak through
the tone system instead of the audience docs.

**Consequences:** `hearthlight-terse` reads `charged_register:` from the project spec. If the key is
missing the agent must **ask**, not guess.

---

## D-005 · Mechanics terse, art full
**Date:** ~2026-08-01 · **Source:** `skills/hearthlight-terse/SKILL.md`, `CLAUDE.md`

**Context:** Agent responses drifted verbose, burying the signal in machine chatter.

**Reason:** The test is whether a sentence is about the machine or about the story and the people in
it. Explicitly: *"A mechanical topic does not become creative by sitting inside a film that matters."*

**Consequences:** Default is caveman-style fragments for all status, plans, errors, and logs. Art
full is a narrow enumerated exception. The rule is stated in three files; `CLAUDE.md` and `AGENTS.md`
both explicitly defer to the skill as authoritative, which is what keeps it from becoming drift.

---

## D-006 · Git tracks the instruction layer only; `projects/` stays out
**Date:** 2026-07-01 · **Source:** `.gitignore` header comment

**Context:** Project folders hold source interviews, generated media, and rights-constrained material.

**Reason:** *"The repo is the reusable pipeline, not the films."* Media is large and some of it is
rights-constrained — the McConaughey pilot is private use only.

**Consequences:** History covers the system, not the work. Creative progress is invisible to Git,
which is why gate state lives in per-project `status.yml` ledgers. Confirmed by Vince on 2026-08-03:
the checkpoint tracks **the system only**.

---

## D-007 · Autonomy between gates, never through them
**Date:** ~2026-08-01 · **Source:** `hearthlight-shot-runner`, `AGENTS.md`

**Context:** Batch rendering dozens of shots one at a time needs autonomy; creative approval must not
be automated.

**Reason:** Splits review in two — **Stage A** spec compliance, judged by the machine (verbatim style
block, aspect ratio, references); **Stage B** quality, judged **only by Vince**. No script can judge
taste.

**Consequences:** A durable ledger so a crashed session never re-renders a paid generation, and a
two-strike parking rule so one stubborn shot cannot stall a batch.

---

## D-008 · Aspect ratio is a composition law, not an export setting
**Date:** ~2026-08-01 · **Source:** `hearthlight-distribution-spec`, `USER-GUIDE.md`

**Context:** Format could have been decided at export.

**Reason:** *"A wide shot drawn for 16:9 doesn't survive a vertical crop, it has to be re-conceived."*
Deciding late means redrawing.

**Consequences:** The distribution spec is decided first and read before framing any shot.

---

## D-009 · Shots have permanent IDs; deletion is retirement
**Date:** ~2026-08-03 · **Source:** `hearthlight-dashboard/references/SHOT-IDENTITY-PROTOCOL.md`

**Context:** Shots get inserted, reordered, and retired mid-production, so a visible shot number is
not a stable identifier for media and approvals.

**Reason:** Position-based identity silently mis-attaches assets when a workbook is regenerated.

**Consequences:** Every spreadsheet must carry a `Shot ID` column. If a match cannot be proven,
Hearthlight **stops for reconciliation** rather than moving assets by row number. Retired shots keep
their media, prompts, approvals, and versions, and can be restored.

---

## D-010 · Git initialized; the old init script's guard was self-defeating
**Date:** 2026-08-03 · **Source:** this session · **Agent:** cowork

**Context:** `git-init-commit.sh` was written 2026-07-01 to create the repository. It never ran
successfully, so Hearthlight had no version history at all for a month.

**Reason:** The script aborts if a known-leaked RunningHub key appears anywhere in the working tree —
but the key literal is written **inside the script itself**, so its own `grep -r` always matched and
it aborted every time. The guard could never pass.

**Consequences:** Repository initialized on `main`. The guard is reimplemented in
`governance/checkpoint.py` matching a **SHA-256 of the key**, so the literal never enters the
repository. `git-init-commit.sh` is superseded and retained only as a historical record — it still
contains the raw key and still assumes WSL paths.

---

## D-011 · The checkpoint splits facts from judgment
**Date:** 2026-08-03 · **Source:** this session · **Agent:** cowork

**Context:** The daily checkpoint has to do two different kinds of work: gather evidence (what
changed, what is orphaned, what is stale) and reach conclusions (is this drift?). A shell script
cannot judge alignment; an agent alone cannot be trusted to gather facts reproducibly.

**Reason:** Splitting them means the mechanical half can **fail loudly and block the commit**, while
the judgment half can be wrong in the open where Vince can correct it. It also means a broken
checkpoint never commits broken output — the script's exit code gates the commit.

**Consequences:** `checkpoint.py gather` writes facts + a skeleton; the scheduled agent fills the
judgment sections and updates Miro; `checkpoint.py commit` re-validates, then commits and pushes.
The agent may write checkpoints and mechanical doc updates — never `GOALS.md`, never deletions,
never refactors. Those surface as recommendations.

---

## D-012 · Multiple agents contribute; commits carry attribution
**Date:** 2026-08-03 · **Source:** Vince, this session

**Context:** Three agents edit these files — Claude Cowork, Hermes (Telegram gateway), and ChatGPT —
plus Vince directly. Until today there was no version history, so a change had no author, no time,
and no stated reason. This is the most likely root cause of the disorientation that prompted the
governance system.

**Reason:** Agents cannot coordinate through shared memory; they have none. The only medium they all
touch is the files. So the files must carry the coordination.

**Consequences:** Every agent commit carries an `Agent:` trailer. Changes that appear with no
attribution are reported by the checkpoint as **unattributed** rather than silently absorbed — which
is the detection path for ChatGPT edits, since it cannot run Git. See `AGENTS.md` § Multi-agent
working agreement.

---

## D-013 · The system improves itself under the same gate law it enforces
**Date:** 2026-08-03 · **Source:** Vince, this session · **Agent:** cowork

**Context:** Vince asked for a system that does not wait to be told what to fix — one that infers
work from the roadmap and goals, generates ideas, attacks problems creatively, prunes what is
useless, and keeps the architecture coherent so technical debt does not accumulate.

The obvious risk is that this becomes the thing it was built to prevent. An agent instructed to
improve something daily will always find something to improve; a year of that is 365 ideas and a
system more elaborate than the one that was confusing him in the first place.

**Reason:** Hearthlight already solved this problem for filmmaking — *autonomy between gates, never
through them*. Applying the same law to the system itself needed no new concept, just a mapping:

- **GREEN** — mechanical, reversible, no product judgment → execute and report.
- **AMBER** — changes how the system behaves → propose, wait for ✅.
- **RED** — `GOALS.md`, the gate protocol, deletion, strategy, `TASTE.md` → never autonomous.

Three brakes make the backlog self-limiting rather than accumulating: a **WIP cap of 7** (a new idea
must displace a worse one, which forces ranking instead of appending), **30-day expiry** (if it
mattered it comes back), and **the v1 test** — every proposal must name the v1 blocker it removes or
it is parked. The v1 test is the strongest of the three: it is what keeps the system improving the
*film* rather than improving the system.

**Cadence is split deliberately.** Daily observes and stays a two-minute read; weekly proposes. Ideas
generated daily would be restated before Vince had a chance to act, and patterns worth naming only
become visible across several days.

**Consequences:** `PROPOSALS.md` (the backlog), `governance/WEEKLY-WORKSHOP.md` (the runbook), and a
coherence audit in `checkpoint.py workshop`. The audit is explicitly framed as **questions, not
verdicts** — its checks are heuristics and it produces false positives, so an agent that treats a hit
as a defect will delete something it should not have.

The failure mode to watch: if a month of workshops adds more surface area than it removes, the
workshop has become the problem. The runbook instructs the agent to say so.

---

## D-014 · Checkpoints commit but do not push
**Date:** 2026-08-03 · **Source:** Vince, this session · **Agent:** cowork

**Context:** The remote is `github.com/vincetheeleventh/hearthlight`. The agent sandbox that runs the
checkpoint is ephemeral and holds no GitHub credentials, and cannot inherit the Windows credential
manager. Pushing automatically would have required a token stored on disk.

**Reason:** Vince chose to push manually rather than store a credential for an automated process.
Fewer secrets at rest, and the push stays a deliberate act.

**Consequences:** `commit` no longer pushes by default; `--push` is opt-in. Each run reports how many
commits are waiting locally. **The tradeoff is real and should not be forgotten:** until Vince pushes,
the entire history lives on one machine with no backup — the same single-point fragility that let a
month of work go unrecorded. If commits start piling up unpushed, the checkpoint should say so
loudly.

---

## D-015 · Krea still prompts are exact frame-one data, not assembled prose
**Date:** 2026-08-03 · **Source:** Vince, this session · **Agent:** chatgpt

**Context:** The first Krea runs received prompts containing workflow labels, timed video action,
camera movement, continuity bookkeeping, character arrays, and global negatives. Those fields were
being appended by the compiler even though the workbook now has separate `Still (frame one)` and
`Action (motion — video only)` columns.

**Reason:** For the style/composition pass, the authored still cell already defines everything visible
in one image. Assembly from additional columns creates a second source of truth and turns motion into
impossible still-image instructions. Exact extraction is simpler, auditable, and preserves Vince's
approved framing. Krea taste controls belong in API parameters, not prompt prose.

**Consequences:** `krea_style_comp.py` is the sole Stage-A compiler. It requires a current stable Shot
ID registry, compiles one packet per unique setup, excludes shared and source-photo shots, and rejects
motion/workflow contamination. `krea_style_comp_run.py` consumes packets without rewriting them, uses
`creativity=raw` plus neutral K2 sliders, records the complete request fingerprint, downloads and
ledgers each result before the next paid job, and resumes without resubmitting completed work. The
legacy Stage-A path in `two_pass.py` remains disabled.