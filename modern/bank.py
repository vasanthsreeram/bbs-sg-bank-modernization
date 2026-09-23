"""Indexed replacement for the mock bank's flat-file daily batch."""

from pathlib import Path
import sys


MAX_BALANCE_CENTS = 999_999_999_999


def run(directory: Path) -> tuple[int, int, int]:
    accounts = {}
    for row in (directory / "accounts.dat").read_text().splitlines():
        account, cents = row.split("|")
        if account in accounts:
            raise ValueError(f"duplicate account id: {account}")
        if len(account) != 8 or not account.isascii() or not account.isdigit() or len(cents) != 12 or not cents.isascii() or not cents.isdigit():
            raise ValueError("invalid account record")
        accounts[account] = int(cents)

    processed = rejected = 0
    for row in (directory / "operations.dat").read_text().splitlines():
        parts = row.split("|")
        if len(parts) != 4 or len(parts[3]) != 12 or not parts[3].isascii() or not parts[3].isdigit():
            rejected += 1
            continue
        kind, source, target, value = parts
        amount = int(value)
        if (
            kind not in {"D", "W", "T"}
            or amount <= 0
            or source not in accounts
            or (kind == "T" and (target not in accounts or source == target))
            or (kind != "D" and accounts[source] < amount)
            or (kind == "D" and accounts[source] + amount > MAX_BALANCE_CENTS)
            or (kind == "T" and accounts[target] + amount > MAX_BALANCE_CENTS)
        ):
            rejected += 1
            continue
        accounts[source] += amount if kind == "D" else -amount
        if kind == "T":
            accounts[target] += amount
        processed += 1

    (directory / "accounts.dat").write_text(
        "".join(f"{account}|{balance:012d}\n" for account, balance in accounts.items())
    )
    return processed, rejected, sum(accounts.values())


if __name__ == "__main__":
    processed, rejected, total = run(Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd())
    print(f"PROCESSED={processed:08d}")
    print(f"REJECTED={rejected:08d}")
    print(f"TOTAL_CENTS={total:016d}")
