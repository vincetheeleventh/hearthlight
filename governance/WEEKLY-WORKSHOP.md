# Weekly workshop runbook

*The improvement pass. The daily checkpoint **observes**; this one **acts**.*

Working directory: `C:\Users\vxi\AppData\Local\hermes\Story Studio`

The job: read the week as a whole, audit whether the architecture is still coherent, execute the
safe improvements, and propose the rest. You are not waiting for Vince to notice problems — you are
finding them and bringing solutions.

---

## 1. Generate the facts

```bash
python governance/checkpoint.py workshop
```

Writes `checkpoints/weekly-YYYY-Www.md` plus the facts JSON. Non-zero exit → stop, report, commit
nothing.

## 2. Read the week

- **The last 7 daily checkpoints.** Look for what no single day showed: a problem mentioned three
  days running, a next-action nobody acted on, an area with churn and no progress.
- **`GOALS.md`** — especially the **v1 definition**. Everything below is measured against it.
- **`ROADMAP.md`** — what we said we were doing. Does the week's evidence match?
- **`PROPOSALS.md`** — what is open, what expired, what got approved and never built.
- **The previous workshop.** Do not re-propose something already rejected. A rejected idea that
  keeps resurfacing is worth *saying so once*, not re-pitching.

## 3. Audit coherence

The mechanical findings in the generated file are **questions, not verdicts** — heuristics with false
positives. Interrogate them:

| Finding | The real question |
|---|---|
| No inbound references | Is this dead, or just under-integrated like `hearthlight-character`? |
| Oversized SKILL.md | Is it doing two jobs that should split — or is it genuinely one big job? |
| Scripts with no test | Does breakage here cost money or corrupt shot state? Untested + expensive is the bad quadrant. |
| Stale skill counts | A doc asserting a number that is no longer true. Usually a GREEN fix. |
| Broken skill refs | Points at something that does not exist. Always a GREEN fix. |

Also look for what no script can see: the same law stated in two places that have started to
disagree, a stage whose handoff keeps breaking, a component whose justification died when a decision
changed, abstraction built for a future that has not arrived.

## 4. Execute the GREEN work

Do it, commit it, report it after. No approval needed. GREEN means **mechanical, reversible, and free
of product judgment**:

- doc/index sync — a skill missing from `AGENTS.md` or `README.md`, a stale count, a dead reference
- correcting `PRODUCT_SPEC.md` where implementation moved
- tests for code that already exists
- refreshing the Miro board (see §6)
- `.gitignore` hygiene, removing generated artifacts

**If you are unsure whether something is GREEN, it is AMBER.** The cost of asking is one day. The
cost of a wrong autonomous change to the instruction layer is that Vince stops trusting the system.

## 5. Propose the rest

Write new entries into `PROPOSALS.md`. **Every proposal names the v1 blocker it removes** — no named
blocker means `parked`, not built.

Respect the three brakes: **7 open max** (a new idea must displace a worse one — say which and why),
**30-day expiry**, **the v1 test**.

Bias toward **removal and merging**. The best proposal deletes something. A backlog that only grows
the system has misunderstood the job.

Two or three good proposals beat seven mediocre ones. A week with nothing worth proposing gets
**zero** — say so plainly. Manufacturing work to look useful is the failure mode here.

## 6. Refresh Miro

Board and IDs: `governance/miro.json`.

- **Governance panel** — update `stamp`, `roadmap`, `health`, `flags`, `open_questions` in place.
  Leave `north_star` and `non_goals` unless `GOALS.md` changed.
- **Pipeline diagram** — it is a generated diagram (not hand-placed art), so it **may** be updated
  when the pipeline genuinely changes: a stage added, a skill renamed or retired. Regenerate it from
  its DSL rather than nudging individual shapes. Do not rewrite it for cosmetics — only when
  `PRODUCT_SPEC.md` § pipeline no longer matches what it shows. Known gaps as of 2026-08-03:
  `hearthlight-character`, `hearthlight-dashboard`, `hearthlight-shot-runner`.

## 7. Commit

```bash
python governance/checkpoint.py commit --weekly --agent cowork
```

Does not push — Vince pushes from Windows (`DECISIONS.md` D-014). It reports how many commits are
waiting locally.

## 8. Report to Vince

Short, and in this order:

1. **Distance to v1** — did the film and the pipeline get closer this week?
2. **What I did** (GREEN, already done)
3. **What I want to do** (AMBER, needs ✅) — the strongest one or two, with the v1 blocker named
4. **What I think should go** (pruning candidates, with evidence)
5. **What is blocked on you**

---

## The hard limits

**RED — never autonomous, no exceptions:** `GOALS.md` · the approval model · deleting any file, skill,
or feature · product strategy · a project's charged register · `profile/TASTE.md` (his aesthetic
memory is his) · rewriting an existing `DECISIONS.md` entry · resolving a `⚠️ NEEDS VINCE` marker.

**Never touch `projects/`.** Not gitignored by accident — the checkpoint watches the system, not the
films (`DECISIONS.md` D-006).

**Do not delete another agent's in-flight work.** Hermes and ChatGPT edit these files too. Untracked
scratch that appeared mid-week is probably someone's work in progress — report it, leave it.

## The thing to keep remembering

This exists so Hearthlight gets *simpler and more coherent* over time, not more elaborate. If a
month of workshops has produced more surface area than it removed, the workshop itself has become
the problem — and saying so is your job too.
