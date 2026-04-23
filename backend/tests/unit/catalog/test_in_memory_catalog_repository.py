"""Unit tests for InMemoryCatalogRepository cache behaviour."""
from unittest.mock import MagicMock

import pytest

from domain.interfaces.catalog_repository import CatalogView
from domain.interfaces.schema_reflector import ISchemaReflector
from infrastructure.catalog.in_memory_catalog_repository import InMemoryCatalogRepository


def _make_repo(reflector=None) -> InMemoryCatalogRepository:
    if reflector is None:
        reflector = MagicMock(spec=ISchemaReflector)
        reflector.reflect.return_value = MagicMock(spec=CatalogView)
    return InMemoryCatalogRepository(
        reflector=reflector,
        url_for={"conn-1": "postgresql://localhost/testdb"},
    )


def test_cache_hit_calls_reflector_once():
    repo = _make_repo()
    tables = frozenset({"customers"})

    view1 = repo.view_for("conn-1", tables)
    view2 = repo.view_for("conn-1", tables)

    repo._reflector.reflect.assert_called_once()
    assert view1 is view2


def test_different_table_set_produces_separate_cache_entries():
    repo = _make_repo()

    repo.view_for("conn-1", frozenset({"a"}))
    repo.view_for("conn-1", frozenset({"a", "b"}))

    assert repo._reflector.reflect.call_count == 2


def test_invalidate_evicts_and_triggers_re_reflection():
    repo = _make_repo()
    tables = frozenset({"customers"})

    repo.view_for("conn-1", tables)
    repo.invalidate("conn-1")
    repo.view_for("conn-1", tables)

    assert repo._reflector.reflect.call_count == 2


def test_invalidate_only_removes_target_connection():
    repo = InMemoryCatalogRepository(
        reflector=MagicMock(spec=ISchemaReflector, **{"reflect.return_value": MagicMock(spec=CatalogView)}),
        url_for={
            "conn-1": "postgresql://localhost/db1",
            "conn-2": "postgresql://localhost/db2",
        },
    )
    tables = frozenset({"t"})

    repo.view_for("conn-1", tables)
    repo.view_for("conn-2", tables)
    repo.invalidate("conn-1")
    repo.view_for("conn-2", tables)  # should be a cache hit

    # conn-1 reflected once, conn-2 reflected once (cache not evicted)
    assert repo._reflector.reflect.call_count == 2
