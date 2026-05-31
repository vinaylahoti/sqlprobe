"""LLM judge evaluator stub.

Anthropic and OpenAI judge support is planned for a later release. LLM judging
is not part of v0.0.1, so this module exposes a stable placeholder API only.
"""

from __future__ import annotations

from typing import Any


def evaluate_with_judge(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return {
        "skipped": True,
        "reason": "LLM judge not implemented in v0.0.1",
    }
