"""Session-scoped Postgres testcontainer + TestClient factory for integration tests."""
import shutil

import pytest
import sqlalchemy as sa
from fastapi import FastAPI
from fastapi.testclient import TestClient

from adapters.catalog.sqlalchemy_schema_reflector import SqlAlchemySchemaReflector
from adapters.compilers.sqlalchemy_core_compiler import SqlAlchemyCoreCompiler
from adapters.executor.sqlalchemy_query_executor import SqlAlchemyQueryExecutor
from adapters.policy.default_query_policy import DefaultQueryPolicy
from adapters.policy.table_allowlist_policy import TableAllowlistPolicy
from infrastructure.catalog.in_memory_catalog_repository import InMemoryCatalogRepository
from infrastructure.connection.cipher_backed_connection_repository import CipherBackedConnectionRepository
from infrastructure.dataset.in_memory_dataset_repository import InMemoryDatasetRepository
from infrastructure.api.routes.datasets import make_datasets_router
from infrastructure.api.routes.queries import make_queries_router
from tests.fakes.fake_audit_log import FakeAuditLog
from tests.fakes.fake_credential_cipher import FakeCredentialCipher
from use_cases.compile_query import CompileQueryUseCase
from use_cases.execute_query import ExecuteQueryUseCase
from use_cases.get_dataset import GetDatasetUseCase
from use_cases.save_dataset import SaveDatasetUseCase

docker_available = shutil.which("docker") is not None


@pytest.fixture(scope="session")
def pg_url():
    if not docker_available:
        pytest.skip("Docker not available")
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:16-alpine") as pg:
        url = pg.get_connection_url()
        engine = sa.create_engine(url)
        with engine.begin() as conn:
            conn.execute(sa.text("""
                CREATE TABLE customers (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL
                )
            """))
            conn.execute(sa.text("""
                CREATE TABLE orders (
                    id SERIAL PRIMARY KEY,
                    customer_id INTEGER NOT NULL,
                    amount NUMERIC NOT NULL
                )
            """))
            conn.execute(sa.text("""
                INSERT INTO customers (name, status) VALUES
                  ('Alice', 'active'),
                  ('Bob', 'active'),
                  ('Carol', 'inactive'),
                  ('Dave', 'active'),
                  ('Eve', 'inactive')
            """))
            conn.execute(sa.text("""
                INSERT INTO orders (customer_id, amount) VALUES
                  (1, 100), (1, 200), (2, 150), (3, 50), (4, 300)
            """))
        engine.dispose()
        yield url


@pytest.fixture()
def fake_audit_log() -> FakeAuditLog:
    return FakeAuditLog()


@pytest.fixture()
def http_client(pg_url, fake_audit_log) -> TestClient:
    """Full-stack TestClient wired to the Postgres container."""
    conn_id = "test-conn"
    allowlist = {"test-conn": frozenset({"customers", "orders"})}

    cipher = FakeCredentialCipher()
    conn_repo = CipherBackedConnectionRepository(cipher)
    conn_repo.register(conn_id, pg_url)

    reflector = SqlAlchemySchemaReflector()
    catalog_repo = InMemoryCatalogRepository(reflector=reflector, url_for={conn_id: pg_url})

    compile_uc = CompileQueryUseCase(
        catalog_repo=catalog_repo,
        policies=[DefaultQueryPolicy(), TableAllowlistPolicy(allowlist)],
        compiler=SqlAlchemyCoreCompiler(),
    )
    execute_uc = ExecuteQueryUseCase(compile_uc, conn_repo, SqlAlchemyQueryExecutor(), fake_audit_log)

    dataset_repo = InMemoryDatasetRepository()
    save_uc = SaveDatasetUseCase(compile_uc, dataset_repo)
    get_uc = GetDatasetUseCase(dataset_repo)

    app = FastAPI(title="Test App")
    app.include_router(make_queries_router(execute_uc))
    app.include_router(make_datasets_router(save_uc, get_uc, dataset_repo))
    return TestClient(app)
