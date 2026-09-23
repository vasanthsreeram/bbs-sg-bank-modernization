/* JavaScript port of modern/bank.py.

   The Python engine reads accounts.dat / operations.dat from a directory and
   rewrites accounts.dat.  Workers have no filesystem, so this port operates on
   the same two file bodies as strings: the caller passes in the exact bytes it
   would have written and receives the exact bytes the Python engine would have
   written back, plus the same PROCESSED / REJECTED / TOTAL_CENTS counters.

   Validation order, rejection reasons and integer-cent arithmetic mirror
   modern/bank.py line for line. */

import { isAscii, isDigit, splitLines } from "./py.mjs";

export const MAX_BALANCE_CENTS = 999999999999;

const KINDS = new Set(["D", "W", "T"]);

function serialiseAccounts(accounts) {
  let rows = "";
  for (const [account, balance] of accounts) {
    rows += `${account}|${String(balance).padStart(12, "0")}\n`;
  }
  return rows;
}

/**
 * Run the batch over the supplied flat-file bodies.
 *
 * @param {{accountsText: string, operationsText: string}} input
 * @returns {{processed: number, rejected: number, total: number,
 *            accountsText: string, accounts: Map<string, number>}}
 */
export function run({ accountsText, operationsText }) {
  const accounts = new Map();
  for (const row of splitLines(accountsText)) {
    const parts = row.split("|");
    if (parts.length !== 2) {
      throw new Error(`too many values to unpack (expected 2)`);
    }
    const [account, cents] = parts;
    if (accounts.has(account)) {
      throw new Error(`duplicate account id: ${account}`);
    }
    if (
      account.length !== 8 ||
      !isAscii(account) ||
      !isDigit(account) ||
      cents.length !== 12 ||
      !isAscii(cents) ||
      !isDigit(cents)
    ) {
      throw new Error("invalid account record");
    }
    accounts.set(account, Number(cents));
  }

  let processed = 0;
  let rejected = 0;
  for (const row of splitLines(operationsText)) {
    const parts = row.split("|");
    if (parts.length !== 4 || parts[3].length !== 12 || !isAscii(parts[3]) || !isDigit(parts[3])) {
      rejected += 1;
      continue;
    }
    const [kind, source, target, value] = parts;
    const amount = Number(value);
    if (
      !KINDS.has(kind) ||
      amount <= 0 ||
      !accounts.has(source) ||
      (kind === "T" && (!accounts.has(target) || source === target)) ||
      (kind !== "D" && accounts.get(source) < amount) ||
      (kind === "D" && accounts.get(source) + amount > MAX_BALANCE_CENTS) ||
      (kind === "T" && accounts.get(target) + amount > MAX_BALANCE_CENTS)
    ) {
      rejected += 1;
      continue;
    }
    accounts.set(source, accounts.get(source) + (kind === "D" ? amount : -amount));
    if (kind === "T") {
      accounts.set(target, accounts.get(target) + amount);
    }
    processed += 1;
  }

  let total = 0;
  for (const balance of accounts.values()) total += balance;

  return { processed, rejected, total, accounts, accountsText: serialiseAccounts(accounts) };
}

/** modern/bank.py's __main__ output, for parity checks against the CLI. */
export function formatMetrics({ processed, rejected, total }) {
  return [
    `PROCESSED=${String(processed).padStart(8, "0")}`,
    `REJECTED=${String(rejected).padStart(8, "0")}`,
    `TOTAL_CENTS=${String(total).padStart(16, "0")}`,
  ].join("\n");
}
