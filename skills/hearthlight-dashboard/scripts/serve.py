#!/usr/bin/env python3
"""Hearthlight cockpit server — stdlib only.

GET  /                → index.html
GET  /status.json     → full rescan (refresh = truth)
POST /api/upload      → save a dropped file  (?project=&zone=&name=&sub=)
POST /api/note        → save a typed rant/idea  {project, kind, text}
POST /api/new-project → scaffold a project  {slug}

Boundary: NO gate approvals here. Gates live in Telegram; the ledger
(status.yml) is written by the agent, never by this server.

Run:  python serve.py [port]     (default 8787)
"""
import http.server, json, os, re, sys, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scan as scanner

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STUDIO_ROOT = os.path.dirname(os.path.dirname(SKILL_DIR))
PROJECTS_DIR = os.path.join(STUDIO_ROOT, "projects")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8787

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,40}$")
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,40}$")

SCAFFOLD = ["00-source/audio", "01-intake/clips", "02-outline",
            "03-bible/refs/storyboard-panels", "03-bible/refs/environments",
            "03-bible/refs/props", "03-bible/characters",
            "04-images", "05-storyboard", "06-video", "07-final"]

LEDGER_TEMPLATE = """# Hearthlight gate ledger — the durable record of Vince's ✅s.
# States: approved YYYY-MM-DD | pending | unconfirmed | done | n/a
project: {slug}

distribution_spec: pending
gate0_vision: pending
gate1_outline: pending
critique: pending
gate2_mise_en_scene: pending
clip_prep: pending
gate3_images: pending
gate4_storyboard: pending
gate5_video: pending
final_edit: pending
"""


def load_zones():
    with open(os.path.join(SKILL_DIR, "intake.json"), encoding="utf-8") as f:
        return {z["id"]: z for z in json.load(f)["zones"]}


def safe_filename(name):
    name = os.path.basename(name.replace("\\", "/")).strip()
    name = re.sub(r"[^\w.\- ()\[\]']", "_", name)
    if not name or name.startswith("."):
        return None
    return name


def unique_path(folder, filename):
    """Never overwrite — conventions say versions, not overwrites."""
    base, ext = os.path.splitext(filename)
    p, n = os.path.join(folder, filename), 2
    while os.path.exists(p):
        p = os.path.join(folder, f"{base}-v{n}{ext}")
        n += 1
    return p


class Handler(http.server.BaseHTTPRequestHandler):
    # -------- GET --------
    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/status.json":
            self._json(200, scanner.scan())
        elif path in ("/", "/index.html"):
            with open(os.path.join(SKILL_DIR, "index.html"), "rb") as f:
                self._send(200, "text/html; charset=utf-8", f.read())
        else:
            self._send(404, "text/plain", b"not found")

    # -------- POST --------
    def do_POST(self):
        path, _, query = self.path.partition("?")
        try:
            if path == "/api/upload":
                self._upload(dict(p.split("=", 1) for p in query.split("&") if "=" in p))
            elif path == "/api/note":
                self._note(self._read_json())
            elif path == "/api/new-project":
                self._new_project(self._read_json())
            else:
                self._json(404, {"error": "unknown endpoint"})
        except Exception as e:
            self._json(500, {"error": str(e)})

    def _upload(self, q):
        from urllib.parse import unquote
        slug = unquote(q.get("project", ""))
        zone_id = unquote(q.get("zone", ""))
        fname = safe_filename(unquote(q.get("name", "")))
        sub = unquote(q.get("sub", "")).strip().lower().replace(" ", "-")
        zones = load_zones()
        proj_dir = os.path.join(PROJECTS_DIR, slug)
        if not SLUG_RE.match(slug) or not os.path.isdir(proj_dir):
            return self._json(400, {"error": "unknown project"})
        if zone_id not in zones or not fname:
            return self._json(400, {"error": "bad zone or filename"})
        zone = zones[zone_id]
        target = os.path.join(proj_dir, zone["target"].replace("/", os.sep))
        if zone.get("named"):
            if not NAME_RE.match(sub):
                return self._json(400, {"error": f"need a valid {zone.get('name_label','name')}"})
            target = os.path.join(target, sub)
        os.makedirs(target, exist_ok=True)
        dest = unique_path(target, fname)
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0:
            return self._json(400, {"error": "empty body"})
        with open(dest, "wb") as f:
            remaining = length
            while remaining > 0:
                chunk = self.rfile.read(min(1024 * 1024, remaining))
                if not chunk:
                    break
                f.write(chunk)
                remaining -= len(chunk)
        rel = os.path.relpath(dest, proj_dir).replace(os.sep, "/")
        self._json(200, {"saved": rel})

    def _note(self, body):
        slug, kind = body.get("project", ""), body.get("kind", "")
        text = (body.get("text") or "").strip()
        proj_dir = os.path.join(PROJECTS_DIR, slug)
        if not SLUG_RE.match(slug) or not os.path.isdir(proj_dir):
            return self._json(400, {"error": "unknown project"})
        if kind not in ("rant", "idea") or not text:
            return self._json(400, {"error": "kind must be rant|idea, text required"})
        intake = os.path.join(proj_dir, "01-intake")
        os.makedirs(intake, exist_ok=True)
        now = datetime.datetime.now()
        stamp = now.strftime("%Y-%m-%d %H:%M")
        if kind == "rant":
            dest = unique_path(intake, f"rant-typed-{now.strftime('%Y%m%d-%H%M')}.md")
            with open(dest, "w", encoding="utf-8") as f:
                f.write(f"# Rant (typed via cockpit) — {stamp}\n\n"
                        f"> Raw, unedited. Treat like a voice-note transcript.\n\n{text}\n")
        else:
            dest = os.path.join(intake, "ideas-inbox.md")
            new = not os.path.exists(dest)
            with open(dest, "a", encoding="utf-8") as f:
                if new:
                    f.write("# Ideas Inbox (typed via cockpit)\n\n"
                            "Loose ideas awaiting the ideation loop. Take / park / no.\n")
                f.write(f"\n---\n**{stamp}**\n\n{text}\n")
        rel = os.path.relpath(dest, proj_dir).replace(os.sep, "/")
        self._json(200, {"saved": rel})

    def _new_project(self, body):
        slug = (body.get("slug") or "").strip().lower().replace(" ", "-")
        if not SLUG_RE.match(slug):
            return self._json(400, {"error": "slug: lowercase, hyphens, 2-41 chars"})
        proj_dir = os.path.join(PROJECTS_DIR, slug)
        if os.path.exists(proj_dir):
            return self._json(400, {"error": "project already exists"})
        for d in SCAFFOLD:
            os.makedirs(os.path.join(proj_dir, d.replace("/", os.sep)), exist_ok=True)
        with open(os.path.join(proj_dir, "status.yml"), "w", encoding="utf-8") as f:
            f.write(LEDGER_TEMPLATE.format(slug=slug))
        with open(os.path.join(proj_dir, "AGENTS.md"), "w", encoding="utf-8") as f:
            f.write(f"# {slug} — project context\n\n"
                    "New Hearthlight project (scaffolded via cockpit).\n"
                    "FIRST: lock the distribution spec (`hearthlight-distribution-spec`) — "
                    "aspect ratio is a composition law.\n"
                    "Conventions: `hearthlight-conventions`. Gate ledger: `status.yml`.\n")
        self._json(200, {"created": slug})

    # -------- plumbing --------
    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length) or b"{}")

    def _json(self, code, obj):
        self._send(code, "application/json; charset=utf-8",
                   json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def _send(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    print(f"Hearthlight cockpit → http://localhost:{PORT}  (Ctrl+C to stop)")
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
