"""Integration tests: dataset save/retrieve round-trip against a real Postgres database."""
import shutil

import pytest

pytestmark = pytest.mark.skipif(
    not shutil.which("docker"), reason="Docker not available"
)

_CONN = "test-conn"
_DIALECT = "postgres"

_SAVE_BODY = {
    "name": "Active customers",
    "description": "All active customers",
    "connection_id": _CONN,
    "created_by": "integration-test",
    "dialect": _DIALECT,
    "source": {"type": "inner", "table": "customers", "alias": "c", "on": []},
    "select": [
        {"kind": "column", "source": {"alias": "c", "name": "id"}, "label": "id"},
        {"kind": "column", "source": {"alias": "c", "name": "name"}, "label": "name"},
        {"kind": "column", "source": {"alias": "c", "name": "status"}, "label": "status"},
    ],
    "limit": 100,
}


def test_post_dataset_returns_201_with_dataset_id(http_client):
    resp = http_client.post("/datasets", json=_SAVE_BODY)
    assert resp.status_code == 201
    data = resp.json()
    assert "dataset_id" in data
    assert data["name"] == "Active customers"
    assert data["connection_id"] == _CONN


def test_get_dataset_returns_spec_fields(http_client):
    post_resp = http_client.post("/datasets", json=_SAVE_BODY)
    assert post_resp.status_code == 201
    dataset_id = post_resp.json()["dataset_id"]

    get_resp = http_client.get(f"/datasets/{dataset_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["dataset_id"] == dataset_id
    assert data["name"] == _SAVE_BODY["name"]
    assert data["connection_id"] == _SAVE_BODY["connection_id"]
    assert data["created_by"] == _SAVE_BODY["created_by"]


def test_execute_retrieved_spec_returns_same_rows(http_client):
    post_resp = http_client.post("/datasets", json=_SAVE_BODY)
    assert post_resp.status_code == 201
    dataset_id = post_resp.json()["dataset_id"]

    get_resp = http_client.get(f"/datasets/{dataset_id}")
    assert get_resp.status_code == 200
    retrieved_spec = get_resp.json()["spec"]

    # Execute directly from the retrieved spec dict — adds caller/dialect only
    exec_body = {**retrieved_spec, "caller_id": "integration-test", "dialect": _DIALECT}
    exec_resp = http_client.post("/queries/execute", json=exec_body)
    assert exec_resp.status_code == 200
    assert exec_resp.json()["row_count"] == 5  # all 5 seeded customers
