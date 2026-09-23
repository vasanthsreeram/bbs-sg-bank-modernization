"""End-to-end tests for the demo HTTP app.

A real server is started on an ephemeral port in a background thread and driven
over HTTP, so these cover routing, JSON shaping, static files and error paths.
"""

from __future__ import annotations

import http.client
import json
import sys
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import app  # noqa: E402


class ApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = app.build_server("127.0.0.1", 0)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, name="demo-server", daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    # ------------------------------------------------------------- helpers

    def request(self, path: str, method: str = "GET", body=None):
        data = None if body is None else json.dumps(body).encode()
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=data,
            method=method,
            headers={"Content-Type": "application/json"} if data else {},
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                raw = response.read().decode()
                return response.status, json.loads(raw) if raw.startswith(("{", "[")) else raw
        except urllib.error.HTTPError as error:
            raw = error.read().decode()
            error.close()
            try:
                return error.code, json.loads(raw)
            except json.JSONDecodeError:
                return error.code, raw

    def raw_get(self, path: str) -> tuple[int, str]:
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        connection.request("GET", path)
        response = connection.getresponse()
        payload = response.read().decode("utf-8", "replace")
        connection.close()
        return response.status, payload

    # --------------------------------------------------------------- basics

    def test_health_and_meta(self) -> None:
        status, payload = self.request("/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "ok")
        self.assertTrue(payload["fictional"])

        status, meta = self.request("/api/meta")
        self.assertEqual(status, 200)
        self.assertTrue(meta["fictional"])
        self.assertIn("not a real institution", meta["disclaimer"].lower())
        self.assertIn("synthetic", meta["disclaimer"].lower())
        self.assertIn("modern/bank.py", meta["engine"]["modern"])

    def test_static_frontend_is_served(self) -> None:
        for path, needle in (("/", "BBS SG Bank"), ("/styles.css", ":root"), ("/app.js", "fictional")):
            status, payload = self.request(path)
            self.assertEqual(status, 200, path)
            self.assertIn(needle, payload)
        status, html = self.request("/")
        self.assertIn("BBS SG Bank", html)
        self.assertIn("synthetic demo", html)
        self.assertIn("not a real institution", html)

    def test_static_traversal_is_refused(self) -> None:
        for path in ("/../backend/service.py", "/%2e%2e/backend/service.py", "/../../etc/hosts"):
            status, payload = self.raw_get(path)
            self.assertIn(status, (403, 404), path)
            self.assertNotIn("BankService", payload)

    def test_unknown_api_and_asset_404(self) -> None:
        status, payload = self.request("/api/nope")
        self.assertEqual(status, 404)
        self.assertEqual(payload["error"]["code"], "not_found")

        status, _ = self.request("/missing.js")
        self.assertEqual(status, 404)

    def test_bad_json_body_is_reported(self) -> None:
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        connection.request("POST", "/api/operations", body=b"{not json", headers={"Content-Length": "9"})
        response = connection.getresponse()
        payload = json.loads(response.read().decode())
        connection.close()
        self.assertEqual(response.status, 400)
        self.assertEqual(payload["error"]["code"], "invalid_json")

    # ------------------------------------------------------------ ledger api

    def test_summary_and_accounts(self) -> None:
        status, summary = self.request("/api/summary")
        self.assertEqual(status, 200)
        self.assertEqual(summary["account_count"], 12)
        self.assertTrue(summary["invariant_ok"])
        self.assertEqual(summary["currency"], "SGD")

        status, accounts = self.request("/api/accounts")
        self.assertEqual(status, 200)
        self.assertEqual(accounts["count"], 12)
        self.assertTrue(all(account["balance_cents"] > 0 for account in accounts["accounts"]))

        status, filtered = self.request("/api/accounts?q=changi")
        self.assertEqual(status, 200)
        self.assertEqual(filtered["count"], 1)
        self.assertEqual(filtered["accounts"][0]["id"], "10000009")

    def test_account_detail_and_missing_account(self) -> None:
        status, detail = self.request("/api/accounts/10000009")
        self.assertEqual(status, 200)
        self.assertEqual(detail["name"], "Changi Freight Services")
        self.assertIn("history", detail)

        status, payload = self.request("/api/accounts/42424242")
        self.assertEqual(status, 404)
        self.assertEqual(payload["error"]["code"], "not_found")

    def test_audit_filters_and_validation(self) -> None:
        status, audit = self.request("/api/audit?limit=5")
        self.assertEqual(status, 200)
        self.assertLessEqual(audit["count"], 5)
        self.assertTrue(audit["fictional"])

        status, rejected = self.request("/api/audit?status=rejected")
        self.assertEqual(status, 200)
        self.assertTrue(all(entry["status"] == "rejected" for entry in rejected["entries"]))

        status, payload = self.request("/api/audit?status=maybe")
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"]["code"], "bad_request")

    def test_legacy_source_excerpt(self) -> None:
        status, excerpt = self.request("/api/legacy/source")
        self.assertEqual(status, 200)
        self.assertEqual(excerpt["path"], "legacy/bank.cob")
        self.assertTrue(excerpt["bottleneck_lines"])

    # -------------------------------------------------------------- postings

    def test_posting_a_transfer_and_a_rejection(self) -> None:
        status, response = self.request(
            "/api/operations",
            method="POST",
            body={"kind": "T", "source": "10000004", "target": "10000005", "amount_cents": 2500},
        )
        self.assertEqual(status, 201)
        self.assertEqual(response["posted"], 1)
        operation = response["result"]["operations"][0]
        self.assertEqual(operation["status"], "posted")
        self.assertTrue(response["result"]["invariant_ok"])

        status, rejected = self.request(
            "/api/operations",
            method="POST",
            body={"kind": "W", "source": "10000008", "amount_cents": 9_999_999_999},
        )
        # Rejections are business outcomes: understood, judged, audited - not an error.
        self.assertEqual(status, 200)
        self.assertEqual(rejected["rejected"], 1)
        self.assertEqual(rejected["posted"], 0)
        self.assertEqual(rejected["result"]["operations"][0]["reason"], "insufficient funds")

    def test_posting_accepts_a_batch_of_operations(self) -> None:
        status, response = self.request(
            "/api/operations",
            method="POST",
            body={
                "operations": [
                    {"kind": "D", "source": "10000006", "amount_cents": 10_000},
                    {"kind": "T", "source": "10000006", "target": "10000007", "amount_cents": 5_000},
                ]
            },
        )
        self.assertEqual(status, 201)
        self.assertEqual(response["result"]["processed"], 2)

    def test_reset_restores_seed_state(self) -> None:
        self.request(
            "/api/operations",
            method="POST",
            body={"kind": "D", "source": "10000010", "amount_cents": 1_000_000},
        )
        status, payload = self.request("/api/reset", method="POST")
        self.assertEqual(status, 200)
        self.assertEqual(payload["summary"]["audit_count"], 12)
        _, summary = self.request("/api/summary")
        self.assertEqual(summary["total_cents"], 78_461_450)

    # ------------------------------------------------------------ demo batch

    def test_demo_batch_endpoint_conserves_value(self) -> None:
        status, payload = self.request(
            "/api/batch",
            method="POST",
            body={"operations": 15, "include_edge_cases": True, "seed": 4},
        )
        self.assertEqual(status, 200)
        batch = payload["result"]
        self.assertTrue(batch["conservation_ok"])
        self.assertTrue(batch["engine_matches_simulation"])
        self.assertEqual(batch["processed"] + batch["rejected"], 18)
        self.assertTrue(batch["rejections_by_reason"])

    def test_demo_batch_rejects_bad_sizes(self) -> None:
        status, payload = self.request("/api/batch", method="POST", body={"operations": 0})
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"]["code"], "ledger_error")

    # ------------------------------------------------------------- benchmark

    def test_benchmark_reports_only_measured_values(self) -> None:
        status, report = self.request("/api/benchmark?accounts=60&operations=20&repeats=1&fresh=1")
        self.assertEqual(status, 200)
        self.assertIn("environment", report)
        self.assertTrue(report["modern"]["available"])
        self.assertGreater(report["modern"]["median"], 0)
        self.assertEqual(report["modern"]["PROCESSED"], 20)

        legacy = report["legacy"]
        if legacy["available"]:
            self.assertGreater(legacy["median"], 0)
            self.assertIsNotNone(report["speedup"])
            self.assertEqual(legacy["REJECTED"], 3)
            self.assertTrue(report["outputs_identical"])
        else:
            # Honesty contract: no timing, no ratio, and a reason is always given.
            self.assertIsNone(legacy["seconds"])
            self.assertIsNone(report["speedup"])
            self.assertTrue(legacy["reason"])

    def test_benchmark_validates_parameters(self) -> None:
        status, payload = self.request("/api/benchmark?accounts=1")
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"]["code"], "benchmark_error")


if __name__ == "__main__":
    unittest.main()
