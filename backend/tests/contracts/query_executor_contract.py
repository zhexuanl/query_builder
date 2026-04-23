"""Contract test base class for IQueryExecutor implementations.

To test a custom IQueryExecutor, subclass ``QueryExecutorContract`` and
override the ``executor`` and ``connection_url`` fixtures.
"""
import pytest

from domain.errors import SourceConnectionError
from domain.interfaces.query_compiler import CompiledQuery
from domain.interfaces.query_executor import IQueryExecutor
from domain.value_objects.dialect import Dialect


class QueryExecutorContract:
    """Abstract contract test suite for IQueryExecutor.

    Subclasses must override the ``executor`` and ``connection_url`` fixtures.
    The ``connection_url`` must point to a live database suitable for running
    ``SELECT 1`` without side effects.
    """

    @pytest.fixture
    def executor(self) -> IQueryExecutor:
        raise NotImplementedError("Subclass must provide an IQueryExecutor instance")

    @pytest.fixture
    def connection_url(self) -> str:
        raise NotImplementedError("Subclass must provide a valid connection URL")

    def test_returns_list_of_dicts(self, executor, connection_url):
        query = CompiledQuery(sql="SELECT 1 AS n", params={}, dialect=Dialect.postgres)
        result = executor.execute(query, connection_url)
        assert isinstance(result, list)
        assert all(isinstance(row, dict) for row in result)

    def test_bad_url_raises_source_connection_error(self, executor):
        query = CompiledQuery(sql="SELECT 1", params={}, dialect=Dialect.postgres)
        with pytest.raises(SourceConnectionError):
            executor.execute(query, "not-a-real-dialect://user:pw@localhost/db")
