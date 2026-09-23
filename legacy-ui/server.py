#!/usr/bin/env python3
"""Local COBOL-backed runner for the BBS SG Bank 1980s operations terminal.

Serves ``legacy-ui/terminal.html`` and a tiny JSON API that:

* generates deterministic flat-file fixtures (``accounts.dat`` / ``operations.dat``)
  using the same fixed-width layout the legacy batch expects;
* compiles the *unmodified* ``legacy/bank.cob`` with the isolated GnuCOBOL build
  (``scripts/get_cobc.sh``) and runs that binary as a real subprocess;
* streams the job's real journal -- including its genuine wall-clock elapsed
  time -- to the operator terminal;
* optionally cross-checks the COBOL result against ``modern/bank.py``.

Standard library only, bound to localhost, works on generated synthetic data.
Nothing here contacts a network, a real bank, or a real customer.

Run ``python3 legacy-ui/server.py`` (or ``legacy-ui/run.sh``) and open the URL.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
LEGACY_SOURCE = ROOT / "legacy" / "bank.cob"
MODERN_SCRIPT = ROOT / "modern" / "bank.py"
TERMINAL_HTML = HERE / "terminal.html"

DEFAULT_SEED = 20260923
EDGE_CASE_COUNT = 3
DEFAULT_PORT = 8792

# Warehouse presets. Account count drives the legacy batch's O(operations x
# accounts) cost, so the larger presets are genuinely slower -- that is the
# delay the operator terminal shows, and it is measured, never scripted.
WAREHOUSES = {
    "SMALL": {"accounts": 400, "operations": 150},
    "STANDARD": {"accounts": 1200, "operations": 400},
    "LARGE": {"accounts": 5000, "operations": 500},
}

DISCLOSURE = (
    "SYNTHETIC DEMO -- BBS SG Bank is fictional. Every account, balance and "
    "operation is generated locally on this machine; no real customers, "
    "credential or banking system is involved."
)

# Display-only holder names. They never enter the flat files, which carry the
# 8-digit numeric ids the COBOL record layout requires.
PREFIXES = (
    "HARBOURFRONT", "TIONG BAHRU", "KRANJI", "SENTOSA", "JURONG", "ANG MO KIO",
    "PUNGGOL", "QUEENSTOWN", "CHANGI", "ORCHARD", "WOODLANDS", "SERANGOON",
)
SUFFIXES = (
    "RETAIL PTE LTD", "COFFEE CO", "AGRI SUPPLIES", "LEISURE GROUP",
    "PRECISION TOOLS", "HARDWARE", "DIGITAL WORKS", "BAKERY SUPPLIES",
    "FREIGHT SERVICES", "FASHION HOUSE", "AUTO PARTS", "GROCERS CO-OP",
    "MARINE SUPPLIES", "ELECTRICALS", "MEDICAL TRADING", "STORAGE PTE LTD",
    "FOODS PTE LTD", "SYSTEMS PTE LTD",
)


class EngineError(RuntimeError):
    """The local COBOL toolchain is missing or refused to compile."""


# --------------------------------------------------------------------- toolchain

def find_cobc() -> Path | None:
    """Locate a usable ``cobc``: ``$COBC``, ``PATH``, then the isolated build."""
    override = os.environ.get("COBC")
    if override:
        candidate = Path(override)
        if candidate.is_file():
            return candidate
        found = shutil.which(override)
        if found:
            return Path(found)
    found = shutil.which("cobc")
    if found:
        return Path(found)
    prefixes = (
        Path(os.environ.get("GNUBOL_PREFIX", "/tmp/gcb-build/install")),
        Path.home() / ".local" / "gnucobol",
    )
    for prefix in prefixes:
        candidate = prefix / "bin" / "cobc"
        if candidate.is_file():
            return candidate
    return None


def cobc_env(cobc: Path) -> dict[str, str]:
    """Environment that lets the toolchain and its programs find ``libcob``."""
    env = dict(os.environ)
    libdir = cobc.resolve().parent.parent / "lib"
    if not libdir.is_dir():
        return env
    for key in ("DYLD_FALLBACK_LIBRARY_PATH", "LD_LIBRARY_PATH"):
        existing = [p for p in env.get(key, "").split(os.pathsep) if p]
        if str(libdir) not in existing:
            env[key] = os.pathsep.join([str(libdir), *existing])
    return env


def cobc_version(cobc: Path) -> str:
    try:
        proc = subprocess.run([str(cobc), "--version"], capture_output=True, text=True)
    except OSError:
        return "unknown"
    return proc.stdout.splitlines()[0].strip() if proc.stdout else "unknown"


def compile_legacy(cobc: Path, out_dir: Path) -> tuple[Path, float]:
    """Compile the legacy program once; return its path and the compile time."""
    out_dir.mkdir(parents=True, exist_ok=True)
    binary = out_dir / "legacy-bank"
    command = [str(cobc), "-x", "-free", "-o", str(binary), str(LEGACY_SOURCE)]
    started = time.perf_counter()
    proc = subprocess.run(command, capture_output=True, text=True, env=cobc_env(cobc))
    seconds = time.perf_counter() - started
    if proc.returncode != 0:
        raise EngineError(
            "cobc failed to compile legacy/bank.cob:\n" + (proc.stdout or "") + (proc.stderr or "")
        )
    return binary, seconds


# ---------------------------------------------------------------------- fixtures

def opening_balance_cents(account_index: int) -> int:
    """Deterministic, spread-out opening balance in cents (PIC 9(12) safe)."""
    return 50_000 + (account_index * 2_654_435_761) % 9_000_000


def holder_for(account_index: int) -> str:
    prefix = PREFIXES[(account_index - 1) % len(PREFIXES)]
    suffix = SUFFIXES[((account_index - 1) // len(PREFIXES)) % len(SUFFIXES)]
    return f"{prefix} {suffix}"


def product_for(account_index: int) -> str:
    return "CURRENT" if account_index % 2 else "SAVINGS"


def replay(balances: dict[int, int], operations: list[dict]) -> tuple[dict[int, int], list[dict], int, int]:
    """Mirror the batch's accept/reject rules to label each queued row.

    The COBOL program remains the authority for the counts; this deterministic
    replay only explains *which* rows it accepted, and is used to cross-check it.
    """
    ledger = dict(balances)
    rows: list[dict] = []
    processed = rejected = 0
    for seq, op in enumerate(operations, start=1):
        kind, source, target, amount = op["kind"], op["source"], op["target"], op["amount_cents"]
        reason = None
        if amount <= 0:
            reason = "amount not positive"
        elif kind not in ("D", "W", "T"):
            reason = "unknown operation code"
        elif source not in ledger:
            reason = "source account not found"
        elif kind == "T" and target not in ledger:
            reason = "destination account not found"
        elif kind == "T" and source == target:
            reason = "source and destination equal"
        elif kind != "D" and ledger[source] < amount:
            reason = "insufficient funds"
        if reason is None:
            ledger[source] += amount if kind == "D" else -amount
            if kind == "T":
                ledger[target] += amount
            processed += 1
        else:
            rejected += 1
        rows.append(
            {
                "seq": seq,
                "kind": kind,
                "source": source,
                "target": target,
                "amount_cents": amount,
                "status": "POSTED" if reason is None else "REJECTED",
                "reason": reason,
                "edge": bool(op.get("edge")),
                "line": f"{kind}|{source:08d}|{target:08d}|{amount:012d}",
            }
        )
    return ledger, rows, processed, rejected


def generate_warehouse(name: str, seed: int) -> dict:
    """Build a deterministic warehouse: flat-file bytes plus display metadata."""
    spec = WAREHOUSES[name]
    count, operations_count = spec["accounts"], spec["operations"]

    balances = {index: opening_balance_cents(index) for index in range(1, count + 1)}
    accounts_bytes = "".join(f"{index:08d}|{cents:012d}\n" for index, cents in balances.items())

    rng = random.Random(seed)
    operations: list[dict] = []
    for index in range(operations_count):
        kind = "DWT"[index % 3]
        source = rng.randint(1, count)
        target = rng.randint(1, count)
        if target == source:
            target = source % count + 1
        operations.append(
            {
                "kind": kind,
                "source": source,
                "target": target,
                "amount_cents": rng.randint(1, 500) * 25,
            }
        )
    # Three operations pinned to the rejection paths the batch documents.
    operations.append({"kind": "W", "source": 1, "target": 0, "amount_cents": 99_999_999, "edge": True})
    operations.append({"kind": "T", "source": 1, "target": count + 1, "amount_cents": 1, "edge": True})
    operations.append({"kind": "T", "source": 1, "target": 1, "amount_cents": 1, "edge": True})

    operations_bytes = "".join(
        f"{op['kind']}|{op['source']:08d}|{op['target']:08d}|{op['amount_cents']:012d}\n"
        for op in operations
    )
    digest = hashlib.sha256()
    digest.update(b"accounts.dat")
    digest.update(accounts_bytes.encode())
    digest.update(b"operations.dat")
    digest.update(operations_bytes.encode())

    closing, rows, predicted_processed, predicted_rejected = replay(balances, operations)
    return {
        "name": name,
        "accounts": count,
        "operations": operations_count,
        "edge_operations": EDGE_CASE_COUNT,
        "seed": seed,
        "opening_balances": balances,
        "closing_balances": closing,
        "accounts_bytes": accounts_bytes,
        "operations_bytes": operations_bytes,
        "rows": rows,
        "predicted": {"processed": predicted_processed, "rejected": predicted_rejected},
        "digest": digest.hexdigest(),
    }


# ----------------------------------------------------------------------- session

class Session:
    """Holds the operator session: compiled engine, current ledger, job journal."""

    def __init__(self, binary: Path | None, compile_seconds: float | None, engine_note: str) -> None:
        self.lock = threading.RLock()
        self.id = uuid.uuid4().hex[:6].upper()
        self.opened_at = dt.datetime.now(dt.timezone.utc)
        self.binary = binary
        self.compile_seconds = compile_seconds
        self.engine_note = engine_note
        self.cobc = None
        self.cobc_version = None
        self._warehouses: dict[str, dict] = {}
        self.warehouse = "STANDARD"
        self.seed = DEFAULT_SEED
        self.ledger: dict[int, int] = {}
        self.ledger_state = "OPENING"
        self.job: dict | None = None
        self.runs: list[dict] = []
        self._load_warehouse("STANDARD", DEFAULT_SEED)

    # ------------------------------------------------------------------ helpers

    def warehouse_data(self, name: str, seed: int) -> dict:
        key = f"{name}:{seed}"
        if key not in self._warehouses:
            self._warehouses[key] = generate_warehouse(name, seed)
        return self._warehouses[key]

    def _load_warehouse(self, name: str, seed: int) -> None:
        data = self.warehouse_data(name, seed)
        self.warehouse = name
        self.seed = seed
        self.ledger = dict(data["opening_balances"])
        self.ledger_state = "OPENING"

    # -------------------------------------------------------------------- views

    def summary(self) -> dict:
        data = self.warehouse_data(self.warehouse, self.seed)
        balances = list(self.ledger.values())
        return {
            "session": self.id,
            "bank": "BBS SG BANK",
            "warehouse": self.warehouse,
            "warehouses": WAREHOUSES,
            "seed": self.seed,
            "account_count": data["accounts"],
            "operation_count": data["operations"],
            "edge_operations": data["edge_operations"],
            "fixture_digest": data["digest"],
            "ledger_total_cents": sum(balances or [0]),
            "opening_total_cents": sum(data["opening_balances"].values()),
            "ledger_state": self.ledger_state,
            "last_job": self.job["id"] if self.job else None,
            "runs": len(self.runs),
            "engine": {
                "available": self.binary is not None,
                "path": str(self.binary) if self.binary else None,
                "cobc": str(self.cobc) if self.cobc else None,
                "cobc_version": self.cobc_version,
                "source": "legacy/bank.cob",
                "compile_seconds": round(self.compile_seconds, 3) if self.compile_seconds is not None else None,
                "note": self.engine_note,
            },
            "python": sys.version.split()[0],
            "disclosure": DISCLOSURE,
        }

    def accounts_page(self, page: int, size: int) -> dict:
        data = self.warehouse_data(self.warehouse, self.seed)
        movements: dict[int, int] = {}
        for row in data["rows"]:
            movements[row["source"]] = movements.get(row["source"], 0) + 1
            if row["kind"] == "T":
                movements[row["target"]] = movements.get(row["target"], 0) + 1
        ids = sorted(data["opening_balances"])
        pages = max(1, (len(ids) + size - 1) // size)
        page = max(0, min(page, pages - 1))
        window = ids[page * size : page * size + size]
        rows = [
            {
                "id": f"{account:08d}",
                "name": holder_for(account),
                "product": product_for(account),
                "opening_cents": data["opening_balances"][account],
                "balance_cents": self.ledger.get(account, data["opening_balances"][account]),
                "movements": movements.get(account, 0),
            }
            for account in window
        ]
        return {
            "page": page,
            "size": size,
            "total": len(ids),
            "total_pages": pages,
            "ledger_state": self.ledger_state,
            "ledger_total_cents": sum(self.ledger.values()),
            "opening_total_cents": sum(data["opening_balances"].values()),
            "rows": rows,
        }

    def operations_page(self, page: int, size: int) -> dict:
        data = self.warehouse_data(self.warehouse, self.seed)
        rows = data["rows"]
        pages = max(1, (len(rows) + size - 1) // size)
        page = max(0, min(page, pages - 1))
        posted = sum(1 for row in rows if row["status"] == "POSTED")
        return {
            "page": page,
            "size": size,
            "total": len(rows),
            "total_pages": pages,
            "counts": {
                "total": len(rows),
                "posted": posted,
                "rejected": len(rows) - posted,
            },
            "ledger_state": self.ledger_state,
            "rows": rows[page * size : page * size + size],
        }

    def journal_view(self) -> dict:
        return {"runs": list(reversed(self.runs))[:12]}

    # -------------------------------------------------------------------- batch

    def start_batch(self, warehouse: str, seed: int, verify: bool, mode: str) -> dict:
        if warehouse not in WAREHOUSES:
            raise ValueError(f"unknown warehouse {warehouse!r}")
        if mode not in ("cobol", "simulated"):
            raise ValueError(f"unknown mode {mode!r}")
        if mode == "cobol" and self.binary is None:
            raise EngineError(
                "no local GnuCOBOL (cobc) is available; run scripts/get_cobc.sh "
                "or set $COBC, then restart this server"
            )

        with self.lock:
            data = self.warehouse_data(warehouse, seed)
            self.warehouse, self.seed = warehouse, seed
            self.ledger = dict(data["opening_balances"])
            self.ledger_state = "OPENING"
            job = {
                "id": f"NB{dt.datetime.now(dt.timezone.utc):%y%m%d%H%M%S}",
                "state": "running",
                "phase": "SUBMITTED",
                "mode": mode,
                "warehouse": warehouse,
                "accounts": data["accounts"],
                "operations": data["operations"],
                "edge_operations": data["edge_operations"],
                "seed": seed,
                "verify": verify,
                "started_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
                "elapsed_s": 0.0,
                "journal": [],
                "metrics": None,
                "rc": None,
                "seconds": None,
                "digest_before": data["digest"],
                "digest_after": None,
                "prediction": {
                    "processed": data["predicted"]["processed"],
                    "rejected": data["predicted"]["rejected"],
                    "matches": None,
                },
                "verify_result": None,
                "error": None,
                "spool": self._spool_display(data),
                "spool_simulated": True,
            }
            self.job = job
            threading.Thread(
                target=self._run_job, args=(job, data), name=f"batch-{job['id']}", daemon=True
            ).start()
            return job

    @staticmethod
    def _spool_display(data: dict, limit: int = 48) -> list[str]:
        """Rows for the terminal's spool window.

        This is a *display* rendering of the queue, not job output: the COBOL
        program prints only its three summary counters, so the terminal labels
        this window SIMULATED.
        """
        spool = []
        for row in data["rows"][:limit]:
            spool.append(
                f"#{row['seq']:05d} {row['kind']} {row['source']:08d} "
                f"{row['target']:08d} {row['amount_cents']:012d}"
            )
        if len(data["rows"]) > limit:
            spool.append(f"... {len(data['rows']) - limit} FURTHER ROWS IN QUEUE")
        return spool

    def _log(self, job: dict, line: str, tone: str = "info") -> None:
        with self.lock:
            job["journal"].append(
                {"seq": len(job["journal"]) + 1, "t": f"{dt.datetime.now():%H:%M:%S}", "line": line, "tone": tone}
            )

    def _run_job(self, job: dict, data: dict) -> None:
        run_dir = Path(tempfile.mkdtemp(prefix="bbs-sgbank-run-"))
        started = dt.datetime.now(dt.timezone.utc)
        try:
            (run_dir / "accounts.dat").write_text(data["accounts_bytes"])
            (run_dir / "operations.dat").write_text(data["operations_bytes"])

            self._log(job, f"JOB {job['id']} SUBMITTED -- BBS SG BANK NBATCH")
            self._log(
                job,
                f"WAREHOUSE={job['warehouse']} ACCOUNTS={job['accounts']} "
                f"OPERATIONS={job['operations']} (+{job['edge_operations']} EDGE) SEED={job['seed']}",
            )
            self._log(job, f"FIXTURE SHA256={job['digest_before']}", "dim")
            self._log(job, "STEP010 DELETE/REDEFINE ACCOUNTS.DAT OPERATIONS.DAT", "dim")

            if job["mode"] == "simulated":
                self._run_simulated(job, data, run_dir, started)
            else:
                self._run_cobol(job, data, run_dir, started)

            if job["verify"] and not job.get("failed"):
                self._verify(job, data)

            if job.get("failed"):
                job["state"] = "error"
                job["error"] = job.get("error") or "batch step failed"
            else:
                job["state"] = "done"
                self._log(job, f"JOB {job['id']} COMPLETE", "ok")
        except Exception as exc:  # surface any engine problem on the terminal
            job["state"] = "error"
            job["error"] = f"{type(exc).__name__}: {exc}"
            self._log(job, f"JOB ABENDED -- {job['error']}", "err")
        finally:
            job["elapsed_s"] = round((dt.datetime.now(dt.timezone.utc) - started).total_seconds(), 3)
            job["finished_at"] = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
            with self.lock:
                self.runs.append(
                    {
                        "id": job["id"],
                        "finished_at": job["finished_at"],
                        "warehouse": job["warehouse"],
                        "accounts": job["accounts"],
                        "operations": job["operations"],
                        "mode": job["mode"],
                        "seconds": job["seconds"],
                        "metrics": job["metrics"],
                        "rc": job["rc"],
                        "state": job["state"],
                        "verify": (job["verify_result"] or {}).get("ok"),
                    }
                )
                self.runs = self.runs[-40:]
            shutil.rmtree(run_dir, ignore_errors=True)

    def _run_cobol(self, job: dict, data: dict, run_dir: Path, started: dt.datetime) -> None:
        self._log(job, f"COBC={self.cobc} ({self.cobc_version})", "dim")
        self._log(job, f"COMPILE legacy/bank.cob -> {self.binary}", "dim")
        if self.compile_seconds is not None:
            self._log(job, f"COMPILE REUSED (cached binary, {self.compile_seconds:.3f}s at start-up)", "dim")
        self._log(job, "STEP010 EXEC PGM=LEGACY-BANK PARM='NBATCH'")
        job["phase"] = "STEP010 EXEC"

        clock = time.perf_counter()
        proc = subprocess.run(
            [str(self.binary)],
            cwd=str(run_dir),
            capture_output=True,
            text=True,
            env=cobc_env(self.cobc),
        )
        seconds = time.perf_counter() - clock
        job["seconds"] = round(seconds, 3)
        job["rc"] = proc.returncode

        for line in proc.stdout.splitlines():
            self._log(job, f"OUT> {line}", "ok" if "=" in line else "info")
        for line in proc.stderr.splitlines():
            self._log(job, f"ERR> {line}", "err")

        metrics = {}
        for line in proc.stdout.splitlines():
            if "=" in line:
                key, _, value = line.partition("=")
                if value.strip().isdigit():
                    metrics[key.strip()] = int(value.strip())
        job["metrics"] = metrics or None

        accounts_after = (run_dir / "accounts.dat").read_bytes()
        digest = hashlib.sha256()
        digest.update(b"accounts.dat")
        digest.update(accounts_after)
        job["digest_after"] = digest.hexdigest()

        posted = metrics.get("PROCESSED")
        rejected = metrics.get("REJECTED")
        if posted is not None:
            job["prediction"]["matches"] = (
                posted == job["prediction"]["processed"] and rejected == job["prediction"]["rejected"]
            )

        with self.lock:
            self.ledger = {}
            for text in accounts_after.decode().splitlines():
                account_id, cents = text.split("|")
                self.ledger[int(account_id)] = int(cents)
            self.ledger_state = f"POSTED {job['id']}"

        self._log(job, f"STEP010 ENDED RC={proc.returncode} ELAPSED={seconds:.3f}s (wall clock, real)")
        if proc.returncode == 0:
            self._log(job, "STEP010 RC=0 -- MASTER FILE REWRITTEN IN PLACE")
        else:
            self._log(job, "STEP010 RC<>0 -- SEE ERR> LINES ABOVE", "warn")
            job["failed"] = True
            job["error"] = f"legacy batch exited with RC={proc.returncode}"
        job["phase"] = "STEP010 ENDED"

    def _run_simulated(self, job: dict, data: dict, run_dir: Path, started: dt.datetime) -> None:
        """Explicit, labelled fallback. Uses no COBOL and fabricates nothing."""
        self._log(job, "*** SIMULATED RUN -- NO COBOL JOB EXECUTED ***", "warn")
        job["phase"] = "SIMULATED"
        self._log(job, "ENGINE=js-replay (deterministic rules only, not the legacy program)", "warn")
        pace = 0.02 if job["warehouse"] == "SMALL" else 0.05
        total = min(job["accounts"] * job["operations"], 600)
        for step in range(0, max(total, 12), max(1, total // 12)):
            time.sleep(pace)
            job["elapsed_s"] = round((dt.datetime.now(dt.timezone.utc) - started).total_seconds(), 3)
            self._log(job, f"SIMULATED heartbeat -- display only ({job['elapsed_s']:.2f}s)", "dim")
        processed, rejected = data["predicted"]["processed"], data["predicted"]["rejected"]
        total_cents = sum(data["closing_balances"].values())
        job["metrics"] = {"PROCESSED": processed, "REJECTED": rejected, "TOTAL_CENTS": total_cents}
        job["rc"] = 0
        job["seconds"] = 0.0
        job["digest_after"] = data["digest"]
        job["prediction"]["matches"] = True
        with self.lock:
            self.ledger = dict(data["closing_balances"])
            self.ledger_state = f"REPLAY {job['id']} (simulated)"
        self._log(job, f"OUT> PROCESSED={processed:08d}", "ok")
        self._log(job, f"OUT> REJECTED={rejected:08d}", "ok")
        self._log(job, f"OUT> TOTAL_CENTS={total_cents:016d}", "ok")
        self._log(job, "SIMULATION COMPLETE -- no real batch elapsed time to report", "warn")
        job["phase"] = "SIMULATION ENDED"

    def _verify(self, job: dict, data: dict) -> None:
        """Re-run the same fixture through modern/bank.py and compare results."""
        self._log(job, "STEP020 VERIFY -- modern/bank.py parity check")
        job["phase"] = "STEP020 VERIFY"
        with tempfile.TemporaryDirectory(prefix="bbs-sgbank-modern-") as tmp:
            work = Path(tmp)
            (work / "accounts.dat").write_text(data["accounts_bytes"])
            (work / "operations.dat").write_text(data["operations_bytes"])
            proc = subprocess.run(
                [sys.executable or "python3", str(MODERN_SCRIPT)],
                cwd=str(work),
                capture_output=True,
                text=True,
            )
        metrics = {}
        for line in proc.stdout.splitlines():
            if "=" in line:
                key, _, value = line.partition("=")
                if value.strip().isdigit():
                    metrics[key.strip()] = int(value.strip())
        ok = proc.returncode == 0 and job["metrics"] == metrics
        job["verify_result"] = {
            "ok": ok,
            "rc": proc.returncode,
            "metrics": metrics or None,
            "engine": "modern/bank.py",
        }
        if ok:
            self._log(job, "STEP020 VERIFY PASS -- metrics identical to modern/bank.py", "ok")
        else:
            self._log(
                job,
                f"STEP020 VERIFY FAIL -- legacy={job['metrics']} modern={metrics or None}",
                "warn",
            )


# ---------------------------------------------------------------------- HTTP API

SESSION: Session


class Server(ThreadingHTTPServer):
    """Threaded loopback server; a browser dropping a keep-alive socket is normal."""

    daemon_threads = True

    def handle_error(self, request, client_address) -> None:
        error = sys.exc_info()[1]
        if isinstance(error, (ConnectionResetError, BrokenPipeError)):
            return
        super().handle_error(request, client_address)


class Handler(BaseHTTPRequestHandler):
    server_version = "BbsSgBankLegacyUI/1.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args) -> None:  # keep the console readable
        return

    # ------------------------------------------------------------------ plumbing
    def _send(self, payload, status: int = 200, content_type: str = "application/json") -> None:
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        # Allow terminal.html to be opened from file:// and pointed at this engine.
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _error(self, message: str, status: int = 400) -> None:
        self._send({"error": message}, status)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        path = parsed.path.rstrip("/") or "/"
        try:
            if path == "/":
                if not TERMINAL_HTML.is_file():
                    return self._error("terminal.html is missing", 500)
                return self._send(TERMINAL_HTML.read_bytes(), content_type="text/html; charset=utf-8")
            if path == "/api/status":
                with SESSION.lock:
                    return self._send(SESSION.summary())
            if path == "/api/accounts":
                page = int(query.get("page", ["0"])[0])
                size = max(1, min(int(query.get("size", ["14"])[0]), 200))
                with SESSION.lock:
                    return self._send(SESSION.accounts_page(page, size))
            if path == "/api/operations":
                page = int(query.get("page", ["0"])[0])
                size = max(1, min(int(query.get("size", ["14"])[0]), 200))
                with SESSION.lock:
                    return self._send(SESSION.operations_page(page, size))
            if path == "/api/batch":
                with SESSION.lock:
                    if not SESSION.job:
                        return self._send({"state": "idle"})
                    return self._send(SESSION.job)
            if path == "/api/journal":
                with SESSION.lock:
                    return self._send(SESSION.journal_view())
            return self._error("not found", 404)
        except ValueError as exc:
            return self._error(str(exc), 400)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw or b"{}")
        except json.JSONDecodeError as exc:
            return self._error(f"invalid JSON body: {exc}", 400)
        try:
            if parsed.path.rstrip("/") == "/api/batch":
                warehouse = str(payload.get("warehouse", "STANDARD")).upper()
                seed = int(payload.get("seed", DEFAULT_SEED))
                mode = str(payload.get("mode", "cobol")).lower()
                verify = bool(payload.get("verify", True))
                with SESSION.lock:
                    job = SESSION.start_batch(warehouse, seed, verify, mode)
                return self._send(job, 202)
            if parsed.path.rstrip("/") == "/api/reset":
                with SESSION.lock:
                    SESSION._load_warehouse(SESSION.warehouse, SESSION.seed)
                    SESSION.job = None
                    return self._send(SESSION.summary())
            return self._error("not found", 404)
        except EngineError as exc:
            return self._error(str(exc), 503)
        except ValueError as exc:
            return self._error(str(exc), 400)


def build_session() -> Session:
    cobc = find_cobc()
    if cobc is None:
        return Session(None, None, "cobc not found; run scripts/get_cobc.sh or set $COBC")
    try:
        binary, seconds = compile_legacy(cobc, Path(tempfile.mkdtemp(prefix="bbs-sgbank-bin-")))
    except EngineError as exc:
        session = Session(None, None, f"compile failed: {exc}")
        session.cobc = cobc
        session.cobc_version = cobc_version(cobc)
        return session
    session = Session(binary, seconds, f"compiled legacy/bank.cob with {cobc_version(cobc)}")
    session.cobc = cobc
    session.cobc_version = cobc_version(cobc)
    return session


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"loopback port (default {DEFAULT_PORT})")
    parser.add_argument("--host", default="127.0.0.1", help="bind address (default 127.0.0.1)")
    args = parser.parse_args(argv)

    global SESSION
    SESSION = build_session()
    engine = SESSION.summary()["engine"]
    print("BBS SG BANK -- legacy operations terminal (synthetic demo)")
    print(f"  engine: {'READY  ' + str(engine['path']) if engine['available'] else 'UNAVAILABLE -- ' + engine['note']}")
    print(f"  source: {LEGACY_SOURCE}")
    server = Server((args.host, args.port), Handler)
    print(f"  serving: http://{args.host}:{args.port}/  (Ctrl-C to stop)")
    print("  All accounts, balances and operations are generated synthetic data.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nterminal closed")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
