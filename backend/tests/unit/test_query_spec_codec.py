"""Unit tests for QuerySpecCodec encode/decode round-trips."""
import pytest

from domain.entities.query_spec import QuerySpec
from domain.value_objects.filters import FilterGroup, Predicate
from domain.value_objects.query_parts import JoinDef, SelectField, SortDef
from domain.value_objects.refs import ColumnRef, ParamRef, ValueRef
from domain.value_objects.serialisation import QuerySpecCodec


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def source() -> JoinDef:
    return JoinDef(type="inner", table="customers", alias="c", on=())


@pytest.fixture()
def id_col() -> ColumnRef:
    return ColumnRef(alias="c", name="id")


@pytest.fixture()
def minimal_spec(source, id_col) -> QuerySpec:
    return QuerySpec(
        connection_id="conn-1",
        source=source,
        select=(SelectField(kind="column", source=id_col, label="id"),),
    )


# ---------------------------------------------------------------------------
# Encode tests
# ---------------------------------------------------------------------------

class TestEncode:
    def test_column_ref_encoded_with_kind_column(self, minimal_spec):
        data = QuerySpecCodec.encode(minimal_spec)
        source_enc = data["source"]
        assert source_enc["alias"] == "c"
        assert source_enc["table"] == "customers"
        select_source = data["select"][0]["source"]
        assert select_source["kind"] == "column"
        assert select_source["alias"] == "c"
        assert select_source["name"] == "id"

    def test_param_ref_encoded_with_kind_param(self, source):
        spec = QuerySpec(
            connection_id="conn-1",
            source=source,
            select=(SelectField(kind="column", source=ColumnRef("c", "id"), label="id"),),
            where=FilterGroup(
                op="and",
                items=(
                    Predicate(
                        left=ColumnRef("c", "name"),
                        op="=",
                        right=ParamRef(name="p_name"),
                    ),
                ),
            ),
        )
        data = QuerySpecCodec.encode(spec)
        right = data["where"]["items"][0]["right"]
        assert right == {"kind": "param", "name": "p_name"}

    def test_value_ref_encoded_with_kind_value(self, source):
        spec = QuerySpec(
            connection_id="conn-1",
            source=source,
            select=(SelectField(kind="column", source=ColumnRef("c", "id"), label="id"),),
            where=FilterGroup(
                op="and",
                items=(
                    Predicate(
                        left=ColumnRef("c", "status"),
                        op="=",
                        right=ValueRef(value="active"),
                    ),
                ),
            ),
        )
        data = QuerySpecCodec.encode(spec)
        right = data["where"]["items"][0]["right"]
        assert right == {"kind": "value", "value": "active"}

    def test_nullary_predicate_right_is_none(self, source):
        spec = QuerySpec(
            connection_id="conn-1",
            source=source,
            select=(SelectField(kind="column", source=ColumnRef("c", "id"), label="id"),),
            where=FilterGroup(
                op="and",
                items=(Predicate(left=ColumnRef("c", "deleted_at"), op="is_null"),),
            ),
        )
        data = QuerySpecCodec.encode(spec)
        assert data["where"]["items"][0]["right"] is None

    def test_tuple_right_encoded_as_list(self, source):
        spec = QuerySpec(
            connection_id="conn-1",
            source=source,
            select=(SelectField(kind="column", source=ColumnRef("c", "id"), label="id"),),
            where=FilterGroup(
                op="and",
                items=(
                    Predicate(
                        left=ColumnRef("c", "age"),
                        op="between",
                        right=(ValueRef(value=18), ValueRef(value=65)),
                    ),
                ),
            ),
        )
        data = QuerySpecCodec.encode(spec)
        right = data["where"]["items"][0]["right"]
        assert right == [{"kind": "value", "value": 18}, {"kind": "value", "value": 65}]


# ---------------------------------------------------------------------------
# Decode tests
# ---------------------------------------------------------------------------

class TestDecode:
    def test_round_trip_minimal_spec(self, minimal_spec):
        data = QuerySpecCodec.encode(minimal_spec)
        decoded = QuerySpecCodec.decode(data)
        assert decoded == minimal_spec

    def test_round_trip_unlimited_spec(self, source, id_col):
        spec = QuerySpec(
            connection_id="conn-1",
            source=source,
            select=(SelectField(kind="column", source=id_col, label="id"),),
            limit=None,
        )
        decoded = QuerySpecCodec.decode(QuerySpecCodec.encode(spec))
        assert decoded.limit is None

    def test_value_ref_decoded_from_kind_value(self, source):
        data = {
            "version": 1,
            "connection_id": "conn-1",
            "source": {"type": "inner", "table": "customers", "alias": "c", "on": []},
            "select": [
                {"kind": "column", "source": {"kind": "column", "alias": "c", "name": "id"}, "label": "id"}
            ],
            "where": {
                "op": "and",
                "items": [
                    {
                        "left": {"kind": "column", "alias": "c", "name": "status"},
                        "op": "=",
                        "right": {"kind": "value", "value": 42},
                    }
                ],
            },
        }
        spec = QuerySpecCodec.decode(data)
        pred = spec.where.items[0]  # type: ignore[union-attr]
        assert isinstance(pred, Predicate)
        assert isinstance(pred.right, ValueRef)
        assert pred.right.value == 42

    def test_column_ref_decoded_from_kind_column(self):
        data = {
            "version": 1,
            "connection_id": "conn-1",
            "source": {"type": "inner", "table": "customers", "alias": "c", "on": []},
            "select": [
                {"kind": "column", "source": {"kind": "column", "alias": "c", "name": "id"}, "label": "id"}
            ],
            "where": {
                "op": "and",
                "items": [
                    {
                        "left": {"kind": "column", "alias": "c", "name": "ref_col"},
                        "op": "=",
                        "right": {"kind": "column", "alias": "c", "name": "other_col"},
                    }
                ],
            },
        }
        spec = QuerySpecCodec.decode(data)
        pred = spec.where.items[0]  # type: ignore[union-attr]
        assert isinstance(pred.right, ColumnRef)
        assert pred.right == ColumnRef("c", "other_col")

    def test_unknown_kind_raises_value_error(self):
        data = {
            "version": 1,
            "connection_id": "conn-1",
            "source": {"type": "inner", "table": "customers", "alias": "c", "on": []},
            "select": [
                {"kind": "column", "source": {"kind": "column", "alias": "c", "name": "id"}, "label": "id"}
            ],
            "where": {
                "op": "and",
                "items": [
                    {
                        "left": {"kind": "column", "alias": "c", "name": "expr"},
                        "op": "=",
                        "right": {"kind": "expression", "sql": "NOW()"},
                    }
                ],
            },
        }
        with pytest.raises(ValueError):
            QuerySpecCodec.decode(data)

    def test_tuple_right_decoded_as_tuple(self):
        data = {
            "version": 1,
            "connection_id": "conn-1",
            "source": {"type": "inner", "table": "orders", "alias": "o", "on": []},
            "select": [
                {"kind": "column", "source": {"kind": "column", "alias": "o", "name": "id"}, "label": "id"}
            ],
            "where": {
                "op": "and",
                "items": [
                    {
                        "left": {"kind": "column", "alias": "o", "name": "amount"},
                        "op": "between",
                        "right": [
                            {"kind": "value", "value": 10},
                            {"kind": "value", "value": 100},
                        ],
                    }
                ],
            },
        }
        spec = QuerySpecCodec.decode(data)
        pred = spec.where.items[0]  # type: ignore[union-attr]
        assert isinstance(pred.right, tuple)
        assert len(pred.right) == 2
        assert all(isinstance(o, ValueRef) for o in pred.right)
