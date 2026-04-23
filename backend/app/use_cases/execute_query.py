import time
from datetime import datetime, timezone
from typing import Any

from domain.entities.query_spec import QuerySpec
from domain.errors import CatalogMiss, CompilationError, PolicyViolation, SourceConnectionError
from domain.interfaces.audit_log import IAuditLog
from domain.interfaces.connection_repository import IConnectionRepository
from domain.interfaces.query_executor import IQueryExecutor
from domain.value_objects.audit_event import AuditEvent
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
        audit_log: IAuditLog,
    ) -> None:
        self._compile = compile_use_case
        self._connection_repo = connection_repo
        self._executor = executor
        self._audit_log = audit_log

    def execute(self, spec: QuerySpec, dialect: Dialect, caller_id: str) -> list[dict[str, Any]]:
        """Compile and execute ``spec``, returning result rows.

        Args:
            spec: The dataset definition to compile and execute.
            dialect: Target SQL dialect.
            caller_id: Opaque caller identity for audit records.

        Returns:
            Result rows as plain dicts, at most ``_MAX_RESULT_ROWS`` entries.

        Raises:
            PolicyViolation: From the compile step or if the row cap is exceeded.
            CompilationError: If the spec cannot be compiled.
            CatalogMiss: If a referenced table/column or connection is unknown.
            SourceConnectionError: If the source database is unreachable.
        """
        start = time.monotonic()
        table_names = frozenset({spec.source.table} | {j.table for j in spec.joins})
        outcome: str = "source_error"  # safe sentinel; overwritten in every named branch
        row_count: int | None = None

        try:
            compiled = self._compile.execute(spec, dialect)
            url = self._connection_repo.get_url(spec.connection_id)
            rows = self._executor.execute(compiled, url)
            if len(rows) > _MAX_RESULT_ROWS:
                outcome = "row_cap_exceeded"
                raise PolicyViolation(
                    f"Result exceeds the {_MAX_RESULT_ROWS}-row cap; got {len(rows)} rows"
                )
            row_count = len(rows)
            outcome = "success"
            return rows
        except PolicyViolation:
            if outcome != "row_cap_exceeded":
                outcome = "policy_violation"
            raise
        except CompilationError:
            outcome = "compilation_error"
            raise
        except CatalogMiss:
            outcome = "catalog_miss"
            raise
        except SourceConnectionError:
            outcome = "source_error"
            raise
        finally:
            duration_ms = int((time.monotonic() - start) * 1000)
            event = AuditEvent(
                caller_id=caller_id,
                connection_id=spec.connection_id,
                table_names=table_names,
                dialect=dialect.value,
                outcome=outcome,
                row_count=row_count,
                duration_ms=duration_ms,
                timestamp=datetime.now(tz=timezone.utc),
            )
            try:
                self._audit_log.append(event)
            except Exception:
                pass
