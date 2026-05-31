"""Execution evaluator stub.

Execution evaluation will be implemented in a future release. DuckDB fixture
execution is outside the v0.0.1 scope; this module exists so future CLI imports
remain stable while the execution layer is still planned.
"""

from __future__ import annotations

from ..core.result import LayerResult
from ..core.taxonomy import Layer


def evaluate_execution(
    sql: str,
) -> LayerResult:
    return LayerResult(
        layer=Layer.EXECUTION,
        passed=True,
        skipped=True,
    )
