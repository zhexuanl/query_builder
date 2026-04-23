"""Unit tests for SqlAlchemyCatalogView."""
import sqlalchemy as sa
import pytest

from adapters.catalog.sqlalchemy_catalog_view import SqlAlchemyCatalogView
from domain.errors import CatalogMiss


@pytest.fixture()
def catalog() -> SqlAlchemyCatalogView:
    customers_table = sa.Table(
        "customers",
        sa.MetaData(),
        sa.Column("id", sa.Integer),
        sa.Column("name", sa.String),
    )
    aliased = customers_table.alias("c")
    return SqlAlchemyCatalogView({"c": aliased})


def test_sa_table_returns_aliased_table(catalog):
    tbl = catalog.sa_table("c")
    assert tbl is not None


def test_sa_table_unknown_alias_raises_catalog_miss(catalog):
    with pytest.raises(CatalogMiss):
        catalog.sa_table("unknown")


def test_column_returns_column_expression(catalog):
    col = catalog.column("c", "id")
    assert col is not None


def test_column_missing_col_raises_catalog_miss(catalog):
    with pytest.raises(CatalogMiss):
        catalog.column("c", "missing_col")


def test_column_unknown_alias_raises_catalog_miss(catalog):
    with pytest.raises(CatalogMiss):
        catalog.column("nonexistent", "id")
