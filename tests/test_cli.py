import json

from typer.testing import CliRunner

from sqlprobe.cli.main import app


runner = CliRunner()


def test_validate_succeeds_on_examples():
    result = runner.invoke(app, ["validate", "cases/examples/"])

    assert result.exit_code == 0
    assert "OK   churn_rate_monthly" in result.output
    assert "OK   revenue_q1_enterprise" in result.output


def test_run_succeeds_on_examples():
    result = runner.invoke(app, ["run", "cases/examples/"])

    assert result.exit_code == 0
    assert "PASS  churn_rate_monthly" in result.output
    assert "PASS  revenue_q1_enterprise" in result.output
    assert "Failed: 0" in result.output


def test_run_with_bad_revenue_sql_outputs_fail():
    result = runner.invoke(
        app,
        [
            "run",
            "cases/examples/revenue_q1_enterprise.yaml",
            "--sql",
            (
                "SELECT SUM(amount) "
                "FROM transactions t "
                "JOIN accounts a ON t.account_id = a.id "
                "WHERE a.segment = 'enterprise'"
            ),
        ],
    )

    assert result.exit_code == 0
    assert "FAIL  revenue_q1_enterprise" in result.output
    assert "MISSING_BUSINESS_FILTER" in result.output
    assert "COLUMN_SUBSTITUTION" in result.output


def test_json_report_generated(tmp_path):
    output = tmp_path / "report.json"

    result = runner.invoke(
        app,
        ["run", "cases/examples/", "--output", str(output)],
    )

    assert result.exit_code == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report == [
        {
            "case_id": "churn_rate_monthly",
            "passed": True,
            "failure_modes": [],
        },
        {
            "case_id": "revenue_q1_enterprise",
            "passed": True,
            "failure_modes": [],
        },
    ]


def test_demo_command_executes():
    result = runner.invoke(app, ["demo"])

    assert result.exit_code == 0
    assert "Demo: failing SQL" in result.output
    assert "FAIL  revenue_q1_enterprise" in result.output
    assert "Demo: corrected SQL" in result.output
    assert "PASS  revenue_q1_enterprise" in result.output


def test_fail_on_critical_exits_nonzero():
    result = runner.invoke(
        app,
        [
            "run",
            "cases/examples/revenue_q1_enterprise.yaml",
            "--sql",
            (
                "SELECT SUM(amount) "
                "FROM transactions t "
                "JOIN accounts a ON t.account_id = a.id "
                "WHERE a.segment = 'enterprise'"
            ),
            "--fail-on",
            "critical",
        ],
    )

    assert result.exit_code == 1
    assert "Critical: 1" in result.output
