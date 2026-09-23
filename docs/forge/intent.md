# Intent profile

**Status:** complete

**Artifact:** `0e0655e7-62be-4351-b2c3-b954feb6c49b`

## Vision

Modernize the synthetic BBS SG Bank daily COBOL batch into a one-day working prototype that preserves the legacy fixed-width flat-file ledger contract and cent-accurate behavior while eliminating the documented O(m × n) per-operation scan/rewrite bottleneck through indexed account lookups, one deterministic end-of-batch ledger write, and golden-file parity validation.

## Target personas

- Modernization engineer responsible for preserving COBOL batch behavior while replacing inefficient ledger-processing internals
- QA or regression tester validating byte-identical outputs, rejection behavior, and performance measurements across legacy and modern implementations
- Demo operator or technical stakeholder reviewing before/after batch behavior, timing results, and auditability for an educational modernization prototype

## Core features

- **Indexed in-memory ledger processing** (priority 1)
  - Description: Replace the legacy `bank.cob` behavior that reopens and scans `accounts.dat` for every operation with a single upfront read into an indexed in-memory structure keyed by the 8-digit account ID. Operations must be processed sequentially in file order while preserving the legacy `accounts.dat` and `operations.dat` pipe-delimited fixed-width contracts.
  - Acceptance: Read `accounts.dat` once before operation processing begins.
  - Acceptance: Build an indexed account lookup keyed by the 8-digit account ID.
  - Acceptance: Process `operations.dat` sequentially in source file order.
  - Acceptance: Preserve `accounts.dat` format exactly as `IIIIIIII|BBBBBBBBBBBB`.
  - Acceptance: Preserve `operations.dat` format exactly as `K|SSSSSSSS|TTTTTTTT|AAAAAAAAAAAA`.
  - Acceptance: Parse operation kind from position `ops-row(1:1)`.
  - Acceptance: Parse source account ID from positions equivalent to `ops-row(3:8)`.
  - Acceptance: Parse destination account ID from positions equivalent to `ops-row(12:8)`.
  - Acceptance: Parse amount text from positions equivalent to `ops-row(21:12)`.
  - Acceptance: Use integer cents for every monetary calculation.
  - Acceptance: Do not use floating-point monetary arithmetic.
  - Acceptance: Support deposit operation kind `D`.
  - Acceptance: Support withdrawal operation kind `W`.
  - Acceptance: Support transfer operation kind `T`.
  - Acceptance: Reject unsupported operation types.
  - Acceptance: Reject non-numeric amounts.
  - Acceptance: Reject zero amounts.
  - Acceptance: Reject malformed fixed-width rows according to legacy behavior rather than silently correcting them.
  - Acceptance: Reject operations with missing source accounts.
  - Acceptance: Reject transfers with missing destination accounts.
  - Acceptance: Reject self-transfers where source and destination account IDs are the same.
  - Acceptance: Reject withdrawals and transfers that would create overdrafts or insufficient funds.
  - Acceptance: Rejected operations must increment the rejected count and must not abort the full batch.
  - Acceptance: Accepted operations must increment the processed count.
  - Acceptance: Final balances must remain cent-accurate relative to the COBOL baseline for equivalent accepted operations.
  - Acceptance: Final output must preserve deterministic account ordering compatible with the original ledger ordering unless a future requirement explicitly changes it.
  - Acceptance: The implementation must address the documented O(m × n) Data Gravity hotspot caused by repeated full-ledger scans.
- **Single deterministic ledger write phase** (priority 2)
  - Description: Replace the legacy per-accepted-operation full-file rewrite through `accounts.tmp` with accumulated in-memory balance mutations and one end-of-batch ledger write. The write phase must use a safe temporary file and final replacement step while preserving deterministic fixed-width output formatting.
  - Acceptance: Do not rewrite `accounts.dat` after each accepted operation.
  - Acceptance: Accumulate accepted balance mutations in memory during batch processing.
  - Acceptance: Perform exactly one final ledger write phase after all operations have been processed.
  - Acceptance: Write the final ledger using deterministic ordering compatible with the legacy flat-file contract.
  - Acceptance: Use a safe temporary output file during final ledger generation.
  - Acceptance: Replace the final `accounts.dat` only after the temporary ledger has been fully written.
  - Acceptance: Avoid publishing partially written ledger output as a completed result.
  - Acceptance: Preserve balance field width as 12 numeric digits.
  - Acceptance: Preserve account ID field width as 8 numeric digits.
  - Acceptance: Preserve pipe delimiter placement between account ID and balance.
  - Acceptance: Emit batch summary metrics equivalent to `PROCESSED`, `REJECTED`, and `TOTAL_CENTS`.
  - Acceptance: Format `PROCESSED` as an 8-digit count consistent with the legacy COBOL picture clause.
  - Acceptance: Format `REJECTED` as an 8-digit count consistent with the legacy COBOL picture clause.
  - Acceptance: Format `TOTAL_CENTS` as a 16-digit total consistent with the legacy COBOL picture clause.
  - Acceptance: Preserve byte-identical final account balances compared with the COBOL baseline where formatting is expected to match.
  - Acceptance: Reduce file-system mutation windows compared with the legacy per-operation rewrite approach.
  - Acceptance: Include explicit migration notes describing how legacy fixed-width fields map into indexed account records.
  - Acceptance: Include explicit rollback notes describing how to retain original inputs, compare modern output against COBOL output, discard generated modern output, and rerun the COBOL baseline.
- **Golden-file parity and benchmark fixtures** (priority 3)
  - Description: Add executable golden-file fixtures and parity checks to protect the modernization from behavior drift. Tests must compare the COBOL baseline and modern implementation on shared fixtures, including valid operations, malformed rows, rejection cases, fixed-width output, final ledger totals, and measured performance at the requested fixture sizes.
  - Acceptance: Create golden-file fixtures for valid deposits.
  - Acceptance: Create golden-file fixtures for valid withdrawals.
  - Acceptance: Create golden-file fixtures for valid transfers.
  - Acceptance: Create golden-file fixtures for malformed fixed-width rows.
  - Acceptance: Create golden-file fixtures for insufficient funds or overdraft attempts.
  - Acceptance: Create golden-file fixtures for missing source accounts.
  - Acceptance: Create golden-file fixtures for missing transfer destination accounts.
  - Acceptance: Create golden-file fixtures for same-account transfers.
  - Acceptance: Create golden-file fixtures for invalid operation types.
  - Acceptance: Create golden-file fixtures for non-numeric amounts.
  - Acceptance: Create golden-file fixtures for zero amounts.
  - Acceptance: Create golden-file fixtures validating fixed-width output formatting.
  - Acceptance: Create golden-file fixtures validating final ledger totals.
  - Acceptance: Run the COBOL baseline and modern implementation against the same fixture inputs.
  - Acceptance: Compare final `accounts.dat` output between the COBOL baseline and modern implementation.
  - Acceptance: Compare processed count between the COBOL baseline and modern implementation.
  - Acceptance: Compare rejected count between the COBOL baseline and modern implementation.
  - Acceptance: Compare total cents between the COBOL baseline and modern implementation.
  - Acceptance: Confirm byte-identical final balances where formatting is expected to match.
  - Acceptance: Measure and report runtime for `1,200 accounts × 400 operations`.
  - Acceptance: Measure and report runtime for `5,000 accounts × 500 operations`.
  - Acceptance: Document current preliminary local prototype speedup of `28.6x` at `1,200 × 400` only as `Local prototype result on one host, pending independent review.`
  - Acceptance: Document current preliminary local prototype speedup of `128.1x` at `5,000 × 500` only as `Local prototype result on one host, pending independent review.`
  - Acceptance: Do not present the preliminary speedup values as independently validated benchmarks until reviewed.
  - Acceptance: Store enough parity evidence to make the fixed-width ledger contract an executable specification rather than relying only on source comments.

## In Scope

- Replace per-operation full-ledger scans with indexed in-memory account lookups keyed by 8-digit account ID.
- Replace per-operation full-file rewrites with accumulated in-memory mutations and one deterministic end-of-batch ledger write using a safe temp file and final replacement step.
- Add golden-file parity and regression fixtures covering valid deposits, withdrawals, transfers, malformed rows, insufficient funds, missing accounts, same-account transfers, fixed-width output, final ledger totals, and requested benchmark sizes.

## Out of Scope

- Production banking platform functionality.
- Real customer onboarding or account management.
- Regulatory compliance certification.
- Payment network integration.
- Authentication against real enterprise identity providers.
- Real-time transaction authorization.
- Multi-tenant SaaS operations.
- Replacement of any production core banking system.
- Unselected assessment recommendations beyond ledger lookup performance, single ledger write, and behavioral parity fixtures.
- Claims that preliminary speedup measurements are independently validated benchmarks.
- Handling real bank or customer records.

## Technical constraints

- Goal scope is modernization of an existing synthetic COBOL batch, not a greenfield banking platform.
- Existing dominant language is COBOL; source repository contains `bank.cob` and `README.md`.
- Current architecture is a standalone procedural monolith using line-sequential local flat files.
- Legacy input/output files are local flat files named `accounts.dat`, `operations.dat`, and `accounts.tmp`.
- `accounts.dat` must retain the fixed-width pipe-delimited format `IIIIIIII|BBBBBBBBBBBB`.
- `operations.dat` must retain the fixed-width pipe-delimited format `K|SSSSSSSS|TTTTTTTT|AAAAAAAAAAAA`.
- Account IDs must be exactly 8 numeric digits.
- Balances must be exactly 12 numeric digits representing integer cents.
- Amounts must be exactly 12 numeric digits, greater than zero, and represented as integer cents.
- Operation kind must be one of `D`, `W`, or `T`.
- No floating-point monetary calculations are allowed.
- Invalid rows must be rejected according to legacy semantics rather than silently corrected.
- Final balances must be byte-identical to the COBOL baseline for equivalent accepted operations where formatting is expected to match.
- Batch summary semantics must preserve `PROCESSED`, `REJECTED`, and `TOTAL_CENTS`.
- Performance measurements must include `1,200 × 400` and `5,000 × 500` fixture sizes.
- Preliminary speedup values must be labeled as local prototype results on one host pending independent review.
- Do not infer or claim production banking compliance, real customer data handling, or readiness for live financial operations.
- Keep implementation scope to a one-day working prototype.
- If UI/API demo elements are implemented around the selected modernization work, they must be clearly labeled as prototype/demo surfaces and must not imply production banking operation.
- Externally supplied fixture inputs must be validated server-side using allow-list rules.
- User-facing errors must avoid leaking stack traces, secrets, or host paths.

## Confidence

Overall: **90%**

> The provided code analysis, selected recommendations, and user modernization instructions give a strong basis for extracting scope and constraints, with only minor uncertainty around exact UI/API expectations versus the narrowed selected-recommendation scope.

| Section | Score | Why | How to Improve |
| --- | --- | --- | --- |
| Vision | 93% | The modernization objective is clearly stated and reinforced by source comments, README content, assessment findings, and selected recommendations. | Confirm whether the prototype should remain COBOL-based, be reimplemented in another language, or include both baseline and modern implementations. |
| Target personas | 78% | Personas are inferred from the educational modernization context rather than explicitly named user roles in the codebase. | Name the exact demo and engineering users who will operate the prototype, such as developer, QA tester, stakeholder reviewer, or instructor. |
| Core features | 94% | The selected assessment recommendations provide a clear authoritative scope for indexed lookups, single ledger write, and parity fixtures. | Confirm whether the operator dashboard, APIs, and audit history are implementation requirements for this phase or supporting demo requirements outside the selected assessment scope. |
| Technical constraints | 93% | The legacy file formats, COBOL implementation details, precision rules, performance targets, and non-production boundaries are well specified. | Specify the target runtime, compiler or interpreter, operating system, and whether GnuCOBOL, Python, or another modernization stack should be used. |

---

# Modernization Analysis

> Review the proposals below and select the modernization areas you want to pursue. You can reply in the chat to confirm your choices or ask follow-up questions.

## Tech Stack

*Language, framework, and tooling modernization*

| # | Area | Current | Proposed | Rationale |
| --- | --- | --- | --- | --- |
| 1 | Batch processing engine | Single COBOL program in bank.cob using line-sequential flat files and repeated full-ledger scans for each operation. | Introduce a modern batch engine implementation that reads accounts.dat once into an indexed in-memory account map keyed by the 8-digit account ID, processes operations sequentially, and writes the ledger once at the end of the batch while retaining the COBOL program as the parity baseline. | This directly removes the documented O(m × n) I/O hotspot while preserving the external fixed-width flat-file contract and legacy business semantics. |
| 2 | Ledger write strategy | For every accepted operation, bank.cob writes all account rows to accounts.tmp and then copies accounts.tmp back over accounts.dat. | Accumulate accepted balance mutations in memory and perform one deterministic end-of-batch write through a same-directory temporary file followed by final replacement. | A single write phase reduces file-system work, narrows mutation windows, and makes rollback and parity comparison easier to reason about. |
| 3 | Record parsing and formatting | Fixed-width pipe-delimited layouts are embedded as COBOL substring offsets such as ops-row(1:1), ops-row(3:8), and bank-row(10:12). | Define an explicit record contract for accounts.dat and operations.dat in the modern engine, preserving accounts.dat as IIIIIIII|BBBBBBBBBBBB and operations.dat as K|SSSSSSSS|TTTTTTTT|AAAAAAAAAAAA. | Making the layout explicit protects byte-identical output behavior and reduces the chance of accidental formatting drift during modernization. |
| 4 | Testing framework | No automated tests, benchmark fixtures, or parity harness are present in the repository. | Add golden-file parity tests that execute the COBOL baseline and the modern engine against the same fixtures and compare final ledger bytes, processed count, rejected count, and total cents. | The modernization depends on preserving cent-accurate behavior, so executable parity tests are required before and during performance refactoring. |
| 5 | Prototype API and operator visibility | The legacy program only reads local files and prints PROCESSED, REJECTED, and TOTAL_CENTS to stdout. | Expose a small prototype API and dashboard surface limited to batch execution, run status, parity results, rejection summaries, audit history, generated ledger download, and performance measurements. | This supports the requested one-day demo without expanding into production banking functionality or changing the core ledger contract. |

## Packages & Dependencies

*Dependency upgrades and vulnerability remediation*

| # | Area | Current | Proposed | Rationale |
| --- | --- | --- | --- | --- |
| 1 | COBOL baseline compiler | Compiler/runtime version is not specified in the repository. | Use a pinned COBOL baseline runner such as GnuCOBOL 3.2 for local parity execution, or IBM Enterprise COBOL 6.5.x / OpenText Visual COBOL 10.0 where those environments are the chosen host. | Pinning the baseline compiler makes parity results reproducible and aligns the legacy execution path with currently supported COBOL tooling. |
| 2 | Golden-file and regression tests | No testing dependency or framework is present. | Add a test harness using pytest 8.x for fixture-driven parity tests, including valid deposits, withdrawals, transfers, malformed rows, insufficient funds, missing accounts, self-transfers, zero amounts, and non-numeric amounts. | A lightweight test framework turns the legacy ledger behavior into living specifications and reduces regression risk during the batch-engine rewrite. |
| 3 | Benchmark measurement | The README mentions parity benchmarking, but no benchmark package or repeatable benchmark assets are present. | Use pytest-benchmark 5.x or a small dedicated timing harness with fixture sets for 1,200 accounts × 400 operations and 5,000 accounts × 500 operations. | Measured performance must be reproducible and labeled clearly, especially because the current 28.6x and 128.1x speedups are local prototype results pending independent review. |
| 4 | Prototype API layer | No HTTP API package exists; the batch is invoked as a local program over files. | For the one-day prototype, use FastAPI 0.115.x or later with Pydantic 2.x for typed request and response validation around batch runs, results, audit history, and parity reports. | A small typed API makes the modernization testable without introducing a large application platform or implying production banking readiness. |
| 5 | Prototype dashboard UI | No user interface package exists. | Use a minimal React 19 + Vite 7 + Tailwind CSS 4 prototype frontend for the operator dashboard and clearly labeled legacy-terminal visual simulation. | This provides the requested before/after demo surface while keeping the UI lightweight and explicitly scoped to prototype observability. |

## Infrastructure

*Hosting, orchestration, and platform modernization*

| # | Area | Current | Proposed | Rationale |
| --- | --- | --- | --- | --- |
| 1 | Batch runtime execution | The program assumes accounts.dat, operations.dat, and accounts.tmp exist in the current working directory. | Package the prototype in a reproducible local container or scripted development environment with mounted fixture directories and pinned compiler/runtime versions. | A controlled runtime prevents environment drift from invalidating parity or performance results while avoiding unnecessary production infrastructure. |
| 2 | Ledger publication | accounts.dat is repeatedly rewritten during the batch through accounts.tmp for each accepted operation. | Write the final ledger once to a same-directory temporary output, validate record counts and optional checksums, then replace the target ledger in a final publish step. | This reduces partial-write exposure and supports explicit migration and rollback notes without changing the fixed-width ledger contract. |
| 3 | CI and regression verification | No CI/CD or automated verification is visible. | Add a CI job that builds/runs the COBOL baseline, executes the modern engine, runs golden-file parity tests, and records benchmark outputs for the required fixture sizes. | Automated parity gates ensure that performance improvements do not silently alter accepted/rejected behavior or final balances. |
| 4 | Fixture and output management | No benchmark fixtures, golden outputs, or structured run artifacts are present in the repository. | Store synthetic fixture inputs, expected COBOL outputs, modern outputs, summaries, timings, and comparison results as versioned test artifacts. | Versioned artifacts make the modernization independently reviewable and prevent benchmark claims from relying on undocumented local state. |
| 5 | Audit and run history | The batch emits only stdout summary lines and mutates the ledger file. | Record prototype audit events for run started, run completed, run failed, fixture selected, ledger generated, parity executed, and performance measured. | Audit history supports demo traceability and engineering review while remaining clearly labeled as prototype-level evidence, not production compliance. |

## Technical Capabilities

*New capabilities unlocked by modernization*

| # | Area | Current | Proposed | Rationale |
| --- | --- | --- | --- | --- |
| 1 | Indexed account lookup | Each operation reopens and scans accounts.dat to find source and destination accounts. | Load accounts.dat once into an indexed in-memory structure keyed by account ID and perform constant-time or logarithmic lookups during operation processing. | This removes the main Data Weight bottleneck and makes performance scale with account and operation volume far more predictably. |
| 2 | Single-pass operation processing | The legacy batch validates and rewrites the ledger operation by operation. | Process operations sequentially against the in-memory ledger state and apply accepted mutations immediately in memory while counting rejected rows. | Sequential in-memory processing preserves legacy ordering semantics while eliminating repeated full-file I/O. |
| 3 | One final ledger write per batch | The entire account file is rewritten for every accepted operation. | Perform one deterministic final ledger serialization after all operations are processed, preserving original account ordering and fixed-width formatting. | This dramatically reduces write volume and enables byte-identical final-balance comparison against the COBOL baseline. |
| 4 | Golden-file behavioral parity | Behavioral rules are embedded in COBOL code and comments without executable regression coverage. | Use golden fixtures to verify valid deposits, withdrawals, transfers, overdraft rejection, invalid-row rejection, missing accounts, self-transfers, zero amounts, malformed rows, final ledger output, and summary totals. | Golden-file testing protects the legacy contract while allowing the implementation strategy to change. |
| 5 | Measured performance reporting | The source documents an intentional scaling bottleneck, but the repository does not provide reproducible benchmark runs. | Measure and report runtime for 1,200 accounts × 400 operations and 5,000 accounts × 500 operations, clearly labeling preliminary speedups as local prototype results on one host pending independent review. | Transparent measurement demonstrates the value of the indexed design without overstating benchmark validity. |
| 6 | Prototype run observability | Only PROCESSED, REJECTED, and TOTAL_CENTS are printed to stdout. | Expose structured run results containing processed count, rejected count, total cents, duration, rejection summary, parity status, and generated ledger artifact references. | Structured results make the batch testable through APIs and usable from the requested operator dashboard without changing ledger semantics. |

## Risk Register

*Top risks for this modernization effort*

| # | Area | Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- | --- | --- |
| 1 | Ledger behavior parity | The modern engine may subtly diverge from COBOL behavior for rejected rows, overdrafts, missing accounts, or operation ordering. | high | high | Create golden fixtures for every documented acceptance and rejection case, run both COBOL and modern engines on the same inputs, and block changes unless final ledger bytes and summary counts match. |
| 2 | Fixed-width formatting | Output may be numerically correct but not byte-identical because of padding, field width, newline, ordering, or delimiter differences. | medium | high | Define the account and operation record layouts explicitly, compare generated accounts.dat byte-for-byte, and include newline and ordering checks in parity tests. |
| 3 | Single final write phase | A failed batch could leave a partial output or overwrite the original ledger incorrectly if the temp-file replacement is implemented poorly. | medium | high | Write to a same-directory temp file, validate record counts before publish, replace only at the final step, retain original inputs, and document rollback to the COBOL baseline. |
| 4 | Performance claims | Local speedup numbers such as 28.6x and 128.1x may be interpreted as independently validated production benchmarks. | medium | medium | Label those values as local prototype results on one host pending independent review and store repeatable benchmark fixtures, commands, host details, and raw timings. |
| 5 | Scope control | The prototype could drift into production banking, compliance, identity, or real customer-data assumptions beyond the selected modernization scope. | medium | medium | Keep the implementation limited to synthetic fixtures, indexed batch processing, one-write ledger output, parity tests, performance reporting, and clearly labeled prototype/demo UI surfaces. |
