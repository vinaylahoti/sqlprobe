from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from ..core.case import EvaluationCase
from ..core.result import AssertionFailure, EvaluationResult, LayerResult
from ..core.taxonomy import FailureMode, Severity
from ..evaluators.assertions import evaluate_assertions
from ..evaluators.execution import evaluate_execution
from ..evaluators.syntax import evaluate_syntax
from ..loader.assertion_loader import Assertion, load_assertions_from_dir
from ..loader.case_loader import load_case, load_cases_from_dir


app = typer.Typer(help="SQLProbe - Production trust layer for AI-generated SQL")
console = Console()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_cases(path: Path) -> list[EvaluationCase]:
    if path.is_file():
        return [load_case(path)]
    if path.is_dir():
        return load_cases_from_dir(path)
    raise typer.BadParameter(f"Path does not exist: {path}")


def _load_assertions() -> dict[str, Assertion]:
    return load_assertions_from_dir(_repo_root() / "assertions")


def _collect_failures(
    syntax_result: LayerResult,
    assertion_result: LayerResult,
) -> list[AssertionFailure]:
    return [*syntax_result.failures, *assertion_result.failures]


def _overall_severity(failures: list[AssertionFailure]) -> Optional[Severity]:
    if any(failure.severity == Severity.CRITICAL for failure in failures):
        return Severity.CRITICAL
    if any(failure.severity == Severity.WARNING for failure in failures):
        return Severity.WARNING
    if any(failure.severity == Severity.INFO for failure in failures):
        return Severity.INFO
    return None


def _build_result(
    *,
    case: EvaluationCase,
    generated_sql: str,
    syntax_result: LayerResult,
    assertion_result: LayerResult,
    execution_result: LayerResult,
) -> EvaluationResult:
    failures = _collect_failures(syntax_result, assertion_result)
    failure_modes = [
        failure.failure_mode
        for failure in failures
        if failure.failure_mode is not None
    ]
    return EvaluationResult(
        case_id=case.id,
        generated_sql=generated_sql,
        passed=syntax_result.passed and assertion_result.passed,
        syntax=syntax_result,
        execution=execution_result,
        business=assertion_result,
        failure_modes=failure_modes,
        overall_severity=_overall_severity(failures),
    )


def _print_case_result(result: EvaluationResult) -> None:
    status = "PASS" if result.passed else "FAIL"
    style = "green" if result.passed else "red"
    console.print(f"{status}  {result.case_id}", style=style)

    failures: list[AssertionFailure] = []
    if result.syntax is not None:
        failures.extend(result.syntax.failures)
    if result.business is not None:
        failures.extend(result.business.failures)

    for failure in failures:
        failure_mode = (
            failure.failure_mode.value
            if failure.failure_mode is not None
            else "UNKNOWN"
        )
        console.print(f"  Failure Mode: {failure_mode}")
        console.print(f"  Assertion: {failure.assertion_id}")
        console.print(f"  Detail: {failure.detail}")


def _write_json_report(path: Path, results: list[EvaluationResult]) -> None:
    report = [
        {
            "case_id": result.case_id,
            "passed": result.passed,
            "failure_modes": [
                failure_mode.value for failure_mode in result.failure_modes
            ],
        }
        for result in results
    ]
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")


@app.command()
def validate(path: Path) -> None:
    assertion_registry = _load_assertions()
    had_error = False

    try:
        cases = _load_cases(path)
    except Exception as exc:
        console.print(f"ERR  {path}")
        console.print(f"     {exc}")
        raise typer.Exit(1) from exc

    for case in cases:
        unknown_assertions = [
            assertion_id
            for assertion_id in case.assertions
            if assertion_id not in assertion_registry
        ]
        if unknown_assertions:
            had_error = True
            console.print(f"ERR  {case.id}", style="red")
            for assertion_id in unknown_assertions:
                console.print(f"     Unknown assertion: {assertion_id}")
        else:
            console.print(f"OK   {case.id}", style="green")

    if had_error:
        raise typer.Exit(1)


def _run_cases(
    path: Path,
    sql: Optional[str] = None,
    dialect: str = "ansi",
    output: Optional[Path] = None,
    fail_on: Optional[str] = None,
) -> None:
    cases = _load_cases(path)
    assertion_registry = _load_assertions()
    results: list[EvaluationResult] = []

    for case in cases:
        generated_sql = sql if sql is not None else case.expected.sql
        if not generated_sql:
            console.print(f"FAIL  {case.id}", style="red")
            console.print("  Failure Mode: DIALECT_MISMATCH")
            console.print("  Assertion: sql")
            console.print("  Detail: No SQL provided for evaluation")
            raise typer.Exit(1)

        syntax_result = evaluate_syntax(generated_sql, dialect=dialect)
        assertion_result = (
            evaluate_assertions(
                case=case,
                sql=generated_sql,
                assertion_registry=assertion_registry,
            )
            if syntax_result.passed
            else LayerResult(layer=syntax_result.layer, passed=True, skipped=True)
        )
        execution_result = evaluate_execution(generated_sql)
        result = _build_result(
            case=case,
            generated_sql=generated_sql,
            syntax_result=syntax_result,
            assertion_result=assertion_result,
            execution_result=execution_result,
        )
        results.append(result)
        _print_case_result(result)

    critical_count = sum(
        1 for result in results if result.overall_severity == Severity.CRITICAL
    )
    passed_count = sum(1 for result in results if result.passed)
    failed_count = len(results) - passed_count

    console.print(f"Cases: {len(results)}")
    console.print(f"Passed: {passed_count}")
    console.print(f"Failed: {failed_count}")
    console.print(f"Critical: {critical_count}")

    if output is not None:
        _write_json_report(output, results)

    if fail_on == "critical" and critical_count > 0:
        raise typer.Exit(1)


@app.command()
def run(
    path: Path,
    sql: Optional[str] = typer.Option(None, "--sql"),
    dialect: str = typer.Option("ansi", "--dialect"),
    output: Optional[Path] = typer.Option(None, "--output"),
    fail_on: Optional[str] = typer.Option(None, "--fail-on"),
) -> None:
    _run_cases(
        path=path,
        sql=sql,
        dialect=dialect,
        output=output,
        fail_on=fail_on,
    )


@app.command()
def demo() -> None:
    demo_case = _repo_root() / "cases" / "examples" / "revenue_q1_enterprise.yaml"

    failing_sql = """SELECT SUM(amount)
FROM transactions t
JOIN accounts a ON t.account_id = a.id
WHERE a.segment = 'enterprise'"""

    passing_sql = """SELECT SUM(t.net_revenue)
FROM transactions t
JOIN accounts a ON t.account_id = a.id
WHERE a.segment IN ('ENT', 'ENTERPRISE')
  AND a.is_test = false
  AND t.recognized_at >= '2024-02-01'
  AND t.recognized_at < '2024-05-01'"""

    console.print("Demo: failing SQL")
    _run_cases(demo_case, sql=failing_sql)
    console.print("Demo: corrected SQL")
    _run_cases(demo_case, sql=passing_sql)


if __name__ == "__main__":
    app()
