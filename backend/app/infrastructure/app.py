from fastapi import FastAPI

from adapters.catalog.sqlalchemy_schema_reflector import SqlAlchemySchemaReflector
from adapters.compilers.sqlalchemy_core_compiler import SqlAlchemyCoreCompiler
from adapters.executor.sqlalchemy_query_executor import SqlAlchemyQueryExecutor
from adapters.policy.default_query_policy import DefaultQueryPolicy
from infrastructure.catalog.in_memory_catalog_repository import InMemoryCatalogRepository
from infrastructure.connection.in_memory_connection_repository import InMemoryConnectionRepository
from infrastructure.api.routes.queries import make_queries_router
from use_cases.compile_query import CompileQueryUseCase
from use_cases.execute_query import ExecuteQueryUseCase


def create_app(config: dict) -> FastAPI:
    """Construct a fully-wired FastAPI application.

    Args:
        config: Optional configuration dict. Recognised keys:
            ``connections`` — ``dict[str, str]`` mapping connection_id to URL.

    Returns:
        A ``FastAPI`` instance with ``POST /queries/execute`` registered.
    """
    connections: dict[str, str] = config.get("connections", {})

    reflector = SqlAlchemySchemaReflector()
    catalog_repo = InMemoryCatalogRepository(reflector=reflector, url_for=connections)
    compile_uc = CompileQueryUseCase(
        catalog_repo=catalog_repo,
        policies=[DefaultQueryPolicy()],
        compiler=SqlAlchemyCoreCompiler(),
    )
    conn_repo = InMemoryConnectionRepository(connections)
    executor = SqlAlchemyQueryExecutor()
    execute_uc = ExecuteQueryUseCase(compile_uc, conn_repo, executor)

    app = FastAPI(title="Query Builder API")
    app.include_router(make_queries_router(execute_uc))
    return app
