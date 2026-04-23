from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from domain.errors import CatalogMiss, CompilationError, PolicyViolation, SourceConnectionError
from domain.entities.query_spec import QuerySpec
from domain.value_objects.dialect import Dialect
from domain.value_objects.filters import FilterGroup, Predicate
from domain.value_objects.query_parts import JoinDef, SelectField, SortDef
from domain.value_objects.refs import ColumnRef, ParamRef, ValueRef
from infrastructure.api.models.query_models import (
    ErrorResponse,
    QueryResultResponse,
    QuerySpecRequest,
    _FilterGroupModel,
    _PredicateModel,
)
from use_cases.execute_query import ExecuteQueryUseCase


def _col(m) -> ColumnRef:
    return ColumnRef(alias=m.alias, name=m.name)


def _operand_from_json(v: Any):
    """Convert a raw JSON value to the appropriate Operand domain type."""
    if isinstance(v, dict):
        if "alias" in v and "name" in v:
            return ColumnRef(alias=v["alias"], name=v["name"])
        if "name" in v:
            return ParamRef(name=v["name"])
    return ValueRef(value=v)


def _predicate(m) -> Predicate:
    right = m.right
    if isinstance(right, list):
        right = tuple(_operand_from_json(v) for v in right)
    elif right is not None:
        right = _operand_from_json(right)
    return Predicate(left=_col(m.left), op=m.op, right=right)


def _filter_group(m: _FilterGroupModel) -> FilterGroup:
    items = tuple(
        _filter_group(i) if isinstance(i, _FilterGroupModel) else _predicate(i)
        for i in m.items
    )
    return FilterGroup(op=m.op, items=items)


def _to_domain_spec(req: QuerySpecRequest) -> QuerySpec:
    def _join(m) -> JoinDef:
        return JoinDef(
            type=m.type,
            table=m.table,
            alias=m.alias,
            on=tuple(_predicate(p) for p in m.on),
        )

    return QuerySpec(
        connection_id=req.connection_id,
        source=_join(req.source),
        select=tuple(
            SelectField(kind=f.kind, source=_col(f.source), label=f.label, func=f.func)
            for f in req.select
        ),
        joins=tuple(_join(j) for j in req.joins),
        where=_filter_group(req.where) if req.where else None,
        group_by=tuple(_col(c) for c in req.group_by),
        order_by=tuple(SortDef(label=s.label, direction=s.direction) for s in req.order_by),
        limit=req.limit,
    )


def make_queries_router(execute_use_case: ExecuteQueryUseCase) -> APIRouter:
    """Build and return a queries router wired to ``execute_use_case``."""
    router = APIRouter(prefix="/queries")

    @router.post("/execute", response_model=QueryResultResponse)
    async def execute_query(req: QuerySpecRequest):
        try:
            spec = _to_domain_spec(req)
            dialect = Dialect(req.dialect)
            rows = execute_use_case.execute(spec, dialect, caller_id=req.caller_id)
            return QueryResultResponse.from_rows(rows)
        except PolicyViolation as exc:
            return JSONResponse(
                status_code=422,
                content=ErrorResponse(error_code="POLICY_VIOLATION", detail=str(exc)).model_dump(),
            )
        except CompilationError as exc:
            return JSONResponse(
                status_code=422,
                content=ErrorResponse(error_code="COMPILATION_ERROR", detail=str(exc)).model_dump(),
            )
        except CatalogMiss as exc:
            return JSONResponse(
                status_code=422,
                content=ErrorResponse(error_code="CATALOG_MISS", detail=str(exc)).model_dump(),
            )
        except SourceConnectionError:
            return JSONResponse(
                status_code=502,
                content=ErrorResponse(error_code="SOURCE_UNAVAILABLE").model_dump(),
            )

    return router
