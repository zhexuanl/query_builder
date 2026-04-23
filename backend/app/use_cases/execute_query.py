from typing import Any

from domain.entities.query_spec import QuerySpec
from domain.errors import PolicyViolation
from domain.interfaces.connection_repository import IConnectionRepository
from domain.interfaces.query_executor import IQueryExecutor
from domain.value_objects.dialect import Dialect
from use_cases.compile_query import CompileQueryUseCase

_MAX_RESULT_ROWS = 10_000


class ExecuteQueryUseCase:
    """Chains compile → connection-resolve → execute with a row-count cap."""

    def __init__(
        self,
        compile_use_case: CompileQueryUseCase,
        connection_repo: IConnectionRepository,
        executor: IQueryExecutor,
    ) -> None:
        self._compile = compile_use_case
        self._connection_repo = connection_repo
        self._executor = executor

    def execute(self, spec: QuerySpec, dialect: Dialect) -> list[dict[str, Any]]:
        """Compile and execute ``spec``, returning result rows.

        Args:
            spec: The dataset definition to compile and execute.
            dialect: Target SQL dialect.

        Returns:
            Result rows as plain dicts, at most ``_MAX_RESULT_ROWS`` entries.

        Raises:
            PolicyViolation: From the compile step or if the row cap is exceeded.
            CompilationError: If the spec cannot be compiled.
            CatalogMiss: If a referenced table/column or connection is unknown.
            SourceConnectionError: If the source database is unreachable.
        """
        compiled = self._compile.execute(spec, dialect)
        url = self._connection_repo.get_url(spec.connection_id)
        rows = self._executor.execute(compiled, url)
        if len(rows) > _MAX_RESULT_ROWS:
            raise PolicyViolation(
                f"Result exceeds the {_MAX_RESULT_ROWS}-row cap; got {len(rows)} rows"
            )
        return rows
