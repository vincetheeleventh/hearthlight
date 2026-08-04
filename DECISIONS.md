---
doc: DECISIONS
role: law
authority: canon
owner: agents
updated: 2026-08-04
answers:
  - which design rules are currently in force
  - where a given rule binds
  - whether a choice has already been settled
not_here:
  the argument behind a rule: archive/decisions/D-0XX.md
  what is built: PRODUCT_SPEC.md
  what is proposed: PROPOSALS.md
archive: archive/decisions/
---

# DECISIONS — the rules in force

One line per decision: **what is settled, and where it binds.** The reasoning that produced each —
Context, Reason, Consequences — lives in `archive/decisions/D-0XX.md`. Open that file only when you
are about to challenge the rule; otherwise this table is the whole of what you need.

**Adding one.** Write the argument to `archive/decisions/D-0XX.md`, then add its law here. A
decision earns an entry when it closes off an alternative someone would plausibly reconsider. Never
rewrite a rule in place — supersede it: set `in_force: false` and `superseded_by:` in the archived
file, and replace the row.

---

| ID | The rule | Binds |
|---|---|---|
| D-001 | The skills **are** the pipeline. Behaviour changes by editing Markdown, not by writing code. | `skills/` |
| D-002 | The Claude skill store holds pointer stubs only; `skills/*/SKILL.md` is the single source. | every stub |
| D-003 | Hearthlight is the **engine**; a client (Talefeather) runs on it. Assuming a client is a defect. | every project |
| D-004 | `charged_register` is declared per project and never defaulted — least of all to grief. | `hearthlight-terse`, distribution spec |
| D-005 | Mechanics terse, art full. Machine talk gets fragments; story and people get sentences. | every response |
| D-006 | Git tracks the instruction layer. `projects/` stays out — large, rights-constrained, not the system. | `.gitignore` |
| D-007 | Autonomy lives **between** gates, never through them. Stage A is machine-judged; Stage B is Vince only. | `hearthlight-shot-runner` |
| D-008 | Aspect ratio is a composition law, decided before framing — not an export setting. | distribution spec, all framing |
| D-009 | `shot_id` is immutable identity. Deletion is retirement. No asset moves by row number. | shot registry, every workbook |
| D-010 | The leaked-key guard is hash-based inside `checkpoint.py`. `git-init-commit.sh` is dead. | `governance/` |
| D-011 | The checkpoint splits facts from judgment: `gather` fails loudly, the agent writes the verdict. | `governance/checkpoint.py` |
| D-012 | Every agent commit carries an `Agent:` trailer. Unattributed changes are reported, not hidden. | every commit |
| D-013 | The system improves itself under its own gate law: GREEN executes, AMBER proposes, RED never. | `PROPOSALS.md`, weekly workshop |
| D-014 | Checkpoints commit but do not push. Vince pushes. | `governance/checkpoint.py` |
| D-015 | The enemy is AI filmmaking itself — wrong generations, drifting style, obsolete workflows — not a competitor. | `GOALS.md` |
| D-017 | Canon documents state the current state only. History moves to `archive/`; every canon doc carries YAML front matter. | `governance/canon.py`, all canon docs |
| D-018 | Stage-A prompts compile from versioned Shot Vision into visibility-aware production objects; Action is validation context only, and exact Prompt Board approval precedes spend. | Studio, `hearthlight-image-prompts`, Krea runner |
| D-019 | Stage-A prompt craft belongs to a focused LLM author; Python grounds and enforces invariants, and an independent LLM reviewer must pass semantic quality before approval. | hearthlight-image-prompts, Studio Prompt Board |
