# Testing

**Selected Categories:** Functional test cases, Smoke test suite, Regression test suite, Performance test scenarios

**Total Test Cases:** 132


---

## Functional test cases (33)

### FUNCTIONAL-001 — Scaffold Python modernization package

- User Story: WO-001
- Objective: Validate functional behavior for "Scaffold Python modernization package" against acceptance criteria.
- Expected: Story "Scaffold Python modernization package" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Unit tests: running python -m pytest tests/test_project_scaffold.py from the repository root succeeds and test_project_imports_modern_bank imports modern_bank from modern_bank/__init__.py.
- Check acceptance criterion 2: System integration tests: N/A — this story creates package metadata only and does not expose a service boundary, but python -m pip install -e . must complete using pyproject.toml without requiring accounts.dat or operations.dat.
- Check acceptance criterion 3: Mock data/fixtures: N/A — no ledger parsing is implemented in this scaffold story; README.md must state that synthetic fixture files are introduced by later fixture work rather than by pyproject.toml.

### FUNCTIONAL-002 — Add reproducible COBOL baseline runner

- User Story: WO-002
- Objective: Validate functional behavior for "Add reproducible COBOL baseline runner" against acceptance criteria.
- Expected: Story "Add reproducible COBOL baseline runner" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Unit tests: N/A — scripts/run_legacy.sh is a shell wrapper around bank.cob, and verification is performed by the executable integration command documented in README.md.
- Check acceptance criterion 2: System integration tests: running docker build -t bbs-sg-legacy-baseline . uses Dockerfile and completes without modifying bank.cob.
- Check acceptance criterion 3: System integration tests: running scripts/run_legacy.sh tests/fixtures/legacy_smoke after creating tests/fixtures/legacy_smoke/accounts.dat and tests/fixtures/legacy_smoke/operations.dat exits with status 0 and stdout contains PROCESSED=, REJECTED=, and TOTAL_CENTS= from bank.cob.

### FUNCTIONAL-003 — Implement fixed-width record codec

- User Story: WO-003
- Objective: Validate functional behavior for "Implement fixed-width record codec" against acceptance criteria.
- Expected: Story "Implement fixed-width record codec" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Unit tests: running python -m pytest tests/test_records.py succeeds and includes assertions for FixedWidthCodec.parse_account_line, FixedWidthCodec.format_account_record, FixedWidthCodec.parse_operation_line, and FixedWidthCodec.format_operation_record.
- Check acceptance criterion 2: System integration tests: N/A — modern_bank/records.py is a pure contract module with no service boundary or subprocess boundary; integration with scripts/run_modern.py is covered by the later CLI story.
- Check acceptance criterion 3: Mock data/fixtures: tests/test_records.py commits representative account rows such as 00000001|000000001000 and operation rows such as D|00000001|00000000|000000000250 as test literals or fixture parameters.

### FUNCTIONAL-004 — Add fixture allow-list catalog

- User Story: WO-005
- Objective: Validate functional behavior for "Add fixture allow-list catalog" against acceptance criteria.
- Expected: Story "Add fixture allow-list catalog" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Unit tests: running python -m pytest tests/test_fixture_catalog.py succeeds and test_fixture_catalog_entries_validate_with_fixed_width_codec parses each catalog accounts.dat and operations.dat file through FixedWidthCodec.
- Check acceptance criterion 2: System integration tests: N/A — tests/fixtures/fixture_catalog.json is a local allow-list artifact and does not expose a service or subprocess boundary in this story.
- Check acceptance criterion 3: Mock data/fixtures: tests/fixtures/fixture_catalog.json and at least one committed fixture directory containing accounts.dat and operations.dat are present under tests/fixtures.

### FUNCTIONAL-005 — Add modern CLI contract skeleton

- User Story: WO-006
- Objective: Validate functional behavior for "Add modern CLI contract skeleton" against acceptance criteria.
- Expected: Story "Add modern CLI contract skeleton" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Unit tests: running python -m pytest tests/test_run_modern_cli.py succeeds and includes coverage for the main function in scripts/run_modern.py using valid and invalid fixture paths.
- Check acceptance criterion 2: System integration tests: running python scripts/run_modern.py --accounts tests/fixtures/modern_smoke/accounts.dat --operations tests/fixtures/modern_smoke/operations.dat --contract-check exits with status 0 and stdout contains CONTRACT_OK.
- Check acceptance criterion 3: Mock data/fixtures: tests/fixtures/modern_smoke/accounts.dat and tests/fixtures/modern_smoke/operations.dat are committed and are parsed by tests/test_run_modern_cli.py.

### FUNCTIONAL-006 — Build ordered ledger account index

- User Story: WO-007
- Objective: Validate functional behavior for "Build ordered ledger account index" against acceptance criteria.
- Expected: Story "Build ordered ledger account index" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Unit tests: running python -m pytest tests/test_ledger.py exits with code 0 and includes assertions that LedgerIndex.load_from_path in modern_bank/ledger.py parses tests/fixtures/ledger/basic_accounts.dat into account_ids [00000001, 00000002, 00000003] in source-file order.
- Check acceptance criterion 2: Unit tests: tests/test_ledger.py asserts LedgerIndex.get_account in modern_bank/ledger.py returns integer balance 1250 for account ID 00000001 and returns None or raises the documented lookup exception for account ID 99999999 without reading accounts.dat again.
- Check acceptance criterion 3: Unit tests: tests/test_ledger.py asserts LedgerIndex.to_rows in modern_bank/ledger.py serializes every row as exactly 21 characters before the newline using 8 account digits, one pipe at offset 9, and 12 balance digits.

### FUNCTIONAL-007 — Preflight account ledger validity

- User Story: WO-010
- Objective: Validate functional behavior for "Preflight account ledger validity" against acceptance criteria.
- Expected: Story "Preflight account ledger validity" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Unit tests: running python -m pytest tests/test_ledger_preflight.py exits with code 0 and asserts LedgerIndex.load_from_path in modern_bank/ledger.py raises DuplicateAccountError for tests/fixtures/ledger/duplicate_accounts.dat containing account ID 00000001 twice.
- Check acceptance criterion 2: Unit tests: tests/test_ledger_preflight.py asserts LedgerIndex.load_from_path in modern_bank/ledger.py raises InvalidAccountRowError for tests/fixtures/ledger/bad_balance_width.dat where the balance field is not exactly 12 digits.
- Check acceptance criterion 3: Unit tests: tests/test_ledger_preflight.py asserts LedgerIndex.load_from_path in modern_bank/ledger.py raises InvalidAccountRowError for tests/fixtures/ledger/non_numeric_balance.dat where bank-row(10:12) contains a non-numeric character.

### FUNCTIONAL-008 — Process accepted DWT mutations

- User Story: WO-011
- Objective: Validate functional behavior for "Process accepted DWT mutations" against acceptance criteria.
- Expected: Story "Process accepted DWT mutations" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Unit tests: running python -m pytest tests/test_processor_valid_ops.py exits with code 0 and asserts OperationProcessor.process_rows in modern_bank/processor.py applies D|00000001|00000000|000000000250 by increasing account 00000001 in LedgerIndex by 250 cents.
- Check acceptance criterion 2: Unit tests: tests/test_processor_valid_ops.py asserts OperationProcessor.process_rows in modern_bank/processor.py applies W|00000001|00000000|000000000100 by decreasing account 00000001 in LedgerIndex by 100 cents when funds are available.
- Check acceptance criterion 3: Unit tests: tests/test_processor_valid_ops.py asserts OperationProcessor.process_rows in modern_bank/processor.py applies T|00000001|00000002|000000000125 by subtracting 125 cents from account 00000001 and adding 125 cents to account 00000002 in the same in-memory ledger.

### FUNCTIONAL-009 — Preserve processor rejection paths

- User Story: WO-012
- Objective: Validate functional behavior for "Preserve processor rejection paths" against acceptance criteria.
- Expected: Story "Preserve processor rejection paths" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Unit tests: running python -m pytest tests/test_processor_rejections.py exits with code 0 and asserts OperationProcessor.process_rows in modern_bank/processor.py increments rejected by 1 and leaves LedgerIndex balances unchanged for unsupported operation kind X.
- Check acceptance criterion 2: Unit tests: tests/test_processor_rejections.py asserts modern_bank/processor.py rejects non-numeric amount text, zero amount text 000000000000, and operation rows shorter than 32 characters without mutating any account balance.
- Check acceptance criterion 3: Unit tests: tests/test_processor_rejections.py asserts modern_bank/processor.py rejects missing source account 99999999 for D, W, and T rows and rejects missing transfer destination account 99999998 for T rows.

### FUNCTIONAL-010 — Format fixed-width batch summary

- User Story: WO-013
- Objective: Validate functional behavior for "Format fixed-width batch summary" against acceptance criteria.
- Expected: Story "Format fixed-width batch summary" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Unit tests: running python -m pytest tests/test_summary.py exits with code 0 and asserts SummaryReporter.format_summary in modern_bank/summary.py returns PROCESSED=00000003, REJECTED=00000002, and TOTAL_CENTS=0000000000012500 for the specified test ledger and counters.
- Check acceptance criterion 2: Unit tests: tests/test_summary.py asserts SummaryReporter.calculate_total_cents in modern_bank/summary.py sums integer balances from LedgerIndex in modern_bank/ledger.py and returns an int, not a float or formatted currency string.
- Check acceptance criterion 3: Integration tests: running python -m pytest tests/test_summary_integration.py exits with code 0 and asserts OperationProcessor from modern_bank/processor.py plus SummaryReporter from modern_bank/summary.py formats the summary for tests/fixtures/operations/summary_mixed.dat exactly as tests/fixtures/expected/summary_mixed_stdout.txt.

### FUNCTIONAL-011 — Publish ledger with safe replacement

- User Story: WO-014
- Objective: Validate functional behavior for "Publish ledger with safe replacement" against acceptance criteria.
- Expected: Story "Publish ledger with safe replacement" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Running python -m pytest tests/test_publisher.py::test_publish_uses_same_directory_temp_file exits with code 0 and asserts LedgerPublisher.publish in modern_bank/publisher.py creates its temporary ledger path with the same parent directory as the target accounts.dat.
- Check acceptance criterion 2: Running python -m pytest tests/test_publisher.py::test_publish_replaces_accounts_dat_only_after_success exits with code 0 and asserts modern_bank/publisher.py updates the target accounts.dat bytes only after the temporary file write has completed.
- Check acceptance criterion 3: Running python -m pytest tests/test_publisher.py::test_publish_failure_preserves_original_accounts_dat exits with code 0 and asserts LedgerPublisher.publish leaves the original accounts.dat content unchanged when the temp-file write raises an OSError.

### FUNCTIONAL-012 — Validate ledger before replacement

- User Story: WO-015
- Objective: Validate functional behavior for "Validate ledger before replacement" against acceptance criteria.
- Expected: Story "Validate ledger before replacement" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Running python -m pytest tests/test_publisher_validation.py::test_publish_rejects_record_count_mismatch exits with code 0 and asserts LedgerPublisher.publish in modern_bank/publisher.py does not replace accounts.dat when expected_record_count differs from len(serialized_rows).
- Check acceptance criterion 2: Running python -m pytest tests/test_publisher_validation.py::test_publish_rejects_invalid_account_row exits with code 0 and asserts modern_bank/publisher.py invokes FixedWidthCodec validation before os.replace for rows not matching IIIIIIII|BBBBBBBBBBBB.
- Check acceptance criterion 3: Running python -m pytest tests/test_publisher_validation.py::test_validation_failure_preserves_original_accounts_dat exits with code 0 and asserts the target accounts.dat bytes remain equal to tests/fixtures/publisher_validation/original_accounts.dat after a malformed row failure.

### FUNCTIONAL-013 — Orchestrate CLI ledger publication

- User Story: WO-016
- Objective: Validate functional behavior for "Orchestrate CLI ledger publication" against acceptance criteria.
- Expected: Story "Orchestrate CLI ledger publication" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Running python -m modern_bank.cli load --accounts tests/fixtures/cli/basic/accounts.dat --operations tests/fixtures/cli/basic/operations.dat exits with code 0 and prints PROCESSED=, REJECTED=, and TOTAL_CENTS= lines from modern_bank/cli.py.
- Check acceptance criterion 2: Running python -m pytest tests/test_cli.py::test_cli_invokes_ledger_publisher_once exits with code 0 and asserts modern_bank.cli calls LedgerPublisher.publish exactly once after operation processing completes.
- Check acceptance criterion 3: Running python -m pytest tests/test_cli.py::test_cli_missing_operations_file_returns_nonzero exits with code 0 and asserts the modern_bank/cli.py load command returns a non-zero status without replacing tests/fixtures/cli/missing_operations/accounts.dat.

### FUNCTIONAL-014 — Append run audit JSONL

- User Story: WO-017
- Objective: Validate functional behavior for "Append run audit JSONL" against acceptance criteria.
- Expected: Story "Append run audit JSONL" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Running python -m pytest tests/test_audit.py::test_audit_writer_appends_jsonl_events exits with code 0 and asserts AuditWriter.append_event in modern_bank/audit.py appends valid JSON lines without overwriting the existing audit file.
- Check acceptance criterion 2: Running python -m pytest tests/test_audit.py::test_required_event_types_are_written exits with code 0 and asserts modern_bank/audit.py records fixture_selected, ledger_generated, and run_completed event_type values.
- Check acceptance criterion 3: Running python -m pytest tests/test_cli_audit_integration.py::test_cli_load_emits_audit_events exits with code 0 and asserts modern_bank/cli.py creates or appends audit.jsonl entries when the load command completes successfully.

### FUNCTIONAL-015 — Document migration and rollback

- User Story: WO-018
- Objective: Validate functional behavior for "Document migration and rollback" against acceptance criteria.
- Expected: Story "Document migration and rollback" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: File inspection of README.md shows a migration map section that references bank.cob offsets bank-row(1:8), bank-row(10:12), ops-row(1:1), ops-row(3:8), ops-row(12:8), and ops-row(21:12).
- Check acceptance criterion 2: File inspection of README.md shows the account ledger contract accounts.dat as IIIIIIII|BBBBBBBBBBBB and the operation feed contract operations.dat as K|SSSSSSSS|TTTTTTTT|AAAAAAAAAAAA.
- Check acceptance criterion 3: File inspection of README.md shows a rollback procedure that explicitly references accounts.tmp, accounts.dat, operations.dat, retaining original inputs, discarding generated modern output, and rerunning the COBOL baseline bank.cob.

### FUNCTIONAL-016 — Store run artifacts metadata

- User Story: WO-021
- Objective: Validate functional behavior for "Store run artifacts metadata" against acceptance criteria.
- Expected: Story "Store run artifacts metadata" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Running python -m pytest tests/test_artifacts.py::test_run_artifact_store_writes_metadata_json exits with code 0 and asserts RunArtifactStore.write_metadata in modern_bank/artifacts.py creates a run_metadata.json file.
- Check acceptance criterion 2: Running python -m pytest tests/test_artifacts.py::test_metadata_contains_internal_classification_and_retention exits with code 0 and asserts modern_bank/artifacts.py writes data_classification=Internal and retention_days greater than or equal to 365 in run_metadata.json.
- Check acceptance criterion 3: Running python -m pytest tests/test_cli_artifact_integration.py::test_cli_load_records_ledger_summary_and_audit_artifacts exits with code 0 and asserts modern_bank/cli.py records generated accounts.dat, summary output, and audit.jsonl entries in run_metadata.json.

### FUNCTIONAL-017 — Test Fixed-Width Record Parsing

- User Story: WO-008
- Objective: Validate functional behavior for "Test Fixed-Width Record Parsing" against acceptance criteria.
- Expected: Story "Test Fixed-Width Record Parsing" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Unit tests: running python -m pytest tests/test_records.py -q exits with status 0 and includes assertions in tests/test_records.py for accounts.dat rows formatted as IIIIIIII|BBBBBBBBBBBB.
- Check acceptance criterion 2: Unit tests: tests/test_records.py contains test functions that verify modern_bank/records.py extracts operation kind from row[0], source account from row[2:10], destination account from row[11:19], and amount from row[20:32] for operations.dat.
- Check acceptance criterion 3: Unit tests: tests/test_records.py asserts malformed account rows with a missing pipe at character position 9 and malformed operation rows with non-numeric 12-character amount text are rejected by modern_bank/records.py without floating-point conversion.

### FUNCTIONAL-018 — Commit Golden Parity Fixture Catalog

- User Story: WO-009
- Objective: Validate functional behavior for "Commit Golden Parity Fixture Catalog" against acceptance criteria.
- Expected: Story "Commit Golden Parity Fixture Catalog" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Mock data and fixtures: tests/fixtures/golden contains 13 category directories named valid_deposit, valid_withdrawal, valid_transfer, malformed_row, insufficient_funds, missing_source, missing_destination, self_transfer, invalid_type, non_numeric_amount, zero_amount, fixed_width_formatting, and final_totals.
- Check acceptance criterion 2: Mock data and fixtures: each tests/fixtures/golden/* directory contains accounts.dat and operations.dat files whose account rows match the IIIIIIII|BBBBBBBBBBBB shape and whose operation rows intentionally represent the named category.
- Check acceptance criterion 3: Mock data and fixtures: tests/fixtures/golden/manifest.json lists all 13 category IDs and includes expected_summary fields named processed, rejected, and total_cents for each category.

### FUNCTIONAL-019 — Build Side-by-Side Parity Runner

- User Story: WO-019
- Objective: Validate functional behavior for "Build Side-by-Side Parity Runner" against acceptance criteria.
- Expected: Story "Build Side-by-Side Parity Runner" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: System integration tests: running python -m pytest tests/test_parity_runner.py -q exits with status 0 and verifies tests/parity_runner.py creates isolated legacy and modern work directories for a fixture under tests/fixtures/golden.
- Check acceptance criterion 2: System integration tests: executing python tests/parity_runner.py --fixture tests/fixtures/golden/valid_deposit --out .tmp/parity/valid_deposit creates .tmp/parity/valid_deposit/legacy/accounts.dat and .tmp/parity/valid_deposit/modern/accounts.dat when both runners are available.
- Check acceptance criterion 3: System integration tests: .tmp/parity/valid_deposit/legacy/stdout.txt and .tmp/parity/valid_deposit/modern/stdout.txt contain captured stdout with PROCESSED=, REJECTED=, and TOTAL_CENTS= lines or the runner records a nonzero exit_code in run.json for the failing side.

### FUNCTIONAL-020 — Gate Parity With Byte Comparisons

- User Story: WO-022
- Objective: Validate functional behavior for "Gate Parity With Byte Comparisons" against acceptance criteria.
- Expected: Story "Gate Parity With Byte Comparisons" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: System integration tests: running python -m pytest tests/test_parity.py -q iterates every category listed in tests/fixtures/golden/manifest.json and invokes tests/parity_runner.py for each fixture.
- Check acceptance criterion 2: System integration tests: tests/test_parity.py asserts legacy final accounts.dat bytes equal modern final accounts.dat bytes by comparing binary reads from the legacy/accounts.dat and modern/accounts.dat artifacts.
- Check acceptance criterion 3: System integration tests: tests/test_parity.py asserts parsed PROCESSED, REJECTED, and TOTAL_CENTS values from legacy/stdout.txt equal the corresponding values from modern/stdout.txt for every fixture.

### FUNCTIONAL-021 — Add Required Benchmark Timing Harness

- User Story: WO-023
- Objective: Validate functional behavior for "Add Required Benchmark Timing Harness" against acceptance criteria.
- Expected: Story "Add Required Benchmark Timing Harness" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: System integration tests: running python benchmarks/runner.py --sizes 1200x400 5000x500 --out .tmp/benchmarks/results.json creates .tmp/benchmarks/results.json with entries for 1200x400 and 5000x500.
- Check acceptance criterion 2: System integration tests: .tmp/benchmarks/results.json contains legacy_duration_ms, modern_duration_ms, parity_status, accounts_count, operations_count, and command fields for each benchmark size.
- Check acceptance criterion 3: Unit tests: running python -m pytest tests/test_benchmark_runner.py -q exits with status 0 and verifies benchmarks/runner.py duration calculations use time.perf_counter_ns or an equivalent monotonic timer.

### FUNCTIONAL-022 — Publish Qualified Benchmark Speedup Report

- User Story: WO-026
- Objective: Validate functional behavior for "Publish Qualified Benchmark Speedup Report" against acceptance criteria.
- Expected: Story "Publish Qualified Benchmark Speedup Report" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Unit tests: running python -m pytest tests/test_benchmark_report.py -q exits with status 0 and verifies benchmarks/report.py computes speedup from legacy_duration_ms and modern_duration_ms fields.
- Check acceptance criterion 2: System integration tests: running python benchmarks/report.py --input .tmp/benchmarks/results.json --output .tmp/benchmarks/report.md creates .tmp/benchmarks/report.md when .tmp/benchmarks/results.json contains 1200x400 and 5000x500 entries.
- Check acceptance criterion 3: System integration tests: .tmp/benchmarks/report.md contains the exact sentence Local prototype result on one host, pending independent review. beside both 28.6x at 1200x400 and 128.1x at 5000x500 when preliminary prototype labels are included.

### FUNCTIONAL-023 — Scaffold Vite React Tailwind dashboard

- User Story: WO-004
- Objective: Validate functional behavior for "Scaffold Vite React Tailwind dashboard" against acceptance criteria.
- Expected: Story "Scaffold Vite React Tailwind dashboard" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: File inspection of web/package.json shows scripts for dev, build, preview, and test or lint, with dependencies for React, Vite, and Tailwind CSS appropriate for the lightweight local dashboard.
- Check acceptance criterion 2: File inspection of web/src/App.jsx shows a React component rendering a visible synthetic prototype placeholder and no production banking claims.
- Check acceptance criterion 3: Running cd web && npm install && npm run build exits with code 0 and creates a Vite build output directory such as web/dist/.

### FUNCTIONAL-024 — Create localhost batch API endpoints

- User Story: WO-024
- Objective: Validate functional behavior for "Create localhost batch API endpoints" against acceptance criteria.
- Expected: Story "Create localhost batch API endpoints" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: File inspection of modern_bank/api.py shows a FastAPI app object and route handlers registered for GET /api/v1/fixtures and POST /api/v1/runs with Pydantic request and response models for fixture_id, mode, run_id, status, processed_count, rejected_count, total_cents, duration_ms, parity_status, artifact_refs, and audit_events.
- Check acceptance criterion 2: Running python -m pytest tests/test_api.py::test_get_fixtures_returns_catalog exits with code 0 and asserts that GET /api/v1/fixtures returns HTTP 200 with a JSON array containing at least one object with id, label, account_count, operation_count, and synthetic_prototype fields.
- Check acceptance criterion 3: Running python -m pytest tests/test_api.py::test_post_runs_starts_fixture_run exits with code 0 and asserts that POST /api/v1/runs with application/json body containing fixture_id and mode returns HTTP 202 or HTTP 200 with run_id, status, processed_count, rejected_count, total_cents, parity_status, and duration_ms fields.

### FUNCTIONAL-025 — Return safe structured API errors

- User Story: WO-027
- Objective: Validate functional behavior for "Return safe structured API errors" against acceptance criteria.
- Expected: Story "Return safe structured API errors" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: File inspection of modern_bank/api_errors.py shows an ApiError model or equivalent typed structure with errorCode, message, correlationId, and statusCode fields and no field intended to return traceback, stack, cwd, hostname, or absolute_path.
- Check acceptance criterion 2: File inspection of modern_bank/api.py shows the FastAPI app registers exception handlers from modern_bank/api_errors.py for request validation errors, known API errors, and uncaught exceptions.
- Check acceptance criterion 3: Running python -m pytest tests/test_api_errors.py::test_validation_error_shape exits with code 0 and asserts POST /api/v1/runs with missing fixture_id returns HTTP 400 or 422 with JSON keys errorCode, message, correlationId, and statusCode.

### FUNCTIONAL-026 — Enforce allow-listed fixture identifiers

- User Story: WO-028
- Objective: Validate functional behavior for "Enforce allow-listed fixture identifiers" against acceptance criteria.
- Expected: Story "Enforce allow-listed fixture identifiers" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: File inspection of modern_bank/api.py shows POST /api/v1/runs request models contain fixture_id and mode fields and do not contain path, file_path, accounts_path, operations_path, directory, or cwd request fields.
- Check acceptance criterion 2: File inspection of modern_bank/api.py shows fixture validation calls a FixtureCatalog capability or dependency before run service execution and passes only the resolved catalog fixture object or fixture ID to the run service.
- Check acceptance criterion 3: Running python -m pytest tests/test_fixture_allowlist_api.py::test_allowed_fixture_id_starts_run exits with code 0 and asserts POST /api/v1/runs using a catalog fixture ID returns HTTP 200 or HTTP 202 with the same fixture_id in the JSON body.

### FUNCTIONAL-027 — Render batch evidence dashboard

- User Story: WO-030
- Objective: Validate functional behavior for "Render batch evidence dashboard" against acceptance criteria.
- Expected: Story "Render batch evidence dashboard" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: File inspection of web/src/App.jsx shows fetch calls or an equivalent API client for GET /api/v1/fixtures and POST /api/v1/runs, with no request field named path, accounts_path, operations_path, or directory.
- Check acceptance criterion 2: Running cd web && npm run build exits with code 0 and verifies web/src/App.jsx compiles after rendering fixture selection, run status, processed_count, rejected_count, total_cents, parity_status, duration_ms, rejection_summary, and audit_events fields.
- Check acceptance criterion 3: Frontend unit test web/src/App.test.jsx::renders_run_evidence or equivalent exits with code 0 and asserts the dashboard displays status, parity, processed count, rejected count, total cents, duration, and at least one audit event from mocked API responses.

### FUNCTIONAL-028 — Add prototype labels and focus states

- User Story: WO-032
- Objective: Validate functional behavior for "Add prototype labels and focus states" against acceptance criteria.
- Expected: Story "Add prototype labels and focus states" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: File inspection of web/src/App.jsx shows the exact visible phrase Synthetic prototype or equivalent on the page header, run evidence region, artifact or audit region, and any benchmark timing region rendered by the dashboard.
- Check acceptance criterion 2: File inspection of web/src/App.jsx shows form controls for fixture selection and run start have associated label elements or aria-label attributes with accessible names referencing fixture selection and starting a synthetic run.
- Check acceptance criterion 3: Running cd web && npm run build exits with code 0 after the label and focus-state changes.

### FUNCTIONAL-029 — Create Forge build and scan pipeline

- User Story: WO-020
- Objective: Validate functional behavior for "Create Forge build and scan pipeline" against acceptance criteria.
- Expected: Story "Create Forge build and scan pipeline" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: File inspection of .forge/shipping.yml shows four top-level or named pipeline steps containing the exact identifiers build:python, build:docker, secret-scan, and dependency-scan.
- Check acceptance criterion 2: Running forge shipping validate .forge/shipping.yml exits with status code 0 and reports no YAML schema error for the .forge/shipping.yml pipeline definition.
- Check acceptance criterion 3: The .forge/shipping.yml build:python step contains a command that invokes the Python build or test entry point, including python -m pytest or an equivalent project test command, and does not modify bank.cob.

### FUNCTIONAL-030 — Gate releases on P0 parity

- User Story: WO-025
- Objective: Validate functional behavior for "Gate releases on P0 parity" against acceptance criteria.
- Expected: Story "Gate releases on P0 parity" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: The .forge/shipping.yml file contains a parity gate step after build:python and build:docker that invokes python -m pytest tests/test_parity.py or the established parity test command.
- Check acceptance criterion 2: Running python -m pytest tests/test_parity.py -q exits with status code 0 on the committed P0 fixture set and reports no failed assertion for final accounts.dat byte comparison.
- Check acceptance criterion 3: The parity gate command in .forge/shipping.yml fails with a non-zero status when tests/test_parity.py has an assertion failure for PROCESSED, REJECTED, or TOTAL_CENTS summary comparison.

### FUNCTIONAL-031 — Capture benchmark reports in shipping

- User Story: WO-029
- Objective: Validate functional behavior for "Capture benchmark reports in shipping" against acceptance criteria.
- Expected: Story "Capture benchmark reports in shipping" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: The .forge/shipping.yml file contains a benchmark artifact step that invokes python benchmarks/runner.py or the established benchmark command after the parity gate step.
- Check acceptance criterion 2: The .forge/shipping.yml benchmark step declares artifact capture paths for benchmark reports produced by benchmarks/runner.py, including a machine-readable report file path and a human-readable report file path.
- Check acceptance criterion 3: Running python benchmarks/runner.py --output artifacts/benchmarks or the repository-supported equivalent creates report files under artifacts/benchmarks for the 1200x400 and 5000x500 fixture sizes.

### FUNCTIONAL-032 — Package evidence artifacts deterministically

- User Story: WO-031
- Objective: Validate functional behavior for "Package evidence artifacts deterministically" against acceptance criteria.
- Expected: Story "Package evidence artifacts deterministically" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: The scripts/package_artifacts.sh file exists, is executable, and starts with a POSIX shell or bash shebang plus strict error handling such as set -euo pipefail.
- Check acceptance criterion 2: Running scripts/package_artifacts.sh artifacts dist/evidence.tar.gz creates dist/evidence.tar.gz and a manifest file inside the archive that lists packaged fixture, ledger, audit JSONL, parity diff, and benchmark report paths.
- Check acceptance criterion 3: Archive inspection with tar -tzf dist/evidence.tar.gz shows repository-relative entries for fixtures, ledgers or accounts.dat outputs, audit .jsonl files, parity diff files, and benchmark report files.

### FUNCTIONAL-033 — Document rollout and rollback runbook

- User Story: WO-033
- Objective: Validate functional behavior for "Document rollout and rollback runbook" against acceptance criteria.
- Expected: Story "Document rollout and rollback runbook" satisfies expected functional validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: README.md contains a rollout runbook section that references .forge/shipping.yml, bank.cob, tests/test_parity.py, benchmarks/runner.py, and scripts/package_artifacts.sh by path.
- Check acceptance criterion 2: README.md includes a Docker execution step that names the Docker build or run command used for the prototype and explicitly states that execution uses synthetic accounts.dat and operations.dat fixtures only.
- Check acceptance criterion 3: README.md documents that python -m pytest tests/test_parity.py -q is the P0 parity command and that any mismatch in final accounts.dat, PROCESSED, REJECTED, or TOTAL_CENTS blocks sign-off.

---

## Smoke test suite (33)

### SMOKE-001 — Scaffold Python modernization package

- User Story: WO-001
- Objective: Run critical-path smoke verification for "Scaffold Python modernization package" after deployment.
- Expected: Story "Scaffold Python modernization package" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-001.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-002 — Add reproducible COBOL baseline runner

- User Story: WO-002
- Objective: Run critical-path smoke verification for "Add reproducible COBOL baseline runner" after deployment.
- Expected: Story "Add reproducible COBOL baseline runner" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-002.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-003 — Implement fixed-width record codec

- User Story: WO-003
- Objective: Run critical-path smoke verification for "Implement fixed-width record codec" after deployment.
- Expected: Story "Implement fixed-width record codec" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-003.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-004 — Add fixture allow-list catalog

- User Story: WO-005
- Objective: Run critical-path smoke verification for "Add fixture allow-list catalog" after deployment.
- Expected: Story "Add fixture allow-list catalog" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-005.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-005 — Add modern CLI contract skeleton

- User Story: WO-006
- Objective: Run critical-path smoke verification for "Add modern CLI contract skeleton" after deployment.
- Expected: Story "Add modern CLI contract skeleton" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-006.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-006 — Build ordered ledger account index

- User Story: WO-007
- Objective: Run critical-path smoke verification for "Build ordered ledger account index" after deployment.
- Expected: Story "Build ordered ledger account index" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-007.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-007 — Preflight account ledger validity

- User Story: WO-010
- Objective: Run critical-path smoke verification for "Preflight account ledger validity" after deployment.
- Expected: Story "Preflight account ledger validity" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-010.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-008 — Process accepted DWT mutations

- User Story: WO-011
- Objective: Run critical-path smoke verification for "Process accepted DWT mutations" after deployment.
- Expected: Story "Process accepted DWT mutations" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-011.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-009 — Preserve processor rejection paths

- User Story: WO-012
- Objective: Run critical-path smoke verification for "Preserve processor rejection paths" after deployment.
- Expected: Story "Preserve processor rejection paths" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-012.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-010 — Format fixed-width batch summary

- User Story: WO-013
- Objective: Run critical-path smoke verification for "Format fixed-width batch summary" after deployment.
- Expected: Story "Format fixed-width batch summary" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-013.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-011 — Publish ledger with safe replacement

- User Story: WO-014
- Objective: Run critical-path smoke verification for "Publish ledger with safe replacement" after deployment.
- Expected: Story "Publish ledger with safe replacement" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-014.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-012 — Validate ledger before replacement

- User Story: WO-015
- Objective: Run critical-path smoke verification for "Validate ledger before replacement" after deployment.
- Expected: Story "Validate ledger before replacement" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-015.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-013 — Orchestrate CLI ledger publication

- User Story: WO-016
- Objective: Run critical-path smoke verification for "Orchestrate CLI ledger publication" after deployment.
- Expected: Story "Orchestrate CLI ledger publication" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-016.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-014 — Append run audit JSONL

- User Story: WO-017
- Objective: Run critical-path smoke verification for "Append run audit JSONL" after deployment.
- Expected: Story "Append run audit JSONL" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-017.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-015 — Document migration and rollback

- User Story: WO-018
- Objective: Run critical-path smoke verification for "Document migration and rollback" after deployment.
- Expected: Story "Document migration and rollback" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-018.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-016 — Store run artifacts metadata

- User Story: WO-021
- Objective: Run critical-path smoke verification for "Store run artifacts metadata" after deployment.
- Expected: Story "Store run artifacts metadata" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-021.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-017 — Test Fixed-Width Record Parsing

- User Story: WO-008
- Objective: Run critical-path smoke verification for "Test Fixed-Width Record Parsing" after deployment.
- Expected: Story "Test Fixed-Width Record Parsing" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-008.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-018 — Commit Golden Parity Fixture Catalog

- User Story: WO-009
- Objective: Run critical-path smoke verification for "Commit Golden Parity Fixture Catalog" after deployment.
- Expected: Story "Commit Golden Parity Fixture Catalog" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-009.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-019 — Build Side-by-Side Parity Runner

- User Story: WO-019
- Objective: Run critical-path smoke verification for "Build Side-by-Side Parity Runner" after deployment.
- Expected: Story "Build Side-by-Side Parity Runner" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-019.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-020 — Gate Parity With Byte Comparisons

- User Story: WO-022
- Objective: Run critical-path smoke verification for "Gate Parity With Byte Comparisons" after deployment.
- Expected: Story "Gate Parity With Byte Comparisons" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-022.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-021 — Add Required Benchmark Timing Harness

- User Story: WO-023
- Objective: Run critical-path smoke verification for "Add Required Benchmark Timing Harness" after deployment.
- Expected: Story "Add Required Benchmark Timing Harness" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-023.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-022 — Publish Qualified Benchmark Speedup Report

- User Story: WO-026
- Objective: Run critical-path smoke verification for "Publish Qualified Benchmark Speedup Report" after deployment.
- Expected: Story "Publish Qualified Benchmark Speedup Report" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-026.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-023 — Scaffold Vite React Tailwind dashboard

- User Story: WO-004
- Objective: Run critical-path smoke verification for "Scaffold Vite React Tailwind dashboard" after deployment.
- Expected: Story "Scaffold Vite React Tailwind dashboard" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-004.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-024 — Create localhost batch API endpoints

- User Story: WO-024
- Objective: Run critical-path smoke verification for "Create localhost batch API endpoints" after deployment.
- Expected: Story "Create localhost batch API endpoints" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-024.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-025 — Return safe structured API errors

- User Story: WO-027
- Objective: Run critical-path smoke verification for "Return safe structured API errors" after deployment.
- Expected: Story "Return safe structured API errors" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-027.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-026 — Enforce allow-listed fixture identifiers

- User Story: WO-028
- Objective: Run critical-path smoke verification for "Enforce allow-listed fixture identifiers" after deployment.
- Expected: Story "Enforce allow-listed fixture identifiers" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-028.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-027 — Render batch evidence dashboard

- User Story: WO-030
- Objective: Run critical-path smoke verification for "Render batch evidence dashboard" after deployment.
- Expected: Story "Render batch evidence dashboard" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-030.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-028 — Add prototype labels and focus states

- User Story: WO-032
- Objective: Run critical-path smoke verification for "Add prototype labels and focus states" after deployment.
- Expected: Story "Add prototype labels and focus states" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-032.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-029 — Create Forge build and scan pipeline

- User Story: WO-020
- Objective: Run critical-path smoke verification for "Create Forge build and scan pipeline" after deployment.
- Expected: Story "Create Forge build and scan pipeline" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-020.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-030 — Gate releases on P0 parity

- User Story: WO-025
- Objective: Run critical-path smoke verification for "Gate releases on P0 parity" after deployment.
- Expected: Story "Gate releases on P0 parity" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-025.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-031 — Capture benchmark reports in shipping

- User Story: WO-029
- Objective: Run critical-path smoke verification for "Capture benchmark reports in shipping" after deployment.
- Expected: Story "Capture benchmark reports in shipping" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-029.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-032 — Package evidence artifacts deterministically

- User Story: WO-031
- Objective: Run critical-path smoke verification for "Package evidence artifacts deterministically" after deployment.
- Expected: Story "Package evidence artifacts deterministically" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-031.
- Verify no blocking errors in logs, APIs, or UI.

### SMOKE-033 — Document rollout and rollback runbook

- User Story: WO-033
- Objective: Run critical-path smoke verification for "Document rollout and rollback runbook" after deployment.
- Expected: Story "Document rollout and rollback runbook" satisfies expected smoke validation outcomes without critical issues.

**Steps**
- Deploy the latest build to target environment.
- Execute primary user flow for WO-033.
- Verify no blocking errors in logs, APIs, or UI.

---

## Regression test suite (33)

### REGRESSION-001 — Scaffold Python modernization package

- User Story: WO-001
- Objective: Prevent regressions in existing behavior impacted by "Scaffold Python modernization package".
- Expected: Story "Scaffold Python modernization package" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Unit tests: running python -m pytest tests/test_project_scaffold.py from the repository root succeeds and test_project_imports_modern_bank imports modern_bank from modern_bank/__init__.py.
- Check acceptance criterion 2: System integration tests: N/A — this story creates package metadata only and does not expose a service boundary, but python -m pip install -e . must complete using pyproject.toml without requiring accounts.dat or operations.dat.
- Check acceptance criterion 3: Mock data/fixtures: N/A — no ledger parsing is implemented in this scaffold story; README.md must state that synthetic fixture files are introduced by later fixture work rather than by pyproject.toml.

### REGRESSION-002 — Add reproducible COBOL baseline runner

- User Story: WO-002
- Objective: Prevent regressions in existing behavior impacted by "Add reproducible COBOL baseline runner".
- Expected: Story "Add reproducible COBOL baseline runner" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Unit tests: N/A — scripts/run_legacy.sh is a shell wrapper around bank.cob, and verification is performed by the executable integration command documented in README.md.
- Check acceptance criterion 2: System integration tests: running docker build -t bbs-sg-legacy-baseline . uses Dockerfile and completes without modifying bank.cob.
- Check acceptance criterion 3: System integration tests: running scripts/run_legacy.sh tests/fixtures/legacy_smoke after creating tests/fixtures/legacy_smoke/accounts.dat and tests/fixtures/legacy_smoke/operations.dat exits with status 0 and stdout contains PROCESSED=, REJECTED=, and TOTAL_CENTS= from bank.cob.

### REGRESSION-003 — Implement fixed-width record codec

- User Story: WO-003
- Objective: Prevent regressions in existing behavior impacted by "Implement fixed-width record codec".
- Expected: Story "Implement fixed-width record codec" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Unit tests: running python -m pytest tests/test_records.py succeeds and includes assertions for FixedWidthCodec.parse_account_line, FixedWidthCodec.format_account_record, FixedWidthCodec.parse_operation_line, and FixedWidthCodec.format_operation_record.
- Check acceptance criterion 2: System integration tests: N/A — modern_bank/records.py is a pure contract module with no service boundary or subprocess boundary; integration with scripts/run_modern.py is covered by the later CLI story.
- Check acceptance criterion 3: Mock data/fixtures: tests/test_records.py commits representative account rows such as 00000001|000000001000 and operation rows such as D|00000001|00000000|000000000250 as test literals or fixture parameters.

### REGRESSION-004 — Add fixture allow-list catalog

- User Story: WO-005
- Objective: Prevent regressions in existing behavior impacted by "Add fixture allow-list catalog".
- Expected: Story "Add fixture allow-list catalog" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Unit tests: running python -m pytest tests/test_fixture_catalog.py succeeds and test_fixture_catalog_entries_validate_with_fixed_width_codec parses each catalog accounts.dat and operations.dat file through FixedWidthCodec.
- Check acceptance criterion 2: System integration tests: N/A — tests/fixtures/fixture_catalog.json is a local allow-list artifact and does not expose a service or subprocess boundary in this story.
- Check acceptance criterion 3: Mock data/fixtures: tests/fixtures/fixture_catalog.json and at least one committed fixture directory containing accounts.dat and operations.dat are present under tests/fixtures.

### REGRESSION-005 — Add modern CLI contract skeleton

- User Story: WO-006
- Objective: Prevent regressions in existing behavior impacted by "Add modern CLI contract skeleton".
- Expected: Story "Add modern CLI contract skeleton" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Unit tests: running python -m pytest tests/test_run_modern_cli.py succeeds and includes coverage for the main function in scripts/run_modern.py using valid and invalid fixture paths.
- Check acceptance criterion 2: System integration tests: running python scripts/run_modern.py --accounts tests/fixtures/modern_smoke/accounts.dat --operations tests/fixtures/modern_smoke/operations.dat --contract-check exits with status 0 and stdout contains CONTRACT_OK.
- Check acceptance criterion 3: Mock data/fixtures: tests/fixtures/modern_smoke/accounts.dat and tests/fixtures/modern_smoke/operations.dat are committed and are parsed by tests/test_run_modern_cli.py.

### REGRESSION-006 — Build ordered ledger account index

- User Story: WO-007
- Objective: Prevent regressions in existing behavior impacted by "Build ordered ledger account index".
- Expected: Story "Build ordered ledger account index" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Unit tests: running python -m pytest tests/test_ledger.py exits with code 0 and includes assertions that LedgerIndex.load_from_path in modern_bank/ledger.py parses tests/fixtures/ledger/basic_accounts.dat into account_ids [00000001, 00000002, 00000003] in source-file order.
- Check acceptance criterion 2: Unit tests: tests/test_ledger.py asserts LedgerIndex.get_account in modern_bank/ledger.py returns integer balance 1250 for account ID 00000001 and returns None or raises the documented lookup exception for account ID 99999999 without reading accounts.dat again.
- Check acceptance criterion 3: Unit tests: tests/test_ledger.py asserts LedgerIndex.to_rows in modern_bank/ledger.py serializes every row as exactly 21 characters before the newline using 8 account digits, one pipe at offset 9, and 12 balance digits.

### REGRESSION-007 — Preflight account ledger validity

- User Story: WO-010
- Objective: Prevent regressions in existing behavior impacted by "Preflight account ledger validity".
- Expected: Story "Preflight account ledger validity" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Unit tests: running python -m pytest tests/test_ledger_preflight.py exits with code 0 and asserts LedgerIndex.load_from_path in modern_bank/ledger.py raises DuplicateAccountError for tests/fixtures/ledger/duplicate_accounts.dat containing account ID 00000001 twice.
- Check acceptance criterion 2: Unit tests: tests/test_ledger_preflight.py asserts LedgerIndex.load_from_path in modern_bank/ledger.py raises InvalidAccountRowError for tests/fixtures/ledger/bad_balance_width.dat where the balance field is not exactly 12 digits.
- Check acceptance criterion 3: Unit tests: tests/test_ledger_preflight.py asserts LedgerIndex.load_from_path in modern_bank/ledger.py raises InvalidAccountRowError for tests/fixtures/ledger/non_numeric_balance.dat where bank-row(10:12) contains a non-numeric character.

### REGRESSION-008 — Process accepted DWT mutations

- User Story: WO-011
- Objective: Prevent regressions in existing behavior impacted by "Process accepted DWT mutations".
- Expected: Story "Process accepted DWT mutations" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Unit tests: running python -m pytest tests/test_processor_valid_ops.py exits with code 0 and asserts OperationProcessor.process_rows in modern_bank/processor.py applies D|00000001|00000000|000000000250 by increasing account 00000001 in LedgerIndex by 250 cents.
- Check acceptance criterion 2: Unit tests: tests/test_processor_valid_ops.py asserts OperationProcessor.process_rows in modern_bank/processor.py applies W|00000001|00000000|000000000100 by decreasing account 00000001 in LedgerIndex by 100 cents when funds are available.
- Check acceptance criterion 3: Unit tests: tests/test_processor_valid_ops.py asserts OperationProcessor.process_rows in modern_bank/processor.py applies T|00000001|00000002|000000000125 by subtracting 125 cents from account 00000001 and adding 125 cents to account 00000002 in the same in-memory ledger.

### REGRESSION-009 — Preserve processor rejection paths

- User Story: WO-012
- Objective: Prevent regressions in existing behavior impacted by "Preserve processor rejection paths".
- Expected: Story "Preserve processor rejection paths" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Unit tests: running python -m pytest tests/test_processor_rejections.py exits with code 0 and asserts OperationProcessor.process_rows in modern_bank/processor.py increments rejected by 1 and leaves LedgerIndex balances unchanged for unsupported operation kind X.
- Check acceptance criterion 2: Unit tests: tests/test_processor_rejections.py asserts modern_bank/processor.py rejects non-numeric amount text, zero amount text 000000000000, and operation rows shorter than 32 characters without mutating any account balance.
- Check acceptance criterion 3: Unit tests: tests/test_processor_rejections.py asserts modern_bank/processor.py rejects missing source account 99999999 for D, W, and T rows and rejects missing transfer destination account 99999998 for T rows.

### REGRESSION-010 — Format fixed-width batch summary

- User Story: WO-013
- Objective: Prevent regressions in existing behavior impacted by "Format fixed-width batch summary".
- Expected: Story "Format fixed-width batch summary" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Unit tests: running python -m pytest tests/test_summary.py exits with code 0 and asserts SummaryReporter.format_summary in modern_bank/summary.py returns PROCESSED=00000003, REJECTED=00000002, and TOTAL_CENTS=0000000000012500 for the specified test ledger and counters.
- Check acceptance criterion 2: Unit tests: tests/test_summary.py asserts SummaryReporter.calculate_total_cents in modern_bank/summary.py sums integer balances from LedgerIndex in modern_bank/ledger.py and returns an int, not a float or formatted currency string.
- Check acceptance criterion 3: Integration tests: running python -m pytest tests/test_summary_integration.py exits with code 0 and asserts OperationProcessor from modern_bank/processor.py plus SummaryReporter from modern_bank/summary.py formats the summary for tests/fixtures/operations/summary_mixed.dat exactly as tests/fixtures/expected/summary_mixed_stdout.txt.

### REGRESSION-011 — Publish ledger with safe replacement

- User Story: WO-014
- Objective: Prevent regressions in existing behavior impacted by "Publish ledger with safe replacement".
- Expected: Story "Publish ledger with safe replacement" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Running python -m pytest tests/test_publisher.py::test_publish_uses_same_directory_temp_file exits with code 0 and asserts LedgerPublisher.publish in modern_bank/publisher.py creates its temporary ledger path with the same parent directory as the target accounts.dat.
- Check acceptance criterion 2: Running python -m pytest tests/test_publisher.py::test_publish_replaces_accounts_dat_only_after_success exits with code 0 and asserts modern_bank/publisher.py updates the target accounts.dat bytes only after the temporary file write has completed.
- Check acceptance criterion 3: Running python -m pytest tests/test_publisher.py::test_publish_failure_preserves_original_accounts_dat exits with code 0 and asserts LedgerPublisher.publish leaves the original accounts.dat content unchanged when the temp-file write raises an OSError.

### REGRESSION-012 — Validate ledger before replacement

- User Story: WO-015
- Objective: Prevent regressions in existing behavior impacted by "Validate ledger before replacement".
- Expected: Story "Validate ledger before replacement" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Running python -m pytest tests/test_publisher_validation.py::test_publish_rejects_record_count_mismatch exits with code 0 and asserts LedgerPublisher.publish in modern_bank/publisher.py does not replace accounts.dat when expected_record_count differs from len(serialized_rows).
- Check acceptance criterion 2: Running python -m pytest tests/test_publisher_validation.py::test_publish_rejects_invalid_account_row exits with code 0 and asserts modern_bank/publisher.py invokes FixedWidthCodec validation before os.replace for rows not matching IIIIIIII|BBBBBBBBBBBB.
- Check acceptance criterion 3: Running python -m pytest tests/test_publisher_validation.py::test_validation_failure_preserves_original_accounts_dat exits with code 0 and asserts the target accounts.dat bytes remain equal to tests/fixtures/publisher_validation/original_accounts.dat after a malformed row failure.

### REGRESSION-013 — Orchestrate CLI ledger publication

- User Story: WO-016
- Objective: Prevent regressions in existing behavior impacted by "Orchestrate CLI ledger publication".
- Expected: Story "Orchestrate CLI ledger publication" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Running python -m modern_bank.cli load --accounts tests/fixtures/cli/basic/accounts.dat --operations tests/fixtures/cli/basic/operations.dat exits with code 0 and prints PROCESSED=, REJECTED=, and TOTAL_CENTS= lines from modern_bank/cli.py.
- Check acceptance criterion 2: Running python -m pytest tests/test_cli.py::test_cli_invokes_ledger_publisher_once exits with code 0 and asserts modern_bank.cli calls LedgerPublisher.publish exactly once after operation processing completes.
- Check acceptance criterion 3: Running python -m pytest tests/test_cli.py::test_cli_missing_operations_file_returns_nonzero exits with code 0 and asserts the modern_bank/cli.py load command returns a non-zero status without replacing tests/fixtures/cli/missing_operations/accounts.dat.

### REGRESSION-014 — Append run audit JSONL

- User Story: WO-017
- Objective: Prevent regressions in existing behavior impacted by "Append run audit JSONL".
- Expected: Story "Append run audit JSONL" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Running python -m pytest tests/test_audit.py::test_audit_writer_appends_jsonl_events exits with code 0 and asserts AuditWriter.append_event in modern_bank/audit.py appends valid JSON lines without overwriting the existing audit file.
- Check acceptance criterion 2: Running python -m pytest tests/test_audit.py::test_required_event_types_are_written exits with code 0 and asserts modern_bank/audit.py records fixture_selected, ledger_generated, and run_completed event_type values.
- Check acceptance criterion 3: Running python -m pytest tests/test_cli_audit_integration.py::test_cli_load_emits_audit_events exits with code 0 and asserts modern_bank/cli.py creates or appends audit.jsonl entries when the load command completes successfully.

### REGRESSION-015 — Document migration and rollback

- User Story: WO-018
- Objective: Prevent regressions in existing behavior impacted by "Document migration and rollback".
- Expected: Story "Document migration and rollback" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: File inspection of README.md shows a migration map section that references bank.cob offsets bank-row(1:8), bank-row(10:12), ops-row(1:1), ops-row(3:8), ops-row(12:8), and ops-row(21:12).
- Check acceptance criterion 2: File inspection of README.md shows the account ledger contract accounts.dat as IIIIIIII|BBBBBBBBBBBB and the operation feed contract operations.dat as K|SSSSSSSS|TTTTTTTT|AAAAAAAAAAAA.
- Check acceptance criterion 3: File inspection of README.md shows a rollback procedure that explicitly references accounts.tmp, accounts.dat, operations.dat, retaining original inputs, discarding generated modern output, and rerunning the COBOL baseline bank.cob.

### REGRESSION-016 — Store run artifacts metadata

- User Story: WO-021
- Objective: Prevent regressions in existing behavior impacted by "Store run artifacts metadata".
- Expected: Story "Store run artifacts metadata" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Running python -m pytest tests/test_artifacts.py::test_run_artifact_store_writes_metadata_json exits with code 0 and asserts RunArtifactStore.write_metadata in modern_bank/artifacts.py creates a run_metadata.json file.
- Check acceptance criterion 2: Running python -m pytest tests/test_artifacts.py::test_metadata_contains_internal_classification_and_retention exits with code 0 and asserts modern_bank/artifacts.py writes data_classification=Internal and retention_days greater than or equal to 365 in run_metadata.json.
- Check acceptance criterion 3: Running python -m pytest tests/test_cli_artifact_integration.py::test_cli_load_records_ledger_summary_and_audit_artifacts exits with code 0 and asserts modern_bank/cli.py records generated accounts.dat, summary output, and audit.jsonl entries in run_metadata.json.

### REGRESSION-017 — Test Fixed-Width Record Parsing

- User Story: WO-008
- Objective: Prevent regressions in existing behavior impacted by "Test Fixed-Width Record Parsing".
- Expected: Story "Test Fixed-Width Record Parsing" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Unit tests: running python -m pytest tests/test_records.py -q exits with status 0 and includes assertions in tests/test_records.py for accounts.dat rows formatted as IIIIIIII|BBBBBBBBBBBB.
- Check acceptance criterion 2: Unit tests: tests/test_records.py contains test functions that verify modern_bank/records.py extracts operation kind from row[0], source account from row[2:10], destination account from row[11:19], and amount from row[20:32] for operations.dat.
- Check acceptance criterion 3: Unit tests: tests/test_records.py asserts malformed account rows with a missing pipe at character position 9 and malformed operation rows with non-numeric 12-character amount text are rejected by modern_bank/records.py without floating-point conversion.

### REGRESSION-018 — Commit Golden Parity Fixture Catalog

- User Story: WO-009
- Objective: Prevent regressions in existing behavior impacted by "Commit Golden Parity Fixture Catalog".
- Expected: Story "Commit Golden Parity Fixture Catalog" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Mock data and fixtures: tests/fixtures/golden contains 13 category directories named valid_deposit, valid_withdrawal, valid_transfer, malformed_row, insufficient_funds, missing_source, missing_destination, self_transfer, invalid_type, non_numeric_amount, zero_amount, fixed_width_formatting, and final_totals.
- Check acceptance criterion 2: Mock data and fixtures: each tests/fixtures/golden/* directory contains accounts.dat and operations.dat files whose account rows match the IIIIIIII|BBBBBBBBBBBB shape and whose operation rows intentionally represent the named category.
- Check acceptance criterion 3: Mock data and fixtures: tests/fixtures/golden/manifest.json lists all 13 category IDs and includes expected_summary fields named processed, rejected, and total_cents for each category.

### REGRESSION-019 — Build Side-by-Side Parity Runner

- User Story: WO-019
- Objective: Prevent regressions in existing behavior impacted by "Build Side-by-Side Parity Runner".
- Expected: Story "Build Side-by-Side Parity Runner" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: System integration tests: running python -m pytest tests/test_parity_runner.py -q exits with status 0 and verifies tests/parity_runner.py creates isolated legacy and modern work directories for a fixture under tests/fixtures/golden.
- Check acceptance criterion 2: System integration tests: executing python tests/parity_runner.py --fixture tests/fixtures/golden/valid_deposit --out .tmp/parity/valid_deposit creates .tmp/parity/valid_deposit/legacy/accounts.dat and .tmp/parity/valid_deposit/modern/accounts.dat when both runners are available.
- Check acceptance criterion 3: System integration tests: .tmp/parity/valid_deposit/legacy/stdout.txt and .tmp/parity/valid_deposit/modern/stdout.txt contain captured stdout with PROCESSED=, REJECTED=, and TOTAL_CENTS= lines or the runner records a nonzero exit_code in run.json for the failing side.

### REGRESSION-020 — Gate Parity With Byte Comparisons

- User Story: WO-022
- Objective: Prevent regressions in existing behavior impacted by "Gate Parity With Byte Comparisons".
- Expected: Story "Gate Parity With Byte Comparisons" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: System integration tests: running python -m pytest tests/test_parity.py -q iterates every category listed in tests/fixtures/golden/manifest.json and invokes tests/parity_runner.py for each fixture.
- Check acceptance criterion 2: System integration tests: tests/test_parity.py asserts legacy final accounts.dat bytes equal modern final accounts.dat bytes by comparing binary reads from the legacy/accounts.dat and modern/accounts.dat artifacts.
- Check acceptance criterion 3: System integration tests: tests/test_parity.py asserts parsed PROCESSED, REJECTED, and TOTAL_CENTS values from legacy/stdout.txt equal the corresponding values from modern/stdout.txt for every fixture.

### REGRESSION-021 — Add Required Benchmark Timing Harness

- User Story: WO-023
- Objective: Prevent regressions in existing behavior impacted by "Add Required Benchmark Timing Harness".
- Expected: Story "Add Required Benchmark Timing Harness" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: System integration tests: running python benchmarks/runner.py --sizes 1200x400 5000x500 --out .tmp/benchmarks/results.json creates .tmp/benchmarks/results.json with entries for 1200x400 and 5000x500.
- Check acceptance criterion 2: System integration tests: .tmp/benchmarks/results.json contains legacy_duration_ms, modern_duration_ms, parity_status, accounts_count, operations_count, and command fields for each benchmark size.
- Check acceptance criterion 3: Unit tests: running python -m pytest tests/test_benchmark_runner.py -q exits with status 0 and verifies benchmarks/runner.py duration calculations use time.perf_counter_ns or an equivalent monotonic timer.

### REGRESSION-022 — Publish Qualified Benchmark Speedup Report

- User Story: WO-026
- Objective: Prevent regressions in existing behavior impacted by "Publish Qualified Benchmark Speedup Report".
- Expected: Story "Publish Qualified Benchmark Speedup Report" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: Unit tests: running python -m pytest tests/test_benchmark_report.py -q exits with status 0 and verifies benchmarks/report.py computes speedup from legacy_duration_ms and modern_duration_ms fields.
- Check acceptance criterion 2: System integration tests: running python benchmarks/report.py --input .tmp/benchmarks/results.json --output .tmp/benchmarks/report.md creates .tmp/benchmarks/report.md when .tmp/benchmarks/results.json contains 1200x400 and 5000x500 entries.
- Check acceptance criterion 3: System integration tests: .tmp/benchmarks/report.md contains the exact sentence Local prototype result on one host, pending independent review. beside both 28.6x at 1200x400 and 128.1x at 5000x500 when preliminary prototype labels are included.

### REGRESSION-023 — Scaffold Vite React Tailwind dashboard

- User Story: WO-004
- Objective: Prevent regressions in existing behavior impacted by "Scaffold Vite React Tailwind dashboard".
- Expected: Story "Scaffold Vite React Tailwind dashboard" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: File inspection of web/package.json shows scripts for dev, build, preview, and test or lint, with dependencies for React, Vite, and Tailwind CSS appropriate for the lightweight local dashboard.
- Check acceptance criterion 2: File inspection of web/src/App.jsx shows a React component rendering a visible synthetic prototype placeholder and no production banking claims.
- Check acceptance criterion 3: Running cd web && npm install && npm run build exits with code 0 and creates a Vite build output directory such as web/dist/.

### REGRESSION-024 — Create localhost batch API endpoints

- User Story: WO-024
- Objective: Prevent regressions in existing behavior impacted by "Create localhost batch API endpoints".
- Expected: Story "Create localhost batch API endpoints" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: File inspection of modern_bank/api.py shows a FastAPI app object and route handlers registered for GET /api/v1/fixtures and POST /api/v1/runs with Pydantic request and response models for fixture_id, mode, run_id, status, processed_count, rejected_count, total_cents, duration_ms, parity_status, artifact_refs, and audit_events.
- Check acceptance criterion 2: Running python -m pytest tests/test_api.py::test_get_fixtures_returns_catalog exits with code 0 and asserts that GET /api/v1/fixtures returns HTTP 200 with a JSON array containing at least one object with id, label, account_count, operation_count, and synthetic_prototype fields.
- Check acceptance criterion 3: Running python -m pytest tests/test_api.py::test_post_runs_starts_fixture_run exits with code 0 and asserts that POST /api/v1/runs with application/json body containing fixture_id and mode returns HTTP 202 or HTTP 200 with run_id, status, processed_count, rejected_count, total_cents, parity_status, and duration_ms fields.

### REGRESSION-025 — Return safe structured API errors

- User Story: WO-027
- Objective: Prevent regressions in existing behavior impacted by "Return safe structured API errors".
- Expected: Story "Return safe structured API errors" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: File inspection of modern_bank/api_errors.py shows an ApiError model or equivalent typed structure with errorCode, message, correlationId, and statusCode fields and no field intended to return traceback, stack, cwd, hostname, or absolute_path.
- Check acceptance criterion 2: File inspection of modern_bank/api.py shows the FastAPI app registers exception handlers from modern_bank/api_errors.py for request validation errors, known API errors, and uncaught exceptions.
- Check acceptance criterion 3: Running python -m pytest tests/test_api_errors.py::test_validation_error_shape exits with code 0 and asserts POST /api/v1/runs with missing fixture_id returns HTTP 400 or 422 with JSON keys errorCode, message, correlationId, and statusCode.

### REGRESSION-026 — Enforce allow-listed fixture identifiers

- User Story: WO-028
- Objective: Prevent regressions in existing behavior impacted by "Enforce allow-listed fixture identifiers".
- Expected: Story "Enforce allow-listed fixture identifiers" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: File inspection of modern_bank/api.py shows POST /api/v1/runs request models contain fixture_id and mode fields and do not contain path, file_path, accounts_path, operations_path, directory, or cwd request fields.
- Check acceptance criterion 2: File inspection of modern_bank/api.py shows fixture validation calls a FixtureCatalog capability or dependency before run service execution and passes only the resolved catalog fixture object or fixture ID to the run service.
- Check acceptance criterion 3: Running python -m pytest tests/test_fixture_allowlist_api.py::test_allowed_fixture_id_starts_run exits with code 0 and asserts POST /api/v1/runs using a catalog fixture ID returns HTTP 200 or HTTP 202 with the same fixture_id in the JSON body.

### REGRESSION-027 — Render batch evidence dashboard

- User Story: WO-030
- Objective: Prevent regressions in existing behavior impacted by "Render batch evidence dashboard".
- Expected: Story "Render batch evidence dashboard" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: File inspection of web/src/App.jsx shows fetch calls or an equivalent API client for GET /api/v1/fixtures and POST /api/v1/runs, with no request field named path, accounts_path, operations_path, or directory.
- Check acceptance criterion 2: Running cd web && npm run build exits with code 0 and verifies web/src/App.jsx compiles after rendering fixture selection, run status, processed_count, rejected_count, total_cents, parity_status, duration_ms, rejection_summary, and audit_events fields.
- Check acceptance criterion 3: Frontend unit test web/src/App.test.jsx::renders_run_evidence or equivalent exits with code 0 and asserts the dashboard displays status, parity, processed count, rejected count, total cents, duration, and at least one audit event from mocked API responses.

### REGRESSION-028 — Add prototype labels and focus states

- User Story: WO-032
- Objective: Prevent regressions in existing behavior impacted by "Add prototype labels and focus states".
- Expected: Story "Add prototype labels and focus states" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: File inspection of web/src/App.jsx shows the exact visible phrase Synthetic prototype or equivalent on the page header, run evidence region, artifact or audit region, and any benchmark timing region rendered by the dashboard.
- Check acceptance criterion 2: File inspection of web/src/App.jsx shows form controls for fixture selection and run start have associated label elements or aria-label attributes with accessible names referencing fixture selection and starting a synthetic run.
- Check acceptance criterion 3: Running cd web && npm run build exits with code 0 after the label and focus-state changes.

### REGRESSION-029 — Create Forge build and scan pipeline

- User Story: WO-020
- Objective: Prevent regressions in existing behavior impacted by "Create Forge build and scan pipeline".
- Expected: Story "Create Forge build and scan pipeline" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: File inspection of .forge/shipping.yml shows four top-level or named pipeline steps containing the exact identifiers build:python, build:docker, secret-scan, and dependency-scan.
- Check acceptance criterion 2: Running forge shipping validate .forge/shipping.yml exits with status code 0 and reports no YAML schema error for the .forge/shipping.yml pipeline definition.
- Check acceptance criterion 3: The .forge/shipping.yml build:python step contains a command that invokes the Python build or test entry point, including python -m pytest or an equivalent project test command, and does not modify bank.cob.

### REGRESSION-030 — Gate releases on P0 parity

- User Story: WO-025
- Objective: Prevent regressions in existing behavior impacted by "Gate releases on P0 parity".
- Expected: Story "Gate releases on P0 parity" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: The .forge/shipping.yml file contains a parity gate step after build:python and build:docker that invokes python -m pytest tests/test_parity.py or the established parity test command.
- Check acceptance criterion 2: Running python -m pytest tests/test_parity.py -q exits with status code 0 on the committed P0 fixture set and reports no failed assertion for final accounts.dat byte comparison.
- Check acceptance criterion 3: The parity gate command in .forge/shipping.yml fails with a non-zero status when tests/test_parity.py has an assertion failure for PROCESSED, REJECTED, or TOTAL_CENTS summary comparison.

### REGRESSION-031 — Capture benchmark reports in shipping

- User Story: WO-029
- Objective: Prevent regressions in existing behavior impacted by "Capture benchmark reports in shipping".
- Expected: Story "Capture benchmark reports in shipping" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: The .forge/shipping.yml file contains a benchmark artifact step that invokes python benchmarks/runner.py or the established benchmark command after the parity gate step.
- Check acceptance criterion 2: The .forge/shipping.yml benchmark step declares artifact capture paths for benchmark reports produced by benchmarks/runner.py, including a machine-readable report file path and a human-readable report file path.
- Check acceptance criterion 3: Running python benchmarks/runner.py --output artifacts/benchmarks or the repository-supported equivalent creates report files under artifacts/benchmarks for the 1200x400 and 5000x500 fixture sizes.

### REGRESSION-032 — Package evidence artifacts deterministically

- User Story: WO-031
- Objective: Prevent regressions in existing behavior impacted by "Package evidence artifacts deterministically".
- Expected: Story "Package evidence artifacts deterministically" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: The scripts/package_artifacts.sh file exists, is executable, and starts with a POSIX shell or bash shebang plus strict error handling such as set -euo pipefail.
- Check acceptance criterion 2: Running scripts/package_artifacts.sh artifacts dist/evidence.tar.gz creates dist/evidence.tar.gz and a manifest file inside the archive that lists packaged fixture, ledger, audit JSONL, parity diff, and benchmark report paths.
- Check acceptance criterion 3: Archive inspection with tar -tzf dist/evidence.tar.gz shows repository-relative entries for fixtures, ledgers or accounts.dat outputs, audit .jsonl files, parity diff files, and benchmark report files.

### REGRESSION-033 — Document rollout and rollback runbook

- User Story: WO-033
- Objective: Prevent regressions in existing behavior impacted by "Document rollout and rollback runbook".
- Expected: Story "Document rollout and rollback runbook" satisfies expected regression validation outcomes without critical issues.

**Steps**
- Check acceptance criterion 1: README.md contains a rollout runbook section that references .forge/shipping.yml, bank.cob, tests/test_parity.py, benchmarks/runner.py, and scripts/package_artifacts.sh by path.
- Check acceptance criterion 2: README.md includes a Docker execution step that names the Docker build or run command used for the prototype and explicitly states that execution uses synthetic accounts.dat and operations.dat fixtures only.
- Check acceptance criterion 3: README.md documents that python -m pytest tests/test_parity.py -q is the P0 parity command and that any mismatch in final accounts.dat, PROCESSED, REJECTED, or TOTAL_CENTS blocks sign-off.

---

## Performance test scenarios (33)

### PERFORMANCE-001 — Scaffold Python modernization package

- User Story: WO-001
- Objective: Assess performance and stability impact introduced by "Scaffold Python modernization package".
- Expected: Story "Scaffold Python modernization package" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-001.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-002 — Add reproducible COBOL baseline runner

- User Story: WO-002
- Objective: Assess performance and stability impact introduced by "Add reproducible COBOL baseline runner".
- Expected: Story "Add reproducible COBOL baseline runner" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-002.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-003 — Implement fixed-width record codec

- User Story: WO-003
- Objective: Assess performance and stability impact introduced by "Implement fixed-width record codec".
- Expected: Story "Implement fixed-width record codec" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-003.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-004 — Add fixture allow-list catalog

- User Story: WO-005
- Objective: Assess performance and stability impact introduced by "Add fixture allow-list catalog".
- Expected: Story "Add fixture allow-list catalog" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-005.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-005 — Add modern CLI contract skeleton

- User Story: WO-006
- Objective: Assess performance and stability impact introduced by "Add modern CLI contract skeleton".
- Expected: Story "Add modern CLI contract skeleton" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-006.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-006 — Build ordered ledger account index

- User Story: WO-007
- Objective: Assess performance and stability impact introduced by "Build ordered ledger account index".
- Expected: Story "Build ordered ledger account index" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-007.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-007 — Preflight account ledger validity

- User Story: WO-010
- Objective: Assess performance and stability impact introduced by "Preflight account ledger validity".
- Expected: Story "Preflight account ledger validity" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-010.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-008 — Process accepted DWT mutations

- User Story: WO-011
- Objective: Assess performance and stability impact introduced by "Process accepted DWT mutations".
- Expected: Story "Process accepted DWT mutations" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-011.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-009 — Preserve processor rejection paths

- User Story: WO-012
- Objective: Assess performance and stability impact introduced by "Preserve processor rejection paths".
- Expected: Story "Preserve processor rejection paths" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-012.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-010 — Format fixed-width batch summary

- User Story: WO-013
- Objective: Assess performance and stability impact introduced by "Format fixed-width batch summary".
- Expected: Story "Format fixed-width batch summary" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-013.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-011 — Publish ledger with safe replacement

- User Story: WO-014
- Objective: Assess performance and stability impact introduced by "Publish ledger with safe replacement".
- Expected: Story "Publish ledger with safe replacement" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-014.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-012 — Validate ledger before replacement

- User Story: WO-015
- Objective: Assess performance and stability impact introduced by "Validate ledger before replacement".
- Expected: Story "Validate ledger before replacement" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-015.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-013 — Orchestrate CLI ledger publication

- User Story: WO-016
- Objective: Assess performance and stability impact introduced by "Orchestrate CLI ledger publication".
- Expected: Story "Orchestrate CLI ledger publication" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-016.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-014 — Append run audit JSONL

- User Story: WO-017
- Objective: Assess performance and stability impact introduced by "Append run audit JSONL".
- Expected: Story "Append run audit JSONL" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-017.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-015 — Document migration and rollback

- User Story: WO-018
- Objective: Assess performance and stability impact introduced by "Document migration and rollback".
- Expected: Story "Document migration and rollback" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-018.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-016 — Store run artifacts metadata

- User Story: WO-021
- Objective: Assess performance and stability impact introduced by "Store run artifacts metadata".
- Expected: Story "Store run artifacts metadata" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-021.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-017 — Test Fixed-Width Record Parsing

- User Story: WO-008
- Objective: Assess performance and stability impact introduced by "Test Fixed-Width Record Parsing".
- Expected: Story "Test Fixed-Width Record Parsing" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-008.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-018 — Commit Golden Parity Fixture Catalog

- User Story: WO-009
- Objective: Assess performance and stability impact introduced by "Commit Golden Parity Fixture Catalog".
- Expected: Story "Commit Golden Parity Fixture Catalog" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-009.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-019 — Build Side-by-Side Parity Runner

- User Story: WO-019
- Objective: Assess performance and stability impact introduced by "Build Side-by-Side Parity Runner".
- Expected: Story "Build Side-by-Side Parity Runner" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-019.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-020 — Gate Parity With Byte Comparisons

- User Story: WO-022
- Objective: Assess performance and stability impact introduced by "Gate Parity With Byte Comparisons".
- Expected: Story "Gate Parity With Byte Comparisons" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-022.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-021 — Add Required Benchmark Timing Harness

- User Story: WO-023
- Objective: Assess performance and stability impact introduced by "Add Required Benchmark Timing Harness".
- Expected: Story "Add Required Benchmark Timing Harness" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-023.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-022 — Publish Qualified Benchmark Speedup Report

- User Story: WO-026
- Objective: Assess performance and stability impact introduced by "Publish Qualified Benchmark Speedup Report".
- Expected: Story "Publish Qualified Benchmark Speedup Report" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-026.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-023 — Scaffold Vite React Tailwind dashboard

- User Story: WO-004
- Objective: Assess performance and stability impact introduced by "Scaffold Vite React Tailwind dashboard".
- Expected: Story "Scaffold Vite React Tailwind dashboard" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-004.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-024 — Create localhost batch API endpoints

- User Story: WO-024
- Objective: Assess performance and stability impact introduced by "Create localhost batch API endpoints".
- Expected: Story "Create localhost batch API endpoints" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-024.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-025 — Return safe structured API errors

- User Story: WO-027
- Objective: Assess performance and stability impact introduced by "Return safe structured API errors".
- Expected: Story "Return safe structured API errors" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-027.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-026 — Enforce allow-listed fixture identifiers

- User Story: WO-028
- Objective: Assess performance and stability impact introduced by "Enforce allow-listed fixture identifiers".
- Expected: Story "Enforce allow-listed fixture identifiers" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-028.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-027 — Render batch evidence dashboard

- User Story: WO-030
- Objective: Assess performance and stability impact introduced by "Render batch evidence dashboard".
- Expected: Story "Render batch evidence dashboard" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-030.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-028 — Add prototype labels and focus states

- User Story: WO-032
- Objective: Assess performance and stability impact introduced by "Add prototype labels and focus states".
- Expected: Story "Add prototype labels and focus states" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-032.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-029 — Create Forge build and scan pipeline

- User Story: WO-020
- Objective: Assess performance and stability impact introduced by "Create Forge build and scan pipeline".
- Expected: Story "Create Forge build and scan pipeline" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-020.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-030 — Gate releases on P0 parity

- User Story: WO-025
- Objective: Assess performance and stability impact introduced by "Gate releases on P0 parity".
- Expected: Story "Gate releases on P0 parity" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-025.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-031 — Capture benchmark reports in shipping

- User Story: WO-029
- Objective: Assess performance and stability impact introduced by "Capture benchmark reports in shipping".
- Expected: Story "Capture benchmark reports in shipping" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-029.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-032 — Package evidence artifacts deterministically

- User Story: WO-031
- Objective: Assess performance and stability impact introduced by "Package evidence artifacts deterministically".
- Expected: Story "Package evidence artifacts deterministically" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-031.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.

### PERFORMANCE-033 — Document rollout and rollback runbook

- User Story: WO-033
- Objective: Assess performance and stability impact introduced by "Document rollout and rollback runbook".
- Expected: Story "Document rollout and rollback runbook" satisfies expected performance validation outcomes without critical issues.

**Steps**
- Identify throughput/latency-sensitive path for WO-033.
- Run benchmark/load scenario with representative input.
- Compare key metrics against baseline and acceptance thresholds.