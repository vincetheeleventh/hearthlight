# live-action/ — PARKED. Not for illustrated films.

**Nothing in this folder is read by the illustrated pipeline.** It is craft for a capability
Hearthlight does not yet use: films that declare `medium: live-action` in their distribution spec.

Every current Hearthlight project is `medium: illustrated`. **If that is your project, stop here.**

---

## Why it is parked rather than deleted

The material is good, and it came from a real production practice. It is simply written for a
different medium — photoreal 8K live-action — and it is **actively harmful in an illustrated film.**

An ink-and-wash frame has no lens. It has no bokeh, no focus plane, no sensor and no shutter. Asking
a video model for "creamy bokeh" or "razor-thin focus" over a painted source is a direct instruction
to abandon the medium — the photoreal creep Vince watches for at Gate 5, and the failure the style
block and preservation clause exist to prevent.

## What is in here

| File | Holds |
|---|---|
| `optics-language-bank.md` | Six ready-to-paste FOV blocks (8°–107°), the lens decision tree, telephoto and wide visual outcome stacks, anti-drift locks, multi-shot lens consistency, optics anti-patterns |

## The one part that crosses over

**Field of view and camera distance are medium-independent** — they control how much world is in
frame, which is a framing decision, not a photographic one. That much has been kept in the
illustrated path, in `../prompt-architecture.md`, translated into illustration terms.

Everything else in here — bokeh, chromatic aberration, shutter blur, focus falloff, pore-level skin
— stays parked.

## Before using any of it

The project's distribution spec must read `medium: live-action`. If it does not, and you are reaching
for this folder, one of the two is wrong — resolve that first.
