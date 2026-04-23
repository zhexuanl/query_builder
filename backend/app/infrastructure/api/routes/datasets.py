from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from domain.entities.dataset_definition import DatasetDefinition
from domain.errors import CatalogMiss, CompilationError, DatasetNotFound, PolicyViolation
from domain.interfaces.dataset_repository import IDatasetRepository
from domain.value_objects.dialect import Dialect
from infrastructure.api.models.dataset_models import DatasetResponse, SaveDatasetRequest
from infrastructure.api.models.query_models import ErrorResponse
from infrastructure.api.routes._spec_mapper import to_domain_spec
from use_cases.get_dataset import GetDatasetUseCase
from use_cases.save_dataset import SaveDatasetUseCase


def make_datasets_router(
    save_use_case: SaveDatasetUseCase,
    get_use_case: GetDatasetUseCase,
    dataset_repo: IDatasetRepository,
) -> APIRouter:
    """Build and return a datasets router wired to the provided use cases."""
    router = APIRouter(prefix="/datasets")

    @router.post("", status_code=201, response_model=DatasetResponse)
    async def save_dataset(req: SaveDatasetRequest):
        try:
            spec = to_domain_spec(req)
            dataset = DatasetDefinition(
                dataset_id=uuid4(),
                name=req.name,
                description=req.description,
                connection_id=req.connection_id,
                spec=spec,
                created_at=datetime.now(timezone.utc),
                created_by=req.created_by,
            )
            save_use_case.execute(dataset, Dialect(req.dialect))
            return DatasetResponse.from_definition(dataset)
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

    @router.get("/{dataset_id}", response_model=DatasetResponse)
    async def get_dataset(dataset_id: UUID):
        try:
            dataset = get_use_case.execute(dataset_id)
            return DatasetResponse.from_definition(dataset)
        except DatasetNotFound as exc:
            return JSONResponse(
                status_code=404,
                content=ErrorResponse(error_code="DATASET_NOT_FOUND", detail=str(exc)).model_dump(),
            )

    @router.get("", response_model=list[DatasetResponse])
    async def list_datasets(connection_id: str | None = None):
        datasets = dataset_repo.list(connection_id=connection_id)
        return [DatasetResponse.from_definition(d) for d in datasets]

    @router.delete("/{dataset_id}", status_code=204)
    async def delete_dataset(dataset_id: UUID):
        try:
            dataset_repo.delete(dataset_id)
        except DatasetNotFound as exc:
            return JSONResponse(
                status_code=404,
                content=ErrorResponse(error_code="DATASET_NOT_FOUND", detail=str(exc)).model_dump(),
            )

    return router
