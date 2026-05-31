from sqlprobe.evaluators.judge import evaluate_with_judge
from sqlprobe.regression.baseline import compare_baseline, create_baseline

import pytest


def test_evaluate_with_judge_returns_skipped_response():
    result = evaluate_with_judge()

    assert result == {
        "skipped": True,
        "reason": "LLM judge not implemented in v0.0.1",
    }


def test_create_baseline_raises_not_implemented():
    with pytest.raises(
        NotImplementedError,
        match="Baseline comparison is planned for a future release.",
    ):
        create_baseline()


def test_compare_baseline_raises_not_implemented():
    with pytest.raises(
        NotImplementedError,
        match="Baseline comparison is planned for a future release.",
    ):
        compare_baseline()
