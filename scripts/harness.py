"""Shared helpers for exercising the legacy COBOL batch and the modern Python one.

GnuCOBOL's ``cobc`` is not installed system-wide in this environment: Homebrew's
``/opt/homebrew`` is read-only and there is no root, so ``brew install`` fails and
no global change is permitted. ``scripts/get_cobc.sh`` instead builds GnuCOBOL 3.2
from source into an isolated prefix (default ``/tmp/gcb-build/install``) using the
system compiler. :func:`find_cobc` locates that build, an explicit ``$COBC``, or a
``cobc`` already on ``PATH``.

Both ``benchmark.py`` and ``test_bank.py`` import this module so the toolchain
discovery, fixture generation and process plumbing exist in exactly one place.
"""

from __future__ import annotations

import hashlib
import os
import random
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import NamedTuple

REPO_ROOT = Path(__file__).resolve().parents[1]
LEGACY_SOURCE = REPO_ROOT / "legacy" / "bank.cob"
MODERN_SCRIPT = REPO_ROOT / "modern" / "bank.py"

# Isolated source build produced by scripts/get_cobc.sh.
GNUBOL_PREFIX = Path(os.environ.get("GNUBOL_PREFIX", "/tmp/gcb-build/install"))
SEARCH_PREFIXES = (GNUBOL_PREFIX, Path.home() / ".local" / "gnucobol")

# Fixture constants. Kept in the ledger's fixed-width domain: 8-digit ids and
# 12-digit amounts/balances, so legacy and modern stay byte-compatible.
ACCOUNT_BALANCE_CENTS = 100_000
DEFAULT_SEED = 20260923
EDGE_CASE_COUNT = 3

METRICS_RE = re.compile(r"(PROCESSED|REJECTED|TOTAL_CENTS)=(\d+)")

INSTALL_HINT = (
    "cobc not found. Run scripts/get_cobc.sh to build an isolated GnuCOBOL "
    "under /tmp (no root, no global changes), or set $COBC to an existing cobc."
)


class Result(NamedTuple):
    """Outcome of one batch process invocation."""

    returncode: int
    seconds: float
    stdout: str
    stderr: str
    metrics: dict[str, int]
    accounts: bytes | None


def find_cobc() -> Path | None:
    """Return a usable ``cobc`` path, or ``None`` when none can be found."""
    override = os.environ.get("COBC")
    if override:
        candidate = Path(override)
        if candidate.is_file():
            return candidate
        found = shutil.which(override)
        if found:
            return Path(found)
        print(f"warning: $COBC={override!r} is not executable; searching elsewhere", file=sys.stderr)
    found = shutil.which("cobc")
    if found:
        return Path(found)
    for prefix in SEARCH_PREFIXES:
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


def compile_legacy(cobc: Path, out_dir: Path, source: Path = LEGACY_SOURCE) -> Path:
    """Compile the legacy program once and return the executable path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    binary = out_dir / "legacy-bank"
    command = [str(cobc), "-x", "-free", "-o", str(binary), str(source)]
    proc = subprocess.run(command, capture_output=True, text=True, env=cobc_env(cobc))
    if proc.returncode != 0:
        raise RuntimeError(
            "cobc failed to compile the legacy program:\n"
            + (proc.stdout or "")
            + (proc.stderr or "")
        )
    return binary


def legacy_command(binary: Path) -> list[str]:
    """Command that runs the compiled legacy batch in its working directory."""
    return [str(binary)]


def modern_command() -> list[str]:
    """Command that runs the modern batch for a directory given as argv[1]."""
    return [sys.executable or "python3", str(MODERN_SCRIPT)]


def parse_metrics(stdout: str) -> dict[str, int]:
    """Extract the PROCESSED/REJECTED/TOTAL_CENTS summary from batch stdout."""
    return {key: int(value) for key, value in METRICS_RE.findall(stdout)}


def run_batch(
    command: list[str],
    directory: Path,
    env: dict[str, str] | None = None,
) -> Result:
    """Run one batch process, timing it and capturing its result and output file."""
    start = time.perf_counter()
    proc = subprocess.run(
        command, cwd=str(directory), capture_output=True, text=True, env=env
    )
    seconds = time.perf_counter() - start
    accounts_path = Path(directory) / "accounts.dat"
    accounts = accounts_path.read_bytes() if accounts_path.exists() else None
    return Result(proc.returncode, seconds, proc.stdout, proc.stderr, parse_metrics(proc.stdout), accounts)


def build_fixture(
    directory: Path,
    accounts: int,
    operations: int,
    seed: int = DEFAULT_SEED,
) -> dict[str, object]:
    """Materialise ``accounts.dat`` and ``operations.dat`` deterministically.

    Pure function of ``(accounts, operations, seed)``: identical arguments always
    produce byte-identical fixtures, so a recorded run is exactly reproducible.

    Every account opens at :data:`ACCOUNT_BALANCE_CENTS`. The generated operations
    cycle kinds ``D``/``W``/``T`` with small amounts; :data:`EDGE_CASE_COUNT` extra
    operations then pin the rejection paths (insufficient funds, missing
    destination, self-transfer). Returns metadata including a digest of both files.
    """
    if accounts < 2:
        raise ValueError("accounts must be >= 2 so transfers can pick a distinct target")
    if operations < 0:
        raise ValueError("operations must be >= 0")

    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)

    account_text = "".join(
        f"{i:08d}|{ACCOUNT_BALANCE_CENTS:012d}\n" for i in range(1, accounts + 1)
    )
    ops_lines: list[str] = []
    for i in range(operations):
        source = rng.randint(1, accounts)
        target = rng.randint(1, accounts)
        if target == source:
            target = source % accounts + 1
        ops_lines.append(f"{'DWT'[i % 3]}|{source:08d}|{target:08d}|{(i % 73 + 1) * 25:012d}\n")
    ops_lines += [
        f"W|{1:08d}|{0:08d}|{99_999_999:012d}\n",       # insufficient funds
        f"T|{1:08d}|{accounts + 1:08d}|{1:012d}\n",     # missing destination
        f"T|{1:08d}|{1:08d}|{1:012d}\n",                # self-transfer
    ]

    (directory / "accounts.dat").write_text(account_text)
    (directory / "operations.dat").write_text("".join(ops_lines))
    return {
        "accounts": accounts,
        "operations": operations,
        "edge_operations": EDGE_CASE_COUNT,
        "seed": seed,
        "digest": fixture_digest(directory),
    }


def fixture_digest(directory: Path) -> str:
    """SHA-256 over ``accounts.dat`` and ``operations.dat`` for reproducibility."""
    digest = hashlib.sha256()
    for name in ("accounts.dat", "operations.dat"):
        digest.update(name.encode())
        digest.update((Path(directory) / name).read_bytes())
    return digest.hexdigest()


def seed_batch(source_dir: Path, target_dir: Path) -> None:
    """Copy the fixture and clear any temp file a previous run left behind."""
    target_dir.mkdir(parents=True, exist_ok=True)
    for name in ("accounts.dat", "operations.dat"):
        shutil.copyfile(Path(source_dir) / name, Path(target_dir) / name)
    for leftover in ("accounts.tmp",):
        stale = Path(target_dir) / leftover
        if stale.exists():
            stale.unlink()
