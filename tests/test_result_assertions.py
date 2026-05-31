from pathlib import Path

from sqlprobe.core.case import EvaluationCase, ExpectedOutput
from sqlprobe.core.result import ExecutionResult
from sqlprobe.core.taxonomy import FailureMode, Severity
from sqlprobe.evaluators.assertions import evaluate_assertions
from sqlprobe.loader.assertion_loader import (
    Assertion,
    AssertionCheck,
    AssertionTrigger,
    load_assertions_from_dir,
)


REPO_ROOT = Path(__file__).parent.parent
ASSERTIONS_DIR = REPO_ROOT / "assertions"


def _case(
    *,
    question: str,
    assertions: list[str],
    sql: str = "SELECT 1",
) -> EvaluationCase:
    return EvaluationCase(
        id="test_case",
        version="1.0",
        question=question,
        expected=ExpectedOutput(sql=sql),
        assertions=assertions,
    )


def _execution_result(
    rows: list[dict],
    columns: list[str] | None = None,
) -> ExecutionResult:
    return ExecutionResult(
        success=True,
        rows=rows,
        row_count=len(rows),
        columns=columns or (list(rows[0].keys()) if rows else []),
        error=None,
        duration_ms=1.0,
        failure_mode=None,
    )


def _result_assertion(
    *,
    assertion_id: str = "custom_assertion",
    column_pattern: str,
    condition: str,
    failure_mode: FailureMode = FailureMode.WRONG_AGGREGATION,
    severity: Severity = Severity.WARNING,
) -> Assertion:
    return Assertion(
        id=assertion_id,
        description="Custom result assertion",
        trigger=AssertionTrigger(),
        assert_=AssertionCheck(
            result_column_satisfies={
                "column_pattern": column_pattern,
                "condition": condition,
            }
        ),
        severity=severity,
        failure_mode=failure_mode,
    )


def _churn_registry() -> dict[str, Assertion]:
    return load_assertions_from_dir(ASSERTIONS_DIR)


def test_result_assertion_passes_when_value_in_range():
    case = _case(
        question="What is monthly churn rate?",
        assertions=["churn_rate_bounded"],
    )
    execution = _execution_result([{"monthly_churn_rate": 0.05}])

    result = evaluate_assertions(
        case,
        "SELECT 0.05 AS monthly_churn_rate",
        _churn_registry(),
        execution_result=execution,
    )

    assert result.passed is True
    assert result.failures == []


def test_result_assertion_fails_when_value_out_of_range():
    case = _case(
        question="What is churn rate?",
        assertions=["churn_rate_bounded"],
    )
    execution = _execution_result([{"churn_rate": 1.5}])

    result = evaluate_assertions(
        case,
        "SELECT 1.5 AS churn_rate",
        _churn_registry(),
        execution_result=execution,
    )

    assert result.passed is False
    assert result.failures[0].failure_mode == FailureMode.NULL_PROPAGATION


def test_result_assertion_skips_when_no_matching_column():
    case = _case(
        question="What is churn rate?",
        assertions=["churn_rate_bounded"],
    )
    execution = _execution_result([{"revenue": 100, "count": 5}])

    result = evaluate_assertions(
        case,
        "SELECT 100 AS revenue, 5 AS count",
        _churn_registry(),
        execution_result=execution,
    )

    assert result.passed is True
    assert result.failures == []


def test_result_assertion_null_value_maps_to_null_propagation():
    case = _case(
        question="What is churn rate?",
        assertions=["churn_rate_bounded"],
    )
    execution = _execution_result([{"churn_rate": None}])

    result = evaluate_assertions(
        case,
        "SELECT NULL AS churn_rate",
        _churn_registry(),
        execution_result=execution,
    )

    assert result.passed is False
    assert result.failures[0].failure_mode == FailureMode.NULL_PROPAGATION
    assert result.failures[0].detail == (
        "Column 'churn_rate' is NULL, cannot evaluate condition "
        "'BETWEEN 0 AND 1'"
    )


def test_revenue_non_negative_passes():
    case = _case(
        question="What is revenue?",
        assertions=["revenue_non_negative"],
    )
    execution = _execution_result([{"net_revenue_sum": 3300000}])

    result = evaluate_assertions(
        case,
        "SELECT SUM(net_revenue) AS net_revenue_sum",
        _churn_registry(),
        execution_result=execution,
    )

    assert result.passed is True


def test_revenue_non_negative_fails():
    case = _case(
        question="What is revenue?",
        assertions=["revenue_non_negative"],
    )
    execution = _execution_result([{"net_revenue_sum": -500}])

    result = evaluate_assertions(
        case,
        "SELECT SUM(net_revenue) AS net_revenue_sum",
        _churn_registry(),
        execution_result=execution,
    )

    assert result.passed is False
    assert result.failures[0].failure_mode == FailureMode.WRONG_AGGREGATION


def test_condition_greater_than():
    assertion = _result_assertion(
        assertion_id="greater_than",
        column_pattern="value",
        condition="> 100",
    )
    case = _case(question="Check value", assertions=["greater_than"])

    passing = evaluate_assertions(
        case,
        "SELECT 200 AS value",
        {"greater_than": assertion},
        execution_result=_execution_result([{"value": 200}]),
    )
    failing = evaluate_assertions(
        case,
        "SELECT 50 AS value",
        {"greater_than": assertion},
        execution_result=_execution_result([{"value": 50}]),
    )

    assert passing.passed is True
    assert failing.passed is False


def test_condition_is_not_null():
    assertion = _result_assertion(
        assertion_id="is_not_null",
        column_pattern="value",
        condition="IS NOT NULL",
    )
    case = _case(question="Check value", assertions=["is_not_null"])

    passing = evaluate_assertions(
        case,
        "SELECT 42 AS value",
        {"is_not_null": assertion},
        execution_result=_execution_result([{"value": 42}]),
    )
    failing = evaluate_assertions(
        case,
        "SELECT NULL AS value",
        {"is_not_null": assertion},
        execution_result=_execution_result([{"value": None}]),
    )

    assert passing.passed is True
    assert failing.passed is False


def test_condition_is_null():
    assertion = _result_assertion(
        assertion_id="is_null",
        column_pattern="value",
        condition="IS NULL",
    )
    case = _case(question="Check value", assertions=["is_null"])

    passing = evaluate_assertions(
        case,
        "SELECT NULL AS value",
        {"is_null": assertion},
        execution_result=_execution_result([{"value": None}]),
    )
    failing = evaluate_assertions(
        case,
        "SELECT 42 AS value",
        {"is_null": assertion},
        execution_result=_execution_result([{"value": 42}]),
    )

    assert passing.passed is True
    assert failing.passed is False


def test_condition_between():
    assertion = _result_assertion(
        assertion_id="between",
        column_pattern="value",
        condition="BETWEEN 0 AND 1",
    )
    case = _case(question="Check value", assertions=["between"])

    passing = evaluate_assertions(
        case,
        "SELECT 0.5 AS value",
        {"between": assertion},
        execution_result=_execution_result([{"value": 0.5}]),
    )
    failing = evaluate_assertions(
        case,
        "SELECT 1.5 AS value",
        {"between": assertion},
        execution_result=_execution_result([{"value": 1.5}]),
    )

    assert passing.passed is True
    assert failing.passed is False


def test_backward_compat_no_execution_result():
    case = _case(
        question="What was revenue?",
        assertions=["revenue_excludes_test_accounts"],
    )

    result = evaluate_assertions(
        case,
        "SELECT SUM(net_revenue) FROM transactions t",
        _churn_registry(),
    )

    assert result.passed is False
    assert result.failures[0].failure_mode == (
        FailureMode.MISSING_BUSINESS_FILTER
    )


def test_structural_and_result_assertions_combined():
    case = _case(
        question="What was revenue?",
        assertions=["revenue_excludes_test_accounts", "revenue_non_negative"],
    )
    execution = _execution_result([{"net_revenue_sum": -500}])

    result = evaluate_assertions(
        case,
        "SELECT SUM(amount) AS net_revenue_sum FROM transactions t",
        _churn_registry(),
        execution_result=execution,
    )

    assert result.passed is False
    assert [failure.failure_mode for failure in result.failures] == [
        FailureMode.MISSING_BUSINESS_FILTER,
        FailureMode.WRONG_AGGREGATION,
    ]
