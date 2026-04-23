"""Contract test base class for IQueryCompiler implementations.

To test a custom IQueryCompiler, subclass ``QueryCompilerContract`` and
override the ``compiler``, ``catalog``, ``valid_spec``, and
``unknown_alias_spec`` fixtures.
"""
import pytest

from domain.errors import CompilationError
from domain.interfaces.query_compiler import CompiledQuery, IQueryCompiler
from domain.value_objects.dialect import Dialect


class QueryCompilerContract:
    """Abstract contract test suite for IQueryCompiler.

    Subclasses must override the ``compiler``, ``catalog``, ``valid_spec``,
    and ``unknown_alias_spec`` fixtures.
    """

    @pytest.fixture
    def compiler(self) -> IQueryCompiler:
        raise NotImplementedError("Subclass must provide an IQueryCompiler instance")

    @pytest.fixture
    def catalog(self):
        raise NotImplementedError("Subclass must provide a CatalogView")

    @pytest.fixture
    def valid_spec(self):
        raise NotImplementedError("Subclass must provide a compilable QuerySpec")

    @pytest.fixture
    def unknown_alias_spec(self):
        raise NotImplementedError("Subclass must provide a spec referencing an unknown alias")

    def test_returns_compiled_query(self, compiler, catalog, valid_spec):
        result = compiler.compile(valid_spec, catalog, Dialect.postgres)
        assert isinstance(result, CompiledQuery)
        assert isinstance(result.sql, str)
        assert len(result.sql) > 0

    def test_unknown_alias_raises_compilation_error(self, compiler, catalog, unknown_alias_spec):
        with pytest.raises(CompilationError):
            compiler.compile(unknown_alias_spec, catalog, Dialect.postgres)
