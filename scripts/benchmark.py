#!/usr/bin/env python3
"""Deterministic, transparent benchmark: legacy COBOL batch vs modern Python batch.

What it does
------------
1. Compiles ``legacy/bank.cob`` once with the isolated ``cobc`` located by
   :mod:`harness` (see ``scripts/get_cobc.sh``).
2. Writes byte-identical flat-file fixtures into two scratch directories.
3. Runs both programs and *verifies* they emit the same PROCESSED/REJECTED/
   TOTAL_CENTS and leave a byte-identical ``accounts.dat``.
4. Times each program several times (inputs are restored from the pristine
   fixture before every run) and reports the median, the minimum and the
   resulting speedup.

Honesty notes
-------------
* Every number is a real wall-clock measurement on this host; timings include
  each program's process start-up and vary by machine and workload. Nothing is
  hard-coded, and no speedup is printed before the parity check passes.
* The legacy program is intentionally ``O(operations x accounts)`` -- it
  re-scans and rewrites the whole ledger for every operation -- so the measured
  speedup grows with the account count. ``--sweep`` makes that visible.
* Fixtures are a pure function of ``(accounts, operations, seed)``; the SHA-256
  digest is printed so a run can be reproduced and compared.

The last three lines of default output are stable:

    accounts=<A> operations=<M> (plus 3 rejected edge cases)
    legacy=<t>s modern=<t>s speedup=<x>x
    identical outputs and account balances: {'PROCESSED': ..., ...}

``--quiet`` prints only those three lines (a ``--transcript`` still records all
detail).
"""

from __future__ import annotations

import argparse
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness import (  # noqa: E402  (import after sys.path fix)
    EDGE_CASE_COUNT,
    INSTALL_HINT,
    LEGACY_SOURCE,
    MODERN_SCRIPT,
    build_fixture,
    cobc_env,
    compile_legacy,
    find_cobc,
    legacy_command,
    modern_command,
    run_batch,
    seed_batch,
)


class Emitter:
    """Collect output lines, echo them, and optionally save them verbatim.

    With ``quiet`` set, only lines tagged ``summary`` reach stdout (the three
    stable result lines); a ``--transcript`` still receives the full record.
    """

    def __init__(self, quiet: bool = False) -> None:
        self.lines: list[str] = []
        self.quiet = quiet

    def __call__(self, line: str = "", level: str = "info") -> None:
        self.lines.append(line)
        if self.quiet and level != "summary":
            return
        print(line, flush=True)

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(self.lines) + "\n")


def cobc_version(cobc: Path) -> str:
    try:
        proc = subprocess.run([str(cobc), "--version"], capture_output=True, text=True)
        return proc.stdout.splitlines()[0].strip() if proc.stdout else "unknown"
    except OSError:
        return "unknown"


def timed_batches(
    sizes: dict[str, int],
    repeats: int,
    warmup: int,
    binary: Path,
    cobc: Path,
) -> dict[str, object]:
    """Verify parity and time both programs on one fixture size."""
    with tempfile.TemporaryDirectory(prefix="bankbench-") as tmp:
        root = Path(tmp)
        pristine, old, new = root / "fixture", root / "old", root / "new"
        meta = build_fixture(pristine, sizes["accounts"], sizes["operations"], sizes["seed"])
        seed_batch(pristine, old)
        seed_batch(pristine, new)

        legacy_cmd = legacy_command(binary)
        modern_cmd = modern_command()
        legacy_env = cobc_env(cobc)

        legacy_ref = run_batch(legacy_cmd, old, legacy_env)
        modern_ref = run_batch(modern_cmd, new)
        required = {"PROCESSED", "REJECTED", "TOTAL_CENTS"}
        parity_ok = (
            legacy_ref.returncode == 0
            and modern_ref.returncode == 0
            and legacy_ref.metrics == modern_ref.metrics
            and set(legacy_ref.metrics) == required
            and legacy_ref.accounts == modern_ref.accounts
        )
        result: dict[str, object] = {
            "sizes": sizes,
            "meta": meta,
            "parity_ok": parity_ok,
            "metrics": legacy_ref.metrics,
            "legacy_ref": legacy_ref,
            "modern_ref": modern_ref,
            "legacy_times": [],
            "modern_times": [],
        }
        if not parity_ok:
            return result

        legacy_times: list[float] = result["legacy_times"]  # type: ignore[assignment]
        modern_times: list[float] = result["modern_times"]  # type: ignore[assignment]
        for i in range(warmup + repeats):
            seed_batch(pristine, old)
            legacy_run = run_batch(legacy_cmd, old, legacy_env)
            seed_batch(pristine, new)
            modern_run = run_batch(modern_cmd, new)
            if (
                legacy_run.returncode != 0
                or legacy_run.metrics != legacy_ref.metrics
                or legacy_run.accounts != legacy_ref.accounts
            ):
                raise RuntimeError("legacy produced a different result on a repeat run")
            if (
                modern_run.returncode != 0
                or modern_run.metrics != modern_ref.metrics
                or modern_run.accounts != modern_ref.accounts
            ):
                raise RuntimeError("modern produced a different result on a repeat run")
            if i >= warmup:
                legacy_times.append(legacy_run.seconds)
                modern_times.append(modern_run.seconds)

        result["legacy_median"] = statistics.median(legacy_times)
        result["modern_median"] = statistics.median(modern_times)
        result["legacy_min"] = min(legacy_times)
        result["modern_min"] = min(modern_times)
        return result


def baseline_overheads(repeats: int, binary: Path, cobc: Path) -> dict[str, float | None]:
    """Median cost of starting each runtime on a trivial workload.

    Reported so the reader can separate process start-up from batch work; it is
    a reference, not a correction silently subtracted from the results.
    """
    env = cobc_env(cobc)
    python_times: list[float] = []
    for _ in range(repeats):
        start = time.perf_counter()
        proc = subprocess.run(
            [sys.executable or "python3", "-c", ""], capture_output=True, text=True
        )
        elapsed = time.perf_counter() - start
        if proc.returncode != 0:
            break
        python_times.append(elapsed)

    legacy_times: list[float] = []
    with tempfile.TemporaryDirectory(prefix="bankbench-base-") as tmp:
        directory = Path(tmp)
        (directory / "accounts.dat").write_text("00000001|000000000100\n")
        (directory / "operations.dat").write_text("")
        for _ in range(repeats):
            result = run_batch(legacy_command(binary), directory, env)
            legacy_times.append(result.seconds)

    return {
        "python_startup": statistics.median(python_times) if python_times else None,
        "legacy_trivial": statistics.median(legacy_times) if legacy_times else None,
    }


def run_sweep(
    counts: list[int],
    operations: int,
    seed: int,
    repeats: int,
    warmup: int,
    binary: Path,
    cobc: Path,
    emit: Emitter,
) -> None:
    emit("")
    emit(f"# scaling sweep: operations fixed at {operations}, seed={seed}")
    emit(f"{'accounts':>10} {'legacy(s)':>12} {'modern(s)':>12} {'speedup':>9}  parity")
    for accounts in counts:
        outcome = timed_batches(
            {"accounts": accounts, "operations": operations, "seed": seed},
            repeats,
            warmup,
            binary,
            cobc,
        )
        if not outcome["parity_ok"]:
            emit(f"{accounts:>10} {'-':>12} {'-':>12} {'-':>9}  FAIL")
            continue
        legacy_median: float = outcome["legacy_median"]  # type: ignore[assignment]
        modern_median: float = outcome["modern_median"]  # type: ignore[assignment]
        speedup = legacy_median / modern_median if modern_median else float("inf")
        emit(
            f"{accounts:>10} {legacy_median:>12.6f} {modern_median:>12.6f} "
            f"{speedup:>8.1f}x  ok"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--accounts", type=int, default=1200, help="accounts in the fixture (default 1200)")
    parser.add_argument("--operations", type=int, default=400, help="generated operations (default 400)")
    parser.add_argument("--seed", type=int, default=20260923, help="fixture RNG seed (default 20260923)")
    parser.add_argument("--repeat", type=int, default=5, help="timed runs per program (default 5)")
    parser.add_argument("--warmup", type=int, default=1, help="untimed warm-up runs (default 1)")
    parser.add_argument("--sweep", default="", help="comma-separated account counts for a scaling table")
    parser.add_argument("--no-baselines", action="store_true", help="skip process-overhead references")
    parser.add_argument("--transcript", type=Path, default=None, help="also write all output to this file")
    parser.add_argument("--quiet", action="store_true", help="print only the three summary lines")
    args = parser.parse_args(argv)

    if args.accounts < 2 or args.operations < 0 or args.repeat < 1 or args.warmup < 0:
        parser.error("need accounts >= 2, operations >= 0, repeat >= 1, warmup >= 0")

    cobc = find_cobc()
    if cobc is None:
        print(INSTALL_HINT, file=sys.stderr)
        return 2

    emit = Emitter(quiet=args.quiet)

    with tempfile.TemporaryDirectory(prefix="bankbench-bin-") as bin_dir:
        binary = compile_legacy(cobc, Path(bin_dir))

        emit("# BBS SG Bank batch benchmark")
        emit(f"# host:   {platform.platform()}  python {platform.python_version()}")
        emit(f"# cobc:   {cobc}  ({cobc_version(cobc)})")
        emit(f"# legacy: {LEGACY_SOURCE} -> {binary}")
        emit(f"# modern: {MODERN_SCRIPT}")
        emit(
            f"# note:   wall-clock on this host, includes process start-up; "
            f"re-run to reproduce (seed={args.seed})."
        )
        if not args.no_baselines:
            base = baseline_overheads(max(args.repeat, 3), binary, cobc)
            emit(
                "# overhead reference (median): "
                f"python interpreter start={base['python_startup']:.6f}s, "
                f"legacy trivial batch={base['legacy_trivial']:.6f}s"
            )

        outcome = timed_batches(
            {"accounts": args.accounts, "operations": args.operations, "seed": args.seed},
            args.repeat,
            args.warmup,
            binary,
            cobc,
        )

        if not outcome["parity_ok"]:
            legacy_ref = outcome["legacy_ref"]
            modern_ref = outcome["modern_ref"]
            emit("", level="summary")
            emit("PARITY FAILED: legacy and modern did not agree.", level="summary")
            emit(
                f"  legacy rc={legacy_ref.returncode} metrics={legacy_ref.metrics} "
                f"stderr={legacy_ref.stderr.strip()[:200]!r}",
                level="summary",
            )
            emit(
                f"  modern rc={modern_ref.returncode} metrics={modern_ref.metrics} "
                f"stderr={modern_ref.stderr.strip()[:200]!r}",
                level="summary",
            )
            emit(f"  accounts identical: {legacy_ref.accounts == modern_ref.accounts}", level="summary")
            if args.transcript:
                emit.save(args.transcript)
            return 1

        meta = outcome["meta"]  # type: ignore[assignment]
        emit("")
        emit(
            f"# fixture: accounts={meta['accounts']} operations={meta['operations']} "
            f"seed={meta['seed']} sha256={meta['digest']}"
        )
        emit("# parity: identical stdout metrics and byte-identical accounts.dat: YES")
        emit(
            f"# per-run wall time (s), inputs restored before every run "
            f"(warmup={args.warmup}, repeats={args.repeat}):"
        )
        emit(f"{'run':>4} {'legacy':>12} {'modern':>12}")
        for index, (legacy_time, modern_time) in enumerate(
            zip(outcome["legacy_times"], outcome["modern_times"]), start=1  # type: ignore[arg-type]
        ):
            emit(f"{index:>4} {legacy_time:>12.6f} {modern_time:>12.6f}")
        emit(f"{'median':>4} {outcome['legacy_median']:>12.6f} {outcome['modern_median']:>12.6f}")
        emit(f"{'min':>4} {outcome['legacy_min']:>12.6f} {outcome['modern_min']:>12.6f}")
        if args.sweep:
            counts = [int(part) for part in args.sweep.split(",") if part.strip()]
            run_sweep(counts, args.operations, args.seed, args.repeat, args.warmup, binary, cobc, emit)
        emit("")

        legacy_median: float = outcome["legacy_median"]  # type: ignore[assignment]
        modern_median: float = outcome["modern_median"]  # type: ignore[assignment]
        speedup = legacy_median / modern_median if modern_median else float("inf")
        emit(
            f"accounts={args.accounts} operations={args.operations} "
            f"(plus {EDGE_CASE_COUNT} rejected edge cases)",
            level="summary",
        )
        emit(
            f"legacy={legacy_median:.6f}s modern={modern_median:.6f}s speedup={speedup:.1f}x",
            level="summary",
        )
        emit(f"identical outputs and account balances: {outcome['metrics']}", level="summary")

        if args.transcript:
            emit.save(args.transcript)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
