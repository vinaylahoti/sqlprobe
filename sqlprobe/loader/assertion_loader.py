from __future__ import annotations
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from ..core.taxonomy import FailureMode, Severity


@dataclass
class AssertionTrigger:
    sql_references_any: list[str] = field(default_factory=list)
    question_contains_any: list[str] = field(default_factory=list)
    question_not_contains: list[str] = field(default_factory=list)


@dataclass
class AssertionCheck:
    sql_contains_filter: Optional[dict] = None
    sql_excludes_column: Optional[str] = None
    requires_column: Optional[str] = None
    aggregation_type: Optional[str] = None
    no_select_star: Optional[bool] = None


@dataclass
class Assertion:
    id: str
    description: str
    trigger: AssertionTrigger
    assert_: AssertionCheck
    severity: Severity
    failure_mode: FailureMode
    on_failure: str = "fail"


def load_assertions_from_dir(directory: Path) -> dict[str, Assertion]:
    assertions: dict[str, Assertion] = {}
    for path in sorted(directory.rglob("*.yaml")):
        loaded = _load_assertion_file(path)
        assertions.update(loaded)
    return assertions


def _load_assertion_file(path: Path) -> dict[str, Assertion]:
    with open(path, encoding="utf-8") as f:
        items = yaml.safe_load(f)
    if items is None:
        return {}
    if isinstance(items, dict):
        items = [items]
    result = {}
    for item in items:
        a = _parse_assertion(item)
        result[a.id] = a
    return result


def _parse_assertion(data: dict) -> Assertion:
    trigger_data = data.get("trigger", {})
    trigger = AssertionTrigger(
        sql_references_any=trigger_data.get("sql_references_any", []),
        question_contains_any=trigger_data.get("question_contains_any", []),
        question_not_contains=trigger_data.get("question_not_contains", []),
    )
    assert_data = data.get("assert", {})
    check = AssertionCheck(
        sql_contains_filter=assert_data.get("sql_contains_filter"),
        sql_excludes_column=assert_data.get("sql_excludes_column"),
        requires_column=assert_data.get("requires_column"),
        aggregation_type=assert_data.get("aggregation_type"),
        no_select_star=assert_data.get("no_select_star"),
    )
    return Assertion(
        id=data["id"],
        description=data["description"],
        trigger=trigger,
        assert_=check,
        severity=Severity(data.get("severity", "warning")),
        failure_mode=FailureMode(data["failure_mode"]),
        on_failure=data.get("on_failure", "fail"),
    )
