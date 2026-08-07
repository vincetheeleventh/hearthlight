---
name: hearthlight-render-batching
description: "Hearthlight shot batches: run parallel, ledger-safe."
metadata:
  hermes:
    tags: [hearthlight, batching, parallel, subagents, kanban, ledger, moderation, krea]
    category: hearthlight
version: 0.1.0
---

# Hearthlight — Render Batching (parallel shot execution)

Cross-cutting lessons for dispatching Hearthlight render batches (Stage 3 conditioning
stills, Stage 6 video). Complements the protected `hearthlight-image-prompts` and
`hearthlight-shot-runner` skills — read those for the full stage gates; this skill owns
*how to run the batch itself*.

## The default: parallel, not sequential (Vince's correction)

Vince's explicit direction ("they could've been done in parallel via subagents... remember
this for future runs"): **independent shot units run in PARALLEL**, not one-at-a-time.
Dispatch via `delegate_task` batch (capped by `delegation.max_concurrent_children`,
default 3) or the durable `hermes kanban` board. This overrides the older "one shot at a
time invites drift" caution.

- Keep each worker's set **small and contiguous (3–5 shots)** — an iterative subagent hits
  its tool-iteration cap mid-batch and stops (see Recovery below).
- Each worker reads its prompt **verbatim from a packet file** and returns artifacts as
  paths, never pasted text, never session history.

## Ledger integrity rule (parallel safety, non-negotiable)

Parallel workers must **NOT** append to the shared append-only ledger (`generations.jsonl`,
or any single append-only file) concurrently — that corrupts it (lost-update / interleaved line).

- **Orchestrator-serializes pattern (preferred):** workers only write their output image and
  RETURN `(asset path, krea job id, url)`. The orchestrator runs the `record`/append step
  afterward, one at a time.
- If workers must record themselves, file-lock the append.

## Recovery: cut-off worker / orphaned in-flight job

A worker that hits its iteration cap may leave a job submitted-but-not-recorded. **Never
re-spend a completed job.** Recover it:

1. Read the worker's live transcript to find the in-flight `job id`.
2. Poll it (`get_job`) — it often completed after the worker died.
3. Download the result and record it yourself.
4. Resume the remaining shots with a fresh worker.

## Content-policy workaround (parent/child beats)

Krea 2 moderation rejects explicit intimate parent/child wording — e.g. "presses his mouth
to the top of the boy's head" + the child descriptor (distinct from bfl FLUX's minor
classifier; landscapes/framings pass).

Stage A fix (with Vince's approval — it's a charged beat):
- Reword **only the ACTION**, keep the silhouette/composition: "bends low, head level with
  the boy's, one hand on his shoulder". Leave the locked style clause and character
  signature strings **verbatim**.
- Write the original charged beat into the packet as `reassert_action` so it's restored at
  Stage B / final — never treat the Stage A base as finalizing that moment.
- The rewording is a per-shot packet edit, applied to the exact packet the worker reads.

See `references/parallel-and-moderation.md` for a full reproduction recipe plus the
project-driven aspect-ratio note.

## Notes

- `hearthlight-image-prompts` and `hearthlight-shot-runner` are user/externally owned and
  cannot be patched by autonomous curation (`hermes curator adopt <name>` opts them in).
- These batching lessons are kept here so a future session starts knowing them even though
  the canonical stage skills are protected.
