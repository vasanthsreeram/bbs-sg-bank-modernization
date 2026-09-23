# BBS SG Bank — fictional legacy modernization demo

This project is a **synthetic bank** created for the SF Enterprise Hackathon 2.0. It contains no real customers, accounts, credentials, banking integrations, or financial advice.

## Project story

The old nightly batch uses a COBOL flat-file ledger. Every deposit, withdrawal, or transfer scans every account, then copies the entire ledger twice to persist a single operation. The modern replacement indexes accounts in memory and writes the ledger once after the batch. The intentionally inefficient access pattern represents a legacy whole-file batch design; disclose this synthetic setup and report only measured performance under identical inputs.

The core preserves account balances in integer cents, source/destination transfers, overdraft rejection, and error cases. The modern version rejects duplicate account IDs and 12-digit balance overflow before writing; the legacy COBOL truncates some out-of-range values, and the tests document this safety divergence. The final core is 54 lines / 2,070 bytes versus 172 lines / 6,349 bytes for the commented COBOL source (about 3.2× shorter by lines). See `docs/` for the modernization record and competition materials, `slides/` for presentation material, `site/` for the modern demo, and `legacy-ui/` for the 1980s-style operator terminal backed by real COBOL execution.

## Run the benchmark

Install GnuCOBOL (`cobc`) in an environment where it is available, then run:

```sh
python3 scripts/benchmark.py --accounts 1200 --operations 400
```

The benchmark generates deterministic synthetic data and compares the final account file and processing summary byte for byte. It prints actual elapsed time and the resulting speedup. On this machine, the median of five runs at 1,200 accounts / 400 operations was **28.6×** (1.003951 s vs 0.035133 s). A separate median of three runs at 5,000 accounts / 500 operations was **128.1×** (4.727858 s vs 0.036914 s). Both matched byte for byte; see `scripts/evidence/benchmark-1200x400.txt` and `scripts/evidence/benchmark-5000x500.txt`. This is a batch-algorithm comparison between a deliberately whole-file-rewriting COBOL baseline and a Python indexed replacement; results vary by machine, workload, and runtime. It is not a general claim about COBOL performance.

## Tests

- **Core:** `scripts/test_bank.py` (33 tests; needs `cobc`) and `tests/test_modern.py` (5 tests).
- **Demo site:** 50 tests under `site/tests/`.
- **Operator terminal:** 20 tests under `legacy-ui/tests/`.

Run a suite directly, for example `GNUBOL_PREFIX=/tmp/gcb-build/install python3 scripts/test_bank.py` or `python3 tests/test_modern.py`.

The `legacy-ui/` terminal is not a mock-up: with its helper server running it compiles the unmodified `legacy/bank.cob` and runs it as a real subprocess. A live 1,200-account / 400-operation job produced **400 processed, 3 rejected** in **1.197 s of actual COBOL execution** (**1.234 s** overall), and the modern engine's `TOTAL_CENTS` (**5489403400**) matched. As with every figure here, this compares a **synthetic** workload against the deliberately inefficient legacy design; it is not a general COBOL claim.

## Forge modernization workflow

Forge's [Modernization guide](https://www.softwareforge.ai/docs/quick-start-modernization) describes **Modernize Legacy Code → ZIP File** (or Local Folder / Git repository), automatic **Assessment and ForgeScore**, then Intent, PRD-Spec, Architecture, User Stories, Testing, and delivery. The synthetic COBOL source was uploaded through the signed-in UI to [the BBS SG Bank project](https://hackathon.softwareforge.ai/projects/6de0abcc-6025-4b07-9e5c-2308e8f4fe10). The **Assessment is complete** (ForgeScore **57/100**, **10 findings incl. 3 high**); [`docs/forge/assessment.md`](docs/forge/assessment.md) is a team transcript of the observed values, and the raw report is still not exported. **Intent v1**, **PRD-Spec v1** (~95% reported confidence), **Architecture v1** (~100%) and **User Stories v1** (6 epics / **33 proposed stories**, ~75%) were **approved** and downloaded, and **Testing v1** (**132 proposed test cases**) was **generated and downloaded** (its browser page showed no Approve action), all into [`docs/forge/`](docs/forge/) — SHAs are recorded in [`docs/forge/README.md`](docs/forge/README.md). The 33 stories and 132 cases are **proposed planning artifacts, not implemented features or executed tests**; the executable local suites total **108 passing** (33 core + 5 modern + 50 site + 20 terminal). **Delivery/public hosting, the demo video, per-member posts and the raw Assessment export are still pending.** Keep generated output and the app implementation distinct in the submission: **Forge authored the planning documents, while the modern Python engine was written separately by the team**, and nothing is deployed publicly. Those Forge documents contain proposals that were **not implemented** (a safe temporary-file replacement step, append-only audit retention, a FastAPI option, and a Forge Shipping pipeline); the shipped engine writes its ledger once directly, the demo API is Python standard library, and audit data is held in memory. The MCP bearer token is for an existing project's context and work orders; the supplied `forge_` token still returns `Invalid or revoked token`, so the exported documents were retrieved through signed-in browser downloads (which work) rather than MCP. Never commit or display an API key.
