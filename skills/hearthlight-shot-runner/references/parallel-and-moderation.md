# Parallel batching + moderation reword — reproduction recipe (session 2026-08-01, yugioh v4)

## Parallel shot batch (orchestrator-serializes ledger)

1. Stage prompts first: compile every shot into a per-shot packet file
   (`04-images/prompt-packets/...`), one file per shot with the EXACT prompt.
2. Split owners into contiguous sets of 3–5 (respect `delegation.max_concurrent_children`).
3. Dispatch `delegate_task(tasks=[...])` one task per set — all run in parallel.
   Each worker: read prompt verbatim from its packet; submit `krea/krea-2/medium`
   (`aspect_ratio=<master>`, `resolution=1K`, `creativity=raw`, moodboard `{id, strength}`);
   poll `get_job`; download the single result; REPORT `(abs path, job id, url)`.
   Workers must NOT call the two-pass `record` / must NOT append to `generations.jsonl`.
4. Orchestrator then serializes the `record` step per returned path (one at a time) and
   reconciles the ledger against disk.

Prompt files are packet text, and subagents must load deferred Krea MCP tools via
`tool_describe(mcp__krea_ai__generate_image)` / `tool_describe(mcp__krea_ai__get_job)`
before `tool_call`. They are NOT in the top-level tool list.

## Iteration-cap recovery

- An iterative subagent hits its tool budget (~50 calls) mid-batch. Its transcript shows
  the last `job id` it submitted in `status: processing`.
- That job usually completes moments later. Poll it, download, record. Never re-submit a
  completed job (paid).
- Resume the untouched remainder with a fresh worker.

## Krea 2 moderation reword (charged parent/child beat)

Trigger: explicit mouth-on-child phrasing + child descriptor → `content_policy` rejection,
even for an innocent stage direction in an ink-illustration pass.

Worked fix (Vince-approved method):
- Reword ONLY the ACTION block. e.g.
  before: `kneeling and bending to kiss the top of the head of a nine-year-old boy ... presses his mouth to the top of the boy's head`
  after:  `kneeling and bending low over a nine-year-old boy ... his head lowered to the level of the boy's, one hand resting on the boy's shoulder`
- Keep the locked style clause + character signature/must-hold strings verbatim.
- Keep the composition, framing, silhouette, scale lines.
- Stash the original beat in the packet as `reassert_action` (and/or `original_action_excerpt`)
  so Stage B / final restores the exact moment. Do NOT let the reworded Stage A base stand
  as the final beat.
- This is Krea-specific; bfl FLUX has its own minor-classifier block (no brand words still
  triggers on "a small boy").

## Project-driven aspect ratio

`two_pass.py` (Hearthlight Stage 3) derives the master ratio from
`03-bible/assets.json` → `master_aspect_ratio`, via `master_ratio(root)`, and validates
recorded images against `ratio_target(master_ratio(root))`. To change a project's master
(4:3 → 16:9, etc.): update `project.json` + `assets.json`; every prompt/packet/
record tag that names the ratio must use `master_ratio(root)`, never a hardcoded literal.
Catching every hardcoded `4:3` at once avoids a silent metadata/validation mismatch.
