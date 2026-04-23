## Why

M1 and M2 deliver compilation and schema reflection, but nothing prevents a user from building a `QuerySpec` that joins 10 tables, selects sensitive columns, or requests an unlimited row export. M3 introduces the governance layer — a policy port that enforces data-access and structural rules before any SQL reaches the database — and the first use case that wires catalog, policy, and compiler together into a callable operation.

## What Changes

- Define `IQueryPolicy` port in `domain/interfaces/` — validates a `QuerySpec` against a rule set, raises `PolicyViolation` on failure
- Implement `DefaultQueryPolicy` adapter — enforces v1 structural rules: max 3 joins, mandatory row limit ≤ 10 000, no duplicate output labels, no self-join on the same alias
- Implement `TableAllowlistPolicy` adapter — enforces a per-connection table allowlist; raises `PolicyViolation` if any `JoinDef.table` is not in the approved set
- Introduce `use_cases/compile_query.py` — the first use case; orchestrates: `ICatalogRepository.view_for` → `IQueryPolicy.validate` → `IQueryCompiler.compile` → returns `CompiledQuery`
- Unit-test all policy rules and the use case with in-memory fakes

## Capabilities

### New Capabilities

- `query-policy`: Validates a `QuerySpec` against structural and data-governance rules before compilation. Raises `PolicyViolation` on any violation. Two implementations: `DefaultQueryPolicy` (structural rules) and `TableAllowlistPolicy` (per-connection table entitlements).
- `compile-query-use-case`: Orchestrates catalog resolution, policy enforcement, and compilation into a single callable unit. Entry point for the FastAPI handler added in a later milestone.

### Modified Capabilities

*(none — compiler and catalog-reflection requirements are unchanged)*

## Non-goals

- Row-level security or column-level masking (future)
- Runtime entitlement checks against an external permission store (M5)
- Audit logging (M5)
- Query execution (M4)
- FastAPI route wiring (M4)

## Impact

- **New files**: `domain/interfaces/query_policy.py`, `adapters/policy/default_query_policy.py`, `adapters/policy/table_allowlist_policy.py`, `use_cases/__init__.py`, `use_cases/compile_query.py`
- **No breaking changes** to M0–M2 domain types, compiler, or catalog interfaces
