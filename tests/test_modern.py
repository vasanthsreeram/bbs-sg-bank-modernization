import importlib.util
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / "modern/bank.py"
spec = importlib.util.spec_from_file_location("modern_bank", MODULE)
bank = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bank)


class BankBatchTests(unittest.TestCase):
    def run_batch(self, accounts: str, operations: str):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "accounts.dat").write_text(accounts)
            (path / "operations.dat").write_text(operations)
            result = bank.run(path)
            return result, (path / "accounts.dat").read_text()

    def test_deposit_withdrawal_and_transfer_use_integer_cents(self):
        result, output = self.run_batch(
            "00000001|000000001000\n00000002|000000000500\n",
            "D|00000001|00000000|000000000025\n"
            "W|00000002|00000000|000000000100\n"
            "T|00000001|00000002|000000000200\n",
        )
        self.assertEqual(result, (3, 0, 1425))
        self.assertEqual(output, "00000001|000000000825\n00000002|000000000600\n")

    def test_malformed_operations_are_rejected_and_batch_continues(self):
        result, output = self.run_batch(
            "00000001|000000000100\n00000002|000000000100\n",
            "D|00000001|00000000|ABCDEFGHIJKL\n"
            "T|00000001|00000002|000000000001\n",
        )
        self.assertEqual(result, (1, 1, 200))
        self.assertEqual(output, "00000001|000000000099\n00000002|000000000101\n")

    def test_balance_overflow_is_rejected_without_widening_ledger_record(self):
        result, output = self.run_batch(
            "00000001|999999999999\n00000002|999999999998\n",
            "D|00000001|00000000|000000000001\n"
            "T|00000001|00000002|000000000002\n",
        )
        self.assertEqual(result, (0, 2, 1999999999997))
        self.assertEqual(output, "00000001|999999999999\n00000002|999999999998\n")

    def test_duplicate_accounts_fail_before_any_write(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            original = "00000001|000000000100\n00000001|000000000300\n"
            (path / "accounts.dat").write_text(original)
            (path / "operations.dat").write_text("D|00000001|00000000|000000000001\n")
            with self.assertRaisesRegex(ValueError, "duplicate account"):
                bank.run(path)
            self.assertEqual((path / "accounts.dat").read_text(), original)

    def test_overdraft_unknown_recipient_and_self_transfer_are_rejected(self):
        result, output = self.run_batch(
            "00000001|000000000100\n00000002|000000000100\n",
            "W|00000001|00000000|000000000101\n"
            "T|00000001|00000003|000000000001\n"
            "T|00000001|00000001|000000000001\n",
        )
        self.assertEqual(result, (0, 3, 200))
        self.assertEqual(output, "00000001|000000000100\n00000002|000000000100\n")


if __name__ == "__main__":
    unittest.main()
