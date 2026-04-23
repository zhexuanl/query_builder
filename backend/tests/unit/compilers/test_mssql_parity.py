"""MSSQL dialect parity tests for SqlAlchemyCoreCompiler."""
import re

import sqlalchemy as sa
import pytest
from sqlalchemy.sql.elements import quoted_name

from adapters.catalog.sqlalchemy_catalog_view import SqlAlchemyCatalogView
from adapters.compilers.sqlalchemy_core_compiler import SqlAlchemyCoreCompiler
from domain.entities.query_spec import QuerySpec
from domain.value_objects.dialect import Dialect
from domain.value_objects.filters import Predicate
from domain.value_objects.query_parts import JoinDef, SelectField
from domain.value_objects.refs import ColumnRef, ValueRef
from tests.fakes.in_memory_catalog import make_catalog


def _norm(sql: str) -> str:
    return re.sub(r"\s+", " ", sql).strip()


@pytest.fixture(scope="module")
def compiler() -> SqlAlchemyCoreCompiler:
    return SqlAlchemyCoreCompiler()


@pytest.fixture()
def catalog():
    return make_catalog(("o", "orders", ["id", "amount", "customer_id"]))


@pytest.fixture()
def quoted_catalog():
    """Catalog with a column whose name is explicitly quoted (forces dialect quoting)."""
    meta = sa.MetaData()
    t = sa.Table(
        "orders",
        meta,
        sa.Column(quoted_name("Amount", True), sa.Numeric),
        sa.Column("id", sa.Integer),
    )
    return SqlAlchemyCatalogView({"o": t.alias("o")})


def _base_spec(catalog_alias: str = "o", col: str = "id", limit: int | None = 50) -> QuerySpec:
    return QuerySpec(
        connection_id="conn-1",
        source=JoinDef(type="inner", table="orders", alias=catalog_alias, on=()),
        select=(SelectField(kind="column", source=ColumnRef(catalog_alias, col), label=col),),
        limit=limit,
    )


def test_limit_uses_top_not_limit(compiler, catalog):
    result = compiler.compile(_base_spec(limit=50), catalog, Dialect.mssql)
    sql = _norm(result.sql)
    assert "TOP" in sql
    assert "LIMIT" not in sql


def test_bracket_quoting_not_double_quote(compiler, quoted_catalog):
    spec = QuerySpec(
        connection_id="conn-1",
        source=JoinDef(type="inner", table="orders", alias="o", on=()),
        select=(SelectField(kind="column", source=ColumnRef("o", "Amount"), label="amt"),),
        limit=None,
    )
    result = compiler.compile(spec, quoted_catalog, Dialect.mssql)
    sql = _norm(result.sql)
    assert "[Amount]" in sql
    assert '"Amount"' not in sql


def test_inner_join_uses_join_not_outer_join(compiler):
    cat = make_catalog(
        ("c", "customers", ["id"]),
        ("o", "orders", ["id", "customer_id"]),
    )
    spec = QuerySpec(
        connection_id="conn-1",
        source=JoinDef(type="inner", table="customers", alias="c", on=()),
        joins=(
            JoinDef(
                type="inner",
                table="orders",
                alias="o",
                on=(Predicate(left=ColumnRef("c", "id"), op="=", right=ColumnRef("o", "customer_id")),),
            ),
        ),
        select=(SelectField(kind="column", source=ColumnRef("c", "id"), label="id"),),
        limit=None,
    )
    result = compiler.compile(spec, cat, Dialect.mssql)
    sql = _norm(result.sql)
    assert "JOIN" in sql
    assert "OUTER JOIN" not in sql


def test_left_join_uses_left_outer_join(compiler):
    cat = make_catalog(
        ("c", "customers", ["id"]),
        ("o", "orders", ["id", "customer_id"]),
    )
    spec = QuerySpec(
        connection_id="conn-1",
        source=JoinDef(type="inner", table="customers", alias="c", on=()),
        joins=(
            JoinDef(
                type="left",
                table="orders",
                alias="o",
                on=(Predicate(left=ColumnRef("c", "id"), op="=", right=ColumnRef("o", "customer_id")),),
            ),
        ),
        select=(SelectField(kind="column", source=ColumnRef("c", "id"), label="id"),),
        limit=None,
    )
    result = compiler.compile(spec, cat, Dialect.mssql)
    sql = _norm(result.sql)
    assert "LEFT OUTER JOIN" in sql
