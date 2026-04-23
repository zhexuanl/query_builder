## Context

M1 shipped `SqlAlchemyCoreCompiler` which depends on `CatalogView` — an abstract port that returns SQLAlchemy table and column objects. The compiler tests use `InMemoryCatalogView` (a dict-backed fake). M2 delivers the production implementation: a `CatalogView` built from live schema reflection via SQLAlchemy `Inspector`, plus the caching repository that manages view lifetimes.

Current state: `domain/interfaces/catalog_repository.py` declares `CatalogView` and `ICatalogRepository` but both have no production implementation. `ISchemaReflector` is listed in the domain ports inventory but has no file.

## Goals / Non-Goals

**Goals:**
- Define `ISchemaReflector` port in domain
- Implement `SqlAlchemySchemaReflector` (adapter layer) — creates a SQLAlchemy `Engine` from a connection URL and uses `Inspector` to enumerate tables and columns
- Implement `SqlAlchemyCatalogView` (adapter layer) — wraps reflected `Table` objects, satisfies `CatalogView`
- Implement `InMemoryCatalogRepository` (infrastructure layer) — caches `CatalogView` instances keyed by `(connection_id, frozenset[table_names])`, evicts on TTL or explicit invalidation
- Integration tests asserting reflection round-trips against real Postgres and MSSQL instances (via `testcontainers`)

**Non-Goals:**
- Connection credential storage or retrieval (M5 — `IConnectionRepository`)
- Reflecting views, functions, indexes, or non-table objects
- Cross-schema or cross-DB references
- Query execution (M4)
- Cache persistence across process restarts

## Decisions

### D1: `ISchemaReflector` takes a URL string, not a `Connection` object

**Chosen**: `reflect(url: str, table_names: frozenset[str]) -> CatalogView`

The port lives in `domain/`, which must have zero framework imports. Accepting a raw URL string keeps the port pure Python. The adapter (`SqlAlchemySchemaReflector`) creates the engine internally.

**Alternative considered**: Accept a SQLAlchemy `Connection` or `Engine`. Rejected — leaks SQLAlchemy into the domain port signature.

*Decision-gate §7 applies*: new port in `domain/interfaces/`. Documented here.

---

### D2: `SqlAlchemyCatalogView` wraps `Table` objects from a shared `MetaData`

Reflection produces SQLAlchemy `Table` objects attached to a `MetaData`. The `CatalogView` holds these and aliases them on `sa_table()` calls. Column access delegates to `table.c[name]`.

**Alternative considered**: Re-reflect on every `column()` call. Rejected — O(N) round-trips per compile.

---

### D3: Cache key is `(connection_id, frozenset[table_names])`

The repository caches `CatalogView` per unique `(connection_id, frozenset[table_names])` pair. Two specs using the same connection but different table sets get separate cache entries (avoids over-reflection). Cache entries carry a `reflected_at` timestamp; callers can force-invalidate by connection_id.

**Alternative considered**: Cache only by `connection_id` and reflect all tables. Rejected — source DBs may have thousands of tables; reflecting all is prohibitively slow.

---

### D4: `testcontainers-python` for integration tests

Integration tests spin up real Postgres and MSSQL containers via `testcontainers`. Fixtures are `session`-scoped to amortise startup cost across all tests in a session.

**Alternative considered**: `pytest-docker` with a `docker-compose.yml`. Rejected — `testcontainers` is programmatic, easier to manage port conflicts, and already common in the Python ecosystem.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| MSSQL `testcontainers` image is large (~1.5 GB `mcr.microsoft.com/mssql/server`) | Mark MSSQL integration tests with `@pytest.mark.mssql`; skip by default in CI unless `MSSQL_TESTS=1` |
| Schema changes on source DB invalidate cached views mid-session | Cache TTL (default 5 min) + force-invalidate endpoint; acceptable for v1 |
| `Inspector` behaviour differs between SA dialects for nullable / default metadata | Restrict to `name` and `type_` only in v1; don't expose nullability or defaults to `CatalogView` |
| `ISchemaReflector` port signature locked in by this milestone | URL-string interface is narrow enough to accommodate future credential injection (M5 wraps URL construction) |

## Open Questions

- **Q1**: Should `InMemoryCatalogRepository` be in `infrastructure/` (wired at startup) or `adapters/` (swappable)? → Placed in `infrastructure/` since it holds process-lifetime state and is wired by the DI container. Adapters remain stateless.
- **Q2**: What column metadata does `CatalogView` need to expose beyond name and SQLAlchemy column object? → v1: name + column expression only. Type information surfaced in M3 for policy validation.
