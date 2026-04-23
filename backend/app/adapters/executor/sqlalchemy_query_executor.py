from typing import Any

import sqlalchemy as sa
from sqlalchemy.exc import SQLAlchemyError

from domain.errors import SourceConnectionError
from domain.interfaces.query_compiler import CompiledQuery
from domain.interfaces.query_executor import IQueryExecutor


class SqlAlchemyQueryExecutor(IQueryExecutor):
    """Executes compiled SQL against a source DB using SQLAlchemy Core."""

    def execute(self, query: CompiledQuery, connection_url: str) -> list[dict[str, Any]]:
        engine = sa.create_engine(connection_url)
        try:
            with engine.connect() as conn:
                result = conn.execute(sa.text(query.sql), query.params)
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as exc:
            raise SourceConnectionError(str(exc)) from exc
        finally:
            engine.dispose()
