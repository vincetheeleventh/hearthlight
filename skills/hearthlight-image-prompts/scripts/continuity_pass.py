#!/usr/bin/env python3
"""The film-level continuity agent — one Hermes pass with every shot in view.

Every other reviewer in Hearthlight judges ONE shot. That keeps them honest and cheap, and
it makes cross-shot disagreement structurally invisible: shot 1 said "a pile of Yu-Gi-Oh
trading cards", shot 5 said "a pile of trading cards", and the per-shot reviewer passed
both because shot 1 was never in the room.

This agent's packet is the whole film and almost nothing else. Wide and shallow, on purpose
— see references/CONTINUITY-PASS.md. It reports disagreements and never resolves them.

Commands
  packet  write the packet without calling Hermes (inspect what the agent will see)
  run     call Hermes and write findings
  show    print the last findings
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUDIO = HERE.parents[2]
CONTRACT = HERE.parent / "references" / "CONTINUITY-PASS.md"

_SPEC = importlib.util.spec_from_file_location("prompt_authoring", HERE / "prompt_authoring.py")
authoring = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(authoring)

SEVERITIES = ("block", "warn", "note")


def project_root(slug: str) -> Path:
    root = STUDIO / "projects" / slug
    if not root.is_dir():
        raise SystemExit(f"No such project: {slug}")
    return root


def build_packet(root: Path) -> dict:
    """Every shot, flattened. Resist enriching this — see the contract."""
    registry, by_id, _by_label = authoring.registry_records(root)
    manifest = authoring.read_json(root / "03-bible" / "assets.json", {}) or {}
    props = authoring.read_json(root / "03-bible" / "props.json", {}) or {}

    label_of = {
        str(shot.get("shot_id")): authoring.normalize_shot(shot.get("display_number"))
        for shot in registry.get("shots", []) if isinstance(shot, dict)
    }

    shots: list[dict] = []
    for shot in registry.get("shots", []):
        if not isinstance(shot, dict) or not shot.get("shot_id"):
            continue
        prompt = shot.get("prompt") if isinstance(shot.get("prompt"), dict) else {}
        owner = shot.get("shared_setup_owner_shot_id")
        shots.append({
            "shot": authoring.normalize_shot(shot.get("display_number")),
            "shot_id": str(shot["shot_id"]),
            "title": shot.get("title"),
            "still": " ".join(str(prompt.get("still") or "").split()),
            "action": " ".join(str(prompt.get("action") or "").split()),
            "bound_characters": authoring.relevant_characters(manifest, shot),
            "bound_props": [item.get("name") for item in authoring.relevant_props(props, shot)],
            "reuses_setup_of": label_of.get(str(owner or ""), None),
        })

    return {
        "schema_version": 1,
        "project": root.name,
        "shot_count": len(shots),
        "props_canon": [
            {"name": prop.get("name"), "canon": prop.get("canon")}
            for prop in authoring.binding_entries(props, "props")
        ],
        "shots": shots,
    }


def instructions(packet: dict) -> str:
    schema = {
        "findings": [{
            "code": "prop_drift|identity_drift|setup_drift|geography_drift|light_drift|binding_gap|count_drift",
            "severity": "block|warn|note",
            "shots": ["", ""],
            "quotes": {"": ""},
            "detail": "",
        }],
        "clean": True,
    }
    return (
        "You are Hearthlight's Film Continuity Supervisor. You are the only agent in this system that sees "
        "every shot at once, and you have exactly one job: find places where two shots state facts that "
        "disagree.\n\n"
        "REPORT, NEVER RESOLVE. Name both shots and quote the exact disagreeing phrase from each. Do not "
        "decide which shot is correct, do not suggest replacement wording, and do not rewrite prompts. "
        "You have the widest view and the shallowest context in the system, which makes you the worst-placed "
        "thing here to make a creative call.\n\n"
        "DO NOT FLAG intentional change, wording variety, or synonym choice. A film is allowed to move: light "
        "changes because time passes, a character changes clothes because he changed. Where the shot text or "
        "the action gives a reason, there is no finding. 'A man in his forties' and 'the father' are the same "
        "person. Prose need not match; FACTS must not disagree.\n\n"
        "A shot that declares reuses_setup_of MUST describe that setup consistently with its owner — that is "
        "the strongest signal available to you. A prop listed in props_canon must be named with its canon "
        "identity everywhere it is visible; a generic substitute in one shot and a specific name in another "
        "is prop_drift at severity block.\n\n"
        "Reserve 'block' for a defect that will make the render wrong. If you emit block for mere variety, "
        "this pass gets ignored and then it protects nothing. Return strict JSON only, no prose outside it.\n\n"
        "CONTRACT:\n" + CONTRACT.read_text(encoding="utf-8")
        + "\n\nOUTPUT SCHEMA:\n" + json.dumps(schema, ensure_ascii=False)
        + "\n\nFILM PACKET:\n" + json.dumps(packet, ensure_ascii=False)
    )


def report(findings: dict) -> None:
    items = findings.get("findings")
    items = [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []
    if not items:
        print("clean — no cross-shot disagreements reported")
        return
    order = {name: index for index, name in enumerate(SEVERITIES)}
    items.sort(key=lambda item: order.get(str(item.get("severity")), 9))
    for item in items:
        shots = ", ".join(str(value) for value in (item.get("shots") or []))
        print(f"\n[{item.get('severity')}] {item.get('code')} — shots {shots}")
        print(f"  {item.get('detail')}")
        for shot, quote in (item.get("quotes") or {}).items():
            print(f"    {shot}: \"{quote}\"")
    counts = {name: sum(1 for item in items if item.get("severity") == name) for name in SEVERITIES}
    print(f"\n{counts['block']} block · {counts['warn']} warn · {counts['note']} note")


def findings_path(root: Path) -> Path:
    return root / "04-images" / "continuity-findings.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("packet", "run", "show"))
    parser.add_argument("--project", required=True)
    parser.add_argument("--out", help="where to write the packet (packet command)")
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()

    root = project_root(args.project)

    if args.command == "show":
        existing = authoring.read_json(findings_path(root), None)
        if not isinstance(existing, dict):
            print("no continuity findings yet — run `continuity_pass.py run`")
            return 0
        print(f"pass at {existing.get('created_at')} · {existing.get('shot_count')} shots")
        report(existing)
        return 0

    packet = build_packet(root)

    if args.command == "packet":
        destination = Path(args.out) if args.out else root / "04-images" / "continuity-packet.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{packet['shot_count']} shots -> {destination}")
        return 0

    try:
        result = authoring.run_hermes(instructions(packet), args.timeout)
    except ValueError as error:
        print(f"continuity pass failed: {error}", file=sys.stderr)
        return 1

    result["created_at"] = authoring.now()
    result["shot_count"] = packet["shot_count"]
    result["packet_hash"] = authoring.sha256_text(
        json.dumps(packet, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    )
    result["contract_hash"] = authoring.sha256_file(CONTRACT)

    destination = findings_path(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report(result)
    print(f"\nwritten: {destination.relative_to(STUDIO)}")
    print("Advisory only. Findings name disagreements; the decision stays Vince's.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
