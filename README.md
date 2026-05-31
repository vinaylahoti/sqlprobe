<div align="center">

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   ███████╗ ██████╗ ██╗     ██████╗ ██████╗  ██████╗   │
│   ██╔════╝██╔═══██╗██║     ██╔══██╗██╔══██╗██╔═══██╗  │
│   ███████╗██║   ██║██║     ██████╔╝██████╔╝██║   ██║  │
│   ╚════██║██║▄▄ ██║██║     ██╔═══╝ ██╔══██╗██║   ██║  │
│   ███████║╚██████╔╝███████╗██║     ██║  ██║╚██████╔╝  │
│   ╚══════╝ ╚══▀▀═╝ ╚══════╝╚═╝     ╚═╝  ╚═╝ ╚═════╝   │
│                                                         │
│          Production Trust Layer for NL-to-SQL           │
└─────────────────────────────────────────────────────────┘
```

**Your AI said revenue was $4.2M. It was $3.8M. You have no idea why.**

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/badge/pypi-v0.1.0-orange.svg)](https://pypi.org/project/sqlprobe/)
[![Discord](https://img.shields.io/badge/Discord-Join_Community-5865F2.svg)](https://discord.gg/sqlprobe)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

[**Docs**](https://sqlprobe.dev/docs) · [**Quickstart**](https://sqlprobe.dev/quickstart) · [**Discord**](https://discord.gg/sqlprobe) · [**Roadmap**](ROADMAP.md)

</div>

---

## The problem no benchmark measures

Spider. BIRD. Spider 2.0. They measure whether AI can generate SQL that runs.

They don't measure whether it was **right**.

In production enterprise analytics systems, the failure mode that kills you isn't a syntax error — it's a query that executes cleanly, returns a number, and is wrong in ways that make it into a board deck.

```sql
-- What the user asked: "Show me Q1 revenue from enterprise customers"
-- What the AI generated:

SELECT SUM(amount)          -- ❌ gross amount, not recognized revenue
FROM transactions t
JOIN accounts a ON t.account_id = a.id
WHERE a.tier = 'enterprise'  -- ❌ missing: AND a.is_test = false
  AND t.created_at >= '2024-01-01'  -- ❌ calendar Q1, not fiscal Q1
  AND t.created_at < '2024-04-01'   --    (your fiscal year starts Feb)

-- Result: $4.2M
-- Correct answer: $3.8M
-- The query ran. No errors. Nobody knew.
```

**SQLProbe** is an open source evaluation and observability framework that sits beside your existing NL-to-SQL pipeline and answers the question your model can't: *is this query actually correct?*

Not for academic benchmarks. For teams shipping AI-powered analytics in production.

---

## What SQLProbe does

```
Your NL-to-SQL Pipeline          SQLProbe Layer
─────────────────────          ───────────────────────────────────────

User question                  ┌─ Syntax check (dialect-aware)
     │                         ├─ Execution check (shape, cardinality)
     ▼                         ├─ Semantic check (intent alignment)
  LLM model          ──────►   ├─ Business check (org-specific rules)
     │                         ├─ Assertion suite (your invariants)
     ▼                         ├─ LLM judge (conditional, structured)
  Generated SQL                └─ Structured trace + failure taxonomy
     │
     ▼
  Database
```

**It is not:**
- A SQL generator
- A chatbot wrapper
- A benchmark leaderboard
- A replacement for your existing pipeline

**It is:**
- An evaluation harness that runs beside any NL-to-SQL system
- A framework for encoding your organization's analytical contracts as testable assertions
- A regression detector that tells you when a schema or model change broke correctness
- A structured trace format so you know exactly why a query failed

---

## Install

```bash
pip install sqlprobe
```

Or for development:

```bash
git clone https://github.com/sqlprobe/sqlprobe
cd sqlprobe
pip install -e ".[dev]"
```

**Requirements:** Python 3.10+, no database required for syntax evaluation, DuckDB for local execution testing.

---

## Quickstart: 5 minutes to your first evaluation

### 1. Write an evaluation case

```yaml
# cases/revenue_q1_enterprise.yaml

id: revenue_q1_enterprise
version: "1.0"

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

assertions:
  - revenue_excludes_test_accounts
  - fiscal_quarter_definition
  - revenue_non_negative

tags: [revenue, enterprise, fiscal, finance]
```

### 2. Write an assertion

```yaml
# assertions/revenue_excludes_test_accounts.yaml

id: revenue_excludes_test_accounts
description: "Revenue queries must always filter out test/demo accounts"

trigger:
  sql_references_any: ["transactions.amount", "net_revenue", "mrr", "arr"]

assert:
  sql_contains_filter:
    column: "accounts.is_test"
    operator: "="
    value: false

severity: critical
failure_mode: MISSING_BUSINESS_FILTER
```

### 3. Run the harness

```bash
# Syntax check only — zero dependencies
sqlprobe validate cases/

# Full evaluation against a local DuckDB
sqlprobe run cases/ --db duckdb://./fixtures/warehouse.db

# With LLM judge for semantic + business evaluation
sqlprobe run cases/ --db duckdb://./fixtures/warehouse.db --judge

# Compare against pinned baseline (CI mode)
sqlprobe run cases/ --compare-baseline --output report.json
```

### 4. See the results

```
SQLProbe Evaluation Report
══════════════════════════════════════════════════════════════

  Cases evaluated:    47
  ✓ Passed:           41  (87.2%)
  ⚠ Warned:            3  (6.4%)
  ✗ Failed:            3  (6.4%)
  Critical failures:   2

──────────────────────────────────────────────────────────────

FAILED  revenue_q1_enterprise
  Layer:          Business
  Failure mode:   MISSING_BUSINESS_FILTER
  Assertion:      revenue_excludes_test_accounts
  Detail:         Query does not filter accounts.is_test = false
                  Expected filter on: accounts.is_test
                  SQL references: transactions.amount (trigger matched)

  Generated SQL diff:
  - WHERE a.segment IN ('ENT', 'ENTERPRISE')          ← present
  + AND a.is_test = false                             ← MISSING
    AND t.recognized_at >= '2024-02-01'

  Judge verdict:  FAIL (confidence: high)
  Judge note:     "Query uses gross `amount` instead of `net_revenue`.
                   Semantic annotation specifies net_revenue for
                   recognized revenue calculations."

──────────────────────────────────────────────────────────────

Regression vs baseline (2024-03-01):
  ↓ Regressed:  2 cases  (were passing, now failing)
  ↑ Recovered:  1 case   (was failing, now passing)

  Regressed cases:
    - revenue_q1_enterprise     [MISSING_BUSINESS_FILTER]
    - arr_by_segment_march      [CALENDAR_VIOLATION]
```

---

## Core concepts

### The four-layer correctness model

SQLProbe evaluates correctness at four layers. A query can pass every lower layer and fail the one above it.

```
┌──────────────────────────────────────────────────────────────┐
│  Layer 4: Business Correctness                               │
│  Does this query reflect YOUR organization's definition      │
│  of this metric? Business logic not in the schema.           │
│  Evaluator: Assertion suite + conditional LLM judge          │
├──────────────────────────────────────────────────────────────┤
│  Layer 3: Semantic Correctness                               │
│  Does the SQL faithfully represent the user's intent?        │
│  Right grain, right filters, right aggregation, right time.  │
│  Evaluator: Reference SQL comparison + intent decomposition  │
├──────────────────────────────────────────────────────────────┤
│  Layer 2: Execution Correctness                              │
│  Does the query run? Does the result shape make sense?       │
│  No cardinality explosions, no silent empties, right types.  │
│  Evaluator: Live DB execution or schema-only dry run         │
├──────────────────────────────────────────────────────────────┤
│  Layer 1: Syntax Correctness                                 │
│  Parseable, dialect-valid SQL.                               │
│  Evaluator: sqlglot (BigQuery, Snowflake, Redshift, DuckDB)  │
└──────────────────────────────────────────────────────────────┘
```

**The key insight:** Business correctness requires organizational knowledge that is never in the schema, the model's training data, or any benchmark dataset. It lives in dbt models, metric catalogues, and the heads of your senior analysts. SQLProbe gives you the framework to encode that knowledge as testable, versionable assertions.

---

### Failure mode taxonomy

SQLProbe uses a named taxonomy of production failure modes. Every evaluation result carries a failure mode code so you can track, aggregate, and act on correctness issues systematically.

| Code | Layer | Description |
|------|-------|-------------|
| `DIALECT_MISMATCH` | Syntax | Valid SQL in one dialect, invalid in target |
| `NONEXISTENT_OBJECT` | Syntax | References hallucinated or deprecated table/column |
| `CARDINALITY_EXPLOSION` | Execution | Missing join condition produces Cartesian product |
| `SILENT_EMPTY` | Execution | Returns zero rows when correct answer is non-empty |
| `TYPE_MISMATCH_COERCION` | Execution | Implicit type coercion produces wrong results silently |
| `NULL_PROPAGATION` | Execution | NULLs in aggregations cause unexpected exclusions |
| `WRONG_GRAIN` | Semantic | Aggregated at wrong level of granularity |
| `WRONG_DATE_BOUNDARY` | Semantic | Off-by-one in date ranges, wrong interval |
| `MISSING_FILTER` | Semantic | Implied filter not applied |
| `SPURIOUS_FILTER` | Semantic | Filter applied that user did not request |
| `WRONG_AGGREGATION` | Semantic | SUM when COUNT, AVG when SUM, DISTINCT omitted |
| `COLUMN_SUBSTITUTION` | Semantic | Plausible-but-wrong column (gross vs net revenue) |
| `DECOMPOSITION_FAILURE` | Semantic | Multi-part question partially answered |
| `METRIC_DEFINITION_VIOLATION` | Business | Metric computed differently than org's canonical definition |
| `MISSING_BUSINESS_FILTER` | Business | Org-specific implicit filter not applied |
| `CALENDAR_VIOLATION` | Business | Calendar quarter used when org uses fiscal calendar |
| `SCOPE_VIOLATION` | Business | Data outside analytical scope or user's access level |
| `STALE_LOGIC` | Business | Uses business rule that was valid before schema/def change |

---

### Assertions

Assertions are the mechanism for encoding your organization's analytical contracts. They are written by data teams, not just engineers. Three tiers:

**Structural** — checked against the SQL AST, no execution required:

```yaml
id: mrr_requires_active_filter
trigger:
  sql_references_any: ["mrr", "monthly_recurring_revenue"]
assert:
  sql_contains_filter:
    column: "subscriptions.status"
    operator: "="
    value: "active"
severity: critical
failure_mode: MISSING_BUSINESS_FILTER
```

**Result** — checked against execution output:

```yaml
id: churn_rate_bounded
trigger:
  question_contains_any: ["churn", "churn rate"]
assert:
  result_column_satisfies:
    column_pattern: "*churn*"
    condition: "BETWEEN 0 AND 1"
severity: warning
failure_mode: NULL_PROPAGATION
```

**Business logic** — checked with org context, escalates to LLM judge on failure:

```yaml
id: fiscal_quarter_definition
trigger:
  question_contains_any: ["quarter", "Q1", "Q2", "Q3", "Q4"]
  question_not_contains: ["calendar quarter"]
assert:
  sql_date_anchor_matches:
    fiscal_year_start_month: 2
on_failure: escalate_to_llm_judge
severity: critical
failure_mode: CALENDAR_VIOLATION
```

---

### Semantic schema annotations

Attach business-layer semantics to schema objects. These are injected into your prompt context and provided as evidence to the LLM judge.

```yaml
# schema/annotations.yaml

annotations:
  - object: "transactions.amount"
    semantic: "Gross transaction value before refunds. Use net_revenue for P&L analysis."
    do_not_use_for: ["revenue reporting", "ARR", "MRR"]

  - object: "transactions.net_revenue"
    semantic: "Recognized revenue net of refunds and discounts. Use for all financial reporting."

  - object: "accounts.segment"
    semantic: "Enterprise = segment IN ('ENT', 'ENTERPRISE', 'E'). Updated Q3 2023."

  - object: "accounts.is_test"
    semantic: "Exclude from all analytical queries. Test/demo accounts for internal use only."
    required_filter: "= false"

  - join: "transactions → accounts"
    on: "transactions.account_id = accounts.id"
    cardinality: "many-to-one"
    notes: "Always inner join. No orphaned transactions in this schema."
```

---

### LLM-as-judge

The judge is used conditionally — only when deterministic checks are insufficient. It receives structured inputs, evaluates specific dimensions, and returns structured outputs with confidence levels.

```python
from sqlprobe import Judge

judge = Judge(model="claude-sonnet-4-20250514")

result = judge.evaluate(
    question="What was Q1 revenue from enterprise customers?",
    sql=generated_sql,
    schema_annotations=annotations,
    assertion_failures=failed_assertions,
    dimensions=["metric_definition", "date_boundary", "segment_filter"]
)

# result.dimensions[0].verdict → "FAIL"
# result.dimensions[0].failure_mode → "COLUMN_SUBSTITUTION"
# result.dimensions[0].evidence → "Query uses gross `amount`..."
# result.overall_score → 0.67
# result.confidence → "high"
```

The judge is calibrated against a set of known-correct cases. A judge model update that changes results on the calibration set triggers a review alert.

---

### Regression testing

```bash
# Pin the current state as baseline
sqlprobe baseline create --label "pre-migration"

# Run on any change: model update, prompt change, schema migration
sqlprobe run cases/ --compare-baseline

# Output shows exactly what regressed and why
# Regression = case moved from PASS to FAIL
# Recovery = case moved from FAIL to PASS (equally important)
```

Regression detection runs on three triggers:
- **Model/prompt change** — run full suite, compare pass rates
- **Schema change** — automatically re-run cases referencing changed objects
- **Business definition change** — invalidate assertions tagged with affected domain

Integrate with CI:

```yaml
# .github/workflows/sqlprobe.yml
- name: Run SQLProbe regression check
  run: |
    sqlprobe run cases/ \
      --db ${{ secrets.WAREHOUSE_URL }} \
      --compare-baseline \
      --fail-on-regression critical \
      --output report.json
```

---

## Integrations

### Works with any NL-to-SQL system

SQLProbe wraps your existing pipeline — it doesn't replace it.

```python
from sqlprobe import Probe

probe = Probe.from_config("sqlprobe.yaml")

# Wrap any callable that takes a question and returns SQL
with probe.trace(question=user_question) as trace:
    sql = your_nl_to_sql_function(user_question)
    trace.set_generated_sql(sql)

# Evaluation runs automatically
# Results available in trace.result
# Logs appended to trace store
```

### Database support

| Database | Syntax | Execution | Dry Run |
|----------|--------|-----------|---------|
| DuckDB | ✓ | ✓ | ✓ |
| BigQuery | ✓ | ✓ | ✓ |
| Snowflake | ✓ | ✓ | — |
| Redshift | ✓ | ✓ | — |
| PostgreSQL | ✓ | ✓ | — |
| Databricks | ✓ | Coming | — |
| Trino/Athena | Coming | Coming | — |

### LLM providers

| Provider | Judge | Intent decomposition |
|----------|-------|---------------------|
| Anthropic (Claude) | ✓ | ✓ |
| OpenAI (GPT-4o) | ✓ | ✓ |
| Azure OpenAI | ✓ | ✓ |
| AWS Bedrock | Coming | Coming |
| Local (Ollama) | Experimental | Experimental |

### Data catalog integrations

```bash
# Import semantic annotations from dbt schema.yml
sqlprobe annotations import --source dbt --path ./dbt/schema.yml

# Import from Datahub
sqlprobe annotations import --source datahub --server https://datahub.internal

# Export annotations for use in prompts
sqlprobe annotations export --format prompt-context --tables transactions,accounts
```

---

## Python SDK

```python
from sqlprobe import Probe, EvaluationCase, Assertion

# Load and run a suite
probe = Probe.from_config("sqlprobe.yaml")
results = probe.run_suite("cases/", db_url="duckdb://./test.db")

# Build a case programmatically
case = EvaluationCase(
    id="revenue_q1",
    question="What was Q1 revenue from enterprise customers?",
    expected_sql=reference_sql,
    assertions=["revenue_excludes_test_accounts", "fiscal_quarter_definition"],
    tags=["revenue", "enterprise"]
)

result = probe.evaluate(case, generated_sql=your_model_output)

# Access structured results
print(result.layers.business.passed)        # False
print(result.failure_modes)                  # ["MISSING_BUSINESS_FILTER"]
print(result.judge_result.overall_score)     # 0.67

# Iterate over assertion failures
for failure in result.assertion_failures:
    print(f"{failure.assertion_id}: {failure.detail}")
```

---

## Project structure

```
sqlprobe/
├── core/
│   ├── case.py              # EvaluationCase datamodel + YAML spec
│   ├── loader.py            # Case loading, validation, registry
│   └── registry.py          # Case registry with tags + versioning
├── evaluators/
│   ├── syntax.py            # sqlglot dialect-aware parser
│   ├── execution.py         # DB execution + result shape checks
│   ├── assertions.py        # Structural assertion engine (AST-based)
│   └── judge.py             # LLM-as-judge with calibration
├── adapters/
│   ├── duckdb.py            # Full support
│   ├── bigquery.py
│   ├── snowflake.py
│   └── redshift.py
├── annotations/
│   ├── schema.py            # Semantic annotation model
│   ├── importers/           # dbt, Datahub, Alation importers
│   └── prompt_builder.py    # Injects annotations into prompt context
├── regression/
│   ├── baseline.py          # Baseline pinning + comparison
│   └── report.py            # Markdown + JSON report generation
├── tracing/
│   ├── trace.py             # Structured trace format
│   └── store.py             # Append-only JSONL trace store
├── cli/
│   └── main.py              # typer CLI
└── assertions/              # Built-in assertion library
    ├── revenue.yaml
    ├── date_handling.yaml
    ├── filters.yaml
    └── cardinality.yaml
```

---

## Roadmap

### v0.1 — Evaluation harness core *(current)*
- [x] YAML evaluation case format + loader
- [x] Four-layer correctness model (syntax, execution, semantic, business)
- [x] sqlglot-based syntax evaluation (BigQuery, Snowflake, Redshift, DuckDB)
- [x] DuckDB execution adapter + result shape checks
- [x] Structural assertion engine (AST-based, no execution required)
- [x] LLM judge (Anthropic + OpenAI) with structured output
- [x] Baseline pinning + regression detection
- [x] CLI: validate, run, baseline, report
- [x] Built-in assertion library (revenue, dates, filters, cardinality)

### v0.2 — Schema observability
- [ ] Semantic annotation format + parser
- [ ] dbt schema.yml importer
- [ ] Schema drift detector (column rename, deprecation, type change)
- [ ] Automatic case invalidation on schema change
- [ ] Datahub + Alation annotation importers

### v0.3 — Correction harvester
- [ ] SDK for capturing user SQL edits as structured signals
- [ ] Edit-to-evaluation-case converter
- [ ] Correction dataset format (for fine-tuning or RAG)
- [ ] Correction signal dashboard

### v0.4 — Observability layer
- [ ] Production trace collector (OpenTelemetry-compatible)
- [ ] Failure mode distribution dashboard
- [ ] Weekly correctness digest (Slack/email)
- [ ] Anomaly detection on result distributions

### v1.0 — Production standard
- [ ] `sqlprobe.json` universal trace format (exportable to any observability platform)
- [ ] Databricks + Trino adapters
- [ ] Enterprise SSO + team workspaces (hosted offering)
- [ ] Certification program for NL-to-SQL vendors

---

## Why this matters as models improve

The obvious question: if models get dramatically better at SQL generation, does this become irrelevant?

No — for three reasons.

**1. Organizational knowledge is not in any training set.** A perfect SQL generation model still cannot know that "active customer" means `last_order_date >= CURRENT_DATE - 90` at your company, or that your fiscal year starts in February, or that `accounts.is_test = true` records must always be excluded. That knowledge has to be explicitly provided and verified. SQLProbe is the runtime for that verification.

**2. Auditability requirements grow with AI adoption.** Finance, legal, and regulated industries don't just need correct answers — they need traceable evidence of how an answer was produced. The evaluation trace is the audit log. This requirement gets *stronger* as AI analytics becomes more prevalent, not weaker.

**3. The assertion suite is institutional memory.** A well-maintained case library captures what your organization has decided is correct. These decisions outlast any model. SQLProbe is the framework for building and maintaining that memory as a first-class engineering artifact.

---

## Contributing

SQLProbe is most useful when the assertion library reflects real production failure modes. If you've encountered a class of error in your NL-to-SQL deployment that isn't covered:

1. Check the [failure mode taxonomy](docs/failure-modes.md)
2. If it's new, open an issue with the pattern and an example
3. If you can write the assertion template, open a PR

The highest-value contributions right now:
- **Database adapters** — especially Databricks and Trino
- **Assertion templates** — domain-specific libraries (finance, SaaS, e-commerce, healthcare)
- **Catalog importers** — dbt Cloud, Monte Carlo, Atlan
- **Real failure mode reports** — anonymized examples of production failures from the taxonomy

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and guidelines.

---

## Community

- **Discord:** [discord.gg/sqlprobe](https://discord.gg/sqlprobe) — #production-failures is the most useful channel
- **GitHub Discussions:** For design proposals and RFC review
- **Roadmap:** Public, community-voted, in [ROADMAP.md](ROADMAP.md)

---

## Design principles

1. **Works without an LLM.** Syntax and structural assertion evaluation run with zero API calls. The LLM judge is conditional, not default.

2. **Works without a live database.** Schema-only dry runs for syntax and structural checks. DuckDB fixtures for local execution testing.

3. **Format-first, not tool-first.** The evaluation case format, assertion format, and trace format are the core artifacts. They should be portable across tools, readable by humans, and committable to version control.

4. **Correctness is contextual.** Every evaluation case carries the organizational context needed to reproduce the evaluation without external state. Schema snapshots are versioned. Assertions carry effective dates.

5. **Signal, not verdicts.** Every result carries what was checked, what was assumed, and what evidence supports the judgment. Teams can act on a failure without reading source code.

6. **No silent degradation.** Schema changes, model updates, and definition changes all trigger explicit review signals. False confidence is worse than no confidence.

---

## License

Apache 2.0. See [LICENSE](LICENSE).

---

<div align="center">

**Built by data engineers who've shipped NL-to-SQL in production.**

*If your AI analytics system has ever returned a wrong number that made it into a report,*
*this project is for you.*

[**Star SQLProbe**](https://github.com/sqlprobe/sqlprobe) · [**Join Discord**](https://discord.gg/sqlprobe) · [**Read the Docs**](https://sqlprobe.dev/docs)

</div>
