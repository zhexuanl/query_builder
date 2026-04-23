## ADDED Requirements

### Requirement: ExecuteQueryUseCase orchestrates compilation and execution
`ExecuteQueryUseCase.execute(spec, dialect, params)` SHALL call `CompileQueryUseCase.execute()` to compile the spec, resolve the `connection_url` via `IConnectionRepository`, run the compiled SQL via `IQueryExecutor`, and return the result rows. It MUST NOT perform SQL compilation logic itself.

#### Scenario: Successful execute returns rows
- **WHEN** `execute()` is called with a valid spec, all policies pass, and the source DB is reachable
- **THEN** `list[dict[str, Any]]` rows are returned

#### Scenario: PolicyViolation propagates unchanged
- **WHEN** any `IQueryPolicy` raises `PolicyViolation` during the compile step
- **THEN** `PolicyViolation` propagates out of `execute()` without wrapping; `IQueryExecutor` is not called

#### Scenario: CompilationError propagates unchanged
- **WHEN** `IQueryCompiler.compile()` raises `CompilationError`
- **THEN** `CompilationError` propagates out of `execute()` without wrapping

#### Scenario: CatalogMiss propagates unchanged
- **WHEN** `ICatalogRepository.view_for()` raises `CatalogMiss`
- **THEN** `CatalogMiss` propagates out of `execute()` without wrapping

#### Scenario: SourceConnectionError propagates unchanged
- **WHEN** `IQueryExecutor.execute()` raises `SourceConnectionError`
- **THEN** `SourceConnectionError` propagates out of `execute()` without wrapping

---

### Requirement: ExecuteQueryUseCase enforces a hard row-count cap
The use case SHALL raise `PolicyViolation` if the number of rows returned by the executor exceeds `_MAX_RESULT_ROWS`. This check MUST occur after execution and MUST NOT require a second database round-trip.

#### Scenario: Result within cap returned as-is
- **WHEN** the executor returns N rows where N ≤ `_MAX_RESULT_ROWS`
- **THEN** all N rows are returned to the caller

#### Scenario: Result exceeding cap raises PolicyViolation
- **WHEN** the executor returns more than `_MAX_RESULT_ROWS` rows
- **THEN** `PolicyViolation` is raised with a message identifying the cap and the actual count
