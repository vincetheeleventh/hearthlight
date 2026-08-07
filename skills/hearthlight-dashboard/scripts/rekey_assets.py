#!/usr/bin/env python3
"""Rekey asset and prop shot bindings from display numbers to stable Shot IDs.

Shot numbers are a *label*. They get renumbered every time the edit changes — 24 of
yugioh's 28 shots were renumbered at least once — and every registry that binds by
number silently rots the moment they do. `shot_id` is permanent (DECISIONS.md D-009);
this script moves the bindings onto it and then the rot cannot happen again.

The failure this was written for: assets.json bound `character-father`, `character-mother`
and `setting-parents-bedroom` to shot 5. Shot 5 is now an overhead close-up of a boy's
hands. The prompt author received four wrong reference sheets and wrote a coherent prompt
from them.

By default numbers resolve against the current display number AND every historical label
in `legacy_numbers`. Where a number matches more than one shot the script REFUSES — it
does not guess which numbering epoch the registry was written in. On yugioh that is almost
every label, because three epochs overlap.

`--epoch` breaks the tie by naming the epoch explicitly:

  display      the current display_number
  legacy-first the oldest label a shot carries
  legacy-last  the most recent label before the current one

Choosing an epoch is a judgment about provenance, so it is Vince's to make and the plan
prints titles beside every binding for exactly that reason. Read the table before applying:
`prop-warrior-card -> Warrior Returning Alive` is right, `-> Cleaning Up` is not.

Where a label resolves to nothing the binding is dropped and reported — the shot was cut.

Commands
  plan    show the resolution table; write nothing
  apply   rewrite the bindings, keeping the old numbers under `shots_legacy`
  verify  confirm every binding is a shot_id that exists in the registry
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve()
STUDIO = HERE.parents[3]

BINDING_FILES = ("03-bible/assets.json", "03-bible/props.json")


def normalize_shot(value: object) -> str:
    """Match prompt_authoring.normalize_shot exactly — divergence here is a silent bug."""
    text = str(value or "").strip()
    return text[:-2] if text.endswith(".0") and text[:-2].isdigit() else text.upper()


def read_json(path: Path, fallback):
    if not path.is_file():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return fallback


def write_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def project_root(slug: str) -> Path:
    root = STUDIO / "projects" / slug
    if not root.is_dir():
        raise SystemExit(f"No such project: {slug}")
    return root


EPOCHS = ("any", "display", "legacy-first", "legacy-last")


def epoch_labels(shot: dict, epoch: str) -> list[object]:
    """The label(s) a shot answers to under one numbering epoch.

    A shot with no `legacy_numbers` answers to no legacy epoch — it did not exist yet.
    Returning [] for it is correct, and is why 18B and 23B fall out as unbound.
    """
    legacy = shot.get("legacy_numbers") or []
    if epoch == "display":
        return [shot.get("display_number")]
    if epoch == "legacy-first":
        return legacy[:1]
    if epoch == "legacy-last":
        return legacy[-1:]
    return [shot.get("display_number"), *legacy]


def label_index(root: Path, epoch: str = "any") -> tuple[dict[str, list[dict]], dict[str, dict], list[dict]]:
    """Map every label in the chosen epoch to the shots that carried it.

    A label maps to a LIST, not a shot. Collision is the whole thing this guards
    against, so it must be representable.
    """
    registry = read_json(root / "05-storyboard" / "shots.json", {})
    shots = registry.get("shots") if isinstance(registry, dict) else None
    if not isinstance(shots, list) or not shots:
        raise SystemExit("05-storyboard/shots.json has no shot registry")

    by_label: dict[str, list[dict]] = defaultdict(list)
    by_id: dict[str, dict] = {}
    for shot in shots:
        if not isinstance(shot, dict) or not shot.get("shot_id"):
            continue
        by_id[str(shot["shot_id"])] = shot
        seen: set[str] = set()
        for value in epoch_labels(shot, epoch):
            label = normalize_shot(value)
            if label and label not in seen:
                seen.add(label)
                by_label[label].append(shot)
    return by_label, by_id, shots


def describe(shot: dict) -> str:
    return f"shot {shot.get('display_number')} · {shot.get('title')}"


def resolve(entry: dict, by_label, by_id) -> tuple[list[str], list[str], list[str]]:
    """Return (shot_ids, dropped_labels, ambiguous_labels) for one binding entry."""
    raw = entry.get("shots")
    if not isinstance(raw, list):
        return [], [], []

    shot_ids: list[str] = []
    dropped: list[str] = []
    ambiguous: list[str] = []
    for value in raw:
        text = str(value or "").strip()
        # already migrated
        if text in by_id:
            if text not in shot_ids:
                shot_ids.append(text)
            continue
        label = normalize_shot(value)
        matches = by_label.get(label, [])
        if not matches:
            dropped.append(label)
        elif len(matches) > 1:
            ambiguous.append(label)
        else:
            shot_id = str(matches[0]["shot_id"])
            if shot_id not in shot_ids:
                shot_ids.append(shot_id)
    return shot_ids, dropped, ambiguous


def entries(payload: dict) -> list[dict]:
    for key in ("assets", "props"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def command_plan(root: Path, apply_changes: bool, epoch: str) -> int:
    by_label, by_id, shots = label_index(root, epoch)
    blocked = False
    touched_ids: set[str] = set()
    print(f"epoch: {epoch}")

    for relative in BINDING_FILES:
        path = root / relative
        payload = read_json(path, None)
        if not isinstance(payload, dict):
            continue
        items = entries(payload)
        if not items:
            continue

        print(f"\n{relative}")
        for entry in items:
            if not isinstance(entry.get("shots"), list):
                continue
            shot_ids, dropped, ambiguous = resolve(entry, by_label, by_id)
            touched_ids.update(shot_ids)
            print(f"  {entry.get('id')}")
            for shot_id in shot_ids:
                print(f"      -> {describe(by_id[shot_id])}")
            for label in dropped:
                print(f"      DROPPED  label {label} matches no shot — cut from the edit")
            for label in ambiguous:
                blocked = True
                names = "; ".join(describe(s) for s in by_label[label])
                print(f"      AMBIGUOUS label {label} matches {len(by_label[label])}: {names}")
            if apply_changes and not ambiguous:
                entry["shot_ids"] = shot_ids
                entry["shots_legacy"] = {"epoch": epoch, "labels": entry.pop("shots")}

        if apply_changes and not blocked:
            payload["schema_version"] = max(int(payload.get("schema_version") or 1), 2)
            write_json(path, payload)
            print(f"  written: {relative}")

    unbound = [s for s in shots if s.get("shot_id") and str(s["shot_id"]) not in touched_ids]
    if unbound:
        print("\nSHOTS WITH NO ASSET BINDING AT ALL — check these by hand:")
        for shot in unbound:
            print(f"  {describe(shot)}")

    if blocked:
        print("\nBLOCKED: ambiguous labels above. Resolve by hand, then re-run.", file=sys.stderr)
        return 1
    if not apply_changes:
        print("\nplan only — nothing written. Re-run with `apply`.")
    return 0


def command_verify(root: Path) -> int:
    _by_label, by_id, _shots = label_index(root, "any")
    failures: list[str] = []
    checked = 0

    for relative in BINDING_FILES:
        path = root / relative
        payload = read_json(path, None)
        if not isinstance(payload, dict):
            continue
        for entry in entries(payload):
            name = f"{relative}:{entry.get('id')}"
            if isinstance(entry.get("shots"), list):
                failures.append(f"{name} still binds by number — run `apply`")
                continue
            bound = entry.get("shot_ids")
            if bound is None:
                continue
            if not isinstance(bound, list):
                failures.append(f"{name} shot_ids is not a list")
                continue
            for shot_id in bound:
                checked += 1
                if str(shot_id) not in by_id:
                    failures.append(f"{name} binds unknown shot_id {shot_id}")

    for failure in failures:
        print(f"FAIL  {failure}", file=sys.stderr)
    print(f"{checked} binding(s) checked, {len(failures)} failure(s)")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "apply", "verify"))
    parser.add_argument("--project", required=True)
    parser.add_argument(
        "--epoch", choices=EPOCHS, default="any",
        help="which numbering the bindings were written in; 'any' refuses on collision",
    )
    args = parser.parse_args()

    root = project_root(args.project)
    if args.command == "verify":
        return command_verify(root)
    return command_plan(root, apply_changes=args.command == "apply", epoch=args.epoch)


if __name__ == "__main__":
    raise SystemExit(main())
