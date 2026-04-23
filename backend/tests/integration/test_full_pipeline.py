"""Integration tests: full HTTP pipeline against a real Postgres database."""
import shutil

import pytest

pytestmark = pytest.mark.skipif(
    not shutil.which("docker"), reason="Docker not available"
)

_CONN = "test-conn"
_DIALECT = "postgres"


def _exec_body(**overrides) -> dict:
    base = {
        "connection_id": _CONN,
        "caller_id": "integration-test",
        "source": {"type": "inner", "table": "customers", "alias": "c", "on": []},
        "select": [
            {"kind": "column", "source": {"alias": "c", "name": "id"}, "label": "id"},
            {"kind": "column", "source": {"alias": "c", "name": "name"}, "label": "name"},
            {"kind": "column", "source": {"alias": "c", "name": "status"}, "label": "status"},
        ],
        "limit": 100,
        "dialect": _DIALECT,
    }
    base.update(overrides)
    return base


def test_single_table_returns_five_rows(http_client):
    resp = http_client.post("/queries/execute", json=_exec_body())
    assert resp.status_code == 200
    data = resp.json()
    assert data["row_count"] == 5
    assert set(data["columns"]) == {"id", "name", "status"}


def test_join_returns_joined_rows(http_client):
    body = _exec_body(
        source={"type": "inner", "table": "customers", "alias": "c", "on": []},
        select=[
            {"kind": "column", "source": {"alias": "c", "name": "name"}, "label": "name"},
            {"kind": "column", "source": {"alias": "o", "name": "amount"}, "label": "amount"},
        ],
        joins=[{
            "type": "inner",
            "table": "orders",
            "alias": "o",
            "on": [{"left": {"alias": "c", "name": "id"}, "op": "=",
                    "right": {"alias": "o", "name": "customer_id"}}],
        }],
    )
    resp = http_client.post("/queries/execute", json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert data["row_count"] == 5  # 5 orders, each joined to a customer
    assert "name" in data["columns"]
    assert "amount" in data["columns"]


def test_filter_reduces_result_set(http_client):
    body = _exec_body(
        where={
            "op": "and",
            "items": [
                {
                    "left": {"alias": "c", "name": "status"},
                    "op": "=",
                    "right": "active",
                }
            ],
        }
    )
    resp = http_client.post("/queries/execute", json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert data["row_count"] == 3  # Alice, Bob, Dave are active
    assert all(r["status"] == "active" for r in data["rows"])


def test_aggregate_group_by_returns_grouped_rows(http_client):
    body = _exec_body(
        source={"type": "inner", "table": "customers", "alias": "c", "on": []},
        select=[
            {"kind": "column", "source": {"alias": "c", "name": "status"}, "label": "status"},
            {"kind": "agg", "func": "count", "source": {"alias": "c", "name": "id"}, "label": "cnt"},
        ],
        group_by=[{"alias": "c", "name": "status"}],
    )
    resp = http_client.post("/queries/execute", json=body)
    assert resp.status_code == 200
    data = resp.json()
    assert data["row_count"] == 2  # "active" and "inactive"
    counts = {r["status"]: r["cnt"] for r in data["rows"]}
    assert counts["active"] == 3
    assert counts["inactive"] == 2


def test_audit_event_recorded_on_success(http_client, fake_audit_log):
    resp = http_client.post("/queries/execute", json=_exec_body())
    assert resp.status_code == 200
    assert len(fake_audit_log.events) == 1
    event = fake_audit_log.events[0]
    assert event.outcome == "success"
    assert event.row_count == 5
    assert event.caller_id == "integration-test"
