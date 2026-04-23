"""Shared helpers for converting Pydantic API models to domain QuerySpec objects."""
from typing import Any

from domain.entities.query_spec import QuerySpec
from domain.value_objects.filters import FilterGroup, Predicate
from domain.value_objects.query_parts import JoinDef, SelectField, SortDef
from domain.value_objects.refs import ColumnRef, ParamRef, ValueRef
from infrastructure.api.models.query_models import _FilterGroupModel, _PredicateModel


def col(m: Any) -> ColumnRef:
    return ColumnRef(alias=m.alias, name=m.name)


def operand_from_json(v: Any) -> Any:
    if isinstance(v, dict):
        if "alias" in v and "name" in v:
            return ColumnRef(alias=v["alias"], name=v["name"])
        if "name" in v:
            return ParamRef(name=v["name"])
    return ValueRef(value=v)


def predicate(m: _PredicateModel) -> Predicate:
    right = m.right
    if isinstance(right, list):
        right = tuple(operand_from_json(v) for v in right)
    elif right is not None:
        right = operand_from_json(right)
    return Predicate(left=col(m.left), op=m.op, right=right)


def filter_group(m: _FilterGroupModel) -> FilterGroup:
    items = tuple(
        filter_group(i) if isinstance(i, _FilterGroupModel) else predicate(i)
        for i in m.items
    )
    return FilterGroup(op=m.op, items=items)


def to_domain_spec(req: Any) -> QuerySpec:
    """Convert a Pydantic request model with QuerySpec fields to a domain QuerySpec.

    Accepts any model that exposes: connection_id, source, select, joins, where,
    group_by, order_by, limit — matching both QuerySpecRequest and SaveDatasetRequest.
    """
    def _join(m: Any) -> JoinDef:
        return JoinDef(
            type=m.type,
            table=m.table,
            alias=m.alias,
            on=tuple(predicate(p) for p in m.on),
        )

    return QuerySpec(
        connection_id=req.connection_id,
        source=_join(req.source),
        select=tuple(
            SelectField(kind=f.kind, source=col(f.source), label=f.label, func=f.func)
            for f in req.select
        ),
        joins=tuple(_join(j) for j in req.joins),
        where=filter_group(req.where) if req.where else None,
        group_by=tuple(col(c) for c in req.group_by),
        order_by=tuple(SortDef(label=s.label, direction=s.direction) for s in req.order_by),
        limit=req.limit,
    )
