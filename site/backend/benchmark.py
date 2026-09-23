"""Benchmark harness for the legacy and modern batch engines.

The site measures the same way the CLI benchmark does.  When the shared helpers
in ``scripts/harness.py`` are importable they are used directly, so toolchain
discovery, fixtures and process plumbing exist in one place; a small built-in
fallback keeps the page working if that module is unavailable or changes shape.

Only measured numbers are reported.  When no ``cobc`` can be found the legacy
side is reported as unavailable rather than estimated.
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import os
import platform
import random
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODERN_ENGINE = ROOT / "modern" / "bank.py"
LEGACY_SOURCE = ROOT / "legacy" / "bank.cob"
HARNESS_SCRIPT = ROOT / "scripts" / "harness.py"

DEFAULT_ACCOUNTS = 1200
DEFAULT_OPERATIONS = 400
DEFAULT_SEED = 20260923
DEFAULT_REPEATS = 3
DEFAULT_WARMUP = 1
MAX_ACCOUNTS = 50_000
MAX_OPERATIONS = 50_000
MAX_REPEATS = 15
CACHE_TTL_SECONDS = 300

METRICS_RE = re.compile(r"(PROCESSED|REJECTED|TOTAL_CENTS)=(\d+)")
ACCOUNT_BALANCE_CENTS = 100_000
EDGE_CASE_COUNT = 3
INSTALL_HINT = (
    "cobc not found. Run scripts/get_cobc.sh to build an isolated GnuCOBOL under /tmp "
    "(no root, no global changes), or set $COBC to an existing cobc."
)

_cache: dict[tuple, tuple[float, dict]] = {}
_cache_lock = threading.Lock()


class BenchmarkError(ValueError):
    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.status = status


# --------------------------------------------------------------- shared helpers


def _load_shared_harness():
    """Import scripts/harness.py, or return None when it is not usable."""
    try:
        spec = importlib.util.spec_from_file_location("site_shared_harness", HARNESS_SCRIPT)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        sys.modules.setdefault("site_shared_harness", module)
        spec.loader.exec_module(module)
    except Exception:  # noqa: BLE001 - any failure just means "use the fallback"
        return None
    required = (
        "find_cobc",
        "cobc_env",
        "compile_legacy",
        "legacy_command",
        "modern_command",
        "run_batch",
        "build_fixture",
        "seed_batch",
    )
    return module if all(hasattr(module, name) for name in required) else None


class _FallbackHarness:
    """Minimal stand-in for scripts/harness.py so the page never breaks."""

    EDGE_CASE_COUNT = EDGE_CASE_COUNT
    INSTALL_HINT = INSTALL_HINT

    @staticmethod
    def find_cobc() -> Path | None:
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
        prefix = Path(os.environ.get("GNUBOL_PREFIX", "/tmp/gcb-build/install"))
        for candidate in (prefix / "bin" / "cobc", Path.home() / ".local" / "gnucobol" / "bin" / "cobc"):
            if candidate.is_file():
                return candidate
        return None

    @staticmethod
    def cobc_env(cobc: Path) -> dict:
        env = dict(os.environ)
        libdir = cobc.resolve().parent.parent / "lib"
        if libdir.is_dir():
            for key in ("DYLD_FALLBACK_LIBRARY_PATH", "LD_LIBRARY_PATH"):
                existing = [part for part in env.get(key, "").split(os.pathsep) if part]
                if str(libdir) not in existing:
                    env[key] = os.pathsep.join([str(libdir), *existing])
        return env

    @classmethod
    def compile_legacy(cls, cobc: Path, out_dir: Path) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        binary = out_dir / "legacy-bank"
        proc = subprocess.run(
            [str(cobc), "-x", "-free", "-o", str(binary), str(LEGACY_SOURCE)],
            capture_output=True,
            text=True,
            env=cls.cobc_env(cobc),
        )
        if proc.returncode != 0:
            raise RuntimeError("cobc failed to compile legacy/bank.cob: " + (proc.stderr or proc.stdout))
        return binary

    @staticmethod
    def legacy_command(binary: Path) -> list[str]:
        return [str(binary)]

    @staticmethod
    def modern_command() -> list[str]:
        return [sys.executable or "python3", str(MODERN_ENGINE)]

    @staticmethod
    def run_batch(command: list[str], directory: Path, env=None):
        started = time.perf_counter()
        proc = subprocess.run(command, cwd=str(directory), capture_output=True, text=True, env=env)
        seconds = time.perf_counter() - started
        accounts_path = Path(directory) / "accounts.dat"
        accounts = accounts_path.read_bytes() if accounts_path.exists() else None
        metrics = {key: int(value) for key, value in METRICS_RE.findall(proc.stdout)}
        outcome = type("Outcome", (), {})
        outcome.returncode = proc.returncode
        outcome.seconds = seconds
        outcome.stdout = proc.stdout
        outcome.stderr = proc.stderr
        outcome.metrics = metrics
        outcome.accounts = accounts
        return outcome

    @staticmethod
    def build_fixture(directory: Path, accounts: int, operations: int, seed: int = DEFAULT_SEED) -> dict:
        if accounts < 2:
            raise ValueError("accounts must be >= 2")
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        rng = random.Random(seed)
        (directory / "accounts.dat").write_text(
            "".join(f"{index:08d}|{ACCOUNT_BALANCE_CENTS:012d}\n" for index in range(1, accounts + 1))
        )
        lines = []
        for index in range(operations):
            source = rng.randint(1, accounts)
            target = rng.randint(1, accounts)
            if target == source:
                target = source % accounts + 1
            lines.append(f"{'DWT'[index % 3]}|{source:08d}|{target:08d}|{(index % 73 + 1) * 25:012d}\n")
        lines += [
            f"W|{1:08d}|{0:08d}|{99_999_999:012d}\n",
            f"T|{1:08d}|{accounts + 1:08d}|{1:012d}\n",
            f"T|{1:08d}|{1:08d}|{1:012d}\n",
        ]
        (directory / "operations.dat").write_text("".join(lines))
        return {"accounts": accounts, "operations": operations, "seed": seed, "edge_operations": EDGE_CASE_COUNT}

    @staticmethod
    def seed_batch(source_dir: Path, target_dir: Path) -> None:
        target_dir.mkdir(parents=True, exist_ok=True)
        for name in ("accounts.dat", "operations.dat"):
            shutil.copyfile(Path(source_dir) / name, Path(target_dir) / name)
        stale = Path(target_dir) / "accounts.tmp"
        if stale.exists():
            stale.unlink()


_shared_cache: object | None = None
_shared_loaded = False


def _shared_harness():
    """Load the shared helpers once; None means the built-in fallback is in use."""
    global _shared_cache, _shared_loaded
    if not _shared_loaded:
        _shared_cache = _load_shared_harness()
        _shared_loaded = True
    return _shared_cache


def _harness():
    return _shared_harness() or _FallbackHarness


def _harness_name() -> str:
    return "scripts/harness.py" if _shared_harness() is not None else "site/backend/benchmark.py (built-in fallback)"


# ------------------------------------------------------------------ environment


def environment() -> dict:
    """Report what this machine can actually measure."""
    harness = _harness()
    cobc = harness.find_cobc()
    version = None
    if cobc:
        try:
            probe = subprocess.run([str(cobc), "--version"], capture_output=True, text=True, timeout=15, check=False)
            version = probe.stdout.splitlines()[0].strip() if probe.stdout else None
        except (OSError, subprocess.SubprocessError):  # pragma: no cover - environment dependent
            version = None
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "cobc_path": str(cobc) if cobc else None,
        "cobc_version": version,
        "legacy_measurable": cobc is not None,
        "modern_engine": str(MODERN_ENGINE.relative_to(ROOT)),
        "legacy_source": str(LEGACY_SOURCE.relative_to(ROOT)),
        "harness": _harness_name(),
    }


# ------------------------------------------------------------------- measuring


def _validate(accounts: int, operations: int, repeats: int, warmup: int) -> None:
    if not 2 <= accounts <= MAX_ACCOUNTS:
        raise BenchmarkError(f"accounts must be between 2 and {MAX_ACCOUNTS}")
    if not 0 <= operations <= MAX_OPERATIONS:
        raise BenchmarkError(f"operations must be between 0 and {MAX_OPERATIONS}")
    if not 1 <= repeats <= MAX_REPEATS:
        raise BenchmarkError(f"repeats must be between 1 and {MAX_REPEATS}")
    if not 0 <= warmup <= MAX_REPEATS:
        raise BenchmarkError(f"warmup must be between 0 and {MAX_REPEATS}")


def _unavailable(reason: str) -> dict:
    return {"available": False, "seconds": None, "operations_per_second": None, "reason": reason}


def _engine_report(outcome, rows: int) -> dict:
    return {
        "available": True,
        "seconds": outcome["median"],
        "median": outcome["median"],
        "min": outcome["min"],
        "samples": outcome["samples"],
        "operations_per_second": round(rows / outcome["median"], 1) if outcome["median"] else None,
        **outcome["metrics"],
    }


def run_benchmark(
    accounts: int = DEFAULT_ACCOUNTS,
    operations: int = DEFAULT_OPERATIONS,
    *,
    repeats: int = DEFAULT_REPEATS,
    warmup: int = DEFAULT_WARMUP,
    seed: int = DEFAULT_SEED,
    fresh: bool = False,
) -> dict:
    """Measure both engines on identical fixtures. Returns only measured values."""
    accounts, operations, repeats, warmup, seed = (
        int(accounts),
        int(operations),
        int(repeats),
        int(warmup),
        int(seed),
    )
    _validate(accounts, operations, repeats, warmup)

    key = (accounts, operations, repeats, warmup, seed)
    with _cache_lock:
        cached = _cache.get(key)
        if cached and not fresh and time.time() - cached[0] < CACHE_TTL_SECONDS:
            return {**cached[1], "cached": True}

    result = _measure(accounts, operations, repeats, warmup, seed)
    with _cache_lock:
        _cache[key] = (time.time(), result)
    return {**result, "cached": False}


def _measure(accounts: int, operations: int, repeats: int, warmup: int, seed: int) -> dict:
    harness = _harness()
    rows = operations + EDGE_CASE_COUNT
    env_info = environment()
    report: dict = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "params": {
            "accounts": accounts,
            "operations": operations,
            "fixture_rows": rows,
            "edge_cases": EDGE_CASE_COUNT,
            "repeats": repeats,
            "warmup": warmup,
            "seed": seed,
        },
        "environment": env_info,
        "modern": None,
        "legacy": None,
        "speedup": None,
        "outputs_identical": None,
        "notes": [
            "Both engines run as separate processes on identical, deterministic fixtures; inputs are "
            "restored from the pristine copy before every timed run.",
            "Timings are wall clock on this host and include each program's process start-up. "
            f"Median of {repeats} timed run(s) after {warmup} warm-up run(s).",
        ],
    }

    cobc = harness.find_cobc()
    with tempfile.TemporaryDirectory(prefix="bbs-bench-") as scratch:
        root = Path(scratch)
        fixture, old, new = root / "fixture", root / "old", root / "new"
        meta = harness.build_fixture(fixture, accounts, operations, seed)
        if isinstance(meta, dict) and meta.get("digest"):
            report["fixture_digest"] = meta["digest"]
        harness.seed_batch(fixture, old)
        harness.seed_batch(fixture, new)

        legacy_command = None
        legacy_env = None
        compile_error = None
        if cobc is None:
            report["legacy"] = _unavailable(
                "No cobc was found on this machine, so the compiled legacy batch could not be timed. " + INSTALL_HINT
            )
        else:
            try:
                binary = harness.compile_legacy(cobc, root / "bin")
                legacy_command = harness.legacy_command(binary)
                legacy_env = harness.cobc_env(cobc)
            except Exception as exc:  # noqa: BLE001 - compile failures are reported, not raised
                compile_error = f"cobc could not compile legacy/bank.cob: {exc}"
                report["legacy"] = _unavailable(compile_error)

        modern_command = harness.modern_command()

        # Parity first: a speed-up without identical output is meaningless.
        harness.seed_batch(fixture, new)
        modern_ref = harness.run_batch(modern_command, new)
        legacy_ref = None
        if legacy_command is not None:
            harness.seed_batch(fixture, old)
            legacy_ref = harness.run_batch(legacy_command, old, legacy_env)

        if modern_ref.returncode != 0:
            report["modern"] = _unavailable(
                f"the modern engine exited {modern_ref.returncode}: {(modern_ref.stderr or '').strip()[:300]}"
            )
        else:
            modern_times: list[float] = []
            failed = None
            for index in range(warmup + repeats):
                harness.seed_batch(fixture, new)
                run = harness.run_batch(modern_command, new)
                if run.returncode != 0 or run.metrics != modern_ref.metrics:
                    failed = "the modern engine produced inconsistent results across runs"
                    break
                if index >= warmup:
                    modern_times.append(run.seconds)
            report["modern"] = (
                _unavailable(failed)
                if failed
                else _engine_report(
                    {
                        "median": statistics.median(modern_times),
                        "min": min(modern_times),
                        "samples": [round(value, 6) for value in modern_times],
                        "metrics": modern_ref.metrics,
                    },
                    rows,
                )
            )

        if legacy_command is not None and legacy_ref is not None:
            if legacy_ref.returncode != 0:
                report["legacy"] = _unavailable(
                    f"the compiled legacy batch exited {legacy_ref.returncode}: "
                    f"{(legacy_ref.stderr or '').strip()[:300]}"
                )
            elif report["modern"].get("available") and (
                legacy_ref.metrics != modern_ref.metrics or legacy_ref.accounts != modern_ref.accounts
            ):
                report["outputs_identical"] = False
                report["legacy"] = _unavailable("output parity with the modern engine failed, so no timing is reported")
                report["notes"].append(
                    "WARNING: the two engines disagreed on output, so no comparison is offered."
                )
            else:
                report["outputs_identical"] = True
                legacy_times: list[float] = []
                failed = None
                for index in range(warmup + repeats):
                    harness.seed_batch(fixture, old)
                    run = harness.run_batch(legacy_command, old, legacy_env)
                    if run.returncode != 0 or run.metrics != legacy_ref.metrics:
                        failed = "the legacy engine produced inconsistent results across runs"
                        break
                    if index >= warmup:
                        legacy_times.append(run.seconds)
                if failed:
                    report["legacy"] = _unavailable(failed)
                else:
                    legacy = _engine_report(
                        {
                            "median": statistics.median(legacy_times),
                            "min": min(legacy_times),
                            "samples": [round(value, 6) for value in legacy_times],
                            "metrics": legacy_ref.metrics,
                        },
                        rows,
                    )
                    legacy["engine"] = str(LEGACY_SOURCE.relative_to(ROOT))
                    report["legacy"] = legacy

        if isinstance(report["modern"], dict) and report["modern"].get("available"):
            report["modern"]["engine"] = str(MODERN_ENGINE.relative_to(ROOT))

        modern = report["modern"]
        legacy = report["legacy"]
        if modern and modern.get("available") and legacy and legacy.get("available"):
            report["speedup"] = round(legacy["median"] / modern["median"], 2) if modern["median"] else None

    report["notes"].append(
        "Legacy I/O shape is a property of the source, not a measurement: bank.cob re-reads the whole "
        "accounts file once per operation to validate and again to rewrite it, so its cost grows with "
        "accounts x operations while the modern engine stays linear in operations."
    )
    return report


if __name__ == "__main__":  # pragma: no cover - manual use
    import json

    print(json.dumps(run_benchmark(), indent=2))
