from sqlprobe.core.taxonomy import FailureMode, Layer
from sqlprobe.evaluators.syntax import evaluate_syntax


def test_valid_select_one_passes():
    result = evaluate_syntax("SELECT 1")

    assert result.layer == Layer.SYNTAX
    assert result.passed is True
    assert result.failures == []


def test_empty_sql_fails():
    result = evaluate_syntax("")

    assert result.layer == Layer.SYNTAX
    assert result.passed is False
    assert result.failures[0].failure_mode == FailureMode.DIALECT_MISMATCH


def test_invalid_sql_fails():
    result = evaluate_syntax("SELECT FROM WHERE")

    assert result.layer == Layer.SYNTAX
    assert result.passed is False
    assert result.failures[0].failure_mode == FailureMode.DIALECT_MISMATCH


def test_bigquery_syntax_passes_under_bigquery_dialect():
    result = evaluate_syntax(
        "SELECT DATE_TRUNC(DATE '2024-01-15', MONTH)",
        dialect="bigquery",
    )

    assert result.layer == Layer.SYNTAX
    assert result.passed is True


def test_nonexistent_table_still_passes_syntax_validation():
    result = evaluate_syntax("SELECT id FROM table_that_does_not_exist")

    assert result.layer == Layer.SYNTAX
    assert result.passed is True
