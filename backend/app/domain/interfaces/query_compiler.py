from abc import ABC, abstractmethod
from typing import Any, NamedTuple

from ..entities.query_spec import QuerySpec
from ..value_objects.dialect import Dialect


class CompiledQuery(NamedTuple):
    """Immutable result of a single compilation pass.

    Attributes:
        sql: Dialect-specific SQL template string with named placeholders.
        params: Bound parameter values keyed by placeholder name.  Runtime
            parameters (``ParamRef``) are absent — they must be supplied by
            the caller at execution time.
        dialect: The dialect used to produce ``sql``.
    """

    sql: str
    params: dict[str, object]
    dialect: Dialect


class IQueryCompiler(ABC):
    """Port: translates a ``QuerySpec`` into a ``CompiledQuery``.

    Compilation is synchronous and side-effect-free.  The compiler receives
    a pre-fetched ``CatalogView`` so that it performs no I/O itself.
    """

    @abstractmethod
    def compile(
        self,
        spec: QuerySpec,
        catalog: Any,
        dialect: Dialect,
    ) -> CompiledQuery:
        """Compile a ``QuerySpec`` to dialect SQL.

        Args:
            spec: The validated dataset definition.
            catalog: A ``CatalogView`` instance supplying table and column
                metadata for all aliases referenced in ``spec``.
            dialect: Target SQL dialect.

        Returns:
            A ``CompiledQuery`` containing the SQL template and bound params.

        Raises:
            CompilationError: If a referenced table or column is absent from
                ``catalog``, or if the spec cannot be compiled for any reason.
        """
