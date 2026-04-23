## 1. Dependencies and Ports

- [x] 1.1 Add `fastapi`, `uvicorn[standard]`, and `httpx` (test client) to `pyproject.toml` / `requirements.txt`; verify `pytest` can import `fastapi`
- [x] 1.2 Create `domain/interfaces/query_executor.py` — `IQueryExecutor` ABC with `execute(query: CompiledQuery, connection_url: str) -> list[dict[str, Any]]`
- [x] 1.3 Create `domain/interfaces/connection_repository.py` — `IConnectionRepository` ABC with `get_url(connection_id: str) -> str`; raises `CatalogMiss` if unknown

## 2. In-Memory Fakes and Infrastructure Adapter

- [x] 2.1 Create `infrastructure/connection/in_memory_connection_repository.py` — wraps `dict[str, str]`; `get_url()` raises `CatalogMiss` for unknown IDs
- [x] 2.2 Create `tests/fakes/fake_query_executor.py` — `FakeQueryExecutor(rows)` that returns preset rows; used in use-case unit tests
- [x] 2.3 Create `adapters/executor/sqlalchemy_query_executor.py` — `SqlAlchemyQueryExecutor.execute()`: `create_engine` → `with engine.connect() as conn: conn.execute(text(sql), params)` → map rows to dicts → `finally: engine.dispose()`; wrap DB errors as `SourceConnectionError`

## 3. ExecuteQueryUseCase

- [x] 3.1 Create `use_cases/execute_query.py` — `ExecuteQueryUseCase.__init__(compile_use_case, connection_repo, executor)`; `execute(spec, dialect)` chains compile → get_url → executor.execute → row-cap check
- [x] 3.2 Add `_MAX_RESULT_ROWS = 10_000` constant; raise `PolicyViolation` if `len(rows) > _MAX_RESULT_ROWS`
- [x] 3.3 Write unit tests in `tests/unit/use_cases/test_execute_query.py`:
  - Successful path returns rows
  - PolicyViolation from compile propagates; executor not called
  - CompilationError propagates; executor not called
  - CatalogMiss propagates; executor not called
  - SourceConnectionError from executor propagates
  - Row-count exceeds cap raises PolicyViolation
  - Row-count at cap returns rows unchanged

## 4. FastAPI Route and App Factory

- [x] 4.1 Create Pydantic request/response models in `infrastructure/api/models/query_models.py` — `QuerySpecRequest`, `QueryResultResponse`; include all QuerySpec fields and `dialect`
- [x] 4.2 Create `infrastructure/api/routes/queries.py` — `router = APIRouter(prefix="/queries")`; `POST /execute` handler calling `execute_query_use_case.execute()`; map `PolicyViolation`/`CompilationError`/`CatalogMiss` → 422, `SourceConnectionError` → 502
- [x] 4.3 Create `infrastructure/app.py` — `create_app(config) -> FastAPI` factory: constructs all adapters and use cases, includes queries router; done signal: `import` + `create_app({})` does not raise

## 5. Tests

- [x] 5.1 Write `tests/unit/api/test_queries_route.py` — use `TestClient`; mock `ExecuteQueryUseCase`; cover 200, 422 (policy/compile/catalog), 502 (source connection) paths
- [x] 5.2 Write `tests/integration/test_execute_query_integration.py` — Postgres testcontainer: reflect schema, compile, execute, assert rows returned; skip when Docker unavailable
- [x] 5.3 Run full test suite (`pytest backend/tests/`) — all tests green before commit
