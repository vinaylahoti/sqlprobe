from enum import Enum
from dataclasses import dataclass

class Layer(str, Enum):
    SYNTAX    = "syntax"
    EXECUTION = "execution"
    SEMANTIC  = "semantic"
    BUSINESS  = "business"

class Severity(str, Enum):
    CRITICAL = "critical"
    WARNING  = "warning"
    INFO     = "info"

class FailureMode(str, Enum):
    # Syntax
    DIALECT_MISMATCH           = "DIALECT_MISMATCH"
    NONEXISTENT_OBJECT         = "NONEXISTENT_OBJECT"
    # Execution
    CARDINALITY_EXPLOSION      = "CARDINALITY_EXPLOSION"
    SILENT_EMPTY               = "SILENT_EMPTY"
    TYPE_MISMATCH_COERCION     = "TYPE_MISMATCH_COERCION"
    NULL_PROPAGATION           = "NULL_PROPAGATION"
    # Semantic
    WRONG_GRAIN                = "WRONG_GRAIN"
    WRONG_DATE_BOUNDARY        = "WRONG_DATE_BOUNDARY"
    MISSING_FILTER             = "MISSING_FILTER"
    SPURIOUS_FILTER            = "SPURIOUS_FILTER"
    WRONG_AGGREGATION          = "WRONG_AGGREGATION"
    COLUMN_SUBSTITUTION        = "COLUMN_SUBSTITUTION"
    DECOMPOSITION_FAILURE      = "DECOMPOSITION_FAILURE"
    # Business
    METRIC_DEFINITION_VIOLATION = "METRIC_DEFINITION_VIOLATION"
    MISSING_BUSINESS_FILTER    = "MISSING_BUSINESS_FILTER"
    CALENDAR_VIOLATION         = "CALENDAR_VIOLATION"
    SCOPE_VIOLATION            = "SCOPE_VIOLATION"
    STALE_LOGIC                = "STALE_LOGIC"

@dataclass(frozen=True)
class FailureModeMetadata:
    code: FailureMode
    layer: Layer
    description: str
    actionable: str

FAILURE_MODE_REGISTRY: dict[FailureMode, FailureModeMetadata] = {
    FailureMode.DIALECT_MISMATCH: FailureModeMetadata(
        code=FailureMode.DIALECT_MISMATCH,
        layer=Layer.SYNTAX,
        description="Valid SQL in one dialect, invalid in the target dialect.",
        actionable="Specify the correct dialect in your sqlprobe config.",
    ),
    FailureMode.NONEXISTENT_OBJECT: FailureModeMetadata(
        code=FailureMode.NONEXISTENT_OBJECT,
        layer=Layer.SYNTAX,
        description="References a table or column that does not exist in the schema.",
        actionable="Check schema annotations for correct table and column names.",
    ),
    FailureMode.CARDINALITY_EXPLOSION: FailureModeMetadata(
        code=FailureMode.CARDINALITY_EXPLOSION,
        layer=Layer.EXECUTION,
        description="Missing join condition produces a Cartesian product.",
        actionable="Verify all join conditions are present and correct.",
    ),
    FailureMode.SILENT_EMPTY: FailureModeMetadata(
        code=FailureMode.SILENT_EMPTY,
        layer=Layer.EXECUTION,
        description="Query returns zero rows when the correct answer is non-empty.",
        actionable="Check filter conditions for over-restriction.",
    ),
    FailureMode.TYPE_MISMATCH_COERCION: FailureModeMetadata(
        code=FailureMode.TYPE_MISMATCH_COERCION,
        layer=Layer.EXECUTION,
        description="Implicit type coercion produces wrong results silently.",
        actionable="Ensure column types match filter value types explicitly.",
    ),
    FailureMode.NULL_PROPAGATION: FailureModeMetadata(
        code=FailureMode.NULL_PROPAGATION,
        layer=Layer.EXECUTION,
        description="NULLs in aggregations cause unexpected exclusions without error.",
        actionable="Add COALESCE or IS NOT NULL guards where appropriate.",
    ),
    FailureMode.WRONG_GRAIN: FailureModeMetadata(
        code=FailureMode.WRONG_GRAIN,
        layer=Layer.SEMANTIC,
        description="Query aggregates at the wrong level of granularity.",
        actionable="Verify GROUP BY matches the requested grain in the question.",
    ),
    FailureMode.WRONG_DATE_BOUNDARY: FailureModeMetadata(
        code=FailureMode.WRONG_DATE_BOUNDARY,
        layer=Layer.SEMANTIC,
        description="Off-by-one in date ranges, wrong interval, or wrong anchor.",
        actionable="Check inclusive/exclusive bounds and fiscal vs calendar alignment.",
    ),
    FailureMode.MISSING_FILTER: FailureModeMetadata(
        code=FailureMode.MISSING_FILTER,
        layer=Layer.SEMANTIC,
        description="A filter implied by the question was not applied.",
        actionable="Add an assertion that requires this filter for similar questions.",
    ),
    FailureMode.SPURIOUS_FILTER: FailureModeMetadata(
        code=FailureMode.SPURIOUS_FILTER,
        layer=Layer.SEMANTIC,
        description="A filter was applied that the user did not request.",
        actionable="Review prompt context â€” model may be over-interpolating.",
    ),
    FailureMode.WRONG_AGGREGATION: FailureModeMetadata(
        code=FailureMode.WRONG_AGGREGATION,
        layer=Layer.SEMANTIC,
        description="Wrong aggregation function used (SUM vs COUNT, AVG vs SUM).",
        actionable="Add a semantic annotation specifying the correct aggregation.",
    ),
    FailureMode.COLUMN_SUBSTITUTION: FailureModeMetadata(
        code=FailureMode.COLUMN_SUBSTITUTION,
        layer=Layer.SEMANTIC,
        description="A plausible-but-wrong column was used (e.g. gross vs net revenue).",
        actionable="Add semantic annotations distinguishing similar columns.",
    ),
    FailureMode.DECOMPOSITION_FAILURE: FailureModeMetadata(
        code=FailureMode.DECOMPOSITION_FAILURE,
        layer=Layer.SEMANTIC,
        description="A multi-part question was only partially answered.",
        actionable="Break complex questions into separate evaluation cases.",
    ),
    FailureMode.METRIC_DEFINITION_VIOLATION: FailureModeMetadata(
        code=FailureMode.METRIC_DEFINITION_VIOLATION,
        layer=Layer.BUSINESS,
        description="Metric computed differently than the organization's canonical definition.",
        actionable="Add a semantic annotation with the exact metric definition.",
    ),
    FailureMode.MISSING_BUSINESS_FILTER: FailureModeMetadata(
        code=FailureMode.MISSING_BUSINESS_FILTER,
        layer=Layer.BUSINESS,
        description="An organization-specific implicit filter was not applied.",
        actionable="Add an assertion that requires this filter for relevant queries.",
    ),
    FailureMode.CALENDAR_VIOLATION: FailureModeMetadata(
        code=FailureMode.CALENDAR_VIOLATION,
        layer=Layer.BUSINESS,
        description="Calendar quarter used when the organization operates on fiscal calendar.",
        actionable="Add a fiscal calendar assertion and annotate fiscal year start.",
    ),
    FailureMode.SCOPE_VIOLATION: FailureModeMetadata(
        code=FailureMode.SCOPE_VIOLATION,
        layer=Layer.BUSINESS,
        description="Query accesses data outside the intended analytical scope or user role.",
        actionable="Add scope assertions tied to user_role in the case context.",
    ),
    FailureMode.STALE_LOGIC: FailureModeMetadata(
        code=FailureMode.STALE_LOGIC,
        layer=Layer.BUSINESS,
        description="Uses a business rule that was valid before a schema or definition change.",
        actionable="Review case effective dates and re-validate after schema changes.",
    ),
}
