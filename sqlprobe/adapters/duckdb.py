from __future__ import annotations

import time

try:
    import duckdb
except ImportError:
    raise ImportError(
        "DuckDB is required for execution evaluation. "
        "Install with: pip install sqlprobe[duckdb]"
    )

from sqlprobe.core.result import ExecutionResult
from sqlprobe.core.taxonomy import FailureMode


CARDINALITY_THRESHOLD = 1_000_000
DUCKDB_URL_PREFIX = "duckdb://"


class DuckDBAdapter:
    def __init__(self, db_url: str):
        if not db_url.startswith(DUCKDB_URL_PREFIX):
            raise ValueError("DuckDB URL must start with duckdb://")

        self.db_path = db_url.removeprefix(DUCKDB_URL_PREFIX)
        self.connection = duckdb.connect(self.db_path)

    def execute(self, sql: str, timeout_seconds: int = 10) -> ExecutionResult:
        start = time.perf_counter()

        try:
            result = self.connection.execute(sql)
            columns = [col[0] for col in (result.description or [])]
            raw_rows = result.fetchall()
            rows = [dict(zip(columns, row)) for row in raw_rows]
            row_count = len(rows)
            duration_ms = (time.perf_counter() - start) * 1000
            failure_mode = (
                FailureMode.CARDINALITY_EXPLOSION
                if row_count > CARDINALITY_THRESHOLD
                else None
            )

            return ExecutionResult(
                success=True,
                rows=rows,
                row_count=row_count,
                columns=columns,
                error=None,
                duration_ms=duration_ms,
                failure_mode=failure_mode,
            )
        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            return ExecutionResult(
                success=False,
                rows=None,
                row_count=None,
                columns=None,
                error=str(exc),
                duration_ms=duration_ms,
                failure_mode=None,
            )

    def close(self):
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # dry_run: deferred to Phase 3
