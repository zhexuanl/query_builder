## M4: Query Execution + FastAPI Route

## Why

`CompileQueryUseCase` produces SQL but nothing yet runs it. M4 closes that gap by adding a query execution layer and the first HTTP endpoint that wires compilation + execution into a single user-facing operation.

## What Changes

- New `IQueryExecutor` port: executes a `CompiledQuery` against a source DB and returns rows
- New `SqlAlchemyQueryExecutor` adapter: uses `engine.connect()` to run the compiled SQL, streams results as dicts
- New `ExecuteQueryUseCase`: orchestrates `CompileQueryUseCase → IQueryExecutor`, enforces row-count cap
- New `POST /queries/execute` FastAPI route: accepts `QuerySpecRequest`, returns `QueryResultResponse`
- DI wiring in the app factory for all new components

## Capabilities

### New Capabilities
- `query-execution`: Port + adapter for running compiled SQL and returning rows as dicts; row-cap enforcement
- `execute-query-use-case`: Orchestration use case that chains compile → execute; surfaces `CompilationError`, `PolicyViolation`, `CatalogMiss`, `SourceConnectionError` as distinct HTTP errors
- `query-api`: FastAPI route contract — request/response schemas, error mapping, OpenAPI metadata

### Modified Capabilities

## Impact

- New files: `domain/interfaces/query_executor.py`, `adapters/executor/sqlalchemy_query_executor.py`, `use_cases/execute_query.py`, `infrastructure/api/routes/queries.py`, Pydantic request/response models
- `infrastructure/app_factory.py` — DI wiring for executor, new route inclusion
- No changes to existing domain types, ports, or compiler

## Non-goals

- Pagination / cursor-based streaming (M5+)
- Per-user row quotas or cost estimation
- Result caching or async job queue
- Frontend integration (separate milestone)
