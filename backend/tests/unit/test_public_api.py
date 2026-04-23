"""Verify the query_builder public API surface."""
import query_builder


_EXPECTED_SYMBOLS = [
    # Tier 1: DSL types
    "QuerySpec", "Dialect", "FilterGroup", "Predicate",
    "JoinDef", "SelectField", "SortDef",
    "ColumnRef", "ParamRef", "ValueRef", "QuerySpecCodec",
    # Tier 2: Errors
    "QueryBuilderError", "PolicyViolation", "CompilationError",
    "CatalogMiss", "SourceConnectionError", "DatasetNotFound",
    # Tier 3: Ports
    "IAuditLog", "CatalogView", "ICatalogRepository",
    "IConnectionRepository", "ICredentialCipher", "IDatasetRepository",
    "CompiledQuery", "IQueryCompiler", "IQueryExecutor", "IQueryPolicy",
    # Tier 4: Reference implementations
    "SqlAlchemySchemaReflector", "FernetCredentialCipher",
    "SqlAlchemyCoreCompiler", "SqlAlchemyQueryExecutor",
    "DefaultQueryPolicy", "TableAllowlistPolicy",
    "InMemoryCatalogRepository", "CipherBackedConnectionRepository",
    "InMemoryConnectionRepository", "InMemoryDatasetRepository",
    "CompileQueryUseCase", "ExecuteQueryUseCase",
    "GetDatasetUseCase", "SaveDatasetUseCase",
]


def test_all_public_symbols_importable():
    for name in _EXPECTED_SYMBOLS:
        assert hasattr(query_builder, name), f"query_builder.{name} not found"


def test_all_symbols_in_dunder_all():
    for name in _EXPECTED_SYMBOLS:
        assert name in query_builder.__all__, f"{name!r} missing from __all__"


def test_create_app_not_in_all():
    assert "create_app" not in query_builder.__all__
