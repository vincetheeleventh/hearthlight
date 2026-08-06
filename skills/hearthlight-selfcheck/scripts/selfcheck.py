#!/usr/bin/env python3
"""
Hearthlight self-check — verify the PLUMBING (mechanical health), not the art.
Returns a green/red checklist so Vince knows what's wired vs broken in ONE command.

It deliberately does NOT judge quality — taste is Vince's job and always will be.
This catches: missing skills, broken scripts, absent keys, unblessed style block,
unreachable paths. The stuff that fails SILENTLY otherwise.

USAGE (WSL):
  python3 selfcheck.py                      # full check, human-readable
  python3 selfcheck.py --project mcconaughey-call   # also check that project's readiness

Exit code 0 = all green, 1 = at least one RED (hard failure).
"""
import os, sys, subprocess, glob, re, shutil

# Derive paths robustly. NOTE: under the gateway, $HOME is overridden to the
# profile's home/ subdir, so os.path.expanduser("~") points at a nonexistent
# tree. Anchor STUDIO to this script's own location instead (it lives at
# <STUDIO>/skills/hearthlight-selfcheck/scripts/selfcheck.py), and resolve the
# profile dir from HERMES_HOME (set by the gateway) with sane fallbacks.
_HERE = os.path.dirname(os.path.abspath(__file__))
STUDIO = os.path.normpath(os.path.join(_HERE, "..", "..", ".."))
# This is the HEARTHLIGHT selfcheck, so always target the hearthlight profile.
# Honor HERMES_HOME only when it already points at hearthlight (the gateway sets it
# that way). In a standalone shell HERMES_HOME may be the hermes ROOT / default
# profile — in that case derive the hearthlight profile from this script's location,
# or we'd silently check the wrong profile (empty external_dirs → phantom RED).
_hh = os.environ.get("HERMES_HOME", "").replace("\\", "/").rstrip("/")
PROFILE = (os.environ["HERMES_HOME"] if _hh.endswith("hearthlight")
           else os.path.join(os.path.dirname(STUDIO), "profiles", "hearthlight"))

GREEN, RED, WARN = "OK  ", "FAIL", "WARN"
results = []
def check(label, status, detail=""):
    results.append((status, label, detail))

# ── 1. Skills present on disk ────────────────────────────────────
EXPECTED_SKILLS = [
    "conventions","distribution-spec","consolidate","outline","critique","research","character",
    "reference-report","mise-en-scene","shot-crew","clip-extractor","timing-intake",
    "image-prompts","storyboard","video-prompts","comfyui-graph","notion-log","selfcheck",
    "dashboard","shot-runner","terse","acting","asset-sheets",
]
skills_dir = os.path.join(STUDIO, "skills")
present = set()
for d in glob.glob(os.path.join(skills_dir, "hearthlight-*")):
    sk = os.path.join(d, "SKILL.md")
    name = os.path.basename(d).replace("hearthlight-","")
    if os.path.isfile(sk):
        # has frontmatter name?
        head = open(sk, encoding="utf-8", errors="replace").read(400)
        if re.search(r'^name:\s*hearthlight-', head, re.M):
            present.add(name)
        else:
            check(f"skill {name}: SKILL.md has no frontmatter name (won't load)", WARN)
for want in EXPECTED_SKILLS:
    check(f"skill present: hearthlight-{want}", GREEN if want in present else RED,
          "" if want in present else "missing or unnamed")
# stray tombstones
for d in glob.glob(os.path.join(skills_dir, "hearthlight-*")):
    if os.path.basename(d).replace("hearthlight-","") not in EXPECTED_SKILLS:
        check(f"unexpected skill folder: {os.path.basename(d)} (tombstone? delete it)", WARN)

# ── 2. Scripts execute ───────────────────────────────────────────
def runnable(path, args):
    if not os.path.isfile(path):
        return RED, "script missing"
    try:
        r = subprocess.run([sys.executable, path] + args, capture_output=True, timeout=20, text=True)
        # we expect a usage/help or clean exit, not a Python traceback
        if "Traceback" in r.stderr:
            return RED, r.stderr.strip().splitlines()[-1][:120]
        return GREEN, ""
    except Exception as e:
        return RED, str(e)[:120]

for label, rel, args in [
    ("timing.py runs",      "skills/hearthlight-timing-intake/scripts/timing.py", []),
    ("build_timeline.py runs","skills/hearthlight-timing-intake/scripts/build_timeline.py", []),
    ("clip extract.sh present","skills/hearthlight-clip-extractor/scripts/extract.sh", None),
    ("image_pass.py runs", "skills/hearthlight-image-prompts/scripts/image_pass.py", ["--help"]),
]:
    p = os.path.join(STUDIO, rel)
    if args is None:
        check(label, GREEN if os.path.isfile(p) else RED, "" if os.path.isfile(p) else "missing")
    else:
        st, dt = runnable(p, args); check(label, st, dt)

# ── 3. Tools available (shutil.which is cross-platform; `which` is Linux-only) ─
for tool in ["ffmpeg", "ffprobe"]:
    ok = shutil.which(tool) is not None
    check(f"tool available: {tool}", GREEN if ok else WARN,
          "" if ok else "not on PATH — needed for clip/audio extraction (Stage 4.5)")
check("tool available: python", GREEN)  # we're running under it

# ── 4. Secrets / config (presence only — never print values) ─────
env = os.path.join(PROFILE, ".env")
if os.path.isfile(env):
    txt = open(env, errors="replace").read()
    for key, why in [("TELEGRAM","Telegram bot"), ("NOTION","Notion logging"),
                     ("OPENAI","image gen"), ("RUNNINGHUB","video gen")]:
        has = bool(re.search(key, txt, re.I))
        check(f"key present: {key} ({why})", GREEN if has else WARN,
              "" if has else "absent — that feature won't work")
else:
    check(".env present in hearthlight profile", RED, "no .env — gateway/keys unconfigured")

# config.yaml: external_dirs + cwd + mcp
cfg = os.path.join(PROFILE, "config.yaml")
if os.path.isfile(cfg):
    c = open(cfg, errors="replace").read()
    check("config: skills.external_dirs points at Story Studio",
          GREEN if "Story Studio/skills" in c else RED)
    check("config: skill directories include local and installed skills",
          GREEN if "Story Studio/skills" in c and "Story Studio/.agents/skills" in c else RED,
          "" if "Story Studio/.agents/skills" in c else "installed Krea skills directory is not loaded")
    krea_block = re.search(r"(?ms)^  krea-ai:\s*\n(?P<body>.*?)(?=^  [\w-]+:\s*$|\Z)", c)
    krea_body = krea_block.group("body") if krea_block else ""
    required_krea = ["list_models", "get_model_schema", "generate_image", "get_upload_url", "get_job", "list_moodboards"]
    krea_missing = [tool for tool in required_krea if tool not in krea_body]
    check("config: Krea MCP OAuth block and safe image tools present",
          GREEN if krea_block and "auth: oauth" in krea_body and not krea_missing else RED,
          "" if krea_block and not krea_missing else "missing Krea OAuth block or tools: " + ", ".join(krea_missing))
    check("config: Notion MCP server block present",
          GREEN if re.search(r'mcp_servers:.*notion', c, re.S) else WARN,
          "" if "notion" in c else "Notion MCP not configured yet")
else:
    check("config.yaml present", RED)

# ── 5. Project readiness (optional) ──────────────────────────────
proj = None
if "--project" in sys.argv:
    proj = sys.argv[sys.argv.index("--project")+1]
    pdir = os.path.join(STUDIO, "projects", proj)
    if not os.path.isdir(pdir):
        check(f"project {proj}: folder exists", RED)
    else:
        # style block blessed? (mise-en-scene draft marker blocks generation)
        mes = glob.glob(os.path.join(pdir, "03-bible", "mise-en-scene.md"))
        if mes:
            t = open(mes[0], errors="replace").read()
            header = t[:1000].upper()
            blessed = ("CANON" in header or "LOCKED" in header) and not re.search(r"(?m)^\s*(?:>\s*)?\*\*DRAFT\b", header)
            check(f"project {proj}: style block blessed (gen unblocked)",
                  GREEN if blessed else WARN, "" if blessed else "style block still DRAFT — no images until blessed")
        else:
            check(f"project {proj}: mise-en-scene.md exists", WARN, "not built yet")
        check(f"project {proj}: distribution-spec.md exists",
              GREEN if os.path.isfile(os.path.join(pdir,"distribution-spec.md")) else WARN)
        check(f"project {proj}: 00-source has material",
              GREEN if os.listdir(os.path.join(pdir,"00-source")) else WARN)
        compiler = os.path.join(STUDIO, "skills", "hearthlight-image-prompts", "scripts", "krea_style_comp.py")
        assets = os.path.join(pdir, "03-bible", "assets.json")
        if os.path.isfile(assets) and os.path.isfile(compiler):
            r = subprocess.run([sys.executable, compiler, "--project", proj, "--all", "--check-only"],
                               capture_output=True, text=True, timeout=20)
            try:
                import json
                readiness = json.loads(r.stdout)
                ready = r.returncode == 0 and readiness.get("generation_count", 0) > 0
                detail = (f"{readiness.get('generation_count', 0)} unique prompts; "
                          f"{len(readiness.get('shared_setups', []))} shared; "
                          f"{len(readiness.get('source_only', []))} source-only")
                check(f"project {proj}: Krea style/composition prompt readiness",
                      GREEN if ready else WARN, detail)
            except Exception:
                detail = (r.stderr or r.stdout or "preflight did not return valid JSON")[:500]
                check(f"project {proj}: Krea style/composition prompt readiness", RED, detail)

# ── Report ───────────────────────────────────────────────────────
order = {RED:0, WARN:1, GREEN:2}
results.sort(key=lambda r: order[r[0]])
reds = sum(1 for s,_,_ in results if s==RED)
warns = sum(1 for s,_,_ in results if s==WARN)
print("\n=== Hearthlight self-check (PLUMBING only — not quality) ===\n")
for status, label, detail in results:
    print(f"  [{status}] {label}" + (f"  — {detail}" if detail else ""))
print(f"\n  {reds} RED (hard failures), {warns} WARN (feature-not-ready), "
      f"{len(results)-reds-warns} OK")
print("\n  NOTE: this checks WIRING, not the work. Whether a shot is *good* is Vince's call —\n"
      "  no self-check can validate taste. Green here = the machine is ready, not that the art is right.\n")
sys.exit(1 if reds else 0)
