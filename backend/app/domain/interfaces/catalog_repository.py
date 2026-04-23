from abc import ABC, abstractmethod
from typing import Any


class CatalogView(ABC):
    """Read-only view of catalog metadata for a single compilation pass.

    Implementations resolve table aliases and column names to SQLAlchemy
    expression objects.  The domain declares the interface using ``Any``
    return types so that ``domain/`` remains free of SQLAlchemy imports.
    """

    @abstractmethod
    def sa_table(self, alias: str) -> Any:
        """Return the SQLAlchemy aliased-table object for the given table alias.

        Args:
            alias: The table alias as declared in ``JoinDef.alias``.

        Returns:
            A SQLAlchemy ``Alias`` or ``Table`` object usable in expressions.

        Raises:
            CatalogMiss: If no table is registered for ``alias``.
        """

    @abstractmethod
    def column(self, alias: str, name: str) -> Any:
        """Return the SQLAlchemy column expression for the given alias and name.

        Args:
            alias: Table alias.
            name: Column name.

        Returns:
            A SQLAlchemy column expression.

        Raises:
            CatalogMiss: If the alias is unknown or ``name`` does not exist on it.
        """


class ICatalogRepository(ABC):
    """Port: supplies a ``CatalogView`` scoped to a compilation pass.

    The use case fetches a view once and passes it to the compiler.
    This keeps catalog I/O out of the compiler.
    """

    @abstractmethod
    def view_for(
        self, connection_id: str, table_names: frozenset[str]
    ) -> CatalogView:
        """Build a catalog view covering the requested tables.

        Args:
            connection_id: Source DB connection identifier.
            table_names: Qualified table names to include in the view.

        Returns:
            A ``CatalogView`` populated with metadata for the requested tables.
        """

    @abstractmethod
    def invalidate(self, connection_id: str) -> None:
        """Evict all cached views for the given connection.

        The next ``view_for`` call after invalidation will re-fetch from the
        source database.

        Args:
            connection_id: Connection whose cache entries should be removed.
        """
