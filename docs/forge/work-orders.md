## Prototype Runtime Foundation and Fixed-Width Contract

### [P0] Scaffold Python modernization package

Create a minimal Python project scaffold so modernization engineers can install and test the prototype runtime repeatably instead of relying only on the legacy COBOL source. The change belongs at the repository root in pyproject.toml, with README.md updated to describe the new local Python package alongside the existing bank.cob baseline. The current repository has only bank.cob and README.md, so there is no package metadata, test runner configuration, or typed module namespace for future fixed-width contract work. Stakeholders need this foundation because parity, fixture validation, and the modern CLI must be automated from a predictable runtime rather than ad hoc interpreter commands. When the story is complete, a developer can install the project in editable mode, import the modern_bank package, and run pytest without external service dependencies. This story does not implement the ledger engine, fixed-width record parsing, Dockerized COBOL execution, fixture allow-listing, or the modern batch CLI. It depends only on the existing modernization objective in README.md and the legacy contract documented in bank.cob. The scaffold should stay intentionally small, local-only, and synthetic-data oriented so the one-day prototype does not drift into production platform scope. It should also make later automation easy for DevOps teams by keeping commands deterministic and avoiding hidden global environment assumptions.

| Field | Value |
|---|---|
| Story Points | 2 |
| Hours | 20h |
| Priority | P0 |
| Labels | epic:runtime-foundation, type:devex, type:modernization, complexity:low |

**Acceptance Criteria**
- Unit tests: running python -m pytest tests/test_project_scaffold.py from the repository root succeeds and test_project_imports_modern_bank imports modern_bank from modern_bank/__init__.py.
- System integration tests: N/A — this story creates package metadata only and does not expose a service boundary, but python -m pip install -e . must complete using pyproject.toml without requiring accounts.dat or operations.dat.
- Mock data/fixtures: N/A — no ledger parsing is implemented in this scaffold story; README.md must state that synthetic fixture files are introduced by later fixture work rather than by pyproject.toml.
- File inspection of pyproject.toml shows project.name is bbs-sg-modern, requires-python is set to a Python 3 compatible floor, pytest configuration is present under tool.pytest.ini_options, and package discovery includes modern_bank.
- File inspection of README.md shows a Python modernization section that references pyproject.toml, modern_bank/__init__.py, pytest, and the existing bank.cob COBOL baseline without claiming production banking readiness.

### [P0] Add reproducible COBOL baseline runner

Add a Dockerfile and a scripts/run_legacy.sh wrapper so engineers can execute the authoritative COBOL baseline reproducibly for parity evidence. The change belongs at the repository root in Dockerfile and under scripts/run_legacy.sh, with README.md updated to show how the wrapper runs bank.cob against accounts.dat and operations.dat in a controlled working directory. Today bank.cob assumes current-directory files and there is no build script, compiler pin, or containerized runtime path for DevOps teams to reproduce baseline results. Stakeholders need this because the modern Python implementation cannot be trusted unless every parity fixture can run against the same legacy behavior on demand. When the story is complete, a developer can build a local GnuCOBOL image and run the baseline wrapper against synthetic fixture files to produce the legacy stdout summary and mutated accounts.dat. This story does not change bank.cob logic, implement the Python engine, add the fixed-width codec, or create the full golden-file parity harness. It depends on the existing COBOL compiler model and the flat-file names documented directly in bank.cob. The wrapper should be automation-first, fail fast on missing inputs, avoid shell interpolation of untrusted arguments, and preserve run artifacts so failures are debuggable. The operational outcome is a small repeatable baseline run path that later tests and benchmark jobs can call without hand-written compiler commands.

| Field | Value |
|---|---|
| Story Points | 3 |
| Hours | 30h |
| Priority | P0 |
| Labels | epic:runtime-foundation, type:devops, type:baseline, complexity:medium |

**Acceptance Criteria**
- Unit tests: N/A — scripts/run_legacy.sh is a shell wrapper around bank.cob, and verification is performed by the executable integration command documented in README.md.
- System integration tests: running docker build -t bbs-sg-legacy-baseline . uses Dockerfile and completes without modifying bank.cob.
- System integration tests: running scripts/run_legacy.sh tests/fixtures/legacy_smoke after creating tests/fixtures/legacy_smoke/accounts.dat and tests/fixtures/legacy_smoke/operations.dat exits with status 0 and stdout contains PROCESSED=, REJECTED=, and TOTAL_CENTS= from bank.cob.
- Mock data/fixtures: tests/fixtures/legacy_smoke/accounts.dat and tests/fixtures/legacy_smoke/operations.dat are committed with synthetic rows that match the bank.cob layouts IIIIIIII|BBBBBBBBBBBB and K|SSSSSSSS|TTTTTTTT|AAAAAAAAAAAA.
- File inspection of scripts/run_legacy.sh shows it checks for accounts.dat and operations.dat inside the supplied work directory, invokes cobc with bank.cob as an argument array or quoted path, and does not use eval.
- File inspection of README.md shows a legacy baseline section referencing Dockerfile, scripts/run_legacy.sh, bank.cob, accounts.dat, operations.dat, and accounts.tmp.

### [P0] Implement fixed-width record codec

Implement modern_bank/records.py with a FixedWidthCodec so the Python prototype has one canonical parser and serializer for the legacy account and operation row contracts. The new module must mirror the offsets embedded in bank.cob, specifically account ID from bank-row positions 1 through 8, balance from positions 10 through 21, operation kind from ops-row position 1, source ID from positions 3 through 10, destination ID from positions 12 through 19, and amount from positions 21 through 32. Today those contracts exist only in bank.cob comments, COBOL substring expressions, and README.md prose, which makes later parity work fragile if each Python component re-creates offsets separately. Stakeholders need a single executable contract because byte-identical ledgers and cent-accurate summaries are the primary acceptance gate for modernization. When the story is complete, tests can parse and format accounts.dat rows as IIIIIIII|BBBBBBBBBBBB and operations.dat rows as K|SSSSSSSS|TTTTTTTT|AAAAAAAAAAAA without using floats. The codec must reject malformed row shape, nonnumeric account IDs, nonnumeric balances, nonnumeric amounts, zero amounts where operation parsing validates amount semantics, unsupported operation kinds, and duplicate account IDs when parsing a ledger collection. This story does not process a batch, mutate balances, publish accounts.dat, call bank.cob, build benchmarks, or implement a CLI. It depends on the Python package scaffold capability and on the legacy offsets documented in the COBOL baseline. The implementation should make safety divergences explicit by rejecting duplicate account records and balance values outside the 12-digit ledger field instead of reproducing legacy truncation defects. This module becomes the low-blast-radius seam that later engine, fixture, parity, and operator tooling should import rather than duplicating fixed-position string slicing.

| Field | Value |
|---|---|
| Story Points | 5 |
| Hours | 50h |
| Priority | P0 |
| Labels | epic:runtime-foundation, type:contract, type:testing, complexity:medium |

**Acceptance Criteria**
- Unit tests: running python -m pytest tests/test_records.py succeeds and includes assertions for FixedWidthCodec.parse_account_line, FixedWidthCodec.format_account_record, FixedWidthCodec.parse_operation_line, and FixedWidthCodec.format_operation_record.
- System integration tests: N/A — modern_bank/records.py is a pure contract module with no service boundary or subprocess boundary; integration with scripts/run_modern.py is covered by the later CLI story.
- Mock data/fixtures: tests/test_records.py commits representative account rows such as 00000001|000000001000 and operation rows such as D|00000001|00000000|000000000250 as test literals or fixture parameters.
- File inspection of modern_bank/records.py shows AccountRecord and OperationRecord data structures store monetary values as Python int cents and contain no float annotations, float conversions, or decimal point parsing.
- pytest test test_account_offsets_match_bank_cob in tests/test_records.py asserts that parsing 12345678|000000000999 returns account_id 12345678 and balance_cents 999 from the same offsets used by bank.cob bank-row(1:8) and bank-row(10:12).
- pytest test test_operation_offsets_match_bank_cob in tests/test_records.py asserts that parsing T|00000001|00000002|000000000125 returns kind T, source_account_id 00000001, destination_account_id 00000002, and amount_cents 125 from the same offsets used by bank.cob ops-row fields.
- pytest test test_parse_accounts_rejects_duplicate_ids in tests/test_records.py asserts that FixedWidthCodec.parse_accounts raises a ValueError or project-specific record validation error for two account rows with the same 8-digit account ID.

### [P0] Add fixture allow-list catalog

Create tests/fixtures/fixture_catalog.json as an allow-list of synthetic accounts.dat and operations.dat fixture IDs so parity and demo tooling never accept arbitrary local paths. The catalog belongs under tests/fixtures/fixture_catalog.json, with fixture files stored under tests/fixtures and README.md updated to explain the allow-list boundary. The current repository has no tests directory, no fixture inventory, and no governed way to distinguish approved synthetic inputs from accidental or real data files. Stakeholders need this control because later parity, benchmark, and local UI flows must be able to select known fixture IDs without exposing the filesystem as an input surface. When the story is complete, a test can load the catalog, resolve every listed accounts.dat and operations.dat path relative to tests/fixtures, and validate the listed rows with the Python fixed-width codec. This story does not generate the full golden-file parity suite, run the COBOL baseline, compare modern and legacy outputs, or produce benchmark timings. It depends on the fixed-width codec capability so the catalog test can validate row shapes using the same contract as the modern engine. The catalog should include stable IDs, fixture categories, relative file paths, parity-critical flags, and synthetic-data labeling so later automation can fail closed on unknown fixture IDs. From an operational perspective, this story reduces blast radius by establishing an allow-list before the modern CLI or demo surface starts accepting fixture selections. The committed sample fixtures should be small, deterministic, and safe for local execution.

| Field | Value |
|---|---|
| Story Points | 3 |
| Hours | 30h |
| Priority | P0 |
| Labels | epic:runtime-foundation, type:fixtures, type:security, complexity:medium |

**Acceptance Criteria**
- Unit tests: running python -m pytest tests/test_fixture_catalog.py succeeds and test_fixture_catalog_entries_validate_with_fixed_width_codec parses each catalog accounts.dat and operations.dat file through FixedWidthCodec.
- System integration tests: N/A — tests/fixtures/fixture_catalog.json is a local allow-list artifact and does not expose a service or subprocess boundary in this story.
- Mock data/fixtures: tests/fixtures/fixture_catalog.json and at least one committed fixture directory containing accounts.dat and operations.dat are present under tests/fixtures.
- Running python -m json.tool tests/fixtures/fixture_catalog.json exits with status 0, proving the fixture catalog is valid JSON.
- File inspection of tests/fixtures/fixture_catalog.json shows each fixture entry contains id, category, accounts_path, operations_path, synthetic_data, and parity_required fields.
- pytest test test_fixture_catalog_rejects_absolute_paths in tests/test_fixture_catalog.py asserts that accounts_path and operations_path entries in tests/fixtures/fixture_catalog.json are relative paths and do not begin with a filesystem root.
- pytest test test_fixture_catalog_ids_are_unique in tests/test_fixture_catalog.py asserts that no two fixture entries in tests/fixtures/fixture_catalog.json share the same id.

**Depends on:** WO-003

### [P0] Add modern CLI contract skeleton

Add scripts/run_modern.py as the first Python CLI entry point so operators and automation can validate accounts.dat and operations.dat inputs through the modern record contract before the full engine exists. The script belongs under scripts/run_modern.py and must import modern_bank.records rather than duplicating offsets from bank.cob. Today the only executable path is bank.cob, which mutates accounts.dat directly and provides no Python command boundary for later indexed processing, safe publication, or parity automation. Stakeholders need a thin CLI seam because fixture-based validation, benchmark harnesses, and future demo surfaces should all call one local command instead of hand-wiring Python modules. When the story is complete, a developer can run the CLI with explicit accounts and operations file paths, receive a deterministic contract-validation result, and get a nonzero exit with a safe message for malformed inputs. This story does not implement balance mutation, indexed lookups, overdraft logic, final ledger publication, parity comparison, Docker invocation, audit logging, or web UI behavior. It depends on the Python package scaffold and the fixed-width codec capability. The CLI should remain a skeleton with clear extension points for the later batch processor, keeping business rules out of the script and limiting the blast radius of future changes. For reliability, the command must fail closed on missing files or invalid rows and must not leak stack traces or absolute host paths in user-facing error output. The initial system test should use committed synthetic fixture files so DevOps teams can exercise the boundary without external data.

| Field | Value |
|---|---|
| Story Points | 3 |
| Hours | 30h |
| Priority | P0 |
| Labels | epic:runtime-foundation, type:cli, type:operability, complexity:medium |

**Acceptance Criteria**
- Unit tests: running python -m pytest tests/test_run_modern_cli.py succeeds and includes coverage for the main function in scripts/run_modern.py using valid and invalid fixture paths.
- System integration tests: running python scripts/run_modern.py --accounts tests/fixtures/modern_smoke/accounts.dat --operations tests/fixtures/modern_smoke/operations.dat --contract-check exits with status 0 and stdout contains CONTRACT_OK.
- Mock data/fixtures: tests/fixtures/modern_smoke/accounts.dat and tests/fixtures/modern_smoke/operations.dat are committed and are parsed by tests/test_run_modern_cli.py.
- System integration tests: running python scripts/run_modern.py --accounts tests/fixtures/modern_smoke/missing.dat --operations tests/fixtures/modern_smoke/operations.dat --contract-check exits nonzero and stderr contains INPUT_NOT_FOUND without a Python traceback.
- File inspection of scripts/run_modern.py shows it imports FixedWidthCodec from modern_bank.records and does not hardcode bank.cob substring offsets such as 21:12 or 10:12.
- File inspection of scripts/run_modern.py shows argparse defines --accounts, --operations, and --contract-check arguments, with no HTTP server, database connection, or production banking endpoint.
- pytest test test_cli_invalid_operation_reports_safe_error in tests/test_run_modern_cli.py asserts stderr does not contain Traceback and does not contain an absolute path when an operations.dat row is malformed.

**Depends on:** WO-001, WO-003

---

## Indexed Modern Ledger Processing Engine

### [P0] Build ordered ledger account index

Implement an ordered in-memory ledger account map so the modern batch can look up accounts without reopening and scanning the full ledger for every operation. The work belongs in the LedgerIndex module at modern_bank/ledger.py, created alongside the existing legacy reference program in bank.cob. The current COBOL path treats accounts.dat as the source of truth but pays an O(m x n) file-I/O cost because every operation scans account rows repeatedly. Stakeholders need the same fixed-width ledger behavior with materially less file work so parity and benchmark evidence can be produced on the required synthetic fixtures. When this story is complete, loading accounts.dat will produce a deterministic account order list plus an indexed lookup keyed by each 8-digit account ID. Developers should be able to inspect modern_bank/ledger.py and see parsing for the account contract IIIIIIII|BBBBBBBBBBBB, integer-cent balances, and serialization that preserves the same field widths and delimiter. The module must preserve original ledger ordering for final output rather than sorting accounts by key unless a later requirement explicitly changes ordering. This story does not implement operation processing, rejection counters, summary formatting, benchmark reporting, web APIs, or final safe ledger publication. It depends on the capability to create the Python package scaffold and run local tests in this repository, while bank.cob remains the authoritative behavior reference. The implementation should keep blast radius low by making ledger parsing and lookup testable without invoking the COBOL runtime or any external service.

| Field | Value |
|---|---|
| Story Points | 5 |
| Hours | 50h |
| Priority | P0 |
| Labels | epic:EPIC-002, modernization, ledger-index, flat-file, complexity:medium |

**Acceptance Criteria**
- Unit tests: running python -m pytest tests/test_ledger.py exits with code 0 and includes assertions that LedgerIndex.load_from_path in modern_bank/ledger.py parses tests/fixtures/ledger/basic_accounts.dat into account_ids [00000001, 00000002, 00000003] in source-file order.
- Unit tests: tests/test_ledger.py asserts LedgerIndex.get_account in modern_bank/ledger.py returns integer balance 1250 for account ID 00000001 and returns None or raises the documented lookup exception for account ID 99999999 without reading accounts.dat again.
- Unit tests: tests/test_ledger.py asserts LedgerIndex.to_rows in modern_bank/ledger.py serializes every row as exactly 21 characters before the newline using 8 account digits, one pipe at offset 9, and 12 balance digits.
- System integration tests: N/A — bbs-sg-legacy.zip currently exposes 0 API endpoints and this story only introduces the batch-core LedgerIndex module; the verifiable boundary is the file-to-module test in tests/test_ledger.py.
- Mock data and fixtures: tests/fixtures/ledger/basic_accounts.dat is committed and contains at least three rows matching IIIIIIII|BBBBBBBBBBBB for deterministic local test execution without external dependencies.
- File inspection: modern_bank/ledger.py contains no float, decimal floating-point, or currency arithmetic path; balances are stored and mutated as Python int values representing cents.

**Depends on:** WO-003

### [P0] Preflight account ledger validity

Add duplicate account and 12-digit balance preflight checks so the modern batch refuses unsafe ledger input before any balance mutation can occur. The work belongs in the LedgerIndex module at modern_bank/ledger.py, extending the ordered account map created for accounts.dat. The legacy COBOL source in bank.cob assumes unique 8-digit account IDs and 12-digit balances but does not enforce those assumptions as a full preflight gate. Stakeholders explicitly need the modern Python prototype to characterize and avoid known legacy defects such as duplicate account rewrites or balance field overflow. When this story is complete, a malformed account ledger will fail during load with a clear row-level diagnostic and no processor will receive a partially trusted ledger. Developers should observe that duplicate 8-digit account IDs are detected before operation processing starts and that balance fields must be exactly 12 numeric digits. This story does not add operation-row rejection paths, overdraft logic, summary formatting, final publication, or benchmark claims. It depends on the ordered ledger index capability being present so validation can be integrated with the single ledger load path instead of a second scan. The failure behavior should be operationally safe: fail closed, preserve original inputs, and produce a deterministic error that can be asserted in tests. The implementation must still preserve parity for well-formed in-range fixtures and document that stricter preflight behavior is an intentional safety divergence from the legacy defect surface.

| Field | Value |
|---|---|
| Story Points | 3 |
| Hours | 30h |
| Priority | P0 |
| Labels | epic:EPIC-002, modernization, input-validation, ledger-preflight, complexity:medium |

**Acceptance Criteria**
- Unit tests: running python -m pytest tests/test_ledger_preflight.py exits with code 0 and asserts LedgerIndex.load_from_path in modern_bank/ledger.py raises DuplicateAccountError for tests/fixtures/ledger/duplicate_accounts.dat containing account ID 00000001 twice.
- Unit tests: tests/test_ledger_preflight.py asserts LedgerIndex.load_from_path in modern_bank/ledger.py raises InvalidAccountRowError for tests/fixtures/ledger/bad_balance_width.dat where the balance field is not exactly 12 digits.
- Unit tests: tests/test_ledger_preflight.py asserts LedgerIndex.load_from_path in modern_bank/ledger.py raises InvalidAccountRowError for tests/fixtures/ledger/non_numeric_balance.dat where bank-row(10:12) contains a non-numeric character.
- System integration tests: N/A — bbs-sg-legacy.zip currently has 0 API endpoints and this story is a file preflight gate inside modern_bank/ledger.py; integration with operation processing is covered by later batch-core tests.
- Mock data and fixtures: tests/fixtures/ledger/duplicate_accounts.dat, tests/fixtures/ledger/bad_balance_width.dat, and tests/fixtures/ledger/non_numeric_balance.dat are committed and referenced by tests/test_ledger_preflight.py.
- File inspection: README.md contains migration notes stating that duplicate account records and invalid 12-digit balances are rejected by the modern preflight before any write, while bank.cob remains the parity baseline for well-formed in-range fixtures.

**Depends on:** WO-007

### [P0] Process accepted DWT mutations

Implement the modern operation processor for accepted deposit, withdrawal, and transfer rows so balances mutate in memory using integer cents and source-file order. The work belongs in OperationProcessor at modern_bank/processor.py, consuming the LedgerIndex behavior in modern_bank/ledger.py and preserving the process-operation semantics from bank.cob. The current COBOL path validates and applies each operation by scanning and rewriting accounts.dat, which creates repeated full-ledger file work for every accepted operation. Stakeholders need the same accepted-operation outcomes with the mutation cost moved into a deterministic in-memory engine that later can be published once. When this story is complete, valid D, W, and T records from operations.dat will be parsed from the legacy fixed positions and applied sequentially to the ordered ledger index. Deposits must add amount cents to the source account, withdrawals must subtract amount cents from the source account, and transfers must subtract from source and add to destination. Accepted rows must increment the processed count and leave the rejected count unchanged for this happy-path story. The implementation must not use floating-point arithmetic, must not write accounts.dat or accounts.tmp per operation, and must not implement malformed-row rejection paths that belong to the rejection-focused processor story. It depends on the ledger index and ledger preflight capabilities so operation code can rely on a trusted in-memory account map. The observable outcome is a processor result object that exposes processed count, rejected count, and the mutated LedgerIndex state for later summary and publication components.

| Field | Value |
|---|---|
| Story Points | 5 |
| Hours | 50h |
| Priority | P0 |
| Labels | epic:EPIC-002, modernization, operation-processing, integer-cents, complexity:medium |

**Acceptance Criteria**
- Unit tests: running python -m pytest tests/test_processor_valid_ops.py exits with code 0 and asserts OperationProcessor.process_rows in modern_bank/processor.py applies D|00000001|00000000|000000000250 by increasing account 00000001 in LedgerIndex by 250 cents.
- Unit tests: tests/test_processor_valid_ops.py asserts OperationProcessor.process_rows in modern_bank/processor.py applies W|00000001|00000000|000000000100 by decreasing account 00000001 in LedgerIndex by 100 cents when funds are available.
- Unit tests: tests/test_processor_valid_ops.py asserts OperationProcessor.process_rows in modern_bank/processor.py applies T|00000001|00000002|000000000125 by subtracting 125 cents from account 00000001 and adding 125 cents to account 00000002 in the same in-memory ledger.
- Integration tests: running python -m pytest tests/test_processor_ledger_integration.py exits with code 0 and asserts tests/fixtures/operations/valid_sequence.dat is processed in source-file order against tests/fixtures/ledger/basic_accounts.dat with final LedgerIndex.to_rows output matching tests/fixtures/expected/valid_sequence_accounts.dat.
- Mock data and fixtures: tests/fixtures/operations/valid_sequence.dat and tests/fixtures/expected/valid_sequence_accounts.dat are committed and require no external COBOL compiler, network access, or database.
- File inspection: modern_bank/processor.py contains no open, write, replace, or accounts.tmp file mutation path; operation processing mutates the LedgerIndex object created by modern_bank/ledger.py.

**Depends on:** WO-007, WO-010

### [P0] Preserve processor rejection paths

Add processor rejection paths for malformed operation rows, invalid amounts, missing accounts, self-transfers, unsupported types, overdrafts, and 12-digit balance overflow so invalid rows increment rejection counts without aborting the batch. The work belongs in OperationProcessor at modern_bank/processor.py, extending the accepted mutation engine that consumes modern_bank/ledger.py. The legacy process-operation paragraph in bank.cob rejects invalid operation rows and continues processing, and that behavior is a primary parity requirement for the modernization prototype. Stakeholders need high-confidence rejection semantics because a behavior drift here would change final balances, processed counts, rejected counts, and total cents. When this story is complete, invalid rows from operations.dat will be classified as rejected, the rejected count will increment by one per invalid row, and no balance mutation will be applied for that row. The processor must parse operation kind from position 1, source account from positions 3 through 10, destination account from positions 12 through 19, and amount text from positions 21 through 32. This story must also implement the modern safety divergence that rejects any deposit or transfer whose resulting balance would exceed the 12-digit ledger field, rather than allowing COBOL-style truncation defects. It does not implement summary formatting, final safe ledger publication, parity harness orchestration, UI, API endpoints, or benchmark reporting. It depends on the valid D, W, and T in-memory mutation capability and the ledger preflight behavior that guarantees account records are unique and well-formed. The operational goal is reject-and-continue for row-level business problems while reserving fail-closed behavior for file-level ledger preflight failures.

| Field | Value |
|---|---|
| Story Points | 8 |
| Hours | 80h |
| Priority | P0 |
| Labels | epic:EPIC-002, modernization, rejection-semantics, parity-risk, complexity:high |

**Acceptance Criteria**
- Unit tests: running python -m pytest tests/test_processor_rejections.py exits with code 0 and asserts OperationProcessor.process_rows in modern_bank/processor.py increments rejected by 1 and leaves LedgerIndex balances unchanged for unsupported operation kind X.
- Unit tests: tests/test_processor_rejections.py asserts modern_bank/processor.py rejects non-numeric amount text, zero amount text 000000000000, and operation rows shorter than 32 characters without mutating any account balance.
- Unit tests: tests/test_processor_rejections.py asserts modern_bank/processor.py rejects missing source account 99999999 for D, W, and T rows and rejects missing transfer destination account 99999998 for T rows.
- Unit tests: tests/test_processor_rejections.py asserts modern_bank/processor.py rejects self-transfer T|00000001|00000001|000000000001 and rejects W or T rows that would reduce source balance below zero.
- Unit tests: tests/test_processor_rejections.py asserts modern_bank/processor.py rejects a deposit or transfer destination update that would make the resulting balance greater than 999999999999 cents, and processed remains unchanged for that row.
- Integration tests: running python -m pytest tests/test_processor_rejection_sequence.py exits with code 0 and asserts tests/fixtures/operations/rejection_sequence.dat produces the expected final ledger rows in tests/fixtures/expected/rejection_sequence_accounts.dat while continuing after rejected rows.
- Mock data and fixtures: tests/fixtures/operations/rejection_sequence.dat and expected ledger fixture tests/fixtures/expected/rejection_sequence_accounts.dat are committed with cases for invalid type, malformed row, non-numeric amount, zero amount, missing source, missing destination, self-transfer, overdraft, and overflow.
- System integration tests: N/A for HTTP boundaries — bbs-sg-legacy.zip has 0 API endpoints; the applicable system boundary for this story is processor-plus-ledger integration in tests/test_processor_rejection_sequence.py.

**Depends on:** WO-011

### [P0] Format fixed-width batch summary

Implement fixed-width summary formatting so the modern batch emits PROCESSED, REJECTED, and TOTAL_CENTS lines compatible with the legacy COBOL output contract. The work belongs in the SummaryReporter module at modern_bank/summary.py, consuming processed and rejected counts from modern_bank/processor.py and final balances from modern_bank/ledger.py. The current COBOL program in bank.cob prints these three metrics at the end using picture-clause widths of 8, 8, and 16 digits. Stakeholders need exact summary formatting because parity approval compares not only final ledger bytes but also processed count, rejected count, and total cents. When this story is complete, the modern formatter will return or write three newline-separated lines in the order PROCESSED, REJECTED, and TOTAL_CENTS. The numeric fields must be zero-padded to 8 digits for processed and rejected counts and 16 digits for total cents. TOTAL_CENTS must be computed from the final in-memory ledger using integer cents and must ignore floating-point or locale currency formatting entirely. This story does not implement operation validation, ledger parsing, final ledger publication, COBOL runner orchestration, API endpoints, UI display, or benchmark reporting. It depends on the processor result counters and ordered ledger state being available from the modern batch core. The observable result is a small isolated module that makes summary parity easy to test and prevents formatting logic from being duplicated across CLI, test, or future demo surfaces.

| Field | Value |
|---|---|
| Story Points | 2 |
| Hours | 20h |
| Priority | P0 |
| Labels | epic:EPIC-002, modernization, summary-formatting, fixed-width, complexity:low |

**Acceptance Criteria**
- Unit tests: running python -m pytest tests/test_summary.py exits with code 0 and asserts SummaryReporter.format_summary in modern_bank/summary.py returns PROCESSED=00000003, REJECTED=00000002, and TOTAL_CENTS=0000000000012500 for the specified test ledger and counters.
- Unit tests: tests/test_summary.py asserts SummaryReporter.calculate_total_cents in modern_bank/summary.py sums integer balances from LedgerIndex in modern_bank/ledger.py and returns an int, not a float or formatted currency string.
- Integration tests: running python -m pytest tests/test_summary_integration.py exits with code 0 and asserts OperationProcessor from modern_bank/processor.py plus SummaryReporter from modern_bank/summary.py formats the summary for tests/fixtures/operations/summary_mixed.dat exactly as tests/fixtures/expected/summary_mixed_stdout.txt.
- Mock data and fixtures: tests/fixtures/operations/summary_mixed.dat, tests/fixtures/expected/summary_mixed_accounts.dat, and tests/fixtures/expected/summary_mixed_stdout.txt are committed for repeatable local execution without external services.
- System integration tests: N/A for API endpoints — bbs-sg-legacy.zip has 0 API endpoints; the relevant system boundary is the in-process ledger, processor, and summary integration in tests/test_summary_integration.py.
- File inspection: modern_bank/summary.py contains exactly the three legacy labels PROCESSED=, REJECTED=, and TOTAL_CENTS= and formats counts with 8 digits and totals with 16 digits.

**Depends on:** WO-011

---

## Safe Ledger Publication and Operational Artifacts

### [P0] Publish ledger with safe replacement

Implement a LedgerPublisher that writes the final account ledger through a same-directory temporary file and then replaces accounts.dat so operators never see a partially written final ledger. The change belongs in the new modern_bank/publisher.py module, with tests under tests/test_publisher.py and fixture data under tests/fixtures/publisher. Today the legacy COBOL batch in bank.cob rewrites accounts.dat through accounts.tmp for every accepted operation, which increases the mutation window and makes interrupted runs harder to reason about. The target behavior is one end-of-batch publication primitive that accepts already-processed ledger rows, writes them to a temporary file located beside the target ledger, flushes and closes that file, and performs the final replacement only after the write step succeeds. When this story is done, a developer can run the publisher against a temporary workspace and observe that the temp file is created in the same directory as accounts.dat and that the final file changes only after the publish call reaches its replacement phase. Failed writes must leave the original accounts.dat bytes intact so rollback remains a whole-batch rerun from the original synthetic inputs. This story does not include record-count validation, FixedWidthCodec row validation, CLI orchestration, audit JSONL events, artifact retention metadata, or README rollback documentation. It depends on the modern fixed-width record contract and in-memory ledger processing capabilities being available so the publisher can focus only on safe file publication. The implementation should remain local-file based and must not introduce databases, remote storage, locking services, or production banking infrastructure. The operational intent is to reduce blast radius during ledger publication while keeping the prototype small enough for offline parity testing.

| Field | Value |
|---|---|
| Story Points | 5 |
| Hours | 50h |
| Priority | P0 |
| Labels | epic:EPIC-003, component:publisher, reliability, data-integrity, complexity:medium |

**Acceptance Criteria**
- Running python -m pytest tests/test_publisher.py::test_publish_uses_same_directory_temp_file exits with code 0 and asserts LedgerPublisher.publish in modern_bank/publisher.py creates its temporary ledger path with the same parent directory as the target accounts.dat.
- Running python -m pytest tests/test_publisher.py::test_publish_replaces_accounts_dat_only_after_success exits with code 0 and asserts modern_bank/publisher.py updates the target accounts.dat bytes only after the temporary file write has completed.
- Running python -m pytest tests/test_publisher.py::test_publish_failure_preserves_original_accounts_dat exits with code 0 and asserts LedgerPublisher.publish leaves the original accounts.dat content unchanged when the temp-file write raises an OSError.
- System integration test: running python -m pytest tests/test_publisher.py::test_end_to_end_publish_writes_expected_accounts_dat exits with code 0 using tests/fixtures/publisher/accounts.dat and verifies the final accounts.dat bytes equal the expected fixed-width ledger fixture.
- Mock data / fixtures: file inspection confirms tests/fixtures/publisher/original_accounts.dat and tests/fixtures/publisher/expected_accounts.dat are committed and contain rows shaped as IIIIIIII|BBBBBBBBBBBB.
- Unit tests: tests/test_publisher.py contains assertions for LedgerPublisher.publish, including same-directory temp placement, final replacement, and original-file preservation on write failure.

**Depends on:** WO-007, WO-013

### [P0] Validate ledger before replacement

Add record-count and FixedWidthCodec validation to LedgerPublisher before accounts.dat replacement so invalid or incomplete ledger output cannot be promoted as a completed batch result. The change belongs in modern_bank/publisher.py and should use the canonical fixed-width account codec rather than duplicating the bank.cob substring contract. The current safe replacement primitive can protect against partial writes, but without validation it could still publish the wrong number of rows or rows that do not match the IIIIIIII|BBBBBBBBBBBB account format. Stakeholders will recognize this as the data-integrity gate that prevents a numerically plausible but byte-incompatible ledger from entering parity evidence. When the story is done, publication will fail closed before os.replace if the serialized row count differs from the expected account count or any row violates the account record contract. Developers should be able to run targeted pytest cases that prove malformed rows, bad delimiters, short rows, non-numeric balances, and count mismatches preserve the original accounts.dat. This story does not implement the codec itself, change operation processing rules, create audit events, or wire CLI orchestration. It depends on the canonical account record parser and serializer capability and on the safe same-directory publication primitive already existing. The implementation should report safe validation failure details suitable for CLI display without exposing absolute host paths. This preserves the fixed-width contract as an executable publication gate rather than relying on comments in bank.cob.

| Field | Value |
|---|---|
| Story Points | 5 |
| Hours | 50h |
| Priority | P0 |
| Labels | epic:EPIC-003, component:publisher, component:codec, data-integrity, complexity:medium |

**Acceptance Criteria**
- Running python -m pytest tests/test_publisher_validation.py::test_publish_rejects_record_count_mismatch exits with code 0 and asserts LedgerPublisher.publish in modern_bank/publisher.py does not replace accounts.dat when expected_record_count differs from len(serialized_rows).
- Running python -m pytest tests/test_publisher_validation.py::test_publish_rejects_invalid_account_row exits with code 0 and asserts modern_bank/publisher.py invokes FixedWidthCodec validation before os.replace for rows not matching IIIIIIII|BBBBBBBBBBBB.
- Running python -m pytest tests/test_publisher_validation.py::test_validation_failure_preserves_original_accounts_dat exits with code 0 and asserts the target accounts.dat bytes remain equal to tests/fixtures/publisher_validation/original_accounts.dat after a malformed row failure.
- System integration test: running python -m pytest tests/test_publisher_validation.py::test_validated_publish_end_to_end exits with code 0 using modern_bank/publisher.py and modern_bank/codec.py to write a fixture ledger and compare the resulting accounts.dat bytes to tests/fixtures/publisher_validation/expected_accounts.dat.
- Mock data / fixtures: file inspection confirms tests/fixtures/publisher_validation/malformed_accounts_rows.dat and tests/fixtures/publisher_validation/expected_accounts.dat are committed and include at least one invalid delimiter case and one invalid numeric balance case.
- Unit tests: tests/test_publisher_validation.py contains assertions for record-count mismatch, FixedWidthCodec account-row failure, and successful validated publication through LedgerPublisher.publish.

**Depends on:** WO-014

### [P0] Orchestrate CLI ledger publication

Wire the modern CLI load process so accounts.dat and operations.dat are processed once and the final ledger is published through LedgerPublisher as the only accounts.dat mutation step. The change belongs in modern_bank/cli.py, with orchestration tests under tests/test_cli.py and CLI fixture workspaces under tests/fixtures/cli. The legacy bank.cob entry point mixes operation reading, validation, per-operation rewrites, final total calculation, and stdout reporting inside one procedural program. The target CLI should coordinate the already-built ledger loading, operation processing, summary reporting, and validated publication components without reintroducing per-operation file writes. When complete, running the CLI against a fixture workspace will read accounts.dat and operations.dat, process operations sequentially in memory, call LedgerPublisher once after processing, and print or return the summary labels PROCESSED, REJECTED, and TOTAL_CENTS. File-level failures such as missing accounts.dat, unreadable operations.dat, or publication validation failure must return a non-zero process exit and leave the original ledger intact. This story does not implement the processor, codec, publisher validation, audit writer, artifact store, web UI, parity runner, or benchmark runner. It depends on the fixed-width codec, ordered ledger processing, summary formatting, and validated safe publisher capabilities being available. The CLI must remain an offline local prototype surface and must not accept arbitrary remote inputs or imply production banking operation. This story establishes the operational control path that later audit and artifact stories can observe.

| Field | Value |
|---|---|
| Story Points | 5 |
| Hours | 50h |
| Priority | P0 |
| Labels | epic:EPIC-003, component:cli, component:publisher, operability, complexity:medium |

**Acceptance Criteria**
- Running python -m modern_bank.cli load --accounts tests/fixtures/cli/basic/accounts.dat --operations tests/fixtures/cli/basic/operations.dat exits with code 0 and prints PROCESSED=, REJECTED=, and TOTAL_CENTS= lines from modern_bank/cli.py.
- Running python -m pytest tests/test_cli.py::test_cli_invokes_ledger_publisher_once exits with code 0 and asserts modern_bank.cli calls LedgerPublisher.publish exactly once after operation processing completes.
- Running python -m pytest tests/test_cli.py::test_cli_missing_operations_file_returns_nonzero exits with code 0 and asserts the modern_bank/cli.py load command returns a non-zero status without replacing tests/fixtures/cli/missing_operations/accounts.dat.
- System integration test: running python -m pytest tests/test_cli.py::test_cli_load_end_to_end_updates_accounts_dat exits with code 0 and compares the fixture workspace accounts.dat bytes to tests/fixtures/cli/basic/expected_accounts.dat after the CLI load command.
- Mock data / fixtures: file inspection confirms tests/fixtures/cli/basic/accounts.dat, tests/fixtures/cli/basic/operations.dat, and tests/fixtures/cli/basic/expected_accounts.dat are committed and use the legacy fixed-width file contracts.
- Unit tests: tests/test_cli.py contains assertions for argument parsing in modern_bank/cli.py, non-zero failure status for missing input files, and the single call to LedgerPublisher.publish.

**Depends on:** WO-006, WO-012, WO-013, WO-015

### [P1] Append run audit JSONL

Implement append-only JSONL audit events for fixture selection, ledger generation, and run completion so every prototype ledger publication has a minimal operational trail. The change belongs in modern_bank/audit.py and should be called from modern_bank/cli.py after the load orchestration path is available. The current legacy batch in bank.cob prints only aggregate counters to stdout and leaves no structured record of which synthetic fixture was selected or when the final ledger was generated. Stakeholders need this traceability to review prototype evidence, diagnose failed runs, and satisfy the local one-year audit-artifact expectation without deploying a production audit platform. When the story is done, running the CLI against a fixture workspace will append JSON lines containing event_type, run_id, timestamp, actor, resource, and synthetic metadata for the required lifecycle points. Audit writes must be append-only, newline-delimited, parseable by Python json.loads, and safe to display without stack traces, secrets, or host paths. This story does not implement artifact storage metadata, benchmark events, parity comparison events, web UI display, centralized log shipping, or production SIEM integration. It depends on the CLI load orchestration and validated ledger publication path so audit events can represent real run lifecycle boundaries. The implementation should classify the audit content as Internal synthetic prototype evidence and avoid storing raw absolute fixture paths. This adds observability and recoverability without changing ledger processing behavior.

| Field | Value |
|---|---|
| Story Points | 3 |
| Hours | 30h |
| Priority | P1 |
| Labels | epic:EPIC-003, component:audit, observability, governance, complexity:medium |

**Acceptance Criteria**
- Running python -m pytest tests/test_audit.py::test_audit_writer_appends_jsonl_events exits with code 0 and asserts AuditWriter.append_event in modern_bank/audit.py appends valid JSON lines without overwriting the existing audit file.
- Running python -m pytest tests/test_audit.py::test_required_event_types_are_written exits with code 0 and asserts modern_bank/audit.py records fixture_selected, ledger_generated, and run_completed event_type values.
- Running python -m pytest tests/test_cli_audit_integration.py::test_cli_load_emits_audit_events exits with code 0 and asserts modern_bank/cli.py creates or appends audit.jsonl entries when the load command completes successfully.
- System integration test: running python -m pytest tests/test_cli_audit_integration.py::test_audit_jsonl_is_parseable_after_cli_run exits with code 0 and parses every line in the generated audit.jsonl with json.loads.
- Mock data / fixtures: file inspection confirms tests/fixtures/audit/basic/accounts.dat and tests/fixtures/audit/basic/operations.dat are committed for the CLI audit integration test.
- Unit tests: tests/test_audit.py contains assertions for AuditWriter.append_event timestamp presence, run_id presence, actor presence, resource presence, and append-only file growth.

**Depends on:** WO-016

### [P1] Document migration and rollback

Update README.md with the bank.cob fixed-width migration map and accounts.tmp rollback procedure so operators can run, verify, and recover the prototype safely. The change belongs in the existing README.md file at the repository root. The current README.md is only seven lines and names accounts.dat, operations.dat, the deliberate scan/rewrite bottleneck, and the modernization objective without detailed operational runbook guidance. Stakeholders need the documentation to explain exactly how COBOL substring offsets map to the modern fixed-width codec and why the Python publisher uses one final same-directory temporary ledger before replacement. When this story is done, a reviewer can inspect README.md and find the account row layout, operation row layout, bank.cob offset references, modern module ownership, safe publish sequence, and rollback procedure. The rollback procedure must cover retaining original inputs, comparing modern output with the COBOL baseline, discarding generated modern output, restoring or rerunning from original accounts.dat and operations.dat, and rerunning the legacy baseline when needed. This story does not change bank.cob behavior, implement Python code, create fixtures, or add audit/artifact modules. It depends on the CLI and validated publisher behavior being available so the documented runbook matches the implemented flow. The document must reinforce that all data is synthetic, local, and not production banking evidence. The goal is operational clarity that reduces mean time to recovery during failed demo or parity runs.

| Field | Value |
|---|---|
| Story Points | 2 |
| Hours | 20h |
| Priority | P1 |
| Labels | epic:EPIC-003, component:documentation, runbook, operability, complexity:low |

**Acceptance Criteria**
- File inspection of README.md shows a migration map section that references bank.cob offsets bank-row(1:8), bank-row(10:12), ops-row(1:1), ops-row(3:8), ops-row(12:8), and ops-row(21:12).
- File inspection of README.md shows the account ledger contract accounts.dat as IIIIIIII|BBBBBBBBBBBB and the operation feed contract operations.dat as K|SSSSSSSS|TTTTTTTT|AAAAAAAAAAAA.
- File inspection of README.md shows a rollback procedure that explicitly references accounts.tmp, accounts.dat, operations.dat, retaining original inputs, discarding generated modern output, and rerunning the COBOL baseline bank.cob.
- Documentation validation: running python -m pytest tests/test_readme_documentation.py::test_readme_contains_publication_runbook exits with code 0 and asserts README.md contains the safe temp-file replacement sequence and rollback keywords.
- Unit tests: N/A — README.md documentation has no executable unit-level business logic; verification is covered by tests/test_readme_documentation.py content assertions.
- System integration tests: N/A — this story changes documentation only; CLI and publisher integration behavior is validated by modern_bank/cli.py and modern_bank/publisher.py stories.
- Mock data / fixtures: N/A — this story does not add executable ledger behavior; existing fixture requirements are covered by publisher and CLI stories.

**Depends on:** WO-016

### [P1] Store run artifacts metadata

Implement a RunArtifactStore for Internal synthetic outputs and one-year audit retention metadata so CLI runs produce reviewable operational evidence without a production storage platform. The change belongs in modern_bank/artifacts.py and should integrate with modern_bank/cli.py after audit events are available. The current repository has only bank.cob and README.md, so generated ledgers, summaries, audit JSONL files, and run metadata have no structured local home. Stakeholders need artifact metadata to understand what was generated, how it is classified, and how long evidence should be retained for prototype governance review. When the story is done, a run workspace will contain a metadata JSON document that references generated accounts.dat output, summary output, and audit JSONL using sanitized artifact names and Internal data classification. The metadata must include retention_until or retention_days indicating at least one year of retention for audit evidence and generated outputs. This story does not implement automated purge enforcement, cloud object storage, artifact signing, parity comparison, benchmark reporting, or a web download endpoint. It depends on audit JSONL event generation and CLI run orchestration so artifacts can share a consistent run_id and lifecycle. The implementation must avoid recording absolute host paths and must not imply production compliance certification. This makes the prototype more operable by giving SRE and QA reviewers deterministic files to inspect after a batch run.

| Field | Value |
|---|---|
| Story Points | 3 |
| Hours | 30h |
| Priority | P1 |
| Labels | epic:EPIC-003, component:artifacts, governance, operability, complexity:medium |

**Acceptance Criteria**
- Running python -m pytest tests/test_artifacts.py::test_run_artifact_store_writes_metadata_json exits with code 0 and asserts RunArtifactStore.write_metadata in modern_bank/artifacts.py creates a run_metadata.json file.
- Running python -m pytest tests/test_artifacts.py::test_metadata_contains_internal_classification_and_retention exits with code 0 and asserts modern_bank/artifacts.py writes data_classification=Internal and retention_days greater than or equal to 365 in run_metadata.json.
- Running python -m pytest tests/test_cli_artifact_integration.py::test_cli_load_records_ledger_summary_and_audit_artifacts exits with code 0 and asserts modern_bank/cli.py records generated accounts.dat, summary output, and audit.jsonl entries in run_metadata.json.
- System integration test: running python -m pytest tests/test_cli_artifact_integration.py::test_artifact_metadata_uses_sanitized_relative_names exits with code 0 and asserts run_metadata.json contains artifact names without absolute host paths.
- Mock data / fixtures: file inspection confirms tests/fixtures/artifacts/basic/accounts.dat and tests/fixtures/artifacts/basic/operations.dat are committed for artifact-store integration tests.
- Unit tests: tests/test_artifacts.py contains assertions for RunArtifactStore metadata schema fields including run_id, created_at, artifacts, data_classification, retention_days, and retention_until.

**Depends on:** WO-017

---

## Golden-File Parity and Benchmark Evidence

### [P0] Test Fixed-Width Record Parsing

Add pytest unit coverage for the modern fixed-width account and operation record parser so modernization engineers can prove the Python record contract preserves the legacy ledger interface before broader parity runs. The tests belong beside the planned modern record contract module at modern_bank/records.py, with developer-facing run instructions added to README.md in this repository. The current COBOL baseline in bank.cob parses account IDs from bank-row positions 1 through 8, balances from positions 10 through 21, operation kind from ops-row position 1, source ID from positions 3 through 10, destination ID from positions 12 through 19, and amount text from positions 21 through 32. Stakeholders need this parser-level evidence because a single offset drift can create byte-identical-looking but financially incorrect fixture results later in the parity pipeline. When this story is complete, a developer can run a targeted pytest command and see assertions for exact field widths, delimiter placement, integer-cent conversion, malformed row rejection, and serialization round trips. The scope is limited to unit tests around record parsing and formatting; it does not create the full golden fixture catalog, execute COBOL side by side, or benchmark runtime. This depends on the modern record contract capability already existing with public parsing and serialization APIs for accounts.dat and operations.dat. The implementation must keep bank.cob as the behavioral reference and must not modify legacy COBOL behavior while adding these tests.

| Field | Value |
|---|---|
| Story Points | 3 |
| Hours | 30h |
| Priority | P0 |
| Labels | epic:golden-file-parity, type:test, complexity:medium, runtime:python, contract:fixed-width |

**Acceptance Criteria**
- Unit tests: running python -m pytest tests/test_records.py -q exits with status 0 and includes assertions in tests/test_records.py for accounts.dat rows formatted as IIIIIIII|BBBBBBBBBBBB.
- Unit tests: tests/test_records.py contains test functions that verify modern_bank/records.py extracts operation kind from row[0], source account from row[2:10], destination account from row[11:19], and amount from row[20:32] for operations.dat.
- Unit tests: tests/test_records.py asserts malformed account rows with a missing pipe at character position 9 and malformed operation rows with non-numeric 12-character amount text are rejected by modern_bank/records.py without floating-point conversion.
- System integration tests: N/A — this story only validates the parser module boundary in modern_bank/records.py; side-by-side COBOL and modern execution is covered by the parity runner story.
- Mock data and fixtures: tests/test_records.py commits inline representative rows such as 00000001|000000001250 and D|00000001|00000000|000000000500 so the parser tests run without external files.
- File inspection: README.md includes a command line mentioning python -m pytest tests/test_records.py -q and identifies bank.cob as the fixed-width offset reference.

**Depends on:** WO-003

### [P0] Commit Golden Parity Fixture Catalog

Create committed golden fixture inputs for the 13 required parity categories so QA and platform automation can validate behavior drift using repeatable synthetic data instead of one-off local files. The fixture catalog should live under tests/fixtures with README.md updated to describe how the categories map back to the legacy logic in bank.cob. The current repository only documents accounts.dat and operations.dat shapes in README.md and bank.cob comments, but it does not include any committed sample ledgers, operation feeds, expected outputs, or fixture inventory. This matters to stakeholders because missing fixture categories block sign-off even when existing tests happen to pass, and parity evidence must become an executable specification of the fixed-width ledger contract. When this story is complete, every required category has an accounts.dat and operations.dat input, plus expected summary metadata or expected final accounts output where the fixture design can state it unambiguously. The scope is limited to deterministic synthetic fixture data and inventory validation; it does not implement side-by-side execution, byte comparison tests, or benchmark timing. This depends on the modern record contract and core batch behavior being available so fixture expectations can align with the Python implementation while still treating COBOL as the final oracle. The fixture data must remain synthetic, avoid real customer records, and preserve exactly the fixed-width formats used by bank.cob.

| Field | Value |
|---|---|
| Story Points | 5 |
| Hours | 50h |
| Priority | P0 |
| Labels | epic:golden-file-parity, type:fixture, complexity:medium, data:synthetic, contract:fixed-width |

**Acceptance Criteria**
- Mock data and fixtures: tests/fixtures/golden contains 13 category directories named valid_deposit, valid_withdrawal, valid_transfer, malformed_row, insufficient_funds, missing_source, missing_destination, self_transfer, invalid_type, non_numeric_amount, zero_amount, fixed_width_formatting, and final_totals.
- Mock data and fixtures: each tests/fixtures/golden/* directory contains accounts.dat and operations.dat files whose account rows match the IIIIIIII|BBBBBBBBBBBB shape and whose operation rows intentionally represent the named category.
- Mock data and fixtures: tests/fixtures/golden/manifest.json lists all 13 category IDs and includes expected_summary fields named processed, rejected, and total_cents for each category.
- Unit tests: running python -m pytest tests/test_fixture_inventory.py -q exits with status 0 and validates that tests/fixtures/golden/manifest.json references only directories that contain accounts.dat and operations.dat.
- System integration tests: N/A — this story creates fixture inputs and inventory checks only; executing COBOL and modern runners against the fixtures is covered by the side-by-side runner story.
- File inspection: README.md includes a fixture catalog section naming tests/fixtures/golden and all 13 required parity categories.

**Depends on:** WO-002, WO-005

### [P0] Build Side-by-Side Parity Runner

Implement a side-by-side parity runner that executes the COBOL baseline and modern Python batch against the same fixture workspace so approval evidence can be generated reproducibly. The orchestration should be implemented in tests/parity_runner.py, with legacy execution delegated to scripts/run_legacy.sh and modern execution delegated to scripts/run_modern.py, while README.md documents the operational command sequence. The current legacy behavior in bank.cob requires accounts.dat and operations.dat in the process working directory, rewrites accounts.dat, and prints PROCESSED, REJECTED, and TOTAL_CENTS to stdout, but the repository has no scripts or runner to isolate those mutations. This story matters because parity cannot be trusted if legacy and modern runs share a mutable directory, reuse stale accounts.tmp, or capture different inputs. When complete, a developer can invoke the parity runner for one fixture category and receive separate legacy and modern output directories containing final accounts.dat, stdout capture, stderr capture, exit code metadata, and a copy of the exact input files. The scope is orchestration and artifact capture only; strict byte comparison assertions and benchmark measurement are handled by later stories. This depends on a runnable modern batch capability, a COBOL baseline execution path, and the committed golden fixture catalog. The runner must avoid unsafe shell interpolation and must treat fixture IDs or paths as allow-listed local artifacts rather than arbitrary operator-controlled commands.

| Field | Value |
|---|---|
| Story Points | 5 |
| Hours | 50h |
| Priority | P0 |
| Labels | epic:golden-file-parity, type:integration, complexity:medium, operability:artifact-capture, security:subprocess-safety |

**Acceptance Criteria**
- System integration tests: running python -m pytest tests/test_parity_runner.py -q exits with status 0 and verifies tests/parity_runner.py creates isolated legacy and modern work directories for a fixture under tests/fixtures/golden.
- System integration tests: executing python tests/parity_runner.py --fixture tests/fixtures/golden/valid_deposit --out .tmp/parity/valid_deposit creates .tmp/parity/valid_deposit/legacy/accounts.dat and .tmp/parity/valid_deposit/modern/accounts.dat when both runners are available.
- System integration tests: .tmp/parity/valid_deposit/legacy/stdout.txt and .tmp/parity/valid_deposit/modern/stdout.txt contain captured stdout with PROCESSED=, REJECTED=, and TOTAL_CENTS= lines or the runner records a nonzero exit_code in run.json for the failing side.
- Unit tests: tests/test_parity_runner.py covers summary parsing in tests/parity_runner.py for PROCESSED=00000001, REJECTED=00000000, and TOTAL_CENTS=0000000000012500.
- Mock data and fixtures: tests/test_parity_runner.py uses a temporary copy of tests/fixtures/golden/valid_deposit/accounts.dat and operations.dat so orchestration tests do not depend on external files.
- File inspection: scripts/run_legacy.sh and scripts/run_modern.py exist, and tests/parity_runner.py invokes them with subprocess argument arrays rather than concatenated shell command strings.

**Depends on:** WO-002, WO-016, WO-009

### [P0] Gate Parity With Byte Comparisons

Implement strict parity tests that compare legacy and modern final ledger bytes and summary counters so modernization approval is blocked on any observable behavior drift. The test module should be tests/test_parity.py and it should use tests/parity_runner.py to execute each committed golden fixture against bank.cob and the modern Python batch. The current COBOL baseline in bank.cob prints PROCESSED, REJECTED, and TOTAL_CENTS after mutating accounts.dat, but the repository has no automated test that compares those outputs with the modern path. Stakeholders recognize this as the primary release gate because a numerically plausible ledger is not enough if field widths, byte ordering, or rejection counts differ from the baseline. When this story is complete, running the parity pytest module iterates the fixture catalog, creates side-by-side artifacts, and fails with a diagnostic that identifies whether accounts.dat bytes, processed count, rejected count, or total cents diverged. The scope does not include creating the fixture catalog, writing the side-by-side runner, or measuring performance; it consumes those capabilities. This depends on reproducible legacy and modern execution and on committed golden fixtures covering the required categories. The test output must retain enough artifact references for operational debugging while avoiding absolute host paths in failure messages.

| Field | Value |
|---|---|
| Story Points | 3 |
| Hours | 30h |
| Priority | P0 |
| Labels | epic:golden-file-parity, type:parity-gate, complexity:medium, quality:blocking, operability:evidence |

**Acceptance Criteria**
- System integration tests: running python -m pytest tests/test_parity.py -q iterates every category listed in tests/fixtures/golden/manifest.json and invokes tests/parity_runner.py for each fixture.
- System integration tests: tests/test_parity.py asserts legacy final accounts.dat bytes equal modern final accounts.dat bytes by comparing binary reads from the legacy/accounts.dat and modern/accounts.dat artifacts.
- System integration tests: tests/test_parity.py asserts parsed PROCESSED, REJECTED, and TOTAL_CENTS values from legacy/stdout.txt equal the corresponding values from modern/stdout.txt for every fixture.
- Unit tests: tests/test_parity.py or tests/test_parity_runner.py includes direct tests for the summary parser using stdout lines PROCESSED=00000002, REJECTED=00000001, and TOTAL_CENTS=0000000000001500.
- Mock data and fixtures: tests/test_parity.py uses tests/fixtures/golden/manifest.json and the committed tests/fixtures/golden/*/accounts.dat and operations.dat files, with no external test data dependencies.
- File inspection: README.md documents python -m pytest tests/test_parity.py -q as the approval gate for accounts.dat bytes, PROCESSED, REJECTED, and TOTAL_CENTS.

**Depends on:** WO-019

### [P1] Add Required Benchmark Timing Harness

Implement a benchmark timing harness for the required 1200 accounts by 400 operations and 5000 accounts by 500 operations fixture sizes so performance evidence is repeatable after parity is established. The harness should be implemented in benchmarks/runner.py, with README.md documenting the benchmark command and artifact location. The current bank.cob source explicitly documents the O(m x n) scan and rewrite bottleneck, but the repository has no benchmark runner, benchmark fixture generator, or timing artifact format. This matters because stakeholders need raw timing evidence for the legacy and modern paths before accepting claims that indexed lookups and one final write reduce file-system work. When complete, a developer can run a single command that generates or validates deterministic benchmark fixtures, executes both implementations through the parity runner path, records elapsed milliseconds, and writes a machine-readable benchmark result. The scope is timing measurement and artifact generation only; it does not format stakeholder-facing speedup labels or independently certify benchmark results. This depends on the side-by-side runner capability and should treat parity status as a prerequisite signal in the benchmark output. The harness must be automation-friendly, avoid uncontrolled shell execution, and record enough metadata for SRE-style reproducibility without implying production banking readiness.

| Field | Value |
|---|---|
| Story Points | 5 |
| Hours | 50h |
| Priority | P1 |
| Labels | epic:golden-file-parity, type:benchmark, complexity:medium, operability:timing, evidence:performance |

**Acceptance Criteria**
- System integration tests: running python benchmarks/runner.py --sizes 1200x400 5000x500 --out .tmp/benchmarks/results.json creates .tmp/benchmarks/results.json with entries for 1200x400 and 5000x500.
- System integration tests: .tmp/benchmarks/results.json contains legacy_duration_ms, modern_duration_ms, parity_status, accounts_count, operations_count, and command fields for each benchmark size.
- Unit tests: running python -m pytest tests/test_benchmark_runner.py -q exits with status 0 and verifies benchmarks/runner.py duration calculations use time.perf_counter_ns or an equivalent monotonic timer.
- Mock data and fixtures: benchmarks/runner.py creates or uses deterministic local benchmark inputs for exactly 1200 accounts by 400 operations and 5000 accounts by 500 operations without requiring external data downloads.
- System integration tests: benchmarks/runner.py calls tests/parity_runner.py or its Python helpers rather than duplicating legacy and modern execution logic.
- File inspection: README.md documents the command python benchmarks/runner.py --sizes 1200x400 5000x500 --out .tmp/benchmarks/results.json and states that benchmark inputs are synthetic prototype artifacts.

**Depends on:** WO-019

### [P1] Publish Qualified Benchmark Speedup Report

Implement benchmark report generation that presents measured timing results and qualifies the preliminary 28.6x and 128.1x prototype speedups with the required governance-safe language. The reporting code should live in benchmarks/report.py, with README.md documenting how to convert benchmarks/runner.py JSON output into a human-readable report. The current repository has only the short README.md and bank.cob comments, so there is no controlled place to present benchmark evidence or prevent overstated performance claims. This matters because stakeholders want performance evidence, but the project must not imply independent validation, production readiness, or use with real banking records. When this story is complete, a developer can feed the benchmark results JSON into the report command and receive a Markdown or JSON report that includes raw timings, computed speedups, parity status, fixture sizes, and exact qualification text for the local prototype values. The scope is report formatting and labeling only; it does not rerun benchmarks, implement the timing harness, or change parity checks. This depends on the benchmark runner emitting a stable results.json artifact for the required sizes. The report must be automation-friendly for CI artifact publishing while preserving the synthetic offline prototype boundary.

| Field | Value |
|---|---|
| Story Points | 2 |
| Hours | 20h |
| Priority | P1 |
| Labels | epic:golden-file-parity, type:reporting, complexity:low, governance:benchmark-labeling, evidence:performance |

**Acceptance Criteria**
- Unit tests: running python -m pytest tests/test_benchmark_report.py -q exits with status 0 and verifies benchmarks/report.py computes speedup from legacy_duration_ms and modern_duration_ms fields.
- System integration tests: running python benchmarks/report.py --input .tmp/benchmarks/results.json --output .tmp/benchmarks/report.md creates .tmp/benchmarks/report.md when .tmp/benchmarks/results.json contains 1200x400 and 5000x500 entries.
- System integration tests: .tmp/benchmarks/report.md contains the exact sentence Local prototype result on one host, pending independent review. beside both 28.6x at 1200x400 and 128.1x at 5000x500 when preliminary prototype labels are included.
- System integration tests: benchmarks/report.py includes raw legacy_duration_ms, modern_duration_ms, parity_status, accounts_count, and operations_count values from the input results JSON in the generated report.
- Mock data and fixtures: tests/test_benchmark_report.py commits a sample benchmark results fixture or inline JSON containing 1200x400 and 5000x500 entries so report tests require no benchmark execution.
- File inspection: README.md documents python benchmarks/report.py --input .tmp/benchmarks/results.json --output .tmp/benchmarks/report.md and states that preliminary speedup values are not independently validated benchmarks.

**Depends on:** WO-023

---

## Local Prototype API and Dashboard Visibility

### [P2] Scaffold Vite React Tailwind dashboard

Add a minimal Vite React Tailwind frontend scaffold so demo operators have a local dashboard foundation for reviewing synthetic batch evidence. This work belongs in web/package.json and supporting new files under web/, while README.md should document how to start the local dashboard. The current repository has no web directory, package manifest, build tool, or frontend entry point, so this story creates the operator UI substrate without implementing the full run-status dashboard content. Stakeholders need the scaffold because the one-day prototype requires a lightweight local web UI, but it must remain separate from the COBOL batch and not imply a production banking portal. When complete, npm install and npm run dev from web should start a Vite React app, and npm run build should produce a static production bundle for local review. The story does not implement API data fetching, parity rendering, audit event rendering, or accessibility refinements beyond a basic scaffold. It depends on the repository modernization foundation being ready for additive frontend files. The observable result is a committed frontend package with pinned scripts, Tailwind styling entry point, React mounting code, and a placeholder synthetic prototype page.

| Field | Value |
|---|---|
| Story Points | 3 |
| Hours | 30h |
| Priority | P2 |
| Labels | epic:local-prototype-api-dashboard, frontend, vite, react, tailwind, complexity:medium |

**Acceptance Criteria**
- File inspection of web/package.json shows scripts for dev, build, preview, and test or lint, with dependencies for React, Vite, and Tailwind CSS appropriate for the lightweight local dashboard.
- File inspection of web/src/App.jsx shows a React component rendering a visible synthetic prototype placeholder and no production banking claims.
- Running cd web && npm install && npm run build exits with code 0 and creates a Vite build output directory such as web/dist/.
- Running cd web && npm run dev -- --host 127.0.0.1 is documented in README.md as the localhost-only dashboard startup command.
- Unit test coverage is addressed by a committed web test setup or N/A — if no frontend test runner is added in this scaffold, README.md must state that UI behavior tests are added with the dashboard implementation story.
- System integration tests are N/A — this scaffold does not call the API yet, and API-to-dashboard integration is implemented when web/src/App.jsx renders run evidence.
- Mock data and fixtures are N/A — this scaffold renders a static placeholder and does not consume API or fixture data yet.

**Depends on:** WO-001

### [P1] Create localhost batch API endpoints

Create a FastAPI localhost API with fixture listing and run creation endpoints so demo operators can start synthetic batch evidence runs without invoking the COBOL baseline or Python CLI by hand. This work belongs in the new ModernBank API module at modern_bank/api.py, with README.md updated to document the local-only operator command and endpoint purpose. The current repository has bank.cob and README.md only, so the target state is an additive Python API layer that does not change the legacy COBOL program or the fixed-width ledger contract. Stakeholders should be able to call GET /api/v1/fixtures and receive synthetic fixture metadata, then call POST /api/v1/runs with a fixture identifier and mode to receive a run identifier, status, summary counters, parity state, duration fields, and artifact references produced by the completed batch services. The API must be explicit that it is a prototype orchestration surface, not a banking transaction API, and it must not expose account onboarding, payment authorization, identity integration, or real customer data handling. The story does not include the dashboard implementation, structured error sanitization beyond basic HTTP validation, or the final allow-list enforcement hardening that is handled separately. It depends on the completed modern batch engine, fixture catalog capability, run orchestration capability, audit artifact writer, and parity or benchmark result contracts. When complete, the observable behavior is that a developer can run the API locally, inspect the OpenAPI route list, and exercise both endpoints with committed synthetic fixture data using automated tests.

| Field | Value |
|---|---|
| Story Points | 5 |
| Hours | 50h |
| Priority | P1 |
| Labels | epic:local-prototype-api-dashboard, backend, fastapi, prototype, complexity:medium |

**Acceptance Criteria**
- File inspection of modern_bank/api.py shows a FastAPI app object and route handlers registered for GET /api/v1/fixtures and POST /api/v1/runs with Pydantic request and response models for fixture_id, mode, run_id, status, processed_count, rejected_count, total_cents, duration_ms, parity_status, artifact_refs, and audit_events.
- Running python -m pytest tests/test_api.py::test_get_fixtures_returns_catalog exits with code 0 and asserts that GET /api/v1/fixtures returns HTTP 200 with a JSON array containing at least one object with id, label, account_count, operation_count, and synthetic_prototype fields.
- Running python -m pytest tests/test_api.py::test_post_runs_starts_fixture_run exits with code 0 and asserts that POST /api/v1/runs with application/json body containing fixture_id and mode returns HTTP 202 or HTTP 200 with run_id, status, processed_count, rejected_count, total_cents, parity_status, and duration_ms fields.
- System integration test tests/test_api.py::test_api_uses_run_service_boundary uses FastAPI TestClient against modern_bank.api:app and verifies POST /api/v1/runs calls the configured run orchestration boundary rather than executing bank.cob directly from modern_bank/api.py.
- Mock data and fixtures are committed under tests/fixtures/api/ or the completed fixture catalog path, and the test suite can run GET /api/v1/fixtures and POST /api/v1/runs without accessing real bank records, production paths, or network services.
- README.md contains a localhost-only startup example using 127.0.0.1 and documents GET /api/v1/fixtures and POST /api/v1/runs as synthetic prototype endpoints, while bank.cob remains unchanged by git diff.
- N/A — database migrations do not apply because the repository has no database objects and this API persists run evidence through local prototype artifacts supplied by the completed run service.

**Depends on:** WO-005, WO-017, WO-019

### [P1] Return safe structured API errors

Add a structured API error module so local demo users receive actionable JSON failures without stack traces, secrets, or host filesystem paths. This work belongs in the new ModernBank API errors module at modern_bank/api_errors.py and must be wired into the existing FastAPI app in modern_bank/api.py. The current API layer is expected to expose fixture and run endpoints, but without a dedicated sanitizer any raised exception could leak implementation details from the local workspace. Stakeholders need safe errors because failed fixture selection, malformed JSON, unknown runs, and internal batch failures are expected during demos and should be diagnosable without exposing host details. When the story is complete, invalid requests return stable JSON fields such as errorCode, message, correlationId, and statusCode with appropriate HTTP status codes. The story does not add new API business endpoints, dashboard screens, authentication, or production observability infrastructure. It depends on the local FastAPI endpoint capability already existing and on completed run services surfacing typed domain errors or catchable exceptions. The implementation should make failures operationally useful for local triage while keeping the blast radius of unexpected exceptions contained.

| Field | Value |
|---|---|
| Story Points | 3 |
| Hours | 30h |
| Priority | P1 |
| Labels | epic:local-prototype-api-dashboard, backend, security, error-handling, complexity:medium |

**Acceptance Criteria**
- File inspection of modern_bank/api_errors.py shows an ApiError model or equivalent typed structure with errorCode, message, correlationId, and statusCode fields and no field intended to return traceback, stack, cwd, hostname, or absolute_path.
- File inspection of modern_bank/api.py shows the FastAPI app registers exception handlers from modern_bank/api_errors.py for request validation errors, known API errors, and uncaught exceptions.
- Running python -m pytest tests/test_api_errors.py::test_validation_error_shape exits with code 0 and asserts POST /api/v1/runs with missing fixture_id returns HTTP 400 or 422 with JSON keys errorCode, message, correlationId, and statusCode.
- Running python -m pytest tests/test_api_errors.py::test_internal_error_sanitizes_host_paths exits with code 0 and asserts an injected exception containing an absolute path such as /tmp/private/accounts.dat is returned as HTTP 500 without /tmp, accounts.dat absolute path context, Traceback, or File in the response body.
- System integration test tests/test_api_errors.py::test_unknown_route_returns_safe_json calls GET /api/v1/not-found and asserts HTTP 404 with application/json content type and an errorCode field.
- Mock data and fixtures are committed in tests/fixtures/api_errors/ or implemented through a deterministic failing fake run service so safe-error tests execute without external services or production files.
- N/A — database migrations do not apply because error handling is implemented in FastAPI middleware and exception handlers, not a database layer.

**Depends on:** WO-024

### [P1] Enforce allow-listed fixture identifiers

Enforce FixtureCatalog allow-listed fixture identifiers in the API so operators can select only committed synthetic inputs and cannot submit raw filesystem paths. This work belongs in modern_bank/api.py, integrating the completed fixture catalog capability that resolves fixture IDs to approved account and operation files. The legacy bank.cob program trusts accounts.dat and operations.dat in the current working directory, so the API must add a safer boundary around demo fixture selection without changing the COBOL baseline. Stakeholders need this control to prevent accidental use of real records, path traversal, or arbitrary local file access during prototype demos. When complete, POST /api/v1/runs accepts a fixture_id from the catalog and rejects path-like, unknown, or malformed fixture identifiers before any run workspace is created. The story does not create new fixture categories, implement the run engine, or change dashboard rendering. It depends on a completed fixture catalog that owns synthetic fixture metadata and on the local FastAPI run endpoint already existing. The observable result is that developers can run targeted API tests proving allowed fixture IDs are accepted and path input is rejected with safe structured JSON.

| Field | Value |
|---|---|
| Story Points | 3 |
| Hours | 30h |
| Priority | P1 |
| Labels | epic:local-prototype-api-dashboard, backend, security, input-validation, complexity:medium |

**Acceptance Criteria**
- File inspection of modern_bank/api.py shows POST /api/v1/runs request models contain fixture_id and mode fields and do not contain path, file_path, accounts_path, operations_path, directory, or cwd request fields.
- File inspection of modern_bank/api.py shows fixture validation calls a FixtureCatalog capability or dependency before run service execution and passes only the resolved catalog fixture object or fixture ID to the run service.
- Running python -m pytest tests/test_fixture_allowlist_api.py::test_allowed_fixture_id_starts_run exits with code 0 and asserts POST /api/v1/runs using a catalog fixture ID returns HTTP 200 or HTTP 202 with the same fixture_id in the JSON body.
- Running python -m pytest tests/test_fixture_allowlist_api.py::test_raw_path_fixture_id_rejected exits with code 0 and asserts fixture_id values such as ../accounts.dat, /tmp/accounts.dat, C:\temp\accounts.dat, and fixtures/demo/accounts.dat return HTTP 400 or HTTP 403 with errorCode FIXTURE_NOT_ALLOWED or equivalent.
- System integration test tests/test_fixture_allowlist_api.py::test_rejected_fixture_does_not_call_run_service verifies an unknown fixture_id returns a safe JSON error and the run service fake invocation count remains 0.
- Mock fixture catalog data is committed under tests/fixtures/fixture_catalog/ or provided through a deterministic in-repository fixture catalog test double containing at least one allowed synthetic fixture ID.
- N/A — database migrations do not apply because fixture allow-listing uses repository fixtures and local catalog metadata rather than tables.

**Depends on:** WO-005, WO-024

### [P2] Render batch evidence dashboard

Implement the React dashboard so demo operators can see synthetic run status, parity outcome, rejection summary, timing, and audit events in one local review surface. This work belongs in web/src/App.jsx and consumes the already available localhost API endpoints from modern_bank/api.py. The current frontend scaffold only renders a placeholder, while the legacy bank.cob output is limited to three stdout summary lines that are not enough for stakeholder visibility. Stakeholders need a readable dashboard to review whether the modern run preserved processed count, rejected count, total cents, parity evidence, and benchmark timing before approving the prototype demonstration. When complete, the page loads fixture metadata from GET /api/v1/fixtures, lets an operator start a run through POST /api/v1/runs, and renders the returned status fields and audit event list without exposing host paths. The story does not add new backend endpoints, change fixture allow-listing, implement production authentication, or certify benchmarks as independently reviewed. It depends on the local API endpoints, structured safe errors, allow-listed fixture selection, completed run evidence contract, and the frontend scaffold. The observable result is that a developer can run the API and Vite app locally, start a synthetic fixture run, and verify dashboard text for status, parity, rejection counts, duration, and audit entries.

| Field | Value |
|---|---|
| Story Points | 8 |
| Hours | 80h |
| Priority | P2 |
| Labels | epic:local-prototype-api-dashboard, frontend, dashboard, observability, complexity:high |

**Acceptance Criteria**
- File inspection of web/src/App.jsx shows fetch calls or an equivalent API client for GET /api/v1/fixtures and POST /api/v1/runs, with no request field named path, accounts_path, operations_path, or directory.
- Running cd web && npm run build exits with code 0 and verifies web/src/App.jsx compiles after rendering fixture selection, run status, processed_count, rejected_count, total_cents, parity_status, duration_ms, rejection_summary, and audit_events fields.
- Frontend unit test web/src/App.test.jsx::renders_run_evidence or equivalent exits with code 0 and asserts the dashboard displays status, parity, processed count, rejected count, total cents, duration, and at least one audit event from mocked API responses.
- System integration test tests/test_dashboard_api_contract.py or web contract test verifies the mock JSON used by web/src/App.jsx matches the POST /api/v1/runs response fields defined in modern_bank/api.py.
- Mock API response fixtures are committed under web/src/__fixtures__/ or tests/fixtures/dashboard/ for fixtures, successful run, failed run, parity failure, and empty audit event states.
- Manual verification command README.md includes running the API on 127.0.0.1 and the Vite dashboard on 127.0.0.1, then selecting a synthetic fixture and confirming visible fields for parity_status, rejected_count, duration_ms, and audit_events.
- The dashboard error state renders the structured API error message and correlationId returned by modern_bank/api_errors.py without displaying Traceback, absolute paths, or raw exception text.

**Depends on:** WO-026, WO-027, WO-028, WO-004

### [P2] Add prototype labels and focus states

Add explicit synthetic prototype labels and WCAG-conscious keyboard focus states so the local dashboard is safe to present and usable without a mouse. This work belongs in web/src/App.jsx, with supporting style updates in the existing web Tailwind entry file created by the scaffold. The current dashboard renders run evidence, but it needs final governance and accessibility refinements to avoid implying production banking operation and to support keyboard-only review. Stakeholders need this because the prototype handles banking-style synthetic data and must be visually clear that it is educational evidence, not a production bank portal. When complete, every major dashboard region includes synthetic prototype wording, interactive controls have visible focus indicators, and keyboard users can navigate fixture selection, run action, error details, and audit events in a predictable order. The story does not add new run metrics, new API calls, authentication, or full internationalization. It depends on the completed dashboard rendering run status, parity, rejection summary, timing, and audit events. The observable result is that automated tests and file inspection verify labels, accessible names, and focus class names on the controls used during the local demo.

| Field | Value |
|---|---|
| Story Points | 3 |
| Hours | 30h |
| Priority | P2 |
| Labels | epic:local-prototype-api-dashboard, frontend, accessibility, governance, complexity:medium |

**Acceptance Criteria**
- File inspection of web/src/App.jsx shows the exact visible phrase Synthetic prototype or equivalent on the page header, run evidence region, artifact or audit region, and any benchmark timing region rendered by the dashboard.
- File inspection of web/src/App.jsx shows form controls for fixture selection and run start have associated label elements or aria-label attributes with accessible names referencing fixture selection and starting a synthetic run.
- Running cd web && npm run build exits with code 0 after the label and focus-state changes.
- Frontend unit or accessibility test web/src/App.test.jsx::renders_synthetic_prototype_labels exits with code 0 and asserts the header, run summary, parity area, and audit events area include synthetic prototype wording.
- Frontend accessibility test web/src/App.test.jsx::keyboard_controls_have_focus_classes or equivalent exits with code 0 and asserts buttons, selects, links, and error detail controls include visible focus styles such as focus-visible:outline, focus-visible:ring, or equivalent Tailwind classes.
- System integration tests are N/A — this story changes browser rendering and accessibility states only; API boundary behavior remains covered by dashboard and API tests.
- Mock data and fixtures are addressed by reusing committed dashboard mock responses under web/src/__fixtures__/ or tests/fixtures/dashboard/, with no new backend fixture generation required.

**Depends on:** WO-030

---

## Forge Shipping Pipeline Packaging and Rollout Gates

### [P1] Create Forge build and scan pipeline

Add a Forge Shipping pipeline configuration so the modernization prototype has repeatable Python build, Docker build, secret-scan, and dependency-scan automation before evidence is promoted for stakeholder review. The change belongs beside the legacy batch baseline in .forge/shipping.yml, with README.md updated only enough to point operators from the existing BBS SG Bank overview to the new shipping entry point. Today the repository contains only bank.cob and README.md, so every build and scan action is manual, unaudited, and easy to skip during the one-day prototype. Stakeholders need a reliable pipeline because parity and benchmark evidence is only credible if it is generated after a known build and clean scan posture. When this story is complete, a developer can inspect .forge/shipping.yml and see named build:python, build:docker, secret-scan, and dependency-scan steps with deterministic commands and no production deployment step. The pipeline should treat bank.cob as the retained COBOL baseline and should invoke the Python modernization assets created by earlier work without altering the legacy fixed-width file contract. This story does not add parity gating, benchmark capture, artifact packaging, rollout approval, or changes to COBOL transaction semantics. It depends on an existing modern Python batch build surface, a Docker build definition, and dependency metadata being available from earlier modernization work. It must keep the execution model local, offline, and synthetic-only so a failed scan blocks release evidence without implying any live banking deployment. The implementation should favor explicit step names and log-safe commands so SREs can quickly identify whether a failure came from build, container packaging, secret detection, or dependency analysis.

| Field | Value |
|---|---|
| Story Points | 3 |
| Hours | 30h |
| Priority | P1 |
| Labels | platform, ci-cd, security-scan, forge-shipping, complexity:medium |

**Acceptance Criteria**
- File inspection of .forge/shipping.yml shows four top-level or named pipeline steps containing the exact identifiers build:python, build:docker, secret-scan, and dependency-scan.
- Running forge shipping validate .forge/shipping.yml exits with status code 0 and reports no YAML schema error for the .forge/shipping.yml pipeline definition.
- The .forge/shipping.yml build:python step contains a command that invokes the Python build or test entry point, including python -m pytest or an equivalent project test command, and does not modify bank.cob.
- The .forge/shipping.yml build:docker step contains a docker build command or Forge Docker build integration that references the repository Docker build context and does not define any deploy or production traffic step.
- The .forge/shipping.yml secret-scan step is configured to scan the repository contents and excludes generated run artifacts by path only if those paths are explicitly named in .forge/shipping.yml.
- The .forge/shipping.yml dependency-scan step is configured to analyze Python dependency metadata and fail the pipeline on critical findings rather than only emitting an informational log.
- Unit tests: N/A — .forge/shipping.yml is declarative pipeline configuration, and there is no new application function in bank.cob or README.md to unit test for this story.
- System integration tests: running forge shipping run --dry-run .forge/shipping.yml or the repository-supported Forge dry-run command completes the build and scan graph without executing any production deployment endpoint.
- Mock data/fixtures: N/A — this story introduces build and scan automation only; fixture generation is owned by the parity and benchmark capabilities referenced by later gates.

**Depends on:** WO-001, WO-002, WO-016

### [P1] Gate releases on P0 parity

Add a Forge Shipping parity gate that blocks release evidence unless tests/test_parity.py reports a full P0 fixture pass, because behavioral drift in ledger bytes or summary counters invalidates the modernization prototype. The change is made in .forge/shipping.yml and must reference the parity test module tests/test_parity.py that exercises the bank.cob baseline against the modern Python engine. The current shipping configuration only builds and scans once the base pipeline exists, so it cannot yet stop promotion when deposits, withdrawals, transfers, malformed rows, or rejection cases diverge from the COBOL behavior. Stakeholders recognize this as the hard sign-off control that keeps performance improvements from masking incorrect balances. When complete, a pipeline run should execute the parity test command after successful build and scan steps, publish the parity result as a gate decision, and stop later evidence or packaging steps on any P0 failure. The observable behavior is that changing a golden expected final accounts.dat or summary count causes the parity gate to return a non-zero status before any rollout sign-off can proceed. This story does not create the parity fixture categories, rewrite the COBOL baseline, implement the Python engine, or add benchmark reporting. It depends on a working golden-file parity harness, shared fixtures, and a modern batch implementation that can run side by side with legacy-bank. The gate must compare what stakeholders care about: byte-identical final ledger output, processed count, rejected count, and total cents for required P0 fixtures. The implementation should keep logs diagnostic but safe, retaining diff artifact paths without exposing host-specific absolute paths or pretending the prototype is a production banking release.

| Field | Value |
|---|---|
| Story Points | 3 |
| Hours | 30h |
| Priority | P1 |
| Labels | platform, ci-cd, parity-gate, quality-gate, complexity:medium |

**Acceptance Criteria**
- The .forge/shipping.yml file contains a parity gate step after build:python and build:docker that invokes python -m pytest tests/test_parity.py or the established parity test command.
- Running python -m pytest tests/test_parity.py -q exits with status code 0 on the committed P0 fixture set and reports no failed assertion for final accounts.dat byte comparison.
- The parity gate command in .forge/shipping.yml fails with a non-zero status when tests/test_parity.py has an assertion failure for PROCESSED, REJECTED, or TOTAL_CENTS summary comparison.
- File inspection of tests/test_parity.py shows assertions or helper calls that compare final accounts.dat bytes, processed count, rejected count, and total cents between the COBOL baseline and modern output.
- Unit tests: N/A — this story wires an existing integration-style parity module into .forge/shipping.yml and does not add standalone application functions requiring isolated unit tests.
- System integration tests: python -m pytest tests/test_parity.py -q validates the service boundary between the bank.cob legacy baseline runner and the modern Python batch runner using shared fixture files.
- Mock data/fixtures: the committed P0 fixture inputs referenced by tests/test_parity.py are present in the repository fixture path used by that test module, including at least one fixture that exercises the accounts.dat fixed-width contract.

**Depends on:** WO-022, WO-020

### [P1] Capture benchmark reports in shipping

Add Forge Shipping benchmark artifact capture for benchmarks/runner.py reports so performance evidence is retained alongside parity evidence for operational review. The change belongs in .forge/shipping.yml and must call the benchmark runner module at benchmarks/runner.py that measures the required fixed-width ledger fixture sizes. At present, the base pipeline can build, scan, and later gate parity, but it does not persist the runtime measurements stakeholders need to evaluate whether the indexed modern batch reduced the O(m × n) file I/O bottleneck. The business value is reliable, reviewable performance evidence that shows raw timings without overstating local prototype speedups as independently validated results. When the story is complete, a shipping run should execute the benchmark command after parity succeeds and upload or retain report files from the benchmark output directory as named artifacts. The observable behavior is that reports for 1,200 accounts by 400 operations and 5,000 accounts by 500 operations are present in the configured artifact location after the benchmark stage finishes. This story does not implement the benchmark runner, generate new benchmark fixtures, change the performance threshold, or modify bank.cob transaction processing. It depends on a benchmark runner that already emits machine-readable and human-readable reports, plus a parity gate that prevents benchmark publication for behaviorally invalid runs. The benchmark capture must preserve the required caveat that preliminary 28.6x and 128.1x values are local prototype results on one host pending independent review. From a platform perspective, the step must be diagnosable by artifact name, fixture size, command, and exit code so failed performance evidence does not turn into ambiguous release risk.

| Field | Value |
|---|---|
| Story Points | 3 |
| Hours | 30h |
| Priority | P1 |
| Labels | platform, ci-cd, benchmarking, artifact-capture, complexity:medium |

**Acceptance Criteria**
- The .forge/shipping.yml file contains a benchmark artifact step that invokes python benchmarks/runner.py or the established benchmark command after the parity gate step.
- The .forge/shipping.yml benchmark step declares artifact capture paths for benchmark reports produced by benchmarks/runner.py, including a machine-readable report file path and a human-readable report file path.
- Running python benchmarks/runner.py --output artifacts/benchmarks or the repository-supported equivalent creates report files under artifacts/benchmarks for the 1200x400 and 5000x500 fixture sizes.
- File inspection of a generated benchmark report under artifacts/benchmarks shows both fixture size labels 1200x400 and 5000x500 and raw duration fields for legacy and modern runs.
- The generated benchmark report under artifacts/benchmarks contains the exact qualification phrase Local prototype result on one host, pending independent review. for preliminary speedup references.
- Unit tests: N/A — this story wires benchmark execution and artifact capture in .forge/shipping.yml; benchmark calculation tests belong to the benchmark runner capability.
- System integration tests: executing the Forge Shipping benchmark stage after a green parity gate runs benchmarks/runner.py and captures artifacts without requiring network services or database endpoints.
- Mock data/fixtures: the benchmark command referenced by .forge/shipping.yml uses committed synthetic benchmark fixtures and does not require external account or operation files outside the repository workspace.

**Depends on:** WO-026, WO-020

### [P2] Package evidence artifacts deterministically

Add scripts/package_artifacts.sh to create a deterministic archive containing fixtures, ledgers, audit JSONL, parity diffs, and benchmark reports so reviewers can download one complete modernization evidence bundle. The new script belongs at scripts/package_artifacts.sh, with README.md receiving only a minimal operator pointer if needed because README.md is the existing documentation surface in the repository. Currently the repository has no packaging script and evidence from parity, benchmark, audit, and run workspaces can remain scattered across local directories after a Forge Shipping run. Stakeholders need a single reproducible archive to support offline side-by-side sign-off, rollback review, and SRE incident-style diagnosis when a gate fails. When complete, a developer can run the script with an input artifact root and output path, then inspect the archive and find fixture inputs, final ledgers, audit JSONL files, parity diffs, benchmark reports, and a manifest. The script should preserve relative paths, avoid absolute host paths, and exclude secrets or unrelated local files from the package. This story does not create the fixtures, generate parity diffs, run benchmarks, decide sign-off, or upload the archive to a remote artifact store. It depends on stable artifact directories produced by parity and benchmark automation, plus append-only local audit evidence from the prototype runtime. The packaging workflow must be safe for shell execution by using strict mode, validating allow-listed directories, and failing closed when required evidence categories are absent. Operationally, the archive becomes the handoff artifact for rollback analysis: retain original inputs, compare outputs, discard generated modern output if needed, and rerun the COBOL baseline.

| Field | Value |
|---|---|
| Story Points | 5 |
| Hours | 50h |
| Priority | P2 |
| Labels | platform, artifact-packaging, audit-evidence, shell-script, complexity:medium |

**Acceptance Criteria**
- The scripts/package_artifacts.sh file exists, is executable, and starts with a POSIX shell or bash shebang plus strict error handling such as set -euo pipefail.
- Running scripts/package_artifacts.sh artifacts dist/evidence.tar.gz creates dist/evidence.tar.gz and a manifest file inside the archive that lists packaged fixture, ledger, audit JSONL, parity diff, and benchmark report paths.
- Archive inspection with tar -tzf dist/evidence.tar.gz shows repository-relative entries for fixtures, ledgers or accounts.dat outputs, audit .jsonl files, parity diff files, and benchmark report files.
- The scripts/package_artifacts.sh script rejects an input artifact root containing path traversal characters or an absolute output path outside the repository workspace with a non-zero exit code and an error message that references scripts/package_artifacts.sh.
- The generated archive manifest does not contain absolute host paths, secret-looking environment values, or unrelated files outside the supplied artifact root when inspected with tar -xOf dist/evidence.tar.gz manifest.txt.
- Unit tests: N/A — scripts/package_artifacts.sh is a shell packaging utility; verification is performed through command-level script tests against fixture directories rather than isolated application unit tests.
- System integration tests: running the script after python -m pytest tests/test_parity.py -q and python benchmarks/runner.py --output artifacts/benchmarks packages the resulting parity and benchmark files without modifying bank.cob.
- Mock data/fixtures: a committed or generated synthetic artifact sample directory used by the script test contains representative accounts.dat, operations.dat, audit JSONL, parity diff, and benchmark report files.

**Depends on:** WO-021, WO-025, WO-029

### [P2] Document rollout and rollback runbook

Update README.md with an operational rollout runbook covering Docker execution, parity gates, benchmark interpretation, rollback, and synthetic-only sign-off so DevOps and SRE reviewers can run the prototype without relying on tribal knowledge. The change belongs in README.md, the only existing documentation module for the bbs-sg legacy batch, and it should reference bank.cob as the retained COBOL baseline. Today README.md is only a seven-line overview, so it does not explain the Forge Shipping pipeline, the parity gate, benchmark artifact capture, the packaging script, or how to recover by discarding modern output and rerunning legacy-bank. Stakeholders need this runbook because the prototype is intentionally offline and evidence-driven, and approval must be blocked by parity failure rather than operator judgment. When complete, a developer can follow README.md from a clean checkout through Docker build, Forge Shipping validation, parity execution, benchmark capture, evidence packaging, rollback, and sign-off boundaries. The observable behavior is documentation that names the specific commands and artifacts operators should use, including .forge/shipping.yml, tests/test_parity.py, benchmarks/runner.py, and scripts/package_artifacts.sh. This story does not change pipeline behavior, implement Docker files, alter test code, generate benchmarks, or modify the COBOL batch logic. It depends on working build and scan automation, parity gating, benchmark capture, and deterministic evidence packaging being available. The runbook must explicitly state that only synthetic fixtures are allowed, preliminary speedups are local single-host prototype results pending independent review, and no production banking readiness is implied. It should be written in operational language with clear rollback triggers, expected artifacts, and failure handling so mean-time-to-recovery for a failed prototype run is a rerun from retained inputs rather than manual reconstruction.

| Field | Value |
|---|---|
| Story Points | 2 |
| Hours | 20h |
| Priority | P2 |
| Labels | documentation, runbook, rollout, rollback, complexity:low |

**Acceptance Criteria**
- README.md contains a rollout runbook section that references .forge/shipping.yml, bank.cob, tests/test_parity.py, benchmarks/runner.py, and scripts/package_artifacts.sh by path.
- README.md includes a Docker execution step that names the Docker build or run command used for the prototype and explicitly states that execution uses synthetic accounts.dat and operations.dat fixtures only.
- README.md documents that python -m pytest tests/test_parity.py -q is the P0 parity command and that any mismatch in final accounts.dat, PROCESSED, REJECTED, or TOTAL_CENTS blocks sign-off.
- README.md documents the benchmark report requirement for 1200x400 and 5000x500 fixture sizes and includes the exact phrase Local prototype result on one host, pending independent review. for preliminary speedup references.
- README.md documents rollback steps to retain original inputs, compare modern output with COBOL output, discard generated modern output, and rerun the bank.cob COBOL baseline from the retained fixture workspace.
- README.md documents the evidence packaging command using scripts/package_artifacts.sh and names the expected archive contents: fixtures, ledgers, audit JSONL, parity diffs, and benchmark reports.
- Unit tests: N/A — this is a documentation-only story that changes README.md and does not introduce executable application logic.
- System integration tests: N/A — README.md documents integration commands, while command execution is validated by the pipeline, parity, benchmark, and packaging stories.
- Mock data/fixtures: N/A — README.md references existing synthetic fixtures and does not create or modify fixture data.

**Depends on:** WO-018, WO-031