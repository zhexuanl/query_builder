## ADDED Requirements

### Requirement: PooledSqlAlchemyQueryExecutor reuses a caller-supplied Engine
`PooledSqlAlchemyQueryExecutor` SHALL implement `IQueryExecutor` and accept a pre-built `sa.Engine` at construction. `execute()` MUST use the provided engine directly and MUST NOT call `engine.dispose()` — the caller owns the engine lifecycle. It MUST wrap DB errors as `SourceConnectionError` with the same contract as `SqlAlchemyQueryExecutor`.

#### Scenario: execute uses the injected engine, not a new one
- **WHEN** `PooledSqlAlchemyQueryExecutor(engine).execute(query, url)` is called
- **THEN** the query runs against the injected engine; `url` is ignored

#### Scenario: DB error raises SourceConnectionError
- **WHEN** the engine raises an exception during execution
- **THEN** `SourceConnectionError` is raised, chaining the original exception

#### Scenario: engine.dispose() is never called by the executor
- **WHEN** `execute()` succeeds or raises
- **THEN** `engine.dispose()` has not been called (pool remains available for subsequent calls)

---

### Requirement: Default SqlAlchemyQueryExecutor remains stateless (create-and-dispose per call)
The existing `SqlAlchemyQueryExecutor` SHALL continue to create a new `Engine` per `execute()` call and dispose it in `finally`. This is the safe default for library consumers who do not manage a pool. Its behaviour MUST NOT change.

#### Scenario: Default executor disposes engine after each call
- **WHEN** `SqlAlchemyQueryExecutor().execute(query, url)` is called
- **THEN** `engine.dispose()` is called exactly once per `execute()` invocation regardless of outcome
