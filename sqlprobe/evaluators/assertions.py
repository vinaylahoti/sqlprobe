from __future__ import annotations

from typing import Any

import sqlglot
from sqlglot import exp

from ..core.case import EvaluationCase
from ..core.result import AssertionFailure, LayerResult
from ..core.taxonomy import FailureMode, Layer, Severity
from ..loader.assertion_loader import Assertion, AssertionCheck, AssertionTrigger


COMPARISON_EXPRESSIONS = (exp.EQ, exp.NEQ, exp.GT, exp.GTE, exp.LT, exp.LTE)

COMPARISON_OPERATORS = {
    exp.EQ: "=",
    exp.NEQ: "!=",
    exp.GT: ">",
    exp.GTE: ">=",
    exp.LT: "<",
    exp.LTE: "<=",
}

AGGREGATION_EXPRESSIONS = {
    "SUM": exp.Sum,
    "COUNT": exp.Count,
    "AVG": exp.Avg,
    "MIN": exp.Min,
    "MAX": exp.Max,
}


def evaluate_assertions(
    *,
    case: EvaluationCase,
    sql: str,
    assertion_registry: dict[str, Assertion],
) -> LayerResult:
    failures: list[AssertionFailure] = []

    try:
        tree = sqlglot.parse_one(sql)
    except Exception as exc:
        return LayerResult(
            layer=Layer.BUSINESS,
            passed=False,
            failures=[
                AssertionFailure(
                    assertion_id="assertion_parse",
                    detail=f"Could not parse SQL for assertion evaluation: {exc}",
                    failure_mode=FailureMode.DIALECT_MISMATCH,
                    severity=Severity.CRITICAL,
                )
            ],
        )

    for assertion_id in case.assertions:
        assertion = assertion_registry.get(assertion_id)
        if assertion is None:
            failures.append(
                AssertionFailure(
                    assertion_id=assertion_id,
                    detail="Assertion not found in registry",
                    failure_mode=None,
                    severity=Severity.WARNING,
                )
            )
            continue

        if not _triggers_match(sql, case.question, assertion.trigger):
            continue

        failures.extend(_evaluate_assertion(tree, sql, assertion))

    return LayerResult(
        layer=Layer.BUSINESS,
        passed=not failures,
        failures=failures,
    )


def _triggers_match(
    sql: str,
    question: str,
    trigger: AssertionTrigger,
) -> bool:
    sql_lower = sql.lower()
    question_lower = question.lower()

    if trigger.sql_references_any and not any(
        reference.lower() in sql_lower for reference in trigger.sql_references_any
    ):
        return False

    if trigger.question_contains_any and not any(
        value.lower() in question_lower for value in trigger.question_contains_any
    ):
        return False

    if trigger.question_not_contains and any(
        value.lower() in question_lower for value in trigger.question_not_contains
    ):
        return False

    return True


def _evaluate_assertion(
    tree: exp.Expression,
    sql: str,
    assertion: Assertion,
) -> list[AssertionFailure]:
    failures: list[AssertionFailure] = []
    check = assertion.assert_

    if check.sql_contains_filter is not None:
        passed = _sql_contains_filter(tree, check.sql_contains_filter)
        if not passed:
            failures.append(
                _make_failure(
                    assertion=assertion,
                    detail=(
                        "Expected filter not found: "
                        f"{_format_filter_spec(check.sql_contains_filter)}"
                    ),
                )
            )

    if check.no_select_star is True and _contains_select_star(tree):
        failures.append(
            _make_failure(
                assertion=assertion,
                detail="SELECT * is not allowed",
            )
        )

    if check.requires_column is not None and not _text_contains(
        sql, check.requires_column
    ):
        failures.append(
            _make_failure(
                assertion=assertion,
                detail=f"Required column not found: {check.requires_column}",
            )
        )

    if check.sql_excludes_column is not None and _text_contains(
        sql, check.sql_excludes_column
    ):
        failures.append(
            _make_failure(
                assertion=assertion,
                detail=f"Excluded column found: {check.sql_excludes_column}",
            )
        )

    if check.aggregation_type is not None and not _contains_aggregation(
        tree, check.aggregation_type
    ):
        failures.append(
            _make_failure(
                assertion=assertion,
                detail=f"Required aggregation not found: {check.aggregation_type}",
            )
        )

    return failures


def _sql_contains_filter(tree: exp.Expression, filter_spec: dict[str, Any]) -> bool:
    expected_operator = filter_spec.get("operator")

    for node in tree.walk():
        if not isinstance(node, COMPARISON_EXPRESSIONS):
            continue

        operator = COMPARISON_OPERATORS[type(node)]
        if expected_operator is not None and operator != expected_operator:
            continue

        if _comparison_side_matches(node.left, node.right, filter_spec):
            return True
        if _comparison_side_matches(node.right, node.left, filter_spec):
            return True

    return False


def _comparison_side_matches(
    column_expr: exp.Expression,
    value_expr: exp.Expression,
    filter_spec: dict[str, Any],
) -> bool:
    expected_column = str(filter_spec.get("column", ""))
    expected_value = filter_spec.get("value")
    return _column_matches(column_expr, expected_column) and _value_matches(
        value_expr, expected_value
    )


def _column_matches(column_expr: exp.Expression, expected_column: str) -> bool:
    expected = expected_column.lower()
    expected_name = expected.split(".")[-1]

    if isinstance(column_expr, exp.Column):
        column_sql = column_expr.sql().lower()
        column_name = column_expr.name.lower()
        return column_sql == expected or column_name == expected_name

    column_sql = column_expr.sql().lower()
    return column_sql == expected or column_sql.endswith(f".{expected_name}")


def _value_matches(value_expr: exp.Expression, expected_value: Any) -> bool:
    if isinstance(value_expr, exp.Boolean):
        return value_expr.this is expected_value

    if isinstance(value_expr, exp.Literal):
        literal_value = value_expr.this
        if isinstance(expected_value, str):
            return str(literal_value).lower() == expected_value.lower()
        return str(literal_value).lower() == str(expected_value).lower()

    return value_expr.sql().strip("'\"").lower() == str(expected_value).lower()


def _contains_select_star(tree: exp.Expression) -> bool:
    return any(isinstance(node, exp.Star) for node in tree.walk())


def _contains_aggregation(tree: exp.Expression, aggregation_type: str) -> bool:
    aggregation_class = AGGREGATION_EXPRESSIONS.get(aggregation_type.upper())
    if aggregation_class is None:
        return False
    return any(isinstance(node, aggregation_class) for node in tree.walk())


def _text_contains(sql: str, value: str) -> bool:
    return value.lower() in sql.lower()


def _format_filter_spec(filter_spec: dict[str, Any]) -> str:
    return (
        f"{filter_spec.get('column')} "
        f"{filter_spec.get('operator', '=')} "
        f"{filter_spec.get('value')}"
    )


def _make_failure(
    *,
    assertion: Assertion,
    detail: str,
) -> AssertionFailure:
    return AssertionFailure(
        assertion_id=assertion.id,
        detail=detail,
        failure_mode=assertion.failure_mode,
        severity=assertion.severity,
    )
