from typing import Any

import sqlalchemy as sa

from domain.errors import CatalogMiss
from domain.interfaces.catalog_repository import CatalogView


class SqlAlchemyCatalogView(CatalogView):
    """Production ``CatalogView`` backed by SQLAlchemy ``Table`` objects.

    Stores aliased tables keyed by alias name.  Typically produced by
    ``SqlAlchemySchemaReflector``, which aliases each reflected table under its
    own table name so that ``sa_table("customers")`` returns the expression for
    ``customers AS customers``.

    Attributes:
        _tables: Mapping of alias → SQLAlchemy aliased table expression.
    """

    def __init__(self, tables: dict[str, Any]) -> None:
        self._tables = tables

    def sa_table(self, alias: str) -> Any:
        """Return the aliased table expression for the given alias.

        Args:
            alias: Table alias as declared in ``JoinDef.alias``.

        Returns:
            SQLAlchemy aliased table expression.

        Raises:
            CatalogMiss: If no table is registered for ``alias``.
        """
        try:
            return self._tables[alias]
        except KeyError:
            raise CatalogMiss(f"No table found for alias '{alias}'")

    def column(self, alias: str, name: str) -> Any:
        """Return the column expression for the given alias and column name.

        Args:
            alias: Table alias.
            name: Column name.

        Returns:
            SQLAlchemy column expression.

        Raises:
            CatalogMiss: If the alias is unknown or the column does not exist.
        """
        tbl = self.sa_table(alias)
        if name not in tbl.c:
            raise CatalogMiss(f"Column '{alias}.{name}' not found in catalog")
        return tbl.c[name]
