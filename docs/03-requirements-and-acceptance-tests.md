# 03 — Requirements & Acceptance Tests

Derived from the observed behaviour of [`legacy/bank.cob`](../legacy/bank.cob). The modern
implementation must match legacy semantics **exactly**, plus satisfy the modernization
non-functionals. Every test below is re-runnable.

**Result date:** 2026-09-23 · **Environment:** `python3` 3.14, isolated GnuCOBOL **3.2.0**
(`/tmp/gcb-build/install/bin/cobc`).
**Runners:** `scripts/test_bank.py` (33 tests), `tests/test_modern.py` (5 tests), the
`site/tests/` suite (50 tests) and `legacy-ui/tests/test_terminal.py` (20 tests), plus the
manual fixture below. These **executable local suites total 108 passing tests**; the Forge
**Testing v1** artifact (`docs/forge/testing.md`, 132 *proposed* cases) is a separate
**planning document, not an execution record**.

---

## 1. Functional requirements

| ID | Requirement | Source of truth |
|---|---|---|
| FR-1 | Process every record in `operations.dat` in file order, applying kinds `D` (deposit), `W` (withdraw), `T` (transfer). | `bank.cob` L65-171 |
| FR-2 | Reject an operation whose kind ∉ {D, W, T}. | `bank.cob` L99-103 |
| FR-3 | Reject an operation whose amount is non-positive or not a 12-digit numeric. | `bank.cob` L94-97 |
| FR-4 | Reject an operation whose source account is not present in `accounts.dat`. | `bank.cob` L128-132 |
| FR-5 | Reject a transfer whose destination is missing or equals the source. | `bank.cob` L105-108, L128-132 |
| FR-6 | Reject any non-deposit (`W`, `T`) whose amount exceeds the source balance. | `bank.cob` L116-118 |
| FR-7 | Persist resulting balances back to `accounts.dat`. | `bank.cob` L133-171 |
| FR-8 | Emit `PROCESSED`, `REJECTED`, and `TOTAL_CENTS` on stdout, zero-padded 8/8/16. | `bank.cob` L84-86 |
| FR-9 | For identical inputs, produce byte-identical `accounts.dat` and identical counts to legacy. | `bank.cob` semantics |
| FR-10 | Keep the on-disk record layout unchanged (fixed-width-compatible). | `bank.cob` L2-10, L34-48 |

## 2. Non-functional requirements

| ID | Requirement | Rationale |
|---|---|---|
| NFR-1 | Batch time is `O(accounts + operations)`; no per-operation full-file scan. | Removes the `bank.cob` L108 / L133 bottleneck. |
| NFR-2 | At most one write of `accounts.dat` per run; no temp-file shuffle. | Reduce I/O churn. |
| NFR-3 | Runs on Python 3 standard library only. | Portability, easy hosting. |
| NFR-4 | Malformed rows are rejected and processing continues (no whole-batch abort). | Match legacy tolerance; **met — `bank.py` L23-25, AT-11**. |
| NFR-5 | Behaviour is continuously verifiable by automated tests. | `scripts/test_bank.py` (legacy/parity) + `tests/test_modern.py` (engine) + `scripts/benchmark.py`. |

---

## 3. Shared test fixture

```bash
T=$(mktemp -d)
printf '%s\n' '00000001|000000000100' '00000002|000000000100' > "$T/accounts.dat"
printf '%s\n' \
 'D|00000001|00000000|000000000050' \
 'W|00000001|00000000|000000000020' \
 'T|00000002|00000001|000000000030' \
 'W|00000001|00000000|000000099999' \
 'T|00000001|00000001|000000000001' \
 'Z|00000001|00000000|000000000001' \
 'D|00000009|00000000|000000000001' > "$T/operations.dat"
python3 modern/bank.py "$T"
cat "$T/accounts.dat"
```

**Observed 2026-09-23:**

```
PROCESSED=00000003
REJECTED=00000004
TOTAL_CENTS=0000000000000230
00000001|000000000160
00000002|000000000070
```

---

## 4. Acceptance test matrix

| ID | Covers | Given → When → Then | Observed 2026-09-23 | Status |
|---|---|---|---|---|
| AT-1 | FR-1, FR-7 | acct1=100; `D acct1 50` → acct1=150 | acct1 advanced 100→150 within run | ✅ |
| AT-2 | FR-1, FR-7 | acct1=150; `W acct1 20` → acct1=130 | applied; no rejection | ✅ |
| AT-3 | FR-1, FR-7 | `T acct2→acct1 30` → acct2:100→70, acct1:130→160 | final `acct1=160`, `acct2=70` | ✅ |
| AT-4 | FR-6 | `W acct1 99999` with 160 available → rejected | counted in `REJECTED=4` | ✅ |
| AT-5 | FR-5 | `T acct1→acct1 1` → rejected (self) | counted in `REJECTED=4` | ✅ |
| AT-6 | FR-2 | `Z acct1 1` (bad kind) → rejected | counted in `REJECTED=4` | ✅ |
| AT-7 | FR-4, FR-5 | `D acct9 1` (unknown source) → rejected | counted in `REJECTED=4` | ✅ |
| AT-8 | FR-8 | stdout zero-padded 8/8/16 | `...00000003 / ...00000004 / 0000000000000230` | ✅ |
| AT-9 | FR-7, FR-10 | resulting `accounts.dat` layout unchanged | `00000001\|000000000160` (+`acct2`) | ✅ |
| AT-10 | FR-8 | `TOTAL_CENTS` = sum of balances | 160+70 = 230 = `0000000000000230` | ✅ |
| AT-11 | FR-3, NFR-4 | amount `ABCDEFGHIJKL` → reject & continue | **rejected; batch continued** (`bank.py` L23-25); verified 2026-09-23 | ✅ |
| AT-12 | FR-9 | legacy vs modern on identical input → identical output | **parity YES, byte-identical `accounts.dat`** in all `scripts/evidence/benchmark-*.txt`; verified 2026-09-23 | ✅ |
| AT-13 | NFR-1 | speedup grows with account count (linear modern vs quadratic legacy) | sweep 300→4.3x, 600→8.0x, 1200→13.1x, 2400→24.6x, all `parity ok` (`benchmark-sweep.txt`) | ✅ |

Expected counts cross-check: 3 accepted (D, W, T) and 4 rejected (insufficient, self,
bad-kind, unknown-source) ⇒ `PROCESSED=3`, `REJECTED=4`. ✔

**Automated coverage (2026-09-23).** `python3 tests/test_modern.py` →
`Ran 5 tests … OK`:

| Test | Covers |
|---|---|
| `test_deposit_withdrawal_and_transfer_use_integer_cents` | AT-1, AT-2, AT-3, AT-8 |
| `test_malformed_operations_are_rejected_and_batch_continues` | AT-11 |
| `test_overdraft_unknown_recipient_and_self_transfer_are_rejected` | AT-4, AT-5, AT-7 |
| `test_balance_overflow_is_rejected_without_widening_ledger_record` | Safety divergence: 12-digit overflow rejection (see `02-before-after.md` §4.3) |
| `test_duplicate_accounts_fail_before_any_write` | Safety divergence: duplicate-ID rejection |

Plus `scripts/test_bank.py` → **`Ran 33 tests … OK`** (with the isolated `cobc`): fixture
generator and metrics-parser units, legacy contract tests, legacy/modern parity tests on
byte-identical fixtures, characterization tests for documented divergences (including
duplicate IDs and 12-digit overflow), and an end-to-end `benchmark.py` integration test.

> Run them as `python3 tests/test_modern.py` and
> `GNUBOL_PREFIX=/tmp/gcb-build/install python3 scripts/test_bank.py`. The demo site
> (`site/tests/`, **50 tests**) and the operator terminal (`legacy-ui/tests/test_terminal.py`,
> **20 tests**) run separately.

---

## 5. Full parity / performance test (runnable)

```bash
# With the isolated GnuCOBOL 3.2.0 built by scripts/get_cobc.sh. Compiles legacy/bank.cob,
# generates identical fixtures for both programs, and asserts identical stdout +
# byte-identical accounts.dat before reporting any speedup.
GNUBOL_PREFIX=/tmp/gcb-build/install python3 scripts/benchmark.py --accounts 1200 --operations 400
```

- `benchmark.py` computes a `parity_ok` gate and **refuses to report** unless the two engines agree.
- `benchmark.py` prints the speedup **only after** the parity gate passes.
- The site equivalent is `GET /api/benchmark`, which reports the legacy side as
  `unavailable` and `speedup: null` when `cobc` is missing (never estimates).
- **Status: ✅ measured.** See `scripts/evidence/benchmark-1200x400.txt` (median
  **1.003951 s → 0.035133 s = 28.6x**) and `benchmark-5000x500.txt` (median
  **4.727858 s → 0.036914 s = 128.1x**). **Disclosure:** the fixtures are synthetic and the
  legacy design is deliberately inefficient (whole-file rewrite per operation); these are
  not general claims about COBOL. See `02-before-after.md` §6.

---

## 6. Definition of done

A requirement is *done* when its AT passes **and** has a saved transcript. Currently:
**AT-1…AT-13 all pass** — AT-1…AT-11 via the fixture and the 5 `tests/test_modern.py`
cases, AT-12/AT-13 via the byte-identical parity runs and the scaling sweep, plus 33
`scripts/test_bank.py` tests. The demo site (`site/tests/`, 50) and terminal
(`legacy-ui/tests/`, 20) suites pass independently. The documented safety divergence —
modern **rejects** duplicate account IDs and 12-digit balance overflow while legacy rewrites
duplicate rows and truncates the overflow — is intentional and covered by tests (see
`02-before-after.md` §4.3). The remaining caveat is **operational**, not correctness:
these were run **locally** with the isolated compiler, not yet against the public hosted
prototype (no `{HOSTED_URL}`).

### Next actions
1. Add a `tests/__init__.py` (or a pytest wrapper) so both suites run via one command.
2. Guard `accounts.dat` parsing (`bank.py` L13) to close the remaining robustness gap.
3. Re-run the benchmark on the deployment host once hosted, to record production-machine timings.
