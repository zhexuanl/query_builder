## Why

M1 proved the compiler can turn a `QuerySpec` into correct SQL, but the catalog it depends on (`CatalogView`) is still a test fake — there is no production path from a source DB connection to real table and column metadata. M2 closes that gap by implementing schema reflection so the compiler can operate against live source databases.

## What Changes

- Introduce `ISchemaReflector` port in `domain/interfaces/` — reflects table names and column metadata from a live connection
- Implement `SqlAlchemySchemaReflector` adapter in `adapters/catalog/` — uses SQLAlchemy `Inspector` to reflect schema from Postgres and MSSQL connections
- Implement `SqlAlchemyCatalogView` — the production `CatalogView` backed by reflected `Table` objects
- Implement `InMemoryCatalogRepository` (infrastructure) — caches reflected views keyed by `(connection_id, frozenset[table_names])` to avoid re-reflecting on every compile
- Add integration tests (Docker) asserting reflection round-trips for both dialects

## Capabilities

### New Capabilities

- `catalog-reflection`: Reflects table and column schema from a live source DB into a `CatalogView` usable by the compiler. Supports Postgres and MSSQL. Caches results per connection + table set.

### Modified Capabilities

*(none — `IQueryCompiler` and `CatalogView` port signatures are unchanged)*

## Non-goals

- Connection credential management (M5)
- Reflecting views, stored procedures, or non-table objects
- Cross-schema or cross-DB joins
- Query execution (M4)

## Impact

- **New files**: `domain/interfaces/schema_reflector.py`, `adapters/catalog/sqlalchemy_schema_reflector.py`, `adapters/catalog/sqlalchemy_catalog_view.py`, `infrastructure/catalog/in_memory_catalog_repository.py`
- **Dependencies added**: none (SQLAlchemy already present; test infra adds `pytest-docker` or `testcontainers`)
- **No breaking changes** to M0 domain types or M1 compiler
