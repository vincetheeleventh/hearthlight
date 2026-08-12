from __future__ import annotations

import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch


SCAN_PATH = Path(__file__).resolve().parents[1] / "scripts" / "scan.py"
SPEC = importlib.util.spec_from_file_location("hearthlight_dashboard_scan", SCAN_PATH)
scan = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(scan)


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


class DashboardScanTests(unittest.TestCase):
    def test_production_state_is_passed_through_from_studio(self) -> None:
        payload = {
            "runtimeSeconds": 12.5,
            "identitySource": "project.json",
            "shots": [
                {"designState": {"state": "locked"}, "productionState": {"state": "approved"}, "inputs": {"state": "ready"}},
                {"designState": {"state": "designed"}, "productionState": {"state": "candidate-ready"}, "inputs": {"state": "broken"}},
            ],
        }
        with patch.object(scan.urllib.request, "urlopen", return_value=Response(json.dumps(payload).encode())):
            state = scan.production_payload("demo")
        self.assertTrue(state["available"])
        self.assertEqual(state["design"], {"locked": 1, "designed": 1})
        self.assertEqual(state["production"], {"approved": 1, "candidate-ready": 1})
        self.assertEqual(state["inputs"], {"ready": 1, "broken": 1})
        self.assertEqual(state["nextAction"], "Repair inputs on 1 shot(s).")

    def test_scanner_reports_unavailable_without_inventing_progress(self) -> None:
        with patch.object(scan.urllib.request, "urlopen", side_effect=OSError("offline")):
            state = scan.production_payload("demo")
        self.assertFalse(state["available"])
        self.assertEqual(state["shots"], 0)
        self.assertEqual(state["design"], {})


if __name__ == "__main__":
    unittest.main()
