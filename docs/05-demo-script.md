# 05 — Demo Script (2–3 minutes)

**Target length:** 2:30 (hard cap 3:00). **Presenter:** `{PRESENTER_NAME}`.
**Recording:** `{DEMO_VIDEO_URL}` · **Live app:** `{HOSTED_URL}`.

Rule for this demo: **show, don't claim.** We show the legacy code, run the modern batch
through the actual demo app, run both test suites, and show the measured parity/benchmark
transcripts. Every speedup figure is shown **only** with the disclosure that the workload is
synthetic and the legacy design deliberately inefficient (see `02-before-after.md` §6).

---

## Pre-flight checklist (do before recording)

- [ ] Hosted app reachable at `{HOSTED_URL}`; otherwise run locally:
      `python3 site/backend/app.py --open` (defaults to `http://127.0.0.1:8765/`).
- [ ] `legacy/bank.cob` open at the two bottleneck comments (L108, L133) in a side tab.
- [ ] Forge project tab open: `https://hackathon.softwareforge.ai/projects/6de0abcc-6025-4b07-9e5c-2308e8f4fe10` (Assessment complete, ForgeScore 57/100; Intent v1, PRD-Spec v1, Architecture v1 and User Stories v1 approved and exported, Testing v1 generated and exported, to `docs/forge/`; Delivery pending).
- [ ] Terminal ready for both suites: `GNUBOL_PREFIX=/tmp/gcb-build/install python3 scripts/test_bank.py` and `python3 tests/test_modern.py`.
- [ ] Demo site suites ready (`site/tests/`, 50 tests) and the operator terminal ready (`legacy-ui/run.sh`, 20 tests) if showing the real-COBOL job.
- [ ] Benchmark transcripts open: `scripts/evidence/benchmark-1200x400.txt` (and `-5000x500.txt`).
- [ ] Fixture files staged for the CLI fallback (content in `03-...` §3).
- [ ] Terminal font large; notifications off; browser zoom ~125%.
- [ ] If `cobc` is not on `PATH`, know the fallback line: *"This host lacks GnuCOBOL, so the
      app reports the legacy time as unavailable — here are the transcripts from a host
      that has it."* (Never invent a number.)

---

## Script

### 0:00–0:20 — Hook (screen: app **Overview** tab)

> "BBS SG Bank runs its overnight batch on this: a COBOL program that, for **every single
> transaction**, re-opens the accounts file and scans **every account**, then rewrites the
> whole file. Deposit, withdraw, transfer — same cost every time. This is the app we built
> around the modernized engine; everything you'll see runs live against the real batch code."

### 0:20–0:45 — Before (screen: `legacy/bank.cob`, highlight L108 + L133)

> "Two lines tell the story. Line 108: *'reopen and scan the flat file for every
> operation.'* Line 133: *'rewrite every account for every accepted operation.'* The cost is
> **operations times accounts** — it gets quadratically worse as the bank grows. The fix
> isn't faster COBOL; it's not doing that work at all."

### 0:45–1:20 — After (screen: **Batch console** tab → Run a batch)

> "The modern engine loads accounts **once** into an in-memory index, applies each operation
> with a constant-time lookup, and writes the file **once** — `O(accounts + operations)`
> instead of `O(operations × accounts)`. I'll run a 60-operation batch."

Click **Run a batch**; point at the result panel.

> "Notice three things: the ledger total is **unchanged** — transfers only move value, they
> don't create it; the rejected rows are broken out by reason; and this 'engine matches
> simulation' check confirms the UI's expectations agree with what the batch actually did.
> The site runs the *unmodified* engine, not a reimplementation."

### 1:20–1:50 — Correctness (screen: terminal → run both suites, then open the transcripts)

> "We don't ask you to trust that. The core suites pass: 33 tests in `scripts/test_bank.py` and 5
> in `tests/test_modern.py` — covering deposits, withdrawals, transfers, every rejection
> case, malformed input, and the duplicate-ID / overflow safety checks. The demo site has 50
> more and the operator terminal 20. And here's the parity proof: the harness compiles the
> **real** COBOL and the modern batch, runs them on byte-identical fixtures, and confirms
> **identical output and byte-identical account files**."

```bash
GNUBOL_PREFIX=/tmp/gcb-build/install python3 scripts/test_bank.py     # Ran 33 tests … OK
python3 tests/test_modern.py                                          # Ran 5 tests … OK
```

Open `scripts/evidence/benchmark-1200x400.txt`.

> "Same results on both engines. And because we've now built GnuCOBOL, the harness can time
> both: the legacy batch takes about a second at 1,200 accounts versus 35 milliseconds for
> the modern engine — **28.6x** — and at 5,000 accounts it's **128.1x**. The operator
> terminal runs that same real COBOL live: a 1,200×400 job did **400 processed, 3 rejected**
> in **1.197 s of actual COBOL execution** (1.234 s overall), and the modern engine's total
> matched. Two honest caveats: this is a **synthetic** workload, and the legacy design is
> **deliberately** inefficient — it rewrites the whole ledger per operation — so this is a
> fact about that algorithm, not a claim about COBOL in general."

### 1:50–2:15 — How we built it (screen: Forge pipeline slide)

> "We drove the **planning** of this through the Opsera Forge pipeline. We uploaded the
> legacy folder to Forge and its **Assessment is complete**: ForgeScore **57 out of 100 —
> Developing**, with **10 findings including 3 high**, flagging exactly the `O(m×n)` scans,
> the full-file rewrites, and the missing specs. We approved and downloaded **Intent v1**,
> **PRD-Spec v1**, **Architecture v1** and **User Stories v1** (6 epics / 33 proposed stories),
> and Forge **generated and exported Testing v1** (132 proposed test cases) — that page had no
> Approve button — all into `docs/forge/` with recorded hashes. The
> stories and test cases are **proposals**, not implemented features or executed tests; the
> local suites are separate and total 108 passing. The supplied MCP token still returns 401,
> so we pulled the documents through the signed-in browser, which works. To be clear: Forge
> authored the planning documents, and its proposals (safe temp-file replacement, append-only
> audit, FastAPI, Forge Shipping) are **not implemented**; the modern Python is our own code —
> Forge assessed and framed the work; it didn't write or run the engine, and nothing is
> deployed."

### 2:15–2:35 — Impact + close (screen: impact slide)

> "The impact: a super-linear batch becomes linear — **one file write per run instead of one
> per transaction** — no GnuCOBOL toolchain, an audit trail for every posting, and tests
> that guard every future change. That's BBS SG Bank's batch, modernized, with the proof in
> the repo."

---

## Timing table

| Segment | Length | Cumulative |
|---|---|---|
| Hook / problem | 0:20 | 0:20 |
| Before (legacy) | 0:25 | 0:45 |
| After (live batch) | 0:35 | 1:20 |
| Correctness (tests + measured parity) | 0:30 | 1:50 |
| Forge pipeline | 0:25 | 2:15 |
| Impact + close | 0:20 | 2:35 |

## Do / Don't

| ✅ Do | ❌ Don't |
|---|---|
| Show the two bottleneck lines in real code | Quote a speedup without the synthetic-workload disclosure |
| Run a batch live in the app | Hand-wave the parity check |
| Show the measured transcripts (28.6x / 128.1x) with the disclosure | Present 128.1x as a general COBOL or banking claim |
| State "33 + 5 core tests pass; parity byte-identical" if asked | Claim the prototype has a public hosted URL |
| Credit Forge for the Assessment, Intent v1 and PRD-Spec v1 documents | Claim Forge generated or ran the modern engine |

## Q&A crib

| Likely question | Answer |
|---|---|
| "Prove the speedup." | "Measured with isolated GnuCOBOL 3.2.0: 1.004s→0.035s (**28.6x**) at 1200×400 and 4.728s→0.037s (**128.1x**) at 5000×500, parity byte-identical. Synthetic fixtures against a deliberately inefficient legacy design — not a general COBOL claim." |
| "How do you know it's correct?" | "33 tests in `scripts/test_bank.py` + 5 in `tests/test_modern.py` (plus 50 site and 20 terminal tests); the parity runs assert byte-identical account files." |
| "Is the UI a separate reimplementation?" | "No — `site/backend/service.py` calls the unmodified `modern/bank.py` engine and cross-checks its counts against a simulation after every batch." |
| "Where did Forge help?" | "The Forge Assessment is complete — 57/100, 10 findings incl. 3 high — and Intent v1, PRD-Spec v1, Architecture v1 and User Stories v1 (33 proposed stories) are approved, while Testing v1 (132 proposed cases) was generated and exported without an approval step; all are downloaded into `docs/forge/` (hashes recorded). Those stories/tests are proposals, not code or runs; our local suites are 108 passing. Every stage maps to an artifact under `docs/forge/` (doc 04). Forge authored the planning documents; we wrote the engine." |
| "What's unfinished?" | "The raw Assessment export, the Delivery stage, public hosting, demo recording, and per-member posts." |
