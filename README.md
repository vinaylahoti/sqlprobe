# SQLProbe

Production trust layer for AI-generated SQL.

SQLProbe is an open source evaluation harness for NL-to-SQL systems. It does not generate SQL. It checks generated SQL against versioned evaluation cases, assertion rules, and optional execution evidence so teams can catch production-style correctness failures before a wrong number reaches a report.

## Current Release Scope

This repository is currently at `v0.0.3`. The implemented release includes:

- YAML evaluation case loading
- YAML assertion loading
- SQL syntax validation with `sqlglot`
- Structural assertion checks against SQL text and AST
- DuckDB execution adapter for local fixture databases
- Result shape evaluation for row counts, value ranges, null checks, and column presence
- Result assertions against actual query output
- Optional LLM judge evaluation with Claude
- Optional schema annotations for judge context
- Failure mode taxonomy
- Typer CLI with `validate`, `run`, `demo`, `run --db`, `run --judge`, and `run --annotations`
- JSON report output for `run`, including execution and judge results

## What's New in v0.0.2

- DuckDB execution adapter: run generated SQL against a local database
- Result shape evaluation: row count, value ranges, null checks, column presence
- `--db` flag on `sqlprobe run`: `sqlprobe run cases/ --db duckdb://./fixtures/warehouse.db`
- JSON report now includes execution layer results
- 18-failure-mode reference: see `docs/failure-modes.md`

## What's New in v0.0.3

- LLM judge: semantic and business dimension evaluation via Claude
- `--judge` flag: `sqlprobe run cases/ --db duckdb://./fixtures/warehouse.db --judge`
- `--annotations` flag: inject schema context into the judge
- Result assertions: check conditions against actual query output
- 11 additional failure modes now detectable (previously required human review)
- Judge is additive: evaluation pipeline works without it

The following are planned but not implemented:

- Baseline and regression comparison
- Semantic schema annotation import from dbt or catalogs
- dbt or catalog importers
- Trace store
- PyPI release

## Requirements

- Python 3.10+
- No database required for syntax and structural assertion checks
- DuckDB optional extra or development install required for `--db`
- No LLM API key required unless using `--judge`

## Install From Source

```bash
git clone https://github.com/vinaylahoti/sqlprobe.git
cd sqlprobe
python -m venv .venv
```

Activate the virtual environment:

```bash
# macOS/Linux
source .venv/bin/activate

# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

Install:

```bash
pip install -e .
```

For DuckDB execution support:

```bash
pip install -e ".[duckdb]"
```

For development and tests:

```bash
pip install -e ".[dev]"
```

If the `sqlprobe` command is not on your shell `PATH`, use the module entrypoint:

```bash
python -m sqlprobe.cli.main --help
```

## Quickstart

Validate the bundled example cases:

```bash
sqlprobe validate cases/examples
```

Expected output:

```text
OK   churn_rate_monthly
OK   revenue_q1_enterprise
```

Run the bundled examples using each case's expected SQL:

```bash
sqlprobe run cases/examples
```

Expected output:

```text
PASS  churn_rate_monthly
PASS  revenue_q1_enterprise
Cases: 2
Passed: 2
Failed: 0
Critical: 0
```

Run the bundled examples against the local DuckDB fixture database:

```bash
sqlprobe run cases/examples --db duckdb://./fixtures/warehouse.db
```

Expected output:

```text
PASS  churn_rate_monthly
PASS  revenue_q1_enterprise
Cases: 2
Passed: 2
Failed: 0
Critical: 0
Execution: ran against duckdb://./fixtures/warehouse.db
```

Run the demo:

```bash
sqlprobe demo
```

Expected output:

```text
Demo: failing SQL
FAIL  revenue_q1_enterprise
  Failure Mode: MISSING_BUSINESS_FILTER
  Assertion: revenue_excludes_test_accounts
  Detail: Expected filter not found: accounts.is_test = False
  Failure Mode: COLUMN_SUBSTITUTION
  Assertion: no_amount_for_revenue
  Detail: Excluded column found: amount
Cases: 1
Passed: 0
Failed: 1
Critical: 1
Demo: corrected SQL
PASS  revenue_q1_enterprise
Cases: 1
Passed: 1
Failed: 0
Critical: 0
```

Generate a JSON report:

```bash
sqlprobe run cases/examples --output report.json
```

Example report:

```json
[
  {
    "case_id": "churn_rate_monthly",
    "passed": true,
    "failure_modes": [],
    "execution": { "ran": false },
    "judge": { "ran": false }
  },
  {
    "case_id": "revenue_q1_enterprise",
    "passed": true,
    "failure_modes": [],
    "execution": { "ran": false },
    "judge": { "ran": false }
  }
]
```

Generate a JSON report with execution results:

```bash
sqlprobe run cases/examples --db duckdb://./fixtures/warehouse.db --output report.json
```

## Example Case

```yaml
id: revenue_q1_enterprise
version: "1.0"
description: "Recognized revenue from enterprise segment, fiscal Q1 2024"

input:
  question: "What was total recognized revenue from enterprise customers in Q1 2024?"
  context:
    fiscal_year_start: february
    user_role: finance_analyst

expected:
  sql: |
    SELECT SUM(t.net_revenue) AS net_revenue_sum
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
      net_revenue_sum:
        min: 1000000
        max: 50000000

assertions:
  - revenue_excludes_test_accounts
  - no_amount_for_revenue
  - no_created_at_for_revenue
  - revenue_no_select_star

tags: [revenue, enterprise, fiscal, finance]
status: active
```

## Example Assertion

```yaml
- id: revenue_excludes_test_accounts
  description: "Revenue queries must always filter out test/demo accounts"
  trigger:
    sql_references_any:
      - "transactions.amount"
      - "amount"
      - "net_revenue"
      - "mrr"
      - "arr"
      - "revenue"
  assert:
    sql_contains_filter:
      column: "accounts.is_test"
      operator: "="
      value: false
  severity: critical
  failure_mode: MISSING_BUSINESS_FILTER
```

## CLI

```bash
sqlprobe --help
sqlprobe validate cases/examples
sqlprobe run cases/examples
sqlprobe run cases/examples --db duckdb://./fixtures/warehouse.db
sqlprobe run cases/examples --judge
sqlprobe run cases/examples --judge --annotations schema/annotations.yaml
sqlprobe run cases/examples/revenue_q1_enterprise.yaml --sql "SELECT SUM(amount) FROM transactions t JOIN accounts a ON t.account_id = a.id WHERE a.segment = 'enterprise'"
sqlprobe run cases/examples --output report.json
sqlprobe run cases/examples --db duckdb://./fixtures/warehouse.db --output report.json
sqlprobe run cases/examples/revenue_q1_enterprise.yaml --sql "SELECT SUM(amount) FROM transactions t JOIN accounts a ON t.account_id = a.id WHERE a.segment = 'enterprise'" --fail-on critical
sqlprobe demo
```

`--fail-on critical` exits with status code `1` when any critical failure is present.

## Architecture

```text
sqlprobe/
  core/
    taxonomy.py         FailureMode, Layer, Severity metadata
    case.py             EvaluationCase dataclasses
    result.py           EvaluationResult and ExecutionResult dataclasses
  loader/
    case_loader.py      YAML case loading
    assertion_loader.py YAML assertion loading
  evaluators/
    syntax.py           sqlglot syntax validation
    assertions.py       structural assertion engine
    execution.py        result shape evaluation
    judge.py            optional Claude judge; requires --judge and ANTHROPIC_API_KEY
  adapters/
    duckdb.py           DuckDB execution adapter
  regression/
    baseline.py         stub for future baseline comparison
  cli/
    main.py             Typer CLI
fixtures/
  seed.sql              fixture schema and seed data
  warehouse.db          committed DuckDB fixture database
```

## Failure Modes

SQLProbe defines 18 failure modes across four layers:

- Syntax: `DIALECT_MISMATCH`, `NONEXISTENT_OBJECT`
- Execution: `CARDINALITY_EXPLOSION`, `SILENT_EMPTY`, `TYPE_MISMATCH_COERCION`, `NULL_PROPAGATION`
- Semantic: `WRONG_GRAIN`, `WRONG_DATE_BOUNDARY`, `MISSING_FILTER`, `SPURIOUS_FILTER`, `WRONG_AGGREGATION`, `COLUMN_SUBSTITUTION`, `DECOMPOSITION_FAILURE`
- Business: `METRIC_DEFINITION_VIOLATION`, `MISSING_BUSINESS_FILTER`, `CALENDAR_VIOLATION`, `SCOPE_VIOLATION`, `STALE_LOGIC`

See `docs/failure-modes.md` for detection status and examples.

## Development

```bash
pip install -e ".[dev]"
pytest -v
pytest --cov=sqlprobe --cov-report=term-missing
```

Regenerate the fixture database:

```bash
python scripts/build_fixture_db.py
```

## Project Documents

- `IMPLEMENTATION_PLAN.md`: planned v0.0.1 implementation sequence
- `PROJECT_STATUS.md`: current implementation reality
- `CHANGELOG.md`: notable changes
- `RELEASE_CHECKLIST.md`: release readiness checklist
- `docs/failure-modes.md`: failure mode reference

## License

Apache 2.0. See `LICENSE`.
