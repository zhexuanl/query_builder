from collections.abc import Mapping

from domain.interfaces.catalog_repository import CatalogView, ICatalogRepository
from domain.interfaces.schema_reflector import ISchemaReflector


class InMemoryCatalogRepository(ICatalogRepository):
    """Process-lifetime catalog cache backed by an ``ISchemaReflector``.

    Caches ``CatalogView`` instances keyed by ``(connection_id, table_names)``
    so that repeated compilations for the same connection and table set avoid
    redundant network round-trips to the source database.

    Attributes:
        _reflector: The reflector used on cache misses.
        _cache: Mapping of ``(connection_id, frozenset[table_names])``
            to the cached ``CatalogView``.
    """

    def __init__(self, reflector: ISchemaReflector, url_for: Mapping[str, str]) -> None:
        """Initialise the repository.

        Args:
            reflector: Concrete ``ISchemaReflector`` used when a cache miss
                occurs.
            url_for: Read-only mapping of ``connection_id`` → connection URL.
                In v1 this is a static dict; M5 will replace it with an
                ``IConnectionRepository`` lookup.
        """
        self._reflector = reflector
        self._url_for = url_for
        self._cache: dict[tuple[str, frozenset[str]], CatalogView] = {}

    def view_for(self, connection_id: str, table_names: frozenset[str]) -> CatalogView:
        """Return a ``CatalogView`` for the given connection and table set.

        Serves from the cache when possible.  Delegates to the injected
        ``ISchemaReflector`` on a cache miss and stores the result.

        Args:
            connection_id: Source DB connection identifier.
            table_names: Table names to include in the view.

        Returns:
            A ``CatalogView`` populated with metadata for ``table_names``.

        Raises:
            KeyError: If ``connection_id`` has no URL in ``url_for``.
            SourceConnectionError: Propagated from the reflector on failure.
        """
        key = (connection_id, table_names)
        if key not in self._cache:
            url = self._url_for[connection_id]
            self._cache[key] = self._reflector.reflect(url, table_names)
        return self._cache[key]

    def invalidate(self, connection_id: str) -> None:
        """Evict all cached views for the given connection.

        The next ``view_for`` call after invalidation will re-reflect from the
        source database.

        Args:
            connection_id: Connection whose cache entries should be removed.
        """
        keys_to_remove = [k for k in self._cache if k[0] == connection_id]
        for key in keys_to_remove:
            del self._cache[key]
