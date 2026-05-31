from __future__ import annotations

from sqlprobe.core.case import ExpectedResultShape
from sqlprobe.core.result import (
    AssertionFailure,
    ExecutionResult,
    LayerResult,
)
from sqlprobe.core.taxonomy import FailureMode, Layer, Severity


_MISSING = object()


def evaluate_execution(
    execution_result: ExecutionResult,
    expected_shape: ExpectedResultShape | None = None,
) -> LayerResult:
    if isinstance(execution_result, str):
        return LayerResult(
            layer=Layer.EXECUTION,
            passed=True,
            skipped=True,
        )

    if not execution_result.success:
        return LayerResult(
            layer=Layer.EXECUTION,
            passed=False,
            failures=[
                AssertionFailure(
                    assertion_id="execution_error",
                    detail=execution_result.error or "Execution failed",
                    # TYPE_MISMATCH_COERCION is the closest existing taxonomy
                    # code for database-level execution errors in v0.0.2.
                    failure_mode=FailureMode.TYPE_MISMATCH_COERCION,
                    severity=Severity.CRITICAL,
                )
            ],
            skipped=False,
        )

    if execution_result.failure_mode == FailureMode.CARDINALITY_EXPLOSION:
        return LayerResult(
            layer=Layer.EXECUTION,
            passed=False,
            failures=[
                AssertionFailure(
                    assertion_id="cardinality_explosion",
                    detail=(
                        f"Query returned {execution_result.row_count} rows, "
                        "exceeding threshold"
                    ),
                    failure_mode=FailureMode.CARDINALITY_EXPLOSION,
                    severity=Severity.CRITICAL,
                )
            ],
            skipped=False,
        )

    if expected_shape is None:
        return LayerResult(
            layer=Layer.EXECUTION,
            passed=True,
            failures=[],
            skipped=False,
        )

    failures: list[AssertionFailure] = []

    if expected_shape.row_count is not None:
        if (
            execution_result.row_count == 0
            and expected_shape.row_count > 0
        ):
            failures.append(
                AssertionFailure(
                    assertion_id="row_count",
                    detail=f"Expected {expected_shape.row_count} rows, got 0",
                    failure_mode=FailureMode.SILENT_EMPTY,
                    severity=Severity.CRITICAL,
                )
            )
        elif execution_result.row_count != expected_shape.row_count:
            failures.append(
                AssertionFailure(
                    assertion_id="row_count",
                    detail=(
                        f"Expected {expected_shape.row_count} rows, "
                        f"got {execution_result.row_count}"
                    ),
                    failure_mode=FailureMode.WRONG_GRAIN,
                    severity=Severity.WARNING,
                )
            )

    if expected_shape.columns_present is not None:
        columns = execution_result.columns or []
        for col in expected_shape.columns_present:
            if col not in columns:
                failures.append(
                    AssertionFailure(
                        assertion_id="columns_present",
                        detail=(
                            f"Expected column '{col}' not found in result. "
                            f"Got: {execution_result.columns}"
                        ),
                        failure_mode=FailureMode.COLUMN_SUBSTITUTION,
                        severity=Severity.WARNING,
                    )
                )

    if (
        expected_shape.no_nulls_in is not None
        and execution_result.rows is not None
    ):
        for col in expected_shape.no_nulls_in:
            if any(row.get(col) is None for row in execution_result.rows):
                failures.append(
                    AssertionFailure(
                        assertion_id="no_nulls_in",
                        detail=f"Column '{col}' contains NULL values",
                        failure_mode=FailureMode.NULL_PROPAGATION,
                        severity=Severity.WARNING,
                    )
                )

    if (
        expected_shape.value_range is not None
        and execution_result.rows is not None
    ):
        for key, bounds in expected_shape.value_range.items():
            match = _find_value_range_match(execution_result.rows, key)
            if match is _MISSING:
                # Missing value range columns are checked separately by
                # columns_present when the case requires that behavior.
                continue

            value = match
            if value is None:
                failures.append(
                    AssertionFailure(
                        assertion_id="value_range",
                        detail=f"Value range column '{key}' is NULL",
                        failure_mode=FailureMode.NULL_PROPAGATION,
                        severity=Severity.CRITICAL,
                    )
                )
            elif value < bounds["min"] or value > bounds["max"]:
                failures.append(
                    AssertionFailure(
                        assertion_id="value_range",
                        detail=(
                            f"Column '{key}' value {value} outside range "
                            f"[{bounds['min']}, {bounds['max']}]"
                        ),
                        failure_mode=FailureMode.WRONG_AGGREGATION,
                        severity=Severity.WARNING,
                    )
                )

    return LayerResult(
        layer=Layer.EXECUTION,
        passed=len(failures) == 0,
        failures=failures,
        skipped=False,
    )


def _find_value_range_match(rows: list[dict], key: str):
    for row in rows:
        if key in row:
            return row[key]

        key_lower = key.lower()
        for column, value in row.items():
            if column.lower() == key_lower:
                return value

    return _MISSING
