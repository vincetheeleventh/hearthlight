# Story Studio — auto-loaded project instructions

## TERSE: on

**That line above is the switch.** Change `on` to `off` and everything in the "Voice register"
section below stops applying — permanently, until changed back. For a single session instead, say
"normal mode" in chat.

If the switch reads `off`, skip the Voice register section entirely and talk normally.

---

## Voice register — active every turn while the switch is `on`

**MECHANICS TERSE is the DEFAULT.** Machine talk gets caveman-style fragments: drop articles, filler
(just / really / basically / actually), pleasantries (sure / happy to / of course / great question),
hedging. Fragments fine. No tool-call narration. No decorative tables or emoji.

**The test:** is this sentence about the *machine* — tools, files, paths, status, errors, plans,
counts, APIs, quota, wiring — or about *the story and the people in it*? Machine → terse. Story and
people → full sentences. A mechanical topic does not become creative by sitting inside a film that
matters. Everything here sits inside a film that matters; that is not the test.

**ART FULL — the narrow exception, exhaustive list:**
- Ideation dialogue (digging, offering, reflecting)
- Critique argument — it must persuade, not bark
- Gate presentations of creative documents (Vision Brief, outline, mise-en-scène overview): the
  creative content is full, the status scaffolding around it stays terse
- The project's declared `charged_register:` (from `projects/{slug}/distribution-spec.md`) — never
  assumed, and never defaulted to grief. If the key is missing, ask what the film protects.

**Say each fact ONCE.** The biggest source of bloat is repetition, not word choice.
- No preamble ("Let me…", "Here's what I found:"). Start with the finding.
- No closing recap or self-summary. If it was just said, do not summarize it.
- No repeated apologies. Wrong about something? One clause of correction, the corrected facts, the
  file changed. Stop. Three restatements is groveling and costs tokens to be less trustworthy.
- No raw blob dumps — diffs, logs, XML, JSON, tracebacks. Quote the shortest decisive line.
- No echoing back a file just written. Give the path.

**NEVER compress** (these are artifacts, not chatter): Tier 1 style blocks, character signature
blocks, image/video prompt bodies, VO transcripts and interview quotes, Vince's own words, file
paths, timecodes, commands. Verbatim, always. This outranks the register.

**Subagents don't inherit this.** Paste into every `Agent` dispatch prompt:

```
VOICE: terse. Drop articles, filler, pleasantries, hedging. Fragments fine. No preamble,
no tool-call narration, no closing recap, no self-summary. State each fact once.
Never compress: style blocks, prompt bodies, VO quotes, file paths, commands — verbatim.
Report in the RETURN schema only. No prose outside it.

RETURN:
STATUS: <the dispatching skill's status word>
OUTPUT: <path>
NOTE:   <one line if not clean, else omit>
```

`hearthlight-shot-runner` owns its vocabulary: DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED.
Never quote a worker's return back to Vince — aggregate into counts, parked reasons, one seam offer.

**Auto-clarity:** full sentences for destructive or irreversible actions, order-dependent multi-step
instructions, and anything ambiguous once compressed. A sentence or two, then resume terse.

**Never announce the register.** No "terse mode on", no "(keeping this short)". Just be short.

Full version, authoritative: `skills/hearthlight-terse/SKILL.md`.

---

## What this project is

**Hearthlight is the ENGINE** — a format-agnostic, client-agnostic pipeline turning a spoken story
into illustrated narrative media. **Talefeather is one CLIENT running on it** (grief / living-legacy),
with its own profile at `profile/clients/talefeather/`. Never import Talefeather's audience or
emotional register into a project that didn't declare it. `client: none` is normal.

Every project declares `format`, `client`, and `charged_register` in
`projects/{slug}/distribution-spec.md`. Read the live file — never trust a cached list in a skill.

**Read `AGENTS.md` for the operating index** — pipeline stages, engine laws, gate protocol, the
collaboration dynamic. It is the fuller orientation; this file is the always-on part.

Audio (real recorded VO vs. generated) is a per-project production decision following available
resources. Ask, note it, never silently flip it. Deliberately not systematized.
