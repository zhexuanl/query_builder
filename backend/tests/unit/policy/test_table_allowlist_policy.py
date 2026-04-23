"""Unit tests for TableAllowlistPolicy entitlement rules."""
import pytest

from adapters.policy.table_allowlist_policy import TableAllowlistPolicy
from domain.entities.query_spec import QuerySpec
from domain.errors import PolicyViolation
from domain.value_objects.filters import Predicate
from domain.value_objects.query_parts import JoinDef, SelectField
from domain.value_objects.refs import ColumnRef


def _source(table: str = "customers") -> JoinDef:
    return JoinDef(type="inner", table=table, alias="c", on=())


def _join(alias: str, table: str) -> JoinDef:
    return JoinDef(
        type="inner", table=table, alias=alias,
        on=(Predicate(left=ColumnRef("c", "id"), op="=", right=ColumnRef(alias, "c_id")),),
    )


def _field(label: str = "id") -> SelectField:
    return SelectField(kind="column", source=ColumnRef("c", "id"), label=label)


def _spec(connection_id: str = "conn-1", source_table: str = "customers", joins=()) -> QuerySpec:
    return QuerySpec(
        connection_id=connection_id,
        source=_source(source_table),
        select=(_field(),),
        joins=joins,
        limit=100,
    )


_catalog = None


# ---------------------------------------------------------------------------
# 5.7  Unapproved source table
# ---------------------------------------------------------------------------

def test_unapproved_source_table_raises():
    policy = TableAllowlistPolicy({"conn-1": frozenset({"orders"})})
    spec = _spec(source_table="customers")
    with pytest.raises(PolicyViolation, match="'customers'"):
        policy.validate(spec, _catalog)


# ---------------------------------------------------------------------------
# 5.8  Unapproved join table
# ---------------------------------------------------------------------------

def test_unapproved_join_table_raises():
    policy = TableAllowlistPolicy({"conn-1": frozenset({"customers"})})
    spec = _spec(joins=(_join("o", "orders"),))
    with pytest.raises(PolicyViolation, match="'orders'"):
        policy.validate(spec, _catalog)


# ---------------------------------------------------------------------------
# 5.9  Approved / unknown connection
# ---------------------------------------------------------------------------

def test_all_tables_approved_passes():
    policy = TableAllowlistPolicy({"conn-1": frozenset({"customers", "orders"})})
    spec = _spec(joins=(_join("o", "orders"),))
    policy.validate(spec, _catalog)  # must not raise


def test_unknown_connection_id_raises():
    policy = TableAllowlistPolicy({})  # no entry for conn-1
    spec = _spec()
    with pytest.raises(PolicyViolation, match="No allowlist configured"):
        policy.validate(spec, _catalog)
