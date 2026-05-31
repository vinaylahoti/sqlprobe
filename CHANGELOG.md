# Changelog

All notable changes to SQLProbe will be documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased] — v0.0.1

### Added
- Initial project scaffold (directories, `__init__.py` files, empty placeholders)
- `pyproject.toml` with all dependencies defined
- `LICENSE` (Apache 2.0)
- `README.md` — full project vision
- `IMPLEMENTATION_PLAN.md` — weekend build plan
- `sqlprobe/core/taxonomy.py` — 18 failure modes across 4 layers, Layer enum, Severity enum, FailureModeMetadata, FAILURE_MODE_REGISTRY
- `sqlprobe/core/case.py` — EvaluationCase dataclass with full field schema
- `sqlprobe/core/result.py` — EvaluationResult, LayerResult, AssertionFailure dataclasses
- case_loader and assertion_loader implemented
- Built-in assertion library created (4 assertions across 3 files)
- Two example evaluation cases created
- syntax evaluator implemented using sqlglot

---
