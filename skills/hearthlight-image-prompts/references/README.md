# references/ — the authoring system

**These files are not background reading. They are the system.** A prompt written without them is
an improvisation that bypasses a contract, a reviewer, and every lesson paid for in failed
generations.

| File | Read it when |
|---|---|
| **`PROMPT-AUTHOR.md`** | Before writing any still prompt. The author's contract |
| **`PANEL-READING.md`** | Before interpreting a hand-drawn board panel. The vision pass |
| **`versioned-review.md`** | Before approving anything. The independent reviewer |
| **`CONTINUITY-PASS.md`** | Before a batch. The one agent that sees every shot at once |

## Four agents, three narrow and one wide

Three of these contracts govern an agent that sees **one shot**: the author, the panel reader,
the reviewer. That narrowness is deliberate — it keeps each one honest and cheap.

It also makes one class of defect invisible. Shot 1's prompt said *"Yu-Gi-Oh trading cards"*;
shot 5, which declares itself a re-use of shot 1's setup, said *"trading cards"*. Both are
individually fine. The reviewer passed both, because shot 1 was never in the room when shot 5
was judged, and the render came back generic.

`CONTINUITY-PASS.md` governs the fourth agent, whose packet is **the whole film and nothing
else** — no bible, no style, no Visions. Wide and shallow. It reports that two shots disagree
and never decides which is right.

## The authority order — memorise this

From `PROMPT-AUTHOR.md`. Everything downstream depends on it:

1. Film laws, rights, declared aspect ratio, locked aesthetic laws
2. **Latest submitted Shot Vision**
3. Storyboard frame-one, camera, Notes, **and the panel drawing** — baseline execution evidence
4. Narrative meaning and adjacent-shot continuity
5. Character, setting, wardrobe, prop records
6. Provider profile and request controls

> **The storyboard is baseline evidence, never a vote against the current Vision.** The panel
> drawing sits at tier 3 with it. A sketch is concrete and visual while a Vision is abstract and
> textual — and **concreteness is not authority.**

When sources cannot be reconciled: **block. Never average contradictions into vague prose.**

## The one thing that is not automated

An LLM authors; Python validates and appends nothing (`DECISIONS.md` D-020). There is no script that
writes prompt text, and there should not be — that is the charged part, and it stays with a model
under contract, reviewed by a second model, approved by Vince.

What Python owns: assembling the packet, hashing the contract version, validating the returned JSON,
refusing what fails.
