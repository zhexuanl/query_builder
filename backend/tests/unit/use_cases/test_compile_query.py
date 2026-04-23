"""Unit tests for CompileQueryUseCase orchestration."""
from unittest.mock import MagicMock, call

import pytest

from domain.entities.query_spec import QuerySpec
from domain.errors import CatalogMiss, PolicyViolation
from domain.interfaces.catalog_repository import CatalogView, ICatalogRepository
from domain.interfaces.query_compiler import CompiledQuery, IQueryCompiler
from domain.interfaces.query_policy import IQueryPolicy
from domain.value_objects.dialect import Dialect
from domain.value_objects.filters import Predicate
from domain.value_objects.query_parts import JoinDef, SelectField
from domain.value_objects.refs import ColumnRef
from use_cases.compile_query import CompileQueryUseCase


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _source(alias: str = "c", table: str = "customers") -> JoinDef:
    return JoinDef(type="inner", table=table, alias=alias, on=())


def _join(alias: str, table: str) -> JoinDef:
    return JoinDef(
        type="inner", table=table, alias=alias,
        on=(Predicate(left=ColumnRef("c", "id"), op="=", right=ColumnRef(alias, "c_id")),),
    )


def _field(label: str = "id") -> SelectField:
    return SelectField(kind="column", source=ColumnRef("c", "id"), label=label)


def _spec(**overrides) -> QuerySpec:
    defaults = dict(
        connection_id="conn-1",
        source=_source(),
        select=(_field(),),
        limit=100,
    )
    defaults.update(overrides)
    return QuerySpec(**defaults)


def _make_use_case(catalog_repo=None, policies=None, compiler=None):
    fake_catalog = MagicMock(spec=CatalogView)
    fake_compiled = CompiledQuery(sql="SELECT 1", params={}, dialect=Dialect.postgres)

    if catalog_repo is None:
        catalog_repo = MagicMock(spec=ICatalogRepository)
        catalog_repo.view_for.return_value = fake_catalog
    if policies is None:
        policies = []
    if compiler is None:
        compiler = MagicMock(spec=IQueryCompiler)
        compiler.compile.return_value = fake_compiled

    return CompileQueryUseCase(catalog_repo, policies, compiler), catalog_repo, compiler


# ---------------------------------------------------------------------------
# 6.2  Successful path
# ---------------------------------------------------------------------------

def test_successful_execute_returns_compiled_query():
    manager = MagicMock()
    manager.repo = MagicMock(spec=ICatalogRepository)
    manager.repo.view_for.return_value = MagicMock(spec=CatalogView)
    manager.policy = MagicMock(spec=IQueryPolicy)
    manager.compiler = MagicMock(spec=IQueryCompiler)
    manager.compiler.compile.return_value = CompiledQuery(
        sql="SELECT 1", params={}, dialect=Dialect.postgres
    )

    use_case = CompileQueryUseCase(
        manager.repo, [manager.policy], manager.compiler
    )
    result = use_case.execute(_spec(), Dialect.postgres)

    assert isinstance(result, CompiledQuery)
    # assert ordering: view_for → validate → compile
    call_names = [str(c) for c in manager.mock_calls]
    view_for_idx = next(i for i, n in enumerate(call_names) if "view_for" in n)
    validate_idx = next(i for i, n in enumerate(call_names) if "validate" in n)
    compile_idx = next(i for i, n in enumerate(call_names) if "compile" in n)
    assert view_for_idx < validate_idx < compile_idx


# ---------------------------------------------------------------------------
# 6.3  PolicyViolation propagates; compiler not called
# ---------------------------------------------------------------------------

def test_policy_violation_propagates_and_compiler_not_called():
    policy = MagicMock(spec=IQueryPolicy)
    policy.validate.side_effect = PolicyViolation("too many joins")
    use_case, _, compiler = _make_use_case(policies=[policy])

    with pytest.raises(PolicyViolation, match="too many joins"):
        use_case.execute(_spec(), Dialect.postgres)

    compiler.compile.assert_not_called()


# ---------------------------------------------------------------------------
# 6.4  CatalogMiss from repository propagates
# ---------------------------------------------------------------------------

def test_catalog_miss_propagates():
    repo = MagicMock(spec=ICatalogRepository)
    repo.view_for.side_effect = CatalogMiss("table not found")
    use_case = CompileQueryUseCase(repo, [], MagicMock(spec=IQueryCompiler))

    with pytest.raises(CatalogMiss):
        use_case.execute(_spec(), Dialect.postgres)


# ---------------------------------------------------------------------------
# 6.5  Table names derived correctly — single-table spec
# ---------------------------------------------------------------------------

def test_table_names_single_table():
    use_case, repo, _ = _make_use_case()
    spec = _spec()  # source table = "customers", no joins

    use_case.execute(spec, Dialect.postgres)

    repo.view_for.assert_called_once_with("conn-1", frozenset({"customers"}))


# ---------------------------------------------------------------------------
# 6.6  Table names derived correctly — spec with two joins
# ---------------------------------------------------------------------------

def test_table_names_with_joins():
    use_case, repo, _ = _make_use_case()
    spec = _spec(
        source=_source("c", "customers"),
        joins=(
            _join("o", "orders"),
            _join("p", "products"),
        ),
        select=(_field("id"), _field("order_id")),
    )

    use_case.execute(spec, Dialect.postgres)

    repo.view_for.assert_called_once_with(
        "conn-1", frozenset({"customers", "orders", "products"})
    )


# ---------------------------------------------------------------------------
# First failing policy short-circuits
# ---------------------------------------------------------------------------

def test_first_policy_short_circuits():
    p1 = MagicMock(spec=IQueryPolicy)
    p1.validate.side_effect = PolicyViolation("first")
    p2 = MagicMock(spec=IQueryPolicy)

    use_case, _, _ = _make_use_case(policies=[p1, p2])

    with pytest.raises(PolicyViolation, match="first"):
        use_case.execute(_spec(), Dialect.postgres)

    p2.validate.assert_not_called()
