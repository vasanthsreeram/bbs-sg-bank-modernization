"""Ledger service for the fictional BBS SG Bank demo site.

Balances live in the same ``accounts.dat`` / ``operations.dat`` flat files the
CLI uses, and every posting is applied by the *unmodified* modern batch engine
(``modern/bank.py``).  The demo therefore exercises the real code path instead of
a reimplementation: the service only supplies accounts, validation messages and
an audit trail around it.

Nothing here touches a real bank.  Accounts, balances, counterparties and audit
history are invented so the site can be demonstrated safely.
"""

from __future__ import annotations

import datetime as dt
import random
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODERN_DIR = ROOT / "modern"
LEGACY_SOURCE = ROOT / "legacy" / "bank.cob"

if str(MODERN_DIR) not in sys.path:
    sys.path.insert(0, str(MODERN_DIR))

import bank as batch_engine  # noqa: E402  (imported after the path is extended)

CURRENCY = "SGD"
KIND_LABELS = {"D": "Deposit", "W": "Withdrawal", "T": "Transfer"}
MAX_SERIALISED_AMOUNT = 999_999_999_999  # PIC 9(12) in the COBOL record layout
DEMO_SEED = 20260923

# Fictional customers.  Balances are the ledger's opening state in cents.
SEED_ACCOUNTS = (
    ("10000001", "Harbourfront Retail Pte Ltd", "Current", 4_820_500),
    ("10000002", "Tiong Bahru Coffee Co", "Current", 1_275_000),
    ("10000003", "Kranji Agri Supplies", "Current", 8_940_250),
    ("10000004", "Sentosa Leisure Group", "Current", 15_600_000),
    ("10000005", "Jurong Precision Tools", "Current", 3_415_900),
    ("10000006", "Ang Mo Kio Hardware", "Savings", 640_300),
    ("10000007", "Punggol Digital Works", "Current", 22_180_750),
    ("10000008", "Queenstown Bakery Supplies", "Savings", 512_600),
    ("10000009", "Changi Freight Services", "Current", 11_004_000),
    ("10000010", "Orchard Fashion House", "Current", 2_730_450),
    ("10000011", "Woodlands Auto Parts", "Savings", 987_200),
    ("10000012", "Serangoon Grocers Co-op", "Current", 5_362_900),
)

SEED_EPOCH = dt.datetime(2026, 9, 22, 9, 12, 0, tzinfo=dt.timezone.utc)

# Illustrative audit history.  These are replayed through the engine on reset,
# so the balances the UI shows are genuinely the result of this history.
SEED_OPERATIONS = (
    (0, "T", "10000009", "10000001", 3_250_000, "tellering.ws01", "TRF-20411"),
    (7, "W", "10000002", None, 118_400, "branch.orchard", "CSH-20412"),
    (15, "T", "10000004", "10000010", 980_000, "api.payments", "TRF-20413"),
    (23, "D", "10000006", None, 250_000, "branch.amk", "DEP-20414"),
    (34, "T", "10000011", "10000012", 75_000, "api.payments", "TRF-20415"),
    (41, "T", "10000005", "10000007", 4_100_000, "api.payments", "TRF-20416"),
    (52, "T", "10000003", "10000003", 12_000, "batch.nightly", "TRF-20417"),
    (58, "W", "10000008", None, 9_999_999_999, "branch.queenstown", "CSH-20418"),
    (66, "T", "10000012", "10000002", 420_000, "api.payments", "TRF-20419"),
    (74, "D", "10000010", None, 1_500_000, "branch.orchard", "DEP-20420"),
    (83, "T", "10000001", "10000009", 2_640_000, "api.payments", "TRF-20421"),
    (91, "W", "10000007", None, 640_000, "branch.punggol", "CSH-20422"),
)


class LedgerError(ValueError):
    """Raised when an operation request is structurally unusable."""

    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.status = status


def _clean_id(value) -> str:
    """Normalise an account id to the 8-character field the batch files use."""
    if value is None:
        return ""
    text = str(value).strip().upper().replace("|", "")
    return text.zfill(8) if text.isdigit() and len(text) <= 8 else text


def _field(value: str, width: int = 8) -> str:
    return value[:width].ljust(width)


def _serialise_amount(amount: int) -> int:
    """Map unusable amounts onto a value both engines agree is invalid."""
    if amount <= 0:
        return 0  # bank.py rejects amount <= 0; COBOL rejects all-zero amounts.
    return amount


class BankService:
    """Holds the demo ledger, applies operations and records the audit trail."""

    def __init__(self, workdir: Path | None = None) -> None:
        self.workdir = Path(workdir) if workdir else Path(tempfile.mkdtemp(prefix="bbs-sgbank-"))
        self.workdir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.last_batch: dict | None = None
        self.reset()

    # ------------------------------------------------------------------ setup

    def reset(self) -> dict:
        """Rebuild the ledger from the seed history and return a summary."""
        with self._lock:
            self.accounts = {
                account_id: {
                    "id": account_id,
                    "name": name,
                    "product": product,
                    "opening_balance_cents": opening,
                    "balance_cents": opening,
                }
                for account_id, name, product, opening in SEED_ACCOUNTS
            }
            self.audit: list[dict] = []
            self._seq = 0
            self._write_accounts()
            self.last_batch = None

            seed_ops = []
            for minutes, kind, source, target, amount, actor, reference in SEED_OPERATIONS:
                seed_ops.append(
                    {
                        "kind": kind,
                        "source": source,
                        "target": target,
                        "amount_cents": amount,
                        "actor": actor,
                        "reference": reference,
                        "recorded_at": SEED_EPOCH + dt.timedelta(minutes=minutes),
                        "seeded": True,
                    }
                )
            self.process(seed_ops, channel="seed.history", record_stats=False)
            return self.summary()

    # ------------------------------------------------------------- flat files

    def _accounts_path(self) -> Path:
        return self.workdir / "accounts.dat"

    def _operations_path(self) -> Path:
        return self.workdir / "operations.dat"

    def _write_accounts(self) -> None:
        rows = "".join(
            f"{account['id']}|{account['balance_cents']:012d}\n"
            for account in sorted(self.accounts.values(), key=lambda a: a["id"])
        )
        self._accounts_path().write_text(rows)

    def _load_accounts(self) -> None:
        for row in self._accounts_path().read_text().splitlines():
            account_id, cents = row.split("|")
            self.accounts[account_id]["balance_cents"] = int(cents)

    def _write_operations(self, operations: list[dict]) -> None:
        lines = []
        for op in operations:
            kind = op["kind"] if len(op["kind"]) == 1 else "?"
            lines.append(
                f"{kind}|{_field(op['source'])}|{_field(op['target'])}|{_serialise_amount(op['amount_cents']):012d}\n"
            )
        self._operations_path().write_text("".join(lines))

    # -------------------------------------------------------------- validation

    @staticmethod
    def _normalise(op: dict) -> dict:
        if not isinstance(op, dict):
            raise LedgerError("each operation must be an object")
        raw_kind = str(op.get("kind", "")).strip().upper()
        amount = op.get("amount_cents", op.get("amount"))
        try:
            amount_cents = int(amount)
        except (TypeError, ValueError):
            raise LedgerError(f"amount must be a whole number of cents, got {amount!r}") from None
        if amount_cents > MAX_SERIALISED_AMOUNT:
            raise LedgerError("amount exceeds the 12-digit batch field")
        recorded_at = op.get("recorded_at")
        if recorded_at is not None and not isinstance(recorded_at, dt.datetime):
            raise LedgerError("recorded_at must be a datetime")
        return {
            "kind": raw_kind[:1],
            "source": _clean_id(op.get("source")),
            "target": _clean_id(op.get("target")),
            "amount_cents": amount_cents,
            "actor": str(op.get("actor") or "demo.user"),
            "reference": str(op.get("reference") or ""),
            "channel": str(op.get("channel") or ""),
            "recorded_at": recorded_at,
            "seeded": bool(op.get("seeded")),
        }

    def _simulate(self, operations: list[dict]) -> list[dict]:
        """Mirror the engine's rules to attach a human-readable reason per row.

        The engine remains the authority: its processed/rejected counts are
        cross-checked against this simulation after every batch.
        """
        balances = {account_id: account["balance_cents"] for account_id, account in self.accounts.items()}
        predictions = []
        for op in operations:
            kind, source, target, amount = op["kind"], op["source"], op["target"], op["amount_cents"]
            reason = None
            if kind not in KIND_LABELS:
                reason = "unsupported operation code"
            elif amount <= 0:
                reason = "amount must be greater than zero"
            elif source not in balances:
                reason = "source account not found"
            elif kind == "T" and target not in balances:
                reason = "destination account not found"
            elif kind == "T" and source == target:
                reason = "source and destination are the same account"
            elif kind != "D" and balances[source] < amount:
                reason = "insufficient funds"
            elif kind == "D" and balances[source] + amount > MAX_SERIALISED_AMOUNT:
                reason = "account balance exceeds the 12-digit ledger field"
            elif kind == "T" and balances[target] + amount > MAX_SERIALISED_AMOUNT:
                reason = "destination balance exceeds the 12-digit ledger field"

            accepted = reason is None
            source_balance = balances.get(source)
            target_balance = balances.get(target)
            if accepted:
                balances[source] += amount if kind == "D" else -amount
                source_balance = balances[source]
                if kind == "T":
                    balances[target] += amount
                    target_balance = balances[target]
            predictions.append(
                {
                    "accepted": accepted,
                    "reason": reason,
                    "source_balance_cents": source_balance,
                    "target_balance_cents": target_balance,
                }
            )
        return predictions

    # -------------------------------------------------------------- processing

    def process(self, operations: list[dict], *, channel: str = "live.api", record_stats: bool = True) -> dict:
        """Apply operations through the modern batch engine and audit each row."""
        if not isinstance(operations, list):
            raise LedgerError("operations must be a list")
        if len(operations) > 5000:
            raise LedgerError("at most 5000 operations per batch", status=413)

        with self._lock:
            normalised = [self._normalise(op) for op in operations]
            predictions = self._simulate(normalised)
            self._write_operations(normalised)

            started = time.perf_counter()
            processed, rejected, engine_total = batch_engine.run(self.workdir)
            elapsed_ms = (time.perf_counter() - started) * 1000

            self._load_accounts()
            predicted_processed = sum(1 for p in predictions if p["accepted"])
            ledger_total = self.total_cents()
            engine_matches = (processed, rejected, engine_total) == (
                predicted_processed,
                len(predictions) - predicted_processed,
                ledger_total,
            )

            results = []
            for op, prediction in zip(normalised, predictions):
                self._seq += 1
                entry = self._audit_entry(op, prediction, channel)
                self.audit.append(entry)
                results.append(
                    {
                        "id": entry["id"],
                        "kind": op["kind"],
                        "kind_label": KIND_LABELS.get(op["kind"], "Unknown"),
                        "source": op["source"],
                        "source_name": self._name(op["source"]),
                        "target": op["target"] or None,
                        "target_name": self._name(op["target"]) if op["target"] else None,
                        "amount_cents": op["amount_cents"],
                        "status": entry["status"],
                        "reason": prediction["reason"],
                        "source_balance_cents": prediction["source_balance_cents"],
                        "target_balance_cents": prediction["target_balance_cents"],
                        "reference": op["reference"] or None,
                    }
                )
            batch = {
                "channel": channel,
                "processed": processed,
                "rejected": rejected,
                "engine_total_cents": engine_total,
                "ledger_total_cents": ledger_total,
                "elapsed_ms": round(elapsed_ms, 3),
                "engine_matches_simulation": engine_matches,
                "invariant_ok": engine_total == ledger_total,
                "operations": results,
            }
            if record_stats:
                self.last_batch = batch
            return batch

    def _audit_entry(self, op: dict, prediction: dict, channel: str) -> dict:
        recorded_at = op["recorded_at"] or dt.datetime.now(dt.timezone.utc)
        return {
            "id": f"AUD-{self._seq:05d}",
            "timestamp": recorded_at.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
            "kind": op["kind"],
            "kind_label": KIND_LABELS.get(op["kind"], "Unknown"),
            "source": op["source"],
            "source_name": self._name(op["source"]),
            "target": op["target"] or None,
            "target_name": self._name(op["target"]) if op["target"] else None,
            "amount_cents": op["amount_cents"],
            "status": "posted" if prediction["accepted"] else "rejected",
            "reason": prediction["reason"],
            "actor": op["actor"],
            "reference": op["reference"] or None,
            "channel": channel,
            "seeded": op["seeded"],
        }

    def _name(self, account_id: str) -> str:
        account = self.accounts.get(account_id)
        return account["name"] if account else "unknown account"

    # ----------------------------------------------------------- interactive batch

    def demo_batch(
        self,
        operations_count: int = 60,
        *,
        include_edge_cases: bool = True,
        seed: int = DEMO_SEED,
        max_amount_cents: int = 25_000,
    ) -> dict:
        """Generate a transfer-only batch over the live ledger and run it.

        Transfers only, so the total value in the ledger must be unchanged by a
        batch regardless of how many rows are rejected.
        """
        operations_count = int(operations_count)
        if not 1 <= operations_count <= 2000:
            raise LedgerError("operations must be between 1 and 2000")
        max_amount_cents = int(max_amount_cents)
        if not 100 <= max_amount_cents <= 500_000:
            raise LedgerError("max amount must be between 100 and 500000 cents")

        with self._lock:
            ids = sorted(self.accounts)
            randomizer = random.Random(seed)
            operations = []
            for index in range(operations_count):
                source = ids[randomizer.randrange(len(ids))]
                target = ids[randomizer.randrange(len(ids))]
                if target == source:
                    target = ids[(ids.index(source) + 1) % len(ids)]
                operations.append(
                    {
                        "kind": "T",
                        "source": source,
                        "target": target,
                        "amount_cents": randomizer.randint(100, max_amount_cents),
                        "actor": "batch.nightly",
                        "reference": f"SIM-{90000 + index}",
                    }
                )
            if include_edge_cases:
                operations.extend(
                    [
                        {  # More than any balance in the ledger.
                            "kind": "T",
                            "source": ids[0],
                            "target": ids[-1],
                            "amount_cents": MAX_SERIALISED_AMOUNT,
                            "actor": "batch.nightly",
                            "reference": "SIM-EDGE-1",
                        },
                        {  # Destination is not in the ledger.
                            "kind": "T",
                            "source": ids[0],
                            "target": "99999999",
                            "amount_cents": 1,
                            "actor": "batch.nightly",
                            "reference": "SIM-EDGE-2",
                        },
                        {  # Self transfer.
                            "kind": "T",
                            "source": ids[0],
                            "target": ids[0],
                            "amount_cents": 1,
                            "actor": "batch.nightly",
                            "reference": "SIM-EDGE-3",
                        },
                    ]
                )

            before = self.total_cents()
            batch = self.process(operations, channel="batch.simulated")
            after = self.total_cents()
            batch.update(
                {
                    "requested": operations_count,
                    "edge_cases": 3 if include_edge_cases else 0,
                    "total_before_cents": before,
                    "total_after_cents": after,
                    "conservation_ok": before == after,
                    "rejections_by_reason": self._rejection_breakdown(batch["operations"]),
                }
            )
            self.last_batch = batch
            return batch

    @staticmethod
    def _rejection_breakdown(results: list[dict]) -> list[dict]:
        counts: dict[str, int] = {}
        for result in results:
            if result["status"] == "rejected":
                reason = result["reason"] or "unknown"
                counts[reason] = counts.get(reason, 0) + 1
        return [
            {"reason": reason, "count": count}
            for reason, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        ]

    # ------------------------------------------------------------------ queries

    def total_cents(self) -> int:
        return sum(account["balance_cents"] for account in self.accounts.values())

    def _file_total(self) -> int:
        """Total read back from accounts.dat, used as an independent invariant."""
        total = 0
        for row in self._accounts_path().read_text().splitlines():
            total += int(row.split("|")[1])
        return total

    def accounts_view(self) -> list[dict]:
        with self._lock:
            return [
                {
                    **account,
                    "movements": sum(1 for entry in self.audit if account["id"] in (entry["source"], entry["target"])),
                }
                for account in sorted(self.accounts.values(), key=lambda a: a["id"])
            ]

    def account_detail(self, account_id: str) -> dict | None:
        account_id = _clean_id(account_id)
        with self._lock:
            account = self.accounts.get(account_id)
            if not account:
                return None
            activity = [entry for entry in self.audit if account_id in (entry["source"], entry["target"])]
            return {
                **account,
                "history": list(reversed(activity))[:25],
            }

    def audit_view(self, limit: int = 100, status: str | None = None, kind: str | None = None) -> list[dict]:
        with self._lock:
            entries = self.audit
            if status:
                entries = [entry for entry in entries if entry["status"] == status]
            if kind:
                entries = [entry for entry in entries if entry["kind"] == kind]
            return list(reversed(entries))[:limit]

    def summary(self) -> dict:
        with self._lock:
            posted = sum(1 for entry in self.audit if entry["status"] == "posted")
            rejected = sum(1 for entry in self.audit if entry["status"] == "rejected")
            balances = [account["balance_cents"] for account in self.accounts.values()]
            return {
                "currency": CURRENCY,
                "total_cents": sum(balances),
                "account_count": len(self.accounts),
                "posted_count": posted,
                "rejected_count": rejected,
                "audit_count": len(self.audit),
                "largest_balance_cents": max(balances) if balances else 0,
                "smallest_balance_cents": min(balances) if balances else 0,
                "invariant_ok": self.total_cents() == self._file_total(),
                "engine": "modern/bank.py",
                "last_batch": self.last_batch,
            }


def legacy_source_excerpt() -> dict:
    """Return the COBOL source and the lines that contain the batch bottleneck."""
    text = LEGACY_SOURCE.read_text().splitlines()
    bottleneck = [
        index + 1
        for index, line in enumerate(text)
        if "open input bank-file" in line or "open output temp-file" in line or "open output bank-file" in line
    ]
    return {
        "path": str(LEGACY_SOURCE.relative_to(ROOT)),
        "lines": text,
        "bottleneck_lines": bottleneck,
    }
