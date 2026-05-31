import pathlib

from sqlprobe.adapters.duckdb import DuckDBAdapter
from sqlprobe.core.result import LayerResult
from sqlprobe.core.taxonomy import FailureMode
from sqlprobe.evaluators.assertions import evaluate_assertions
from sqlprobe.evaluators.execution import evaluate_execution
from sqlprobe.evaluators.syntax import evaluate_syntax
from sqlprobe.loader.assertion_loader import load_assertions_from_dir
from sqlprobe.loader.case_loader import load_case


REPO_ROOT = pathlib.Path(__file__).parent.parent
FIXTURE_DB = f"duckdb://{REPO_ROOT / 'fixtures' / 'warehouse.db'}"
CASES_DIR = REPO_ROOT / "cases" / "examples"
ASSERTIONS_DIR = REPO_ROOT / "assertions"


def _load_revenue_case():
    return load_case(CASES_DIR / "revenue_q1_enterprise.yaml")


def _load_churn_case():
    return load_case(CASES_DIR / "churn_rate_monthly.yaml")


def _execute(sql: str):
    with DuckDBAdapter(FIXTURE_DB) as adapter:
        return adapter.execute(sql)


def test_revenue_case_loads_correctly():
    case = _load_revenue_case()

    assert case.id == "revenue_q1_enterprise"
    assert case.expected.sql is not None
    assert len(case.expected.sql) > 0
    assert case.expected.result_shape is not None
    assert case.expected.result_shape.row_count == 1


def test_revenue_expected_sql_executes_successfully():
    case = _load_revenue_case()

    execution_result = _execute(case.expected.sql)

    assert execution_result.success is True
    assert execution_result.row_count == 1
    assert execution_result.error is None


def test_revenue_result_shape_passes():
    case = _load_revenue_case()
    execution_result = _execute(case.expected.sql)

    layer_result = evaluate_execution(
        execution_result,
        case.expected.result_shape,
    )

    assert layer_result.passed is True
    assert len(layer_result.failures) == 0


def test_revenue_bad_sql_fails_assertions():
    case = _load_revenue_case()
    assertion_registry = load_assertions_from_dir(ASSERTIONS_DIR)
    sql = """
    SELECT SUM(amount) FROM transactions t
    JOIN accounts a ON t.account_id = a.id
    WHERE a.segment = 'enterprise'
    """

    layer_result = evaluate_assertions(
        case=case,
        sql=sql,
        assertion_registry=assertion_registry,
    )

    assert layer_result.passed is False
    assert any(
        failure.failure_mode == FailureMode.MISSING_BUSINESS_FILTER
        for failure in layer_result.failures
    )


def test_revenue_bad_sql_executes_but_shape_fails():
    case = _load_revenue_case()
    sql = """
    SELECT SUM(amount) FROM transactions t
    JOIN accounts a ON t.account_id = a.id
    WHERE a.segment = 'enterprise'
    """

    execution_result = _execute(sql)
    assert execution_result.success is True

    layer_result = evaluate_execution(
        execution_result,
        case.expected.result_shape,
    )

    assert isinstance(layer_result, LayerResult)


def test_full_pipeline_revenue_expected_sql():
    case = _load_revenue_case()
    assertion_registry = load_assertions_from_dir(ASSERTIONS_DIR)

    syntax_result = evaluate_syntax(case.expected.sql)
    assertion_result = evaluate_assertions(
        case=case,
        sql=case.expected.sql,
        assertion_registry=assertion_registry,
    )
    execution_result = _execute(case.expected.sql)
    execution_layer_result = evaluate_execution(
        execution_result,
        case.expected.result_shape,
    )

    assert syntax_result.passed is True
    assert assertion_result.passed is True
    assert execution_layer_result.passed is True


def test_churn_case_loads_correctly():
    case = _load_churn_case()

    assert case.id == "churn_rate_monthly"
    assert case.expected.sql is not None


def test_churn_expected_sql_executes_without_error():
    case = _load_churn_case()

    execution_result = _execute(case.expected.sql)

    assert execution_result.success is True
    assert execution_result.error is None


def test_adapter_closes_cleanly():
    with DuckDBAdapter(FIXTURE_DB) as adapter:
        execution_result = adapter.execute("SELECT 1 AS ok")

    assert execution_result.success is True
