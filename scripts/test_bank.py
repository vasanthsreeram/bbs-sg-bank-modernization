#!/usr/bin/env python3
"""Unit and integration tests for the legacy COBOL batch and the parity harness.

Run with::

    python3 scripts/test_bank.py -v
    # or, from the repo root:
    python3 -m unittest discover -s scripts -p 'test_*.py'

Coverage
--------
* pure-Python unit tests for the fixture generator and the metrics parser;
* legacy-only contract tests (edge cases the COBOL program must handle);
* legacy/modern parity tests on byte-identical fixtures;
* characterization tests pinning the inputs where the two implementations are
  documented to diverge (fixed-width vs. variable-width parsing);
* an end-to-end integration test of ``scripts/benchmark.py``.

The legacy tests need the isolated ``cobc`` built by ``scripts/get_cobc.sh``.
When it is missing they are skipped with a clear reason, so the pure-Python
tests still run anywhere.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness import (  # noqa: E402  (import after sys.path fix)
    ACCOUNT_BALANCE_CENTS,
    EDGE_CASE_COUNT,
    build_fixture,
    cobc_env,
    compile_legacy,
    find_cobc,
    fixture_digest,
    legacy_command,
    modern_command,
    parse_metrics,
    run_batch,
)

COBC = find_cobc()
_WORKDIR: Path | None = None
_BINARY: Path | None = None


def setUpModule() -> None:  # noqa: N802 (unittest naming)
    global _WORKDIR, _BINARY
    if COBC is None:
        return
    _WORKDIR = Path(tempfile.mkdtemp(prefix="banktest-"))
    _BINARY = compile_legacy(COBC, _WORKDIR)


def tearDownModule() -> None:  # noqa: N802 (unittest naming)
    if _WORKDIR is not None:
        shutil.rmtree(_WORKDIR, ignore_errors=True)


def acct(account: int, cents: int) -> str:
    return f"{account:08d}|{cents:012d}\n"


def op(kind: str, source: int, target: int, cents: int) -> str:
    return f"{kind}|{source:08d}|{target:08d}|{cents:012d}\n"


PAIR_BALANCE = 100
PAIR = acct(1, PAIR_BALANCE) + acct(2, PAIR_BALANCE)


class BatchCase(unittest.TestCase):
    """Base class with helpers to run either implementation on raw fixtures."""

    def require_cobol(self) -> None:
        if COBC is None or _BINARY is None:
            self.skipTest("cobc not found; run scripts/get_cobc.sh or set $COBC")

    def _run(self, command: list[str], accounts: str, operations: str, env=None):
        directory = Path(tempfile.mkdtemp(prefix="bankcase-"))
        self.addCleanup(shutil.rmtree, str(directory), True)
        (directory / "accounts.dat").write_text(accounts)
        (directory / "operations.dat").write_text(operations)
        return run_batch(command, directory, env)

    def legacy(self, accounts: str = PAIR, operations: str = ""):
        self.require_cobol()
        return self._run(legacy_command(_BINARY), accounts, operations, cobc_env(COBC))

    def modern(self, accounts: str = PAIR, operations: str = ""):
        return self._run(modern_command(), accounts, operations)

    def assert_legacy(
        self,
        accounts: str,
        operations: str,
        *,
        metrics: dict[str, int],
        balances: str | None = None,
    ):
        result = self.legacy(accounts, operations)
        self.assertEqual(result.returncode, 0, f"legacy crashed: {result.stderr!r}")
        self.assertEqual(result.metrics, metrics, "unexpected legacy metrics")
        if balances is not None:
            self.assertEqual((result.accounts or b"").decode(), balances)
        return result

    def assert_parity(self, accounts: str, operations: str):
        old = self.legacy(accounts, operations)
        new = self.modern(accounts, operations)
        self.assertEqual(old.returncode, 0, f"legacy crashed: {old.stderr!r}")
        self.assertEqual(new.returncode, 0, f"modern crashed: {new.stderr!r}")
        self.assertEqual(old.metrics, new.metrics, "metric mismatch between legacy and modern")
        self.assertEqual(old.accounts, new.accounts, "accounts.dat mismatch between legacy and modern")
        return old


class TestFixtureUnit(unittest.TestCase):
    """Pure-Python checks that need no compiler."""

    def test_parse_metrics(self):
        out = "PROCESSED=00000003\nREJECTED=00000004\nTOTAL_CENTS=0000000000000230\n"
        self.assertEqual(
            parse_metrics(out),
            {"PROCESSED": 3, "REJECTED": 4, "TOTAL_CENTS": 230},
        )

    def test_parse_metrics_ignores_noise_and_missing(self):
        self.assertEqual(parse_metrics("no metrics here"), {})
        self.assertEqual(parse_metrics("PROCESSED=1\n"), {"PROCESSED": 1})

    def test_build_fixture_is_deterministic(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            build_fixture(Path(a), 25, 40)
            build_fixture(Path(b), 25, 40)
            for name in ("accounts.dat", "operations.dat"):
                self.assertEqual((Path(a) / name).read_bytes(), (Path(b) / name).read_bytes())
            self.assertEqual(fixture_digest(Path(a)), fixture_digest(Path(b)))

    def test_build_fixture_seed_changes_operations(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            build_fixture(Path(a), 25, 40, seed=1)
            build_fixture(Path(b), 25, 40, seed=2)
            self.assertNotEqual(
                (Path(a) / "operations.dat").read_bytes(),
                (Path(b) / "operations.dat").read_bytes(),
            )
            self.assertEqual(
                (Path(a) / "accounts.dat").read_bytes(),
                (Path(b) / "accounts.dat").read_bytes(),
            )

    def test_build_fixture_layout_and_edge_cases(self):
        with tempfile.TemporaryDirectory() as tmp:
            meta = build_fixture(Path(tmp), 10, 20)
            accounts = (Path(tmp) / "accounts.dat").read_text().splitlines()
            operations = (Path(tmp) / "operations.dat").read_text().splitlines()
        self.assertEqual(len(accounts), 10)
        self.assertEqual(len(operations), 20 + EDGE_CASE_COUNT)
        self.assertEqual(meta["edge_operations"], EDGE_CASE_COUNT)
        self.assertEqual(accounts[0], acct(1, ACCOUNT_BALANCE_CENTS).rstrip("\n"))
        self.assertTrue(all(len(line) == 21 for line in accounts))
        self.assertTrue(all(len(line) == 32 for line in operations))
        # The three pinned rejection cases: insufficient funds, missing
        # destination, self-transfer.
        self.assertEqual(operations[-3:], [op("W", 1, 0, 99_999_999).rstrip("\n"),
                                           op("T", 1, 11, 1).rstrip("\n"),
                                           op("T", 1, 1, 1).rstrip("\n")])

    def test_build_fixture_rejects_invalid_sizes(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                build_fixture(Path(tmp), 1, 5)
            with self.assertRaises(ValueError):
                build_fixture(Path(tmp), 5, -1)


class TestLegacyContract(BatchCase):
    """The COBOL program's required behaviour on well-formed and malformed input."""

    def test_happy_path_preserves_integer_cents(self):
        result = self.assert_legacy(
            PAIR,
            op("D", 1, 0, 50) + op("W", 1, 0, 20) + op("T", 2, 1, 30),
            metrics={"PROCESSED": 3, "REJECTED": 0, "TOTAL_CENTS": 230},
            balances=acct(1, 160) + acct(2, 70),
        )
        self.assertRegex(
            result.stdout,
            r"^PROCESSED=\d{8}\nREJECTED=\d{8}\nTOTAL_CENTS=\d{16}\n$",
        )

    def test_overdraft_is_rejected_and_balance_unchanged(self):
        self.assert_legacy(
            PAIR, op("W", 1, 0, 101),
            metrics={"PROCESSED": 0, "REJECTED": 1, "TOTAL_CENTS": 200},
            balances=PAIR,
        )

    def test_withdrawal_of_exact_balance_is_allowed(self):
        self.assert_legacy(
            PAIR, op("W", 1, 0, 100),
            metrics={"PROCESSED": 1, "REJECTED": 0, "TOTAL_CENTS": 100},
            balances=acct(1, 0) + acct(2, 100),
        )

    def test_transfer_of_exact_balance_is_allowed(self):
        self.assert_legacy(
            PAIR, op("T", 1, 2, 100),
            metrics={"PROCESSED": 1, "REJECTED": 0, "TOTAL_CENTS": 200},
            balances=acct(1, 0) + acct(2, 200),
        )

    def test_self_transfer_is_rejected(self):
        self.assert_legacy(PAIR, op("T", 1, 1, 1),
                           metrics={"PROCESSED": 0, "REJECTED": 1, "TOTAL_CENTS": 200})

    def test_missing_destination_is_rejected(self):
        self.assert_legacy(PAIR, op("T", 1, 9, 1),
                           metrics={"PROCESSED": 0, "REJECTED": 1, "TOTAL_CENTS": 200})

    def test_missing_source_is_rejected_for_every_kind(self):
        self.assert_legacy(
            PAIR, op("D", 9, 1, 1) + op("W", 9, 1, 1) + op("T", 9, 1, 1),
            metrics={"PROCESSED": 0, "REJECTED": 3, "TOTAL_CENTS": 200},
        )

    def test_unknown_kind_is_rejected(self):
        self.assert_legacy(PAIR, op("Z", 1, 2, 1),
                           metrics={"PROCESSED": 0, "REJECTED": 1, "TOTAL_CENTS": 200})

    def test_lowercase_kind_is_rejected(self):
        self.assert_legacy(PAIR, op("d", 1, 2, 1),
                           metrics={"PROCESSED": 0, "REJECTED": 1, "TOTAL_CENTS": 200})

    def test_zero_amount_is_rejected(self):
        self.assert_legacy(PAIR, op("D", 1, 2, 0),
                           metrics={"PROCESSED": 0, "REJECTED": 1, "TOTAL_CENTS": 200})

    def test_negative_amount_is_rejected(self):
        line = f"W|{1:08d}|{0:08d}|-{5:011d}\n"  # 12-char field with a sign
        self.assert_legacy(
            PAIR, line,
            metrics={"PROCESSED": 0, "REJECTED": 1, "TOTAL_CENTS": 200},
            balances=PAIR,
        )

    def test_operations_apply_in_file_order(self):
        # First withdrawal leaves 40 cents, so the second cannot succeed.
        self.assert_legacy(
            PAIR, op("W", 1, 0, 60) + op("W", 1, 0, 60),
            metrics={"PROCESSED": 1, "REJECTED": 1, "TOTAL_CENTS": 140},
            balances=acct(1, 40) + acct(2, 100),
        )

    def test_empty_operations_leaves_ledger_untouched(self):
        self.assert_legacy(
            PAIR, "",
            metrics={"PROCESSED": 0, "REJECTED": 0, "TOTAL_CENTS": 200},
            balances=PAIR,
        )

    def test_empty_accounts_rejects_everything(self):
        self.assert_legacy(
            "", op("D", 1, 2, 1),
            metrics={"PROCESSED": 0, "REJECTED": 1, "TOTAL_CENTS": 0},
            balances="",
        )

    def test_missing_trailing_newline_is_processed(self):
        self.assert_legacy(
            PAIR, op("D", 1, 2, 10).rstrip("\n"),
            metrics={"PROCESSED": 1, "REJECTED": 0, "TOTAL_CENTS": 210},
            balances=acct(1, 110) + acct(2, 100),
        )

    def test_malformed_rows_are_rejected_without_aborting(self):
        operations = (
            "D|00000001\n"                       # too few fields
            + op("D", 1, 0, 5)                    # valid, must still apply
            + "D|00000001|00000002|00000000abcd\n"  # non-numeric amount
        )
        self.assert_legacy(
            PAIR, operations,
            metrics={"PROCESSED": 1, "REJECTED": 2, "TOTAL_CENTS": 205},
            balances=acct(1, 105) + acct(2, 100),
        )


class TestParity(BatchCase):
    """legacy and modern must agree byte-for-byte on well-formed fixtures."""

    def test_acceptance_fixture_from_docs(self):
        accounts = acct(1, 100) + acct(2, 100)
        operations = (
            op("D", 1, 0, 50)
            + op("W", 1, 0, 20)
            + op("T", 2, 1, 30)
            + op("W", 1, 0, 99_999)
            + op("T", 1, 1, 1)
            + "Z|00000001|00000000|000000000001\n"
            + op("D", 9, 0, 1)
        )
        result = self.assert_parity(accounts, operations)
        self.assertEqual(result.metrics, {"PROCESSED": 3, "REJECTED": 4, "TOTAL_CENTS": 230})
        self.assertEqual((result.accounts or b"").decode(), acct(1, 160) + acct(2, 70))

    def test_parity_on_randomized_fixtures(self):
        for seed in (1, 2, 3, 4, 5):
            for accounts, operations in ((40, 30), (7, 50), (2, 12)):
                with self.subTest(seed=seed, accounts=accounts, operations=operations):
                    with tempfile.TemporaryDirectory() as tmp:
                        build_fixture(Path(tmp), accounts, operations, seed)
                        accounts_text = (Path(tmp) / "accounts.dat").read_text()
                        ops_text = (Path(tmp) / "operations.dat").read_text()
                    self.assert_parity(accounts_text, ops_text)

    def test_parity_on_boundary_shapes(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_fixture(Path(tmp), 2, 0)
            accounts_text = (Path(tmp) / "accounts.dat").read_text()
            self.assert_parity(accounts_text, "")
        self.assert_parity(PAIR, op("W", 1, 0, 100) + op("T", 1, 2, 100) + op("D", 1, 0, 0))

    def test_parity_without_trailing_newline(self):
        self.assert_parity(PAIR, op("D", 1, 2, 10).rstrip("\n"))

    def test_parity_with_crlf_line_endings(self):
        accounts = PAIR.replace("\n", "\r\n")
        operations = (op("D", 1, 2, 10) + op("T", 2, 1, 5)).replace("\n", "\r\n")
        self.assert_parity(accounts, operations)


class TestDocumentedDivergences(BatchCase):
    """Inputs where fixed-width COBOL parsing and Python parsing differ.

    These characterizations pin how the replacement handles unsafe input.
    Modern rejects duplicate accounts and balance overflow explicitly; the
    COBOL program rewrites duplicate rows and truncates a 12-digit overflow.
    Modern also rejects a 13-digit amount that COBOL parses by fixed columns.
    """

    def test_duplicate_account_ids(self):
        accounts = acct(1, 100) + acct(1, 300) + acct(2, 200)
        operations = op("D", 1, 2, 10)
        legacy = self.legacy(accounts, operations)
        modern = self.modern(accounts, operations)
        # Legacy rewrites *every* row whose id matches the source.
        self.assertEqual(legacy.metrics, {"PROCESSED": 1, "REJECTED": 0, "TOTAL_CENTS": 620})
        self.assertEqual((legacy.accounts or b"").decode(), acct(1, 110) + acct(1, 310) + acct(2, 200))
        # Modern aborts before writing rather than silently losing an account.
        self.assertNotEqual(modern.returncode, 0)
        self.assertIn("duplicate account id", modern.stderr)
        self.assertEqual(modern.accounts, accounts.encode())

    def test_balance_overflow_truncates_in_legacy(self):
        accounts = acct(1, 999_999_999_999) + acct(2, 200)
        operations = op("D", 1, 2, 2)
        legacy = self.legacy(accounts, operations)
        modern = self.modern(accounts, operations)
        # Legacy stores balances in PIC 9(12): 999999999999 + 2 wraps to 1.
        self.assertEqual(legacy.metrics, {"PROCESSED": 1, "REJECTED": 0, "TOTAL_CENTS": 201})
        self.assertEqual((legacy.accounts or b"").decode(), acct(1, 1) + acct(2, 200))
        # Modern refuses a deposit that would exceed the on-disk field width.
        self.assertEqual(modern.metrics, {"PROCESSED": 0, "REJECTED": 1, "TOTAL_CENTS": 1_000_000_000_199})
        self.assertEqual((modern.accounts or b"").decode(), accounts)

    def test_thirteenth_amount_digit_is_dropped_by_legacy(self):
        accounts = PAIR
        operations = f"D|{1:08d}|{2:08d}|{10:013d}\n"  # 13-digit amount field
        legacy = self.legacy(accounts, operations)
        modern = self.modern(accounts, operations)
        # Legacy reads a fixed 12-column field, so it sees the first 12 digits
        # ("000000000001") and deposits 1 cent.
        self.assertEqual(legacy.metrics, {"PROCESSED": 1, "REJECTED": 0, "TOTAL_CENTS": 201})
        self.assertEqual((legacy.accounts or b"").decode(), acct(1, 101) + acct(2, 100))
        # Modern only accepts an exactly-12-digit amount field, so it rejects.
        # (If modern ever re-parses fixed columns too, this should converge.)
        if modern.returncode == 0:
            self.assertEqual(modern.metrics, {"PROCESSED": 0, "REJECTED": 1, "TOTAL_CENTS": 200})
            self.assertEqual((modern.accounts or b"").decode(), PAIR)

    def test_malformed_amount_legacy_rejects_modern_raises_or_converges(self):
        accounts = PAIR
        operations = op("D", 1, 0, 5) + "D|00000001|00000002|00000000abcd\n"
        legacy = self.legacy(accounts, operations)
        self.assertEqual(legacy.returncode, 0)
        self.assertEqual(legacy.metrics, {"PROCESSED": 1, "REJECTED": 1, "TOTAL_CENTS": 205})
        modern = self.modern(accounts, operations)
        if modern.returncode == 0:
            # Defensive parsing added: it should now match legacy.
            self.assertEqual(modern.metrics, legacy.metrics)
        else:
            self.assertNotEqual(modern.returncode, 0, "modern should raise on a non-numeric amount")


class TestBenchmarkIntegration(BatchCase):
    """End-to-end run of scripts/benchmark.py."""

    def benchmark(self, *extra: str) -> subprocess.CompletedProcess:
        self.require_cobol()
        command = [
            sys.executable or "python3",
            str(Path(__file__).resolve().parent / "benchmark.py"),
            "--accounts", "60",
            "--operations", "20",
            "--repeat", "2",
            "--warmup", "0",
            "--no-baselines",
            *extra,
        ]
        return subprocess.run(command, capture_output=True, text=True, env=os.environ.copy())

    def test_quiet_benchmark_prints_the_three_summary_lines(self):
        proc = self.benchmark("--quiet")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        lines = [line for line in proc.stdout.splitlines() if line.strip()]
        self.assertEqual(len(lines), 3, f"expected 3 summary lines, got: {lines!r}")
        self.assertRegex(lines[0], r"^accounts=60 operations=20 \(plus 3 rejected edge cases\)$")
        self.assertRegex(lines[1], r"^legacy=\d+\.\d{6}s modern=\d+\.\d{6}s speedup=\d+\.\dx$")
        self.assertRegex(lines[2], r"^identical outputs and account balances: \{'PROCESSED': \d+, 'REJECTED': \d+, 'TOTAL_CENTS': \d+\}$")

    def test_full_benchmark_verifies_parity_and_reports_scaling(self):
        proc = self.benchmark("--sweep", "30,60")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("parity: identical stdout metrics and byte-identical accounts.dat: YES", proc.stdout)
        self.assertIn("# fixture: accounts=60 operations=20", proc.stdout)
        self.assertIn("scaling sweep", proc.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
