## ADDED Requirements

### Requirement: Reflect table schema from a live source database
The `ISchemaReflector` port SHALL accept a connection URL and a set of table names, connect to the source database, and return a `CatalogView` containing the reflected table and column metadata. Only the requested tables SHALL be reflected (not the entire schema).

#### Scenario: Reflect two tables from Postgres
- **WHEN** `reflect(url, frozenset({"customers", "transactions"}))` is called against a running Postgres instance containing both tables
- **THEN** the returned `CatalogView.sa_table("customers")` and `CatalogView.sa_table("transactions")` return valid SQLAlchemy aliased table expressions with the correct columns

#### Scenario: Reflect two tables from MSSQL
- **WHEN** `reflect(url, frozenset({"orders", "order_lines"}))` is called against a running MSSQL instance
- **THEN** the returned `CatalogView` resolves both tables and their columns correctly

#### Scenario: Requested table does not exist in the source database
- **WHEN** a table name in `table_names` does not exist in the source database
- **THEN** the reflector raises `SourceConnectionError` with a message identifying the missing table

---

### Requirement: CatalogView resolves table aliases and columns
The `CatalogView` returned by `ISchemaReflector` SHALL implement the same interface as the test fake — `sa_table(alias)` returns the aliased SQLAlchemy expression and `column(alias, name)` returns the column expression. The alias used for look-up SHALL be the table name used at reflection time.

#### Scenario: Column look-up succeeds
- **WHEN** `catalog.column("customers", "email")` is called on a `CatalogView` that was reflected with table `"customers"` containing column `"email"`
- **THEN** a valid SQLAlchemy column expression is returned

#### Scenario: Unknown alias raises CatalogMiss
- **WHEN** `catalog.sa_table("unknown")` is called and `"unknown"` was not in the reflected table set
- **THEN** `CatalogMiss` is raised

#### Scenario: Unknown column raises CatalogMiss
- **WHEN** `catalog.column("customers", "nonexistent_col")` is called and that column does not exist
- **THEN** `CatalogMiss` is raised

---

### Requirement: CatalogRepository caches reflected views by connection and table set
The `ICatalogRepository` implementation SHALL cache `CatalogView` instances keyed by `(connection_id, frozenset[table_names])`. Subsequent calls with the same key SHALL return the cached view without re-reflecting.

#### Scenario: Cache hit avoids re-reflection
- **WHEN** `view_for(connection_id, table_names)` is called twice with the same arguments
- **THEN** the reflector is invoked only once and the same `CatalogView` object is returned both times

#### Scenario: Different table sets produce separate cache entries
- **WHEN** `view_for("conn-1", frozenset({"a"}))` and `view_for("conn-1", frozenset({"a", "b"}))` are called
- **THEN** two separate reflections occur and two distinct `CatalogView` objects are cached

#### Scenario: Cache invalidation by connection_id
- **WHEN** `invalidate(connection_id)` is called
- **THEN** all cached views for that `connection_id` are evicted and the next `view_for` call re-reflects

---

### Requirement: Reflector and CatalogView are usable by the compiler without modification
The `SqlAlchemyCatalogView` returned by the reflector SHALL satisfy the `CatalogView` interface such that `SqlAlchemyCoreCompiler.compile(spec, catalog, dialect)` produces correct SQL when given a reflected catalog.

#### Scenario: End-to-end compile with reflected catalog — Postgres
- **WHEN** a `QuerySpec` selecting two columns from `"customers"` is compiled using a `CatalogView` reflected from a live Postgres DB
- **THEN** `CompiledQuery.sql` contains `SELECT … FROM customers AS c …` with no errors

#### Scenario: End-to-end compile with reflected catalog — MSSQL
- **WHEN** the same `QuerySpec` is compiled using a `CatalogView` reflected from a live MSSQL DB
- **THEN** `CompiledQuery.sql` contains `SELECT TOP … FROM customers AS c …` with no errors
