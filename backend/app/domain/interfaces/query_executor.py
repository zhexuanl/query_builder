from abc import ABC, abstractmethod
from typing import Any

from domain.interfaces.query_compiler import CompiledQuery


class IQueryExecutor(ABC):
    """Port: executes a compiled SQL query against a source database."""

    @abstractmethod
    def execute(self, query: CompiledQuery, connection_url: str) -> list[dict[str, Any]]:
        """Run ``query`` against the database at ``connection_url``.

        Args:
            query: The compiled SQL template and bound params.
            connection_url: SQLAlchemy-compatible connection URL.

        Returns:
            Each result row as a plain ``dict`` keyed by column label.

        Raises:
            SourceConnectionError: If the source DB is unreachable or rejects
                the query.
        """
