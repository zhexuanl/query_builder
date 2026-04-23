from typing import Any

from domain.interfaces.query_compiler import CompiledQuery
from domain.interfaces.query_executor import IQueryExecutor


class FakeQueryExecutor(IQueryExecutor):
    """Test double that returns preset rows without touching a database."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows
        self.calls: list[tuple[CompiledQuery, str]] = []

    def execute(self, query: CompiledQuery, connection_url: str) -> list[dict[str, Any]]:
        self.calls.append((query, connection_url))
        return list(self._rows)
