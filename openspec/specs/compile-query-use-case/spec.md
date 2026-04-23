## ADDED Requirements

### Requirement: CompileQueryUseCase orchestrates catalog, policy, and compilation
`CompileQueryUseCase.execute(spec, dialect)` SHALL resolve the catalog, run all policies, compile the spec, and return a `CompiledQuery`. It MUST NOT execute SQL against the source database.

#### Scenario: Successful compile returns CompiledQuery
- **WHEN** `execute(spec, dialect)` is called with a valid spec, the catalog resolves successfully, and all policies pass
- **THEN** a `CompiledQuery` with non-empty `sql` is returned

#### Scenario: Policy violation propagates to caller
- **WHEN** any `IQueryPolicy` raises `PolicyViolation` during `execute()`
- **THEN** `PolicyViolation` propagates out of `execute()` unchanged; no SQL is compiled

#### Scenario: CatalogMiss from repository propagates to caller
- **WHEN** `ICatalogRepository.view_for()` raises `CatalogMiss`
- **THEN** `CatalogMiss` propagates out of `execute()` unchanged

#### Scenario: CompilationError from compiler propagates to caller
- **WHEN** `IQueryCompiler.compile()` raises `CompilationError`
- **THEN** `CompilationError` propagates out of `execute()` unchanged

---

### Requirement: Use case resolves table names from the QuerySpec
The use case SHALL derive the set of table names to pass to `ICatalogRepository.view_for()` from `spec.source.table` plus all `JoinDef.table` values in `spec.joins`, without requiring the caller to supply this set manually.

#### Scenario: Table names derived correctly for single-table spec
- **WHEN** `execute()` is called with a spec that has one source table and no joins
- **THEN** `ICatalogRepository.view_for()` is called with `frozenset({spec.source.table})`

#### Scenario: Table names derived correctly for joined spec
- **WHEN** `execute()` is called with a spec that has a source and two joined tables
- **THEN** `ICatalogRepository.view_for()` is called with a frozenset of all three table names
