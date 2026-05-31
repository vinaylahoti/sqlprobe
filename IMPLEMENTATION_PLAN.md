# SQLProbe Implementation Plan

## Vision Alignment

SQLProbe is the production trust layer for NL-to-SQL systems described in the README. It does not generate SQL, replace an analytics pipeline, or act as a benchmark leaderboard. It evaluates generated SQL against explicit correctness contracts and returns structured evidence about whether the query is safe to trust.

The README describes the long-term product: syntax checks, execution checks, semantic checks, business assertions, conditional LLM judging, regression detection, semantic annotations, tracing, and integrations. This v0.0.1 plan implements the smallest useful slice of that vision: a local, dependency-light evaluation harness that can load YAML cases, parse SQL, run structural assertions, and report named failure modes without a database, without an LLM, and without hosted infrastructure.

For v0.0.1, README alignment is resolved as follows:

- The authoritative product vision remains the README.
- The authoritative v0.0.1 implementation scope is this document.
- Features described in the README but outside the v0.0.1 contract must exist only as stubs or future work.
- The first release version is `0.0.1`, even though the README contains broader package and roadmap references.

## v0.0.1 Scope

The v0.0.1 contract:

A data engineer can write an evaluation case in YAML, point SQLProbe at generated SQL, and get a structured pass/fail report with named failure modes without a database, without an LLM, and without external services.

The release proves:

- The data model is correct enough to build on.
- The CLI is usable for local validation.
- The structural assertion engine can detect real production SQL failure patterns.
- Failure reports are structured, named, and actionable.

Implemented in v0.0.1:

| Component | Decision | Rationale |
| --- | --- | --- |
| `EvaluationCase` | Implement | Core data model. All evaluation behavior depends on it. |
| YAML case loader | Implement | Required to run cases from repository files. |
| YAML assertion loader | Implement | Required to load built-in and user-defined assertions. |
| SQL syntax parser | Implement | Use `sqlglot` for dialect-aware parsing with zero service dependencies. |
| Structural assertion engine | Implement | Highest-value v0.0.1 feature. AST-based and database-free. |
| Failure taxonomy | Implement | Constants and metadata make output meaningful and stable. |
| CLI | Implement | Provide `validate`, `run`, and `demo` as the primary user interface. |
| DuckDB integration | Stub | Real value, but execution fixtures are outside v0.0.1. |
| Baseline and regression | Stub | Depends on execution and persisted result history. |
| LLM judge | Stub | Depends on multi-layer evaluation and provider configuration. |
| Trace store | Stub | Depends on the full pipeline and observability layer. |

Package metadata for v0.0.1:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "sqlprobe"
version = "0.0.1"
description = "Production trust layer for AI-generated SQL"
readme = "README.md"
license = { file = "LICENSE" }
requires-python = ">=3.10"
dependencies = [
    "typer>=0.12.0",
    "rich>=13.0.0",
    "pyyaml>=6.0",
    "sqlglot>=23.0.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=5.0.0",
]
duckdb = ["duckdb>=0.10.0"]
llm = ["anthropic>=0.25.0", "openai>=1.0.0"]

[project.scripts]
sqlprobe = "sqlprobe.cli.main:app"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

## Non Goals

The following are out of scope for v0.0.1 and must not be implemented beyond explicit stubs:

- No LLM judge implementation.
- No database execution implementation.
- No DuckDB fixture execution path.
- No regression or baseline comparison implementation.
- No semantic annotation implementation.
- No trace store implementation.
- No hosted service, SaaS workflow, dashboard, or team workspace.
- No SQL generation.
- No chatbot wrapper.
- No benchmark leaderboard.

Stubbed components must import cleanly and communicate that the feature is planned for a later release.

## Repository Structure

The v0.0.1 repository structure:

```text
sqlprobe/
|
+-- sqlprobe/                        # Main package
|   +-- __init__.py
|   +-- core/
|   |   +-- __init__.py
|   |   +-- case.py                  # EvaluationCase dataclass
|   |   +-- result.py                # EvaluationResult dataclass
|   |   +-- taxonomy.py              # Failure mode constants + metadata
|   +-- evaluators/
|   |   +-- __init__.py
|   |   +-- syntax.py                # sqlglot syntax + dialect check
|   |   +-- execution.py             # STUB - interface only
|   |   +-- assertions.py            # Structural assertion engine
|   |   +-- judge.py                 # STUB - interface only
|   +-- adapters/
|   |   +-- __init__.py
|   |   +-- duckdb.py                # STUB - interface only
|   +-- loader/
|   |   +-- __init__.py
|   |   +-- case_loader.py           # YAML to EvaluationCase
|   |   +-- assertion_loader.py      # YAML to Assertion
|   +-- regression/
|   |   +-- __init__.py
|   |   +-- baseline.py              # STUB - interface only
|   +-- cli/
|       +-- __init__.py
|       +-- main.py                  # typer CLI entry point
|
+-- assertions/                      # Built-in assertion library
|   +-- revenue.yaml
|   +-- date_handling.yaml
|   +-- filters.yaml
|
+-- cases/                           # Example evaluation cases
|   +-- examples/
|       +-- revenue_q1_enterprise.yaml
|       +-- churn_rate_monthly.yaml
|
+-- tests/
|   +-- __init__.py
|   +-- test_case_loader.py
|   +-- test_assertion_loader.py
|   +-- test_syntax_evaluator.py
|   +-- test_assertion_engine.py
|
+-- docs/
|   +-- failure-modes.md             # Taxonomy reference from README
|
+-- pyproject.toml
+-- README.md
+-- IMPLEMENTATION_PLAN.md
+-- CONTRIBUTING.md
+-- LICENSE
+-- .github/
    +-- workflows/
        +-- ci.yml                   # pytest on push and PR
        +-- publish.yml              # PyPI release workflow
```

The package tree in the README is broader than v0.0.1. Do not add `annotations/`, `tracing/`, BigQuery, Snowflake, Redshift, or report modules in this release unless they are explicitly needed as import-only stubs. The v0.0.1 structure above is the implementation target.

## Core Components

### Failure Taxonomy

Implement `sqlprobe/core/taxonomy.py` first. Every result and assertion imports it.

Required enums:

- `Layer`: `syntax`, `execution`, `semantic`, `business`.
- `Severity`: `critical`, `warning`, `info`.
- `FailureMode`: all failure modes listed in the README.

Required failure modes:

| Code | Layer |
| --- | --- |
| `DIALECT_MISMATCH` | Syntax |
| `NONEXISTENT_OBJECT` | Syntax |
| `CARDINALITY_EXPLOSION` | Execution |
| `SILENT_EMPTY` | Execution |
| `TYPE_MISMATCH_COERCION` | Execution |
| `NULL_PROPAGATION` | Execution |
| `WRONG_GRAIN` | Semantic |
| `WRONG_DATE_BOUNDARY` | Semantic |
| `MISSING_FILTER` | Semantic |
| `SPURIOUS_FILTER` | Semantic |
| `WRONG_AGGREGATION` | Semantic |
| `COLUMN_SUBSTITUTION` | Semantic |
| `DECOMPOSITION_FAILURE` | Semantic |
| `METRIC_DEFINITION_VIOLATION` | Business |
| `MISSING_BUSINESS_FILTER` | Business |
| `CALENDAR_VIOLATION` | Business |
| `SCOPE_VIOLATION` | Business |
| `STALE_LOGIC` | Business |

`FAILURE_MODE_REGISTRY` must contain `FailureModeMetadata` for all 18 modes. Metadata must include:

- `code`
- `layer`
- `description`
- `actionable`

### Evaluation Case Datamodel

Implement `sqlprobe/core/case.py` with plain dataclasses. Do not use Pydantic in v0.0.1 datamodels.

Required dataclasses:

- `ExpectedResultShape`
- `ExpectedOutput`
- `InputContext`
- `EvaluationCase`

Required `EvaluationCase` fields:

- `id`
- `version`
- `question`
- `expected`
- `context`
- `assertions`
- `tags`
- `created_at`
- `created_by`
- `status`
- `schema_snapshot_id`
- `description`

`status` defaults to `active`. Mutable defaults must use `field(default_factory=...)`.

### Evaluation Result Datamodel

Implement `sqlprobe/core/result.py` with plain dataclasses.

Required dataclasses:

- `AssertionFailure`
- `LayerResult`
- `EvaluationResult`

`EvaluationResult` must include optional layer slots:

- `syntax`
- `execution`
- `semantic`
- `business`

It must also include:

- `case_id`
- `generated_sql`
- `passed`
- `failure_modes`
- `overall_severity`
- `summary_line()`

`summary_line()` returns a compact formatted result such as:

```text
PASS  revenue_q1_enterprise
FAIL  revenue_q1_enterprise  [MISSING_BUSINESS_FILTER]
```

ASCII output is acceptable for v0.0.1. Rich may add color in CLI output.

### YAML Loaders

Implement:

- `sqlprobe/loader/case_loader.py`
- `sqlprobe/loader/assertion_loader.py`

Case loader requirements:

- `load_case(path)` parses one YAML file into `EvaluationCase`.
- `load_cases_from_dir(directory)` recursively loads `*.yaml`.
- Required top-level fields are `id`, `version`, `input`, and `expected`.
- Missing required fields raise `ValueError` with a helpful message.
- Unknown fields are ignored for forward compatibility.
- `input.question` maps to `EvaluationCase.question`.
- `input.context` maps known fields to `InputContext` and unknown context keys to `extras`.
- `expected.sql`, `expected.result_shape`, and `expected.intent_components` are supported.

Assertion loader requirements:

- `load_assertions_from_dir(directory)` recursively loads `*.yaml`.
- Assertion YAML may contain either one assertion mapping or a list of assertion mappings.
- Assertion trigger fields:
  - `sql_references_any`
  - `question_contains_any`
  - `question_not_contains`
- Assertion check fields:
  - `sql_contains_filter`
  - `sql_excludes_column`
  - `requires_column`
  - `aggregation_type`
  - `no_select_star`
- `failure_mode` must parse to `FailureMode`.
- `severity` defaults to `warning`.
- `on_failure` defaults to `fail`.

### Syntax Evaluator

Implement `sqlprobe/evaluators/syntax.py`.

Requirements:

- Use `sqlglot.parse()` with `error_level=sqlglot.ErrorLevel.RAISE`.
- Supported dialects: `ansi`, `bigquery`, `snowflake`, `redshift`, `duckdb`, `postgres`, `mysql`, `spark`, `trino`.
- Valid SQL returns `LayerResult(layer=Layer.SYNTAX, passed=True)`.
- Invalid SQL returns `passed=False` with `DIALECT_MISMATCH`.
- Empty SQL returns `passed=False`.
- Syntax evaluation does not validate whether tables or columns exist.

### Structural Assertion Engine

Implement `sqlprobe/evaluators/assertions.py`. This is the highest-priority v0.0.1 component.

Requirements:

- Parse SQL with `sqlglot.parse_one()`.
- Match assertion triggers before running assertion checks.
- Unknown assertion IDs produce a warning failure and do not crash.
- Trigger matching checks SQL text and question text case-insensitively.
- `sql_contains_filter` walks the SQL AST and detects comparison nodes such as `EQ`, `NEQ`, `GT`, `LT`, `GTE`, and `LTE`.
- Filter detection must match both bare column names and `table.column` names.
- Boolean values must handle `exp.Boolean`.
- String and numeric values must handle `exp.Literal`.
- `no_select_star` detects `SELECT *`.
- `requires_column` detects required column references in SQL text.
- `sql_excludes_column` fails when disallowed column references appear in SQL text.
- `aggregation_type` checks for required aggregate usage where implemented.
- Built-in assertions must run against example cases without requiring a database.

Layer placement for v0.0.1:

- Structural assertions may return `Layer.BUSINESS` when enforcing business rules.
- This matches the README: business correctness is encoded as explicit assertions.

### CLI

Implement `sqlprobe/cli/main.py` using Typer and Rich.

Commands:

- `sqlprobe --help`
- `sqlprobe validate <path>`
- `sqlprobe run <path>`
- `sqlprobe demo`

`validate` requirements:

- Accept a case file or case directory.
- Load case YAML.
- Load built-in assertions.
- Print `OK`, `WARN`, or `ERR` per file.
- Exit `0` when all files are valid.
- Exit non-zero when any file cannot be parsed.

`run` requirements:

- Accept a case file or case directory.
- Load assertions from built-in `assertions/` or a `--assertions` override.
- Use `expected.sql` as generated SQL when `--sql` is not provided.
- Use inline generated SQL when `--sql` is provided.
- Run syntax evaluation and structural assertion evaluation for each case.
- Do not run execution or judge logic except as skipped stubs.
- Print colored PASS/FAIL results with failure mode, assertion ID, and detail.
- Print a summary line with pass, fail, and critical counts.
- Support `--dialect`.
- Support `--output report.json` and write valid JSON.
- Support `--fail-on critical` and exit `1` when critical failures exist.
- `--help` must be accurate for every command.

`demo` requirements:

- Run the built-in revenue example with failing SQL.
- Show named failures for missing test-account filtering and wrong revenue column.
- Run or display the corrected SQL path that passes.

### Future Stubs

Implement importable stubs only:

- `sqlprobe/evaluators/execution.py`
- `sqlprobe/evaluators/judge.py`
- `sqlprobe/adapters/duckdb.py`
- `sqlprobe/regression/baseline.py`

Stub requirements:

- Import cleanly from the CLI.
- Include docstrings explaining the future implementation.
- Return skipped `LayerResult` where an evaluator interface exists.
- Raise `NotImplementedError` with descriptive messages where an adapter or baseline operation is called directly.

## Built-in Assertions

Create exactly these built-in assertion files for v0.0.1:

- `assertions/revenue.yaml`
- `assertions/filters.yaml`
- `assertions/date_handling.yaml`

### `assertions/revenue.yaml`

Contains two assertions.

`revenue_excludes_test_accounts`:

- Description: revenue queries must filter out test or demo accounts.
- Trigger: SQL references revenue-like fields such as `transactions.amount`, `net_revenue`, `mrr`, or `arr`.
- Check: SQL contains `accounts.is_test = false`.
- Severity: `critical`.
- Failure mode: `MISSING_BUSINESS_FILTER`.

`revenue_no_select_star`:

- Description: revenue queries must not use `SELECT *`; column selection must be explicit.
- Trigger: SQL references revenue-like fields such as `revenue`, `mrr`, `arr`, or `net_revenue`.
- Check: `no_select_star: true`.
- Severity: `warning`.
- Failure mode: `COLUMN_SUBSTITUTION`.

### `assertions/filters.yaml`

Contains one assertion.

`require_explicit_date_filter`:

- Description: queries referencing time-series tables must include a date filter.
- Trigger: SQL references time-series tables such as `transactions`, `events`, `sessions`, or `orders`, and the question contains time language such as last, this, quarter, month, year, Q1, Q2, Q3, or Q4.
- Check: requires a date-like column reference.
- Severity: `warning`.
- Failure mode: `WRONG_DATE_BOUNDARY`.

### `assertions/date_handling.yaml`

Contains one assertion.

`no_created_at_for_revenue`:

- Description: recognized revenue queries must not use gross transaction amount or `created_at` for revenue timing.
- Trigger: SQL or question indicates revenue or recognized revenue.
- Check: SQL excludes `created_at` for recognized revenue windows and excludes gross `amount` when the expected metric is recognized revenue.
- Severity: `warning`.
- Failure mode: `COLUMN_SUBSTITUTION`.

The source build plan places this assertion in `date_handling.yaml`, while its demo requires the assertion to catch the README's wrong-column example. Implement it so the failing demo SQL produces the promised `COLUMN_SUBSTITUTION` failure for `amount` while still enforcing `created_at` avoidance.

All assertion IDs referenced by example cases must exist in the built-in assertion registry.

## Example Cases

Create example cases under `cases/examples/`.

### `cases/examples/revenue_q1_enterprise.yaml`

Purpose: demonstrate the README's core failure mode: generated SQL runs and returns a number, but violates the organization's revenue definition.

Required fields:

```yaml
id: revenue_q1_enterprise
version: "1.0"
description: "Q1 enterprise recognized revenue must use fiscal Q1, net revenue, and exclude test accounts"

input:
  question: "What was total recognized revenue from enterprise customers in Q1 2024?"
  context:
    fiscal_year_start: february
    user_role: finance_analyst

expected:
  sql: |
    SELECT SUM(t.net_revenue)
    FROM transactions t
    JOIN accounts a ON t.account_id = a.id
    WHERE a.segment IN ('ENT', 'ENTERPRISE')
      AND a.is_test = false
      AND t.recognized_at >= '2024-02-01'
      AND t.recognized_at < '2024-05-01'
      AND t.status = 'recognized'
  result_shape:
    row_count: 1
    value_range:
      net_revenue_sum: { min: 1000000, max: 50000000 }
  intent_components:
    metric: recognized revenue
    segment_filter: enterprise
    time_scope: fiscal Q1 2024
    grain: total aggregate

assertions:
  - revenue_excludes_test_accounts
  - no_created_at_for_revenue
  - revenue_no_select_star

tags: [revenue, enterprise, fiscal, finance]
created_at: "2024-01-15"
created_by: analytics-team
status: active
```

### `cases/examples/churn_rate_monthly.yaml`

Purpose: demonstrate non-revenue analytical checks and date-filter expectations.

Required fields:

```yaml
id: churn_rate_monthly
version: "1.0"
description: "Monthly churn rate must use active subscriptions as denominator"

input:
  question: "What is our monthly churn rate for the last 3 months?"
  context:
    user_role: growth_analyst

expected:
  sql: |
    SELECT
      DATE_TRUNC('month', cancelled_at) AS month,
      COUNT(*) * 1.0 / NULLIF(
        (SELECT COUNT(*) FROM subscriptions WHERE status = 'active'), 0
      ) AS churn_rate
    FROM subscriptions
    WHERE cancelled_at >= CURRENT_DATE - INTERVAL '3 months'
      AND status = 'cancelled'
    GROUP BY 1
    ORDER BY 1

assertions:
  - revenue_no_select_star
  - require_explicit_date_filter

tags: [churn, subscriptions, growth]
status: active
```

## CLI Commands

Initial setup:

```bash
pip install -e .
```

Validate case files without generated SQL:

```bash
sqlprobe validate cases/examples/
```

Run cases using each case's `expected.sql` as generated SQL:

```bash
sqlprobe run cases/examples/
```

Run a specific case with inline generated SQL:

```bash
sqlprobe run cases/examples/revenue_q1_enterprise.yaml \
  --sql "SELECT SUM(amount) FROM transactions t JOIN accounts a ON t.account_id = a.id WHERE a.segment = 'enterprise'"
```

Run with BigQuery dialect:

```bash
sqlprobe run cases/examples/ --dialect bigquery
```

Write a JSON report:

```bash
sqlprobe run cases/examples/ --output report.json
```

CI mode: fail on critical failures:

```bash
sqlprobe run cases/examples/ --fail-on critical
```

Run the built-in demo:

```bash
sqlprobe demo
```

Expected failing demo SQL:

```sql
SELECT SUM(amount)
FROM transactions t
JOIN accounts a ON t.account_id = a.id
WHERE a.segment = 'enterprise'
```

Expected failing demo output characteristics:

- Result is `FAIL`.
- Exactly two critical failures are shown for `revenue_q1_enterprise`.
- Failures include `MISSING_BUSINESS_FILTER` and `COLUMN_SUBSTITUTION`.
- Failure detail states that `accounts.is_test = false` is missing.
- Failure detail states that `amount` is wrong for recognized revenue and `net_revenue` is expected.

Expected corrected SQL:

```sql
SELECT SUM(t.net_revenue)
FROM transactions t
JOIN accounts a ON t.account_id = a.id
WHERE a.segment IN ('ENT', 'ENTERPRISE')
  AND a.is_test = false
  AND t.recognized_at >= '2024-02-01'
  AND t.recognized_at < '2024-05-01'
```

Expected corrected demo output characteristics:

- Result is `PASS`.
- Summary reports 1 passed, 0 failed, 0 critical.

## Day 1

The task ordering below is authoritative for v0.0.1. Keep this order unless a task is split into smaller implementation commits.

### Task 1.1: Repository Scaffold

Purpose: establish a runnable Python package.

Complexity: Low.

Estimated time: 30 minutes.

Dependencies: none.

Implementation:

- Create the package and directory structure in this document.
- Create `pyproject.toml` with the v0.0.1 dependencies.
- Create all `__init__.py` files.
- Create a minimal Typer CLI in `sqlprobe/cli/main.py`.
- `sqlprobe --help` should print the application help and identify SQLProbe as the production trust layer for AI-generated SQL.
- Do not implement evaluation logic yet.

Acceptance criteria:

- `pip install -e .` completes without error.
- `sqlprobe --help` prints app help text.
- All package directories exist with `__init__.py`.
- `pytest tests/` runs without collection errors, even if there are no tests yet.

### Task 1.2: Failure Taxonomy

Purpose: create shared constants used by cases, assertions, evaluators, and reports.

Complexity: Low.

Estimated time: 30 minutes.

Dependencies: Task 1.1.

Implementation:

- Implement `sqlprobe/core/taxonomy.py`.
- Include all 18 README failure modes.
- Include layer and severity enums.
- Include `FailureModeMetadata`.
- Include `FAILURE_MODE_REGISTRY` metadata for all 18 modes.

Acceptance criteria:

- `from sqlprobe.core.taxonomy import FailureMode, Layer, Severity` works.
- All 18 failure modes from the README are present as enum values.
- `FAILURE_MODE_REGISTRY` contains metadata for every failure mode.

### Task 1.3: EvaluationCase and EvaluationResult Datamodels

Purpose: define the core data contract for the system.

Complexity: Low.

Estimated time: 45 minutes.

Dependencies: Task 1.2.

Implementation:

- Implement `sqlprobe/core/case.py`.
- Implement `sqlprobe/core/result.py`.
- Use Python dataclasses with `field()` for mutable defaults.
- Keep fields aligned with the YAML case schema.
- Do not introduce Pydantic validation in v0.0.1 datamodels.

Acceptance criteria:

- Both modules import without error.
- All fields match the YAML case schema described here.
- `EvaluationResult.summary_line()` returns a formatted status string.
- `EvaluationResult` has optional `syntax`, `execution`, `semantic`, and `business` layer slots.

### Task 1.4: YAML Loaders

Purpose: load evaluation cases and assertion contracts from repository files.

Complexity: Medium.

Estimated time: 1 hour.

Dependencies: Tasks 1.2 and 1.3.

Implementation:

- Implement `sqlprobe/loader/case_loader.py`.
- Implement `sqlprobe/loader/assertion_loader.py`.
- Write loader tests in `tests/test_case_loader.py`.

Acceptance criteria:

- `load_case(path)` correctly parses the two example cases.
- `load_assertions_from_dir(dir)` correctly parses all three assertion files.
- Missing required fields raise `ValueError` with a helpful message.
- Unknown fields in YAML are ignored.
- Tests verify valid case loading, missing `id` failure, and valid failure mode parsing for assertions.

### Task 1.5: Built-in Assertion Files and Example Cases

Purpose: provide runnable data for validation, examples, and the demo.

Complexity: Low.

Estimated time: 45 minutes.

Dependencies: Task 1.4.

Implementation:

- Create `assertions/revenue.yaml`.
- Create `assertions/filters.yaml`.
- Create `assertions/date_handling.yaml`.
- Create `cases/examples/revenue_q1_enterprise.yaml`.
- Create `cases/examples/churn_rate_monthly.yaml`.

Acceptance criteria:

- All three built-in assertion files load without error.
- Both example cases load without error.
- All assertion IDs referenced in example cases exist in the built-in assertion registry.
- This validation command works:

```bash
python -c "from sqlprobe.loader.case_loader import load_cases_from_dir; from pathlib import Path; cases = load_cases_from_dir(Path('cases/examples')); print(len(cases), 'cases loaded')"
```

### Day 2: Core Evaluators

#### Task 2.1: Syntax Evaluator

Purpose: deliver the first working evaluation layer and prove `sqlglot` integration.

Complexity: Low.

Estimated time: 1 hour.

Dependencies: Tasks 1.2 and 1.3.

Acceptance criteria:

- Valid SQL returns `LayerResult(passed=True)`.
- Invalid SQL returns `passed=False` with `DIALECT_MISMATCH`.
- BigQuery-specific syntax passes under `dialect=bigquery`.
- Empty SQL returns `passed=False`.
- SQL with a nonexistent table still passes syntax evaluation.
- `tests/test_syntax_evaluator.py` covers at least 5 cases.

#### Task 2.2: Structural Assertion Engine

Purpose: implement the most important v0.0.1 feature.

Complexity: High.

Estimated time: 2 hours.

Dependencies: Tasks 1.4 and 2.1.

Acceptance criteria:

- `_triggers_match` gates assertions based on SQL and question content.
- `sql_contains_filter` detects `AND a.is_test = false` in the AST.
- `sql_contains_filter` fails when the filter is absent.
- `no_select_star` detects `SELECT *`.
- `requires_column` detects column presence in SQL text.
- All four built-in assertions run correctly against example cases.
- `tests/test_assertion_engine.py` covers at least 8 cases.
- Tests include matching filter, missing filter, `SELECT *`, skipped trigger, and unknown assertion ID warning.

#### Task 2.3: Stub Remaining Evaluators

Purpose: keep the CLI importable while preserving future extension points.

Complexity: Low.

Estimated time: 30 minutes.

Dependencies: Tasks 1.2 and 1.3.

Acceptance criteria:

- `evaluate_execution()` imports without error.
- `evaluate_with_judge()` imports without error.
- Both evaluator stubs return skipped results or skipped dictionaries.
- Stub docstrings explain future behavior and requirements.
- `duckdb.py` and `baseline.py` import cleanly and raise descriptive `NotImplementedError` when called.

### Day 3: CLI and Demo

#### Task 3.1: Full CLI Implementation

Purpose: make SQLProbe usable from the command line.

Complexity: Medium.

Estimated time: 1.5 hours.

Dependencies: all Day 1 and Day 2 tasks.

Acceptance criteria:

- `sqlprobe validate cases/examples/` prints `OK`, `WARN`, or `ERR` per file and exits `0` when valid.
- `sqlprobe run cases/examples/` runs all cases against expected SQL and prints results.
- `sqlprobe run <case> --sql "..."` evaluates inline SQL against the case.
- `sqlprobe run cases/ --output report.json` writes valid JSON.
- `sqlprobe run cases/ --fail-on critical` exits `1` when critical failures exist.
- Rich output includes colored PASS/FAIL, structured failure detail, and summary.
- `--help` output is accurate for every command.

#### Task 3.2: End-to-End Demo Validation

Purpose: ensure the first-time-user experience is reliable.

Complexity: Low.

Estimated time: 45 minutes.

Dependencies: Task 3.1.

Acceptance criteria:

- Failing SQL against `revenue_q1_enterprise.yaml` shows exactly 2 failures with correct failure modes.
- Correct SQL shows `PASS`.
- `sqlprobe validate cases/examples/` exits `0` with all files valid.
- `sqlprobe run cases/examples/ --output /tmp/report.json` writes valid parseable JSON.
- All commands work after a fresh `pip install -e .`.

Demo validation script expectations:

```bash
sqlprobe validate cases/examples/
sqlprobe run cases/examples/revenue_q1_enterprise.yaml --sql "SELECT SUM(amount) FROM transactions t JOIN accounts a ON t.account_id = a.id WHERE a.segment = 'enterprise'"
sqlprobe run cases/examples/revenue_q1_enterprise.yaml --sql "SELECT SUM(t.net_revenue) FROM transactions t JOIN accounts a ON t.account_id = a.id WHERE a.segment IN ('ENT','ENTERPRISE') AND a.is_test = false AND t.recognized_at >= '2024-02-01' AND t.recognized_at < '2024-05-01'"
sqlprobe run cases/examples/ --output /tmp/sqlprobe_demo.json
```

### Day 4: Tests and Polish

#### Task 4.1: Test Suite and CI

Purpose: prevent future agents and contributors from breaking core behavior.

Complexity: Medium.

Estimated time: 1.5 hours.

Dependencies: all previous tasks.

Acceptance criteria:

- `pytest tests/ -v` passes.
- Coverage is at least 80 percent on `core/`, `loader/`, `evaluators/syntax.py`, and `evaluators/assertions.py`.
- Each core module has at least 3 tests.
- CI workflow runs tests on push and pull requests.

CI command:

```bash
pip install -e .[dev] && pytest tests/ --cov=sqlprobe --cov-report=term
```

#### Task 4.2: CONTRIBUTING and Failure Mode Docs

Purpose: make the project contribution-ready.

Complexity: Low.

Estimated time: 45 minutes.

Dependencies: Task 3.2.

Acceptance criteria:

- `CONTRIBUTING.md` explains development setup, assertion authoring, case authoring, test execution, and the PR process.
- `docs/failure-modes.md` lists all 18 failure modes with layer, description, example, and actionable guidance.
- README links to both files.

#### Task 4.3: PyPI Preparation

Purpose: make `pip install sqlprobe` viable for the README quickstart.

Complexity: Low.

Estimated time: 30 minutes.

Dependencies: Task 4.1.

Acceptance criteria:

- `python -m build` produces `.whl` and `.tar.gz` artifacts.
- Package includes `sqlprobe/`, `assertions/*.yaml`, and `cases/examples/*.yaml`.
- `pyproject.toml` includes authors, project URLs, classifiers, homepage, repository, and documentation links.
- GitHub release workflow exists and uses PyPI trusted publishing.
- Wheel verification works:

```bash
python -m build
pip install dist/*.whl
sqlprobe --help
```

### Priority Summary

| Day | Task | Complexity | Estimate | Priority |
| --- | --- | --- | --- | --- |
| Day 1 | 1.1 Repository scaffold | Low | 30m | Start here |
| Day 1 | 1.2 Failure taxonomy | Low | 30m | Required foundation |
| Day 1 | 1.3 Datamodels | Low | 45m | Required foundation |
| Day 1 | 1.4 YAML loaders | Medium | 60m | Required to run files |
| Day 1 | 1.5 Built-in data files | Low | 45m | Required for examples |
| Day 2 | 2.1 Syntax evaluator | Low | 60m | First working evaluation |
| Day 2 | 2.2 Assertion engine | High | 120m | Highest-value feature |
| Day 2 | 2.3 Stub remaining evaluators | Low | 30m | Keeps imports stable |
| Day 3 | 3.1 Full CLI | Medium | 90m | User-facing surface |
| Day 3 | 3.2 Demo validation | Low | 45m | Shareable first impression |
| Day 4 | 4.1 Test suite and CI | Medium | 90m | Trustworthy implementation |
| Day 4 | 4.2 CONTRIBUTING and docs | Low | 45m | Community readiness |
| Day 4 | 4.3 PyPI prep | Low | 30m | Installability |

If time is constrained, keep Task 2.2. The structural assertion engine is the core differentiator of v0.0.1. Tasks 4.2 and 4.3 may move to a follow-up release if needed; Task 2.2 must not be cut.
