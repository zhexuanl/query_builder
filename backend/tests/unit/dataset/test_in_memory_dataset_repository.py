"""Unit tests for InMemoryDatasetRepository."""
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from domain.entities.dataset_definition import DatasetDefinition
from domain.errors import DatasetNotFound
from infrastructure.dataset.in_memory_dataset_repository import InMemoryDatasetRepository
from tests.helpers import simple_spec


def _make_dataset(connection_id: str = "conn-1", name: str = "ds") -> DatasetDefinition:
    return DatasetDefinition(
        dataset_id=uuid4(),
        name=name,
        description="test dataset",
        connection_id=connection_id,
        spec=simple_spec(connection_id=connection_id),
        created_at=datetime.now(timezone.utc),
        created_by="test-user",
    )


def test_save_get_round_trip():
    repo = InMemoryDatasetRepository()
    ds = _make_dataset()
    repo.save(ds)
    assert repo.get(ds.dataset_id) == ds


def test_get_unknown_raises_dataset_not_found():
    repo = InMemoryDatasetRepository()
    with pytest.raises(DatasetNotFound):
        repo.get(uuid4())


def test_list_no_filter_returns_all():
    repo = InMemoryDatasetRepository()
    ds1, ds2 = _make_dataset(), _make_dataset()
    repo.save(ds1)
    repo.save(ds2)
    result = repo.list()
    assert {d.dataset_id for d in result} == {ds1.dataset_id, ds2.dataset_id}


def test_list_by_connection_id_returns_subset():
    repo = InMemoryDatasetRepository()
    ds_a = _make_dataset(connection_id="conn-a")
    ds_b = _make_dataset(connection_id="conn-b")
    repo.save(ds_a)
    repo.save(ds_b)
    result = repo.list(connection_id="conn-a")
    assert len(result) == 1
    assert result[0].dataset_id == ds_a.dataset_id


def test_delete_removes_dataset():
    repo = InMemoryDatasetRepository()
    ds = _make_dataset()
    repo.save(ds)
    repo.delete(ds.dataset_id)
    with pytest.raises(DatasetNotFound):
        repo.get(ds.dataset_id)


def test_delete_unknown_raises_dataset_not_found():
    repo = InMemoryDatasetRepository()
    with pytest.raises(DatasetNotFound):
        repo.delete(uuid4())


def test_save_same_id_twice_overwrites():
    repo = InMemoryDatasetRepository()
    ds = _make_dataset(name="original")
    repo.save(ds)
    updated = DatasetDefinition(
        dataset_id=ds.dataset_id,
        name="updated",
        description=ds.description,
        connection_id=ds.connection_id,
        spec=ds.spec,
        created_at=ds.created_at,
        created_by=ds.created_by,
    )
    repo.save(updated)
    assert repo.get(ds.dataset_id).name == "updated"
