from typing import Any

import sqlalchemy as sa

from domain.errors import CatalogMiss
from domain.interfaces.catalog_repository import CatalogView


class InMemoryCatalogView(CatalogView):
    """Test-only catalog view backed by a dict of SQLAlchemy aliased tables.

    Attributes:
        _tables: Mapping of table alias → SQLAlchemy ``Alias`` object.
    """

    def __init__(self, tables: dict[str, Any]) -> None:
        self._tables = tables

    def sa_table(self, alias: str) -> Any:
        """Return the aliased table for the given alias.

        Args:
            alias: Table alias to look up.

        Returns:
            The SQLAlchemy ``Alias`` registered under ``alias``.

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


def make_catalog(
    *table_defs: tuple[str, str, list[str]],
) -> InMemoryCatalogView:
    """Build an ``InMemoryCatalogView`` from simple table definitions.

    Args:
        *table_defs: Each entry is a ``(alias, table_name, column_names)``
            tuple.  A SQLAlchemy ``Table`` is constructed with string-typed
            columns and then aliased.

    Returns:
        An ``InMemoryCatalogView`` ready for use in compiler tests.

    Example:
        >>> catalog = make_catalog(
        ...     ("c", "customers", ["customer_id", "email", "status", "age"]),
        ...     ("t", "transactions", ["id", "customer_id", "amount"]),
        ... )
    """
    meta = sa.MetaData()
    tables: dict[str, sa.sql.expression.Alias] = {}
    for alias, table_name, column_names in table_defs:
        raw = sa.Table(table_name, meta, *[sa.Column(col) for col in column_names])
        tables[alias] = raw.alias(alias)
    return InMemoryCatalogView(tables)
