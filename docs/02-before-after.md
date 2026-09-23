# 02 — Before / After: BBS SG Bank Batch

Side-by-side of the legacy COBOL batch and the modern indexed batch. Every "after" claim
is tied to a line in [`modern/bank.py`](../modern/bank.py) or a re-runnable command. The
"before" column is tied to [`legacy/bank.cob`](../legacy/bank.cob).

> **Performance honesty.** This migration is an **algorithmic** improvement (`O(M·A)` →
> `O(A+M)`), stated as a fact derivable from the code. Wall-clock figures are now
> **measured** (28.6x and 128.1x) and always shown with the required disclosure that the
> workload is synthetic and the legacy design deliberately inefficient — never as a general
> claim about COBOL. See §6.

---

## 1. One-line summary

| | Before (legacy) | After (modern) |
|---|---|---|
| Paradigm | Flat-file, re-scan per operation | In-memory index, one pass |
| Cost | `O(operations × accounts)` | `O(accounts + operations)` |
| Writes per accepted op | Full file rewritten (via temp file) | None (single write at end) |
| Runtime deps | GnuCOBOL toolchain | Python 3 stdlib only |
| Output | `PROCESSED/REJECTED/TOTAL_CENTS` | Identical, byte-for-byte |

---

## 2. Data contract (unchanged — this is the point)

The two files are **not** reformatted. The pipe-delimited layout happens to be
byte-compatible with the fixed-column offsets the COBOL program reads, so both programs
consume the same bytes.

**`accounts.dat`** — one row per account, 21 chars:

```
00000001|000000000100
└1────8┘ └10─────21┘
 acct(8)   balance PIC 9(12)
```

- Legacy reads: `bank-row(1:8)` account (L115, L143); `bank-row(10:12)` balance (L78, L118, L152).
- Modern reads: `row.split("|")` → `account`, `int(cents)` (`bank.py` L11-13).

**`operations.dat`** — one row per operation, 32 chars:

```
D|00000001|00000002|000000000025
│ └1─8──┘  └12─19┘  └21───32┘
│  from(8)  to(8)   amount PIC 9(12)
kind(col 1)
```

- Legacy reads: `ops-row(1:1)`, `(3:8)`, `(12:8)`, `(21:12)` (`bank.cob` L89-92).
- Modern reads: `row.split("|")` → `kind, source, target, value` (`bank.py` L22-27).

Both write balances as `%012d` at the same offset (`bank.cob` L149/L156 vs `bank.py`
L44-46), which is why `scripts/benchmark.py` can assert byte-identical output.

---

## 3. Control flow

### Before — `legacy/bank.cob`

```
read operations.dat
for each operation:                     # O(M)
    validate (amount, kind, self-transfer)
    open accounts.dat; scan EVERY row    # O(A)  ← bank.cob L108-127
        find source, find dest, check funds
    if accepted:
        open accounts.dat; read all → write all to temp   # O(A)  ← L133-158
        open temp; read all → write all back to accounts  # O(A)  ← L160-171
read accounts.dat; sum balances          # O(A)  ← L74-84
display PROCESSED / REJECTED / TOTAL_CENTS
```

Per accepted operation the accounts file is fully traversed **three times** (find, rewrite
out, rewrite back). At the default benchmark size (1,200 accounts × ~400 ops) that is on
the order of 1.4 million row visits this program performs where ~1,600 suffice.

### After — `modern/bank.py`

```
load accounts.dat → dict                       # O(A)  ← L11-18
for each operation:                            # O(M)
    validate (kind, amount, source, target, funds)     # O(1) dict lookups ← L28-38
    mutate balances                                    # O(1) ← L39-42
write accounts.dat once                        # O(A)  ← L44-46
print PROCESSED / REJECTED / TOTAL_CENTS
```

Total: one read of accounts, one read of operations, one write of accounts. No temp file.

---

## 4. Validation rules — must stay identical

| Rule | Legacy (`bank.cob`) | Modern (`bank.py`) | Parity |
|---|---|---|---|
| Amount is a 12-digit numeric, non-zero | `is not numeric or = all "0"` (L94) | shape guard (L23) + `amount <= 0` (L30) | ✅ (fixed 2026-09-23) |
| Kind ∈ {D, W, T} | L99-103 | `kind not in {"D","W","T"}` (L29) | ✅ |
| No self-transfer | L105-108 | `source == target` for T (L32) | ✅ |
| Source account exists | `found-from` (L128-132) | `source not in accounts` (L31) | ✅ |
| Transfer destination exists | `found-to` (L128-132) | `target not in accounts` (L32) | ✅ |
| Non-deposit needs funds | L116-118 | `accounts[source] < amount` (L33) | ✅ |
| Deposit always allowed if source exists | L116 | falls through to apply (L39) | ✅ |

### Behavioral gaps

1. ~~Malformed amount (AT-11)~~ — **closed 2026-09-23.** `modern/bank.py` L23-25 rejects any
   row whose 4th field isn't a 12-char ASCII integer and **continues**, matching legacy;
   covered by `tests/test_modern.py::test_malformed_operations_are_rejected_and_batch_continues`.
2. **Accounts-file parsing still unguarded.** `modern/bank.py` L13 (`account, cents =
   row.split("|")`) assumes well-formed `accounts.dat`: a malformed master row raises,
   whereas the legacy total loop skips non-numeric balances (`bank.cob` L78). Low priority
   (the master file is machine-written) but it is a real difference — safe to note.
3. **Duplicate IDs and 12-digit overflow (intentional safety divergence).** The modern
   engine **rejects duplicate account IDs** (`ValueError: duplicate account id`, raised
   before any write, `bank.py` L14-15) and **rejects a balance overflow** that would exceed
   `PIC 9(12)` / `MAX_BALANCE_CENTS` (`bank.py` L34-35). The legacy COBOL instead keeps and
   rewrites duplicate rows and **truncates** an out-of-range balance. The modern behaviour is
   deliberate (fail closed rather than silently corrupt a balance); it is characterized by
   `scripts/test_bank.py` (`test_duplicate_account_ids`,
   `test_balance_overflow_truncates_in_legacy`) and `tests/test_modern.py`
   (`test_balance_overflow_is_rejected_without_widening_ledger_record`,
   `test_duplicate_accounts_fail_before_any_write`).

---

## 5. Code & maintainability

| Dimension | Before | After |
|---|---|---|
| Source | `bank.cob` (172 lines, COBOL) | `bank.py` (54 lines / 2,070 bytes, Python) |
| State | Implicit in file + temp file | Explicit `dict` |
| Unit-testable in isolation | Hard (file I/O per op) | Yes — `run(directory)` is pure-ish, returns a tuple; 5 tests in `tests/test_modern.py` |
| Field handling | Magic offsets `(1:8)`, `(10:12)` | Named fields from `split("|")` |
| Toolchain to run | GnuCOBOL (`cobc`) | `python3` (already on the box) |
| Demonstrable | Compile + run CLI | Same engine behind a local web app (`site/`), plus CLI |
| Output surface | `PROCESSED/REJECTED/TOTAL_CENTS` | identical |

---

## 6. Performance — measured

**Algorithmic claim (derivable from code):**
- Asymptotic cost drops from `O(operations × accounts)` to `O(accounts + operations)`.
- Full-file rewrites drop from *one-or-more per accepted operation* to exactly **one per
  run**. I/O bytes written scale with `O(accounts)` instead of `O(accepted × accounts)`.

**Measured (verified 2026-09-23; isolated GnuCOBOL 3.2.0, `cobc` at
`/tmp/gcb-build/install/bin/cobc`).** All runs restore inputs before every iteration, use
seed `20260923`, and report **`parity: … byte-identical accounts.dat: YES`**:

| Fixture (accounts × ops) | Legacy median | Modern median | Speedup | Transcript |
|---|---|---|---|---|
| 1,200 × 400 | 1.003951 s | 0.035133 s | **28.6x** | `scripts/evidence/benchmark-1200x400.txt` |
| 5,000 × 500 | 4.727858 s | 0.036914 s | **128.1x** | `scripts/evidence/benchmark-5000x500.txt` |

Reproduce:

```bash
GNUBOL_PREFIX=/tmp/gcb-build/install python3 scripts/benchmark.py --accounts 1200 --operations 400
GNUBOL_PREFIX=/tmp/gcb-build/install python3 scripts/benchmark.py --accounts 5000 --operations 500
```

The sweep (`scripts/evidence/benchmark-sweep.txt`, ops fixed at 200) shows the ratio grows
with the account count — the signature of the `O(m×n)` → `O(m+n)` change:

| Accounts | Legacy (s) | Modern (s) | Speedup | Parity |
|---|---|---|---|---|
| 300 | 0.146254 | 0.033967 | 4.3x | ok |
| 600 | 0.274801 | 0.034295 | 8.0x | ok |
| 1200 | 0.452227 | 0.034538 | 13.1x | ok |
| 2400 | 0.854747 | 0.034683 | 24.6x | ok |

> **Mandatory disclosure.** The 128.1x figure (and the sweep) are from a **synthetic
> workload** measured against a **deliberately inefficient legacy design** — `bank.cob`
> re-reads the whole master file once per operation and rewrites it in full. The ratio is a
> property of *that* access pattern, **not** a general claim about COBOL, GnuCOBOL, or
> banking workloads generally. The modern run is ~0.035 s regardless of account count,
> which is why the ratio scales with `n`. Report these numbers only together with this
> disclosure.

**Live COBOL execution in the operator terminal.** The `legacy-ui/` terminal is not a
replay: with its helper server running it compiles the unmodified `legacy/bank.cob` and
runs it as a real subprocess. A live 1,200-account / 400-operation job (preset `M`)
reported **400 processed, 3 rejected** in **1.197 s of actual COBOL execution** (**1.234 s**
overall, wall clock), and the modern engine's `TOTAL_CENTS` (**5489403400**) matched — the
same synthetic-fixture / deliberately-inefficient-legacy disclosure applies.

> **Honesty check.** The demo app's `GET /api/benchmark` still reports the legacy side as
> `unavailable` and `speedup: null` on a machine without `cobc`; it never estimates.

---

## 7. Operability / impact

| Aspect | Before | After |
|---|---|---|
| Deploy artifact | Compiled binary per platform | `bank.py` (portable) |
| New-analyst onboarding | Requires COBOL fluency | Python |
| Change safety net | None in repo | Parity harness `scripts/benchmark.py` + `tests/test_modern.py` |
| Demonstrable to non-engineers | CLI stdout only | Local web app (`site/`) showing before/after, live batch and audit trail |
| Scaling with volume | Degrades super-linearly | Linear |
| Downstream compatibility | n/a | Preserved (same file format & stdout contract) |
