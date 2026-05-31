from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from .taxonomy import FailureMode, Layer, Severity


@dataclass
class AssertionFailure:
    assertion_id: str
    detail: str
    failure_mode: Optional[FailureMode]
    severity: Severity


@dataclass
class LayerResult:
    layer: Layer
    passed: bool
    skipped: bool = False
    skip_reason: Optional[str] = None
    failures: list[AssertionFailure] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class EvaluationResult:
    case_id: str
    generated_sql: str
    passed: bool

    syntax: Optional[LayerResult] = None
    execution: Optional[LayerResult] = None
    semantic: Optional[LayerResult] = None
    business: Optional[LayerResult] = None

    failure_modes: list[FailureMode] = field(default_factory=list)
    overall_severity: Optional[Severity] = None

    def summary_line(self) -> str:
        status = "✓ PASS" if self.passed else "✗ FAIL"
        modes = ", ".join(f.value for f in self.failure_modes)
        return f"{status}  {self.case_id}" + (f"  [{modes}]" if modes else "")


@dataclass
class ExecutionResult:
    success: bool
    rows: list[dict] | None
    row_count: int | None
    columns: list[str] | None
    error: str | None
    duration_ms: float
    failure_mode: FailureMode | None


@dataclass
class DimensionResult:
    dimension: str
    verdict: str
    failure_mode: FailureMode | None
    evidence: str
    confidence: str


@dataclass
class JudgeResult:
    overall_verdict: str
    overall_score: float
    confidence: str
    dimensions: list[DimensionResult]
    model: str
    skipped: bool = False


def compute_overall_score(dimensions: list[DimensionResult]) -> float:
    """Fraction of non-SKIP dimensions that returned PASS."""
    countable = [d for d in dimensions if d.verdict != "SKIP"]
    if not countable:
        return 1.0
    passed = [d for d in countable if d.verdict == "PASS"]
    return round(len(passed) / len(countable), 4)


def compute_overall_verdict(dimensions: list[DimensionResult]) -> str:
    """FAIL if any FAIL, WARN if any WARN and no FAIL, else PASS."""
    verdicts = {d.verdict for d in dimensions}
    if "FAIL" in verdicts:
        return "FAIL"
    if "WARN" in verdicts:
        return "WARN"
    return "PASS"
