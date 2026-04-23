"""Integration tests for ExecuteQueryUseCase against a real Postgres database.

Requires Docker. Skipped automatically when Docker is unavailable.
"""
import shutil

import pytest
import sqlalchemy as sa

from adapters.catalog.sqlalchemy_schema_reflector import SqlAlchemySchemaReflector
from adapters.compilers.sqlalchemy_core_compiler import SqlAlchemyCoreCompiler
from adapters.executor.sqlalchemy_query_executor import SqlAlchemyQueryExecutor
from adapters.policy.default_query_policy import DefaultQueryPolicy
from adapters.policy.table_allowlist_policy import TableAllowlistPolicy
from domain.entities.query_spec import QuerySpec
from domain.value_objects.dialect import Dialect
from domain.value_objects.query_parts import JoinDef, SelectField
from domain.value_objects.refs import ColumnRef
from infrastructure.catalog.in_memory_catalog_repository import InMemoryCatalogRepository
from infrastructure.connection.cipher_backed_connection_repository import CipherBackedConnectionRepository
from tests.fakes.fake_audit_log import FakeAuditLog
from tests.fakes.fake_credential_cipher import FakeCredentialCipher
from use_cases.compile_query import CompileQueryUseCase
from use_cases.execute_query import ExecuteQueryUseCase

docker_available = shutil.which("docker") is not None

pytestmark = pytest.mark.skipif(not docker_available, reason="Docker not available")


@pytest.fixture(scope="module")
def pg_url_with_data():
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:16-alpine") as pg:
        url = pg.get_connection_url()
        engine = sa.create_engine(url)
        with engine.begin() as conn:
            conn.execute(sa.text(
                "CREATE TABLE users (id SERIAL PRIMARY KEY, email TEXT NOT NULL)"
            ))
            conn.execute(sa.text(
                "INSERT INTO users (email) VALUES ('alice@example.com'), ('bob@example.com')"
            ))
        engine.dispose()
        yield url


@pytest.fixture
def execute_use_case(pg_url_with_data):
    url = pg_url_with_data
    conn_map = {"test-conn": url}

    cipher = FakeCredentialCipher()
    conn_repo = CipherBackedConnectionRepository(cipher)
    conn_repo.register("test-conn", url)

    reflector = SqlAlchemySchemaReflector()
    catalog_repo = InMemoryCatalogRepository(reflector=reflector, url_for=conn_map)
    compile_uc = CompileQueryUseCase(
        catalog_repo=catalog_repo,
        policies=[
            DefaultQueryPolicy(),
            TableAllowlistPolicy({"test-conn": frozenset({"users"})}),
        ],
        compiler=SqlAlchemyCoreCompiler(),
    )
    executor = SqlAlchemyQueryExecutor()
    audit_log = FakeAuditLog()
    return ExecuteQueryUseCase(compile_uc, conn_repo, executor, audit_log), audit_log


def test_execute_returns_rows(execute_use_case):
    uc, audit_log = execute_use_case
    spec = QuerySpec(
        connection_id="test-conn",
        source=JoinDef(type="inner", table="users", alias="users", on=()),
        select=(
            SelectField(kind="column", source=ColumnRef("users", "id"), label="id"),
            SelectField(kind="column", source=ColumnRef("users", "email"), label="email"),
        ),
        limit=10,
    )
    rows = uc.execute(spec, Dialect.postgres, caller_id="integration-test")
    assert len(rows) == 2
    assert all("id" in r and "email" in r for r in rows)
    emails = {r["email"] for r in rows}
    assert emails == {"alice@example.com", "bob@example.com"}

    assert len(audit_log.events) == 1
    assert audit_log.events[0].outcome == "success"
    assert audit_log.events[0].caller_id == "integration-test"
    assert audit_log.events[0].row_count == 2
