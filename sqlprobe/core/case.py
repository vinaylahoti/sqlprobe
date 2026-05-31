from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ExpectedResultShape:
    row_count: Optional[int] = None
    columns: Optional[list[str]] = None
    value_range: Optional[dict[str, dict]] = None


@dataclass
class ExpectedOutput:
    sql: Optional[str] = None
    result_shape: Optional[ExpectedResultShape] = None
    intent_components: Optional[dict] = None


@dataclass
class InputContext:
    fiscal_year_start: Optional[str] = None
    user_role: Optional[str] = None
    extras: dict = field(default_factory=dict)


@dataclass
class EvaluationCase:
    id: str
    version: str
    question: str
    expected: ExpectedOutput

    context: Optional[InputContext] = None
    assertions: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    created_at: Optional[str] = None
    created_by: Optional[str] = None
    status: str = "active"
    schema_snapshot_id: Optional[str] = None
    description: Optional[str] = None
