## MODIFIED Requirements

### Requirement: ExecuteQueryUseCase orchestrates compilation and execution
`ExecuteQueryUseCase.execute(spec, dialect, caller_id)` SHALL call `CompileQueryUseCase.execute()` to compile the spec, resolve the `connection_url` via `IConnectionRepository`, run the compiled SQL via `IQueryExecutor`, write an `AuditEvent` via `IAuditLog`, and return the result rows. The `caller_id` parameter is mandatory and MUST be recorded in the audit event. It MUST NOT perform SQL compilation logic itself.

#### Scenario: Successful execute returns rows and writes success audit event
- **WHEN** `execute()` is called with a valid spec, `caller_id`, all policies pass, and the source DB is reachable
- **THEN** `list[dict[str, Any]]` rows are returned and `IAuditLog.append()` is called once with `outcome="success"` and the correct `row_count`

#### Scenario: PolicyViolation propagates and writes audit event
- **WHEN** any `IQueryPolicy` raises `PolicyViolation` during the compile step
- **THEN** `PolicyViolation` propagates out of `execute()` without wrapping; `IAuditLog.append()` is called with `outcome="policy_violation"`; `IQueryExecutor` is not called

#### Scenario: CompilationError propagates and writes audit event
- **WHEN** `IQueryCompiler.compile()` raises `CompilationError`
- **THEN** `CompilationError` propagates and `IAuditLog.append()` is called with `outcome="compilation_error"`

#### Scenario: CatalogMiss propagates and writes audit event
- **WHEN** `ICatalogRepository.view_for()` raises `CatalogMiss`
- **THEN** `CatalogMiss` propagates and `IAuditLog.append()` is called with `outcome="catalog_miss"`

#### Scenario: SourceConnectionError propagates and writes audit event
- **WHEN** `IQueryExecutor.execute()` raises `SourceConnectionError`
- **THEN** `SourceConnectionError` propagates and `IAuditLog.append()` is called with `outcome="source_error"`

#### Scenario: Row-cap exceeded raises PolicyViolation and writes audit event
- **WHEN** the executor returns more than `_MAX_RESULT_ROWS` rows
- **THEN** `PolicyViolation` is raised and `IAuditLog.append()` is called with `outcome="row_cap_exceeded"`

#### Scenario: Audit log failure does not surface to caller
- **WHEN** `IAuditLog.append()` raises an exception internally
- **THEN** the exception is swallowed; the use case returns rows or re-raises the original domain error as if the audit log were working
