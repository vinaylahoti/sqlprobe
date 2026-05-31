from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlprobe.annotations.prompt_builder import build_annotation_context
from sqlprobe.core.result import (
    AssertionFailure,
    DimensionResult,
    ExecutionResult,
    JudgeResult,
    compute_overall_score,
    compute_overall_verdict,
)
from sqlprobe.core.taxonomy import FailureMode
from sqlprobe.loader.annotation_loader import SchemaAnnotation


JUDGE_MODEL = "claude-sonnet-4-20250514"

SYSTEM_PROMPT = """You are an expert SQL evaluator. Your role is to assess whether a generated SQL query correctly answers a business question. You evaluate specific dimensions and return a structured JSON verdict.

Return ONLY valid JSON. No preamble, no markdown, no explanation outside the JSON."""

VALID_FAILURE_MODES = {fm.name for fm in FailureMode}


@dataclass
class JudgeInput:
    question: str
    generated_sql: str
    expected_sql: str | None = None
    execution_result: ExecutionResult | None = None
    assertion_failures: list[AssertionFailure] = field(default_factory=list)
    schema_annotations: list[SchemaAnnotation] = field(default_factory=list)
    dimensions: list[str] = field(
        default_factory=lambda: [
            "metric_definition",
            "date_boundary",
            "segment_filter",
            "aggregation",
            "grain",
        ]
    )


class SQLProbeJudge:
    def __init__(self, model: str = JUDGE_MODEL, api_key: str | None = None):
        import os

        self._model = model
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self._api_key:
            raise ValueError(
                "Anthropic API key is required. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key= to SQLProbeJudge."
            )

    def evaluate(self, judge_input: JudgeInput) -> JudgeResult:
        """Run the LLM judge. Returns JudgeResult with skipped=True on any error."""
        try:
            prompt = self._build_prompt(judge_input)
            raw = self._call_api(prompt)
            data = self._parse_response(raw)
            return self._build_result(data, judge_input.dimensions)
        except Exception:
            return JudgeResult(
                overall_verdict="SKIP",
                overall_score=1.0,
                confidence="low",
                dimensions=[],
                model=self._model,
                skipped=True,
            )

    def _build_prompt(self, ji: JudgeInput) -> str:
        parts = []
        parts.append(f"Question: {ji.question}")
        parts.append(f"\nGenerated SQL:\n{ji.generated_sql}")

        if ji.expected_sql:
            parts.append(f"\nReference SQL (correct answer):\n{ji.expected_sql}")

        if ji.schema_annotations:
            ctx = build_annotation_context(ji.schema_annotations)
            parts.append(f"\n{ctx}")

        if ji.assertion_failures:
            parts.append("\nKnown assertion failures already detected:")
            for failure in ji.assertion_failures:
                parts.append(f"  - {failure.assertion_id}: {failure.detail}")

        if ji.execution_result:
            result = ji.execution_result
            parts.append("\nExecution result:")
            parts.append(f"  - Rows returned: {result.row_count}")
            parts.append(f"  - Success: {result.success}")
            if result.error:
                parts.append(f"  - Error: {result.error}")

        dims_str = ", ".join(ji.dimensions)
        parts.append(f"\nEvaluate these dimensions: {dims_str}")

        semantic_business_modes = [
            "WRONG_GRAIN",
            "WRONG_DATE_BOUNDARY",
            "MISSING_FILTER",
            "SPURIOUS_FILTER",
            "WRONG_AGGREGATION",
            "COLUMN_SUBSTITUTION",
            "DECOMPOSITION_FAILURE",
            "METRIC_DEFINITION_VIOLATION",
            "MISSING_BUSINESS_FILTER",
            "CALENDAR_VIOLATION",
            "SCOPE_VIOLATION",
            "STALE_LOGIC",
        ]
        parts.append(
            "\nFailure mode taxonomy (use these codes or null):\n"
            f"{', '.join(semantic_business_modes)}"
        )

        parts.append(
            """
Return ONLY this JSON structure:
{
  "overall_verdict": "PASS" | "FAIL" | "WARN",
  "overall_score": <float 0.0-1.0>,
  "confidence": "high" | "medium" | "low",
  "dimensions": [
    {
      "dimension": "<name>",
      "verdict": "PASS" | "FAIL" | "WARN" | "SKIP",
      "failure_mode": "<taxonomy code>" | null,
      "evidence": "<1-3 sentence reasoning>",
      "confidence": "high" | "medium" | "low"
    }
  ]
}"""
        )
        return "\n".join(parts)

    def _call_api(self, prompt: str) -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=self._api_key)
        response = client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    def _parse_response(self, raw: str) -> dict:
        """Parse JSON from model response. Strip markdown fences if present."""
        import json

        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]).strip()
        return json.loads(text)

    def _build_result(self, data: dict, requested_dimensions: list[str]) -> JudgeResult:
        """Build JudgeResult from parsed API response. Recompute score and verdict locally."""
        dimensions = []
        for dim_data in data.get("dimensions", []):
            fm_str = dim_data.get("failure_mode")
            failure_mode = None
            if fm_str and fm_str in VALID_FAILURE_MODES:
                failure_mode = FailureMode[fm_str]

            dimensions.append(
                DimensionResult(
                    dimension=dim_data.get("dimension", ""),
                    verdict=dim_data.get("verdict", "SKIP"),
                    failure_mode=failure_mode,
                    evidence=dim_data.get("evidence", ""),
                    confidence=dim_data.get("confidence", "low"),
                )
            )

        score = compute_overall_score(dimensions)
        verdict = compute_overall_verdict(dimensions)

        return JudgeResult(
            overall_verdict=verdict,
            overall_score=score,
            confidence=data.get("confidence", "low"),
            dimensions=dimensions,
            model=self._model,
            skipped=False,
        )


def evaluate_with_judge(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Compatibility wrapper retained until the CLI is wired to SQLProbeJudge."""
    return {
        "skipped": True,
        "reason": "LLM judge not implemented in v0.0.1",
    }
