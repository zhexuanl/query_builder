## QA Hardening: Integration Tests, Scenario Coverage, and Optimisations

## Why

M0–M6 built a complete SQL-generation library: compile `QuerySpec` → SQL, preview rows, enforce structural policies, manage connection strings. The unit test suite (14 files) covers each component in isolation, but only two integration tests exercise real databases, and several critical paths — multi-join scenarios, edge-case filters, MSSQL SQL parity, zero-row results, and the full compile→execute→preview pipeline — have never been exercised end-to-end.

Additionally, `SqlAlchemyQueryExecutor` creates a new connection pool on every `execute()` call, which is the correct default for a library (stateless, no side effects) but imposes unnecessary overhead when a consumer calls `execute()` in a tight loop. An optional pooled variant should be provided.

The in-memory reference implementations (`InMemoryConnectionRepository`, `InMemoryDatasetRepository`, `InMemoryCatalogRepository`) are intentionally thin — they are test doubles that consuming projects replace. No persistence layer belongs in this library.

## What Changes

- Integration test suite expanded: full compile→execute pipeline, policy rejection flows, MSSQL SQL-string parity, dataset save→retrieve→execute round-trip
- Common scenario tests: multi-join projections, aggregate+group-by, OR/AND filter nesting, sort+limit combinations
- Edge case tests: NULL predicates, IN with value list, zero-row result, joins exactly at max, `count_distinct`, `is_null`, overlapping aliases caught early
- Port contract test helpers: abstract base test classes that any `IQueryPolicy` / `IQueryExecutor` / `IQueryCompiler` implementation can inherit to verify conformance
- Unit test gaps closed: `JsonStdoutAuditLog`, `SqlAlchemyCatalogView`, API model mapping helpers
- `PooledSqlAlchemyQueryExecutor`: optional executor variant that accepts a pre-built `Engine` instead of a URL — consumer responsibility to manage pool lifecycle; default executor unchanged
- `QuerySpecCodec`: pure-Python JSON codec (`QuerySpec ↔ dict`) as a library utility for consumers who need to serialise/deserialise specs; no DB dependency

## Capabilities

### New Capabilities
- `integration-test-suite`: testcontainer-based end-to-end tests covering the full pipeline for Postgres; MSSQL parity assertions via SQL-string comparison (no MSSQL container required)
- `query-spec-codec`: pure-Python `QuerySpec ↔ dict` serialisation utility; enables consumers to persist or transmit specs without any framework dependency
- `pooled-executor`: `PooledSqlAlchemyQueryExecutor` accepting a pre-built `Engine`; documents the pool-management contract for library consumers

### Modified Capabilities
- `query-compiler`: additional scenario and edge-case tests against `SqlAlchemyCoreCompiler`
- `query-policy`: port contract test base class; edge-case tests for exactly-at-boundary values
- `execute-query-use-case`: scenario tests for full pipeline; audit-log failure isolation verified

## Impact

- New test files only (no production code changes except `PooledSqlAlchemyQueryExecutor` and `QuerySpecCodec`)
- New files: `domain/value_objects/serialisation.py`, `adapters/executor/pooled_sqlalchemy_query_executor.py`, `tests/contracts/`, `tests/integration/test_full_pipeline.py`, `tests/integration/test_mssql_parity.py`, `tests/integration/test_edge_cases.py`, `tests/unit/test_query_spec_codec.py`

## Non-goals

- Persistent storage of any kind (consuming project's concern)
- Audit log DB backend (consuming project's concern)
- Dataset persistence (consuming project's concern)
- Frontend integration
- Multi-tenant or auth concerns
