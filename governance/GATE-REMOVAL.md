---
doc: GATE-REMOVAL
role: runbook
authority: canon
owner: vince
updated: 2026-08-11
answers:
  - how to finish removing the gate protocol from the code and the skills
  - what order to do it in, and what proves each step
not_here:
  why gates were removed: archive/decisions/D-026.md
  the rule that replaced them: DECISIONS.md D-026
---

# Removing gates for real

The canon docs are done. This is the rest: **41 skill files, 8 scripts, `status.yml` per project,
and the Studio UI.**

Do not do it in one pass. Every step below leaves the system working, and each one has something
that tells you it worked. A half-finished removal is worse than either state, because half the
system will be waiting for a ✅ that the other half stopped producing.

---

## The replacement, in one line

Approval is **per shot**, on two independent axes, plus one machine-computed axis:

| Axis | Values | Who sets it |
|---|---|---|
| `Design` | Exploring · Designed · **Locked** | Vince. `confirmed_by_user: true` on the current Shot Vision |
| `Production` | Not started · In progress · Needs fix · Candidate ready · **Approved** | Vince, via a hero selection and review events |
| `Inputs` | Ready · Stale · **Broken** | Nobody. Computed. `Broken` blocks generation |

All three are already computed by `film_study_tool/productions.py` (`design_state`,
`production_state`, `inputs_state`) and rendered in the Studio. **The state model is built.** What
remains is deleting the thing it replaced.

---

## Order of work

### 1. Stop writing the ledger  *(30 minutes, reversible)*

Nothing reads `status.yml` for a decision — it is read to *report*. Cut the writer first so the
file stops drifting further while you work.

```bash
grep -rn "status\.yml" skills/ governance/ --include=*.py --include=*.md
```

- `hearthlight-dashboard/SKILL.md` — remove the "gate ledger contract" section. The skill keeps the
  Shot ID protocol and the read-only pipeline view.
- Anything that writes `approved YYYY-MM-DD` — delete the write, keep the read for now.

**Proves it worked:** run a stage end to end. No file in `projects/*/` changes except the shot
record and the ledgers.

### 2. Replace the reporting  *(the real work)*

Everything that reported gate progress now reports shot state. Two consumers:

**`hearthlight-dashboard/scripts/scan.py` and `serve.py`** — replace gate counts with a per-state
tally. The useful line is not "3 of 6 gates" but:

```
28 shots · design 6 locked / 22 designed · production 1 approved / 25 candidate-ready / 2 not started
inputs: 21 ready · 6 stale · 1 broken
```

**`film_study_tool` UI** — `renderGateRail()` and the gate stops in `production.css` come out. The
overview already has the data; give it a state tally in the same place the rail used to sit.
`productions.py` `gateProgress` and `gates` can go once nothing reads them — grep the JS first.

**Proves it worked:** `python skills/hearthlight-dashboard/scripts/scan.py --project yugioh` prints
shot state and the word "gate" appears nowhere in its output.

### 3. Strip the skills  *(mechanical, do it in one sitting)*

```bash
grep -rln -iE "\bgate" skills/ | sort
grep -rn -iE "gate ?[0-5]|gates are sacred|explicit ✅" skills/
```

Three patterns, three treatments:

| Pattern | What to do |
|---|---|
| `Gate N` in a stage heading | Delete the gate number. `hearthlight-outline` is "Stage 2", not "Stage 2 / Gate 1" |
| "Gates are sacred / nothing advances without ✅" | Replace with: *the machine never approves its own work — agents draft, run and report; only Vince marks a design Locked or a shot Approved* |
| "after the gate ✅, run the batch" | Replace the trigger with the state it actually meant: *when the shots you want are Design: Locked* |

**Do not** touch `hearthlight-shot-runner`'s Stage A / Stage B split. That is a review split, not a
gate: spec compliance is machine-judged, quality is Vince only, and D-026 keeps it.

**Proves it worked:** `grep -ril "gate" skills/ | wc -l` returns 0, and `hearthlight-selfcheck`
stays green.

### 4. Retire `status.yml`  *(per project, last)*

Only after 1–3. Move it, do not delete it — it is the only record of what was approved and when.

```bash
git mv projects/yugioh/status.yml projects/yugioh/archive/status-gates-retired.yml
```

Then remove the reader added in step 1.

**Proves it worked:** `hearthlight-selfcheck` and the Studio both load a project with no
`status.yml` and report shot state normally.

### 5. Update `profile/SOUL.md`

It still says *"Gates are sacred. Six approval gates (0–5)."* It loads on every Hermes session, so
it is the one file where a stale rule will actually be obeyed. Replace law 3 with the approval rule
from step 3.

---

## What must NOT be removed with them

Easy to over-delete here, because these read like gates and are not:

- **Stage A / Stage B** in `hearthlight-shot-runner`. A review split. Keep.
- **`Inputs: Broken` blocks generation.** A correctness check, not an approval. Keep, and keep it
  automatic — it is the only block that should not need a human.
- **The two-strike parking rule.** A batch discipline. Keep.
- **`hearthlight-consolidate`'s no-smuggling law.** Nothing an agent originates enters a document
  without Vince adopting it. That is the *substance* of what gates were protecting and it survives
  them entirely.
- **The RED autonomy tier.** Agents still never touch `GOALS.md`, delete things, or resolve a
  `⚠️ NEEDS VINCE` marker.

---

## The thing to watch for afterwards

Gates were also a **pacing** device. They forced a stop-and-look before spending, and they are
being removed partly *because* that stop was being skipped — but removing them removes the brake as
well as the ceremony.

The replacement brake is narrower and should be watched: nothing is Approved except by Vince, and
`Inputs: Broken` blocks generation. If work starts running ahead of judgment again — generations
piling up against shots nobody has looked at — **the answer is not to reinstate ten gates.** It is
to make per-shot state harder to skip: block a batch on unreviewed candidates from the previous
batch, or surface the count of never-looked-at renders where it cannot be ignored.

The number to keep an eye on is the one that started this: **40 generations, 1 approved shot.**
