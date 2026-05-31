# SQLProbe — Project Status

> This file is the source of truth for current implementation reality.
> Updated after every commit.
> README.md = long-term vision. IMPLEMENTATION_PLAN.md = build plan. PROJECT_STATUS.md = what actually exists today.

---

## Current Version: v0.0.1 (in development)

## Last Updated: 2026-05-31

---

## Phase 2 Status

- [x] ExecutionResult dataclass added to core/result.py
- [x] ExpectedResultShape extended with columns_present, no_nulls_in
- [x] case_loader updated to parse new fields
- [x] duckdb added to dev dependencies
- [x] fixtures/seed.sql created
- [x] fixtures/warehouse.db generated and committed
- [x] scripts/build_fixture_db.py created
- [x] DuckDBAdapter implemented in adapters/duckdb.py
- [x] tests/test_duckdb_adapter.py added and passing

---

## What Exists Today

### Repository Structure
- [x] Package scaffold created (`sqlprobe/` with all subdirectories)
- [x] `pyproject.toml` with correct dependencies
- [x] `LICENSE` (Apache 2.0)
- [x] `README.md` (v0.0.1 quickstart and current scope)
- [x] `IMPLEMENTATION_PLAN.md` (build plan)
- [x] Placeholder files for future modules
- [x] YAML files for assertions and example cases

### Core
- [x] `sqlprobe/core/taxonomy.py` — all 18 failure modes, Layer, Severity, FailureModeMetadata, FAILURE_MODE_REGISTRY
- [x] `sqlprobe/core/case.py` — EvaluationCase, ExpectedOutput, ExpectedResultShape, InputContext
- [x] `sqlprobe/core/result.py` — EvaluationResult, LayerResult, AssertionFailure

### Loaders
- [x] `sqlprobe/loader/case_loader.py`
- [x] `sqlprobe/loader/assertion_loader.py`

### Evaluators
- [x] `sqlprobe/evaluators/syntax.py`
- [x] `sqlprobe/evaluators/assertions.py`
- [x] `sqlprobe/evaluators/execution.py`
- [x] `sqlprobe/evaluators/judge.py`

### Adapters
- [x] `sqlprobe/adapters/duckdb.py`

### Regression
- [x] `sqlprobe/regression/baseline.py`

### CLI
- [x] `sqlprobe/cli/main.py`

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
- [x] `tests/test_package.py`
- [x] `tests/test_stubs.py`
- [x] `tests/test_syntax_evaluator.py`

### Docs
- [ ] `docs/failure-modes.md` — not yet implemented

---

## What Does NOT Exist Yet (Planned)

- DuckDB execution adapter
- LLM judge (Anthropic + OpenAI)
- Baseline pinning and regression detection
- Semantic schema annotations
- dbt importer
- Trace store
- CI/CD workflow
- PyPI publishing workflow

---

## CLI Commands Status

| Command | Status |
|---|---|
| `sqlprobe validate <cases/>` | Implemented |
| `sqlprobe run <cases/>` | Implemented |
| `sqlprobe run --sql "..."` | Implemented |
| `sqlprobe demo` | Implemented |
| `sqlprobe baseline create` | Not planned for v0.0.1 |

---

## Known Issues

None yet.

---

## Next Up

- `docs/failure-modes.md` — failure mode reference
- CI workflow for test automation

---
