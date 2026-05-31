"""DuckDB adapter stub.

DuckDB fixture execution is planned for a future release and is outside the
v0.0.1 scope. This class preserves the expected adapter interface for future
CLI and evaluator work.
"""

from __future__ import annotations

from typing import Any


class DuckDBAdapter:
    """Placeholder DuckDB adapter interface."""

    def connect(self, *args: Any, **kwargs: Any) -> None:
        """Connect to DuckDB in a future release."""
        raise NotImplementedError(
            "DuckDB adapter is planned for a future release."
        )

    def execute(self, *args: Any, **kwargs: Any) -> None:
        """Execute SQL against DuckDB in a future release."""
        raise NotImplementedError(
            "DuckDB adapter is planned for a future release."
        )
