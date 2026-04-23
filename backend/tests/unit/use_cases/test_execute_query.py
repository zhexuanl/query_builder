"""Unit tests for ExecuteQueryUseCase."""
from unittest.mock import MagicMock

import pytest

from domain.entities.query_spec import QuerySpec
from domain.errors import (
    CatalogMiss,
    CompilationError,
    PolicyViolation,
    SourceConnectionError,
)
from domain.interfaces.connection_repository import IConnectionRepository
from domain.interfaces.query_compiler import CompiledQuery
from domain.value_objects.dialect import Dialect
from domain.value_objects.query_parts import JoinDef, SelectField
from domain.value_objects.refs import ColumnRef
from tests.fakes.fake_query_executor import FakeQueryExecutor
from use_cases.compile_query import CompileQueryUseCase
from use_cases.execute_query import ExecuteQueryUseCase, _MAX_RESULT_ROWS


def _spec() -> QuerySpec:
    return QuerySpec(
        connection_id="conn-1",
        source=JoinDef(type="inner", table="users", alias="u", on=()),
        select=(SelectField(kind="column", source=ColumnRef("u", "id"), label="id"),),
        limit=100,
    )


def _compiled() -> CompiledQuery:
    return CompiledQuery(sql="SELECT u.id AS id FROM users AS u LIMIT 100", params={}, dialect=Dialect.postgres)


def _make_use_case(rows=None, compile_side_effect=None, url="postgresql://localhost/db"):
    compile_uc = MagicMock(spec=CompileQueryUseCase)
    if compile_side_effect is not None:
        compile_uc.execute.side_effect = compile_side_effect
    else:
        compile_uc.execute.return_value = _compiled()

    conn_repo = MagicMock(spec=IConnectionRepository)
    conn_repo.get_url.return_value = url

    executor = FakeQueryExecutor(rows or [])
    return ExecuteQueryUseCase(compile_uc, conn_repo, executor), compile_uc, conn_repo, executor


def test_successful_execute_returns_rows():
    rows = [{"id": 1}, {"id": 2}]
    uc, _, _, _ = _make_use_case(rows=rows)
    result = uc.execute(_spec(), Dialect.postgres)
    assert result == rows


def test_policy_violation_from_compile_propagates_executor_not_called():
    uc, compile_uc, _, executor = _make_use_case(
        compile_side_effect=PolicyViolation("too many joins")
    )
    with pytest.raises(PolicyViolation, match="too many joins"):
        uc.execute(_spec(), Dialect.postgres)
    assert executor.calls == []


def test_compilation_error_propagates_executor_not_called():
    uc, _, _, executor = _make_use_case(
        compile_side_effect=CompilationError("bad spec")
    )
    with pytest.raises(CompilationError):
        uc.execute(_spec(), Dialect.postgres)
    assert executor.calls == []


def test_catalog_miss_from_compile_propagates_executor_not_called():
    uc, _, _, executor = _make_use_case(
        compile_side_effect=CatalogMiss("unknown table")
    )
    with pytest.raises(CatalogMiss):
        uc.execute(_spec(), Dialect.postgres)
    assert executor.calls == []


def test_catalog_miss_from_connection_repo_propagates():
    compile_uc = MagicMock(spec=CompileQueryUseCase)
    compile_uc.execute.return_value = _compiled()
    conn_repo = MagicMock(spec=IConnectionRepository)
    conn_repo.get_url.side_effect = CatalogMiss("unknown connection")
    executor = FakeQueryExecutor([])
    uc = ExecuteQueryUseCase(compile_uc, conn_repo, executor)

    with pytest.raises(CatalogMiss, match="unknown connection"):
        uc.execute(_spec(), Dialect.postgres)
    assert executor.calls == []


def test_source_connection_error_from_executor_propagates():
    from domain.interfaces.query_executor import IQueryExecutor

    compile_uc = MagicMock(spec=CompileQueryUseCase)
    compile_uc.execute.return_value = _compiled()
    conn_repo = MagicMock(spec=IConnectionRepository)
    conn_repo.get_url.return_value = "postgresql://localhost/db"
    executor = MagicMock(spec=IQueryExecutor)
    executor.execute.side_effect = SourceConnectionError("db unreachable")
    uc = ExecuteQueryUseCase(compile_uc, conn_repo, executor)

    with pytest.raises(SourceConnectionError, match="db unreachable"):
        uc.execute(_spec(), Dialect.postgres)


def test_row_count_exceeds_cap_raises_policy_violation():
    rows = [{"id": i} for i in range(_MAX_RESULT_ROWS + 1)]
    uc, _, _, _ = _make_use_case(rows=rows)
    with pytest.raises(PolicyViolation, match=str(_MAX_RESULT_ROWS)):
        uc.execute(_spec(), Dialect.postgres)


def test_row_count_at_cap_returns_rows():
    rows = [{"id": i} for i in range(_MAX_RESULT_ROWS)]
    uc, _, _, _ = _make_use_case(rows=rows)
    result = uc.execute(_spec(), Dialect.postgres)
    assert len(result) == _MAX_RESULT_ROWS
