# BBS SG Bank — 1980s operations terminal (synthetic demo)

A period green-screen operator terminal for the fictional BBS SG Bank nightly
batch. It looks and behaves like a 24×80 data-entry station: program function
keys, a menu, an account master file, an operations queue and a job journal.

The nightly batch is **not** a mock-up when the helper server is running: the
terminal submits the real `legacy/bank.cob` (compiled with the isolated GnuCOBOL
build) as a subprocess, streams the job's actual journal and elapsed wall-clock
time, and prints the counters the COBOL program itself produced.

> **Synthetic demo.** BBS SG Bank is fictional. Every account, balance and
> operation is generated from a seed on this machine. No real customers,
> credentials or banking systems are involved. The terminal repeats this in its
> status line, and any simulated screen is labelled `SIMULATED` on the screen
> itself.

## Run it

```sh
legacy-ui/run.sh                 # http://127.0.0.1:8792/
PORT=9000 legacy-ui/run.sh       # a different loopback port
```

Then open <http://127.0.0.1:8792/>. If the default port is taken, pass `PORT`.

No GnuCOBOL? Build the isolated one first (`scripts/get_cobc.sh`), or set
`$COBC`. Without it the terminal still starts, but it says `SIMULATED`
everywhere and never claims a job ran.

`terminal.html` also opens straight from the filesystem (`file://`). In that
case there is no helper server, so it runs on embedded synthetic data in
**labelled simulated mode**. To point a directly-opened file at the engine, add
`?engine=http://127.0.0.1:8792`.

## Using the terminal

| Key | Action |
| --- | --- |
| `ENTER` | send the marked field (or the command line) |
| `TAB` | next field |
| `ESC` | clear the marked field |
| `↑` `↓` / `PgUp` `PgDn` | page lists |
| `F1` | help and key legend |
| `F2` | operations menu |
| `F3` | return one level |
| `F4`/`F5` | refresh |
| `F6` | reset the ledger to opening |
| `F7` / `F8` | page up / page down |
| `F9` | submit the nightly batch (from the batch screen) |
| `F10` | job output |
| `F11` | disclosure |
| `F12` | log off |

The on-screen keypad below the screen is clickable; some browsers intercept the
function keys, so the keypad is the reliable route.

Typed commands: `ACCT <id>`, `OPS`, `BATCH`, `RUN S|M|L`, `JOB`, `JOURNAL`,
`SYS`, `MENU`, `HELP`, `DISCLOSURE`, `RESET`, `PAGE <n>`, `LOGOFF`.

## The batch, honestly

* Presets `S` (400 accounts / 150 ops), `M` (1,200 / 400) and `L` (5,000 / 500).
  The job re-reads and rewrites the whole master file for every operation, so the
  elapsed time really does grow with the account count — the delay on screen is
  the process's own wall clock, not an animation.
* The counters show the job's real reason for stopping: `S`/`M`/`L` include three
  operations pinned to the rejection paths (insufficient funds, unknown
  destination, self transfer), so `REJECTED=3` is expected.
* `VERIFY Y` re-runs the same fixture through the unmodified `modern/bank.py` and
  compares counters; the journal shows `PASS`/`FAIL`.
* The **spool window** is explicitly labelled *DISPLAY ONLY, NOT JOB OUTPUT*: the
  COBOL program prints only its three counters, so the scrolling rows are a
  simulated display of the queue.
* Per-row `POSTED`/`REJECTED` in the operations queue is a deterministic replay of
  the documented rules (the same rules `modern/bank.py` implements), used to label
  rows and to cross-check the job. The screen says so.

## Files

| File | Purpose |
| --- | --- |
| `terminal.html` | the terminal: markup, CRT styling and all screen logic (self-contained, no CDN) |
| `server.py` | standard-library helper server: fixtures, COBOL compile/run, journal, parity check |
| `run.sh` | starts the helper server on loopback |
| `tests/` | static checks, a headless interaction walkthrough and server/API tests |

## Tests

```sh
python3 legacy-ui/tests/test_terminal.py     # static + server/API + interaction
node legacy-ui/tests/interaction.mjs         # headless browser-style walkthrough
```

The interaction test needs the helper server running (`legacy-ui/run.sh`); it
drives the page through sign-on, the menus, paging, a real batch submission and
log-off, and asserts on what the screen renders.
