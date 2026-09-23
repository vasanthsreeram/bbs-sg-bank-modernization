"""Tests for the legacy-ui operations terminal.

Three layers:

* static checks that ``terminal.html`` is self-contained, carries the synthetic
  disclosure and wires up every element the scripts touching the DOM need;
* server/API tests that drive ``legacy-ui/server.py`` through a real HTTP
  server, including one genuine COBOL batch run through ``legacy/bank.cob``;
* a runner for ``tests/interaction.mjs``, the headless walkthrough that drives
  the terminal page itself.

Run with::

    python3 legacy-ui/tests/test_terminal.py

The COBOL batch test and the interaction walkthrough are skipped when GnuCOBOL
or Node are unavailable; nothing is faked in their place.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
UI = HERE.parent
sys.path.insert(0, str(UI))

import server as ui_server  # noqa: E402  (path fixed above)

HTML = (UI / "terminal.html").read_text()
LOGIC = re.search(r'<script id="terminal-logic">(.*?)</script>', HTML, re.S).group(1)
WIRING = re.search(r'<script id="terminal-wiring">(.*?)</script>', HTML, re.S).group(1)
NODE = shutil.which("node")


def terminal_ids() -> set[str]:
    return set(re.findall(r'id="([a-z0-9-]+)"', HTML))


class StaticTests(unittest.TestCase):
    def test_page_is_self_contained(self) -> None:
        for match in re.findall(r'(?:src|href)="([^"]+)"', HTML):
            self.assertTrue(match.startswith("data:"), f"external asset referenced: {match}")

    def test_no_external_urls_in_markup_or_scripts(self) -> None:
        allowed = ("http://www.w3.org/", "https://www.w3.org/", "http://127.0.0.1", "http://localhost")
        for name, text in (("terminal.html", HTML), ("logic", LOGIC), ("wiring", WIRING)):
            for match in re.findall(r"https?://[^\s\"'<>)]+", text):
                if match.startswith(allowed):
                    continue
                self.fail(f"{name} references an external URL: {match}")

    def test_disclosure_is_present_and_discreet(self) -> None:
        self.assertIn("SYNTHETIC DEMO", LOGIC)
        self.assertIn("fictional", HTML.lower())
        self.assertIn("synthetic demo", HTML.lower())
        self.assertIn("doc-disclosure", HTML)
        # A discreet line, not a full-screen banner.
        self.assertLess(HTML.lower().count("synthetic"), 12)

    def test_simulated_labels_exist_for_every_simulated_path(self) -> None:
        for marker in ("SIMULATED RUN -- NO LOCAL COBOL ENGINE REACHABLE",
                       "SPOOL DISPLAY (SIMULATED",
                       "SIMULATION COMPLETE",
                       "SIMULATED RESULT"):
            self.assertIn(marker, LOGIC + ui_server.__doc__ + Path(ui_server.__file__).read_text())

    def test_elements_touched_by_wiring_exist(self) -> None:
        ids = terminal_ids()
        for name in re.findall(r'getElementById\("([^"]+)"\)', WIRING):
            self.assertIn(name, ids, f"wiring looks up #{name}, which is not in the markup")

    def test_required_controls_are_present(self) -> None:
        for hook in ("id=\"screen\"", "id=\"keypad\"", "id=\"engine-label\"", "role=\"application\"",
                     "@media (prefers-reduced-motion", "scanlines"):
            self.assertIn(hook, HTML)

    def test_function_keys_cover_the_period_set(self) -> None:
        for key in range(1, 13):
            self.assertIn(f"key: {key},", LOGIC, f"PF{key} is not defined")
        self.assertIn("PF9=SUBMIT JOB", LOGIC)

    def test_row_budget_matches_a_24_line_screen(self) -> None:
        self.assertIn("ROWS = 24", LOGIC)
        self.assertIn("COLS = 80", LOGIC)
        self.assertIn("for (var i = 0; i < 18; i++) rows.push(content[i]", LOGIC)

    @unittest.skipUnless(NODE, "node is not installed")
    def test_inline_scripts_parse(self) -> None:
        for name, source in (("logic", LOGIC), ("wiring", WIRING)):
            path = HERE / f"_parse-{name}.js"
            path.write_text(source)
            try:
                proc = subprocess.run([NODE, "--check", str(path)], capture_output=True, text=True)
            finally:
                path.unlink()
            self.assertEqual(proc.returncode, 0, f"{name} script does not parse:\n{proc.stderr}")


class ServerApiTests(unittest.TestCase):
    """Drive server.py over HTTP, including one real COBOL batch."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.session = ui_server.build_session()
        cls.engine = cls.session.summary()["engine"]
        ui_server.SESSION = cls.session
        cls.httpd = ui_server.Server(("127.0.0.1", 0), ui_server.Handler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def get(self, path: str):
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}{path}", timeout=15) as response:
            return json.loads(response.read())

    def post(self, path: str, payload: dict):
        request = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read())

    def test_terminal_page_is_served(self) -> None:
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/", timeout=15) as response:
            body = response.read().decode()
        self.assertEqual(response.status, 200)
        self.assertIn("BBS SG BANK", body)
        self.assertIn("SYNTHETIC DEMO", body)

    def test_status_reports_the_engine(self) -> None:
        status = self.get("/api/status")
        self.assertEqual(status["bank"], "BBS SG BANK")
        self.assertTrue(status["engine"]["source"].endswith("bank.cob"))
        self.assertIn("disclosure", status)

    def test_accounts_are_paged_and_sum_to_the_ledger(self) -> None:
        page = self.get("/api/accounts?page=0&size=10")
        self.assertEqual(len(page["rows"]), 10)
        self.assertEqual(page["total"], 1200)
        self.assertEqual(page["ledger_total_cents"], page["opening_total_cents"])
        self.assertTrue(all(len(row["id"]) == 8 and row["id"].isdigit() for row in page["rows"]))

    def test_operations_queue_marks_the_pinned_rejections(self) -> None:
        page = self.get("/api/operations?page=0&size=5")
        self.assertGreaterEqual(page["counts"]["rejected"], 1)
        self.assertEqual(page["counts"]["total"], 403)
        last = self.get(f"/api/operations?page={page['total_pages'] - 1}&size=5")
        reasons = {row["reason"] for row in last["rows"] if row["reason"]}
        self.assertIn("insufficient funds", reasons)
        self.assertIn("source and destination equal", reasons)

    def test_unknown_warehouse_is_rejected(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as caught:
            self.post("/api/batch", {"warehouse": "HUGE"})
        self.assertEqual(caught.exception.code, 400)
        caught.exception.close()

    @unittest.skipUnless(shutil.which("cobc") or ui_server.find_cobc(), "cobc is not available")
    def test_real_cobol_batch_runs_and_matches_the_replay(self) -> None:
        self.assertTrue(self.engine["available"], self.engine["note"])
        started = time.perf_counter()
        job = self.post("/api/batch", {"warehouse": "SMALL", "seed": 20260923, "verify": True})
        self.assertEqual(job["state"], "running")
        deadline = time.time() + 90
        while time.time() < deadline:
            job = self.get("/api/batch")
            if job["state"] != "running":
                break
            time.sleep(0.15)
        wall = time.perf_counter() - started
        self.assertEqual(job["state"], "done", job.get("error"))
        self.assertEqual(job["rc"], 0)
        metrics = job["metrics"]
        self.assertEqual(metrics["PROCESSED"], 150)
        self.assertEqual(metrics["REJECTED"], 3)
        self.assertIsNotNone(job["seconds"])
        self.assertLess(job["seconds"], wall)
        self.assertTrue(job["prediction"]["matches"], "replay disagreed with the COBOL counters")
        self.assertTrue(job["verify_result"]["ok"], job["verify_result"])
        self.assertEqual(job["verify_result"]["metrics"], metrics)
        self.assertTrue(job["spool_simulated"], "the spool display must be labelled simulated")
        journal = "\n".join(entry["line"] for entry in job["journal"])
        self.assertIn("PROCESSED=00000150", journal)
        self.assertNotIn("SIMULATED", journal)
        # the ledger now reflects the job's rewritten master file
        status = self.get("/api/status")
        self.assertEqual(status["ledger_state"], f"POSTED {job['id']}")
        self.assertEqual(status["ledger_total_cents"], metrics["TOTAL_CENTS"])
        # and the run is on the journal
        runs = self.get("/api/journal")["runs"]
        self.assertEqual(runs[0]["id"], job["id"])
        self.assertTrue(runs[0]["verify"])

    def test_reset_restores_the_opening_ledger(self) -> None:
        status = self.post("/api/reset", {})
        self.assertEqual(status["ledger_state"], "OPENING")
        page = self.get("/api/accounts?page=0&size=1")
        self.assertEqual(page["rows"][0]["balance_cents"], page["rows"][0]["opening_cents"])

    def test_simulated_mode_is_available_and_labelled(self) -> None:
        job = self.post("/api/batch", {"warehouse": "SMALL", "seed": 7, "verify": False, "mode": "simulated"})
        deadline = time.time() + 30
        while time.time() < deadline and job["state"] == "running":
            time.sleep(0.2)
            job = self.get("/api/batch")
        self.assertEqual(job["state"], "done")
        journal = "\n".join(entry["line"] for entry in job["journal"])
        self.assertIn("SIMULATED", journal)
        self.assertIn("NO COBOL JOB EXECUTED", journal)
        self.assertEqual(job["seconds"], 0.0)


@unittest.skipUnless(NODE, "node is not installed")
class InteractionTests(unittest.TestCase):
    """Run the headless terminal walkthrough against a live helper server."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.session = ui_server.build_session()
        ui_server.SESSION = cls.session
        cls.httpd = ui_server.Server(("127.0.0.1", 0), ui_server.Handler)
        cls.port = cls.httpd.server_address[1]
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()
        proc = subprocess.run(
            [NODE, str(HERE / "interaction.mjs"), f"http://127.0.0.1:{cls.port}"],
            capture_output=True, text=True, timeout=600,
        )
        cls.returncode, cls.output = proc.returncode, proc.stdout + proc.stderr
        cls.httpd.shutdown()
        cls.httpd.server_close()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.httpd.server_close()

    def test_walkthrough_passes(self) -> None:
        if self.returncode == 2:
            self.skipTest("the interaction harness could not start: " + self.output[-400:])
        self.assertEqual(self.returncode, 0, self.output[-2000:])

    def test_walkthrough_covers_the_batch_and_the_labels(self) -> None:
        summary = re.search(r"(\d+)/(\d+) checks passed", self.output)
        self.assertIsNotNone(summary, self.output[-2000:])
        self.assertGreaterEqual(int(summary.group(1)), 40)
        self.assertIn("LIVE COBOL", self.output)
        self.assertIn("spool window is labelled SIMULATED", self.output)
        self.assertIn("checks passed", self.output)


@unittest.skipUnless(NODE, "node is not installed")
class OfflineInteractionTests(unittest.TestCase):
    """With no engine reachable every batch screen must say SIMULATED."""

    @classmethod
    def setUpClass(cls) -> None:
        proc = subprocess.run(
            [NODE, str(HERE / "interaction.mjs"), "--offline"],
            capture_output=True, text=True, timeout=300,
        )
        cls.returncode, cls.output = proc.returncode, proc.stdout + proc.stderr

    def test_offline_walkthrough_passes(self) -> None:
        if self.returncode == 2:
            self.skipTest("the interaction harness could not start: " + self.output[-400:])
        self.assertEqual(self.returncode, 0, self.output[-2000:])
        self.assertIn("offline page never claims LIVE COBOL", self.output)
        self.assertIn("offline result is flagged as a replay", self.output)


if __name__ == "__main__":
    unittest.main(verbosity=2)
