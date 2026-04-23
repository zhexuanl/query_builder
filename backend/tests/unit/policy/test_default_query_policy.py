"""Unit tests for DefaultQueryPolicy structural rules."""
import pytest

from adapters.policy.default_query_policy import DefaultQueryPolicy, _MAX_JOINS, _MAX_LIMIT
from domain.entities.query_spec import QuerySpec
from domain.errors import PolicyViolation
from domain.value_objects.query_parts import JoinDef, SelectField
from domain.value_objects.refs import ColumnRef


def _source(alias: str = "c", table: str = "customers") -> JoinDef:
    return JoinDef(type="inner", table=table, alias=alias, on=())


def _field(label: str, alias: str = "c", col: str = "id") -> SelectField:
    return SelectField(kind="column", source=ColumnRef(alias, col), label=label)


def _spec(**overrides) -> QuerySpec:
    defaults = dict(
        connection_id="conn-1",
        source=_source(),
        select=(_field("id"),),
        limit=100,
    )
    defaults.update(overrides)
    return QuerySpec(**defaults)


policy = DefaultQueryPolicy()
_catalog = None  # structural policy never uses catalog


# ---------------------------------------------------------------------------
# 5.2  Join count
# ---------------------------------------------------------------------------

def _join(alias: str, table: str) -> JoinDef:
    from domain.value_objects.filters import Predicate
    return JoinDef(
        type="inner", table=table, alias=alias,
        on=(Predicate(left=ColumnRef("c", "id"), op="=", right=ColumnRef(alias, "c_id")),),
    )


def test_join_count_exceeds_max_raises():
    joins = tuple(_join(f"t{i}", f"tbl{i}") for i in range(_MAX_JOINS + 1))
    spec = _spec(joins=joins)
    with pytest.raises(PolicyViolation, match="joins"):
        policy.validate(spec, _catalog)


def test_join_count_at_max_passes():
    joins = tuple(_join(f"t{i}", f"tbl{i}") for i in range(_MAX_JOINS))
    spec = _spec(joins=joins)
    policy.validate(spec, _catalog)  # must not raise


# ---------------------------------------------------------------------------
# 5.3  Row limit
# ---------------------------------------------------------------------------

def test_limit_none_raises():
    spec = _spec(limit=None)
    with pytest.raises(PolicyViolation, match="limit"):
        policy.validate(spec, _catalog)


def test_limit_exceeds_max_raises():
    spec = _spec(limit=_MAX_LIMIT + 1)
    with pytest.raises(PolicyViolation, match=str(_MAX_LIMIT + 1)):
        policy.validate(spec, _catalog)


def test_limit_at_max_passes():
    spec = _spec(limit=_MAX_LIMIT)
    policy.validate(spec, _catalog)  # must not raise


# ---------------------------------------------------------------------------
# 5.4  Duplicate output labels
# ---------------------------------------------------------------------------

def test_duplicate_label_raises():
    spec = _spec(select=(_field("id"), _field("id", col="email")))
    with pytest.raises(PolicyViolation, match="'id'"):
        policy.validate(spec, _catalog)


def test_unique_labels_pass():
    spec = _spec(select=(_field("id"), _field("email", col="email")))
    policy.validate(spec, _catalog)


# ---------------------------------------------------------------------------
# 5.5  Duplicate alias
# ---------------------------------------------------------------------------

def test_duplicate_alias_source_and_join_raises():
    join = _join("c", "orders")  # same alias as source "c"
    spec = _spec(joins=(join,))
    with pytest.raises(PolicyViolation, match="'c'"):
        policy.validate(spec, _catalog)


def test_unique_aliases_pass():
    join = _join("o", "orders")
    spec = _spec(joins=(join,))
    policy.validate(spec, _catalog)


def test_duplicate_alias_two_joins_raises():
    j1 = _join("t", "orders")
    j2 = _join("t", "products")  # same alias "t" as j1
    spec = _spec(joins=(j1, j2), select=(_field("id"), _field("oid")))
    with pytest.raises(PolicyViolation, match="'t'"):
        policy.validate(spec, _catalog)
