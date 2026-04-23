"""Unit tests for POST /queries/execute."""
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from domain.errors import CatalogMiss, CompilationError, PolicyViolation, SourceConnectionError
from infrastructure.api.routes.queries import make_queries_router
from use_cases.execute_query import ExecuteQueryUseCase


_VALID_BODY = {
    "connection_id": "conn-1",
    "source": {"type": "inner", "table": "users", "alias": "u", "on": []},
    "select": [{"kind": "column", "source": {"alias": "u", "name": "id"}, "label": "id"}],
    "dialect": "postgres",
}


def _make_client(rows=None, side_effect=None) -> TestClient:
    uc = MagicMock(spec=ExecuteQueryUseCase)
    if side_effect is not None:
        uc.execute.side_effect = side_effect
    else:
        uc.execute.return_value = rows or []
    app = FastAPI()
    app.include_router(make_queries_router(uc))
    return TestClient(app)


def test_valid_request_returns_200_with_rows():
    rows = [{"id": 1}, {"id": 2}]
    client = _make_client(rows=rows)
    resp = client.post("/queries/execute", json=_VALID_BODY)
    assert resp.status_code == 200
    data = resp.json()
    assert data["rows"] == rows
    assert data["columns"] == ["id"]
    assert data["row_count"] == 2


def test_empty_result_returns_200_empty():
    client = _make_client(rows=[])
    resp = client.post("/queries/execute", json=_VALID_BODY)
    assert resp.status_code == 200
    data = resp.json()
    assert data["rows"] == []
    assert data["columns"] == []
    assert data["row_count"] == 0


def test_policy_violation_returns_422():
    client = _make_client(side_effect=PolicyViolation("too many joins"))
    resp = client.post("/queries/execute", json=_VALID_BODY)
    assert resp.status_code == 422
    assert "too many joins" in resp.json()["detail"]


def test_compilation_error_returns_422():
    client = _make_client(side_effect=CompilationError("bad spec"))
    resp = client.post("/queries/execute", json=_VALID_BODY)
    assert resp.status_code == 422
    assert "bad spec" in resp.json()["detail"]


def test_catalog_miss_returns_422():
    client = _make_client(side_effect=CatalogMiss("unknown table"))
    resp = client.post("/queries/execute", json=_VALID_BODY)
    assert resp.status_code == 422
    assert "unknown table" in resp.json()["detail"]


def test_source_connection_error_returns_502():
    client = _make_client(side_effect=SourceConnectionError("db unreachable"))
    resp = client.post("/queries/execute", json=_VALID_BODY)
    assert resp.status_code == 502
    assert resp.json()["detail"] == "Source database unavailable"


def test_missing_connection_id_returns_422():
    client = _make_client()
    body = {**_VALID_BODY}
    del body["connection_id"]
    resp = client.post("/queries/execute", json=body)
    assert resp.status_code == 422


def test_unknown_dialect_returns_422():
    client = _make_client()
    body = {**_VALID_BODY, "dialect": "oracle"}
    resp = client.post("/queries/execute", json=body)
    assert resp.status_code == 422
