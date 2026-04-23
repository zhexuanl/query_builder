## ADDED Requirements

### Requirement: Port contract base classes enable third-party implementations to self-verify
The library SHALL ship abstract test base classes in `tests/contracts/` (or `src/query_builder/testing/`) that any `IQueryPolicy`, `IQueryCompiler`, or `IQueryExecutor` implementation can subclass to verify port conformance. Each base class MUST document which abstract methods must be overridden to supply fixtures.

#### Scenario: IQueryPolicy contract verifies validate() return type
- **WHEN** a conforming policy is tested via `QueryPolicyContract`
- **THEN** `validate()` returning `None` on a valid spec passes the contract test

#### Scenario: IQueryPolicy contract verifies PolicyViolation is raised, not returned
- **WHEN** a conforming policy raises `PolicyViolation` on an invalid spec
- **THEN** the contract test passes; returning a non-None value instead of raising fails the contract test

#### Scenario: IQueryExecutor contract verifies SourceConnectionError on bad URL
- **WHEN** an executor implementation is tested via `QueryExecutorContract` with an unreachable URL
- **THEN** `SourceConnectionError` is raised, satisfying the contract

---

### Requirement: SqlAlchemyCatalogView unit tests cover CatalogMiss paths
`SqlAlchemyCatalogView` currently has no unit tests. Tests SHALL verify `sa_table()` and `column()` raise `CatalogMiss` for unknown aliases and column names respectively.

#### Scenario: sa_table() raises CatalogMiss for unknown alias
- **WHEN** `catalog_view.sa_table("unknown_alias")` is called
- **THEN** `CatalogMiss` is raised identifying the alias

#### Scenario: column() raises CatalogMiss for unknown column name
- **WHEN** `catalog_view.column("alias", "nonexistent_col")` is called on a known alias
- **THEN** `CatalogMiss` is raised identifying the column

---

### Requirement: JsonStdoutAuditLog unit tests verify output format and exception swallowing
`JsonStdoutAuditLog` currently has no unit tests. Tests SHALL verify one JSON line is emitted per event, all `AuditEvent` fields are present, `timestamp` is ISO-8601, `table_names` is a sorted array, and internal exceptions are swallowed.

#### Scenario: One JSON line per event with all fields present
- **WHEN** `append(event)` is called with a complete `AuditEvent`
- **THEN** exactly one line is written to stdout and `json.loads(line)` contains all field names

#### Scenario: table_names serialised as sorted array
- **WHEN** `AuditEvent.table_names = frozenset({"orders", "customers"})` is appended
- **THEN** the JSON line contains `"table_names": ["customers", "orders"]`

#### Scenario: Internal write failure does not propagate
- **WHEN** stdout is replaced with a broken writer that raises on write
- **THEN** `append()` returns without raising
