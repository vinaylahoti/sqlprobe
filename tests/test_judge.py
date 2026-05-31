from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from sqlprobe.core.result import (
    DimensionResult,
    JudgeResult,
    compute_overall_score,
    compute_overall_verdict,
)
from sqlprobe.core.taxonomy import FailureMode
from sqlprobe.evaluators.judge import JUDGE_MODEL, JudgeInput, SQLProbeJudge


VALID_JUDGE_RESPONSE = {
    "overall_verdict": "FAIL",
    "overall_score": 0.6,
    "confidence": "high",
    "dimensions": [
        {
            "dimension": "metric_definition",
            "verdict": "FAIL",
            "failure_mode": "COLUMN_SUBSTITUTION",
            "evidence": "Query uses gross amount instead of net_revenue.",
            "confidence": "high",
        },
        {
            "dimension": "date_boundary",
            "verdict": "PASS",
            "failure_mode": None,
            "evidence": "Date range looks correct.",
            "confidence": "high",
        },
        {
            "dimension": "segment_filter",
            "verdict": "FAIL",
            "failure_mode": "MISSING_BUSINESS_FILTER",
            "evidence": "Missing is_test = false filter.",
            "confidence": "high",
        },
        {
            "dimension": "aggregation",
            "verdict": "PASS",
            "failure_mode": None,
            "evidence": "SUM is appropriate here.",
            "confidence": "medium",
        },
        {
            "dimension": "grain",
            "verdict": "PASS",
            "failure_mode": None,
            "evidence": "Grain looks correct.",
            "confidence": "high",
        },
    ],
}


def make_judge() -> SQLProbeJudge:
    judge = SQLProbeJudge.__new__(SQLProbeJudge)
    judge._model = JUDGE_MODEL
    judge._api_key = "test-key"
    return judge


def make_judge_input() -> JudgeInput:
    return JudgeInput(
        question="What was Q1 revenue?",
        generated_sql="SELECT SUM(amount) FROM transactions",
    )


def make_dimension(verdict: str) -> DimensionResult:
    return DimensionResult(
        dimension="metric_definition",
        verdict=verdict,
        failure_mode=None,
        evidence="test evidence",
        confidence="high",
    )


def test_judge_raises_without_api_key():
    with patch("os.environ.get", return_value=None):
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            SQLProbeJudge()


def test_judge_returns_judge_result():
    judge = make_judge()
    with patch.object(judge, "_call_api", return_value=json.dumps(VALID_JUDGE_RESPONSE)):
        result = judge.evaluate(make_judge_input())

    assert isinstance(result, JudgeResult)
    assert result.skipped is False


def test_judge_overall_verdict_recomputed():
    response = dict(VALID_JUDGE_RESPONSE)
    response["overall_verdict"] = "PASS"
    judge = make_judge()

    with patch.object(judge, "_call_api", return_value=json.dumps(response)):
        result = judge.evaluate(make_judge_input())

    assert result.overall_verdict == "FAIL"


def test_judge_overall_score_recomputed():
    judge = make_judge()

    with patch.object(judge, "_call_api", return_value=json.dumps(VALID_JUDGE_RESPONSE)):
        result = judge.evaluate(make_judge_input())

    assert result.overall_score == 0.6


def test_judge_dimensions_parsed():
    judge = make_judge()

    with patch.object(judge, "_call_api", return_value=json.dumps(VALID_JUDGE_RESPONSE)):
        result = judge.evaluate(make_judge_input())

    assert len(result.dimensions) == 5
    dim = result.dimensions[0]
    assert dim.dimension == "metric_definition"
    assert dim.verdict == "FAIL"
    assert dim.failure_mode == FailureMode.COLUMN_SUBSTITUTION


def test_judge_invalid_failure_mode_ignored():
    response = {
        "confidence": "high",
        "dimensions": [
            {
                "dimension": "metric_definition",
                "verdict": "FAIL",
                "failure_mode": "NOT_A_REAL_MODE",
                "evidence": "Invalid taxonomy code.",
                "confidence": "high",
            }
        ],
    }
    judge = make_judge()

    with patch.object(judge, "_call_api", return_value=json.dumps(response)):
        result = judge.evaluate(make_judge_input())

    assert result.dimensions[0].failure_mode is None


def test_judge_api_exception_returns_skipped():
    judge = make_judge()

    with patch.object(judge, "_call_api", side_effect=Exception("network error")):
        result = judge.evaluate(make_judge_input())

    assert result.skipped is True
    assert result.overall_verdict == "SKIP"


def test_judge_parse_failure_returns_skipped():
    judge = make_judge()

    with patch.object(judge, "_call_api", return_value="this is not json at all"):
        result = judge.evaluate(make_judge_input())

    assert result.skipped is True


def test_judge_strips_markdown_fences():
    judge = make_judge()
    response = "```json\n" + json.dumps(VALID_JUDGE_RESPONSE) + "\n```"

    with patch.object(judge, "_call_api", return_value=response):
        result = judge.evaluate(make_judge_input())

    assert result.skipped is False
    assert len(result.dimensions) == 5


def test_compute_overall_score_all_pass():
    dimensions = [make_dimension("PASS") for _ in range(5)]

    assert compute_overall_score(dimensions) == 1.0


def test_compute_overall_score_with_skip():
    dimensions = [
        make_dimension("PASS"),
        make_dimension("PASS"),
        make_dimension("PASS"),
        make_dimension("FAIL"),
        make_dimension("SKIP"),
    ]

    assert compute_overall_score(dimensions) == 0.75


def test_compute_overall_verdict_any_fail():
    dimensions = [make_dimension("PASS"), make_dimension("FAIL"), make_dimension("PASS")]

    assert compute_overall_verdict(dimensions) == "FAIL"


def test_compute_overall_verdict_warn_no_fail():
    dimensions = [make_dimension("PASS"), make_dimension("WARN"), make_dimension("PASS")]

    assert compute_overall_verdict(dimensions) == "WARN"


def test_compute_overall_verdict_all_pass():
    dimensions = [make_dimension("PASS"), make_dimension("PASS")]

    assert compute_overall_verdict(dimensions) == "PASS"
