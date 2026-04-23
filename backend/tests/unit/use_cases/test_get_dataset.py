"""Unit tests for GetDatasetUseCase."""
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from domain.entities.dataset_definition import DatasetDefinition
from domain.errors import DatasetNotFound
from infrastructure.dataset.in_memory_dataset_repository import InMemoryDatasetRepository
from use_cases.get_dataset import GetDatasetUseCase
from tests.helpers import simple_spec


def _make_dataset() -> DatasetDefinition:
    return DatasetDefinition(
        dataset_id=uuid4(),
        name="ds",
        description="",
        connection_id="conn-1",
        spec=simple_spec(),
        created_at=datetime.now(timezone.utc),
        created_by="user-1",
    )


def test_known_id_returns_dataset():
    repo = InMemoryDatasetRepository()
    ds = _make_dataset()
    repo.save(ds)
    use_case = GetDatasetUseCase(repo)
    assert use_case.execute(ds.dataset_id) == ds


def test_unknown_id_raises_dataset_not_found():
    repo = InMemoryDatasetRepository()
    use_case = GetDatasetUseCase(repo)
    with pytest.raises(DatasetNotFound):
        use_case.execute(uuid4())
