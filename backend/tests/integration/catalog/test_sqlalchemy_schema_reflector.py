"""Integration tests for SqlAlchemySchemaReflector against real databases.

Requires Docker. Postgres tests run by default but are skipped when Docker is
absent. MSSQL tests require MSSQL_TESTS=1 in the environment.

Run:
    pytest tests/integration/catalog/ -v
    MSSQL_TESTS=1 pytest tests/integration/catalog/ -v -m mssql
"""
import os
import shutil

import pytest
import sqlalchemy as sa

from adapters.catalog.sqlalchemy_schema_reflector import SqlAlchemySchemaReflector
from adapters.compilers.sqlalchemy_core_compiler import SqlAlchemyCoreCompiler
from domain.errors import SourceConnectionError
from domain.entities.query_spec import QuerySpec
from domain.value_objects.dialect import Dialect
from domain.value_objects.query_parts import JoinDef, SelectField
from domain.value_objects.refs import ColumnRef
from tests.helpers import normalize_sql


docker_available = shutil.which("docker") is not None
mssql_enabled = os.environ.get("MSSQL_TESTS") == "1"

pytestmark_docker = pytest.mark.skipif(
    not docker_available, reason="Docker not available"
)


# ---------------------------------------------------------------------------
# Postgres fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
@pytest.mark.skipif(not docker_available, reason="Docker not available")
def postgres_url():
    """Start a Postgres container and return its SQLAlchemy URL."""
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer("postgres:16-alpine") as pg:
        url = pg.get_connection_url()
        engine = sa.create_engine(url)
        with engine.begin() as conn:
            conn.execute(sa.text(
                "CREATE TABLE users (id SERIAL PRIMARY KEY, email TEXT NOT NULL)"
            ))
            conn.execute(sa.text(
                "CREATE TABLE orders (id SERIAL PRIMARY KEY, user_id INT, amount NUMERIC)"
            ))
        yield url


# ---------------------------------------------------------------------------
# 6.3  Postgres reflection tests
# ---------------------------------------------------------------------------

@pytestmark_docker
def test_reflect_postgres_single_table(postgres_url):
    reflector = SqlAlchemySchemaReflector()
    catalog = reflector.reflect(postgres_url, frozenset({"users"}))

    tbl = catalog.sa_table("users")
    assert tbl is not None

    col = catalog.column("users", "email")
    assert col is not None


@pytestmark_docker
def test_reflect_postgres_multiple_tables(postgres_url):
    reflector = SqlAlchemySchemaReflector()
    catalog = reflector.reflect(postgres_url, frozenset({"users", "orders"}))

    assert catalog.sa_table("users") is not None
    assert catalog.sa_table("orders") is not None
    assert catalog.column("orders", "amount") is not None


@pytestmark_docker
def test_reflect_postgres_missing_table_raises(postgres_url):
    reflector = SqlAlchemySchemaReflector()
    with pytest.raises(SourceConnectionError, match="not found"):
        reflector.reflect(postgres_url, frozenset({"nonexistent_table"}))


@pytestmark_docker
def test_reflect_postgres_catalog_miss_unknown_alias(postgres_url):
    from domain.errors import CatalogMiss
    reflector = SqlAlchemySchemaReflector()
    catalog = reflector.reflect(postgres_url, frozenset({"users"}))
    with pytest.raises(CatalogMiss):
        catalog.sa_table("unknown")


# ---------------------------------------------------------------------------
# 6.4  MSSQL reflection tests (skipped unless MSSQL_TESTS=1)
# ---------------------------------------------------------------------------

mssql_enabled = os.environ.get("MSSQL_TESTS") == "1"


@pytest.mark.mssql
@pytest.mark.skipif(not mssql_enabled, reason="Set MSSQL_TESTS=1 to run MSSQL tests")
def test_reflect_mssql_single_table():
    from testcontainers.mssql import SqlServerContainer

    with SqlServerContainer("mcr.microsoft.com/mssql/server:2022-latest") as mssql:
        url = mssql.get_connection_url()
        engine = sa.create_engine(url)
        with engine.begin() as conn:
            conn.execute(sa.text(
                "CREATE TABLE users (id INT PRIMARY KEY, email NVARCHAR(255))"
            ))

        reflector = SqlAlchemySchemaReflector()
        catalog = reflector.reflect(url, frozenset({"users"}))

        assert catalog.sa_table("users") is not None
        assert catalog.column("users", "email") is not None


# ---------------------------------------------------------------------------
# 6.5  End-to-end: reflect → compile → assert SQL (Postgres)
# ---------------------------------------------------------------------------

@pytestmark_docker
def test_e2e_reflect_and_compile_postgres(postgres_url):
    reflector = SqlAlchemySchemaReflector()
    catalog = reflector.reflect(postgres_url, frozenset({"users"}))

    spec = QuerySpec(
        connection_id="conn-1",
        source=JoinDef(type="inner", table="users", alias="users", on=()),
        select=(
            SelectField(
                kind="column",
                source=ColumnRef("users", "id"),
                label="id",
            ),
            SelectField(
                kind="column",
                source=ColumnRef("users", "email"),
                label="email",
            ),
        ),
        limit=10,
    )

    result = SqlAlchemyCoreCompiler().compile(spec, catalog, Dialect.postgres)
    sql = normalize_sql(result.sql)

    assert "SELECT" in sql
    assert "users.id AS id" in sql
    assert "users.email AS email" in sql
    assert "FROM users AS users" in sql
    assert "LIMIT" in sql
