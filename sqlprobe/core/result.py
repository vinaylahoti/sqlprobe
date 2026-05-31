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
