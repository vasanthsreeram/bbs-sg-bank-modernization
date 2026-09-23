# BBS SG Bank — fictional demo site (`site/`)

A local, runnable prototype that shows a fictional bank moving from a COBOL nightly
flat-file batch to an always-on modern ledger: pre/post comparison, accounts and
transfers, an interactive batch console, a sample audit trail and an **honest**
benchmark.

> **Synthetic demo.** BBS SG Bank is not a real institution. There are no real customers,
> accounts, balances, credentials or personal data anywhere in this app, and nothing is
> transmitted to a bank or any third party. Every transaction is invented.
>
> In the UI this disclosure appears **once**, in the footer, with a compact
> `synthetic demo` marker in the header. The machine-readable copy is served from
> `GET /api/meta` (`disclaimer`, `fictional: true`).

---

## Run it

Requires Python 3.10+ (tested on 3.14). No packages to install — standard library only.

```bash
# from the repository root
python3 site/backend/app.py
# then open http://127.0.0.1:8770/
```

Or use the helper script:

```bash
./site/run.sh              # same as above
./site/run.sh --port 9000  # different port
./site/run.sh --open       # also opens your browser
```

Default address is **http://127.0.0.1:8770/**. The server binds to `127.0.0.1` only unless you
pass `--host`, and if the port is busy it automatically steps to the next free one and prints
which port it used. Stop it with `Ctrl+C`.

### Run the tests

```bash
cd site && python3 -m unittest discover -s tests -v
```

50 tests: ledger/engine behaviour, the HTTP API end-to-end, and static checks that
the frontend is wired up and has no external dependencies.

---

## What is on each tab

| Tab | What it shows |
| --- | --- |
| **Overview** | Side-by-side pre/post panels: a legacy-output replay beside the modern dashboard, plus a capability matrix and a link to the live COBOL operator terminal. Start `legacy-ui/run.sh` locally to open the terminal at `http://127.0.0.1:8792/`. |
| **Accounts** | The 12 demo accounts, opening vs current balance, and per-account activity from the audit trail. |
| **Transfers** | Post a deposit, withdrawal or transfer. Validation failures come back with the engine's reason. A "Force rejection" chip is there to demo the failure path. |
| **Batch console** | Generate a transfer-only batch (10–500 rows, seeded), optionally with 3 known-bad rows, run it, and see posted/rejected counts, per-row reasons and the value-conservation check. |
| **Benchmark** | Live measurement of both engines on identical fixtures, with the environment and methodology spelled out. |
| **Audit trail** | Every row the engine saw with status, reason, actor and channel; filters and JSON/CSV export. |

---

## How it is wired (and what is real)

```
browser (site/frontend: HTML + CSS + vanilla JS)
        │  fetch /api/...
        ▼
site/backend/app.py         stdlib HTTP server, localhost only
        │
        ├─ site/backend/service.py    ledger, validation, audit trail
        │        └─ writes accounts.dat / operations.dat in a temp dir and calls
        │           modern/bank.py  ← the UNMODIFIED batch engine, imported as-is
        │
        └─ site/backend/benchmark.py  timing harness
                 └─ uses scripts/harness.py (cobc discovery, fixtures, process
                    plumbing) when importable, else a built-in fallback
```

What that means in practice:

* **Postings really run the shared engine.** `service.py` writes the same flat files
  the CLI uses and calls `modern/bank.py:run()`. The site does not reimplement the
  ledger arithmetic; it re-simulates the rules only to attach a per-row reason, then
  cross-checks that prediction against the engine's own counters
  (`engine_matches_simulation`).
* **The seeded audit is real history.** The 12 illustrative rows are replayed through
  the engine at startup, so the balances you see are genuinely the result of that
  history (including 3 rows the engine rejects).
* **The overview green screen replays output.** Its counters come from this demo's
  ledger. The linked 1980s operator terminal runs the actual `legacy/bank.cob` on a
  separate local service and reports real COBOL wall-clock time, counters, and parity.
* **`legacy/`, `modern/` and `scripts/` are read-only inputs.** This app never edits
  them: it reads `legacy/bank.cob` for the code excerpt and calls into the other two.

---

## Benchmark honesty

* Both engines run **as separate processes** on **identical, deterministic fixtures**
  (`seed` is shown, along with the fixture SHA-256 when the shared harness provides it).
  Inputs are restored from the pristine copy before every timed run.
* Reported numbers are the **median and fastest of N timed runs** (default 3 + 1
  warm-up), including each program's process start-up. Nothing is hard-coded.
* **Output parity is checked first.** If the two engines disagree, no timing or
  comparison is reported at all.
* If no `cobc` is found, the legacy side reads **"Not measurable on this machine"**
  with the install hint — the site never substitutes an estimate. Run
  `scripts/get_cobc.sh` (builds GnuCOBOL into an isolated prefix under `/tmp`, no root
  or global changes) or set `$COBC`, then press *Measure now*.
* There is **no fixed "100x" style claim anywhere.** On a developer laptop with 1200
  accounts and 400 operations the measured ratio lands around 25–30x because the
  legacy program rescans the whole ledger per operation; that number is whatever the
  measurement says on your machine, and it is labelled as a single-host wall-clock
  indication, not a benchmark suite.

---

## API reference

`GET` unless noted. All responses are JSON; errors look like
`{"error": {"code": "...", "message": "..."}}`.

| Endpoint | Purpose |
| --- | --- |
| `/api/health` | Liveness + `fictional: true` |
| `/api/meta` | Site name, disclaimer, engine paths |
| `/api/summary` | Totals, posting counts, invariant check, last batch |
| `/api/accounts?q=` | Account list (id, name, product, opening/current balance, row count) |
| `/api/accounts/{id}` | One account plus its recent history |
| `/api/audit?limit=&status=&kind=` | Audit trail (`status` = `posted`/`rejected`, `kind` = `D`/`W`/`T`) |
| `/api/legacy/source` | `legacy/bank.cob` lines plus the bottleneck line numbers |
| `/api/benchmark?accounts=&operations=&repeats=&fresh=1` | Measured legacy vs modern report |
| `POST /api/operations` | Post one operation (`{kind, source, target, amount_cents}`) or `{operations: [...]}`. `201` when anything posted, `200` when every row was rejected |
| `POST /api/batch` | Generate and run a transfer-only batch (`{operations, seed, include_edge_cases, max_amount_cents}`) |
| `POST /api/reset` | Restore the seeded ledger and audit trail |

Example:

```bash
curl -s -X POST http://127.0.0.1:8770/api/operations \
  -H 'Content-Type: application/json' \
  -d '{"kind":"T","source":"10000007","target":"10000002","amount_cents":12345}'
```

### Validation rules (shared by both engines)

* `kind` must be `D`, `W` or `T`
* amount must be a positive whole number of cents (fits the COBOL `PIC 9(12)` field)
* the source account must exist
* for `T`, the destination must exist and differ from the source
* for `W` and `T`, the source balance must cover the amount

Rejected rows never change a balance; they are recorded in the audit trail with the
reason and counted in the batch results. A rejection is a business outcome, not a
transport failure, so `POST /api/operations` answers `200` with `posted: 0` rather than
an error status — the UI shows the reason in a toast and the audit trail.

---

## Layout

```
site/
├── backend/
│   ├── app.py          # HTTP server, JSON API, static file serving
│   ├── service.py      # ledger, validation mirror, audit trail, demo batch
│   └── benchmark.py    # measurement harness (cobc discovery + fixtures)
├── frontend/
│   ├── index.html      # single page, six tabs
│   ├── styles.css      # dark responsive theme + CRT panel
│   └── app.js          # vanilla JS, no build step, no CDN
├── tests/
│   ├── test_service.py # ledger and engine behaviour
│   ├── test_api.py     # end-to-end HTTP tests against a live server
│   └── test_frontend.py# static wiring/self-containment checks
├── run.sh
└── README.md
```

## Known limits

* The ledger is in-memory plus one temp directory per server process; restarting the
  server resets it (that is the point of a demo).
* There is no authentication, no TLS and no persistence by design — it binds to
  localhost and must not be exposed on a network.
* The mock green screen reproduces the legacy *output format*, not a real 3270
  session.
