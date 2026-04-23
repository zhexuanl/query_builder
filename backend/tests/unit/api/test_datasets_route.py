"""Unit tests for /datasets routes."""
from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from domain.entities.dataset_definition import DatasetDefinition
from domain.errors import CatalogMiss, DatasetNotFound, PolicyViolation
from domain.value_objects.dialect import Dialect
from infrastructure.api.routes.datasets import make_datasets_router
from infrastructure.dataset.in_memory_dataset_repository import InMemoryDatasetRepository
from use_cases.get_dataset import GetDatasetUseCase
from use_cases.save_dataset import SaveDatasetUseCase
from tests.helpers import simple_spec


_VALID_BODY = {
    "name": "test-dataset",
    "description": "a test dataset",
    "connection_id": "conn-1",
    "created_by": "user-1",
    "dialect": "postgres",
    "source": {"type": "inner", "table": "users", "alias": "u", "on": []},
    "select": [{"kind": "column", "source": {"alias": "u", "name": "id"}, "label": "id"}],
}


def _make_client(
    save_side_effect=None,
    get_side_effect=None,
    prefill: DatasetDefinition | None = None,
) -> tuple[TestClient, InMemoryDatasetRepository]:
    save_uc = MagicMock(spec=SaveDatasetUseCase)
    if save_side_effect is not None:
        save_uc.execute.side_effect = save_side_effect
    else:
        save_uc.execute.return_value = None

    repo = InMemoryDatasetRepository()
    if prefill is not None:
        repo.save(prefill)

    get_uc = GetDatasetUseCase(repo)
    app = FastAPI()
    app.include_router(make_datasets_router(save_uc, get_uc, repo))
    return TestClient(app), repo


def _stored_dataset(connection_id: str = "conn-1") -> DatasetDefinition:
    return DatasetDefinition(
        dataset_id=uuid4(),
        name="existing",
        description="pre-existing",
        connection_id=connection_id,
        spec=simple_spec(connection_id=connection_id),
        created_at=datetime.now(timezone.utc),
        created_by="user-1",
    )


# --- POST /datasets ---

def test_post_201_with_generated_dataset_id():
    client, _ = _make_client()
    resp = client.post("/datasets", json=_VALID_BODY)
    assert resp.status_code == 201
    data = resp.json()
    assert "dataset_id" in data
    assert data["name"] == "test-dataset"
    assert "created_at" in data


def test_post_422_on_policy_violation():
    client, _ = _make_client(save_side_effect=PolicyViolation("denied"))
    resp = client.post("/datasets", json=_VALID_BODY)
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "POLICY_VIOLATION"


def test_post_422_on_catalog_miss():
    client, _ = _make_client(save_side_effect=CatalogMiss("unknown table"))
    resp = client.post("/datasets", json=_VALID_BODY)
    assert resp.status_code == 422
    assert resp.json()["error_code"] == "CATALOG_MISS"


# --- GET /datasets/{dataset_id} ---

def test_get_200_with_full_spec():
    ds = _stored_dataset()
    client, _ = _make_client(prefill=ds)
    resp = client.get(f"/datasets/{ds.dataset_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["dataset_id"] == str(ds.dataset_id)
    assert "spec" in data
    assert data["spec"]["connection_id"] == ds.connection_id


def test_get_404_on_unknown_id():
    client, _ = _make_client()
    resp = client.get(f"/datasets/{uuid4()}")
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "DATASET_NOT_FOUND"


# --- GET /datasets ---

def test_list_200_all_datasets():
    ds1 = _stored_dataset(connection_id="conn-a")
    ds2 = _stored_dataset(connection_id="conn-b")
    client, repo = _make_client()
    repo.save(ds1)
    repo.save(ds2)
    resp = client.get("/datasets")
    assert resp.status_code == 200
    ids = {d["dataset_id"] for d in resp.json()}
    assert str(ds1.dataset_id) in ids
    assert str(ds2.dataset_id) in ids


def test_list_200_with_connection_id_filter():
    ds_a = _stored_dataset(connection_id="conn-a")
    ds_b = _stored_dataset(connection_id="conn-b")
    client, repo = _make_client()
    repo.save(ds_a)
    repo.save(ds_b)
    resp = client.get("/datasets?connection_id=conn-a")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["connection_id"] == "conn-a"


# --- DELETE /datasets/{dataset_id} ---

def test_delete_204_success():
    ds = _stored_dataset()
    client, repo = _make_client(prefill=ds)
    resp = client.delete(f"/datasets/{ds.dataset_id}")
    assert resp.status_code == 204
    with pytest.raises(Exception):
        repo.get(ds.dataset_id)


def test_delete_404_on_unknown_id():
    client, _ = _make_client()
    resp = client.delete(f"/datasets/{uuid4()}")
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "DATASET_NOT_FOUND"
