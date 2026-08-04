# Versioned two-stage image review contract

## Ledger

`04-images/generations.jsonl` is append-only. Never edit, reorder, or truncate it.

Events:
- `generation`: shot, immutable version, `workflow_stage`, parent version, local file/digest/dimensions, exact prompt, model, job/URL, exact references, creation time.
- `review`: shot/version, `review_stage`, status, proposal ID, feedback verbatim.
- `selection`: shot/version, purpose (`composition-base` or `final`), immutable asset path.

The same source may serve multiple shots, but it has one generation owner. Review and selection remain per shot.

## Stage order

1. Record Krea output as `workflow_stage: style-composition`.
2. Propose and confirm composition review.
3. Select one `composition-base` per approved setup.
4. Compile GPT Image 2 packets from those selected bases.
5. Record likeness outputs with the base version as parent.
6. Propose and confirm likeness review.
7. Select final.

A likeness-required shot cannot select a Stage A version as final. A shot with no likeness/hero-prop requirement may.

## Rant handling

Absence from a rant is not approval. Parse only named shots. Preserve Vince’s feedback verbatim. Ambiguous numbering blocks application. Show the proposal before applying it. After confirmation, unflagged items become approved for that review stage and flagged items become `revision-requested`.

## Recovery

At resume, read JSONL and the local files. A recorded job is paid-and-done. Continue from the first missing generation owner. Never infer completion from chat. Never generate a shared shot or source-photo shot.

## Imports

Download playground generations first. Record their real chronology and known metadata. Mark unavailable prompt/model/time fields unknown; never invent them. Imported files also use immutable version numbers.