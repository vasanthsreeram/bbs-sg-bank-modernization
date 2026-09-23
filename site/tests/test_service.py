"""Unit tests for the demo ledger service.

These exercise the real modern batch engine (modern/bank.py) through a temporary
work directory, with no network and no browser involved.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import service  # noqa: E402
from service import BankService, LedgerError  # noqa: E402


class BankServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="bbs-test-")
        self.addCleanup(self.tmp.cleanup)
        self.bank = BankService(workdir=Path(self.tmp.name))

    # ------------------------------------------------------------------ seed

    def test_seed_ledger_matches_the_replayed_history(self) -> None:
        summary = self.bank.summary()
        self.assertEqual(summary["account_count"], len(service.SEED_ACCOUNTS))
        self.assertTrue(summary["invariant_ok"])
        self.assertEqual(summary["audit_count"], len(service.SEED_OPERATIONS))
        # 12 seeded rows, 3 of which are deliberately invalid.
        self.assertEqual(summary["rejected_count"], 3)
        self.assertEqual(summary["posted_count"], 9)

    def test_seeded_balances_reflect_the_seeded_operations(self) -> None:
        accounts = {account["id"]: account for account in self.bank.accounts_view()}
        # 10000001 received 3,250,000 and sent 2,640,000 against a 4,820,500 opening.
        self.assertEqual(accounts["10000001"]["opening_balance_cents"], 4_820_500)
        self.assertEqual(accounts["10000001"]["balance_cents"], 5_430_500)
        self.assertEqual(accounts["10000007"]["balance_cents"], 21_540_750)

    def test_flat_files_are_written_for_the_engine(self) -> None:
        accounts = (Path(self.tmp.name) / "accounts.dat").read_text().splitlines()
        operations = (Path(self.tmp.name) / "operations.dat").read_text().splitlines()
        self.assertEqual(len(accounts), len(service.SEED_ACCOUNTS))
        self.assertTrue(all(line.count("|") == 1 for line in accounts))
        self.assertEqual(len(operations), len(service.SEED_OPERATIONS))
        self.assertTrue(all(len(line.split("|")) == 4 for line in operations))

    # ------------------------------------------------------------ postings

    def test_transfer_moves_value_without_changing_the_total(self) -> None:
        before = self.bank.total_cents()
        result = self.bank.process(
            [{"kind": "T", "source": "10000007", "target": "10000002", "amount_cents": 12345}]
        )
        self.assertEqual(result["processed"], 1)
        self.assertEqual(result["rejected"], 0)
        self.assertEqual(result["operations"][0]["status"], "posted")
        self.assertEqual(self.bank.total_cents(), before)
        self.assertTrue(result["invariant_ok"])
        self.assertTrue(result["engine_matches_simulation"])

    def test_deposit_and_withdrawal_change_the_total_by_the_amount(self) -> None:
        before = self.bank.total_cents()
        self.bank.process([{"kind": "D", "source": "10000006", "amount_cents": 50_000}])
        self.assertEqual(self.bank.total_cents(), before + 50_000)
        self.bank.process([{"kind": "W", "source": "10000006", "amount_cents": 20_000}])
        self.assertEqual(self.bank.total_cents(), before + 30_000)

    def test_insufficient_funds_is_rejected_with_a_reason(self) -> None:
        before = self.bank.total_cents()
        result = self.bank.process([{"kind": "W", "source": "10000008", "amount_cents": 99_999_999}])
        self.assertEqual(result["rejected"], 1)
        self.assertEqual(result["operations"][0]["reason"], "insufficient funds")
        self.assertEqual(self.bank.total_cents(), before)

    def test_unknown_accounts_and_self_transfers_are_rejected(self) -> None:
        result = self.bank.process(
            [
                {"kind": "T", "source": "10000001", "target": "99999999", "amount_cents": 1},
                {"kind": "T", "source": "10000001", "target": "10000001", "amount_cents": 1},
                {"kind": "T", "source": "99999999", "target": "10000001", "amount_cents": 1},
            ]
        )
        reasons = [op["reason"] for op in result["operations"]]
        self.assertEqual(result["rejected"], 3)
        self.assertEqual(
            reasons,
            ["destination account not found", "source and destination are the same account", "source account not found"],
        )

    def test_bad_kind_and_nonpositive_amounts_are_rejected(self) -> None:
        result = self.bank.process(
            [
                {"kind": "X", "source": "10000001", "amount_cents": 100},
                {"kind": "D", "source": "10000001", "amount_cents": 0},
                {"kind": "D", "source": "10000001", "amount_cents": -500},
            ]
        )
        self.assertEqual(result["rejected"], 3)
        self.assertEqual(result["operations"][0]["reason"], "unsupported operation code")
        self.assertEqual(result["operations"][1]["reason"], "amount must be greater than zero")
        self.assertEqual(result["operations"][2]["reason"], "amount must be greater than zero")

    def test_overflowing_deposit_is_rejected_with_ledger_unchanged(self) -> None:
        before = self.bank.total_cents()
        result = self.bank.process([{"kind": "D", "source": "10000001", "amount_cents": service.MAX_SERIALISED_AMOUNT}])
        self.assertEqual((result["processed"], result["rejected"]), (0, 1))
        self.assertEqual(result["operations"][0]["reason"], "account balance exceeds the 12-digit ledger field")
        self.assertEqual(self.bank.total_cents(), before)
        self.assertTrue(result["engine_matches_simulation"])
        self.assertTrue(all(len(row) == 21 for row in (Path(self.tmp.name) / "accounts.dat").read_text().splitlines()))

    def test_oversize_amount_is_rejected_before_serialisation(self) -> None:
        with self.assertRaisesRegex(LedgerError, "12-digit"):
            self.bank.process([{"kind": "D", "source": "10000001", "amount_cents": service.MAX_SERIALISED_AMOUNT + 1}])

    def test_amount_must_be_numeric(self) -> None:
        with self.assertRaises(LedgerError):
            self.bank.process([{"kind": "D", "source": "10000001", "amount_cents": "lots"}])

    def test_operations_must_be_a_list(self) -> None:
        with self.assertRaises(LedgerError):
            self.bank.process({"kind": "D", "source": "10000001", "amount_cents": 1})

    def test_account_ids_are_normalised_before_serialisation(self) -> None:
        result = self.bank.process([{"kind": "T", "source": "10000002 ", "target": "7", "amount_cents": 1}])
        self.assertEqual(result["rejected"], 1)
        self.assertEqual(result["operations"][0]["source"], "10000002")
        # "7" pads to 00000007, which is not one of the demo accounts.
        self.assertEqual(result["operations"][0]["reason"], "destination account not found")

    # --------------------------------------------------------------- audit

    def test_every_row_reaches_the_audit_trail(self) -> None:
        self.bank.process(
            [
                {"kind": "T", "source": "10000001", "target": "10000002", "amount_cents": 100},
                {"kind": "W", "source": "10000008", "amount_cents": 9_999_999_999},
            ],
            channel="test",
        )
        newest = self.bank.audit_view(limit=2)
        self.assertEqual(newest[0]["status"], "rejected")
        self.assertEqual(newest[0]["reason"], "insufficient funds")
        self.assertEqual(newest[0]["channel"], "test")
        self.assertEqual(newest[1]["status"], "posted")
        self.assertTrue(all(entry["id"].startswith("AUD-") for entry in newest))

    def test_audit_filters(self) -> None:
        self.assertGreater(len(self.bank.audit_view(status="rejected")), 0)
        self.assertTrue(all(entry["status"] == "rejected" for entry in self.bank.audit_view(status="rejected")))
        self.assertTrue(all(entry["kind"] == "T" for entry in self.bank.audit_view(kind="T")))

    def test_account_detail_lists_its_own_activity(self) -> None:
        detail = self.bank.account_detail("10000001")
        self.assertIsNotNone(detail)
        self.assertTrue(detail["history"])
        self.assertTrue(all("10000001" in (entry["source"], entry["target"]) for entry in detail["history"]))
        self.assertIsNone(self.bank.account_detail("99999999"))

    # --------------------------------------------------------- demo batch

    def test_demo_batch_conserves_value_and_reports_rejections(self) -> None:
        result = self.bank.demo_batch(25, include_edge_cases=True)
        self.assertEqual(result["processed"] + result["rejected"], 28)
        self.assertTrue(result["conservation_ok"])
        self.assertEqual(result["total_before_cents"], result["total_after_cents"])
        self.assertTrue(result["engine_matches_simulation"])
        self.assertEqual(result["edge_cases"], 3)
        reasons = {row["reason"] for row in result["rejections_by_reason"]}
        self.assertEqual(
            reasons,
            {
                "insufficient funds",
                "source and destination are the same account",
                "destination account not found",
            },
        )

    def test_demo_batch_is_deterministic_for_a_seed(self) -> None:
        first = self.bank.demo_batch(12, seed=7)
        self.bank.reset()
        second = self.bank.demo_batch(12, seed=7)
        self.assertEqual(first["processed"], second["processed"])
        self.assertEqual(first["rejected"], second["rejected"])
        self.assertEqual(
            [op["amount_cents"] for op in first["operations"]],
            [op["amount_cents"] for op in second["operations"]],
        )

    def test_demo_batch_rejects_out_of_range_sizes(self) -> None:
        with self.assertRaises(LedgerError):
            self.bank.demo_batch(0)
        with self.assertRaises(LedgerError):
            self.bank.demo_batch(5000)

    # ------------------------------------------------------------- reset

    def test_reset_restores_the_seeded_state(self) -> None:
        baseline = self.bank.summary()["total_cents"]
        self.bank.process([{"kind": "D", "source": "10000009", "amount_cents": 5_000_000}])
        self.assertNotEqual(self.bank.total_cents(), baseline)
        summary = self.bank.reset()
        self.assertEqual(summary["total_cents"], baseline)
        self.assertEqual(summary["audit_count"], len(service.SEED_OPERATIONS))

    # ------------------------------------------------------------ excerpt

    def test_legacy_excerpt_points_at_the_bottleneck(self) -> None:
        excerpt = service.legacy_source_excerpt()
        self.assertTrue(excerpt["bottleneck_lines"])
        self.assertEqual(excerpt["path"], "legacy/bank.cob")
        highlighted = [excerpt["lines"][line - 1] for line in excerpt["bottleneck_lines"]]
        self.assertTrue(any("open input bank-file" in line for line in highlighted))


if __name__ == "__main__":
    unittest.main()
