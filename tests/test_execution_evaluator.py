from sqlprobe.core.case import ExpectedResultShape
from sqlprobe.core.result import ExecutionResult
from sqlprobe.core.taxonomy import FailureMode, Layer, Severity
from sqlprobe.evaluators.execution import evaluate_execution


def _execution_result(
    *,
    success=True,
    rows=None,
    row_count=None,
    columns=None,
    error=None,
    failure_mode=None,
):
    if rows is not None and row_count is None:
        row_count = len(rows)
    if rows is not None and columns is None:
        columns = list(rows[0].keys()) if rows else []

    return ExecutionResult(
        success=success,
        rows=rows,
        row_count=row_count,
        columns=columns,
        error=error,
        duration_ms=1.0,
        failure_mode=failure_mode,
    )


def test_execution_error_returns_failed_layer():
    execution = _execution_result(
        success=False,
        rows=None,
        row_count=None,
        columns=None,
        error="Binder Error: missing column",
    )

    result = evaluate_execution(execution)

    assert result.layer == Layer.EXECUTION
    assert result.passed is False
    assert result.skipped is False
    assert result.failures[0].assertion_id == "execution_error"
    assert result.failures[0].detail == "Binder Error: missing column"
    assert (
        result.failures[0].failure_mode
        == FailureMode.TYPE_MISMATCH_COERCION
    )
    assert result.failures[0].severity == Severity.CRITICAL


def test_cardinality_explosion_returns_failed_layer():
    execution = _execution_result(
        rows=[{"id": 1}],
        row_count=1_000_001,
        columns=["id"],
        failure_mode=FailureMode.CARDINALITY_EXPLOSION,
    )

    result = evaluate_execution(execution)

    assert result.passed is False
    assert result.failures[0].assertion_id == "cardinality_explosion"
    assert (
        result.failures[0].failure_mode
        == FailureMode.CARDINALITY_EXPLOSION
    )
    assert result.failures[0].severity == Severity.CRITICAL


def test_no_expected_shape_returns_passed():
    execution = _execution_result(rows=[{"val": 1}])

    result = evaluate_execution(execution)

    assert result.passed is True
    assert result.failures == []
    assert result.skipped is False


def test_exact_row_count_passes():
    execution = _execution_result(rows=[{"val": 1}])
    shape = ExpectedResultShape(row_count=1)

    result = evaluate_execution(execution, shape)

    assert result.passed is True
    assert result.failures == []


def test_row_count_mismatch_warns():
    execution = _execution_result(rows=[{"val": 1}, {"val": 2}])
    shape = ExpectedResultShape(row_count=1)

    result = evaluate_execution(execution, shape)

    assert result.passed is False
    assert result.failures[0].detail == "Expected 1 rows, got 2"
    assert result.failures[0].failure_mode == FailureMode.WRONG_GRAIN
    assert result.failures[0].severity == Severity.WARNING


def test_silent_empty_is_critical():
    execution = _execution_result(rows=[], row_count=0, columns=["val"])
    shape = ExpectedResultShape(row_count=1)

    result = evaluate_execution(execution, shape)

    assert result.passed is False
    assert result.failures[0].detail == "Expected 1 rows, got 0"
    assert result.failures[0].failure_mode == FailureMode.SILENT_EMPTY
    assert result.failures[0].severity == Severity.CRITICAL


def test_columns_present_missing_column_fails():
    execution = _execution_result(rows=[{"actual": 1}])
    shape = ExpectedResultShape(columns_present=["expected"])

    result = evaluate_execution(execution, shape)

    assert result.passed is False
    assert result.failures[0].failure_mode == FailureMode.COLUMN_SUBSTITUTION
    assert (
        result.failures[0].detail
        == "Expected column 'expected' not found in result. Got: ['actual']"
    )


def test_no_nulls_in_detects_null():
    execution = _execution_result(
        rows=[{"net_revenue": 1}, {"net_revenue": None}]
    )
    shape = ExpectedResultShape(no_nulls_in=["net_revenue"])

    result = evaluate_execution(execution, shape)

    assert result.passed is False
    assert result.failures[0].failure_mode == FailureMode.NULL_PROPAGATION
    assert result.failures[0].detail == (
        "Column 'net_revenue' contains NULL values"
    )
    assert result.failures[0].severity == Severity.WARNING


def test_value_range_passes():
    execution = _execution_result(rows=[{"net_revenue_sum": 3300000}])
    shape = ExpectedResultShape(
        value_range={"net_revenue_sum": {"min": 1000000, "max": 50000000}}
    )

    result = evaluate_execution(execution, shape)

    assert result.passed is True
    assert result.failures == []


def test_value_range_null_is_critical():
    execution = _execution_result(rows=[{"net_revenue_sum": None}])
    shape = ExpectedResultShape(
        value_range={"net_revenue_sum": {"min": 1000000, "max": 50000000}}
    )

    result = evaluate_execution(execution, shape)

    assert result.passed is False
    assert result.failures[0].failure_mode == FailureMode.NULL_PROPAGATION
    assert result.failures[0].severity == Severity.CRITICAL
    assert result.failures[0].detail == (
        "Value range column 'net_revenue_sum' is NULL"
    )


def test_value_range_out_of_range_warns():
    execution = _execution_result(rows=[{"net_revenue_sum": 999}])
    shape = ExpectedResultShape(
        value_range={"net_revenue_sum": {"min": 1000000, "max": 50000000}}
    )

    result = evaluate_execution(execution, shape)

    assert result.passed is False
    assert result.failures[0].failure_mode == FailureMode.WRONG_AGGREGATION
    assert result.failures[0].severity == Severity.WARNING
    assert result.failures[0].detail == (
        "Column 'net_revenue_sum' value 999 outside range "
        "[1000000, 50000000]"
    )


def test_multiple_failures_all_collected():
    execution = _execution_result(
        rows=[{"actual": None}],
        row_count=2,
        columns=["actual"],
    )
    shape = ExpectedResultShape(
        row_count=1,
        no_nulls_in=["actual"],
    )

    result = evaluate_execution(execution, shape)

    assert result.passed is False
    assert [failure.failure_mode for failure in result.failures] == [
        FailureMode.WRONG_GRAIN,
        FailureMode.NULL_PROPAGATION,
    ]
