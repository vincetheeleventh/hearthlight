# Archive — PROPOSALS.md

*Append-only. Decided, rejected, and expired proposals. Kept because a rejected idea that keeps
resurfacing is information. Not read by default.*

---

## 2026-08-04 · P-003 — **done**
**Outcome:** executed by another agent before it was decided, and committed in
`5b458be image pipeline: Stage-A compiler/runner split`.

> | P-003 | 2026-08-03 | AMBER | open | **Write the image-pipeline stages into
> `hearthlight-image-prompts`** — style composition → likeness → final input image is being built by
> hand right now and exists nowhere in the instruction layer. | **Directly blocking.** This is where
> v1 is. Undocumented, it is not v1 of the skill — it is a draft that only works while Vince
> remembers it. |

`hearthlight-image-prompts/SKILL.md` and `hearthlight-shot-runner/SKILL.md` now carry the
two-command contract: `krea_style_comp.py` compiles immutable packets, `krea_style_comp_run.py`
runs them, two calibration shots precede `--all`, and D-016 records the prompt rule.

---

## 2026-08-04 · P-005 — **done**
**Outcome:** implemented by Vince's approved Visibility-Aware Shot Vision plan.

> | P-005 | 2026-08-03 | AMBER | open | **Close the correction loop in Studio** — a per-shot
> correction becomes versioned creative direction consumed by image prompting. | `GOALS.md` core
> problem 1. |

Studio now stores append-only Shot Vision revisions, compiles visibility-aware production objects,
shows exact Krea prompts and estimates on a Prompt Board, and binds generation to that approval.
Video prompt behaviour is unchanged in this milestone.

---

## P-006 — decided 2026-08-11, done

Move `HANDOFF.md` to `archive/`. Done, together with root `AUDIENCE-CONTEXT.md`. Both stated the
engine/client framing as the product's identity, which Vince superseded on 2026-08-11: Hearthlight
is a single-operator AI filmmaking tool. The rule the framing protected — nothing about a project
is assumed — survives as D-003.

## P-004 · P-013 — decided 2026-08-11, moot

Both existed to reconcile `yugioh/status.yml` with reality: gates 0-3 read `pending` while gate 4
read `approved`, and P-013 was raised because no autonomy tier was permitted to write the fix.

D-026 removes gates. There is no ledger left to ratify, and per-shot state is computed from the shot
record rather than declared. Two proposals, open 8 and 1 days, closed by deleting the thing they
were about.
