from typing import Any, Literal

from pydantic import BaseModel


class _ColumnRefModel(BaseModel):
    alias: str
    name: str


class _PredicateModel(BaseModel):
    left: _ColumnRefModel
    op: str
    right: Any = None


class _FilterGroupModel(BaseModel):
    op: Literal["and", "or"]
    items: list["_FilterGroupModel | _PredicateModel"]


_FilterGroupModel.model_rebuild()


class _JoinDefModel(BaseModel):
    type: Literal["inner", "left"]
    table: str
    alias: str
    on: list[_PredicateModel] = []


class _SelectFieldModel(BaseModel):
    kind: Literal["column", "agg"]
    source: _ColumnRefModel
    label: str
    func: Literal["count", "count_distinct", "sum", "avg", "min", "max"] | None = None


class _SortDefModel(BaseModel):
    label: str
    direction: Literal["asc", "desc"] = "asc"


class ErrorResponse(BaseModel):
    """Structured error response body."""

    error_code: str
    detail: str | None = None


class QuerySpecRequest(BaseModel):
    """HTTP request body for POST /queries/execute."""

    connection_id: str
    caller_id: str
    source: _JoinDefModel
    select: list[_SelectFieldModel]
    joins: list[_JoinDefModel] = []
    where: _FilterGroupModel | None = None
    group_by: list[_ColumnRefModel] = []
    order_by: list[_SortDefModel] = []
    limit: int | None = 1000
    dialect: Literal["postgres", "mssql"]


class QueryResultResponse(BaseModel):
    """HTTP response body for POST /queries/execute."""

    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int

    @classmethod
    def from_rows(cls, rows: list[dict[str, Any]]) -> "QueryResultResponse":
        columns = list(rows[0].keys()) if rows else []
        return cls(columns=columns, rows=rows, row_count=len(rows))
