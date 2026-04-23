## 1. Domain port

- [x] 1.1 Create `domain/interfaces/schema_reflector.py` — define `ISchemaReflector` ABC with `reflect(url: str, table_names: frozenset[str]) -> CatalogView`; Google-style docstring

Done signal: `from domain.interfaces.schema_reflector import ISchemaReflector` imports cleanly with no framework dependencies.

## 2. SQLAlchemy adapter — reflector

- [x] 2.1 Create `adapters/catalog/__init__.py` (empty)
- [x] 2.2 Create `adapters/catalog/sqlalchemy_schema_reflector.py` — implement `SqlAlchemySchemaReflector(ISchemaReflector)`; use `sa.create_engine(url)` + `sa.inspect(engine)` to reflect each requested table into a `sa.Table` with a shared `MetaData`; raise `SourceConnectionError` if a table is absent from the reflected metadata
- [x] 2.3 Implement `reflect()` — call `meta.reflect(bind=engine, only=list(table_names))`; wrap the resulting `Table` objects into a `SqlAlchemyCatalogView` and return it

Done signal: `SqlAlchemySchemaReflector().reflect(url, frozenset({"t"}))` returns a `CatalogView` for a live Postgres URL.

## 3. SQLAlchemy adapter — catalog view

- [x] 3.1 Create `adapters/catalog/sqlalchemy_catalog_view.py` — implement `SqlAlchemyCatalogView(CatalogView)`; constructor accepts `dict[str, sa.Table]` (table_name → Table); `sa_table(alias)` aliases the table and returns it; `column(alias, name)` raises `CatalogMiss` if absent
- [x] 3.2 Confirm `SqlAlchemyCoreCompiler.compile(spec, SqlAlchemyCatalogView(...), dialect)` produces correct SQL using a hand-constructed `SqlAlchemyCatalogView` (no live DB needed for this check)

Done signal: A manually constructed `SqlAlchemyCatalogView` satisfies the `CatalogView` interface and compiles a single-table spec without errors.

## 4. Infrastructure — caching catalog repository

- [x] 4.1 Create `infrastructure/__init__.py` and `infrastructure/catalog/__init__.py` (both empty)
- [x] 4.2 Create `infrastructure/catalog/in_memory_catalog_repository.py` — implement `InMemoryCatalogRepository(ICatalogRepository)`; internal cache: `dict[tuple[str, frozenset[str]], CatalogView]`; `view_for(connection_id, table_names)` checks cache before delegating to injected `ISchemaReflector`; `invalidate(connection_id)` removes all entries for that connection

Done signal: Unit test confirms reflector is called once on cache miss and zero times on cache hit.

## 5. Unit tests — repository cache behaviour

- [x] 5.1 Create `tests/unit/catalog/__init__.py` and `tests/unit/catalog/test_in_memory_catalog_repository.py`
- [x] 5.2 Test cache hit: call `view_for` twice with same args; assert reflector mock called once and same object returned
- [x] 5.3 Test cache miss on different table set: call `view_for` with `{"a"}` then `{"a", "b"}`; assert reflector called twice
- [x] 5.4 Test `invalidate`: populate cache, call `invalidate(connection_id)`, call `view_for` again; assert reflector called a second time

Done signal: `pytest tests/unit/catalog/ -v` — all tests pass with no live DB.

## 6. Integration tests — reflection against real DBs

- [x] 6.1 Add `testcontainers` to `[project.optional-dependencies]` dev group in `pyproject.toml`
- [x] 6.2 Create `tests/integration/__init__.py` and `tests/integration/catalog/__init__.py` (both empty)
- [x] 6.3 Create `tests/integration/catalog/test_sqlalchemy_schema_reflector.py` — session-scoped Postgres container fixture; assert `reflect(url, frozenset({"users"}))` returns a `CatalogView` with `sa_table("users")` and `column("users", "id")` working correctly
- [x] 6.4 Add MSSQL integration test marked `@pytest.mark.mssql`; identical assertions against MSSQL container; guarded by `MSSQL_TESTS` env var so it is skipped by default
- [x] 6.5 Add end-to-end test: reflect catalog → compile `QuerySpec` → assert SQL is correct (Postgres only)

Done signal: `pytest tests/integration/catalog/ -v -m "not mssql"` passes against a running Postgres container.
