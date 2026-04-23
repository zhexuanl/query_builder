"""Integration tests: policy rejections and error-path HTTP responses (no DB required)."""
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from adapters.compilers.sqlalchemy_core_compiler import SqlAlchemyCoreCompiler
from adapters.policy.default_query_policy import DefaultQueryPolicy
from adapters.policy.table_allowlist_policy import TableAllowlistPolicy
from domain.errors import SourceConnectionError
from domain.interfaces.catalog_repository import CatalogView, ICatalogRepository
from domain.interfaces.query_executor import IQueryExecutor
from domain.interfaces.query_compiler import CompiledQuery
from infrastructure.api.routes.queries import make_queries_router
from infrastructure.connection.cipher_backed_connection_repository import CipherBackedConnectionRepository
from tests.fakes.fake_audit_log import FakeAuditLog
from tests.fakes.fake_credential_cipher import FakeCredentialCipher
from tests.fakes.in_memory_catalog import make_catalog
from use_cases.compile_query import CompileQueryUseCase
from use_cases.execute_query import ExecuteQueryUseCase


_KNOWN_CONN = "known-conn"
_ALLOWLIST = {_KNOWN_CONN: frozenset({"customers"})}


class _StubCatalogRepo(ICatalogRepository):
    """Always returns a one-table catalog — no real DB needed."""

    def view_for(self, connection_id: str, table_names: frozenset[str]) -> CatalogView:
        return make_catalog(*(("c", t, ["id", "name", "status"]) for t in table_names))

    def invalidate(self, connection_id: str) -> None:
        pass


def _make_client(executor: IQueryExecutor | None = None) -> tuple[TestClient, FakeAuditLog]:
    fake_log = FakeAuditLog()
    cipher = FakeCredentialCipher()
    conn_repo = CipherBackedConnectionRepository(cipher)
    conn_repo.register(_KNOWN_CONN, "postgresql://localhost/test")

    compile_uc = CompileQueryUseCase(
        catalog_repo=_StubCatalogRepo(),
        policies=[DefaultQueryPolicy(), TableAllowlistPolicy(_ALLOWLIST)],
        compiler=SqlAlchemyCoreCompiler(),
    )
    if executor is None:
        executor = MagicMock(spec=IQueryExecutor)
        executor.execute.return_value = [{"id": 1}]
    execute_uc = ExecuteQueryUseCase(compile_uc, conn_repo, executor, fake_log)

    app = FastAPI()
    app.include_router(make_queries_router(execute_uc))
    return TestClient(app), fake_log


_VALID_BODY = {
    "connection_id": _KNOWN_CONN,
    "caller_id": "test",
    "source": {"type": "inner", "table": "customers", "alias": "c", "on": []},
    "select": [{"kind": "column", "source": {"alias": "c", "name": "id"}, "label": "id"}],
    "limit": 100,
    "dialect": "postgres",
}


def test_unknown_connection_id_returns_422_policy_violation():
    client, _ = _make_client()
    body = {**_VALID_BODY, "connection_id": "nonexistent-conn"}
    resp = client.post("/queries/execute", json=body)
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "POLICY_VIOLATION"


def test_duplicate_alias_returns_422_policy_violation():
    client, _ = _make_client()
    body = {
        **_VALID_BODY,
        "joins": [{
            "type": "inner",
            "table": "customers",
            "alias": "c",  # same alias as source
            "on": [],
        }],
    }
    resp = client.post("/queries/execute", json=body)
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "POLICY_VIOLATION"


def test_limit_none_returns_422_policy_violation():
    client, _ = _make_client()
    body = {**_VALID_BODY, "limit": None}
    resp = client.post("/queries/execute", json=body)
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "POLICY_VIOLATION"


def test_source_connection_error_returns_502():
    failing_executor = MagicMock(spec=IQueryExecutor)
    failing_executor.execute.side_effect = SourceConnectionError("connection refused")
    client, _ = _make_client(executor=failing_executor)
    resp = client.post("/queries/execute", json=_VALID_BODY)
    assert resp.status_code == 502
    assert resp.json()["error_code"] == "SOURCE_UNAVAILABLE"
