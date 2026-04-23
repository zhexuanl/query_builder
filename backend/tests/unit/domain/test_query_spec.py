"""Unit tests for all domain value objects and the QuerySpec aggregate root."""
import pytest

from domain.value_objects.refs import ColumnRef, ParamRef, ValueRef
from domain.value_objects.dialect import Dialect
from domain.value_objects.filters import FilterGroup, Predicate
from domain.value_objects.query_parts import JoinDef, SelectField, SortDef
from domain.entities.query_spec import QuerySpec


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def customer_id() -> ColumnRef:
    return ColumnRef(alias="c", name="customer_id")


@pytest.fixture()
def country() -> ColumnRef:
    return ColumnRef(alias="c", name="country")


@pytest.fixture()
def status_col() -> ColumnRef:
    return ColumnRef(alias="c", name="status")


@pytest.fixture()
def source_join() -> JoinDef:
    return JoinDef(type="inner", table="customers", alias="c", on=())


@pytest.fixture()
def txn_join(customer_id) -> JoinDef:
    return JoinDef(
        type="left",
        table="transactions",
        alias="t",
        on=(Predicate(left=customer_id, op="=", right=ColumnRef(alias="t", name="customer_id")),),
    )


@pytest.fixture()
def select_id(customer_id) -> SelectField:
    return SelectField(kind="column", source=customer_id, label="customer_id")


@pytest.fixture()
def select_country(country) -> SelectField:
    return SelectField(kind="column", source=country, label="country")


@pytest.fixture()
def select_txn_count() -> SelectField:
    return SelectField(
        kind="agg",
        source=ColumnRef(alias="t", name="transaction_id"),
        label="txn_count",
        func="count",
    )


# ---------------------------------------------------------------------------
# ColumnRef
# ---------------------------------------------------------------------------

class TestColumnRef:
    def test_valid(self):
        ref = ColumnRef(alias="c", name="id")
        assert str(ref) == "c.id"

    def test_empty_alias_raises(self):
        with pytest.raises(ValueError, match="alias"):
            ColumnRef(alias="", name="id")

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="name"):
            ColumnRef(alias="c", name="")

    def test_frozen(self, customer_id):
        with pytest.raises(Exception):
            customer_id.alias = "x"  # type: ignore[misc]

    def test_equality(self):
        assert ColumnRef("c", "id") == ColumnRef("c", "id")
        assert ColumnRef("c", "id") != ColumnRef("c", "name")

    def test_hashable(self):
        s = {ColumnRef("c", "id"), ColumnRef("c", "id")}
        assert len(s) == 1


# ---------------------------------------------------------------------------
# ParamRef / ValueRef
# ---------------------------------------------------------------------------

class TestParamRef:
    def test_valid(self):
        p = ParamRef(name="status")
        assert p.name == "status"

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="name"):
            ParamRef(name="")


class TestValueRef:
    def test_scalar_types(self):
        assert ValueRef(value="active").value == "active"
        assert ValueRef(value=42).value == 42
        assert ValueRef(value=3.14).value == 3.14
        assert ValueRef(value=True).value is True
        assert ValueRef(value=None).value is None


# ---------------------------------------------------------------------------
# Predicate
# ---------------------------------------------------------------------------

class TestPredicate:
    def test_scalar_op(self, customer_id):
        p = Predicate(left=customer_id, op="=", right=ValueRef(value=1))
        assert p.op == "="

    def test_column_to_column(self, customer_id):
        p = Predicate(
            left=customer_id,
            op="=",
            right=ColumnRef(alias="t", name="customer_id"),
        )
        assert isinstance(p.right, ColumnRef)

    def test_param_ref_right(self, customer_id):
        p = Predicate(left=customer_id, op="=", right=ParamRef(name="cid"))
        assert isinstance(p.right, ParamRef)

    def test_nullary_op_no_right(self, customer_id):
        p = Predicate(left=customer_id, op="is_null")
        assert p.right is None

    def test_nullary_op_with_right_raises(self, customer_id):
        with pytest.raises(ValueError, match="no right operand"):
            Predicate(left=customer_id, op="is_null", right=ValueRef(value=1))

    def test_scalar_op_missing_right_raises(self, customer_id):
        with pytest.raises(ValueError, match="requires a right operand"):
            Predicate(left=customer_id, op="=")

    def test_scalar_op_tuple_right_raises(self, customer_id):
        with pytest.raises(ValueError, match="scalar right operand"):
            Predicate(left=customer_id, op="=", right=(ValueRef(value=1), ValueRef(value=2)))

    def test_in_op(self, customer_id):
        p = Predicate(
            left=customer_id,
            op="in",
            right=(ValueRef(value=1), ValueRef(value=2), ValueRef(value=3)),
        )
        assert len(p.right) == 3  # type: ignore[arg-type]

    def test_in_op_empty_raises(self, customer_id):
        with pytest.raises(ValueError, match="non-empty tuple"):
            Predicate(left=customer_id, op="in", right=())

    def test_between_op(self, customer_id):
        p = Predicate(
            left=customer_id,
            op="between",
            right=(ValueRef(value=1), ValueRef(value=100)),
        )
        assert len(p.right) == 2  # type: ignore[arg-type]

    def test_between_wrong_count_raises(self, customer_id):
        with pytest.raises(ValueError, match="exactly 2"):
            Predicate(
                left=customer_id,
                op="between",
                right=(ValueRef(value=1), ValueRef(value=2), ValueRef(value=3)),
            )


# ---------------------------------------------------------------------------
# FilterGroup
# ---------------------------------------------------------------------------

class TestFilterGroup:
    def test_single_predicate(self, customer_id):
        pred = Predicate(left=customer_id, op="is_null")
        g = FilterGroup(op="and", items=(pred,))
        assert len(g.items) == 1

    def test_empty_items_raises(self):
        with pytest.raises(ValueError, match="at least one item"):
            FilterGroup(op="and", items=())

    def test_nested_groups(self, customer_id, status_col):
        inner = FilterGroup(
            op="or",
            items=(
                Predicate(left=customer_id, op="is_null"),
                Predicate(left=status_col, op="=", right=ValueRef(value="active")),
            ),
        )
        outer = FilterGroup(
            op="and",
            items=(inner, Predicate(left=customer_id, op="is_not_null")),
        )
        assert len(outer.items) == 2
        assert outer.items[0] is inner

    def test_frozen(self, customer_id):
        g = FilterGroup(op="and", items=(Predicate(left=customer_id, op="is_null"),))
        with pytest.raises(Exception):
            g.op = "or"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# JoinDef
# ---------------------------------------------------------------------------

class TestJoinDef:
    def test_source_with_empty_on(self):
        j = JoinDef(type="inner", table="customers", alias="c", on=())
        assert j.on == ()

    def test_empty_table_raises(self):
        with pytest.raises(ValueError, match="table"):
            JoinDef(type="inner", table="", alias="c", on=())

    def test_empty_alias_raises(self):
        with pytest.raises(ValueError, match="alias"):
            JoinDef(type="inner", table="customers", alias="", on=())


# ---------------------------------------------------------------------------
# SelectField
# ---------------------------------------------------------------------------

class TestSelectField:
    def test_column_kind(self, customer_id):
        f = SelectField(kind="column", source=customer_id, label="customer_id")
        assert f.func is None

    def test_agg_kind(self):
        f = SelectField(
            kind="agg",
            source=ColumnRef(alias="t", name="amount"),
            label="total",
            func="sum",
        )
        assert f.func == "sum"

    def test_agg_without_func_raises(self, customer_id):
        with pytest.raises(ValueError, match="func"):
            SelectField(kind="agg", source=customer_id, label="x")

    def test_column_with_func_raises(self, customer_id):
        with pytest.raises(ValueError, match="must not set func"):
            SelectField(kind="column", source=customer_id, label="x", func="count")

    def test_empty_label_raises(self, customer_id):
        with pytest.raises(ValueError, match="label"):
            SelectField(kind="column", source=customer_id, label="")


# ---------------------------------------------------------------------------
# QuerySpec
# ---------------------------------------------------------------------------

class TestQuerySpec:
    def test_minimal_valid(self, source_join, select_id):
        spec = QuerySpec(
            connection_id="conn-1",
            source=source_join,
            select=(select_id,),
        )
        assert spec.version == 1
        assert spec.limit == 1000
        assert not spec.is_aggregating

    def test_with_join(self, source_join, txn_join, select_id, select_txn_count, customer_id, country):
        spec = QuerySpec(
            connection_id="conn-1",
            source=source_join,
            joins=(txn_join,),
            select=(select_id, select_txn_count),
            group_by=(customer_id,),
        )
        assert spec.is_aggregating
        assert "c" in spec.all_table_aliases
        assert "t" in spec.all_table_aliases

    def test_with_filter(self, source_join, select_id, status_col):
        where = FilterGroup(
            op="and",
            items=(Predicate(left=status_col, op="=", right=ValueRef(value="active")),),
        )
        spec = QuerySpec(
            connection_id="conn-1",
            source=source_join,
            select=(select_id,),
            where=where,
        )
        assert spec.where is not None

    def test_with_sort_and_limit(self, source_join, select_id):
        spec = QuerySpec(
            connection_id="conn-1",
            source=source_join,
            select=(select_id,),
            order_by=(SortDef(label="customer_id", direction="desc"),),
            limit=500,
        )
        assert spec.limit == 500

    def test_unlimited(self, source_join, select_id):
        spec = QuerySpec(
            connection_id="conn-1",
            source=source_join,
            select=(select_id,),
            limit=None,
        )
        assert spec.limit is None

    def test_empty_select_raises(self, source_join):
        with pytest.raises(ValueError, match="at least one field"):
            QuerySpec(connection_id="conn-1", source=source_join, select=())

    def test_empty_connection_id_raises(self, source_join, select_id):
        with pytest.raises(ValueError, match="connection_id"):
            QuerySpec(connection_id="", source=source_join, select=(select_id,))

    def test_zero_limit_raises(self, source_join, select_id):
        with pytest.raises(ValueError, match="positive integer"):
            QuerySpec(connection_id="conn-1", source=source_join, select=(select_id,), limit=0)

    def test_negative_limit_raises(self, source_join, select_id):
        with pytest.raises(ValueError, match="positive integer"):
            QuerySpec(connection_id="conn-1", source=source_join, select=(select_id,), limit=-1)

    def test_agg_without_group_by_raises(self, source_join, select_id, select_txn_count):
        """Non-agg column in select without group_by must be rejected."""
        with pytest.raises(ValueError, match="group_by"):
            QuerySpec(
                connection_id="conn-1",
                source=source_join,
                select=(select_id, select_txn_count),
                # select_id is kind="column" but group_by is empty → invalid
            )

    def test_agg_only_no_group_by_ok(self, source_join):
        """Pure aggregate with no group_by columns is valid (e.g. SELECT COUNT(*))."""
        spec = QuerySpec(
            connection_id="conn-1",
            source=source_join,
            select=(
                SelectField(
                    kind="agg",
                    source=ColumnRef(alias="c", name="customer_id"),
                    label="total",
                    func="count",
                ),
            ),
        )
        assert spec.is_aggregating

    def test_all_table_aliases(self, source_join, txn_join, select_id):
        spec = QuerySpec(
            connection_id="conn-1",
            source=source_join,
            joins=(txn_join,),
            select=(select_id,),
        )
        assert spec.all_table_aliases == frozenset({"c", "t"})


# ---------------------------------------------------------------------------
# Dialect
# ---------------------------------------------------------------------------

class TestDialect:
    def test_values(self):
        assert Dialect.postgres == "postgres"
        assert Dialect.mssql == "mssql"

    def test_from_string(self):
        assert Dialect("postgres") is Dialect.postgres
