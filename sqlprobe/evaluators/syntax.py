from __future__ import annotations

import sqlglot
import sqlglot.errors

from ..core.result import AssertionFailure, LayerResult
from ..core.taxonomy import FailureMode, Layer, Severity


SUPPORTED_DIALECTS = {
    "ansi",
    "bigquery",
    "snowflake",
    "redshift",
    "duckdb",
    "postgres",
    "mysql",
    "spark",
    "trino",
}


def evaluate_syntax(
    sql: str,
    dialect: str = "ansi",
) -> LayerResult:
    if dialect not in SUPPORTED_DIALECTS:
        return LayerResult(
            layer=Layer.SYNTAX,
            passed=False,
            failures=[
                AssertionFailure(
                    assertion_id="syntax_dialect",
                    detail=(
                        f"Unsupported dialect: '{dialect}'. "
                        f"Supported dialects: {', '.join(sorted(SUPPORTED_DIALECTS))}."
                    ),
                    failure_mode=FailureMode.DIALECT_MISMATCH,
                    severity=Severity.CRITICAL,
                )
            ],
        )

    if not sql or not sql.strip():
        return LayerResult(
            layer=Layer.SYNTAX,
            passed=False,
            failures=[
                AssertionFailure(
                    assertion_id="syntax_parse",
                    detail="SQL is empty.",
                    failure_mode=FailureMode.DIALECT_MISMATCH,
                    severity=Severity.CRITICAL,
                )
            ],
        )

    try:
        parse_dialect = None if dialect == "ansi" else dialect
        statements = sqlglot.parse(
            sql,
            dialect=parse_dialect,
            error_level=sqlglot.ErrorLevel.RAISE,
        )
    except sqlglot.errors.ParseError as exc:
        return LayerResult(
            layer=Layer.SYNTAX,
            passed=False,
            failures=[
                AssertionFailure(
                    assertion_id="syntax_parse",
                    detail=f"Parse error ({dialect}): {exc}",
                    failure_mode=FailureMode.DIALECT_MISMATCH,
                    severity=Severity.CRITICAL,
                )
            ],
        )

    if not statements or any(statement is None for statement in statements):
        return LayerResult(
            layer=Layer.SYNTAX,
            passed=False,
            failures=[
                AssertionFailure(
                    assertion_id="syntax_parse",
                    detail="SQL produced no parse tree.",
                    failure_mode=FailureMode.DIALECT_MISMATCH,
                    severity=Severity.CRITICAL,
                )
            ],
        )

    return LayerResult(
        layer=Layer.SYNTAX,
        passed=True,
    )
