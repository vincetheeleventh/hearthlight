---
name: hearthlight-reference-report
description: Turn a folder of collected reference images + a research writeup into a glanceable, organized report on Notion — each image shown inline next to its caption and its role (what it's a reference FOR). Use after research/reference-collection so Vince can review at a glance instead of opening a directory of loose files.
version: 0.1.0
metadata:
  hermes:
    tags: [hearthlight, references, notion, report, mise-en-scene]
    category: hearthlight
---

# Hearthlight — Reference Report (loose images → glanceable Notion report)

## When to Use
After Hearthlight has collected reference images (period, likeness, location, style) into a project's `03-bible/refs/` and written a research note. The raw output — a directory of files plus a separate writeup — is NOT reviewable. This skill formats it into one report on Notion where every image sits next to what it's for. Triggered by "make this a report," "format the references," "put the refs in Notion so I can glance over them."

## The principle
A reference is useless if you can't see it next to its purpose. The failure mode is exactly what Vince hit: images in one place, words in another, nothing connected. Every reference in the report must answer, on sight: **what is this, and what is it a reference FOR?**

## Where it goes
Notion (it renders images inline; a markdown file in a folder does not). Build it as a **child page** of the project's thread/working-notes page, titled `{Project} — Visual Reference Report`. Keep the source markdown (`03-bible/visual-reference-*.md`) as the canonical text-with-sources; the Notion report is the visual view of it. Link the two.

## Structure of the report
Organize by **role**, not by filename. Typical sections for a period/likeness collection:
1. **Canon** — the one or two images everything else defers to (e.g. the captioned real photo). Lead with these, full size.
2. **Likeness** — per character, the closest period-accurate references; note age/era fit and any gaps (e.g. "closest free shot; the on-the-nose one is license-walled").
3. **Period & place** — interiors, palette, light, vehicles, signage — grouped by category.
4. **Hero objects** — the charged props (the phone), with the drawing note about why one choice beats another.
5. **Gaps & decisions** — what's confirmed-but-unobtainable (logged source), and the `[stylized — Vince decides]` choices.

Each entry = **image inline + one-line caption + role tag + confidence** (`[verified]` / `[likely]` / `[stylized]`). Group, don't list 21 raw files — a resemblance pool becomes one collapsed gallery with a single caption, not 21 entries.

## How to put images into Notion
The Notion MCP renders images that are reachable by URL. Local files in `03-bible/refs/` aren't URLs, so to show them inline either:
- upload/attach them via the Notion API where the MCP supports file upload, OR
- if upload isn't available, embed a **thumbnail gallery** by referencing the files and include the **local path** under each so Vince can open the full-res from disk; clearly mark which are shown vs. path-only.
Verify which your Notion MCP build supports the first time, and record it here. Never block the report on perfect inline rendering — a well-organized report with paths beats a directory every time.

## Curation rules (don't just dump)
- **Cull before reporting.** Off-target images (the timed-out subagent's "Victorian house" batch) get removed or sent to a clearly-labelled `refs/_rejected/` — never shown as if they were chosen refs.
- **Lead with the strongest.** Canon and best-likeness first; the pool last.
- **Carry the drawing notes.** The research's craft observations (why the coiled-cord phone beats cordless for *tension*) belong in the report next to the image, not buried in prose.
- **Preserve provenance & rights.** Pilot likeness images are private-use reference (PRD §3) — say so in the report header. Keep source URLs (from the writeup) linked.

## Pitfalls
- Reporting filenames instead of roles — Vince thinks in "what's my dad reference," not "gr-31285942.png".
- Showing 21 pool images individually — collapse to a gallery with one caption.
- Including culled/off-target images as if curated.
- Putting it in a markdown file in the folder (the original problem) instead of Notion (where it's glanceable).
- Dropping the rights note on a public-figure pilot.

## Verification
- Every shown reference has: image (or marked path), caption, role, confidence.
- Organized by role/category, strongest first; pools collapsed.
- Rejected images not shown as refs.
- Report links back to the source `visual-reference-*.md` and its sources; rights note present.
- Lives on Notion as a child of the project page; Vince can glance and grasp it without opening the directory.
