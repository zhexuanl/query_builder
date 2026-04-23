from abc import ABC, abstractmethod

from domain.interfaces.catalog_repository import CatalogView


class ISchemaReflector(ABC):
    """Port: reflects table and column schema from a live source database.

    Implementations connect to a source DB, enumerate the requested tables,
    and return a ``CatalogView`` backed by the reflected metadata.  The domain
    declares the interface in terms of plain Python types (URL string,
    frozenset) to remain free of framework imports.
    """

    @abstractmethod
    def reflect(self, url: str, table_names: frozenset[str]) -> CatalogView:
        """Reflect schema for the requested tables and return a catalog view.

        Args:
            url: Database connection URL for the source database.
            table_names: Names of the tables to reflect.  Only these tables
                are included in the returned ``CatalogView``.

        Returns:
            A ``CatalogView`` populated with SQLAlchemy expression objects for
            all requested tables and their columns.

        Raises:
            SourceConnectionError: If the database is unreachable, credentials
                are invalid, or a requested table does not exist in the source.
        """
