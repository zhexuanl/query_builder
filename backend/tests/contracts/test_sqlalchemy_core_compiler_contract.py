"""Smoke-check: SqlAlchemyCoreCompiler satisfies QueryCompilerContract."""
import pytest

from adapters.compilers.sqlalchemy_core_compiler import SqlAlchemyCoreCompiler
from domain.entities.query_spec import QuerySpec
from domain.value_objects.query_parts import JoinDef, SelectField
from domain.value_objects.refs import ColumnRef
from tests.contracts.query_compiler_contract import QueryCompilerContract
from tests.fakes.in_memory_catalog import make_catalog


class TestSqlAlchemyCoreCompilerContract(QueryCompilerContract):
    @pytest.fixture
    def compiler(self):
        return SqlAlchemyCoreCompiler()

    @pytest.fixture
    def catalog(self):
        return make_catalog(("c", "customers", ["id", "name"]))

    @pytest.fixture
    def valid_spec(self):
        return QuerySpec(
            connection_id="conn-1",
            source=JoinDef(type="inner", table="customers", alias="c", on=()),
            select=(SelectField(kind="column", source=ColumnRef("c", "id"), label="id"),),
            limit=10,
        )

    @pytest.fixture
    def unknown_alias_spec(self):
        return QuerySpec(
            connection_id="conn-1",
            source=JoinDef(type="inner", table="customers", alias="c", on=()),
            select=(SelectField(kind="column", source=ColumnRef("x", "id"), label="id"),),
            limit=10,
        )
