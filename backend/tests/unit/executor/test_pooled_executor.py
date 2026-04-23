"""Unit tests for PooledSqlAlchemyQueryExecutor."""
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import OperationalError

from adapters.executor.pooled_sqlalchemy_query_executor import PooledSqlAlchemyQueryExecutor
from domain.errors import SourceConnectionError
from domain.interfaces.query_compiler import CompiledQuery
from domain.value_objects.dialect import Dialect


@pytest.fixture()
def compiled_query() -> CompiledQuery:
    return CompiledQuery(sql="SELECT 1", params={}, dialect=Dialect.postgres)


@pytest.fixture()
def mock_engine():
    engine = MagicMock()
    row = MagicMock()
    row._mapping = {"id": 1}
    conn = MagicMock()
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__ = MagicMock(return_value=False)
    conn.execute.return_value = [row]
    engine.connect.return_value = conn
    return engine


def test_execute_uses_injected_engine(mock_engine, compiled_query):
    executor = PooledSqlAlchemyQueryExecutor(mock_engine)
    result = executor.execute(compiled_query, connection_url="unused://")
    mock_engine.connect.assert_called_once()
    assert result == [{"id": 1}]


def test_db_error_raises_source_connection_error(compiled_query):
    engine = MagicMock()
    conn = MagicMock()
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__ = MagicMock(return_value=False)
    conn.execute.side_effect = OperationalError("connection refused", None, None)
    engine.connect.return_value = conn

    executor = PooledSqlAlchemyQueryExecutor(engine)
    with pytest.raises(SourceConnectionError):
        executor.execute(compiled_query, connection_url="unused://")


def test_dispose_never_called(mock_engine, compiled_query):
    executor = PooledSqlAlchemyQueryExecutor(mock_engine)
    executor.execute(compiled_query, connection_url="unused://")
    mock_engine.dispose.assert_not_called()
