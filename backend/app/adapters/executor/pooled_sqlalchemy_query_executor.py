from typing import Any

import sqlalchemy as sa
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from domain.errors import SourceConnectionError
from domain.interfaces.query_compiler import CompiledQuery
from domain.interfaces.query_executor import IQueryExecutor


class PooledSqlAlchemyQueryExecutor(IQueryExecutor):
    """Executes compiled SQL using a caller-managed SQLAlchemy engine.

    The caller owns the engine lifecycle — this class never calls ``dispose()``.
    Use this when the application already maintains a connection pool.
    """

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def execute(self, query: CompiledQuery, connection_url: str) -> list[dict[str, Any]]:
        try:
            with self._engine.connect() as conn:
                result = conn.execute(sa.text(query.sql), query.params)
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as exc:
            raise SourceConnectionError(str(exc)) from exc
