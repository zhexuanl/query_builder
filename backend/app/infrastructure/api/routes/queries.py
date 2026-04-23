from fastapi import APIRouter
from fastapi.responses import JSONResponse

from domain.errors import CatalogMiss, CompilationError, PolicyViolation, SourceConnectionError
from domain.value_objects.dialect import Dialect
from infrastructure.api.models.query_models import ErrorResponse, QueryResultResponse, QuerySpecRequest
from infrastructure.api.routes._spec_mapper import to_domain_spec
from use_cases.execute_query import ExecuteQueryUseCase


def make_queries_router(execute_use_case: ExecuteQueryUseCase) -> APIRouter:
    """Build and return a queries router wired to ``execute_use_case``."""
    router = APIRouter(prefix="/queries")

    @router.post("/execute", response_model=QueryResultResponse)
    async def execute_query(req: QuerySpecRequest):
        try:
            spec = to_domain_spec(req)
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
