---
doc: CANON-RULES
role: law
authority: canon
owner: vince
updated: 2026-08-04
answers:
  - what a canon document may and may not contain
  - the YAML front-matter schema every canon document carries
  - where removed content goes, and how to put it there
not_here:
  why this rule exists: DECISIONS.md D-017
  the daily procedure: governance/DAILY-CHECKPOINT.md
archive: archive/canon-rules.md
---

# CANON RULES — how the core documents are kept

The canon documents are the **highest-priority, signal-dense statement of the current state.**
They are read at the start of every session by every agent. Their job is to be short, true, and
human-readable. Their job is **not** to remember.

---

## The one rule

> **A canon document describes what is true now. Nothing else.**

If a sentence's purpose is to tell you what *used to be* true, it is not canon. It is archive.

### Banned in canon

| Pattern | Instead |
|---|---|
| `~~strikethrough~~` | Delete the line. Archive it. |
| "✅ ANSWERED 2026-08-03 — …" | State the answer as fact. Archive the question. |
| "*(Resolved 2026-08-03.)*" | Remove the item entirely. Archive it. |
| "was X, is now Y" · "no longer" · "previously" · "used to" | State Y. Archive X. |
| "Reclassified UNCLEAR → CORE, 2026-08-03" | The row says CORE. Archive the reclassification. |
| "the revised GOALS.md" · "the new spec" | It is just `GOALS.md`. There is one. |
| "Verified 2026-08-03" as body prose | `updated:` in the front matter carries this. |

**Dates are allowed** where the date is the fact — a shot approval, a decision date, a scheduled
event. They are banned as narration about the document's own history.

### Not banned

Confidence and provenance are current-state signal, not history. Keep them:

- **CONFIRMED / INFERRED** — whether Vince said it or an agent guessed.
- **NEEDS VINCE** — an open question blocking honest judgment.
- Known limitations, dead components, unfinished work. A limitation is a present-tense fact.

---

## Front matter

Every canon document opens with a YAML block. An agent reads front matter first and can route
without loading bodies.

```yaml
---
doc: ROADMAP                      # UPPERCASE stem, no extension
role: current-work                # see roles below
authority: canon                  # canon | derived | archive
owner: vince                      # vince = agents may not edit the body; agents = agents maintain it
updated: 2026-08-04               # ISO date, bumped on every content change
answers:                          # 2–5 questions this doc is the right place to ask. Lowercase, no '?'
  - what is being built right now
  - what is parked, and why
not_here:                         # questions this doc deliberately does NOT answer → where they go
  why a rule exists: DECISIONS.md
archive: archive/roadmap.md       # where this doc's removed content lands
---
```

**Roles.** `north-star` (why it exists) · `current-state` (what is built) · `current-work` (what is
changing) · `inventory` (what components exist) · `law` (rules in force) · `backlog` (what is
proposed) · `index` (where things are) · `guide` (how to operate it).

**`answers` is the routing payload.** Write the question an agent would actually ask, not a topic.
`what is being built right now` routes; `roadmap items` does not.

**`owner: vince`** means an agent may add or correct front matter but must not touch the body.
`GOALS.md` is the standing example.

---

## The archive

`archive/` holds everything the canon dropped. It is **append-only, never read by default,** and
exists so that removing a line from canon is a lossless act rather than a destructive one.

```
archive/
  roadmap.md            one file per canon doc, newest entry last
  product-spec.md
  skill-inventory.md
  proposals.md
  decisions/
    D-001.md            one file per decision — the full Context / Reason / Consequences
    D-002.md
```

Each archive entry carries the date, the document it left, and one line on why it left:

```markdown
## 2026-08-04 · from ROADMAP.md § Open questions
**Why:** answered — v1 requires both the film and the architecture.

> ~~Is the deliverable the film or the engine?~~ ✅ EFFECTIVELY ANSWERED 2026-08-03 — v1 requires
> **both**: the finished film *and* the architecture that finished it.
```

Strikethrough and dated narration are *correct* inside the archive. That is what it is for.

### Decisions are split

A decision has two halves, and they belong in different places:

- **The law** — one line, still in force, binds behaviour → the table in `DECISIONS.md`.
- **The argument** — Context / Reason / Consequences → `archive/decisions/D-0XX.md`.

An agent reads ~30 lines of rules per session instead of ~300 lines of reasoning, and opens the one
file it needs when it is about to challenge a rule. A superseded decision leaves the table entirely
and its file gains a `superseded_by:` line.

---

## Enforcement

```bash
python governance/canon.py check          # front matter valid + no banned history patterns
python governance/canon.py archive DOC --section "Open questions" --why "answered"
```

`check` runs inside `checkpoint.py commit` and **blocks the commit** on a violation, the same way
the secret scan and the unfilled-section guard do. A canon doc that starts logging history is a
defect, not a style preference — it costs every agent context on every read.
