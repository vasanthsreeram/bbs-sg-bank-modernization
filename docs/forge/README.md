# Forge-generated artifacts

These files were downloaded from the signed-in BBS SG Bank project on 2026-09-23: <https://hackathon.softwareforge.ai/projects/6de0abcc-6025-4b07-9e5c-2308e8f4fe10>.

| File | Forge stage | SHA-256 of downloaded Markdown |
|---|---|---|
| [`intent.md`](intent.md) | Intent v1, artifact `0e0655e7-62be-4351-b2c3-b954feb6c49b`, approved in the UI | `8510138776e896681e3621124aea049e82f20fdb5948432d811ff4d96ecf94cc` |
| [`prd.md`](prd.md) | PRD-Spec v1, generated from the approved Intent and clarification answers | `8b138ae25790357ffb623c8a53f6efe8ee9d7a355fa239657dc80c428fa63453` |
| [`architecture.md`](architecture.md) | Architecture v1, generated after the PRD-Spec and five clarification answers | `d0be1c535a3727558143ba7e872813925a2908efb02477bec251b92a4cb7058b` |
| [`work-orders.md`](work-orders.md) | User Stories v1, 6 epics and 33 proposed stories (~75% reported confidence) | `a78ac60579ae7224d6888e166e211e23ef270eccddb0e22632916766312cd0d2` |
| [`testing.md`](testing.md) | Testing v1, 132 proposed cases across functional, smoke, regression and performance categories | `19749260605e3e1bd85539f069c47db9b06cdddcbdde3b9d85676c41e91d92b3` |

The signed-in Assessment displayed ForgeScore **57/100**, **10 findings** and **3 high-severity findings**. [`assessment.md`](assessment.md) is a clearly labelled team transcription of the observed subset; the raw report has not been exported to this folder. The ZIP uploaded to Forge contains an earlier explanatory-header revision of `legacy/bank.cob`; the banking logic is unchanged. See [`../04-forge-pipeline-mapping.md`](../04-forge-pipeline-mapping.md) for the exact uploaded-source hash and stage status.

**Planning versus implementation:** Forge generated analysis and planning documents. The Python batch engine, websites, tests, and benchmark harness were authored locally. The documents include proposals and assumptions that are not implemented, including a safe temporary-file replacement step, append-only audit retention, a FastAPI option, and a Forge Shipping pipeline. Current `modern/bank.py` writes its ledger once directly, while the demo site's API uses the Python standard library and holds audit data in memory. Treat these as documented follow-up gaps, not delivered behavior. The 33 Forge stories and 132 Forge test cases are proposed work, not implemented features or executed tests; the executable local suites total 108 passing tests (33 core, 5 modern, 50 website, 20 operator-terminal). Parity applies to the valid fixed-width fixture domain; duplicate account IDs and overflow cases are deliberate safety divergences documented in the tests.
