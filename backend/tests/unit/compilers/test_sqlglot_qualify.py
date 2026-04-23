"""Tests for the optional SQLGlot qualify pass in SqlAlchemyCoreCompiler."""
import pytest

from adapters.compilers.sqlalchemy_core_compiler import SqlAlchemyCoreCompiler
from domain.errors import CompilationError
from domain.value_objects.dialect import Dialect
from tests.fakes.in_memory_catalog import make_catalog
from tests.helpers import simple_spec


def test_flag_disabled_by_default_compiles_normally():
    compiler = SqlAlchemyCoreCompiler()
    catalog = make_catalog(("u", "users", ["id", "name"]))
    spec = simple_spec(connection_id="conn-1", alias="u", table="users", columns=["id"])
    result = compiler.compile(spec, catalog, Dialect.postgres)
    assert "users" in result.sql


def test_flag_enabled_valid_sql_no_error():
    compiler = SqlAlchemyCoreCompiler(enable_sqlglot_qualify=True)
    catalog = make_catalog(("u", "users", ["id", "name"]))
    spec = simple_spec(connection_id="conn-1", alias="u", table="users", columns=["id"])
    result = compiler.compile(spec, catalog, Dialect.postgres)
    assert result.sql


def test_flag_enabled_invalid_sql_raises_compilation_error(monkeypatch):
    from adapters.compilers import sqlalchemy_core_compiler as mod
    from domain.interfaces.query_compiler import CompiledQuery

    compiler = SqlAlchemyCoreCompiler(enable_sqlglot_qualify=True)
    catalog = make_catalog(("u", "users", ["id"]))
    spec = simple_spec(connection_id="conn-1", alias="u", table="users", columns=["id"])

    monkeypatch.setattr(
        compiler,
        "_compile",
        lambda *_: CompiledQuery(
            sql="SELECT id FROM WHERE",
            params={},
            dialect=Dialect.postgres,
        ),
    )

    with pytest.raises(CompilationError, match="SQLGlot qualification failed"):
        compiler.compile(spec, catalog, Dialect.postgres)
