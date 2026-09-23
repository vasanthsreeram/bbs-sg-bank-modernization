# 04 — Opsera Forge Pipeline Mapping (Assessment → Delivery)

This document maps each **Opsera Forge** stage to (a) the artifact it must produce, (b) the
concrete Forge mechanism we use, (c) where the exported artifact lives in this repo, and
(d) its **honest status today**. It exists to make the *"substantial use of Opsera Forge"*
(30%) criterion auditable: a judge should be able to point at each row and find the file.

> **No fabricated Forge results.** As of 2026-09-23 the Forge **Assessment is complete**
> (ForgeScore **57/100, Developing**; the raw report is **not exported**, and
> [`docs/forge/assessment.md`](forge/assessment.md) is a clearly labelled team transcription
> of the observed values), **Intent v1 is approved and downloaded** to
> [`docs/forge/intent.md`](forge/intent.md), **PRD-Spec v1 is generated (~95% reported
> confidence), approved and downloaded** to [`docs/forge/prd.md`](forge/prd.md), and
> **Architecture v1 is completed (~100% reported confidence), approved and downloaded** to
> [`docs/forge/architecture.md`](forge/architecture.md), **User Stories v1 (6 epics / 33
> proposed stories, ~75% reported confidence) is approved and downloaded** to
> [`docs/forge/work-orders.md`](forge/work-orders.md), and **Testing v1 (132 proposed test
> cases) is generated and exported — not approved, since its browser page showed no Approve
> action** — to [`docs/forge/testing.md`](forge/testing.md). All exported files
> carry SHA-256 hashes in [`docs/forge/README.md`](forge/README.md). **Delivery is pending.**
> The supplied MCP `forge_` token still returns HTTP 401 `Invalid or revoked token`, so the
> exported documents were retrieved via **signed-in browser downloads** (which work). The
> "team-authored stand-in" column shows work we produced by hand; it is *not* presented as a
> Forge output. **Forge did not generate the modern Python** — `modern/bank.py` is our own
> local code, and nothing was deployed. The **33 User Stories and 132 Testing cases are
> proposed planning artifacts, not implemented features or executed tests** (the local
> executable suites are **108 passing**). The Forge PRD-Spec/Architecture documents contain
> **proposals that were not implemented** (a safe temporary-file replacement step,
> append-only audit retention, a FastAPI option, and a Forge Shipping pipeline); the shipped
> engine writes its ledger once directly, the demo API is Python standard library only, and
> demo audit data is held in memory — see [`docs/forge/README.md`](forge/README.md).

Legend: ✅ Verified · 🟡 In progress · ⛔ Pending · 🚫 Blocked.

## Live evidence (2026-09-23)

| Item | Value |
|---|---|
| Forge project | https://hackathon.softwareforge.ai/projects/6de0abcc-6025-4b07-9e5c-2308e8f4fe10 |
| Ingestion path | *Modernize Legacy Code → ZIP File*, synthetic archive `/tmp/bbs-sg-legacy.zip` (`bbs-sg-legacy/{bank.cob, README.md, accounts.dat, operations.dat}`) |
| COBOL source SHA-256 at upload | `f4730e6d2b3867a5d8908a6dc0f77e714826f15d23118a3f8e42d7f0b2afc21d` (matches the `bank.cob` inside the ZIP) |
| Assessment / ForgeScore | ✅ **complete** — ForgeScore **57/100 (Developing)**; **10 findings incl. 3 high** (`O(m×n)` scans, full-file rewrites, missing specs). Raw report **not exported**; [`docs/forge/assessment.md`](forge/assessment.md) is a **team transcription** of the observed values. |
| Intent | ✅ **v1 approved + exported** — downloaded to [`docs/forge/intent.md`](forge/intent.md), SHA-256 `8510138776e8…94cc`; artifact id `0e0655e7-62be-4351-b2c3-b954feb6c49b` |
| PRD-Spec | ✅ **v1 generated (~95% confidence) + exported** — approved and downloaded to [`docs/forge/prd.md`](forge/prd.md), SHA-256 `8b138ae25790…3453` |
| Architecture | ✅ **v1 completed (~100% confidence) + exported** — approved and downloaded to [`docs/forge/architecture.md`](forge/architecture.md), SHA-256 `d0be1c535a37…058b` |
| User Stories | ✅ **v1 approved + exported** — 6 epics / 33 proposed stories (~75% confidence), downloaded to [`docs/forge/work-orders.md`](forge/work-orders.md), SHA-256 `a78ac60579ae…cd0d2` |
| Testing | ✅ **v1 generated + exported (not approved — no Approve action shown)** — 132 proposed test cases (33 functional / 33 smoke / 33 regression / 33 performance), downloaded to [`docs/forge/testing.md`](forge/testing.md), SHA-256 `19749260605e…92b3`; a **planning artifact, not 132 executed tests** |
| Delivery | ⛔ **pending** — not generated/exported; public hosting and demo video remain open |
| MCP export | 🚫 **401 for the supplied token** — `Invalid or revoked token`; **signed-in browser downloads work** and were used for the Intent / PRD-Spec / Architecture / User Stories / Testing exports |
| ⚠️ Working-tree drift | the current `legacy/bank.cob` hashes to `74669316…446f467`, **different** from the uploaded copy (`f4730e6d…afc21d`) because of **later header edits** — do **not** claim the assessment covers the exact current working-tree bytes |
| Forge scope | Forge produced the **Assessment** and the exported **Intent v1**, **PRD-Spec v1**, **Architecture v1**, **User Stories v1** and **Testing v1** planning documents; the modern engine (`modern/bank.py`) is **our own local code**, not Forge-generated, and was not deployed. The 33 stories / 132 test cases are **proposed, not implemented or executed**. Forge's proposals (safe temp-file replacement, append-only audit, FastAPI, Forge Shipping) are **not implemented** — see [`docs/forge/README.md`](forge/README.md). |

---

## Pipeline overview

```
┌────────────┐  ┌────────┐  ┌──────────┐  ┌──────────────┐  ┌───────────────┐  ┌─────────┐  ┌──────────┐
│ Assessment │→ │ Intent │→ │ PRD-Spec │→ │ Architecture │→ │ User Stories  │→ │ Testing │→ │ Delivery │
└────────────┘  └────────┘  └──────────┘  └──────────────┘  └───────────────┘  └─────────┘  └──────────┘
   scan legacy     goals      requirements     design + ADRs     work orders        test plan    ship + demo
```

**How Forge ingests the work (per the project [`README.md`](../README.md)):** Forge's
*Modernize Legacy Code → ZIP File* (or Local Folder / Git repository) flow performs an
automatic **Assessment and ForgeScore**, then Intent, PRD-Spec, Architecture, User Stories,
Testing, and delivery. Project creation and local ZIP ingestion are done through the Forge
**UI**; the MCP **bearer token is for an existing project's context and work orders**.

Forge surface used (from the hackathon host, `hackathon.softwareforge.ai`):
MCP endpoint `POST /api/mcp` with `Authorization: Bearer forge_<token>` (token from
**Profile → API Tokens**), plus the web UI. Advertised read tools include `get_intent`,
`get_prd`, `get_architecture`, and `get_work_orders` (each needs a `project_id`).

---

## Stage-by-stage mapping

### Stage 1 — Assessment

| Field | Value |
|---|---|
| Purpose | Analyze the legacy system and surface risks/tech debt. |
| Forge artifact | Assessment report (project-level analysis). |
| Mechanism | Forge UI / MCP against a project seeded with `legacy/bank.cob`. |
| Repo landing zone | `docs/forge/assessment.md` (+ raw export). |
| Status | ✅ Complete — ForgeScore **57/100 (Developing)**, 10 findings incl. 3 high. The **raw report has not been exported**; [`docs/forge/assessment.md`](forge/assessment.md) is a team transcription of the observed values. The supplied MCP token is 401, so export the raw report via the signed-in browser before submission. |
| Live evidence | project `6de0abcc-…`; ZIP `/tmp/bbs-sg-legacy.zip`; COBOL SHA-256 `f4730e6d…afc21d` at upload (2026-09-23). |
| Team-authored stand-in | [`01-modernization-journal.md`](01-modernization-journal.md) Phase 0 (bottleneck at `bank.cob` L108/L133; data contracts). |

### Stage 2 — Intent

| Field | Value |
|---|---|
| Purpose | Capture the modernization goal and constraints as a reviewed artifact. |
| Forge artifact | Intent document. |
| Mechanism | Forge `Intent` stage; retrieve with MCP `get_intent` (`project_id`). |
| Repo landing zone | `docs/forge/intent.md`. |
| Status | ✅ Complete and **exported** — Intent **v1**, artifact id `0e0655e7-62be-4351-b2c3-b954feb6c49b`, approved in the UI and downloaded to [`docs/forge/intent.md`](forge/intent.md) (SHA-256 `8510138776e8…94cc`). Forge authored this planning document; the modern engine was written separately. |
| Team-authored stand-in | The **Intent** block in `01-modernization-journal.md` (§Phase 1). |

### Stage 3 — PRD-Spec

| Field | Value |
|---|---|
| Purpose | Turn intent into testable functional + non-functional requirements. |
| Forge artifact | PRD-Spec. |
| Mechanism | Forge PRD-Spec stage; retrieve with MCP `get_prd` (`project_id`). |
| Repo landing zone | `docs/forge/prd.md`. |
| Status | ✅ Complete and **exported** — PRD-Spec **v1** generated from the approved Intent and clarification answers (reported ~95% confidence), approved and downloaded to [`docs/forge/prd.md`](forge/prd.md) (SHA-256 `8b138ae25790…3453`). |
| Team-authored stand-in | [`03-requirements-and-acceptance-tests.md`](03-requirements-and-acceptance-tests.md) FR-1…FR-10, NFR-1…NFR-5. |

### Stage 4 — Architecture

| Field | Value |
|---|---|
| Purpose | Decide the target design and record trade-offs. |
| Forge artifact | Architecture doc / diagrams. |
| Mechanism | Forge Architecture stage; retrieve with MCP `get_architecture` (`project_id`). |
| Repo landing zone | `docs/forge/architecture.md` (+ diagrams). |
| Status | ✅ Complete and **exported** — Architecture **v1** completed at reported ~100% confidence after the PRD-Spec and clarification answers, approved and downloaded to [`docs/forge/architecture.md`](forge/architecture.md) (SHA-256 `d0be1c535a37…058b`). Forge's architecture proposals are **not all implemented**; see the scope note above and [`docs/forge/README.md`](forge/README.md). |
| Team-authored stand-in | ADR block in `01-modernization-journal.md` (§Phase 3) + `02-before-after.md` §3-§4. |

### Stage 5 — User Stories / Work Orders

| Field | Value |
|---|---|
| Purpose | Decompose the approved architecture into implementable units. |
| Forge artifact | User stories / work orders. |
| Mechanism | Forge stories/work-order stage; retrieve with MCP `get_work_orders` (`project_id`). Note: the Forge tool set includes mutating project/work-order/artifact/ship operations — treat MCP as read-write, and export before changing state. |
| Repo landing zone | `docs/forge/work-orders.md`. |
| Status | ✅ Complete and **exported** — User Stories **v1**: **6 epics / 33 proposed stories** at reported ~75% confidence, approved and downloaded to [`docs/forge/work-orders.md`](forge/work-orders.md) (SHA-256 `a78ac60579ae…cd0d2`). These are **proposals, not implemented features**. |
| Team-authored stand-in | Story list below. |

**Team-authored story list (our mapping, reconciled against the exported Forge User Stories v1):**

| Story | As a… | I want… | So that… | Maps to |
|---|---|---|---|---|
| US-1 | bank engineer | the batch to stop re-scanning the whole file per op | overnight windows fit the volume | NFR-1, `bank.py` L11-18 |
| US-2 | bank engineer | behaviour to be provably identical to legacy | migration risk is controlled | FR-9, AT-12 |
| US-3 | operations | the on-disk format unchanged | downstream consumers keep working | FR-10 |
| US-4 | auditor | rejected operations reported as counts | exception handling is observable | FR-8, AT-8 |
| US-5 | support engineer | malformed rows rejected, not fatal | batches don't abort on bad data | NFR-4, AT-11 |
| US-6 | stakeholder | a hosted way to run a batch and view results | demo + trial without a build | Delivery |

### Stage 6 — Testing

| Field | Value |
|---|---|
| Purpose | Prove the modernized batch is correct (parity + acceptance). |
| Forge artifact | Test plan / test cases and results. |
| Mechanism | Forge Testing stage; link test cases to acceptance tests; run against CI. |
| Repo landing zone | `docs/forge/testing.md` + `docs/evidence/` transcripts. |
| Status | ✅ Exported (**not approved** — its browser page showed no Approve action) — Testing **v1**: **132 proposed test cases** (33 functional / 33 smoke / 33 regression / 33 performance), downloaded to [`docs/forge/testing.md`](forge/testing.md) (SHA-256 `19749260605e…92b3`). A generated **planning artifact, not 132 executed tests**; the local executable suites are **108 passing**. |
| Team-authored stand-in | AT-1…AT-13 in `03-requirements-and-acceptance-tests.md`; parity harness `scripts/benchmark.py`. |

### Stage 7 — Delivery

| Field | Value |
|---|---|
| Purpose | Ship the modernized system and its evidence. |
| Forge artifact | Delivery/release record; the hosted app. |
| Mechanism | Forge delivery/ship stage; deploy hosted prototype; record release. |
| Repo landing zone | `docs/forge/delivery.md`; `https://bbs-sg-bank-demo.pages.dev`; `https://bbs-sg-bank-demo.pages.dev/media/bbs-sg-bank-demo.mp4`. |
| Status | ⛔ Pending — project exists; artifact not yet exported. |
| Team-authored stand-in | [`07-submission-checklist.md`](07-submission-checklist.md); `slides/`. |

---

## How Forge is *substantially* used (evidence a judge can check)

1. **Every stage has a home.** Stages 1–7 each name the Forge artifact and the export path
   under `docs/forge/`. Populating those files is the unit of "done" for the 30% criterion.
2. **Machine-retrievable.** Each artifact has a concrete retrieval mechanism
   (`get_intent`, `get_prd`, `get_architecture`, `get_work_orders` via `/api/mcp`), so the
   provenance is reproducible, not narrative. **Current caveat:** the supplied `forge_`
   token is still HTTP 401 `Invalid or revoked token`, so the Intent v1, PRD-Spec v1 and
   Architecture v1 files were retrieved through **signed-in browser downloads** instead; the
   same route can export the remaining stages.
3. **Traceable to code.** Stage 3 requirements ↔ Stage 6 tests ↔ repository code are
   cross-linked by ID (FR-/NFR-/AT-/US-) in docs 01 and 03.
4. **Planning documents, not the engine.** Forge authored the **Assessment** and the
   exported **Intent v1**, **PRD-Spec v1**, **Architecture v1**, **User Stories v1** and
   **Testing v1** planning documents; the modern engine (`modern/bank.py`), parity harness
   and demo app were written **separately** by the team. Forge framed and assessed the work —
   it did **not** run or author the code migration, and nothing was deployed. Forge's output
   is planning material, not delivered behavior: the **33 User Stories and 132 test cases are
   proposed** (not implemented, not executed) and the safe temporary-file replacement step,
   append-only audit retention, FastAPI option and Forge Shipping pipeline are **not
   implemented** (see [`docs/forge/README.md`](forge/README.md)).

## Gap register (drives the 30% criterion)

| Gap | Blocker | Fix |
|---|---|---|
| ~~Forge project not created~~ | — | **Done 2026-09-23:** project `6de0abcc-…` created from `/tmp/bbs-sg-legacy.zip`. |
| ~~Assessment/ForgeScore not captured~~ | — | **Done 2026-09-23:** ForgeScore 57/100 (Developing), 10 findings incl. 3 high. [`docs/forge/assessment.md`](forge/assessment.md) records the observed values as a **team transcription**. Still to do: export the raw report. |
| ~~Intent artifact not finished~~ | — | **Done 2026-09-23:** Intent **v1** approved and downloaded to [`docs/forge/intent.md`](forge/intent.md) (SHA-256 `8510138776e8…94cc`). |
| ~~PRD-Spec not finished~~ | — | **Done 2026-09-23:** PRD-Spec **v1** generated (~95% confidence), approved and downloaded to [`docs/forge/prd.md`](forge/prd.md) (SHA-256 `8b138ae25790…3453`). |
| ~~Architecture not exported~~ | — | **Done 2026-09-23:** Architecture **v1** completed (~100% confidence), approved and downloaded to [`docs/forge/architecture.md`](forge/architecture.md) (SHA-256 `d0be1c535a37…058b`). |
| ~~User Stories not exported~~ | — | **Done 2026-09-23:** User Stories **v1** (6 epics / 33 proposed stories, ~75% confidence), approved and downloaded to [`docs/forge/work-orders.md`](forge/work-orders.md) (SHA-256 `a78ac60579ae…cd0d2`). |
| ~~Testing artifact not exported~~ | — | **Done 2026-09-23:** Testing **v1** (132 proposed cases), **generated and exported — not approved** (no Approve action shown), to [`docs/forge/testing.md`](forge/testing.md) (SHA-256 `19749260605e…92b3`). Not executed tests. |
| Delivery artifact not exported | Not generated / MCP token revoked (401) | Use signed-in **browser downloads** (they work), or issue a fresh `forge_` token (Profile → API Tokens). |
| No linkage from Forge tests to CI | No CI yet | Add CI job running `scripts/benchmark.py` + `scripts/test_bank.py`. |
