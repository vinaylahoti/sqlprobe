from __future__ import annotations
import yaml
from pathlib import Path
from ..core.case import (
    EvaluationCase, ExpectedOutput, ExpectedResultShape, InputContext
)


def load_case(path: Path) -> EvaluationCase:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return _parse_case(data, source=str(path))


def load_cases_from_dir(directory: Path) -> list[EvaluationCase]:
    cases = []
    for path in sorted(directory.rglob("*.yaml")):
        if "assertions" not in str(path):
            cases.append(load_case(path))
    return cases


def _parse_case(data: dict, source: str) -> EvaluationCase:
    _require_fields(data, ["id", "version", "input", "expected"], source)
    inp = data["input"]
    exp = data["expected"]

    result_shape = None
    if "result_shape" in exp:
        rs = exp["result_shape"]
        result_shape = ExpectedResultShape(
            row_count=rs.get("row_count"),
            columns=rs.get("columns"),
            value_range=rs.get("value_range"),
        )

    context = None
    if "context" in inp:
        ctx = inp["context"]
        context = InputContext(
            fiscal_year_start=ctx.get("fiscal_year_start"),
            user_role=ctx.get("user_role"),
            extras={
                k: v for k, v in ctx.items()
                if k not in ("fiscal_year_start", "user_role")
            },
        )

    return EvaluationCase(
        id=data["id"],
        version=data["version"],
        question=inp["question"],
        context=context,
        expected=ExpectedOutput(
            sql=exp.get("sql"),
            result_shape=result_shape,
            intent_components=exp.get("intent_components"),
        ),
        assertions=data.get("assertions", []),
        tags=data.get("tags", []),
        created_at=data.get("created_at"),
        created_by=data.get("created_by"),
        status=data.get("status", "active"),
        schema_snapshot_id=data.get("schema_snapshot_id"),
        description=data.get("description"),
    )


def _require_fields(data: dict, fields: list[str], source: str) -> None:
    for f in fields:
        if f not in data:
            raise ValueError(
                f"Evaluation case missing required field '{f}' in {source}"
            )
