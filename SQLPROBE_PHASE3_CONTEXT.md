# SQLProbe — Phase 3 Codex Context

> Feed this file to Codex at the start of every Phase 3 session.
> It is the source of truth for what exists, what we’re building, and every decision already made.
> Read this completely before writing any code.

-----

## What SQLProbe Is (Brief)

An open source evaluation harness that sits beside any NL-to-SQL pipeline and checks whether
generated SQL is actually correct — not just syntactically valid. Four evaluation layers:
Syntax → Execution → Semantic → Business.

-----

## What Phase 1 and Phase 2 Built (Do Not Re-implement)

### Phase 1 — v0.0.1 ✅

- YAML case + assertion loading
- sqlglot syntax validation (Layer 1)
- Structural assertion engine — AST-based, no DB required (Layer 4 business rules)
- Typer CLI: `validate`, `run`, `demo`
- 18 failure modes defined in taxonomy

### Phase 2 — v0.0.2 ✅

- `DuckDBAdapter` — real implementation in `sqlprobe/adapters/duckdb.py`
- `ExecutionResult` dataclass in `sqlprobe/core/result.py`
- `evaluate_execution()` in `sqlprobe/evaluators/execution.py` — result shape checks (Layer 2)
- `--db` flag wired in CLI: `sqlprobe run cases/ --db duckdb://./fixtures/warehouse.db`
- JSON report extended with `execution` key
- `fixtures/warehouse.db` — committed DuckDB fixture with accounts, transactions, subscriptions
- 63 tests passing

### Currently stubbed (Phase 3 targets)

- `sqlprobe/evaluators/judge.py` — stub, skipped
- `sqlprobe/regression/baseline.py` — stub, leave for Phase 4

-----

## Four-Layer Model — Current State

```text
Layer 4: Business   ✅ structural assertions (AST-based)
                    🔲 business logic assertions with judge escalation (Phase 3)
Layer 3: Semantic   🔲 LLM judge (Phase 3)
Layer 2: Execution  ✅ DuckDB adapter + result shape evaluation
Layer 1: Syntax     ✅ sqlglot
```

-----

## Phase 3 — What We Are Building

### Scope: LLM Judge + Result Assertions + Schema Annotations

Three deliverables, in implementation order:

1. **Result assertions** — new assertion type checked against `ExecutionResult.rows`
1. **Schema annotations** — lightweight YAML format for business-layer column semantics
1. **LLM judge** — Claude API, evaluates semantic + business dimensions, uses execution evidence and annotations as context

### Why this order

Result assertions extend the existing assertion engine (low risk, no API dependency).
Schema annotations are pure data — YAML loader, no logic.
The judge is built last because it consumes both: assertion failures as evidence, annotations as context.
A judge built without these inputs would be weaker and would need rebuilding.

-----

## Deliverable 1: Result Assertions

### What they are

A new assertion type that checks conditions against actual query execution results.
Currently the assertion engine only checks SQL text/AST (structural assertions).
Result assertions run after execution and check `ExecutionResult.rows`.

### New assertion YAML format

```yaml
# assertions/churn.yaml

- id: churn_rate_bounded
  description: "Churn rate must be between 0 and 1 (a ratio, not a percentage)"
  trigger:
    question_contains_any: ["churn", "churn rate"]
  assert:
    result_column_satisfies:
      column_pattern: "*churn*"       # glob-style match against column names
      condition: "BETWEEN 0 AND 1"    # evaluated against each matching column's value
  severity: warning
  failure_mode: NULL_PROPAGATION

- id: revenue_non_negative
  description: "Revenue aggregates must never be negative"
  trigger:
    sql_references_any: ["net_revenue", "mrr", "arr"]
  assert:
    result_column_satisfies:
      column_pattern: "*revenue*"
      condition: "> 0"
  severity: critical
  failure_mode: WRONG_AGGREGATION
```

### Supported conditions (implement these exactly)

- `BETWEEN <min> AND <max>` — value is within inclusive range
- `> <n>` — value is greater than n
- `>= <n>` — value is greater than or equal to n
- `< <n>` — value is less than n
- `<= <n>` — value is less than or equal to n
- `= <n>` — value equals n
- `IS NOT NULL` — value is not None
- `IS NULL` — value is None

### column_pattern matching

Use `fnmatch.fnmatch(col.lower(), pattern.lower())` for glob matching.
`*churn*` matches `monthly_churn_rate`, `churn`, `churn_ratio`.
If no column matches the pattern in the result, skip the assertion (do not fail).
Log a warning comment in the AssertionFailure detail if skipped due to no column match.

### Where result assertions run

In `sqlprobe/evaluators/assertions.py` — extend `evaluate_assertions()` to accept an optional
`execution_result: ExecutionResult | None = None` parameter.
If `execution_result` is None, result assertions are skipped (backward compatible).
If `execution_result` is provided, result assertions run after structural assertions.

### Files to change

- `sqlprobe/evaluators/assertions.py` — extend to handle `result_column_satisfies` assert type
- `sqlprobe/loader/assertion_loader.py` — parse `result_column_satisfies` from YAML
- `assertions/churn.yaml` — new assertion file with at least `churn_rate_bounded` and `revenue_non_negative`
- `sqlprobe/cli/main.py` — pass `execution_result` to `evaluate_assertions()` when `--db` is active

### Files NOT to change

- `sqlprobe/core/result.py` — AssertionFailure already covers result assertions
- `sqlprobe/core/taxonomy.py` — all failure modes already exist

-----

## Deliverable 2: Schema Annotations

### What they are

A YAML file where data teams document business-layer semantics for schema objects.
These are injected into the judge’s prompt as context — they are not evaluated directly.

### File location

`schema/annotations.yaml` — committed to the repo, ships with the fixture example.

### Format

```yaml
# schema/annotations.yaml

annotations:
  - object: "transactions.amount"
    semantic: "Gross transaction value before refunds. Do NOT use for revenue reporting."
    do_not_use_for:
      - "revenue reporting"
      - "ARR"
      - "MRR"

  - object: "transactions.net_revenue"
    semantic: "Recognized revenue net of refunds and discounts. Use for all financial reporting."
    preferred_for:
      - "revenue reporting"
      - "P&L analysis"

  - object: "accounts.is_test"
    semantic: "Marks test/demo accounts for internal use only. Must always be filtered: is_test = false."
    required_filter: "= false"

  - object: "accounts.segment"
    semantic: "Customer segment. Enterprise customers have segment IN ('ENT', 'ENTERPRISE')."

  - join: "transactions → accounts"
    on: "transactions.account_id = accounts.id"
    cardinality: "many-to-one"
    notes: "Always inner join. No orphaned transactions exist."
```

### Loader

`sqlprobe/loader/annotation_loader.py` — new file.

```python
@dataclass
class SchemaAnnotation:
    object: str | None          # "table.column" or None for join annotations
    join: str | None            # "table_a → table_b" or None
    semantic: str | None
    do_not_use_for: list[str] = field(default_factory=list)
    preferred_for: list[str] = field(default_factory=list)
    required_filter: str | None = None
    notes: str | None = None

def load_annotations(path: str | Path) -> list[SchemaAnnotation]:
    ...
```

### Prompt builder

`sqlprobe/annotations/prompt_builder.py` — new file.

```python
def build_annotation_context(annotations: list[SchemaAnnotation]) -> str:
    """
    Returns a formatted string block suitable for injection into a judge prompt.
    Example output:
    
    Schema annotations:
    - transactions.amount: Gross transaction value before refunds. Do NOT use for revenue reporting.
      [do_not_use_for: revenue reporting, ARR, MRR]
    - transactions.net_revenue: Recognized revenue net of refunds and discounts.
      [preferred_for: revenue reporting, P&L analysis]
    - accounts.is_test: Must always be filtered: is_test = false.
      [required_filter: = false]
    """
    ...
```

-----

## Deliverable 3: LLM Judge

### Overview

The judge runs after structural assertions and execution evaluation.
It is invoked conditionally — only when `--judge` flag is passed.
It uses the Claude API (claude-sonnet-4-20250514) with structured output.
It evaluates semantic and business dimensions that deterministic checks cannot cover.

### Judge input

```python
@dataclass
class JudgeInput:
    question: str                              # natural language question from case
    generated_sql: str                         # the SQL being evaluated
    expected_sql: str | None                   # reference SQL if available
    execution_result: ExecutionResult | None   # from Phase 2 adapter
    assertion_failures: list[AssertionFailure] # from structural + result assertions
    schema_annotations: list[SchemaAnnotation] # from annotation loader
    dimensions: list[str]                      # which dimensions to evaluate
```

### Default dimensions to evaluate

- `metric_definition` — is the right metric computed? (net_revenue vs amount, MRR definition)
- `date_boundary` — are date ranges correct? (fiscal vs calendar, off-by-one)
- `segment_filter` — is the right population filtered? (enterprise definition, test account exclusion)
- `aggregation` — is the aggregation correct? (SUM vs COUNT, DISTINCT omitted)
- `grain` — is the query at the right level of granularity?

### Judge output dataclasses (add to `sqlprobe/core/result.py`)

```python
@dataclass
class DimensionResult:
    dimension: str                    # e.g. "metric_definition"
    verdict: str                      # "PASS" | "FAIL" | "WARN" | "SKIP"
    failure_mode: FailureMode | None  # from taxonomy, None if PASS
    evidence: str                     # judge's reasoning (1-3 sentences)
    confidence: str                   # "high" | "medium" | "low"

@dataclass
class JudgeResult:
    overall_verdict: str              # "PASS" | "FAIL" | "WARN"
    overall_score: float              # 0.0 to 1.0 (fraction of dimensions passing)
    confidence: str                   # "high" | "medium" | "low"
    dimensions: list[DimensionResult]
    model: str                        # model string used
    skipped: bool = False             # True if judge was not invoked
```

### Judge implementation — `sqlprobe/evaluators/judge.py`

Replace the stub with a real implementation.

```python
import os
import json
from sqlprobe.core.result import JudgeResult, DimensionResult, ExecutionResult, AssertionFailure
from sqlprobe.core.taxonomy import FailureMode
from sqlprobe.loader.annotation_loader import SchemaAnnotation
from sqlprobe.annotations.prompt_builder import build_annotation_context

JUDGE_MODEL = "claude-sonnet-4-20250514"

class SQLProbeJudge:
    def __init__(self, model: str = JUDGE_MODEL, api_key: str | None = None):
        # api_key: if None, read from ANTHROPIC_API_KEY env var
        ...

    def evaluate(self, judge_input: JudgeInput) -> JudgeResult:
        ...
```

### Judge prompt design

The judge receives a single structured prompt. Design it to return JSON only.

System prompt (exact):

```text
You are an expert SQL evaluator. Your role is to assess whether a generated SQL query
correctly answers a business question. You evaluate specific dimensions and return a
structured JSON verdict.

Return ONLY valid JSON. No preamble, no markdown, no explanation outside the JSON.
```

User prompt structure:

```text
Question: {question}

Generated SQL:
{generated_sql}

{if expected_sql}
Reference SQL (correct answer):
{expected_sql}
{endif}

{if schema_annotations}
Schema context:
{annotation_context_string}
{endif}

{if assertion_failures}
Known assertion failures already detected:
{list each: assertion_id — detail}
{endif}

{if execution_result}
Execution result:
- Rows returned: {row_count}
- Success: {success}
{if error}- Error: {error}{endif}
{endif}

Evaluate these dimensions: {comma-separated dimensions}

For each dimension, respond with:
- verdict: PASS, FAIL, WARN, or SKIP (SKIP if you cannot determine)
- failure_mode: one of the taxonomy codes below, or null if PASS
- evidence: 1-3 sentences explaining your reasoning
- confidence: high, medium, or low

Failure mode taxonomy:
WRONG_GRAIN, WRONG_DATE_BOUNDARY, MISSING_FILTER, SPURIOUS_FILTER,
WRONG_AGGREGATION, COLUMN_SUBSTITUTION, DECOMPOSITION_FAILURE,
METRIC_DEFINITION_VIOLATION, MISSING_BUSINESS_FILTER, CALENDAR_VIOLATION,
SCOPE_VIOLATION, STALE_LOGIC

Return this exact JSON structure:
{
  "overall_verdict": "PASS" | "FAIL" | "WARN",
  "overall_score": <float 0.0-1.0>,
  "confidence": "high" | "medium" | "low",
  "dimensions": [
    {
      "dimension": "<name>",
      "verdict": "PASS" | "FAIL" | "WARN" | "SKIP",
      "failure_mode": "<taxonomy code>" | null,
      "evidence": "<reasoning>",
      "confidence": "high" | "medium" | "low"
    }
  ]
}
```

### API call pattern

```python
import httpx  # or use anthropic SDK if available

def _call_api(self, prompt: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=self._api_key)
    response = client.messages.create(
        model=self._model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text
```

Add `anthropic>=0.25.0` to `pyproject.toml` optional extras:

```toml
[project.optional-dependencies]
judge = ["anthropic>=0.25.0"]
dev = ["pytest>=8.0.0", "pytest-cov>=5.0.0", "duckdb>=0.10.0", "anthropic>=0.25.0"]
```

### Error handling

- If `ANTHROPIC_API_KEY` is not set: raise a clear `ValueError` with instructions
- If the API call fails (network, rate limit): return a `JudgeResult` with `skipped=True` and log the error — do not raise, do not fail the evaluation
- If JSON parsing fails: retry once with a stricter prompt (“Return ONLY the JSON object, nothing else”). If it fails again: return `skipped=True`
- Never let judge errors propagate to fail the overall evaluation result — judge is additive

### CLI wiring

Add `--judge` flag to `run` command:

```bash
sqlprobe run cases/ --db duckdb://./fixtures/warehouse.db --judge
sqlprobe run cases/ --db duckdb://./fixtures/warehouse.db --judge --annotations schema/annotations.yaml
```

Behavior:

- `--judge` without `--db`: judge runs on SQL text + assertion failures only (no execution evidence)
- `--judge` with `--db`: judge receives full execution evidence
- `--annotations path`: load schema annotations, inject into judge context
- If `ANTHROPIC_API_KEY` not set and `--judge` is passed: exit with clear error message before running

Console output when judge runs:

```text
FAIL  revenue_q1_enterprise
  Failure Mode: MISSING_BUSINESS_FILTER
  Assertion: revenue_excludes_test_accounts
  Detail: Expected filter not found: accounts.is_test = False
  
  Judge verdict: FAIL (score: 0.60, confidence: high)
    metric_definition  FAIL  COLUMN_SUBSTITUTION
      Query uses gross `amount` instead of `net_revenue` for revenue reporting.
    date_boundary      PASS
    segment_filter     FAIL  MISSING_BUSINESS_FILTER  
      Filter accounts.is_test = false is absent. Test accounts will inflate revenue.
    aggregation        PASS
    grain              PASS
```

JSON report extension — add `judge` key per case:

```json
{
  "case_id": "revenue_q1_enterprise",
  "passed": false,
  "failure_modes": ["MISSING_BUSINESS_FILTER"],
  "execution": {"ran": true, "success": true, "row_count": 1, "failures": []},
  "judge": {
    "ran": true,
    "overall_verdict": "FAIL",
    "overall_score": 0.60,
    "confidence": "high",
    "dimensions": [
      {
        "dimension": "metric_definition",
        "verdict": "FAIL",
        "failure_mode": "COLUMN_SUBSTITUTION",
        "evidence": "Query uses gross amount instead of net_revenue.",
        "confidence": "high"
      }
    ]
  }
}
```

When `--judge` not passed: `"judge": {"ran": false}`

-----

## File Structure — Full Target for Phase 3

```text
sqlprobe/
  core/
    taxonomy.py           ✅ exists
    case.py               ✅ exists
    result.py             🔨 add DimensionResult, JudgeResult
  loader/
    case_loader.py        ✅ exists
    assertion_loader.py   🔨 extend to parse result_column_satisfies
    annotation_loader.py  🔨 new — SchemaAnnotation dataclass + YAML loader
  evaluators/
    syntax.py             ✅ exists
    assertions.py         🔨 extend to run result assertions with execution_result
    execution.py          ✅ exists
    judge.py              🔨 replace stub — SQLProbeJudge + JudgeInput
  adapters/
    duckdb.py             ✅ exists
  annotations/
    prompt_builder.py     🔨 new — build_annotation_context()
  regression/
    baseline.py           ✅ stub — leave for Phase 4
  cli/
    main.py               🔨 add --judge, --annotations flags; wire judge
schema/
  annotations.yaml        🔨 new — example annotations for fixture schema
assertions/
  churn.yaml              🔨 new — result assertion examples
  revenue.yaml            ✅ exists (structural)
  filters.yaml            ✅ exists (structural)
  date_handling.yaml      ✅ exists (structural)
tests/
  test_assertion_engine.py      ✅ exists — extend for result assertions
  test_cli.py                   ✅ exists — extend for --judge, --annotations flags
  test_duckdb_adapter.py        ✅ exists
  test_execution_evaluator.py   ✅ exists
  test_integration.py           ✅ exists — extend for judge integration
  test_annotation_loader.py     🔨 new
  test_judge.py                 🔨 new (mock API calls — no real API in tests)
  test_result_assertions.py     🔨 new
```

-----

## Key Design Decisions (Already Made — Do Not Revisit)

1. **Judge is additive, never blocking.** If the judge errors, errors silently and returns `skipped=True`. The evaluation result is determined by syntax + execution + assertions. Judge provides extra signal, not the gate.
1. **Judge runs on `--judge` flag only.** No judge calls without explicit opt-in. This keeps the tool usable without an API key.
1. **Result assertions extend the existing assertion engine.** Do not create a separate evaluator. Pass `execution_result` as optional parameter to `evaluate_assertions()`. Existing structural assertion tests must still pass unchanged.
1. **Annotations are optional context, not evaluated.** The annotation loader produces data. The prompt builder formats it. Neither validates SQL against annotations — that is the judge’s job.
1. **JSON output is strict.** Judge must be prompted to return ONLY JSON. Strip any markdown fences before parsing. Retry once on parse failure. Return `skipped=True` on second failure.
1. **`anthropic` SDK, not raw HTTP.** Use the official `anthropic` Python package. Add to optional extras and dev deps.
1. **No real API calls in tests.** All judge tests use `unittest.mock.patch` to mock the Anthropic client. Tests must pass with no `ANTHROPIC_API_KEY` set.
1. **`--annotations` is optional.** `--judge` without `--annotations` still works — judge just has no schema context. Annotation context enriches the judge but is not required.
1. **Dimensions are hardcoded for Phase 3.** The five default dimensions are always evaluated. User-configurable dimensions are a Phase 4 concern.
1. **`overall_score`** = fraction of non-SKIP dimensions that returned PASS. Example: 3 PASS, 1 FAIL, 1 SKIP → score = 3/4 = 0.75.

-----

## Failure Modes the Judge Can Detect (New in Phase 3)

These are in `taxonomy.py` but currently undetectable by deterministic checks:

|Code                         |Layer   |Judge dimension  |
|-----------------------------|--------|-----------------|
|`WRONG_GRAIN`                |Semantic|grain            |
|`WRONG_DATE_BOUNDARY`        |Semantic|date_boundary    |
|`MISSING_FILTER`             |Semantic|segment_filter   |
|`SPURIOUS_FILTER`            |Semantic|segment_filter   |
|`WRONG_AGGREGATION`          |Semantic|aggregation      |
|`COLUMN_SUBSTITUTION`        |Semantic|metric_definition|
|`DECOMPOSITION_FAILURE`      |Semantic|grain            |
|`METRIC_DEFINITION_VIOLATION`|Business|metric_definition|
|`CALENDAR_VIOLATION`         |Business|date_boundary    |
|`SCOPE_VIOLATION`            |Business|segment_filter   |
|`STALE_LOGIC`                |Business|metric_definition|

-----

## Test Strategy

### test_result_assertions.py (no DB, no API)

- Mock `ExecutionResult` with real rows
- Test `churn_rate_bounded`: value in [0,1] → pass; value = 1.5 → fail
- Test `revenue_non_negative`: value > 0 → pass; value = -100 → fail
- Test column_pattern glob matching: `*churn*` matches `monthly_churn_rate`
- Test skipped when no column matches pattern
- Test `IS NOT NULL` and `IS NULL` conditions
- Test backward compat: `evaluate_assertions(case, sql, assertions)` without execution_result still works

### test_annotation_loader.py (no DB, no API)

- Load `schema/annotations.yaml` → list of SchemaAnnotation
- Assert fields parsed correctly
- Test `build_annotation_context()` returns non-empty string containing column names

### test_judge.py (mock API — no real calls)

- Mock `anthropic.Anthropic` client
- Mock response returns valid JSON matching expected structure
- Test `SQLProbeJudge.evaluate()` returns `JudgeResult` with correct fields
- Test parse error → retry → second failure → `skipped=True`
- Test missing API key → `ValueError` with clear message
- Test API exception → `skipped=True`, no raise
- Test `overall_score` calculation: 3 PASS + 1 FAIL + 1 SKIP → 0.75
- Test `overall_verdict`: any FAIL → “FAIL”; all PASS → “PASS”; any WARN but no FAIL → “WARN”

### test_cli.py extensions

- `test_run_with_judge_flag_no_api_key`: set `ANTHROPIC_API_KEY=""`, run with `--judge` → exits with error before running
- `test_run_with_judge_flag_mocked`: mock the judge, confirm `judge` key in JSON output
- `test_run_without_judge_flag_json_has_judge_not_ran`: JSON has `"judge": {"ran": false}`

-----

## Implementation Order for Codex (9 prompts expected)

1. Add `DimensionResult` and `JudgeResult` dataclasses to `core/result.py`
1. Add `anthropic` to pyproject.toml extras + dev
1. Implement `annotation_loader.py` + `SchemaAnnotation` dataclass + `prompt_builder.py`
1. Add `schema/annotations.yaml` example file
1. Extend `assertion_loader.py` to parse `result_column_satisfies`; extend `assertions.py` to run result assertions; add `assertions/churn.yaml`
1. Implement `SQLProbeJudge` in `evaluators/judge.py` + `JudgeInput` dataclass
1. Wire `--judge` and `--annotations` flags in CLI
1. Write all new tests (`test_annotation_loader.py`, `test_result_assertions.py`, `test_judge.py`); extend existing tests
1. Docs + status update

-----

## What Phase 4 Will Be (Don’t Build Yet)

- Baseline pinning (`sqlprobe baseline create`)
- Regression detection (`sqlprobe run --compare-baseline`)
- CI/CD workflow (`.github/workflows/sqlprobe.yml`)
- Judge calibration against known-correct cases
- PyPI publishing

-----

## Codex Instructions

1. Read this file fully before writing any code.
1. Do not modify Phase 1 or Phase 2 files unless extending them (e.g. adding to `result.py`, extending `assertions.py` signature).
1. All Phase 3 work is additive. `sqlprobe run` without `--judge` must behave exactly as in v0.0.2.
1. No real Anthropic API calls in tests. Mock everything.
1. Write tests for every new module. New code target: >80% coverage.
1. Judge errors must never cause the overall evaluation to fail. Always catch and return `skipped=True`.
1. When in doubt about a design decision, check this document first. If not covered, leave a `# TODO: decision needed` comment and flag it.

-----

*Last updated: 2026-05-31*
*Phase 2 complete: v0.0.2 — DuckDB execution layer*
*Phase 3 target: v0.0.3 — LLM judge + result assertions + schema annotations*
