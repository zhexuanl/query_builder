from __future__ import annotations

import importlib.resources
import json
from functools import lru_cache
from typing import Any

from ..entities.query_spec import QuerySpec
from .dialect import Dialect
from .filters import FilterGroup, Predicate
from .query_parts import JoinDef, SelectField, SortDef
from .refs import ColumnRef, Operand, ParamRef, ValueRef

_SUPPORTED_VERSIONS: frozenset[int] = frozenset({1})


@lru_cache(maxsize=1)
def _load_schema() -> dict[str, Any] | None:
    try:
        import jsonschema  # noqa: F401 — presence check only
        # Try importlib.resources first (works when installed as query_builder).
        # Fall back to path-relative lookup for development/editable installs.
        schema_text: str | None = None
        try:
            pkg = importlib.resources.files(__name__.split(".")[0])
            schema_text = pkg.joinpath("schemas/queryspec.v1.json").read_text(encoding="utf-8")
        except Exception:
            pass
        if schema_text is None:
            import pathlib
            schema_path = pathlib.Path(__file__).parents[2] / "schemas" / "queryspec.v1.json"
            if schema_path.exists():
                schema_text = schema_path.read_text(encoding="utf-8")
        return json.loads(schema_text) if schema_text else None
    except Exception:
        return None


def _enc_column_ref(ref: ColumnRef) -> dict[str, Any]:
    return {"kind": "column", "alias": ref.alias, "name": ref.name}


def _enc_param_ref(ref: ParamRef) -> dict[str, Any]:
    return {"kind": "param", "name": ref.name}


def _enc_value_ref(ref: ValueRef) -> dict[str, Any]:
    return {"kind": "value", "value": ref.value}


def _enc_operand(op: Operand) -> dict[str, Any]:
    if isinstance(op, ColumnRef):
        return _enc_column_ref(op)
    if isinstance(op, ParamRef):
        return _enc_param_ref(op)
    return _enc_value_ref(op)


def _enc_predicate(pred: Predicate) -> dict[str, Any]:
    d: dict[str, Any] = {"left": _enc_column_ref(pred.left), "op": pred.op}
    if pred.right is None:
        d["right"] = None
    elif isinstance(pred.right, tuple):
        d["right"] = [_enc_operand(o) for o in pred.right]
    else:
        d["right"] = _enc_operand(pred.right)
    return d


def _enc_filter(node: FilterGroup | Predicate) -> dict[str, Any]:
    if isinstance(node, FilterGroup):
        return {"op": node.op, "items": [_enc_filter(i) for i in node.items]}
    return _enc_predicate(node)


def _enc_join_def(j: JoinDef) -> dict[str, Any]:
    return {
        "type": j.type,
        "table": j.table,
        "alias": j.alias,
        "on": [_enc_predicate(p) for p in j.on],
    }


def _enc_select_field(f: SelectField) -> dict[str, Any]:
    d: dict[str, Any] = {
        "kind": f.kind,
        "source": _enc_column_ref(f.source),
        "label": f.label,
    }
    if f.func is not None:
        d["func"] = f.func
    return d


def _enc_sort_def(s: SortDef) -> dict[str, Any]:
    return {"label": s.label, "direction": s.direction}


def _dec_operand(data: dict[str, Any]) -> Operand:
    kind = data.get("kind")
    if kind == "column":
        return ColumnRef(alias=data["alias"], name=data["name"])
    if kind == "param":
        return ParamRef(name=data["name"])
    if kind == "value":
        return ValueRef(value=data["value"])
    raise ValueError(f"Unknown operand kind: {kind!r}")


def _dec_predicate(data: dict[str, Any]) -> Predicate:
    left = ColumnRef(alias=data["left"]["alias"], name=data["left"]["name"])
    raw_right = data.get("right")
    right: Operand | tuple[Operand, ...] | None
    if raw_right is None:
        right = None
    elif isinstance(raw_right, list):
        right = tuple(_dec_operand(o) for o in raw_right)
    else:
        right = _dec_operand(raw_right)
    return Predicate(left=left, op=data["op"], right=right)


def _dec_filter(data: dict[str, Any]) -> FilterGroup | Predicate:
    if "items" in data:
        items = tuple(_dec_filter(i) for i in data["items"])
        return FilterGroup(op=data["op"], items=items)
    return _dec_predicate(data)


def _dec_join_def(data: dict[str, Any]) -> JoinDef:
    return JoinDef(
        type=data["type"],
        table=data["table"],
        alias=data["alias"],
        on=tuple(_dec_predicate(p) for p in data.get("on", [])),
    )


def _dec_select_field(data: dict[str, Any]) -> SelectField:
    src = data["source"]
    return SelectField(
        kind=data["kind"],
        source=ColumnRef(alias=src["alias"], name=src["name"]),
        label=data["label"],
        func=data.get("func"),
    )


class QuerySpecCodec:
    """Serialises and deserialises ``QuerySpec`` to/from JSON-compatible dicts.

    ``encode`` injects a ``"kind"`` discriminator on every ``ColumnRef``,
    ``ParamRef``, and ``ValueRef`` so the JSON representation is
    unambiguously typed.  ``decode`` reads ``"kind"`` to reconstruct the
    correct Python type and raises ``ValueError`` on unknown kinds.
    """

    @staticmethod
    def encode(spec: QuerySpec) -> dict[str, Any]:
        d: dict[str, Any] = {
            "version": spec.version,
            "connection_id": spec.connection_id,
            "source": _enc_join_def(spec.source),
            "select": [_enc_select_field(f) for f in spec.select],
        }
        if spec.joins:
            d["joins"] = [_enc_join_def(j) for j in spec.joins]
        if spec.where is not None:
            d["where"] = _enc_filter(spec.where)
        if spec.group_by:
            d["group_by"] = [_enc_column_ref(c) for c in spec.group_by]
        if spec.order_by:
            d["order_by"] = [_enc_sort_def(s) for s in spec.order_by]
        if spec.limit is not None:
            d["limit"] = spec.limit
        return d

    @staticmethod
    def decode(data: dict[str, Any]) -> QuerySpec:
        _schema = _load_schema()
        if _schema is not None:
            import jsonschema
            try:
                jsonschema.validate(instance=data, schema=_schema)
            except jsonschema.ValidationError as exc:
                raise ValueError(str(exc)) from exc
        version = data.get("version", 1)
        if version not in _SUPPORTED_VERSIONS:
            raise ValueError(f"Unsupported QuerySpec version: {version!r}")
        where_data = data.get("where")
        group_by_raw = data.get("group_by", [])
        order_by_raw = data.get("order_by", [])
        return QuerySpec(
            version=data.get("version", 1),
            connection_id=data["connection_id"],
            source=_dec_join_def(data["source"]),
            select=tuple(_dec_select_field(f) for f in data["select"]),
            joins=tuple(_dec_join_def(j) for j in data.get("joins", [])),
            where=_dec_filter(where_data) if where_data is not None else None,
            group_by=tuple(
                ColumnRef(alias=c["alias"], name=c["name"]) for c in group_by_raw
            ),
            order_by=tuple(SortDef(label=s["label"], direction=s["direction"]) for s in order_by_raw),
            limit=data["limit"] if "limit" in data else None,
        )
