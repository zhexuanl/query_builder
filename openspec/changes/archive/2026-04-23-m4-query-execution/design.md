## Context

M1–M3 produced a compilation pipeline: `QuerySpec → CompileQueryUseCase → CompiledQuery`. Nothing executes the SQL yet, and no HTTP layer exists. M4 adds a `IQueryExecutor` port + SQLAlchemy adapter, an `ExecuteQueryUseCase` that chains compile → execute, and the first FastAPI route. FastAPI is not yet a project dependency and must be added.

## Goals / Non-Goals

**Goals:**
- Domain port `IQueryExecutor` — execute a `CompiledQuery` against a source DB, return rows as dicts
- `SqlAlchemyQueryExecutor` adapter — runs compiled SQL via `engine.connect()`, maps SA rows to `list[dict[str, Any]]`
- `ExecuteQueryUseCase` — composes `CompileQueryUseCase` + `IQueryExecutor`; enforces a hard row-count cap
- Minimal `IConnectionRepository` port + dict-based in-memory impl to supply `connection_url` to the executor
- `POST /queries/execute` FastAPI route with Pydantic request/response models and structured error mapping
- `create_app()` factory in `infrastructure/app.py` with full DI wiring

**Non-Goals:**
- Streaming / cursor-based pagination
- Per-user quotas, cost estimation, or async execution
- Result caching
- Frontend integration

## Decisions

### Decision 1 — `IQueryExecutor` port signature

**Chosen:** `execute(query: CompiledQuery, connection_url: str) -> list[dict[str, Any]]`

The port lives in `domain/interfaces/` and must be framework-free. Passing a plain `str` URL (established pattern from `ISchemaReflector`) keeps SQLAlchemy confined to the adapter. Returning `list[dict]` is JSON-serializable without leaking SA `Row` objects.

Alternative considered: accept an SA `Engine` — rejected because it imports SQLAlchemy into the domain.

**Layer:** `domain/interfaces/query_executor.py`

### Decision 2 — `ExecuteQueryUseCase` composes `CompileQueryUseCase`

**Chosen:** `ExecuteQueryUseCase.__init__` receives a fully-constructed `CompileQueryUseCase` instance plus `IQueryExecutor` and `IConnectionRepository`. It calls `compile_use_case.execute(spec, dialect)` then `executor.execute(compiled, url)`.

Alternative: duplicate catalog + policy + compiler injection directly in `ExecuteQueryUseCase`. Rejected — splits ownership of the compile contract and risks divergence.

**Layer:** `use_cases/execute_query.py`

### Decision 3 — Row cap enforced in the use case

The use case fetches up to `cap + 1` rows and raises `PolicyViolation("result exceeds N-row cap")` if the count exceeds the cap. This keeps the executor dumb (pure infrastructure) and the business rule in the domain layer.

### Decision 4 — Minimal `IConnectionRepository` port

**Port:** `get_url(connection_id: str) -> str` — raises `CatalogMiss` if unknown.

**In-memory impl:** wraps a `dict[str, str]` of `connection_id → url`. Sufficient for M4; M5 will replace with a credential-cipher–aware adapter.

**Layer:** port in `domain/interfaces/connection_repository.py`; impl in `infrastructure/connection/in_memory_connection_repository.py`

### Decision 5 — Error → HTTP status mapping

| Exception | HTTP status | Detail |
|---|---|---|
| `PolicyViolation` | 422 | message verbatim |
| `CompilationError` | 422 | message verbatim |
| `CatalogMiss` | 422 | message verbatim |
| `SourceConnectionError` | 502 | "Source database unavailable" (no internal detail to clients) |

Mapping lives in the route handler (not a generic exception handler) to keep it explicit and auditable.

### Decision 6 — No decision-gate required

All new ports have exactly one sensible implementation and additive-only contracts. No existing domain types or QuerySpec AST change.

## Risks / Trade-offs

- **Engine-per-request overhead** → `SqlAlchemyQueryExecutor` creates a fresh engine per call and calls `dispose()` in `finally`. This is acceptable for M4 (low concurrency, preview dataset); connection pooling is deferred to M5.
- **Synchronous execution blocks** → FastAPI runs the executor in the default thread pool (via `run_in_executor`). Avoids async SA complexity now; revisit if latency becomes an issue.
- **Row cap is a policy, not a DB-level LIMIT** → executor must fetch `cap+1` rows client-side. For v1 this is acceptable; a DB-side LIMIT guard should be added in M5.
- **In-memory connection repository exposes plain URLs** → adequate for local dev; M5 replaces with `ICredentialCipher`-backed store.

## Migration Plan

Additive only — no existing routes, DI, or domain types change.

1. Add `fastapi`, `uvicorn[standard]`, and `pydantic>=2` to `pyproject.toml`
2. Implement port, adapter, use case, route in order
3. Wire in `create_app()`
4. Run unit tests (mock executor) + integration test (Postgres testcontainer)

Rollback: delete new files; no schema migrations, no API clients yet.

## Open Questions

- Should `IConnectionRepository.get_url()` accept a `Dialect` hint for choosing driver? (Deferred to M5 when credential cipher lands)
- Exact row cap constant — propose `_MAX_RESULT_ROWS = 10_000` matching `_MAX_LIMIT` from `DefaultQueryPolicy`
