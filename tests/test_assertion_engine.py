from pathlib import Path

from sqlprobe.core.case import EvaluationCase, ExpectedOutput
from sqlprobe.core.taxonomy import FailureMode, Layer, Severity
from sqlprobe.evaluators.assertions import _triggers_match, evaluate_assertions
from sqlprobe.loader.assertion_loader import (
    Assertion,
    AssertionCheck,
    AssertionTrigger,
    load_assertions_from_dir,
)
from sqlprobe.loader.case_loader import load_cases_from_dir


def _case(assertions: list[str], question: str = "What was revenue?") -> EvaluationCase:
    return EvaluationCase(
        id="test",
        version="1.0",
        question=question,
        expected=ExpectedOutput(sql="SELECT 1"),
        assertions=assertions,
    )


def _assertion(
    *,
    assertion_id: str = "a1",
    trigger: AssertionTrigger | None = None,
    check: AssertionCheck | None = None,
    failure_mode: FailureMode = FailureMode.MISSING_FILTER,
    severity: Severity = Severity.CRITICAL,
) -> Assertion:
    return Assertion(
        id=assertion_id,
        description="test assertion",
        trigger=trigger or AssertionTrigger(),
        assert_=check or AssertionCheck(),
        severity=severity,
        failure_mode=failure_mode,
    )


def test_trigger_match_by_sql_text():
    trigger = AssertionTrigger(sql_references_any=["revenue"])

    assert _triggers_match("SELECT net_revenue FROM transactions", "", trigger)


def test_trigger_match_by_question_text():
    trigger = AssertionTrigger(question_contains_any=["revenue"])

    assert _triggers_match("SELECT 1", "Show revenue for Q1", trigger)


def test_trigger_skip_when_trigger_not_matched():
    assertion = _assertion(
        trigger=AssertionTrigger(sql_references_any=["revenue"]),
        check=AssertionCheck(no_select_star=True),
    )

    result = evaluate_assertions(
        case=_case(["a1"]),
        sql="SELECT * FROM users",
        assertion_registry={"a1": assertion},
    )

    assert result.layer == Layer.BUSINESS
    assert result.passed is True
    assert result.failures == []


def test_filter_present_passes():
    assertion = _assertion(
        check=AssertionCheck(
            sql_contains_filter={
                "column": "accounts.is_test",
                "operator": "=",
                "value": False,
            }
        )
    )

    result = evaluate_assertions(
        case=_case(["a1"]),
        sql=(
            "SELECT SUM(t.net_revenue) "
            "FROM transactions t JOIN accounts a ON t.account_id = a.id "
            "WHERE a.is_test = false"
        ),
        assertion_registry={"a1": assertion},
    )

    assert result.passed is True


def test_missing_filter_fails():
    assertion = _assertion(
        check=AssertionCheck(
            sql_contains_filter={
                "column": "accounts.is_test",
                "operator": "=",
                "value": False,
            }
        ),
        failure_mode=FailureMode.MISSING_BUSINESS_FILTER,
    )

    result = evaluate_assertions(
        case=_case(["a1"]),
        sql="SELECT SUM(t.net_revenue) FROM transactions t WHERE t.segment = 'enterprise'",
        assertion_registry={"a1": assertion},
    )

    assert result.passed is False
    assert result.failures[0].failure_mode == FailureMode.MISSING_BUSINESS_FILTER


def test_select_star_fails():
    assertion = _assertion(check=AssertionCheck(no_select_star=True))

    result = evaluate_assertions(
        case=_case(["a1"]),
        sql="SELECT * FROM transactions",
        assertion_registry={"a1": assertion},
    )

    assert result.passed is False
    assert result.failures[0].assertion_id == "a1"


def test_sql_excludes_column_fails():
    assertion = _assertion(
        check=AssertionCheck(sql_excludes_column="created_at"),
        failure_mode=FailureMode.COLUMN_SUBSTITUTION,
    )

    result = evaluate_assertions(
        case=_case(["a1"]),
        sql="SELECT SUM(net_revenue) FROM transactions WHERE created_at >= '2024-01-01'",
        assertion_registry={"a1": assertion},
    )

    assert result.passed is False
    assert result.failures[0].failure_mode == FailureMode.COLUMN_SUBSTITUTION


def test_unknown_assertion_id_returns_warning_failure():
    result = evaluate_assertions(
        case=_case(["missing_assertion"]),
        sql="SELECT 1",
        assertion_registry={},
    )

    assert result.passed is False
    assert result.failures[0].assertion_id == "missing_assertion"
    assert result.failures[0].detail == "Assertion not found in registry"
    assert result.failures[0].severity == Severity.WARNING


def test_requires_column_fails_when_missing():
    assertion = _assertion(check=AssertionCheck(requires_column="date"))

    result = evaluate_assertions(
        case=_case(["a1"]),
        sql="SELECT * FROM orders",
        assertion_registry={"a1": assertion},
    )

    assert result.passed is False


def test_aggregation_type_passes_when_present():
    assertion = _assertion(check=AssertionCheck(aggregation_type="SUM"))

    result = evaluate_assertions(
        case=_case(["a1"]),
        sql="SELECT SUM(amount) FROM transactions",
        assertion_registry={"a1": assertion},
    )

    assert result.passed is True


def test_revenue_example_expected_sql_passes_with_real_files():
    assertions = load_assertions_from_dir(Path("assertions"))
    cases = {case.id: case for case in load_cases_from_dir(Path("cases/examples"))}
    case = cases["revenue_q1_enterprise"]

    result = evaluate_assertions(
        case=case,
        sql=case.expected.sql or "",
        assertion_registry=assertions,
    )

    assert result.passed is True


def test_revenue_demo_sql_fails_with_real_files():
    assertions = load_assertions_from_dir(Path("assertions"))
    cases = {case.id: case for case in load_cases_from_dir(Path("cases/examples"))}
    case = cases["revenue_q1_enterprise"]

    result = evaluate_assertions(
        case=case,
        sql=(
            "SELECT SUM(amount) "
            "FROM transactions t "
            "JOIN accounts a ON t.account_id = a.id "
            "WHERE a.segment = 'enterprise'"
        ),
        assertion_registry=assertions,
    )

    failure_modes = {failure.failure_mode for failure in result.failures}
    assert FailureMode.MISSING_BUSINESS_FILTER in failure_modes
    assert FailureMode.COLUMN_SUBSTITUTION in failure_modes
