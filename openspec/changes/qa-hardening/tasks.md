## 1. Library Utilities

- [x] 1.1 Create `domain/value_objects/serialisation.py` — `QuerySpecCodec` with `encode(spec) -> dict` and `decode(data) -> QuerySpec`; handle all value object types; include `"version": 1` field; raise `ValueError` on unrecognised version
- [x] 1.2 Write `tests/unit/test_query_spec_codec.py`:
  - Round-trip on minimal spec (single table, single field)
  - Round-trip on full spec (joins, nested FilterGroup, agg, sort, limit)
  - `json.dumps(encode(spec))` succeeds
  - `decode({"version": 99, ...})` raises `ValueError`
- [x] 1.3 Create `adapters/executor/pooled_sqlalchemy_query_executor.py` — `PooledSqlAlchemyQueryExecutor(engine: Engine)`; `execute()` uses injected engine, never calls `dispose()`; wraps DB errors as `SourceConnectionError`
- [x] 1.4 Write `tests/unit/executor/test_pooled_executor.py`:
  - Mock engine: `execute()` calls `engine.connect()`, not `create_engine()`
  - DB error raises `SourceConnectionError`
  - `engine.dispose()` never called

## 2. Unit Test Gaps

- [x] 2.1 Write `tests/unit/catalog/test_sqlalchemy_catalog_view.py`:
  - `sa_table("unknown")` raises `CatalogMiss`
  - `column("alias", "missing_col")` raises `CatalogMiss`
  - `sa_table("valid")` returns the aliased table object
- [x] 2.2 Write `tests/unit/audit/test_json_stdout_audit_log.py` (capture stdout via `capsys`):
  - One JSON line per `append()` call
  - All `AuditEvent` fields present in JSON
  - `table_names` serialised as sorted array
  - `timestamp` is ISO-8601 string
  - Broken stdout does not propagate exception

## 3. Port Contract Base Classes

- [x] 3.1 Create `tests/contracts/__init__.py` and `tests/contracts/query_policy_contract.py` — `QueryPolicyContract` ABC: `test_valid_spec_returns_none`, `test_violation_raises_not_returns`
- [x] 3.2 Create `tests/contracts/query_executor_contract.py` — `QueryExecutorContract` ABC: `test_returns_list_of_dicts`, `test_bad_url_raises_source_connection_error`
- [x] 3.3 Create `tests/contracts/query_compiler_contract.py` — `QueryCompilerContract` ABC: `test_returns_compiled_query`, `test_unknown_alias_raises_compilation_error`
- [x] 3.4 Wire `DefaultQueryPolicy` and `SqlAlchemyCoreCompiler` into the contract tests as smoke-check (confirms existing impls pass their own contracts)

## 4. Edge Case and Scenario Unit Tests

- [x] 4.1 Add to `tests/unit/compilers/test_sqlalchemy_core_compiler.py`:
  - `IS NULL` predicate: no extra bound param
  - `IN` with three `ValueRef` values: three params in SQL and dict
  - Nested `OR` inside `AND` group: correct parenthesisation
  - `count_distinct` renders `count(DISTINCT ...)`
  - `limit=None` produces no `LIMIT` / `TOP`
- [x] 4.2 Add to `tests/unit/policy/test_default_query_policy.py`:
  - Exactly `_MAX_JOINS` joins: no violation
  - `_MAX_JOINS + 1` joins: violation
  - `limit = _MAX_LIMIT`: no violation
  - `limit = _MAX_LIMIT + 1`: violation

## 5. MSSQL Parity Tests

- [x] 5.1 Create `tests/unit/compilers/test_mssql_parity.py`:
  - `limit=50` + `Dialect.mssql` → SQL contains `TOP`, not `LIMIT`
  - Column refs use bracket quoting `[col]` not double-quotes
  - `JoinDef(type="inner")` → SQL contains `JOIN`, not `OUTER JOIN`
  - `JoinDef(type="left")` → SQL contains `LEFT OUTER JOIN`
  - Normalise whitespace before all assertions (`re.sub(r'\s+', ' ', sql).strip()`)

## 6. Integration Tests

- [x] 6.1 Create `tests/integration/conftest.py` — session-scoped Postgres testcontainer fixture; seeds two tables (`customers`, `orders`) with 5 rows each; creates `TestClient(create_app(test_config))` with `FakeAuditLog` and `InMemoryConnectionRepository` (registered with container URL)
- [x] 6.2 Create `tests/integration/test_full_pipeline.py`:
  - Single-table projection returns 5 seeded rows
  - JOIN returns joined rows
  - Filter reduces result set to matching rows only
  - Aggregate + GROUP BY returns one row per group
  - `FakeAuditLog.events[0].outcome == "success"` with correct `row_count`
- [x] 6.3 Create `tests/integration/test_dataset_round_trip.py`:
  - `POST /datasets` → 201 with `dataset_id`
  - `GET /datasets/{id}` → spec fields intact
  - Execute retrieved spec → same rows as direct compile+execute
- [x] 6.4 Create `tests/integration/test_policy_rejection_flow.py` (no DB):
  - Unknown `connection_id` → 422 `POLICY_VIOLATION`
  - Duplicate alias in joins → 422 `POLICY_VIOLATION`
  - `limit=None` → 422 `POLICY_VIOLATION`
  - `SourceConnectionError` from executor → 502 `SOURCE_UNAVAILABLE`
- [x] 6.5 Run full suite (`pytest backend/tests/ -x`) — all green before commit
