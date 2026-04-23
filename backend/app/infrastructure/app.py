import os

from fastapi import FastAPI

from adapters.audit.json_stdout_audit_log import JsonStdoutAuditLog
from adapters.catalog.sqlalchemy_schema_reflector import SqlAlchemySchemaReflector
from adapters.cipher.fernet_credential_cipher import FernetCredentialCipher
from adapters.compilers.sqlalchemy_core_compiler import SqlAlchemyCoreCompiler
from adapters.executor.sqlalchemy_query_executor import SqlAlchemyQueryExecutor
from adapters.policy.default_query_policy import DefaultQueryPolicy
from infrastructure.catalog.in_memory_catalog_repository import InMemoryCatalogRepository
from infrastructure.connection.cipher_backed_connection_repository import CipherBackedConnectionRepository
from infrastructure.api.routes.queries import make_queries_router
from infrastructure.api.routes.datasets import make_datasets_router
from infrastructure.dataset.in_memory_dataset_repository import InMemoryDatasetRepository
from use_cases.compile_query import CompileQueryUseCase
from use_cases.execute_query import ExecuteQueryUseCase
from use_cases.get_dataset import GetDatasetUseCase
from use_cases.save_dataset import SaveDatasetUseCase


def create_app(config: dict) -> FastAPI:
    """Construct a fully-wired FastAPI application.

    Args:
        config: Optional configuration dict. Recognised keys:
            ``connections`` — ``dict[str, str]`` mapping connection_id to URL.
            ``fernet_key`` — base64-url-encoded 32-byte Fernet key (falls back
            to the ``FERNET_KEY`` environment variable).

    Returns:
        A ``FastAPI`` instance with all routes registered.
    """
    connections: dict[str, str] = config.get("connections", {})
    raw_key: str | None = config.get("fernet_key") or os.environ.get("FERNET_KEY")
    if raw_key is None:
        raise ValueError("FERNET_KEY must be set (config key or environment variable)")

    cipher = FernetCredentialCipher(raw_key.encode())
    conn_repo = CipherBackedConnectionRepository(cipher)
    for conn_id, url in connections.items():
        conn_repo.register(conn_id, url)

    reflector = SqlAlchemySchemaReflector()
    catalog_repo = InMemoryCatalogRepository(reflector=reflector, url_for=connections)
    compile_uc = CompileQueryUseCase(
        catalog_repo=catalog_repo,
        policies=[DefaultQueryPolicy()],
        compiler=SqlAlchemyCoreCompiler(),
    )
    executor = SqlAlchemyQueryExecutor()
    audit_log = JsonStdoutAuditLog()
    execute_uc = ExecuteQueryUseCase(compile_uc, conn_repo, executor, audit_log)

    dataset_repo = InMemoryDatasetRepository()
    save_dataset_uc = SaveDatasetUseCase(compile_uc, dataset_repo)
    get_dataset_uc = GetDatasetUseCase(dataset_repo)

    app = FastAPI(title="Query Builder API")
    app.include_router(make_queries_router(execute_uc))
    app.include_router(make_datasets_router(save_dataset_uc, get_dataset_uc, dataset_repo))
    return app
