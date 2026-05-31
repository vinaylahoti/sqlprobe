# SQLProbe — Project Status

> This file is the source of truth for current implementation reality.
> Updated after every commit.
> README.md = long-term vision. IMPLEMENTATION_PLAN.md = build plan. PROJECT_STATUS.md = what actually exists today.

---

## Current Version: v0.0.2 (in development → complete)

## Last Updated: 2026-05-31

---

## Phase 2 Status

- [x] DuckDBAdapter implemented
- [x] Execution evaluator implemented
- [x] --db flag wired in CLI
- [x] JSON report extended with execution key
- [x] fixtures/seed.sql and warehouse.db created
- [x] tests/test_duckdb_adapter.py (9 tests)
- [x] tests/test_execution_evaluator.py (12 tests)
- [x] tests/test_integration.py (9 tests)
- [x] docs/failure-modes.md written
- [x] README.md updated for v0.0.2

---

## Phase 3 Status

- [x] DimensionResult and JudgeResult added to core/result.py
- [x] compute_overall_score and compute_overall_verdict helpers added
- [x] anthropic added to judge extra and dev dependencies
- [x] SchemaAnnotation dataclass and load_annotations() implemented
- [x] build_annotation_context() implemented
- [x] schema/annotations.yaml created
- [x] tests/test_annotation_loader.py added and passing

---

## What Exists Today

### Repository Structure
- [x] Package scaffold created (`sqlprobe/` with all subdirectories)
- [x] `pyproject.toml` with correct dependencies and optional DuckDB extra
- [x] `LICENSE` (Apache 2.0)
- [x] `README.md` (v0.0.2 quickstart and current scope)
- [x] `IMPLEMENTATION_PLAN.md` (v0.0.1 build plan)
- [x] `PROJECT_STATUS.md`
- [x] `CHANGELOG.md`
- [x] YAML files for assertions and example cases
- [x] DuckDB fixture database and seed SQL

### Core
- [x] `sqlprobe/core/taxonomy.py` — all 18 failure modes, Layer, Severity, FailureModeMetadata, FAILURE_MODE_REGISTRY
- [x] `sqlprobe/core/case.py` — EvaluationCase, ExpectedOutput, ExpectedResultShape, InputContext
- [x] `sqlprobe/core/result.py` — EvaluationResult, LayerResult, AssertionFailure, ExecutionResult

### Loaders
- [x] `sqlprobe/loader/case_loader.py`
- [x] `sqlprobe/loader/assertion_loader.py`

### Evaluators
- [x] `sqlprobe/evaluators/syntax.py`
- [x] `sqlprobe/evaluators/assertions.py`
- [x] `sqlprobe/evaluators/execution.py`
- [x] `sqlprobe/evaluators/judge.py` — skipped stub for Phase 3

### Adapters
- [x] `sqlprobe/adapters/duckdb.py`

### Regression
- [x] `sqlprobe/regression/baseline.py` — skipped stub for future baseline comparison

### CLI
- [x] `sqlprobe/cli/main.py`

### Fixtures
- [x] `fixtures/seed.sql`
- [x] `fixtures/warehouse.db`
- [x] `scripts/build_fixture_db.py`

### Assertion Library (YAML)
- [x] `assertions/revenue.yaml`
- [x] `assertions/filters.yaml`
- [x] `assertions/date_handling.yaml`

### Example Cases (YAML)
- [x] `cases/examples/revenue_q1_enterprise.yaml`
- [x] `cases/examples/churn_rate_monthly.yaml`

### Tests
- [x] `tests/test_assertion_engine.py`
- [x] `tests/test_cli.py`
- [x] `tests/test_duckdb_adapter.py`
- [x] `tests/test_execution_evaluator.py`
- [x] `tests/test_integration.py`
- [x] `tests/test_package.py`
- [x] `tests/test_stubs.py`
- [x] `tests/test_syntax_evaluator.py`

### Docs
- [x] `docs/failure-modes.md`

---

## CLI Commands Status

| Command | Status |
|---|---|
| `sqlprobe validate <cases/>` | Implemented |
| `sqlprobe run <cases/>` | Implemented |
| `sqlprobe run --sql "..."` | Implemented |
| `sqlprobe run --db duckdb://...` | Implemented |
| `sqlprobe run --output report.json` | Implemented |
| `sqlprobe demo` | Implemented |
| `sqlprobe baseline create` | Not implemented |

---

## What Does NOT Exist Yet (Phase 3 And Later)

- LLM judge (`evaluators/judge.py`) — Anthropic Claude API, structured output
- Result assertions (checked against execution output, e.g. `churn_rate_bounded`)
- Baseline pinning and regression detection
- Semantic schema annotations
- dbt importer
- CI/CD workflow
- PyPI publishing

---

## Known Issues

None yet.

---

## Next Up

- Phase 3: LLM judge — see `SQLPROBE_PHASE2_CONTEXT.md` for Phase 3 scope

---
