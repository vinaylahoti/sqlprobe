# SQLProbe — Project Status

> This file is the source of truth for current implementation reality.
> Updated after every commit.
> README.md = long-term vision. IMPLEMENTATION_PLAN.md = build plan. PROJECT_STATUS.md = what actually exists today.

---

## Current Version: v0.0.1 (in development)

## Last Updated: 2026-05-31

---

## What Exists Today

### Repository Structure
- [x] Package scaffold created (`sqlprobe/` with all subdirectories)
- [x] `pyproject.toml` with correct dependencies
- [x] `LICENSE` (Apache 2.0)
- [x] `README.md` (full vision document)
- [x] `IMPLEMENTATION_PLAN.md` (build plan)
- [x] Empty placeholder files for all planned modules
- [x] Empty YAML files for assertions and example cases

### Core
- [x] `sqlprobe/core/taxonomy.py` — all 18 failure modes, Layer, Severity, FailureModeMetadata, FAILURE_MODE_REGISTRY
- [x] `sqlprobe/core/case.py` — EvaluationCase, ExpectedOutput, ExpectedResultShape, InputContext
- [x] `sqlprobe/core/result.py` — EvaluationResult, LayerResult, AssertionFailure

### Loaders
- [ ] `sqlprobe/loader/case_loader.py` — not yet implemented
- [ ] `sqlprobe/loader/assertion_loader.py` — not yet implemented

### Evaluators
- [ ] `sqlprobe/evaluators/syntax.py` — not yet implemented
- [ ] `sqlprobe/evaluators/assertions.py` — not yet implemented
- [ ] `sqlprobe/evaluators/execution.py` — stub planned
- [ ] `sqlprobe/evaluators/judge.py` — stub planned

### Adapters
- [ ] `sqlprobe/adapters/duckdb.py` — stub planned

### Regression
- [ ] `sqlprobe/regression/baseline.py` — stub planned

### CLI
- [ ] `sqlprobe/cli/main.py` — not yet implemented

### Assertion Library (YAML)
- [ ] `assertions/revenue.yaml` — not yet implemented
- [ ] `assertions/filters.yaml` — not yet implemented
- [ ] `assertions/date_handling.yaml` — not yet implemented

### Example Cases (YAML)
- [ ] `cases/examples/revenue_q1_enterprise.yaml` — not yet implemented
- [ ] `cases/examples/churn_rate_monthly.yaml` — not yet implemented

### Tests
- [ ] `tests/test_case_loader.py` — not yet implemented
- [ ] `tests/test_syntax_evaluator.py` — not yet implemented
- [ ] `tests/test_assertion_engine.py` — not yet implemented

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
| `sqlprobe validate <cases/>` | Not implemented |
| `sqlprobe run <cases/>` | Not implemented |
| `sqlprobe run --sql "..."` | Not implemented |
| `sqlprobe demo` | Not implemented |
| `sqlprobe baseline create` | Not planned for v0.0.1 |

---

## Known Issues

None yet.

---

## Next Up

- `sqlprobe/loader/case_loader.py` — YAML loader for evaluation cases
- `sqlprobe/loader/assertion_loader.py` — YAML loader for assertion definitions

---
