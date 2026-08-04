#!/usr/bin/env python3
"""
Hearthlight daily product-alignment checkpoint.

Two commands, deliberately split (see DECISIONS.md D-011):

    gather   Collect facts. Writes checkpoints/.facts-YYYY-MM-DD.json and a
             checkpoints/YYYY-MM-DD.md skeleton with <!-- AGENT:... --> slots.
             Pure mechanics: no judgment, no opinions, no network.

    commit   Validate that the agent filled the skeleton, re-run the secret
             scan, then git commit (and push if a remote exists).
             Refuses to commit a skeleton that still has unfilled slots.

The split matters: `gather` can fail loudly and block the commit, so a broken
checkpoint never produces a committed artifact.

Stdlib only. No dependencies. Python 3.9+.

Usage:
    python governance/checkpoint.py gather
    python governance/checkpoint.py commit
    python governance/checkpoint.py gather --date 2026-08-03   # backfill
    python governance/checkpoint.py commit --no-push
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CHECKPOINTS = REPO / "checkpoints"
SKILLS = REPO / "skills"

CANON = ["GOALS.md", "PRODUCT_SPEC.md", "ROADMAP.md", "DECISIONS.md", "SKILL-INVENTORY.md"]
INDEX_DOCS = ["AGENTS.md", "README.md", "USER-GUIDE.md", "CLAUDE.md"]
PROPOSALS = "PROPOSALS.md"

# Backlog brakes. An agent asked to improve things will always find things to
# improve; these are what stop the backlog becoming the bloat it was built to
# prevent. (DECISIONS.md D-013.)
MAX_OPEN_PROPOSALS = 7
PROPOSAL_EXPIRY_DAYS = 30

# A SKILL.md past this is a merge/split candidate, not automatically a problem.
SKILL_SIZE_WARN_BYTES = 12_000

# SHA-256 of the known-leaked RunningHub key. Stored as a hash so the literal
# never enters the repository -- the bug that made git-init-commit.sh always
# self-abort (DECISIONS.md D-010).
LEAKED_KEY_SHA256 = "7046887de1bc2f4d0289007595441eb4ca1a785e80d1b69da14bc4dd2976c862"

SECRET_PATTERNS = [
    (re.compile(r"sk-[A-Za-z0-9_-]{20,}"), "openai-style key"),
    (re.compile(r"ghp_[A-Za-z0-9]{30,}"), "github token"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"), "slack token"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "aws access key"),
    (re.compile(r"AIza[0-9A-Za-z_-]{30,}"), "google api key"),
    (re.compile(r"(?i)\b(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"\s]{16,}['\"]"),
     "assigned credential"),
]

SCANNABLE = {".md", ".py", ".sh", ".bat", ".ps1", ".json", ".yml", ".yaml", ".txt", ".mjs", ".js"}

# Pruned before descending. `projects/` is excluded on purpose: the checkpoint
# watches the Hearthlight SYSTEM only (Vince, 2026-08-03; see DECISIONS.md D-006).
SKIP_DIRS = {
    ".git", "projects", ".venv-stt", "node_modules", "__pycache__",
    ".artifact-work", "test-tmp", ".test-tmp", "checkpoints", ".pytest_cache",
}

MAX_SCAN_BYTES = 2_000_000


def walk_text_files():
    """Yield (Path, relative-posix-str) for scannable files, pruning noisy trees.

    Uses os.walk so skipped directories are never descended into -- some of them
    (a stale node_modules on a Windows mount) raise OSError on stat().
    """
    import os
    for root, dirs, names in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in names:
            p = Path(root) / name
            if p.suffix.lower() not in SCANNABLE:
                continue
            try:
                if p.stat().st_size > MAX_SCAN_BYTES:
                    continue
            except OSError:
                continue
            yield p, str(p.relative_to(REPO)).replace("\\", "/")

AGENT_SECTIONS = [
    ("what-changed", "What changed?",
     "Summarize meaningful development since the previous checkpoint. Group by agent where "
     "attribution exists. Skip noise."),
    ("why-it-matters", "Why does it matter?",
     "Connect the work to specific goals, features, roadmap items, or known problems. Name them."),
    ("north-star", "North Star alignment",
     "One verdict: ALIGNED / NEUTRAL-INFRASTRUCTURAL / QUESTIONABLE / POTENTIAL-DRIFT. "
     "Then why, against GOALS.md's prior question and four criteria."),
    ("spec-discrepancies", "Product-spec discrepancies",
     "Where implementation moved but PRODUCT_SPEC.md did not. Cite file and section."),
    ("complexity", "Complexity / orphan detection",
     "New or existing components that look unused, redundant, overlapping, undocumented, "
     "disconnected from goals, or speculative with no active use case."),
    ("unfinished", "Unfinished work",
     "TODOs, incomplete features, failing tests, abandoned implementation branches."),
    ("next-actions", "Recommended next actions",
     "At most 3, prioritized. Each one sentence. What deserves Vince's attention next."),
]

KNOWN_AGENTS = ["cowork", "hermes", "chatgpt", "vince"]


# ── shell ────────────────────────────────────────────────────────────────────

def git(*args: str, check: bool = False) -> str:
    """Run a git command in the repo, return stdout (stripped). '' on failure."""
    try:
        r = subprocess.run(
            ["git", *args], cwd=REPO, capture_output=True, text=True, timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        if check:
            fail(f"git {' '.join(args)} failed: {e}")
        return ""
    if r.returncode != 0:
        if check:
            fail(f"git {' '.join(args)} failed:\n{r.stderr.strip()}")
        return ""
    return r.stdout.strip()


def fail(msg: str) -> "NoReturn":  # type: ignore[valid-type]
    print(f"CHECKPOINT FAILED: {msg}", file=sys.stderr)
    sys.exit(1)


def have_git_repo() -> bool:
    return (REPO / ".git").exists() and git("rev-parse", "--git-dir") != ""


# ── fact gathering ───────────────────────────────────────────────────────────

def previous_checkpoint(today: str) -> str | None:
    if not CHECKPOINTS.exists():
        return None
    dates = sorted(
        p.stem for p in CHECKPOINTS.glob("*.md")
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", p.stem) and p.stem < today
    )
    return dates[-1] if dates else None


def last_checkpoint_commit() -> str | None:
    """SHA of the most recent checkpoint commit, our diff baseline."""
    sha = git("log", "-1", "--format=%H", "--grep=^checkpoint: daily product alignment")
    return sha or None


def gather_git(today: str) -> dict:
    if not have_git_repo():
        return {"available": False, "reason": "no git repository"}

    base = last_checkpoint_commit()
    rng = f"{base}..HEAD" if base else ""
    log_args = ["log", "--format=%H%x1f%an%x1f%aI%x1f%s%x1f%b%x1e"]
    if rng:
        log_args.append(rng)
    else:
        log_args += ["-50"]

    raw = git(*log_args)
    commits = []
    for rec in raw.split("\x1e"):
        rec = rec.strip("\n")
        if not rec.strip():
            continue
        parts = rec.split("\x1f")
        if len(parts) < 4:
            continue
        sha, author, date, subject = parts[0], parts[1], parts[2], parts[3]
        body = parts[4] if len(parts) > 4 else ""
        m = re.search(r"^Agent:\s*(\S+)", body, re.M | re.I)
        commits.append({
            "sha": sha[:8],
            "author": author,
            "date": date,
            "subject": subject,
            "agent": (m.group(1).lower() if m else None),
        })

    diff_args = ["diff", "--numstat"]
    diff_args.append(f"{base}..HEAD" if base else "--cached")
    files = []
    for line in git(*diff_args).splitlines():
        bits = line.split("\t")
        if len(bits) == 3:
            add, dele, path = bits
            files.append({
                "path": path,
                "added": None if add == "-" else int(add),
                "deleted": None if dele == "-" else int(dele),
            })

    by_agent: dict[str, int] = {}
    for c in commits:
        by_agent[c["agent"] or "UNATTRIBUTED"] = by_agent.get(c["agent"] or "UNATTRIBUTED", 0) + 1

    status = git("status", "--porcelain")
    uncommitted = [l[3:] for l in status.splitlines() if l.strip()]

    # Push is manual (D-014), so unpushed commits are the backup risk to watch.
    remote_url = git("remote", "get-url", "origin") or None
    unpushed = None
    if remote_url:
        n = git("rev-list", "--count", "origin/main..HEAD")
        if not n:  # remote branch not known yet -- nothing has ever been pushed
            n = git("rev-list", "--count", "HEAD")
        unpushed = int(n) if n.isdigit() else None

    return {
        "available": True,
        "unpushed": unpushed,
        "baseline_commit": base,
        "baseline_is_first_run": base is None,
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "remote": git("remote", "get-url", "origin") or None,
        "commits": commits,
        "commit_count": len(commits),
        "commits_by_agent": by_agent,
        "files_changed": files,
        "uncommitted_paths": uncommitted,
        "uncommitted_count": len(uncommitted),
    }


def gather_skills() -> dict:
    """Inventory skills and measure how well each is wired into the index docs."""
    if not SKILLS.is_dir():
        return {"available": False}

    doc_text = {}
    for d in INDEX_DOCS:
        p = REPO / d
        doc_text[d] = p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""

    skill_names = sorted(p.name for p in SKILLS.iterdir() if p.is_dir())
    peer_text = {}
    for n in skill_names:
        sk = SKILLS / n / "SKILL.md"
        peer_text[n] = sk.read_text(encoding="utf-8", errors="replace") if sk.exists() else ""

    out = []
    for n in skill_names:
        d = SKILLS / n
        sk = d / "SKILL.md"
        peers = sum(1 for other, txt in peer_text.items() if other != n and n in txt)
        out.append({
            "name": n,
            "has_skill_md": sk.exists(),
            "bytes": sk.stat().st_size if sk.exists() else 0,
            "scripts": len(list(d.rglob("*.py"))) + len(list(d.rglob("*.sh"))),
            "tests": len(list(d.rglob("test_*.py"))),
            "in_agents": n in doc_text["AGENTS.md"],
            "in_readme": n in doc_text["README.md"],
            "in_user_guide": n in doc_text["USER-GUIDE.md"],
            "peer_refs": peers,
        })

    return {
        "available": True,
        "count": len(out),
        "skills": out,
        "missing_from_agents": [s["name"] for s in out if not s["in_agents"]],
        "missing_from_readme": [s["name"] for s in out if not s["in_readme"]],
        "no_inbound_refs": [
            s["name"] for s in out
            if not s["in_agents"] and not s["in_readme"] and not s["in_user_guide"]
            and s["peer_refs"] == 0
        ],
    }


def gather_docs(git_facts: dict) -> dict:
    """Canonical docs: present? stale relative to code churn?"""
    docs = {}
    for name in CANON + INDEX_DOCS:
        p = REPO / name
        docs[name] = {
            "exists": p.exists(),
            "bytes": p.stat().st_size if p.exists() else 0,
            "last_commit": git("log", "-1", "--format=%aI", "--", name) or None,
        }

    changed = {f["path"] for f in git_facts.get("files_changed", [])}
    code_changed = any(
        c.startswith("skills/") or c.startswith("governance/") for c in changed
    )
    spec_changed = "PRODUCT_SPEC.md" in changed
    docs["_signals"] = {
        "code_changed_this_period": code_changed,
        "product_spec_changed_this_period": spec_changed,
        "spec_may_be_stale": bool(code_changed and not spec_changed),
    }
    return docs


def gather_unfinished() -> dict:
    """TODO/FIXME markers and unresolved review flags across tracked text."""
    marker = re.compile(r"\b(TODO|FIXME|XXX|HACK|NEEDS VINCE|\[OPEN SLOT\])\b")
    hits = []
    for p, rel in walk_text_files():
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            m = marker.search(line)
            if m:
                hits.append({"path": rel, "line": i,
                             "marker": m.group(1), "text": line.strip()[:160]})
    by_marker: dict[str, int] = {}
    for h in hits:
        by_marker[h["marker"]] = by_marker.get(h["marker"], 0) + 1
    return {"count": len(hits), "by_marker": by_marker, "hits": hits[:60]}


def gather_proposals(today: str) -> dict:
    """Parse PROPOSALS.md. Enforces the WIP limit and flags stale entries.

    Expected row: | P-007 | 2026-08-03 | GREEN | open | ... |
    """
    p = REPO / PROPOSALS
    if not p.exists():
        return {"available": False, "open": 0, "over_wip_limit": False, "expired": []}

    text = p.read_text(encoding="utf-8", errors="replace")
    rows = re.findall(
        r"^\|\s*(P-\d+)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*(\w+)\s*\|\s*(\w[\w-]*)\s*\|",
        text, re.M)

    today_d = dt.date.fromisoformat(today)
    open_rows, expired = [], []
    by_status: dict[str, int] = {}
    for pid, raised, tier, status in rows:
        status = status.lower()
        by_status[status] = by_status.get(status, 0) + 1
        if status in ("open", "proposed"):
            age = (today_d - dt.date.fromisoformat(raised)).days
            open_rows.append({"id": pid, "raised": raised, "tier": tier.upper(), "age_days": age})
            if age > PROPOSAL_EXPIRY_DAYS:
                expired.append({"id": pid, "age_days": age})

    return {
        "available": True,
        "total": len(rows),
        "by_status": by_status,
        "open": len(open_rows),
        "open_rows": open_rows,
        "wip_limit": MAX_OPEN_PROPOSALS,
        "over_wip_limit": len(open_rows) > MAX_OPEN_PROPOSALS,
        "expired": expired,
    }


def gather_coherence(skills: dict) -> dict:
    """Architecture health. Cheap, mechanical checks that catch real rot.

    Every finding here is a QUESTION for the agent, never a verdict -- these
    are heuristics, and a hit is not automatically a defect.
    """
    findings: dict[str, list] = {
        "oversized_skills": [], "scripts_without_tests": [],
        "broken_doc_refs": [], "stale_skill_counts": [], "no_inbound_refs": [],
    }
    if not skills.get("available"):
        return findings

    actual = skills["count"]
    findings["no_inbound_refs"] = skills["no_inbound_refs"]

    for s in skills["skills"]:
        if s["bytes"] > SKILL_SIZE_WARN_BYTES:
            findings["oversized_skills"].append({"name": s["name"], "bytes": s["bytes"]})
        if s["scripts"] > 0 and s["tests"] == 0:
            findings["scripts_without_tests"].append(
                {"name": s["name"], "scripts": s["scripts"]})

    # "N skills" claims in prose that no longer match reality -- this is the
    # exact bug that left HANDOFF.md asserting 17 skills when there were 21.
    for doc in CANON + INDEX_DOCS + ["HANDOFF.md"]:
        dp = REPO / doc
        if not dp.exists():
            continue
        text = dp.read_text(encoding="utf-8", errors="replace")
        # A doc that *reports* a stale count ("says 17, actual 21") is doing its
        # job, not drifting. Only flag lines that ASSERT the number.
        quoting = re.compile(
            r"\b(says|claims|stale|actual|superseded|historical|there are|→)\b", re.I)
        for line in text.splitlines():
            if quoting.search(line):
                continue
            for m in re.finditer(r"\b(\d{1,3})\s+(?:hearthlight-\*\s+)?skills\b", line, re.I):
                claimed = int(m.group(1))
                if claimed != actual and 3 <= claimed <= 99:
                    findings["stale_skill_counts"].append(
                        {"doc": doc, "claims": claimed, "actual": actual})

        # References to skills/<name> that do not exist on disk.
        for m in re.finditer(r"skills/(hearthlight-[a-z-]+)", text):
            if not (SKILLS / m.group(1)).is_dir():
                findings["broken_doc_refs"].append({"doc": doc, "ref": m.group(1)})

    for k in ("stale_skill_counts", "broken_doc_refs"):
        seen, uniq = set(), []
        for item in findings[k]:
            key = tuple(sorted(item.items()))
            if key not in seen:
                seen.add(key)
                uniq.append(item)
        findings[k] = uniq

    return findings


def scan_secrets() -> list[dict]:
    """Pre-commit secret sweep. Returns findings; empty list means clean."""
    findings = []
    for p, rel in walk_text_files():
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for token in re.findall(r"[A-Fa-f0-9]{32}", text):
            if hashlib.sha256(token.lower().encode()).hexdigest() == LEAKED_KEY_SHA256:
                findings.append({"path": rel, "kind": "known leaked key"})
                break
        for pat, kind in SECRET_PATTERNS:
            if pat.search(text):
                findings.append({"path": rel, "kind": kind})
                break
    return findings


def gather_tests() -> dict:
    """Locate test files and report whether a runner is available."""
    tests = sorted(rel for p, rel in walk_text_files()
                   if p.name.startswith("test_") and p.suffix == ".py")
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", "--version"],
                           cwd=REPO, capture_output=True, text=True, timeout=60)
        runner = r.returncode == 0
        version = r.stdout.strip().splitlines()[0] if runner and r.stdout.strip() else None
    except (OSError, subprocess.TimeoutExpired):
        runner, version = False, None

    result = {"files": tests, "count": len(tests),
              "runner_available": runner, "runner_version": version,
              "passed": None, "output": None}

    if runner and tests:
        try:
            r = subprocess.run([sys.executable, "-m", "pytest", "-q", *tests],
                               cwd=REPO, capture_output=True, text=True, timeout=600)
            result["passed"] = r.returncode == 0
            result["output"] = (r.stdout + r.stderr).strip()[-2000:]
        except (OSError, subprocess.TimeoutExpired) as e:
            result["passed"] = False
            result["output"] = f"test run error: {e}"
    return result


# ── skeleton ─────────────────────────────────────────────────────────────────

def render_skeleton(today: str, facts: dict) -> str:
    g = facts["git"]
    s = facts["skills"]
    prev = facts["previous_checkpoint"]

    L = [
        f"# Checkpoint — {today}",
        "",
        f"*Previous checkpoint: {prev or 'none (first run)'}*  ",
        f"*Baseline commit: {g.get('baseline_commit') or 'repository start'}*",
        "",
        "---",
        "",
    ]

    for key, title, hint in AGENT_SECTIONS:
        L += [f"## {title}", "",
              f"<!-- AGENT:{key} — {hint} -->", "", "_(not yet written)_", ""]

    L += ["---", "", "## Mechanical facts", "",
          "<!-- Generated by governance/checkpoint.py. Do not hand-edit. -->", ""]

    if not g.get("available"):
        L.append(f"- Git: unavailable ({g.get('reason')})")
    else:
        L += [
            f"- Branch `{g['branch']}` · remote: {g['remote'] or '**none configured**'}",
            f"- Commits since baseline: **{g['commit_count']}**",
            f"- Files changed: **{len(g['files_changed'])}**",
            f"- Uncommitted paths: **{g['uncommitted_count']}**",
        ]
        n = g.get("unpushed")
        if n:
            warn = " ⚠ **nothing is backed up — push from Windows**" if n >= 5 else ""
            L.append(f"- Unpushed commits: **{n}**{warn}")
        if g["commits_by_agent"]:
            parts = ", ".join(f"{k}: {v}" for k, v in sorted(g["commits_by_agent"].items()))
            L.append(f"- By agent — {parts}")
        if g["commits"]:
            L += ["", "<details><summary>Commits</summary>", ""]
            for c in g["commits"][:40]:
                L.append(f"- `{c['sha']}` [{c['agent'] or 'unattributed'}] {c['subject']}")
            L += ["", "</details>"]

    if s.get("available"):
        L += ["", f"- Skills: **{s['count']}**"]
        if s["missing_from_agents"]:
            L.append(f"- ⚠ Absent from `AGENTS.md`: {', '.join(s['missing_from_agents'])}")
        if s["missing_from_readme"]:
            L.append(f"- ⚠ Absent from `README.md`: {', '.join(s['missing_from_readme'])}")
        if s["no_inbound_refs"]:
            L.append(f"- ⚠ **No inbound references at all**: {', '.join(s['no_inbound_refs'])}")

    d = facts["docs"]["_signals"]
    if d["spec_may_be_stale"]:
        L.append("- ⚠ Code changed this period but `PRODUCT_SPEC.md` did not.")

    u = facts["unfinished"]
    if u["count"]:
        L.append(f"- Unfinished markers: **{u['count']}** "
                 f"({', '.join(f'{k}×{v}' for k, v in sorted(u['by_marker'].items()))})")

    pr = facts.get("proposals", {})
    if pr.get("available"):
        L.append(f"- Proposals open: **{pr['open']}/{pr['wip_limit']}**"
                 + (" ⚠ **OVER LIMIT**" if pr["over_wip_limit"] else ""))
        if pr["expired"]:
            ids = ", ".join(x["id"] for x in pr["expired"])
            L.append(f"- ⚠ Proposals past {PROPOSAL_EXPIRY_DAYS}d with no decision: {ids}")

    co = facts.get("coherence", {})
    for label, key in (("Stale skill counts", "stale_skill_counts"),
                       ("Broken skill refs", "broken_doc_refs")):
        if co.get(key):
            bits = ", ".join(
                f"{i.get('doc')}→{i.get('ref') or i.get('claims')}" for i in co[key][:5])
            L.append(f"- ⚠ {label}: {bits}")

    t = facts["tests"]
    if t["count"]:
        if t["passed"] is True:
            verdict = "passing"
        elif t["passed"] is False:
            verdict = "**FAILING**"
        else:
            verdict = "not run (no runner)"
        L.append(f"- Tests: {t['count']} file(s), {verdict}")

    sec = facts["secrets"]
    L.append(f"- Secret scan: {'clean' if not sec else f'**{len(sec)} finding(s)**'}")

    L += ["", f"*Facts: `checkpoints/.facts-{today}.json`*", ""]
    return "\n".join(L)


# ── commands ─────────────────────────────────────────────────────────────────

def cmd_gather(args) -> int:
    today = args.date or dt.date.today().isoformat()
    CHECKPOINTS.mkdir(exist_ok=True)

    print(f"[gather] {today}")
    git_facts = gather_git(today)
    skills = gather_skills()
    facts = {
        "date": today,
        "generated_at": dt.datetime.now().astimezone().isoformat(),
        "previous_checkpoint": previous_checkpoint(today),
        "git": git_facts,
        "skills": skills,
        "docs": gather_docs(git_facts),
        "unfinished": gather_unfinished(),
        "tests": gather_tests(),
        "proposals": gather_proposals(today),
        "coherence": gather_coherence(skills),
        "secrets": scan_secrets(),
    }

    missing = [d for d in CANON if not (REPO / d).exists()]
    if missing:
        fail(f"canonical documents missing: {', '.join(missing)}")

    (CHECKPOINTS / f".facts-{today}.json").write_text(
        json.dumps(facts, indent=2), encoding="utf-8")

    md = CHECKPOINTS / f"{today}.md"
    if md.exists():
        existing = md.read_text(encoding="utf-8", errors="replace")
        written = not any(f"<!-- AGENT:{k}" in existing for k, _, _ in AGENT_SECTIONS)
        if written:
            # --force must never destroy a finished checkpoint. Losing a day's
            # written judgment to a stray flag is unacceptable; a stale facts
            # block is not.
            print(f"[gather] {md.name} is already written — refusing to overwrite.")
            print("[gather] delete it by hand first if you really mean to redo it.")
        elif args.force:
            md.write_text(render_skeleton(today, facts), encoding="utf-8")
            print(f"[gather] rewrote {md.name} (was an unfilled skeleton)")
        else:
            print(f"[gather] {md.name} exists; leaving it alone (--force to rewrite)")
    else:
        md.write_text(render_skeleton(today, facts), encoding="utf-8")
        print(f"[gather] wrote {md.name}")

    print(f"[gather] commits={git_facts.get('commit_count', 0)} "
          f"skills={facts['skills'].get('count', 0)} "
          f"todos={facts['unfinished']['count']} "
          f"secrets={len(facts['secrets'])}")
    if facts["secrets"]:
        print("[gather] WARNING — secret scan findings:")
        for f in facts["secrets"]:
            print(f"           {f['path']}: {f['kind']}")
    return 0


WORKSHOP_SECTIONS = [
    ("pattern", "The week's pattern",
     "What the last 7 checkpoints show TOGETHER that no single day showed. Direction of travel."),
    ("v1-progress", "Distance to v1",
     "Where the Yu-Gi-Oh! film and the pipeline actually are against GOALS.md's v1 definition. "
     "What moved, what did not, what is now the binding constraint."),
    ("coherence", "Architecture coherence",
     "Read the mechanical findings below as questions, not verdicts. Duplication, rot, "
     "components with no v1 justification, accumulating debt."),
    ("proposals", "New proposals",
     "Ideas generated this week. Each names the v1 blocker it removes, or it is parked. "
     "Respect the WIP limit -- a new idea must displace a worse one, not just be added."),
    ("pruning", "Pruning candidates",
     "What should go. Never delete -- surface with the evidence and let Vince decide."),
    ("ask", "What needs Vince",
     "Amber proposals awaiting approval, and any unanswered NEEDS VINCE marker over a week old."),
]


def iso_week(today: str) -> str:
    d = dt.date.fromisoformat(today)
    y, w, _ = d.isocalendar()
    return f"{y}-W{w:02d}"


def render_workshop(today: str, facts: dict) -> str:
    co = facts["coherence"]
    pr = facts["proposals"]
    L = [f"# Weekly workshop — {iso_week(today)}", "",
         f"*Generated {today}. Improvement pass: read the week, audit coherence, propose.*", "",
         "---", ""]

    for key, title, hint in WORKSHOP_SECTIONS:
        L += [f"## {title}", "", f"<!-- AGENT:{key} — {hint} -->", "", "_(not yet written)_", ""]

    L += ["---", "", "## Mechanical findings", "",
          "<!-- Generated by governance/checkpoint.py. Heuristics, not verdicts. -->", ""]

    if pr.get("available"):
        L.append(f"- Proposals: **{pr['open']} open** of {pr['wip_limit']} allowed"
                 + (" — ⚠ **OVER LIMIT, prune before adding**" if pr["over_wip_limit"] else ""))
        for x in pr["expired"]:
            L.append(f"  - ⚠ `{x['id']}` open {x['age_days']}d with no decision — expire or escalate")
    else:
        L.append("- `PROPOSALS.md` not found — first workshop run?")

    if co["no_inbound_refs"]:
        L.append(f"- **No inbound references**: {', '.join(co['no_inbound_refs'])}")
    if co["oversized_skills"]:
        bits = ", ".join(f"{i['name']} ({i['bytes'] // 1000}KB)" for i in co["oversized_skills"])
        L.append(f"- Large SKILL.md (split/merge candidates): {bits}")
    if co["scripts_without_tests"]:
        bits = ", ".join(f"{i['name']} ({i['scripts']})" for i in co["scripts_without_tests"])
        L.append(f"- Scripts with no test: {bits}")
    if co["stale_skill_counts"]:
        bits = ", ".join(f"{i['doc']} says {i['claims']}, actual {i['actual']}"
                         for i in co["stale_skill_counts"])
        L.append(f"- ⚠ Stale skill counts: {bits}")
    if co["broken_doc_refs"]:
        bits = ", ".join(f"{i['doc']}→{i['ref']}" for i in co["broken_doc_refs"])
        L.append(f"- ⚠ References to skills that do not exist: {bits}")

    g = facts["git"]
    if g.get("available"):
        L.append(f"- Commits in window: {g['commit_count']} "
                 f"({', '.join(f'{k}: {v}' for k, v in sorted(g['commits_by_agent'].items())) or 'none'})")

    L += ["", f"*Facts: `checkpoints/.facts-{today}.json`*", ""]
    return "\n".join(L)


def cmd_workshop(args) -> int:
    """Weekly improvement pass. Same facts, different questions."""
    today = args.date or dt.date.today().isoformat()
    CHECKPOINTS.mkdir(exist_ok=True)
    print(f"[workshop] {iso_week(today)}")

    git_facts = gather_git(today)
    skills = gather_skills()
    facts = {
        "date": today, "kind": "workshop", "week": iso_week(today),
        "generated_at": dt.datetime.now().astimezone().isoformat(),
        "git": git_facts, "skills": skills,
        "proposals": gather_proposals(today),
        "coherence": gather_coherence(skills),
        "unfinished": gather_unfinished(),
        "tests": gather_tests(), "secrets": scan_secrets(),
    }
    (CHECKPOINTS / f".facts-{today}.json").write_text(
        json.dumps(facts, indent=2), encoding="utf-8")

    out = CHECKPOINTS / f"weekly-{iso_week(today)}.md"
    if out.exists() and not args.force:
        print(f"[workshop] {out.name} exists; leaving it (use --force)")
    else:
        out.write_text(render_workshop(today, facts), encoding="utf-8")
        print(f"[workshop] wrote {out.name}")

    pr = facts["proposals"]
    print(f"[workshop] proposals open={pr.get('open', 0)}/{MAX_OPEN_PROPOSALS} "
          f"expired={len(pr.get('expired', []))} "
          f"no-inbound-refs={len(facts['coherence']['no_inbound_refs'])}")
    return 0


def cmd_commit(args) -> int:
    today = args.date or dt.date.today().isoformat()
    if args.weekly:
        md = CHECKPOINTS / f"weekly-{iso_week(today)}.md"
        sections = WORKSHOP_SECTIONS
        label = f"weekly workshop {iso_week(today)}"
    else:
        md = CHECKPOINTS / f"{today}.md"
        sections = AGENT_SECTIONS
        label = f"daily product alignment {today}"

    if not md.exists():
        fail(f"{md.name} does not exist — run `gather`/`workshop` first")
    text = md.read_text(encoding="utf-8")

    # Refuse to commit an unfilled skeleton. This is the guard that keeps a
    # failed run from producing a committed artifact.
    unfilled = [k for k, _, _ in sections if f"<!-- AGENT:{k}" in text]
    if unfilled:
        fail("checkpoint still has unfilled agent sections: " + ", ".join(unfilled))
    if "_(not yet written)_" in text:
        fail("checkpoint still contains '_(not yet written)_' placeholders")

    findings = scan_secrets()
    if findings:
        for f in findings:
            print(f"  {f['path']}: {f['kind']}", file=sys.stderr)
        fail(f"secret scan found {len(findings)} issue(s) — refusing to commit")

    # Canon hygiene (D-017): front matter valid, no history narration in the core docs.
    canon = subprocess.run([sys.executable, str(REPO / "governance" / "canon.py"), "check"],
                           capture_output=True, text=True)
    if canon.returncode:
        print(canon.stderr or canon.stdout, file=sys.stderr)
        fail("canon check failed — history belongs in archive/ (governance/CANON-RULES.md)")

    if not have_git_repo():
        fail("no git repository")

    tests = gather_tests()
    if tests["passed"] is False and not args.skip_tests:
        print(tests["output"] or "", file=sys.stderr)
        fail("tests are failing — refusing to commit (override with --skip-tests)")

    # Stage the checkpoint and the docs that are safe to automate.
    # GOALS.md is deliberately NOT in this list and must never be added.
    safe = [str(md.relative_to(REPO)).replace("\\", "/"),
            "PRODUCT_SPEC.md", "ROADMAP.md", "DECISIONS.md", "SKILL-INVENTORY.md",
            PROPOSALS, "AGENTS.md", "README.md", "governance", "archive"]
    for path in safe:
        if (REPO / path).exists():
            git("add", "--", path)

    staged = git("diff", "--cached", "--name-only").splitlines()
    if not staged:
        print("[commit] nothing staged — already up to date")
        return 0
    if "GOALS.md" in staged:
        fail("GOALS.md is staged — it is human-owned and must never be auto-committed")

    msg = (f"checkpoint: {label}\n\n"
           f"Generated by governance/checkpoint.py.\n\n"
           f"Agent: {args.agent}\n")
    r = subprocess.run(["git", "commit", "-m", msg], cwd=REPO,
                       capture_output=True, text=True)
    if r.returncode != 0:
        fail(f"git commit failed:\n{r.stderr.strip()}")
    print(f"[commit] committed — {label}")

    # Push is OPT-IN by Vince's decision (2026-08-03): the sandbox holds no
    # GitHub credentials and is ephemeral, so he pushes from Windows himself.
    if not args.push:
        ahead = git("rev-list", "--count", "@{u}..HEAD") or "?"
        print(f"[commit] not pushing (default). {ahead} commit(s) waiting locally.")
        print("[commit] push from Windows when ready:  git push origin main")
        return 0

    remote = git("remote", "get-url", "origin")
    if not remote:
        print("[commit] no remote 'origin' configured — commit is local only.")
        print("[commit] add one with: git remote add origin <url>")
        return 0

    branch = git("rev-parse", "--abbrev-ref", "HEAD") or "main"
    r = subprocess.run(["git", "push", "-u", "origin", branch], cwd=REPO,
                       capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        print(f"[commit] PUSH FAILED (commit is safe locally):\n{r.stderr.strip()}",
              file=sys.stderr)
        return 2
    print(f"[commit] pushed to {remote} ({branch})")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Hearthlight daily alignment checkpoint")
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("gather", help="collect facts + write the skeleton")
    g.add_argument("--date", help="YYYY-MM-DD (default: today)")
    g.add_argument("--force", action="store_true", help="overwrite an existing checkpoint")
    g.set_defaults(func=cmd_gather)

    w = sub.add_parser("workshop", help="weekly improvement pass: audit + propose")
    w.add_argument("--date", help="YYYY-MM-DD (default: today)")
    w.add_argument("--force", action="store_true", help="overwrite an existing workshop")
    w.set_defaults(func=cmd_workshop)

    c = sub.add_parser("commit", help="validate, commit, optionally push")
    c.add_argument("--date", help="YYYY-MM-DD (default: today)")
    c.add_argument("--agent", default="cowork", choices=KNOWN_AGENTS,
                   help="which agent is committing")
    c.add_argument("--weekly", action="store_true",
                   help="commit the weekly workshop instead of the daily checkpoint")
    c.add_argument("--push", action="store_true",
                   help="also push (off by default; Vince pushes from Windows)")
    c.add_argument("--skip-tests", action="store_true")
    c.set_defaults(func=cmd_commit)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
