# 01 — Modernization Journal (BBS SG Bank COBOL → Modern)

**System:** BBS SG Bank daily batch (`accounts.dat` + `operations.dat`, line-sequential).
**Scope:** `legacy/bank.cob` → `modern/bank.py`, parity-checked by `scripts/benchmark.py`,
wrapped by the demo app in `site/`.
**Owner of this doc:** `{TEAM_NAME}`.
**Last updated:** `{DATE}` (2026-09-23).

> **How to read this file.** This is a *truthful* journal. A step is only ✅ when its
> evidence cell points at something a judge can re-run **today**. Steps without evidence are
> ⛔ Pending (not started) or 🚫 Blocked (waiting on a named prerequisite). No Opsera Forge
> output is written down that we did not actually obtain. No speedup is stated that we did
> not actually measure.
>
> **Line numbers** were checked on 2026-09-23. This is a **shared workspace**; re-verify
> before submission.

Status legend: ✅ Verified · 🟡 In progress · ⛔ Pending · 🚫 Blocked · ❌ Failing · ➖ N/A.

---

## Phase 0 — Assessment (understand the legacy)

| # | Step | Status | Evidence | Notes |
|---|---|---|---|---|
| 0.1 | Locate and read the legacy batch | ✅ | [`legacy/bank.cob`](../legacy/bank.cob), 172 lines | Free-format COBOL (GnuCOBOL). Its own header (L2-29) documents the data layout and the `O(m×n)` cost. |
| 0.2 | Identify data contracts | ✅ | `bank.cob` L34-48 (select/FD), L89-92 (operation offsets) | `accounts.dat`: acct = cols 1-8, balance = cols 10-21 (`PIC 9(12)`). `operations.dat`: kind=col 1, from=3-10, to=12-19, amount=21-32. |
| 0.3 | Identify the performance bottleneck | ✅ | `bank.cob` L108 ("reopen and scan... for every operation"), L133 ("rewrite every account for every accepted operation") | Two nested full-file loops ⇒ `O(operations × accounts)`; plus a temp-file copy each accepted op. |
| 0.4 | Confirm legacy validation rules | ✅ | `bank.cob` L94-97 (amount), L99-103 (kind), L105-108 (self-transfer), L114-132 (existence/funds) | Rules: numeric & non-zero amount; kind ∈ {D,W,T}; no self-transfer; source/dest must exist; non-deposit needs funds; malformed line ⇒ rejected, not fatal (header L26-28). |
| 0.5 | Run Opsera Forge **Assessment** on the legacy code | ✅ | Forge project [`6de0abcc-…`](https://hackathon.softwareforge.ai/projects/6de0abcc-6025-4b07-9e5c-2308e8f4fe10) (from `/tmp/bbs-sg-legacy.zip`); Assessment **complete** — ForgeScore **57/100 (Developing)**, **10 findings incl. 3 high** (`O(m×n)` scans, full-file rewrites, missing specs) | Score/findings read from the signed-in UI, 2026-09-23. See `04-forge-pipeline-mapping.md` §Stage 1. |
| 0.6 | Confirm GnuCOBOL toolchain for parity runs | ✅ | `scripts/get_cobc.sh` → GnuCOBOL **3.2.0** at `/tmp/gcb-build/install/bin/cobc` | Unblocks 5.1-5.2. |

**Assessment summary (our own analysis, not a Forge output):** the program is I/O-bound,
not CPU-bound. Per operation it performs one full scan to find/validate the accounts and
then two full passes to rewrite the file through a temp file. Cost scales with
`operations × accounts`, so higher transaction volume degrades super-linearly.

---

## Phase 1 — Intent

| # | Step | Status | Evidence | Notes |
|---|---|---|---|---|
| 1.1 | Draft modernization intent | ✅ | This doc, "Intent" block below | Written by the team. |
| 1.2 | Generate/record Forge **Intent** artifact | ✅ | [`docs/forge/intent.md`](forge/intent.md), SHA-256 `8510138776e8…94cc` | **Intent v1 approved** in the signed-in UI and downloaded (2026-09-23); full hash in [`docs/forge/README.md`](forge/README.md). Artifact id `0e0655e7-62be-4351-b2c3-b954feb6c49b`. Map in `04-...` §Stage 2. |

**Intent (team-authored):** *Preserve exact BBS SG Bank batch semantics while removing the
per-operation full-file scan/rewrite. Modernize to an indexed, single-write batch, keep the
on-disk formats byte-compatible so downstream consumers are unaffected, and make the
behaviour continuously re-verifiable by an automated parity test.*

---

## Phase 2 — PRD / Spec

| # | Step | Status | Evidence | Notes |
|---|---|---|---|---|
| 2.1 | Write functional requirements | ✅ | [`03-requirements-and-acceptance-tests.md`](03-requirements-and-acceptance-tests.md) FR-1…FR-10 | Derived from `bank.cob` behaviour. |
| 2.2 | Write non-functional requirements | ✅ | `03-...` NFR-1…NFR-5 | Linearity, single write, stdlib-only, robustness. |
| 2.3 | Generate/record Forge **PRD-Spec** artifact | ✅ | [`docs/forge/prd.md`](forge/prd.md), SHA-256 `8b138ae25790…3453` | **PRD-Spec v1** generated (reported ~95% confidence), approved, and downloaded (2026-09-23); exported. Map in `04-...` §Stage 3. |

---

## Phase 3 — Architecture

| # | Step | Status | Evidence | Notes |
|---|---|---|---|---|
| 3.1 | Design the modern algorithm | ✅ | [`modern/bank.py`](../modern/bank.py) L10-47 | Load `accounts.dat` into a dict once → apply ops with O(1) lookups → write once. |
| 3.2 | Preserve on-disk format | ✅ | `bank.py` L11-18, L44-46 | Pipe layout is byte-compatible with the fixed-column layout the legacy program reads (see `02-before-after.md` §2). |
| 3.3 | Capture Forge **Architecture** artifact | ✅ | [`docs/forge/architecture.md`](forge/architecture.md), SHA-256 `d0be1c535a37…058b` | **Architecture v1 completed** (reported ~100% confidence), approved and downloaded (2026-09-23). Map in `04-...` §Stage 4. |
| 3.4 | Decompose into Forge **User Stories / work orders** | ✅ | [`docs/forge/work-orders.md`](forge/work-orders.md), SHA-256 `a78ac60579ae…cd0d2` | **User Stories v1**: 6 epics / **33 proposed stories**, ~75% reported confidence, approved and downloaded (2026-09-23). Proposed work, not implemented. Map in `04-...` §Stage 5. |

**Architecture decision record (team-authored):**
- **Don't** port the flat-file shuffle. The file was incidental state, not a requirement.
- **Do** model accounts as an in-memory index (`dict[str, int]`) so an operation is O(1).
- **Don't** change the transaction semantics or the rejection rules — parity is a hard gate.
- **Do** keep a single writer at the end so the file is touched once per run.
- **Do** run the *unmodified* engine behind the demo UI so the site exercises the real code
  path, not a reimplementation (`site/backend/service.py` header).

---

## Phase 4 — Implementation

| # | Step | Status | Evidence | Notes |
|---|---|---|---|---|
| 4.1 | Legacy program in repo | ✅ | [`legacy/bank.cob`](../legacy/bank.cob) | Provenance/authorship not recorded here — do not over-claim. |
| 4.2 | Indexed modern implementation | ✅ | [`modern/bank.py`](../modern/bank.py) L10-47 | `run()` returns `(processed, rejected, total)`. |
| 4.3 | Output contract preserved (`PROCESSED/REJECTED/TOTAL_CENTS`) | ✅ | `bank.py` L52-54 | Same 8/8/16-digit zero-padded lines as `bank.cob` L84-86. |
| 4.4 | Malformed-row robustness (reject-and-continue) | ✅ | `bank.py` L23-25 (`len(parts) != 4 or len(parts[3]) != 12 or not parts[3].isascii() or not parts[3].isdigit()` → `rejected`) | Matches the legacy header's promise (L26-28). Closes former AT-11. |
| 4.5 | Fictional demo web app over the real engine | ✅ | [`site/backend/app.py`](../site/backend/app.py) (303 lines), [`site/frontend/index.html`](../site/frontend/index.html) (489 lines) | Stdlib-only HTTP server; `site/backend/service.py` (508 lines) wraps `modern/bank.py`. Smoke-tested 2026-09-23. |
| 4.6 | Forge-driven implementation of the modern engine | ➖ | `modern/bank.py` is team-authored **local** code | **Forge did not generate the modern Python.** Forge produced the Assessment and the exported Intent v1, PRD-Spec v1, Architecture v1, User Stories v1 and Testing v1 planning documents. The 33 stories and 132 test cases are **proposed**, not implemented or executed. |

---

## Phase 5 — Testing (parity + acceptance)

| # | Step | Status | Evidence | Notes |
|---|---|---|---|---|
| 5.1 | Legacy↔modern **parity** run (identical rows, counts, totals) | ✅ | `scripts/evidence/benchmark-1200x400.txt`, `benchmark-5000x500.txt`, `benchmark-sweep.txt` all report `parity: … byte-identical accounts.dat: YES` | Verified 2026-09-23 with isolated GnuCOBOL 3.2.0. |
| 5.2 | Measured speedup | ✅ | median **1.003951s → 0.035133s = 28.6x** (1200×400); median **4.727858s → 0.036914s = 128.1x** (5000×500, synthetic) | See `02-before-after.md` §6 for the required synthetic-workload disclosure. |
| 5.3 | Automated tests (modern engine) | ✅ | [`tests/test_modern.py`](../tests/test_modern.py) → **Ran 5 tests … OK** (2026-09-23) | Covers deposits/withdrawals/transfers, overdraft/unknown/self-transfer, malformed-row continuation, and the duplicate-ID / 12-digit-overflow safety divergence. |
| 5.4 | Acceptance tests AT-1…AT-11 (modern behaviour) | ✅ | Re-run per [`03-...`](03-requirements-and-acceptance-tests.md); outputs captured there | Verified 2026-09-23. |
| 5.5 | Legacy/parity contract suite | ✅ | [`scripts/test_bank.py`](../scripts/test_bank.py) → **Ran 33 tests … OK** (3.2s) | Unit tests (fixture generator, metrics parser), legacy contract tests, parity tests, characterization tests (incl. the duplicate-ID / overflow divergence), end-to-end benchmark test. Skips legacy cases if `cobc` is absent. |
| 5.6 | Demo-site test suite | ✅ | `site/tests/` → **50 tests** (service, HTTP API, frontend wiring) | Confirms the site calls the unmodified engine. |
| 5.7 | Operator-terminal test suite | ✅ | [`legacy-ui/tests/test_terminal.py`](../legacy-ui/tests/test_terminal.py) → **Ran 20 tests … OK** | Includes one genuine COBOL batch run and the headless interaction walkthrough; see 6.7. |
| 5.8 | Forge **Testing** artifact linked | ✅ | [`docs/forge/testing.md`](forge/testing.md), SHA-256 `19749260605e…92b3` | **Testing v1**: **132 proposed test cases** (33 functional / 33 smoke / 33 regression / 33 performance), **generated and exported — not approved** (no Approve action shown). A generated **planning artifact** — **not 132 executed tests**; the local executable suites remain **108 passing**. Map in `04-...` §Stage 6. |

---

## Phase 6 — Delivery

| # | Step | Status | Evidence | Notes |
|---|---|---|---|---|
| 6.1 | Demo app runs locally | ✅ | `python3 site/backend/app.py --port 8791`; `GET /api/health` → `{"status":"ok","fictional":true}`; `GET /` → 200 | Verified 2026-09-23. |
| 6.2 | Hosted prototype deployed to a public URL | ⛔ | placeholder `{HOSTED_URL}` | **Required for submission.** The app is deployable; only hosting remains. |
| 6.3 | Short demo recorded (≤3 min) | ⛔ | placeholder `{DEMO_VIDEO_URL}` | Script ready in [`05-demo-script.md`](05-demo-script.md). |
| 6.4 | Before/after write-up | ✅ | [`02-before-after.md`](02-before-after.md) | Complete, evidence-linked. |
| 6.5 | Per-teammate public post | ⛔ | `{MEMBER_n_POST_URL}` | Outlines ready in [`06-social-posts.md`](06-social-posts.md). |
| 6.6 | Submission checklist signed | 🟡 | [`07-submission-checklist.md`](07-submission-checklist.md) | Open gates: public hosting, demo recording, per-member posts, and the raw Assessment export. |
| 6.7 | Operator terminal runs the **real** COBOL batch | ✅ | [`legacy-ui/`](../legacy-ui/) | Live 1,200×400 job: **400 processed, 3 rejected**, **1.197 s** actual COBOL execution (**1.234 s** overall), matching the modern engine's `TOTAL_CENTS` **5489403400**. Synthetic fixture; deliberately inefficient legacy design. |
| 6.8 | Forge Intent, PRD-Spec, Architecture, User Stories + Testing v1 exported | ✅ | [`docs/forge/`](forge/) | Intent, PRD-Spec, Architecture and User Stories were **approved** in the signed-in UI and downloaded; **Testing v1 was generated/exported but not approved** (its browser page showed no Approve action). SHA-256 in `docs/forge/README.md`. User Stories = 6 epics / 33 **proposed** stories; Testing = 132 **proposed** cases (not executed). Assessment raw report still unexported; Delivery pending. |

---

## Blocked-work register (what unblocks us)

| Blocked step | Prerequisite | Action |
|---|---|---|
| ~~5.1, 5.2~~ | ~~GnuCOBOL `cobc`~~ | **Resolved 2026-09-23:** isolated GnuCOBOL 3.2.0 built by `scripts/get_cobc.sh`; parity and timings captured under `scripts/evidence/`. |
| Export remaining Forge artifacts (raw Assessment report, Delivery) | Forge artifact-export credential | Forge project **already created**; Assessment **complete** (raw report unexported; `docs/forge/assessment.md` is a team transcript); Intent v1, PRD-Spec v1, Architecture v1 and User Stories v1 **approved and downloaded**, and Testing v1 **generated and downloaded** (no Approve action shown), to `docs/forge/`. The supplied MCP `forge_` token returns HTTP 401 `Invalid or revoked token`, but **signed-in browser downloads work** (that is how the exports were retrieved). Use browser downloads for the rest, or issue a fresh token (Profile → API Tokens). |
| 6.2 | Public hosting target | Deploy `site/backend/app.py`; set `{HOSTED_URL}`. |
| 6.3, 6.5 | Recording + publishing | Follow `05-`/`06-`; set the placeholder URLs. |

---

## Evidence log (append-only)

| Date | Command / artifact | Result |
|---|---|---|
| 2026-09-23 | `python3 modern/bank.py <fixture>` (2 accounts, 7 ops incl. 3 edge cases) | `PROCESSED=00000003`, `REJECTED=00000004`, `TOTAL_CENTS=0000000000000230`; balances `…160`, `…070` |
| 2026-09-23 | `python3 tests/test_modern.py` | `Ran 5 tests … OK` |
| 2026-09-23 | `python3 site/backend/app.py --port 8791` → `/api/health`, `/api/summary`, `/api/benchmark`, `/` | health ok; summary `invariant_ok: True`, engine `modern/bank.py`; benchmark modern `0.0336s` (300 ops), legacy `unavailable`, `speedup: null`; `/` → 200 |
| 2026-09-23 | `which cobc` | not found → parity/perf blocked |
| 2026-09-23 | `python3 scripts/benchmark.py` | `error: GnuCOBOL is required: install cobc first` |
| 2026-09-23 | Forge UI: created project [`6de0abcc-…`](https://hackathon.softwareforge.ai/projects/6de0abcc-6025-4b07-9e5c-2308e8f4fe10) from `/tmp/bbs-sg-legacy.zip` | project URL recorded; ZIP contains `bbs-sg-legacy/bank.cob`, SHA-256 `f4730e6d2b3867a5d8908a6dc0f77e714826f15d23118a3f8e42d7f0b2afc21d` |
| 2026-09-23 | Forge UI: **Assessment / ForgeScore** | observed **generating** at the time; later completed — see the Assessment-complete row below |
| 2026-09-23 | Forge MCP with supplied `forge_` token | HTTP 401 `Invalid or revoked token` → machine export blocked (UI still usable) |
| 2026-09-23 | `shasum -a 256 legacy/bank.cob` (working tree) | `74669316…446f467` — **differs** from the uploaded copy (`f4730e6d…afc21d`) because of **later header edits**; the Forge assessment reflects the uploaded revision |
| 2026-09-23 | `/tmp/gcb-build/install/bin/cobc --version` | `cobc (GnuCOBOL) 3.2.0` |
| 2026-09-23 | `scripts/test_bank.py` (with isolated `cobc`) | `Ran 33 tests in 3.194s` → **OK** |
| 2026-09-23 | `tests/test_modern.py` | `Ran 5 tests` → **OK** (includes duplicate-ID rejection and 12-digit-overflow rejection) |
| 2026-09-23 | `site/tests/` | **50 tests** (service, HTTP API, frontend wiring) |
| 2026-09-23 | `scripts/evidence/benchmark-1200x400.txt` | parity **YES**; median legacy `1.003951s` vs modern `0.035133s` = **28.6x**; `PROCESSED 400, REJECTED 3, TOTAL_CENTS 120001200` |
| 2026-09-23 | `scripts/evidence/benchmark-5000x500.txt` | parity **YES**; median legacy `4.727858s` vs modern `0.036914s` = **128.1x**; `PROCESSED 500, REJECTED 3, TOTAL_CENTS 499999475` (synthetic workload) |
| 2026-09-23 | `scripts/evidence/benchmark-sweep.txt` | speedup grows with accounts: 300→4.3x, 600→8.0x, 1200→13.1x, 2400→24.6x; all `parity ok` |
| 2026-09-23 | Forge UI: Assessment **complete** | ForgeScore **57/100 (Developing)**; 10 findings incl. 3 high (`O(m×n)` scans, full-file rewrites, missing specs) |
| 2026-09-23 | Forge UI: goals sent + **Apply & Regenerate** | **Intent** v1 generation initiated; **later completed** — see row below |
| 2026-09-23 | `scripts/benchmark.py` | extended to ≈350 lines with a `parity_ok` gate; later run the same day on the isolated compiler (rows below) |
| 2026-09-23 | Forge UI: **Intent v1 complete** | artifact id `0e0655e7-62be-4351-b2c3-b954feb6c49b` in the signed-in UI; later approved and downloaded — see rows below. The modern Python remains **team-authored**; Forge authored the planning document only. |
| 2026-09-23 | Forge UI: **PRD-Spec clarification submitted** | clarification submitted; PRD-Spec generation started (later completed and exported — see rows below) |
| 2026-09-23 | `legacy-ui/tests/test_terminal.py` | `Ran 20 tests … OK`; includes one genuine COBOL batch run |
| 2026-09-23 | `legacy-ui/` live job, preset **M** (1,200 accounts × 400 ops) via real `legacy/bank.cob` | **PROCESSED 400, REJECTED 3**; actual COBOL execution **1.197 s** (**1.234 s** overall); modern `TOTAL_CENTS` **5489403400** matched (synthetic fixture, deliberately inefficient legacy design) |
| 2026-09-23 | Forge UI → browser download: **Intent v1 approved** | [`docs/forge/intent.md`](forge/intent.md); SHA-256 `8510138776e896681e3621124aea049e82f20fdb5948432d811ff4d96ecf94cc` (verified) |
| 2026-09-23 | Forge UI → browser download: **PRD-Spec v1 generated (~95% reported confidence), approved** | [`docs/forge/prd.md`](forge/prd.md); SHA-256 `8b138ae25790357ffb623c8a53f6efe8ee9d7a355fa239657dc80c428fa63453` (verified) |
| 2026-09-23 | Forge UI: **Architecture clarification answered** | Architecture generation underway at the time; **later completed and exported** — see rows below |
| 2026-09-23 | Forge UI → browser download: **Architecture v1 completed (~100% reported confidence), approved** | [`docs/forge/architecture.md`](forge/architecture.md); SHA-256 `d0be1c535a3727558143ba7e872813925a2908efb02477bec251b92a4cb7058b` (verified) |
| 2026-09-23 | Forge UI: **User Stories generation underway** | generation underway at the time; **later completed and exported** — see rows below |
| 2026-09-23 | `docs/forge/assessment.md` (team transcription) | records the observed Assessment values (ForgeScore **57/100**, **10 findings incl. 3 high**, 3 high findings named); the raw Forge report remains unexported |
| 2026-09-23 | Forge UI → browser download: **User Stories v1 (~75% reported confidence), approved** | [`docs/forge/work-orders.md`](forge/work-orders.md); **6 epics / 33 proposed stories**; SHA-256 `a78ac60579ae7224d6888e166e211e23ef270eccddb0e22632916766312cd0d2` (verified). Proposed work, **not implemented**. |
| 2026-09-23 | Forge UI → browser download: **Testing v1 generated and exported (not approved — no Approve action shown)** | [`docs/forge/testing.md`](forge/testing.md); **132 proposed test cases** (33 functional / 33 smoke / 33 regression / 33 performance); SHA-256 `19749260605e3e1bd85539f069c47db9b06cdddcbdde3b9d85676c41e91d92b3` (verified). A generated **planning artifact, not 132 executed tests**; local executable suites **108 passing** (33 + 5 + 50 + 20). |
| 2026-09-23 | Forge MCP with supplied `forge_` token (re-checked) | still HTTP 401 `Invalid or revoked token`; **signed-in browser downloads work**, used for the Intent/PRD-Spec/Architecture/User Stories/Testing exports |
| 2026-09-23 | [`scripts/evidence/benchmark-final-5000x500.txt`](../scripts/evidence/benchmark-final-5000x500.txt) (three timed runs, one warm-up) | parity **YES**; median legacy `4.723607s` vs modern `0.040941s` = **115.4x**, `PROCESSED 500, REJECTED 3, TOTAL_CENTS 499999475`; variation from prior **128.1x** on the same deliberately inefficient synthetic baseline |
