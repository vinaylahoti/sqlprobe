from pathlib import Path

import sqlprobe.adapters.duckdb as duckdb_adapter
from sqlprobe.adapters.duckdb import DuckDBAdapter
from sqlprobe.core.taxonomy import FailureMode


def test_connect_memory():
    adapter = DuckDBAdapter("duckdb://:memory:")
    adapter.close()


def test_execute_simple():
    with DuckDBAdapter("duckdb://:memory:") as adapter:
        result = adapter.execute("SELECT 42 AS val")

    assert result.success is True
    assert result.rows == [{"val": 42}]
    assert result.row_count == 1
    assert result.error is None


def test_execute_returns_columns():
    with DuckDBAdapter("duckdb://:memory:") as adapter:
        result = adapter.execute("SELECT 1 AS one, 2 AS two")

    assert result.columns == ["one", "two"]


def test_execute_duration():
    with DuckDBAdapter("duckdb://:memory:") as adapter:
        result = adapter.execute("SELECT 1")

    assert isinstance(result.duration_ms, float)
    assert result.duration_ms > 0


def test_execute_sql_error():
    with DuckDBAdapter("duckdb://:memory:") as adapter:
        result = adapter.execute("SELECT FROM")

    assert result.success is False
    assert isinstance(result.error, str)
    assert result.error
    assert result.rows is None


def test_execute_multiple_rows():
    with DuckDBAdapter("duckdb://:memory:") as adapter:
        result = adapter.execute(
            "SELECT * FROM (VALUES (1), (2), (3)) AS rows(val)"
        )

    assert result.success is True
    assert result.row_count == 3


def test_cardinality_flag(monkeypatch):
    monkeypatch.setattr(duckdb_adapter, "CARDINALITY_THRESHOLD", 2)

    with DuckDBAdapter("duckdb://:memory:") as adapter:
        result = adapter.execute(
            "SELECT * FROM (VALUES (1), (2), (3)) AS rows(val)"
        )

    assert result.failure_mode == FailureMode.CARDINALITY_EXPLOSION


def test_context_manager():
    with DuckDBAdapter("duckdb://:memory:") as adapter:
        result = adapter.execute("SELECT 1 AS val")

    assert result.success is True


def test_file_db():
    db_path = Path("fixtures") / "warehouse.db"

    with DuckDBAdapter(f"duckdb://./{db_path.as_posix()}") as adapter:
        result = adapter.execute("SELECT COUNT(*) AS n FROM accounts")

    assert result.success is True
    assert result.row_count == 1
    assert result.rows[0]["n"] >= 5
