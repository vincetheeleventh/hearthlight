# Archive — ROADMAP.md

*Append-only. Removed from canon, kept for the trail. Not read by default.*

---

## 2026-08-04 · from ROADMAP.md § Open questions
**Why:** answered — the answers now stand as fact in canon; the questions were carrying dated
strikethrough narration (D-017).

> 1. ~~Is the deliverable the film or the engine?~~ ✅ **EFFECTIVELY ANSWERED 2026-08-03** — v1 requires
>    **both**: the finished film *and* the architecture that finished it. Neither alone.
> 2. ~~What does "done" look like for v1?~~ ✅ **ANSWERED 2026-08-03** — see *The v1 target* above.
> 5. ~~Is `hearthlight-dashboard` product or personal utility?~~ ✅ **ANSWERED 2026-08-03** — product
>    surface. `GOALS.md` primary outcome 4.

---

## 2026-08-04 · from ROADMAP.md § Known problems
**Why:** resolved. Each was carrying a *(Resolved …)* stamp or describing a state that no longer holds.

> 1. **`git-init-commit.sh` could never succeed.** Its leaked-key guard greps for a key literal that is
>    written inside the guard itself, so it always self-aborted — which is why no repository existed
>    until 2026-08-03. Superseded by `governance/checkpoint.py` (hash-based). *(Resolved 2026-08-03.)*
> 2. **`README.md` is stale.** Its layout tree omits 7 of 21 skills and still describes
>    `hearthlight-asset-bible/` as a tombstone to delete; that folder no longer exists. *(Fixed 2026-08-03.)*
> 5. **`hearthlight-dashboard` is absent from `AGENTS.md`.** The operating index does not list it, so a
>    session that reads only `AGENTS.md` never learns it exists. *(Fixed 2026-08-03.)*

---

## 2026-08-04 · from ROADMAP.md § Near-term priorities
**Why:** inherited verbatim from `HANDOFF.md` §5 (2026-07-06) and unreviewed for five weeks. Kept
here in full; canon now carries one open question pointing at it rather than eleven stale rows.

> From `HANDOFF.md` §5, dated 2026-07-06 — **four weeks old and unverified.** Status below is my
> reading of the current tree, not Vince's confirmation.
>
> | # | Item | Apparent status |
> |---|---|---|
> | 1 | Confirm the Telegram bot responds | Unknown |
> | 2 | Remove dangling `profiles\gemma\skills` symlink | Unknown — outside this repo |
> | 3 | Finish `gemma → LocalHermes` rename | **Not done** — `start-gemma-model.bat` still present |
> | 4 | Stand up local model on the 3090 | Unknown — outside this repo |
> | 5 | Retire WSL Hermes | Likely done — `git-init-commit.sh` still assumes WSL paths |
> | 6 | Rebuild the STT venv | **Not done** — `.venv-stt` still dead |
> | 7 | Rotate + wire the RunningHub key | **Unknown — verify before Stage 6** |
> | 8 | Verify the Notion MCP token | Unknown |
> | 9 | "Love list" — positive side of `TASTE.md` | **Not done** — `TASTE.md` has Reaches-for / Kills / Rules, no swipe file |
> | 10 | Interview skill (question craft for the recording session) | **Not built** |
> | 11 | Cold-viewer subagent (fresh-eyes pass on the assembled cut) | **Not built** |

---

## 2026-08-04 · from ROADMAP.md § header and § The v1 target
**Why:** doc-revision narration — provenance about the document's own rewriting, not about the product.

> Last updated: 2026-08-03 · Source: `HANDOFF.md` §5–6 (2026-07-06), file mtimes, `status.yml` ledgers.
>
> This supersedes `HANDOFF.md` §6, which named McConaughey as the pilot to push end to end.
> **`yugioh` is the active film; `mcconaughey-call` is not the v1 target.**
>
> ## Gaps opened by the revised North Star — 2026-08-03
> `GOALS.md` was rewritten to aim at **AI-filmmaking problems** rather than at a competitor. Three of
> its stated outcomes have no implementation. These are now roadmap items, not oversights.
>
> **Note on the gate ledger:** `yugioh/status.yml` shows gates 0–3 as `pending` while gate 4 is
> approved — the film advanced faster than the ledger was maintained. Worth a ratification pass so the
> record matches reality. *(Now Known problem 8, stated in the present tense.)*

---
