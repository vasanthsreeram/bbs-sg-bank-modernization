# 07 — Submission Checklist

Gate list against the official rubric. **A box is only checked when the evidence exists and
is linked.** Several boxes are intentionally unchecked — that is the honest state.

Legend: `[x]` done + evidence · `[~]` partial · `[ ]` not done / blocked.

---

## A. Eligibility gates (mandatory — missing any one is disqualifying)

| | Requirement | Status | Evidence / placeholder |
|---|---|---|---|
| A1 | **Hosted** working prototype URL | `[ ]` ⛔ | `{HOSTED_URL}` |
| A2 | **Short demo** (≤3 min) | `[ ]` ⛔ | `{DEMO_VIDEO_URL}`; script ready [`05-demo-script.md`](05-demo-script.md) |
| A3 | **Before/after** explanation | `[x]` ✅ | [`02-before-after.md`](02-before-after.md) |
| A4 | **Original public post per team member** (Medium or LinkedIn) | `[ ]` ⛔ | [`06-social-posts.md`](06-social-posts.md); URLs `{MEMBER_n_POST_URL}` |
| A5 | Built **substantially with Opsera Forge** | `[~]` 🟡 | project created; **Assessment complete** (57/100, 10 findings; raw report not exported; `docs/forge/assessment.md` is a team transcript); **Intent v1 + PRD-Spec v1 + Architecture v1 + User Stories v1 approved and exported**, **Testing v1 generated and exported (not approved)** to `docs/forge/`; **Delivery pending** ([`04-...`](04-forge-pipeline-mapping.md)) |
| A6 | Public repo | `[ ]` ⛔ | `{REPO_URL}` |

---

## B. Rubric readiness

### B1 — Working prototype (35%)

| | Item | Status | Evidence |
|---|---|---|---|
| B1.1 | Legacy batch in repo | `[x]` ✅ | [`legacy/bank.cob`](../legacy/bank.cob) |
| B1.2 | Modern batch implemented (with malformed-row guard) | `[x]` ✅ | [`modern/bank.py`](../modern/bank.py) L23-25 |
| B1.3 | End-to-end run produces correct counts/balances | `[x]` ✅ | `03-...` §3 (PROCESSED=3, REJECTED=4, TOTAL=230) |
| B1.4 | Automated tests pass | `[x]` ✅ | `scripts/test_bank.py` → **Ran 33 tests … OK**; `tests/test_modern.py` → **Ran 5 tests … OK** |
| B1.5 | Acceptance tests AT-1…AT-13 pass | `[x]` ✅ | `03-...` §4 |
| B1.6 | Parity AT-12 (legacy ↔ modern, byte-identical) | `[x]` ✅ | `parity … byte-identical: YES` in all `scripts/evidence/benchmark-*.txt` |
| B1.7 | Demo app runs locally | `[x]` ✅ | `site/backend/app.py` (50 site tests), smoke-tested 2026-09-23 |
| B1.8 | Terminal runs the **real** COBOL batch | `[x]` ✅ | `legacy-ui/` (20 tests): live 1,200×400 job → 400 processed, 3 rejected, 1.197 s actual COBOL execution (1.234 s overall), modern `TOTAL_CENTS` 5489403400 |
| B1.9 | Hosted, clickable prototype (public URL) | `[ ]` ⛔ | `{HOSTED_URL}` |

### B2 — Substantial Opsera Forge use (30%)

| | Item | Status | Evidence |
|---|---|---|---|
| B2.1 | Forge project created | `[x]` ✅ | [`projects/6de0abcc-…`](https://hackathon.softwareforge.ai/projects/6de0abcc-6025-4b07-9e5c-2308e8f4fe10) from `/tmp/bbs-sg-legacy.zip` (COBOL SHA-256 `f4730e6d…afc21d` at upload) |
| B2.2 | Assessment / ForgeScore complete | `[x]` ✅ | **57/100 (Developing)**; **10 findings incl. 3 high** (`O(m×n)` scans, full-file rewrites, missing specs) — read from the signed-in UI 2026-09-23 |
| B2.3 | Assessment artifact exported | `[~]` 🟡 | `docs/forge/assessment.md` is a **team transcription** of the observed values (57/100, 10 findings incl. 3 high); the **raw report is not exported** (MCP 401; browser download available) |
| B2.4 | Intent artifact exported | `[x]` ✅ | v1 approved and downloaded to `docs/forge/intent.md` (SHA-256 `8510138776e8…94cc`) |
| B2.5 | PRD-Spec artifact exported | `[x]` ✅ | v1 generated (~95% confidence), approved and downloaded to `docs/forge/prd.md` (SHA-256 `8b138ae25790…3453`) |
| B2.6 | Architecture artifact exported | `[x]` ✅ | v1 completed (~100% confidence), approved and downloaded to `docs/forge/architecture.md` (SHA-256 `d0be1c535a37…058b`) |
| B2.7 | User Stories / work orders | `[x]` ✅ | User Stories **v1** (6 epics / 33 **proposed** stories, ~75% confidence), approved and downloaded to `docs/forge/work-orders.md` (SHA-256 `a78ac60579ae…cd0d2`) |
| B2.8 | Testing artifact exported | `[x]` ✅ | Testing **v1** — 132 **proposed** cases (33 functional / 33 smoke / 33 regression / 33 performance), **generated and exported (not approved** — no Approve action shown) to `docs/forge/testing.md` (SHA-256 `19749260605e…92b3`). **Not executed tests**; local suites 108 passing |
| B2.9 | Delivery record + hosted app | `[ ]` ⛔ | Delivery stage pending; `docs/forge/delivery.md`; `{HOSTED_URL}` |
| B2.10 | MCP export credential | `[ ]` 🚫 | supplied `forge_` token → HTTP 401 `Invalid or revoked token`; **signed-in browser downloads work** and were used to export Intent v1 / PRD-Spec v1 |

### B3 — Modernization impact (15%)

| | Item | Status | Evidence |
|---|---|---|---|
| B3.1 | Algorithmic improvement documented (`O(M·A)`→`O(A+M)`) | `[x]` ✅ | `02-before-after.md` §3, §6 |
| B3.2 | I/O reduction documented (one write/run) | `[x]` ✅ | `02-before-after.md` §6 |
| B3.3 | Maintainability / operability comparison | `[x]` ✅ | `02-before-after.md` §5, §7 |
| B3.4 | Measured speedup, disclosed | `[x]` ✅ | `scripts/evidence/benchmark-1200x400.txt` (**28.6x**), `benchmark-5000x500.txt` (**128.1x**) — synthetic workload, deliberately inefficient legacy design (`02-...` §6) |

### B4 — Presentation (10%)

| | Item | Status | Evidence |
|---|---|---|---|
| B4.1 | Polished slide deck | `[x]` ✅ | [`slides/index.html`](../slides/index.html), [`slides/SLIDES.md`](../slides/SLIDES.md) |
| B4.2 | Demo script timed ≤3 min | `[x]` ✅ | [`05-demo-script.md`](05-demo-script.md) |
| B4.3 | Deck rehearsed end-to-end | `[ ]` ⛔ | — |
| B4.4 | Demo recorded | `[ ]` ⛔ | `{DEMO_VIDEO_URL}` |

### B5 — Content (10%)

| | Item | Status | Evidence |
|---|---|---|---|
| B5.1 | Documentation pack complete | `[x]` ✅ | `docs/README.md` + docs 01–07 |
| B5.2 | Post per member published | `[ ]` ⛔ | `{MEMBER_n_POST_URL}` |
| B5.3 | All placeholder tokens replaced | `[ ]` ⛔ | grep for `{` before submitting |

---

## C. Pre-submit QA

- [ ] `grep -rn "{" sforgehack/docs sforgehack/slides` shows only intentional code examples.
- [ ] Every speedup figure carries the **synthetic-workload / deliberately-inefficient-legacy**
      disclosure and links a `scripts/evidence/` transcript.
- [ ] No document states a Forge artifact exists without a linked export.
- [ ] No document claims **Forge generated or ran the modern engine**, deployed anything, that
      **Testing v1 was approved**, that the **33 proposed stories / 132 proposed test cases were
      implemented or run**, or that Forge's proposals (safe temp-file replacement, append-only
      audit, FastAPI, Forge Shipping) were built — Forge authored the planning documents; the
      engine is our local code and the local suites are 108 passing.
- [ ] No document claims the Forge assessment covers the **current** working-tree COBOL
      (its SHA-256 differs from the uploaded copy).
- [ ] Every ✅ row resolves to a real file/line/command.
- [ ] Hosted URL loads on a clean browser (no auth).
- [ ] Demo video is public and ≤3:00.
- [ ] Each member's post is public, original, and names their own contribution.
- [ ] `{DATE}` fields updated.

---

## D. Known open items (honest summary)

1. ✅ **Parity + speed measured** — isolated GnuCOBOL 3.2.0; byte-identical parity, 28.6x
   (1200×400) and 128.1x (5000×500). **Only open caveat:** figures are synthetic and the
   legacy design is deliberately inefficient — always disclose.
2. 🟡 **Forge Assessment complete; Intent, PRD-Spec, Architecture and User Stories approved
   and exported; Testing v1 generated/exported (not approved); Delivery pending** —
   Assessment is done (57/100, 10 findings; raw report not exported, `docs/forge/assessment.md`
   is a team transcription) and **Intent v1**, **PRD-Spec v1**, **Architecture v1** and
   **User Stories v1** (33 proposed stories) are **approved** and downloaded into `docs/forge/`,
   with **Testing v1** (132 proposed cases) **generated and exported but not approved**. The 33
   stories and 132 cases are **proposals, not implemented features or executed tests** (local
   suites: 108 passing). The supplied MCP `forge_` token is HTTP 401, but **signed-in browser
   downloads work**. 30% criterion is **partly** satisfied.
3. ⛔ **Not deployed publicly** → hosting gate open (the app runs locally).
4. ⛔ **No demo recording or published posts** → eligibility gates open.
5. 🟡 **`accounts.dat` parsing unguarded** (low priority; see `02-...` §4).

> Current defensible claim: **"A modern, linear-time batch that passes AT-1…AT-13 with 33 +
> 5 core passing tests (plus 50 site and 20 terminal tests) and byte-identical legacy/modern
> parity, measured at 28.6x (1200×400) and 128.1x (5000×500) on synthetic fixtures against a
> deliberately inefficient legacy design; wrapped in a working local demo app and an operator
> terminal that runs the real COBOL; with an Opsera Forge project whose Assessment is
> complete (57/100, 10 findings), whose Intent v1, PRD-Spec v1, Architecture v1 and User
> Stories v1 (33 proposed stories) documents are **approved** and exported, and whose Testing
> v1 (132 proposed cases) is **generated/exported (not approved)**, all to `docs/forge/` with
> recorded hashes — the raw Assessment export and Delivery
> stage are still pending, and Forge's proposals are not implemented or executed."**
> Nothing stronger. In particular: do **not** claim a public hosted URL or published posts
> yet, do **not** claim the assessment covers the current working-tree COBOL (its hash
> differs from the uploaded copy), do **not** claim Testing v1 was approved, do **not** claim
> the 33 stories were implemented or the 132 test cases were run, do **not** claim the
> Delivery stage is complete, do **not** claim
> Forge's proposals were built, and **never** claim Forge generated or ran the modern engine
> or deployed anything.
