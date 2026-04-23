## Context

This is a SQL-generation library. Consuming projects own persistence, audit, and materialization. QA hardening means: (1) proving correctness across the full scenario/edge-case space, (2) giving consumers a clean codec for transmitting `QuerySpec` over a wire, and (3) providing an optional pooled executor for high-frequency call sites. No new production infrastructure belongs here.

## Goals / Non-Goals

**Goals:**
- Comprehensive integration test suite against real Postgres (testcontainers)
- MSSQL SQL-string parity assertions (no container — compare rendered SQL strings)
- Port contract base classes consumers can subclass to test their own implementations
- `QuerySpecCodec` pure-Python round-trip serialisation
- `PooledSqlAlchemyQueryExecutor` for consumers who manage engine lifecycle
- Close unit test gaps: `JsonStdoutAuditLog`, `SqlAlchemyCatalogView`, API model mapping

**Non-Goals:**
- Any persistence layer, Alembic, or ORM models
- Production audit log or dataset storage
- Connection pool management beyond the two executor variants

---

## Decisions

### Decision 1 — Integration test matrix

| Test file | Fixture | What it proves |
|---|---|---|
| `test_full_pipeline.py` | Postgres testcontainer + `TestClient(create_app(...))` | `POST /queries/execute` returns correct rows, audit event recorded in `FakeAuditLog`, cipher-backed connection repo decrypts URL correctly |
| `test_dataset_round_trip.py` | Postgres testcontainer | `POST /datasets` → `GET /datasets/{id}` → spec fields intact; `SaveDatasetUseCase` compile dry-run rejects bad specs before save |
| `test_policy_rejection_flow.py` | No DB — all in-memory | Closed-by-default allowlist → 422 `POLICY_VIOLATION`; duplicate alias → 422; row-cap exceeded → 422; correct `error_code` in all cases |
| `test_edge_cases.py` | In-memory fake catalog + fake executor | NULL predicate, IN list, OR nesting, zero-row result, `count_distinct`, 3-join exactly-at-max, spec with no `select` fields raises at construction |
| `test_mssql_parity.py` | No DB | Same `QuerySpec` compiled for `mssql` produces `TOP N`, bracket quoting, no `LIMIT`; compare normalised SQL strings |

Testcontainer fixture is shared via `conftest.py` — one container per session, not per test.

### Decision 2 — Port contract base test classes

```python
# tests/contracts/query_policy_contract.py
class QueryPolicyContract:
    """Subclass and set `policy` and `make_spec()` to verify any IQueryPolicy."""
    def test_valid_spec_does_not_raise(self): ...
    def test_returns_none_on_success(self): ...
```

One contract module per port: `QueryPolicyContract`, `QueryExecutorContract`, `QueryCompilerContract`. These live in `tests/contracts/` and are importable by consuming projects.

### Decision 3 — `QuerySpecCodec` lives in `domain/value_objects/serialisation.py`

Pure Python, zero framework imports. Encodes `QuerySpec → dict[str, Any]` (JSON-safe) and decodes `dict → QuerySpec`. Handles:
- `frozenset` ↔ sorted `list`
- `tuple` ↔ `list`
- Nested frozen dataclasses (recursive)
- `Dialect` enum ↔ string
- `ColumnRef`, `ValueRef`, `ParamRef` discriminated by `"kind"` field

Property-based round-trip test using `hypothesis` (or hand-crafted fixtures if hypothesis is not already a dependency).

### Decision 4 — `PooledSqlAlchemyQueryExecutor` is an adapter variant, not a port change

`IQueryExecutor.execute(query, connection_url)` is unchanged. `PooledSqlAlchemyQueryExecutor.__init__(engine: Engine)` accepts a pre-built engine; `execute()` uses it directly. The default `SqlAlchemyQueryExecutor` continues to create-and-dispose per call (stateless, correct for library default). Consumers who care about pool efficiency instantiate `PooledSqlAlchemyQueryExecutor` with their own engine.

This is the right library pattern: safe default, opt-in performance.

### Decision 5 — No Alembic, no ORM models, no schema

The consuming project owns the database. This library ships with SQLite-backed integration test fixtures only — `create_engine("sqlite:///:memory:")` for test isolation, Postgres testcontainer for real-DB tests. `InMemoryDatasetRepository`, `InMemoryConnectionRepository`, and `InMemoryCatalogRepository` remain as the canonical reference implementations.

### Decision 6 — MSSQL parity without a container

MSSQL testcontainers are heavy and require a licence. SQL parity is verified by:
1. Compiling the same `QuerySpec` for `Dialect.mssql`
2. Asserting `"TOP"` in sql, `"LIMIT"` not in sql, `"["` in sql (bracket quoting)
3. Normalising whitespace before comparison

This is sufficient to catch dialect regressions without a live MSSQL instance. The existing `MSSQL_TESTS=1` gate for schema reflection remains.

## Risks / Trade-offs

- **`QuerySpecCodec` fragility on schema evolution** — any new field added to `QuerySpec` or its children must be added to the codec. Mitigate: codec has an explicit version field in the encoded dict; unrecognised version raises `ValueError`.
- **Hypothesis adds a new dev dependency** — if not already present, only add for the codec round-trip test; it's a test-only dependency.
- **Testcontainer session scope speeds up but couples tests** — if one test corrupts DB state, subsequent tests fail. Mitigate: each test creates its own schema/table names; teardown drops them.

## Migration Plan

Additive only — no production code changes except two new files:
1. `domain/value_objects/serialisation.py`
2. `adapters/executor/pooled_sqlalchemy_query_executor.py`

All other changes are test files. No migration required.

## Open Questions

- Should `QuerySpecCodec` be exported from a top-level `query_builder` package `__init__.py`? (Propose: yes — it is part of the public library surface)
- Should contract test base classes be shipped as part of the library (in `src/`) so consuming projects can import them without copying? (Propose: yes — `query_builder.testing.contracts`)
