from __future__ import annotations

import dataclasses
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel

from domain.entities.dataset_definition import DatasetDefinition
from infrastructure.api.models.query_models import (
    _ColumnRefModel,
    _FilterGroupModel,
    _JoinDefModel,
    _SelectFieldModel,
    _SortDefModel,
)


class SaveDatasetRequest(BaseModel):
    """Request body for POST /datasets."""

    name: str
    description: str
    connection_id: str
    created_by: str
    dialect: Literal["postgres", "mssql"]
    source: _JoinDefModel
    select: list[_SelectFieldModel]
    joins: list[_JoinDefModel] = []
    where: _FilterGroupModel | None = None
    group_by: list[_ColumnRefModel] = []
    order_by: list[_SortDefModel] = []
    limit: int | None = 1000


class DatasetResponse(BaseModel):
    """Response body for dataset endpoints."""

    dataset_id: UUID
    name: str
    description: str
    connection_id: str
    created_at: datetime
    created_by: str
    spec: dict[str, Any]

    @classmethod
    def from_definition(cls, dataset: DatasetDefinition) -> DatasetResponse:
        return cls(
            dataset_id=dataset.dataset_id,
            name=dataset.name,
            description=dataset.description,
            connection_id=dataset.connection_id,
            created_at=dataset.created_at,
            created_by=dataset.created_by,
            spec=dataclasses.asdict(dataset.spec),
        )
