## Context

M3 introduces the first cross-cutting concern that spans domain, adapters, and use_cases. The policy layer sits between the caller and the compiler: every `QuerySpec` must pass policy before SQL is emitted. This is also the milestone that introduces the use_cases layer, which did not exist before.

Current state: `domain/errors.py` already defines `PolicyViolation`. No policy port or use case exists yet. `use_cases/` directory does not exist.

## Goals / Non-Goals

**Goals:**
- Define `IQueryPolicy` port with a single `validate(spec, catalog)` method
- Implement `DefaultQueryPolicy` (structural rules) and `TableAllowlistPolicy` (data entitlement) as separate composable adapters
- Implement `CompileQueryUseCase` — the single entry point for callers: resolves catalog, runs policy, compiles, returns `CompiledQuery`
- Full unit test coverage for each policy rule and the use case orchestration

**Non-Goals:**
- Column-level entitlements, row-level security, or data masking
- Async policy evaluation or external permission stores (M5)
- Audit logging (M5)
- FastAPI route wiring (M4)

## Decisions

### D1: `IQueryPolicy` is a single-method port; composition via a list, not inheritance

**Chosen**: `validate(spec: QuerySpec, catalog: CatalogView) -> None` — raises `PolicyViolation`, returns nothing on success. Multiple policies are composed in the use case by iterating `list[IQueryPolicy]` and calling each in order.

**Alternative considered**: A `CompositePolicy` class wrapping a list. Rejected — the use case itself is the natural composition point and adding a wrapper is one extra moving part with no benefit.

*Decision-gate §7 applies*: new port in `domain/interfaces/`. Documented here.

---

### D2: `DefaultQueryPolicy` and `TableAllowlistPolicy` are separate adapters, not one class

Each enforcer covers a distinct concern. Keeping them separate allows them to be independently unit-tested, enabled, or disabled per deployment.

**Alternative considered**: A single `QueryPolicyEnforcer` with configuration flags. Rejected — one class per concern is cleaner and avoids a god-object with boolean soup.

---

### D3: `CompileQueryUseCase` takes all ports as constructor arguments

```python
class CompileQueryUseCase:
    def __init__(
        self,
        catalog_repo: ICatalogRepository,
        policies: list[IQueryPolicy],
        compiler: IQueryCompiler,
    ) -> None: ...

    def execute(self, spec: QuerySpec, dialect: Dialect) -> CompiledQuery: ...
```

The use case is stateless between calls — all state lives in the injected ports. DI wiring happens in `infrastructure/` (M4).

**Alternative considered**: Pass ports per-call to `execute()`. Rejected — constructor injection is idiomatic for use cases; it keeps call sites clean and makes mocking in tests trivial.

---

### D4: v1 structural rules in `DefaultQueryPolicy`

| Rule | Limit | Rationale |
|------|-------|-----------|
| Max joins | 3 | Prevents accidental cross-table fan-outs; matches UI constraint |
| Limit required | ≤ 10 000 | Prevents unlimited exports; `None` is rejected |
| No duplicate output labels | — | Compiler would produce ambiguous `SELECT` |
| No self-join on same alias | — | `JoinDef.alias` must be unique across source + joins |

These live in `DefaultQueryPolicy`, not `QuerySpec.__post_init__`, because they are governance rules (can be relaxed per tenant) rather than invariants of the data model.

---

### D5: `TableAllowlistPolicy` allowlist is a `frozenset[str]` per connection_id

```python
TableAllowlistPolicy(allowlists: Mapping[str, frozenset[str]])
```

`allowlists["conn-1"]` is the set of approved table names for that connection. A table name not in the set raises `PolicyViolation`. If `connection_id` is absent from `allowlists`, all tables are allowed (open by default; M5 will flip this to closed by default when the real permission store lands).

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Policy order matters if rules have side effects | Rules are pure validators — no side effects, so order is irrelevant |
| `DefaultQueryPolicy` limits are hard-coded | Constants named `_MAX_JOINS`, `_MAX_LIMIT` make them easy to find and change |
| `TableAllowlistPolicy` open-by-default is insecure if misconfigured | Acceptable in v1; M5 flips to closed-by-default with real entitlement data |
| `CompileQueryUseCase` couples catalog + policy + compiler in one class | This is the correct coupling — the use case is the orchestrator by design |

## Open Questions

*(none — all key decisions resolved above)*
