# SQLProbe Failure Mode Reference

Failure modes are SQLProbe's structured labels for correctness risks in generated SQL. They appear on assertion failures, layer results, CLI output, and JSON reports so humans and automation can distinguish syntax errors from execution issues, semantic mistakes, and organization-specific business rule violations.

## Layer 1: Syntax

| Code | Description | Example |
|---|---|---|
| `DIALECT_MISMATCH` | Triggered when SQL cannot be parsed for the configured dialect, the dialect is unsupported, or SQL is empty. In production, this usually means the generator emitted syntax for the wrong warehouse or produced incomplete SQL. | A BigQuery-specific function is generated while validating as Postgres, or the model returns `SELECT FROM`. |
| `NONEXISTENT_OBJECT` | Triggered when SQL references a table, view, or column that does not exist in the available schema. In production, this often points to stale schema context or a hallucinated column name. | A query references `customer_revenue.net_arr` when the warehouse only has `finance.revenue_fact.net_revenue`. |

## Layer 2: Execution

| Code | Description | Example |
|---|---|---|
| `CARDINALITY_EXPLOSION` | Triggered when a query returns far more rows than expected or exceeds the configured row threshold. In production, this often means a join predicate is missing or a grouping exploded the result set. | A customer table joins to transactions without `account_id`, producing millions of rows. |
| `SILENT_EMPTY` | Triggered when a query succeeds but returns zero rows where the case expected a non-empty result. In production, this is dangerous because dashboards can show plausible zeros instead of obvious errors. | A date filter uses May through July while the requested fiscal Q1 data is February through April. |
| `TYPE_MISMATCH_COERCION` | Triggered for database-level execution errors in v0.0.2, using the closest existing taxonomy code. In production, this may indicate an invalid comparison, incompatible cast, or function called with the wrong type. | A query compares a date column to an invalid string or uses a numeric operation on text. |
| `NULL_PROPAGATION` | Triggered when required result columns contain `NULL`, or a value-range column is `NULL`. In production, this can hide missing joins, incomplete data, or aggregations that return no meaningful value. | `SUM(net_revenue)` returns `NULL` because every matched row has null revenue. |

## Layer 3: Semantic

| Code | Description | Example |
|---|---|---|
| `WRONG_GRAIN` | Triggered when the result shape indicates the query returned the wrong number of rows for the requested grain. In production, this means the answer may be grouped too finely or not grouped enough. | A total revenue question returns one row per account instead of one total row. |
| `WRONG_DATE_BOUNDARY` | Triggered when configured assertions detect missing or suspicious date filtering. In production, this usually means the query answers the right metric over the wrong time window. | A "last 3 months" churn query omits any date column filter. |
| `MISSING_FILTER` | Triggered when a filter implied by the user question is not applied. In production, this broadens the scope of the answer and can make the result look plausible but wrong. | The user asks for enterprise accounts, but the SQL includes all account segments. |
| `SPURIOUS_FILTER` | Triggered when the SQL applies a filter the user did not request. In production, this narrows the answer silently and can exclude valid data. | The user asks for all customers, but the SQL adds `region = 'US'`. |
| `WRONG_AGGREGATION` | Triggered when the result range indicates an aggregation is likely wrong, or when a configured assertion requires an aggregation that is missing. In production, this often shows up as `COUNT` versus `SUM`, gross versus net totals, or accidental averaging. | A revenue query counts transactions instead of summing recognized revenue. |
| `COLUMN_SUBSTITUTION` | Triggered when SQL uses a plausible but incorrect column, selects all columns where that is disallowed, or omits an expected result column. In production, this is common when schemas contain similar fields. | A recognized revenue query uses `amount` or `created_at` instead of `net_revenue` and `recognized_at`. |
| `DECOMPOSITION_FAILURE` | Triggered when a multi-part question is only partially answered. In production, this usually means the SQL answers one clause of the request and ignores another. | The user asks for revenue by region and month, but the query only groups by month. |

## Layer 4: Business

| Code | Description | Example |
|---|---|---|
| `METRIC_DEFINITION_VIOLATION` | Triggered when SQL computes a metric differently from the organization's canonical definition. In production, this is a governance issue: the SQL may run and look reasonable while violating internal metric rules. | ARR is calculated from invoice amount instead of active subscription MRR multiplied by 12. |
| `MISSING_BUSINESS_FILTER` | Triggered when an organization-specific required filter is absent. In production, this often catches implicit business rules that are not obvious from the user question. | Revenue SQL does not exclude test or demo accounts with `accounts.is_test = false`. |
| `CALENDAR_VIOLATION` | Triggered when SQL uses the wrong calendar system for the organization. In production, this can make quarterly and yearly reports disagree with finance definitions. | A company with a February fiscal year start receives a calendar Q1 filter for January through March. |
| `SCOPE_VIOLATION` | Triggered when SQL accesses data outside the intended analytical scope or user role. In production, this can cause compliance or permissions issues. | A sales analyst query includes finance-only adjustment tables. |
| `STALE_LOGIC` | Triggered when SQL uses a business rule that has been superseded by a schema or policy change. In production, this often happens after metric migrations. | Churn logic uses `cancelled_at` even after the canonical definition moved to `subscription_events`. |

## Which Failure Modes Are Currently Detected

| Code | v0.0.2 | How detected |
|---|---|---|
| `DIALECT_MISMATCH` | ✅ | `sqlglot` syntax evaluation for parse failures, empty SQL, and unsupported dialects |
| `NONEXISTENT_OBJECT` | 🔲 | Planned schema validation or database-object checks; current execution errors are reported as `TYPE_MISMATCH_COERCION` |
| `CARDINALITY_EXPLOSION` | ✅ | DuckDB adapter row count threshold |
| `SILENT_EMPTY` | ✅ | Execution evaluator row count check when expected rows are greater than zero |
| `TYPE_MISMATCH_COERCION` | ✅ | Execution evaluator maps database execution errors to this closest existing taxonomy code |
| `NULL_PROPAGATION` | ✅ | Execution evaluator `no_nulls_in` and `value_range` null checks |
| `WRONG_GRAIN` | ✅ | Execution evaluator row count mismatch against `expected.result_shape.row_count` |
| `WRONG_DATE_BOUNDARY` | ✅ | Built-in structural assertion `require_explicit_date_filter`; full boundary reasoning is planned |
| `MISSING_FILTER` | 🔲 | Planned semantic judge and richer assertion library |
| `SPURIOUS_FILTER` | 🔲 | Planned semantic judge |
| `WRONG_AGGREGATION` | ✅ | Execution evaluator value-range violations; assertion engine also supports configured `aggregation_type` checks |
| `COLUMN_SUBSTITUTION` | ✅ | Structural assertion engine and execution evaluator `columns_present` failures |
| `DECOMPOSITION_FAILURE` | 🔲 | Planned semantic judge |
| `METRIC_DEFINITION_VIOLATION` | 🔲 | Planned result assertions, semantic annotations, and LLM judge |
| `MISSING_BUSINESS_FILTER` | ✅ | Structural assertion engine, including built-in test-account exclusion rule |
| `CALENDAR_VIOLATION` | 🔲 | Planned fiscal calendar assertions and semantic judge |
| `SCOPE_VIOLATION` | 🔲 | Planned scope assertions tied to case context and user role |
| `STALE_LOGIC` | 🔲 | Planned baseline/regression and business-rule versioning |
