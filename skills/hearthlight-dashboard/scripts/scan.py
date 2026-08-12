#!/usr/bin/env python3
"""Read Hearthlight project state without inventing a second state model.

The production API owns Design, Production, and Inputs state. This scanner adds
intake-zone counts for the small legacy cockpit and otherwise passes that state
through unchanged.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request


SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STUDIO_ROOT = os.path.dirname(os.path.dirname(SKILL_DIR))
PROJECTS_DIR = os.path.join(STUDIO_ROOT, "projects")
STUDIO_API = os.environ.get("HEARTHLIGHT_STUDIO_URL", "http://127.0.0.1:8765").rstrip("/")
IGNORE = re.compile(r"(Zone\.Identifier$|^\.|Thumbs\.db$|desktop\.ini$)", re.I)


def load_zones() -> list[dict[str, object]]:
    with open(os.path.join(SKILL_DIR, "intake.json"), encoding="utf-8") as stream:
        return json.load(stream)["zones"]


def zone_report(project_dir: str, zone: dict[str, object]) -> dict[str, object]:
    target = os.path.join(project_dir, str(zone["target"]).replace("/", os.sep))
    count = 0
    recent: list[tuple[float, str]] = []
    names: list[str] = []
    if os.path.isdir(target):
        for root, directories, files in os.walk(target):
            if zone["id"] == "style":
                directories[:] = []
            for filename in files:
                if IGNORE.search(filename):
                    continue
                count += 1
                path = os.path.join(root, filename)
                recent.append((os.path.getmtime(path), filename))
        if zone.get("named"):
            names = sorted(
                name for name in os.listdir(target)
                if os.path.isdir(os.path.join(target, name))
            )
    return {
        **{key: zone[key] for key in ("id", "label", "icon", "target", "named", "hint")},
        "name_label": zone.get("name_label", ""),
        "count": count,
        "recent": [name for _, name in sorted(recent, reverse=True)[:4]],
        "names": names,
    }


def production_payload(slug: str) -> dict[str, object]:
    url = f"{STUDIO_API}/api/productions/{urllib.parse.quote(slug)}"
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            payload = json.load(response)
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        return {
            "available": False,
            "error": f"Current production state unavailable: {exc}",
            "shots": 0,
            "design": {},
            "production": {},
            "inputs": {},
            "nextAction": "Start Hearthlight Studio, then refresh.",
        }

    shots = payload.get("shots") if isinstance(payload.get("shots"), list) else []

    def tally(axis: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for shot in shots:
            if not isinstance(shot, dict):
                continue
            state = str((shot.get(axis) or {}).get("state") or "unknown")
            counts[state] = counts.get(state, 0) + 1
        return counts

    design = tally("designState")
    production = tally("productionState")
    inputs = tally("inputs")
    if inputs.get("broken"):
        next_action = f"Repair inputs on {inputs['broken']} shot(s)."
    elif production.get("needs-fix"):
        next_action = f"Revise {production['needs-fix']} shot(s) marked Needs fix."
    elif production.get("candidate-ready"):
        next_action = f"Review {production['candidate-ready']} candidate shot(s)."
    elif production.get("not-started"):
        next_action = f"Choose the next {production['not-started']} unstarted shot(s)."
    else:
        next_action = "Continue from the current film state."
    return {
        "available": True,
        "shots": len(shots),
        "runtimeSeconds": payload.get("runtimeSeconds", 0),
        "identitySource": payload.get("identitySource", ""),
        "design": design,
        "production": production,
        "inputs": inputs,
        "nextAction": next_action,
    }


def last_activity(project_dir: str) -> tuple[str, int | None]:
    newest = 0.0
    for root, _, files in os.walk(project_dir):
        for filename in files:
            if IGNORE.search(filename):
                continue
            try:
                newest = max(newest, os.path.getmtime(os.path.join(root, filename)))
            except OSError:
                continue
    if not newest:
        return "", None
    touched = dt.datetime.fromtimestamp(newest)
    return touched.strftime("%Y-%m-%d"), (dt.datetime.now() - touched).days


def scan_project(slug: str, zones: list[dict[str, object]]) -> dict[str, object]:
    project_dir = os.path.join(PROJECTS_DIR, slug)
    touched, idle = last_activity(project_dir)
    return {
        "slug": slug,
        "state": production_payload(slug),
        "last_touched": touched,
        "days_idle": idle,
        "zones": [zone_report(project_dir, zone) for zone in zones],
    }


def scan(project: str | None = None) -> dict[str, object]:
    zones = load_zones()
    slugs = []
    if os.path.isdir(PROJECTS_DIR):
        slugs = sorted(
            slug for slug in os.listdir(PROJECTS_DIR)
            if os.path.isdir(os.path.join(PROJECTS_DIR, slug)) and not slug.startswith(".")
        )
    if project:
        slugs = [slug for slug in slugs if slug == project]
    return {
        "generated_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "studio_root": STUDIO_ROOT,
        "production_api": STUDIO_API,
        "projects": [scan_project(slug, zones) for slug in slugs],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    json.dump(scan(args.project), sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
