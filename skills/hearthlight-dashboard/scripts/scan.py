#!/usr/bin/env python3
"""Hearthlight dashboard scanner.

Reads pipeline.json (stage manifest) + each project's status.yml (gate ledger)
+ the actual files on disk, and emits one status JSON the dashboard renders.

Ground truth rules:
  - status.yml is the ONLY source of gate approval (gates live in Telegram;
    the ledger is their stone on this side of the Jordan).
  - File scanning only tells us what's DRAFTED, never what's APPROVED.
Stdlib only. Runs on Windows, WSL, or any POSIX.
"""
import json, os, re, sys, glob, datetime

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STUDIO_ROOT = os.path.dirname(os.path.dirname(SKILL_DIR))  # .../Story Studio
PROJECTS_DIR = os.path.join(STUDIO_ROOT, "projects")
# Display base for copyable drop paths (Vince's machine, Windows Explorer view)
WINDOWS_BASE = r"C:\Users\vxi\AppData\Local\hermes\Story Studio\projects"

IGNORE = re.compile(r"(Zone\.Identifier$|^\.|Thumbs\.db$|desktop\.ini$)", re.I)

LEDGER_STATES = ("approved", "pending", "unconfirmed", "n/a", "done")


def load_pipeline():
    with open(os.path.join(SKILL_DIR, "pipeline.json"), encoding="utf-8") as f:
        return json.load(f)["stages"]


def load_zones():
    with open(os.path.join(SKILL_DIR, "intake.json"), encoding="utf-8") as f:
        return json.load(f)["zones"]


def zone_report(proj_dir, zone):
    """Count files under a zone target (recursive); for named zones also list subfolder names."""
    target = os.path.join(proj_dir, zone["target"].replace("/", os.sep))
    count, recent, names = 0, [], []
    if os.path.isdir(target):
        for root, dirs, fs in os.walk(target):
            # style zone ('03-bible/refs/') should not swallow its specialised subfolders
            if zone["id"] == "style":
                dirs[:] = []
            for fn in fs:
                if IGNORE.search(fn):
                    continue
                count += 1
                recent.append((os.path.getmtime(os.path.join(root, fn)), fn))
        if zone.get("named"):
            names = sorted(d for d in os.listdir(target)
                           if os.path.isdir(os.path.join(target, d)))
    recent = [n for _, n in sorted(recent, reverse=True)[:4]]
    return {**{k: zone[k] for k in ("id", "label", "icon", "target", "named", "hint")},
            "name_label": zone.get("name_label", ""),
            "count": count, "recent": recent, "names": names}


def parse_ledger(path):
    """Flat 'key: value' file. Values: approved [YYYY-MM-DD] | pending | unconfirmed | n/a | done."""
    ledger, meta = {}, {}
    if not os.path.isfile(path):
        return None, None
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key, val = key.strip(), val.strip()
        if key in ("project", "note"):
            meta[key] = val
            continue
        m = re.match(r"(approved|pending|unconfirmed|n/a|done)\s*(\S.*)?$", val, re.I)
        if m:
            ledger[key] = {"state": m.group(1).lower(), "date": (m.group(2) or "").strip()}
    return ledger, meta


def stage_files(proj_dir, patterns):
    found = []
    for pat in patterns:
        for p in glob.glob(os.path.join(proj_dir, pat.replace("\\", "/"))):
            name = os.path.basename(p)
            if os.path.isfile(p) and not IGNORE.search(name):
                found.append({"name": name, "rel": os.path.relpath(p, proj_dir).replace("\\", "/"),
                              "mtime": os.path.getmtime(p)})
    # dedupe by rel path
    seen, out = set(), []
    for f in sorted(found, key=lambda x: -x["mtime"]):
        if f["rel"] not in seen:
            seen.add(f["rel"])
            out.append(f)
    return out


def derive_status(stage, ledger_entry, files):
    """approved | drafted | in_progress | blocked | not_started  (+ unconfirmed flag)"""
    state = (ledger_entry or {}).get("state", "unconfirmed")
    if state in ("approved", "done"):
        return "approved"
    if state == "n/a":
        return "skipped"
    if files:
        return "drafted"  # material exists, waiting on Vince's ✅ (or ratification)
    return "not_started"


def next_action_for(slug, stages_out, ledger_exists):
    # 1. Unratified history: drafted gate stages whose ledger says 'unconfirmed'
    unconfirmed = [s for s in stages_out
                   if s["kind"] == "gate" and s["status"] == "drafted"
                   and s["ledger_state"] == "unconfirmed"]
    if unconfirmed:
        names = ", ".join(s["label"] for s in unconfirmed)
        return {"type": "decision", "stage": unconfirmed[0]["id"],
                "label": "Ratify your gate history",
                "detail": f"Work exists on disk for: {names} — but no ✅ is recorded. "
                          f"Tell the Hearthlight bot which gates you've approved so it writes status.yml. "
                          f"Until then the dashboard won't guess.",
                "where": "Telegram"}
    # 2. First gate stage not approved
    for s in stages_out:
        if s["kind"] != "gate" or s["status"] in ("approved", "skipped"):
            continue
        if s["status"] == "drafted":
            return {"type": "decision", "stage": s["id"],
                    "label": f"Review & ✅ {s['label']} ({s['gate']})",
                    "detail": s["inputs"][0]["label"] if s["inputs"] else "Give your ✅ in Telegram.",
                    "where": "Telegram"}
        # not started → surface its first input
        for inp in s["inputs"]:
            if inp["type"] == "file":
                return {"type": "file", "stage": s["id"],
                        "label": f"{s['label']}: {inp['label']}",
                        "detail": "Drop it from Windows Explorer, then tell the bot it's there.",
                        "path": WINDOWS_BASE + "\\" + slug + "\\" + inp.get("path", "")}
        if s["inputs"]:
            return {"type": "decision", "stage": s["id"],
                    "label": f"{s['label']} ({s['gate']}) — not started",
                    "detail": s["inputs"][0]["label"], "where": "Telegram"}
        return {"type": "decision", "stage": s["id"],
                "label": f"Start {s['label']}", "detail": "Kick it off with the bot.",
                "where": "Telegram"}
    return {"type": "done", "label": "All gates passed",
            "detail": "The story is through the pipeline. Cut it, watch it, share it."}


def scan_project(slug, pipeline, zones):
    proj_dir = os.path.join(PROJECTS_DIR, slug)
    ledger, meta = parse_ledger(os.path.join(proj_dir, "status.yml"))
    ledger_exists = ledger is not None
    ledger = ledger or {}
    stages_out = []
    for st in pipeline:
        files = stage_files(proj_dir, st["artifacts"])
        entry = ledger.get(st["id"])
        status = derive_status(st, entry, files)
        expected = [{"name": os.path.basename(e),
                     "present": os.path.isfile(os.path.join(proj_dir, e.replace("/", os.sep)))}
                    for e in st.get("expected", [])]
        stages_out.append({
            "id": st["id"], "label": st["label"], "gate": st["gate"], "kind": st["kind"],
            "status": status, "expected": expected,
            "ledger_state": (entry or {}).get("state", "unconfirmed"),
            "ledger_date": (entry or {}).get("date", ""),
            "files": [{"name": f["name"], "rel": f["rel"],
                       "mtime": datetime.datetime.fromtimestamp(f["mtime"]).strftime("%Y-%m-%d")}
                      for f in files[:8]],
            "file_count": len(files),
            "inputs": st["inputs"],
            "drop_base": WINDOWS_BASE + "\\" + slug + "\\",
        })
    # momentum: newest file anywhere in the project (excluding the ledger itself)
    last = 0
    for root, dirs, fs in os.walk(proj_dir):
        for fn in fs:
            if IGNORE.search(fn) or fn == "status.yml":
                continue
            try:
                last = max(last, os.path.getmtime(os.path.join(root, fn)))
            except OSError:
                pass
    last_touched = datetime.datetime.fromtimestamp(last).strftime("%Y-%m-%d") if last else ""
    days_idle = (datetime.datetime.now() - datetime.datetime.fromtimestamp(last)).days if last else None
    return {"slug": slug, "ledger_exists": ledger_exists, "meta": meta or {},
            "last_touched": last_touched, "days_idle": days_idle,
            "stages": stages_out,
            "zones": [zone_report(proj_dir, z) for z in zones],
            "gates_approved": sum(1 for s in stages_out
                                  if s["kind"] == "gate" and s["status"] == "approved"),
            "gates_total": sum(1 for s in stages_out if s["kind"] == "gate"),
            "next_action": next_action_for(slug, stages_out, ledger_exists)}


def scan():
    pipeline = load_pipeline()
    zones = load_zones()
    projects = []
    if os.path.isdir(PROJECTS_DIR):
        for slug in sorted(os.listdir(PROJECTS_DIR)):
            if os.path.isdir(os.path.join(PROJECTS_DIR, slug)) and not slug.startswith("."):
                projects.append(scan_project(slug, pipeline, zones))
    return {"generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "studio_root": STUDIO_ROOT, "projects": projects}


if __name__ == "__main__":
    json.dump(scan(), sys.stdout, indent=2, ensure_ascii=False)
