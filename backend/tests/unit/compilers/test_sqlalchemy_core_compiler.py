"""Golden tests for SqlAlchemyCoreCompiler — one test per spec fixture, both dialects."""
import pytest

from domain.entities.query_spec import QuerySpec
from domain.errors import CompilationError
from domain.value_objects.dialect import Dialect
from domain.value_objects.filters import FilterGroup, Predicate
from domain.value_objects.query_parts import JoinDef, SelectField
from domain.value_objects.refs import ColumnRef, ParamRef, ValueRef
from adapters.compilers.sqlalchemy_core_compiler import SqlAlchemyCoreCompiler
from tests.fakes.in_memory_catalog import make_catalog
from tests.helpers import normalize_sql


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def compiler() -> SqlAlchemyCoreCompiler:
    return SqlAlchemyCoreCompiler()


@pytest.fixture()
def catalog():
    return make_catalog(
        ("c", "customers", ["customer_id", "email", "status", "age", "country"]),
        ("t", "transactions", ["id", "customer_id", "amount"]),
    )


# ---------------------------------------------------------------------------
# 5.2  Single table, two columns, limit 100
# ---------------------------------------------------------------------------

@pytest.fixture()
def spec_single_table() -> QuerySpec:
    return QuerySpec(
        connection_id="conn1",
        source=JoinDef(type="inner", table="customers", alias="c", on=()),
        select=(
            SelectField(kind="column", source=ColumnRef("c", "customer_id"), label="customer_id"),
            SelectField(kind="column", source=ColumnRef("c", "email"), label="email"),
        ),
        limit=100,
    )


def test_single_table_postgres(compiler, catalog, spec_single_table):
    result = compiler.compile(spec_single_table, catalog, Dialect.postgres)
    sql = normalize_sql(result.sql)
    assert "c.customer_id AS customer_id" in sql
    assert "c.email AS email" in sql
    assert "FROM customers AS c" in sql
    assert "LIMIT" in sql
    assert 100 in result.params.values()


def test_single_table_mssql(compiler, catalog, spec_single_table):
    result = compiler.compile(spec_single_table, catalog, Dialect.mssql)
    sql = normalize_sql(result.sql)
    assert "SELECT TOP 100" in sql
    assert "c.customer_id AS customer_id" in sql
    assert "c.email AS email" in sql
    assert "FROM customers AS c" in sql
    assert "LIMIT" not in sql
    assert result.params == {}


# ---------------------------------------------------------------------------
# 5.3  WHERE AND with two ValueRef predicates
# ---------------------------------------------------------------------------

@pytest.fixture()
def spec_filter_and() -> QuerySpec:
    return QuerySpec(
        connection_id="conn1",
        source=JoinDef(type="inner", table="customers", alias="c", on=()),
        select=(
            SelectField(kind="column", source=ColumnRef("c", "customer_id"), label="customer_id"),
        ),
        where=FilterGroup(
            op="and",
            items=(
                Predicate(left=ColumnRef("c", "status"), op="=", right=ValueRef("active")),
                Predicate(left=ColumnRef("c", "age"), op=">", right=ValueRef(18)),
            ),
        ),
        limit=None,
    )


def test_filter_and_postgres(compiler, catalog, spec_filter_and):
    result = compiler.compile(spec_filter_and, catalog, Dialect.postgres)
    sql = normalize_sql(result.sql)
    assert "WHERE" in sql
    assert "c.status" in sql
    assert "c.age" in sql
    assert "AND" in sql
    assert result.params["status_1"] == "active"
    assert result.params["age_1"] == 18


def test_filter_and_mssql(compiler, catalog, spec_filter_and):
    result = compiler.compile(spec_filter_and, catalog, Dialect.mssql)
    sql = normalize_sql(result.sql)
    assert "WHERE" in sql
    assert "AND" in sql
    assert result.params["status_1"] == "active"
    assert result.params["age_1"] == 18


# ---------------------------------------------------------------------------
# 5.4  LEFT JOIN + COUNT aggregate + GROUP BY
# ---------------------------------------------------------------------------

@pytest.fixture()
def spec_left_join_agg() -> QuerySpec:
    return QuerySpec(
        connection_id="conn1",
        source=JoinDef(type="inner", table="customers", alias="c", on=()),
        select=(
            SelectField(kind="column", source=ColumnRef("c", "country"), label="country"),
            SelectField(kind="agg", func="count", source=ColumnRef("t", "id"), label="tx_count"),
        ),
        joins=(
            JoinDef(
                type="left",
                table="transactions",
                alias="t",
                on=(
                    Predicate(
                        left=ColumnRef("c", "customer_id"),
                        op="=",
                        right=ColumnRef("t", "customer_id"),
                    ),
                ),
            ),
        ),
        group_by=(ColumnRef("c", "country"),),
        limit=None,
    )


def test_left_join_agg_postgres(compiler, catalog, spec_left_join_agg):
    result = compiler.compile(spec_left_join_agg, catalog, Dialect.postgres)
    sql = normalize_sql(result.sql)
    assert "LEFT OUTER JOIN transactions AS t" in sql
    assert "ON c.customer_id = t.customer_id" in sql
    assert "count(t.id) AS tx_count" in sql
    assert "GROUP BY c.country" in sql
    assert result.params == {}


def test_left_join_agg_mssql(compiler, catalog, spec_left_join_agg):
    result = compiler.compile(spec_left_join_agg, catalog, Dialect.mssql)
    sql = normalize_sql(result.sql)
    assert "LEFT OUTER JOIN transactions AS t" in sql
    assert "count(t.id) AS tx_count" in sql
    assert "GROUP BY c.country" in sql
    assert result.params == {}


# ---------------------------------------------------------------------------
# 5.5  ParamRef — unbound named placeholder
# ---------------------------------------------------------------------------

@pytest.fixture()
def spec_param_ref() -> QuerySpec:
    return QuerySpec(
        connection_id="conn1",
        source=JoinDef(type="inner", table="customers", alias="c", on=()),
        select=(
            SelectField(kind="column", source=ColumnRef("c", "customer_id"), label="customer_id"),
        ),
        where=Predicate(left=ColumnRef("c", "status"), op="=", right=ParamRef("status")),
        limit=None,
    )


def test_param_ref_postgres(compiler, catalog, spec_param_ref):
    result = compiler.compile(spec_param_ref, catalog, Dialect.postgres)
    sql = normalize_sql(result.sql)
    assert "%(status)s" in sql
    # Key present with None — placeholder is unbound, caller provides value at execution time
    assert "status" in result.params
    assert result.params["status"] is None


def test_param_ref_mssql(compiler, catalog, spec_param_ref):
    result = compiler.compile(spec_param_ref, catalog, Dialect.mssql)
    sql = normalize_sql(result.sql)
    assert ":status" in sql
    assert "status" in result.params
    assert result.params["status"] is None


# ---------------------------------------------------------------------------
# 5.6  MSSQL TOP vs Postgres LIMIT (no ORDER BY)
# ---------------------------------------------------------------------------

@pytest.fixture()
def spec_limit_no_sort() -> QuerySpec:
    return QuerySpec(
        connection_id="conn1",
        source=JoinDef(type="inner", table="customers", alias="c", on=()),
        select=(
            SelectField(kind="column", source=ColumnRef("c", "customer_id"), label="customer_id"),
        ),
        limit=50,
    )


def test_limit_postgres(compiler, catalog, spec_limit_no_sort):
    result = compiler.compile(spec_limit_no_sort, catalog, Dialect.postgres)
    sql = normalize_sql(result.sql)
    assert "LIMIT" in sql
    assert "TOP" not in sql
    assert 50 in result.params.values()


def test_limit_mssql(compiler, catalog, spec_limit_no_sort):
    result = compiler.compile(spec_limit_no_sort, catalog, Dialect.mssql)
    sql = normalize_sql(result.sql)
    assert "SELECT TOP 50" in sql
    assert "LIMIT" not in sql
    assert result.params == {}


# ---------------------------------------------------------------------------
# 5.7  CompilationError on unknown alias
# ---------------------------------------------------------------------------

def test_compilation_error_unknown_alias(compiler, catalog):
    spec = QuerySpec(
        connection_id="conn1",
        source=JoinDef(type="inner", table="unknown_tbl", alias="x", on=()),
        select=(
            SelectField(kind="column", source=ColumnRef("x", "id"), label="id"),
        ),
        limit=None,
    )
    with pytest.raises(CompilationError):
        compiler.compile(spec, catalog, Dialect.postgres)


# ---------------------------------------------------------------------------
# Additional: count_distinct, is_null, OR filter group (warning W4)
# ---------------------------------------------------------------------------

def test_count_distinct(compiler, catalog):
    spec = QuerySpec(
        connection_id="conn1",
        source=JoinDef(type="inner", table="customers", alias="c", on=()),
        select=(
            SelectField(kind="column", source=ColumnRef("c", "country"), label="country"),
            SelectField(kind="agg", func="count_distinct", source=ColumnRef("c", "customer_id"), label="uniq"),
        ),
        group_by=(ColumnRef("c", "country"),),
        limit=None,
    )
    result = compiler.compile(spec, catalog, Dialect.postgres)
    sql = normalize_sql(result.sql)
    assert "count(DISTINCT c.customer_id) AS uniq" in sql


def test_is_null_predicate(compiler, catalog):
    spec = QuerySpec(
        connection_id="conn1",
        source=JoinDef(type="inner", table="customers", alias="c", on=()),
        select=(
            SelectField(kind="column", source=ColumnRef("c", "customer_id"), label="customer_id"),
        ),
        where=Predicate(left=ColumnRef("c", "status"), op="is_null", right=None),
        limit=None,
    )
    result = compiler.compile(spec, catalog, Dialect.postgres)
    sql = normalize_sql(result.sql)
    assert "c.status IS NULL" in sql


def test_or_filter_group(compiler, catalog):
    spec = QuerySpec(
        connection_id="conn1",
        source=JoinDef(type="inner", table="customers", alias="c", on=()),
        select=(
            SelectField(kind="column", source=ColumnRef("c", "customer_id"), label="customer_id"),
        ),
        where=FilterGroup(
            op="or",
            items=(
                Predicate(left=ColumnRef("c", "status"), op="=", right=ValueRef("active")),
                Predicate(left=ColumnRef("c", "status"), op="=", right=ValueRef("trial")),
            ),
        ),
        limit=None,
    )
    result = compiler.compile(spec, catalog, Dialect.postgres)
    sql = normalize_sql(result.sql)
    assert "OR" in sql
    assert result.params["status_1"] == "active"
    assert result.params["status_2"] == "trial"


# ---------------------------------------------------------------------------
# Task 4.1 — edge cases
# ---------------------------------------------------------------------------

def test_is_null_no_bound_param(compiler, catalog):
    spec = QuerySpec(
        connection_id="conn1",
        source=JoinDef(type="inner", table="customers", alias="c", on=()),
        select=(SelectField(kind="column", source=ColumnRef("c", "customer_id"), label="customer_id"),),
        where=Predicate(left=ColumnRef("c", "status"), op="is_null"),
        limit=None,
    )
    result = compiler.compile(spec, catalog, Dialect.postgres)
    assert "IS NULL" in normalize_sql(result.sql)
    assert result.params == {}


def test_in_with_three_value_refs(compiler, catalog):
    spec = QuerySpec(
        connection_id="conn1",
        source=JoinDef(type="inner", table="customers", alias="c", on=()),
        select=(SelectField(kind="column", source=ColumnRef("c", "customer_id"), label="customer_id"),),
        where=Predicate(
            left=ColumnRef("c", "status"),
            op="in",
            right=(ValueRef("active"), ValueRef("trial"), ValueRef("pending")),
        ),
        limit=None,
    )
    result = compiler.compile(spec, catalog, Dialect.postgres)
    sql = normalize_sql(result.sql)
    assert "IN" in sql
    assert len(result.params) == 3
    assert set(result.params.values()) == {"active", "trial", "pending"}


def test_nested_or_in_and_parenthesisation(compiler, catalog):
    spec = QuerySpec(
        connection_id="conn1",
        source=JoinDef(type="inner", table="customers", alias="c", on=()),
        select=(SelectField(kind="column", source=ColumnRef("c", "customer_id"), label="customer_id"),),
        where=FilterGroup(
            op="and",
            items=(
                FilterGroup(
                    op="or",
                    items=(
                        Predicate(left=ColumnRef("c", "status"), op="=", right=ValueRef("active")),
                        Predicate(left=ColumnRef("c", "country"), op="=", right=ValueRef("US")),
                    ),
                ),
                Predicate(left=ColumnRef("c", "age"), op=">", right=ValueRef(18)),
            ),
        ),
        limit=None,
    )
    result = compiler.compile(spec, catalog, Dialect.postgres)
    sql = normalize_sql(result.sql)
    assert "AND" in sql
    assert "OR" in sql
    # The OR clause must be wrapped in parens so AND binds correctly
    assert "(" in sql


def test_limit_none_produces_no_limit_clause(compiler, catalog):
    spec = QuerySpec(
        connection_id="conn1",
        source=JoinDef(type="inner", table="customers", alias="c", on=()),
        select=(SelectField(kind="column", source=ColumnRef("c", "customer_id"), label="customer_id"),),
        limit=None,
    )
    result_pg = compiler.compile(spec, catalog, Dialect.postgres)
    result_ms = compiler.compile(spec, catalog, Dialect.mssql)
    assert "LIMIT" not in normalize_sql(result_pg.sql).upper()
    assert "TOP" not in normalize_sql(result_ms.sql).upper()
