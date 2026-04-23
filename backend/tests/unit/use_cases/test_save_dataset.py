"""Unit tests for SaveDatasetUseCase."""
from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from domain.entities.dataset_definition import DatasetDefinition
from domain.errors import CatalogMiss, PolicyViolation
from domain.value_objects.dialect import Dialect
from use_cases.compile_query import CompileQueryUseCase
from use_cases.save_dataset import SaveDatasetUseCase
from tests.helpers import simple_spec
from infrastructure.dataset.in_memory_dataset_repository import InMemoryDatasetRepository


def _make_dataset() -> DatasetDefinition:
    return DatasetDefinition(
        dataset_id=uuid4(),
        name="test-ds",
        description="",
        connection_id="conn-1",
        spec=simple_spec(),
        created_at=datetime.now(timezone.utc),
        created_by="user-1",
    )


def _make_use_case(compile_side_effect=None):
    compile_uc = MagicMock(spec=CompileQueryUseCase)
    if compile_side_effect is not None:
        compile_uc.execute.side_effect = compile_side_effect
    repo = InMemoryDatasetRepository()
    return SaveDatasetUseCase(compile_uc, repo), compile_uc, repo


def test_valid_spec_saves_dataset():
    use_case, compile_uc, repo = _make_use_case()
    ds = _make_dataset()
    use_case.execute(ds, Dialect.postgres)
    compile_uc.execute.assert_called_once_with(ds.spec, Dialect.postgres)
    assert repo.get(ds.dataset_id) == ds


def test_policy_violation_prevents_save():
    use_case, compile_uc, repo = _make_use_case(compile_side_effect=PolicyViolation("denied"))
    ds = _make_dataset()
    with pytest.raises(PolicyViolation):
        use_case.execute(ds, Dialect.postgres)
    assert repo.list() == []


def test_catalog_miss_prevents_save():
    use_case, compile_uc, repo = _make_use_case(compile_side_effect=CatalogMiss("unknown"))
    ds = _make_dataset()
    with pytest.raises(CatalogMiss):
        use_case.execute(ds, Dialect.postgres)
    assert repo.list() == []
