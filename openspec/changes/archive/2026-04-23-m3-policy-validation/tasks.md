## 1. Domain port

- [x] 1.1 Create `domain/interfaces/query_policy.py` — define `IQueryPolicy` ABC with `validate(spec: QuerySpec, catalog: CatalogView) -> None`; raises `PolicyViolation` on failure; Google-style docstring

Done signal: `from domain.interfaces.query_policy import IQueryPolicy` imports cleanly with no framework dependencies.

## 2. Structural policy adapter

- [x] 2.1 Create `adapters/policy/__init__.py` (empty)
- [x] 2.2 Create `adapters/policy/default_query_policy.py` — implement `DefaultQueryPolicy(IQueryPolicy)` enforcing:
  - `_MAX_JOINS = 3`: raise `PolicyViolation` if `len(spec.joins) > _MAX_JOINS`
  - `_MAX_LIMIT = 10_000`: raise `PolicyViolation` if `spec.limit is None` or `spec.limit > _MAX_LIMIT`
  - No duplicate `SelectField.label` across `spec.select`
  - No duplicate alias across `spec.source.alias` and all `JoinDef.alias` in `spec.joins`

Done signal: `DefaultQueryPolicy().validate(spec, catalog)` raises `PolicyViolation` for each rule; passes on valid specs.

## 3. Table allowlist policy adapter

- [x] 3.1 Create `adapters/policy/table_allowlist_policy.py` — implement `TableAllowlistPolicy(IQueryPolicy)`; constructor takes `allowlists: Mapping[str, frozenset[str]]`; `validate()` checks `spec.source.table` and all `JoinDef.table` against `allowlists.get(spec.connection_id)`, skipping the check if `connection_id` is absent

Done signal: `TableAllowlistPolicy({"conn-1": frozenset({"orders"})}).validate(spec_with_customers, ...)` raises `PolicyViolation`.

## 4. Use case

- [x] 4.1 Create `use_cases/__init__.py` (empty)
- [x] 4.2 Create `use_cases/compile_query.py` — implement `CompileQueryUseCase` with constructor `(catalog_repo: ICatalogRepository, policies: list[IQueryPolicy], compiler: IQueryCompiler)` and method `execute(spec: QuerySpec, dialect: Dialect) -> CompiledQuery`; derive `table_names` from `spec.source.table` + `{j.table for j in spec.joins}`; call `catalog_repo.view_for(spec.connection_id, table_names)`, then each policy's `validate(spec, catalog)`, then `compiler.compile(spec, catalog, dialect)`

Done signal: `CompileQueryUseCase(...).execute(spec, Dialect.postgres)` returns a `CompiledQuery` when all injected fakes are happy.

## 5. Unit tests — policy rules

- [x] 5.1 Create `tests/unit/policy/__init__.py` and `tests/unit/policy/test_default_query_policy.py`
- [x] 5.2 Test join limit: 4 joins → `PolicyViolation`; 3 joins → passes
- [x] 5.3 Test limit=None → `PolicyViolation`; limit=10_001 → `PolicyViolation`; limit=10_000 → passes
- [x] 5.4 Test duplicate output label → `PolicyViolation`
- [x] 5.5 Test duplicate alias (source vs join) → `PolicyViolation`
- [x] 5.6 Create `tests/unit/policy/test_table_allowlist_policy.py`
- [x] 5.7 Test unapproved source table → `PolicyViolation`
- [x] 5.8 Test unapproved join table → `PolicyViolation`
- [x] 5.9 Test all tables approved → passes; unknown connection_id → passes

Done signal: `pytest tests/unit/policy/ -v` — all tests pass.

## 6. Unit tests — use case

- [x] 6.1 Create `tests/unit/use_cases/__init__.py` and `tests/unit/use_cases/test_compile_query.py`
- [x] 6.2 Test successful path: mock catalog_repo, policy, compiler; assert `execute()` returns `CompiledQuery` and all three mocks called in order
- [x] 6.3 Test `PolicyViolation` propagates: policy mock raises `PolicyViolation`; assert compiler mock never called
- [x] 6.4 Test `CatalogMiss` propagates from catalog_repo
- [x] 6.5 Test table names derived correctly for single-table spec (assert `view_for` called with correct frozenset)
- [x] 6.6 Test table names derived correctly for spec with two joins

Done signal: `pytest tests/unit/use_cases/ -v` — all tests pass.
