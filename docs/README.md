# BBS SG Bank — COBOL → Modern Migration — Documentation Pack

Competition submission documentation for **{EVENT_NAME — SF Enterprise Hackathon 2.0}**,
problem statement: *modernize a legacy system (working prototype, built substantially with
Opsera Forge)*.

The subject system is the **BBS SG Bank** daily batch: a legacy flat-file COBOL program
(`legacy/bank.cob`) rewritten as an indexed, in-memory modern batch (`modern/bank.py`).

---

## 1. Truthfulness & evidence policy (read this first)

This pack is written so a judge can re-run every claim. We follow three hard rules:

1. **No step is marked complete until it has observable evidence.** Every journal row
   carries a status, an evidence pointer (file + line, or command + output), and the date
   it was checked.
2. **No fabricated Opsera Forge results.** Where a Forge artifact has not actually been
   produced and exported, the row says **Pending**. We describe *what the stage must
   produce and how we will capture it*, never a result we did not obtain. Exported
   artifacts carry a SHA-256 in `docs/forge/README.md`.
3. **No performance number is claimed without a measurement artifact.** The migration is
   an **algorithmic** improvement (`O(M·A)` → `O(A+M)`). Any wall-clock multiplier is
   quoted **only** from a saved `benchmark.py` run, and the runs are saved under
   `scripts/evidence/` — measured **28.6x** (1200×400) and **128.1x** (5000×500). Every
   figure is shown with the synthetic-workload / deliberately-inefficient-legacy
   disclosure. We explicitly do **not** claim "100x".

### Status legend

| Symbol | Status | Meaning |
|---|---|---|
| ✅ | Verified | Artifact exists / behavior observed, evidence recorded. |
| 🟡 | In progress | Started, not yet verifiable. |
| ⛔ | Pending | Not started; no evidence yet. |
| 🚫 | Blocked | Cannot proceed without an external prerequisite (named). |
| ❌ | Failing | Observed to fail a stated requirement (gap to fix). |
| ➖ | N/A | Not applicable. |

### Repo facts verified at time of writing (2026-09-23)

> This is a **shared workspace**. Line numbers and file contents cited in this pack were
> checked on 2026-09-23; re-verify before submission (the code is under active change).

| Fact | Status | Evidence |
|---|---|---|
| Legacy program present | ✅ | `legacy/bank.cob` (172 lines) — includes a header documenting the `O(m×n)` cost. |
| Modern program present, with malformed-input guard | ✅ | `modern/bank.py` (54 lines / 2,070 bytes); duplicate/overflow guards at L14-17 and L34-35, malformed-op guard at L23-25, `amount = int(value)` at L27. |
| Legacy↔modern parity/perf harness present | ✅ | `scripts/benchmark.py` (≈350 lines); computes a `parity_ok` gate and prints **no** speedup unless parity passes. Evidence transcripts under `scripts/evidence/`. |
| Core automated tests present | ✅ | `scripts/test_bank.py` → **Ran 33 tests … OK**; `tests/test_modern.py` → **Ran 5 tests … OK** (2026-09-23 with the isolated `cobc`). |
| Demo-site and terminal suites present | ✅ | `site/tests/` → **50 tests**; `legacy-ui/tests/test_terminal.py` → **Ran 20 tests … OK**. |
| Modern batch produces correct counts/balances on a controlled fixture | ✅ | run of `modern/bank.py`; see `03-...` AT-1…AT-11. |
| Malformed-row robustness (AT-11) | ✅ (fixed) | `modern/bank.py` L23-25 rejects and continues; covered by `test_malformed_operations_are_rejected_and_batch_continues`. |
| Demo web app present and runnable locally | ✅ | `site/backend/app.py` (303 lines) + `site/frontend/index.html` (489 lines); smoke-tested 2026-09-23 → `/api/health` ok, `/` HTTP 200. |
| Isolated GnuCOBOL builder | ✅ | `scripts/get_cobc.sh` → GnuCOBOL **3.2.0** at `/tmp/gcb-build/install/bin/cobc`. |
| Legacy↔modern **parity** (byte-identical) | ✅ | `parity: … byte-identical accounts.dat: YES` in all three transcripts under `scripts/evidence/`. |
| Safety divergence (duplicate IDs, 12-digit overflow) | ✅ documented | Modern **rejects duplicate account IDs** (before any write) and **rejects a balance overflow** past `PIC 9(12)`; legacy rewrites duplicate rows and truncates an overflow. Characterized in `scripts/test_bank.py` and `tests/test_modern.py`; see `02-before-after.md` §4. |
| Measured speedup (verified) | ✅ | **28.6x** at 1200×400 and **128.1x** at 5000×500 (synthetic workload; see disclosure below). |
| Opsera Forge **project** | ✅ created | [`projects/6de0abcc-6025-4b07-9e5c-2308e8f4fe10`](https://hackathon.softwareforge.ai/projects/6de0abcc-6025-4b07-9e5c-2308e8f4fe10), from synthetic ZIP `/tmp/bbs-sg-legacy.zip`; COBOL source SHA-256 `f4730e6d…afc21d` at upload. |
| Forge **Assessment / ForgeScore** | ✅ complete; raw report not exported | ForgeScore **57/100 (Developing)**; **10 findings incl. 3 high** (`O(m×n)` scans, full-file rewrites, missing specs). [`docs/forge/assessment.md`](forge/assessment.md) is a clearly labelled **team transcript of the observed values**, not a raw export; the raw report is still unexported. |
| Forge **Intent** artifact (v1) | ✅ approved + exported | Approved in the signed-in UI and downloaded to [`docs/forge/intent.md`](forge/intent.md) — SHA-256 `8510138776e8…94cc` (full hash in [`docs/forge/README.md`](forge/README.md)). |
| Forge **PRD-Spec** artifact (v1) | ✅ generated + exported | Generated at ~95% reported confidence, approved, and downloaded to [`docs/forge/prd.md`](forge/prd.md) — SHA-256 `8b138ae25790…3453`. |
| Forge **Architecture** artifact (v1) | ✅ approved + exported | Completed at ~100% reported confidence, approved, and downloaded to [`docs/forge/architecture.md`](forge/architecture.md) — SHA-256 `d0be1c535a37…058b`. |
| Forge **User Stories** artifact (v1) | ✅ approved + exported | **6 epics / 33 proposed stories** at ~75% reported confidence, approved and downloaded to [`docs/forge/work-orders.md`](forge/work-orders.md) — SHA-256 `a78ac60579ae…cd0d2`. Proposed work, **not implemented**. |
| Forge **Testing** artifact (v1) | ✅ generated + exported (not approved) | **132 proposed test cases** (33 functional / 33 smoke / 33 regression / 33 performance) **generated and downloaded — not approved, as the browser page showed no Approve action** — to [`docs/forge/testing.md`](forge/testing.md) — SHA-256 `19749260605e…92b3`. A **generated planning artifact, not 132 executed tests**; the executable local suites are **108 passing** (33 + 5 + 50 + 20). |
| Forge **Delivery** artifact | ⛔ pending | not generated/exported; public hosting and the demo video remain open. The supplied `forge_` token returns HTTP 401 `Invalid or revoked token`, so artifacts are retrieved via **signed-in browser downloads** (which work). |
| Hosted prototype URL (public) | ⛔ pending | app runs locally; `{HOSTED_URL}` not yet deployed. |

> **Speedup disclosure (required):** the numbers above compare a **deliberately
> inefficient** legacy whole-file batch (`bank.cob`: rescan + full-file rewrite per
> operation) against the indexed modern engine on **synthetic** fixtures. They are a
> property of that algorithm, not a general claim about COBOL or about our production
> data. See `02-before-after.md` §6 and the raw transcripts.

> **Forge scope note:** the modern engine (`modern/bank.py`) is **our own local code**.
> Opsera Forge produced the **Assessment** and the **Intent v1**, **PRD-Spec v1**,
> **Architecture v1**, **User Stories v1** and **Testing v1** planning documents; it did
> **not** write the Python implementation and nothing was deployed. Forge authored the
> planning documents; the local engine was written separately. The Forge documents contain
> **proposals that are not implemented** — a safe temporary-file replacement step,
> append-only audit retention, a FastAPI option, and a Forge Shipping pipeline — while the
> shipped engine writes its ledger once directly, the demo API is Python standard library
> only, and demo audit data is held in memory. The **33 User Stories and 132 Testing cases
> are proposed work, not implemented features or executed tests**; the local executable
> suites total **108 passing**. See [`docs/forge/README.md`](forge/README.md) for the
> planning-vs-implementation gaps.

---

## 2. Document map

| Doc | Purpose | Primary judging criterion served |
|---|---|---|
| [`01-modernization-journal.md`](01-modernization-journal.md) | Truthful step-by-step journal, status/evidence columns | Modernization impact, Content |
| [`02-before-after.md`](02-before-after.md) | Precise, side-by-side before/after | Modernization impact (15%) |
| [`03-requirements-and-acceptance-tests.md`](03-requirements-and-acceptance-tests.md) | Requirements + re-runnable acceptance tests | Working prototype (35%) |
| [`04-forge-pipeline-mapping.md`](04-forge-pipeline-mapping.md) | Forge Assessment → delivery mapping | Substantial Opsera Forge use (30%) |
| [`05-demo-script.md`](05-demo-script.md) | 2–3 minute demo script | Presentation (10%) + Working prototype |
| [`06-social-posts.md`](06-social-posts.md) | Per-teammate Medium/LinkedIn outlines | Content (10%) |
| [`07-submission-checklist.md`](07-submission-checklist.md) | Gate list against the official rubric | All / eligibility |
| [`../slides/index.html`](../slides/index.html) | Polished slide deck (self-contained HTML) | Presentation (10%) |
| [`../slides/SLIDES.md`](../slides/SLIDES.md) | Markdown deck source + speaker notes | Presentation (10%) |

---

## 3. Official judging criteria (verbatim weights)

| Criterion | Weight |
|---|---|
| Working prototype | **35%** |
| Substantial use of Opsera Forge | **30%** |
| Modernization impact | **15%** |
| Presentation | **10%** |
| Content | **10%** |

**Hard submission requirements:** a **hosted** prototype URL, a **short demo**, a
**before/after** explanation, and an **original public Medium or LinkedIn post from each
team member**.

How this pack addresses each:

- **Working prototype (35%)** → `03-requirements-and-acceptance-tests.md` gives re-runnable
  tests and the current pass/fail; `07-submission-checklist.md` gates the hosted URL + demo.
- **Opsera Forge (30%)** → `04-forge-pipeline-mapping.md` maps every Forge stage to the
  artifact it produced/will produce, with honest status.
- **Modernization impact (15%)** → `02-before-after.md` (algorithm, I/O, LOC, operability)
  + `01-modernization-journal.md`.
- **Presentation (10%)** → `slides/`.
- **Content (10%)** → `06-social-posts.md` (one required post per teammate).

---

## 4. The one-paragraph story (for reuse)

> BBS SG Bank's overnight batch re-opens and rescans the entire `accounts.dat` flat file
> **for every single operation**, then rewrites the whole file to apply it — classic
> `O(operations × accounts)` legacy I/O. We modernized it into an in-memory indexed batch
> (`O(accounts + operations)`, one write) that is **output-identical** on the same inputs
> (verified byte-for-byte) and, against a deliberately inefficient legacy design on synthetic
> fixtures, measured at **28.6x–128.1x** depending on account count. We wrapped the real
> engine in a fictional demo web app (`site/`) so both modes can be shown side by side, and
> drove the **planning** of the modernization through the Opsera Forge pipeline (Assessment →
> Intent → PRD-Spec → Architecture → User Stories → Testing → delivery): Forge authored the
> planning artifacts, while the modern engine itself was written separately by the team.
> Every claim in this pack is evidence-linked and re-runnable.

---

## 5. Placeholder index

Replace before submission (search the repo for `{`):

| Placeholder | Meaning |
|---|---|
| `{EVENT_NAME}` | Official hackathon name |
| `{HOSTED_URL}` | Public URL of the hosted prototype |
| `{DEMO_VIDEO_URL}` | Public link to the ≤3-min demo recording |
| `{REPO_URL}` | Public repository URL |
| `{TEAM_NAME}` / `{MEMBER_n_NAME}` | Team + member names |
| `{MEMBER_n_POST_URL}` | Published Medium/LinkedIn post per member |
| `{DATE}` | Submission date |

> Ownership note: this pack is authored inside `docs/` and `slides/` only. It describes the
> code in `legacy/`, `modern/`, `scripts/`, `tests/`, and `site/` as it exists on disk; no
> claim about those files is made beyond what is cited with a path and a date. The workspace
> is shared, so re-verify before relying on any line number.
