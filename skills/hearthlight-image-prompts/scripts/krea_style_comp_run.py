#!/usr/bin/env python3
"""Execute validated Krea style/composition packets with durable per-shot history."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import sys
import time
import urllib.request
import uuid
from pathlib import Path

from PIL import Image


HERE = Path(__file__).resolve().parent
COMPILER_SPEC = importlib.util.spec_from_file_location("krea_style_comp", HERE / "krea_style_comp.py")
compiler = importlib.util.module_from_spec(COMPILER_SPEC)
COMPILER_SPEC.loader.exec_module(compiler)
TERMINAL = {"completed", "failed", "cancelled"}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def append_jsonl(path: Path, event: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    events = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid generation ledger line {line_number}: {exc}") from exc
    return events


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_job(value):
    if isinstance(value, dict):
        if "job_id" in value or ("status" in value and ("result" in value or "urls" in value)):
            return value
        for key in ("job", "data", "result"):
            nested = value.get(key)
            found = normalize_job(nested)
            if found:
                return found
    return None


def result_urls(job: dict) -> list[str]:
    result = job.get("result")
    candidates = []
    if isinstance(result, dict):
        candidates.extend(result.get("urls") or [])
        for key in ("url", "image_url", "output_url"):
            if result.get(key):
                candidates.append(result[key])
    candidates.extend(job.get("urls") or [])
    for key in ("url", "image_url", "output_url"):
        if job.get(key):
            candidates.append(job[key])
    return [str(item) for item in candidates if item]


class KreaMcp:
    REQUIRED = ("list_models", "get_model_schema", "generate_image", "get_job")

    def __init__(self) -> None:
        hermes_root = Path(sys.executable).resolve().parents[2]
        if not (hermes_root / "tools" / "mcp_tool.py").exists():
            raise SystemExit("Run with the Hermes Python runtime; Krea OAuth bridge unavailable")
        sys.path.insert(0, str(hermes_root))
        from tools import mcp_tool
        from tools.registry import registry
        self.mcp_tool = mcp_tool
        self.registry = registry
        names = mcp_tool.register_mcp_servers(mcp_tool._load_mcp_config())
        self.names = [name for name in names if "krea" in name.lower()]
        self.tools = {}
        for suffix in self.REQUIRED:
            matches = [name for name in self.names if name.lower().endswith(suffix)]
            if len(matches) != 1:
                raise SystemExit(f"Krea MCP tool {suffix} unavailable or ambiguous: {matches}")
            self.tools[suffix] = matches[0]

    def close(self) -> None:
        self.mcp_tool.shutdown_mcp_servers()

    def schema(self, suffix: str) -> dict:
        return self.registry.get_schema(self.tools[suffix]) or {}

    def call(self, suffix: str, args: dict):
        raw = self.registry.dispatch(self.tools[suffix], args)
        outer = json.loads(raw) if isinstance(raw, str) else raw
        if isinstance(outer, dict) and outer.get("error"):
            raise RuntimeError(str(outer["error"]))
        value = outer.get("structuredContent") if isinstance(outer, dict) else None
        if value is None and isinstance(outer, dict):
            value = outer.get("result")
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    def live_preflight(self, packet: dict) -> dict:
        catalog = self.call("list_models", {})
        models = catalog.get("models", []) if isinstance(catalog, dict) else []
        if packet["model"] not in {item.get("id") for item in models if isinstance(item, dict)}:
            raise SystemExit(f"Krea model unavailable: {packet['model']}")
        live = self.call("get_model_schema", {"model": packet["model"]})
        schema = (live or {}).get("inputSchema") or {}
        props = schema.get("properties") or {}
        required = set(schema.get("required") or [])
        required_fields = {"prompt", "aspect_ratio", "resolution", "moodboards"}
        if not {"prompt", "aspect_ratio", "resolution"}.issubset(required):
            raise SystemExit("Krea model required-input schema changed; generation blocked")
        if not required_fields.issubset(props):
            raise SystemExit("Krea model no longer exposes required prompt/moodboard fields")
        if packet["aspect_ratio"] not in ((props["aspect_ratio"].get("enum") or [])):
            raise SystemExit(f"Live Krea schema rejects aspect ratio {packet['aspect_ratio']}")
        if packet["resolution"] not in ((props["resolution"].get("enum") or [])):
            raise SystemExit(f"Live Krea schema rejects resolution {packet['resolution']}")
        for key in packet["generation_parameters"]:
            if key not in props:
                raise SystemExit(f"Live Krea schema no longer accepts generation parameter {key}")
        moodboard = packet["references"][0]
        if not (0 <= float(moodboard["strength"]) <= 1):
            raise SystemExit("Moodboard strength outside live 0-1 range")
        return live


def validate_plan(root: Path) -> tuple[dict, dict[str, dict]]:
    expected, expected_packets = compiler.compile_batch(root)
    plan_path = compiler.batch_plan_path(root, expected)
    if not plan_path.exists():
        raise SystemExit("Batch plan missing; run krea_style_comp.py --all first")
    plan = read_json(plan_path)
    for key in ("project", "workflow_stage", "model", "aspect_ratio", "resolution", "generation_parameters", "generation_count"):
        if plan.get(key) != expected.get(key):
            raise SystemExit(f"Batch plan stale at {key}; recompile before generation")
    if plan.get("source") != expected.get("source"):
        raise SystemExit("Batch plan workbook/registry identity is stale")
    if plan.get("prompt_contract") != expected.get("prompt_contract"):
        raise SystemExit("Batch prompt contract changed; recompile before generation")
    expected_by_id = {packet["shot_id"]: packet for _, packet in expected_packets}
    if {item["shot_id"] for item in plan.get("packets", [])} != set(expected_by_id):
        raise SystemExit("Batch plan shot set differs from current workbook/registry")
    disk_packets = {}
    for item in plan["packets"]:
        packet_path = root / item["packet"]
        if not packet_path.exists():
            raise SystemExit(f"Prompt packet missing: {item['packet']}")
        disk = read_json(packet_path)
        expected_packet = expected_by_id[item["shot_id"]]
        for key in ("shot", "shot_id", "title", "workflow_stage", "model", "aspect_ratio", "resolution", "generation_parameters", "prompt", "prompt_sha256", "request_sha256", "references", "source"):
            if disk.get(key) != expected_packet.get(key):
                raise SystemExit(f"Shot {item['shot']} packet stale at {key}; recompile before generation")
        compiler.validate_prompt(disk["prompt"])
        disk_packets[disk["shot"]] = disk
    return plan, disk_packets


def asset_event_map(root: Path) -> dict[str, str]:
    path = root / "05-storyboard" / "asset-shot-map.json"
    if not path.exists():
        return {}
    return {
        str(item["event_id"]): str(item["shot_id"])
        for item in read_json(path).get("entries", [])
        if item.get("event_id") and item.get("shot_id")
    }


def event_shot_id(event: dict, mappings: dict[str, str]) -> str | None:
    return event.get("shot_id") or mappings.get(str(event.get("event_id") or ""))


def next_version(events: list[dict], shot_id: str, mappings: dict[str, str]) -> int:
    versions = [
        int(event.get("version") or 0)
        for event in events
        if event_shot_id(event, mappings) == shot_id and str(event.get("version") or "").isdigit()
    ]
    return max(versions, default=0) + 1


def completed_event(root: Path, events: list[dict], packet: dict, mappings: dict[str, str]) -> dict | None:
    for event in reversed(events):
        if event.get("event") != "generation":
            continue
        if event_shot_id(event, mappings) != packet["shot_id"]:
            continue
        if event.get("workflow_stage") != packet["workflow_stage"]:
            continue
        if event.get("request_sha256") != packet["request_sha256"]:
            continue
        asset = event.get("asset_path")
        if asset and (root / asset).exists():
            return event
    return None


def pending_submission(events: list[dict], packet: dict) -> dict | None:
    completed_runs = {event.get("run_id") for event in events if event.get("event") in {"generation", "generation-failed"}}
    for event in reversed(events):
        if event.get("event") != "krea-submitted" or event.get("run_id") in completed_runs:
            continue
        if event.get("shot_id") == packet["shot_id"] and event.get("request_sha256") == packet["request_sha256"]:
            return event
    return None


def poll_job(client: KreaMcp, job_id: str, timeout_seconds: int = 300) -> dict:
    deadline = time.monotonic() + timeout_seconds
    while True:
        payload = client.call("get_job", {"jobId": job_id})
        job = normalize_job(payload)
        if not job:
            raise RuntimeError("Krea get_job returned no job object")
        status = str(job.get("status") or "").lower()
        if status in TERMINAL:
            return job
        if time.monotonic() >= deadline:
            raise TimeoutError(f"Krea job {job_id} still running after {timeout_seconds}s")
        time.sleep(5)


def download_png(url: str, path: Path, aspect_ratio: str) -> tuple[int, int]:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".download")
    request = urllib.request.Request(url, headers={"User-Agent": "Hearthlight/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=120) as response, temp.open("wb") as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
        with Image.open(temp) as image:
            image.load()
            width, height = image.size
            expected = {"16:9": 16 / 9, "4:3": 4 / 3, "9:16": 9 / 16}.get(aspect_ratio)
            if expected and abs((width / height) - expected) > 0.03:
                raise RuntimeError(f"Generated dimensions {width}x{height} violate {aspect_ratio}")
            image.convert("RGB").save(path, format="PNG")
    finally:
        if temp.exists():
            temp.unlink()
    return width, height


def output_path(root: Path, packet: dict, version: int) -> Path:
    safe = compiler.normalize_shot(packet["shot"]).lower()
    return root / "04-images" / "style-composition-v4" / f"shot-{safe}-{packet['shot_id'][:8]}-v{version:02d}.png"


def run_packet(root: Path, client: KreaMcp, packet: dict, events: list[dict], mappings: dict[str, str]) -> dict:
    existing = completed_event(root, events, packet, mappings)
    if existing:
        return {"shot": packet["shot"], "status": "skipped-complete", "asset_path": existing["asset_path"]}
    pending = pending_submission(events, packet)
    if pending:
        run_id = pending["run_id"]
        version = int(pending["version"])
        job_id = pending["krea_job_id"]
    else:
        version = next_version(events, packet["shot_id"], mappings)
        run_id = str(uuid.uuid4())
        input_payload = {
            "prompt": packet["prompt"],
            "aspect_ratio": packet["aspect_ratio"],
            "resolution": packet["resolution"],
            **packet["generation_parameters"],
            "moodboards": [
                {"id": packet["references"][0]["id"], "strength": packet["references"][0]["strength"]}
            ],
        }
        response = client.call("generate_image", {"model": packet["model"], "input": input_payload, "sync": False})
        submitted = normalize_job(response)
        if not submitted or not submitted.get("job_id"):
            raise RuntimeError(f"Shot {packet['shot']}: Krea returned no job ID")
        job_id = submitted["job_id"]
        submit_event = {
            "schema_version": 3,
            "event": "krea-submitted",
            "event_id": str(uuid.uuid4()),
            "run_id": run_id,
            "created_at": utc_now(),
            "shot": packet["shot"],
            "shot_id": packet["shot_id"],
            "version": version,
            "workflow_stage": packet["workflow_stage"],
            "packet": compiler.base.relpath(compiler.packet_path(root, packet), root),
            "prompt_sha256": packet["prompt_sha256"],
            "request_sha256": packet["request_sha256"],
            "generation_parameters": packet["generation_parameters"],
            "model": packet["model"],
            "krea_job_id": job_id,
        }
        append_jsonl(root / "04-images" / "generations.jsonl", submit_event)
        events.append(submit_event)
    job = poll_job(client, job_id)
    status = str(job.get("status") or "").lower()
    if status != "completed":
        failed = {
            "schema_version": 3,
            "event": "generation-failed",
            "event_id": str(uuid.uuid4()),
            "run_id": run_id,
            "created_at": utc_now(),
            "shot": packet["shot"],
            "shot_id": packet["shot_id"],
            "version": version,
            "workflow_stage": packet["workflow_stage"],
            "prompt_sha256": packet["prompt_sha256"],
            "request_sha256": packet["request_sha256"],
            "generation_parameters": packet["generation_parameters"],
            "model": packet["model"],
            "krea_job_id": job_id,
            "status": status,
            "error": job.get("error"),
        }
        append_jsonl(root / "04-images" / "generations.jsonl", failed)
        events.append(failed)
        raise RuntimeError(f"Shot {packet['shot']}: Krea job {status}: {job.get('error')}")
    urls = result_urls(job)
    if not urls:
        raise RuntimeError(f"Shot {packet['shot']}: completed Krea job has no result URL")
    target = output_path(root, packet, version)
    dimensions = download_png(urls[0], target, packet["aspect_ratio"])
    generation = {
        "schema_version": 3,
        "event": "generation",
        "event_id": str(uuid.uuid4()),
        "run_id": run_id,
        "created_at": utc_now(),
        "shot": packet["shot"],
        "shot_id": packet["shot_id"],
        "version": version,
        "parent_version": version - 1 if version > 1 else None,
        "workflow_stage": packet["workflow_stage"],
        "source": "hearthlight-krea-frame-one-v4",
        "asset_path": compiler.base.relpath(target, root),
        "sha256": file_sha256(target),
        "dimensions": list(dimensions),
        "aspect_ratio": packet["aspect_ratio"],
        "resolution": packet["resolution"],
        "prompt": packet["prompt"],
        "prompt_sha256": packet["prompt_sha256"],
        "request_sha256": packet["request_sha256"],
        "generation_parameters": packet["generation_parameters"],
        "prompt_known": True,
        "model": packet["model"],
        "krea_job_id": job_id,
        "krea_url": urls[0],
        "references": packet["references"],
        "source_contract": packet["source"],
        "review_status": "pending-review",
        "selected_final": False,
        "provider_result": job,
    }
    append_jsonl(root / "04-images" / "generations.jsonl", generation)
    events.append(generation)
    return {"shot": packet["shot"], "status": "generated", "asset_path": generation["asset_path"], "job_id": job_id}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--shots", nargs="+")
    mode.add_argument("--all", action="store_true")
    mode.add_argument("--probe", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = compiler.base.project_dir(args.project)
    plan, packets = validate_plan(root)
    selected = list(packets) if args.all or args.probe else [compiler.normalize_shot(item) for item in args.shots]
    unknown = sorted(set(selected) - set(packets))
    if unknown:
        raise SystemExit(f"Shots are shared, source-only, or unknown: {unknown}")
    if args.all:
        approval = read_json(root / "03-bible" / "assets.json").get("cost_approvals", {}).get("style_composition_v4", {})
        if approval.get("status") != "approved":
            raise SystemExit("Full V4 batch cost approval missing; record estimate and explicit approval first")
    if args.dry_run:
        print(json.dumps({
            "status": "validated",
            "shots": selected,
            "count": len(selected),
            "model": plan["model"],
            "aspect_ratio": plan["aspect_ratio"],
            "prompt_contract": plan["prompt_contract"],
        }, indent=2, ensure_ascii=False))
        return 0
    client = KreaMcp()
    try:
        first = packets[selected[0]]
        live = client.live_preflight(first)
        if args.probe:
            print(json.dumps({
                "status": "ready",
                "model": first["model"],
                "live_model_name": live.get("name"),
                "input_fields": sorted((live.get("inputSchema") or {}).get("properties", {})),
                "planned_count": plan["generation_count"],
            }, indent=2, ensure_ascii=False))
            return 0
        events = load_jsonl(root / "04-images" / "generations.jsonl")
        mappings = asset_event_map(root)
        results = []
        for shot in selected:
            result = run_packet(root, client, packets[shot], events, mappings)
            results.append(result)
            print(json.dumps(result, ensure_ascii=False), flush=True)
        print(json.dumps({"status": "complete", "results": results}, ensure_ascii=False))
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())