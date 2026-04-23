## Context

M0 delivered the domain layer: `QuerySpec` and its value objects are frozen, fully validated, and tested. The compiler is the next load-bearing piece — it converts a `QuerySpec` into a `CompiledQuery` (dialect SQL + bound params) without ever touching a live database.

Two new domain ports are introduced in this milestone: `ICatalogRepository` (minimum surface — resolves table names to SQLAlchemy `Table` objects) and `IQueryCompiler` (the compilation contract). Their concrete implementations live in `adapters/`.

## Goals / Non-Goals

**Goals:**
- Define `IQueryCompiler` port and `CompiledQuery` result type in `domain/interfaces/`
- Define the minimum `ICatalogRepository` port surface needed by the compiler
- Implement `SqlAlchemyCoreCompiler` in `adapters/compilers/` using SQLAlchemy Core Expression Language
- Prove correct SQL output for Postgres and MSSQL via golden tests (no live DB)
- Keep all compiler logic inside the adapter — `domain/` and `use_cases/` remain framework-free

**Non-Goals:**
- Executing queries against any real database
- Schema reflection or connection management (M2)
- Policy validation (M3)
- SQLGlot lint pass (M6)

## Decisions

### 1. `IQueryCompiler` is synchronous

**Decision:** `compile()` is a pure synchronous method — no `async`.

**Rationale:** Compilation is CPU-bound in-process work with no I/O. Making it `async` would complicate callers (use cases would need `await`) with zero benefit. The executor (M4) is where `async` belongs.

**Alternatives considered:** `async def compile()` — rejected; adds complexity without I/O.

**Clean Architecture layer:** `domain/interfaces/query_compiler.py`

```python
# domain/interfaces/query_compiler.py
from abc import ABC, abstractmethod
from typing import NamedTuple
from ..value_objects.dialect import Dialect
from ..entities.query_spec import QuerySpec

class CompiledQuery(NamedTuple):
    """Immutable result of a compilation pass."""
    sql: str
    params: dict[str, object]
    dialect: Dialect

class IQueryCompiler(ABC):
    """Port: compiles a QuerySpec to a dialect-specific SQL string with bound params."""

    @abstractmethod
    def compile(self, spec: QuerySpec, catalog: "CatalogView", dialect: Dialect) -> CompiledQuery:
        """Compile a QuerySpec to SQL.

        Args:
            spec: The validated query definition.
            catalog: Resolved table/column metadata for tables referenced in spec.
            dialect: Target SQL dialect.

        Returns:
            A CompiledQuery containing the SQL template and bound parameters.

        Raises:
            CompilationError: If the spec cannot be compiled (e.g. unknown column).
        """
```

### 2. Catalog view passed into `compile()`, not injected into constructor

**Decision:** `compile(spec, catalog, dialect)` receives a pre-fetched `CatalogView` rather than holding a repository.

**Rationale:** The compiler is a pure function over its inputs. Injecting a repository would introduce async complexity and make the compiler stateful. The use case (M4) fetches the catalog view before calling `compile()`.

**Alternatives considered:** Injecting `ICatalogRepository` into the compiler constructor — rejected; mixes I/O concern into a pure compilation step.

**Decision-gate §7 check:** New port `ICatalogRepository` — qualifies. Decision recorded here.

**Minimum `ICatalogRepository` surface for M1:**

```python
# domain/interfaces/catalog_repository.py  (stub — expanded in M2/M3)
class CatalogView:
    """Read-only catalog view for a single compilation pass."""

    def sa_table(self, table_name: str) -> sqlalchemy.Table:
        """Resolve a table name to a SQLAlchemy Table object."""
        ...

class ICatalogRepository(ABC):
    @abstractmethod
    def view_for(self, connection_id: str, table_names: frozenset[str]) -> CatalogView: ...
```

`CatalogView` lives in the domain interface file (not in `adapters/`) because it is part of the port contract that `IQueryCompiler` depends on. It contains no SQLAlchemy import — `sa_table()` is typed as `Any` in the domain; the adapter returns the real `Table`.

**Revised:** To keep `domain/` framework-free, `CatalogView` is an abstract class with `sa_table()` typed returning `Any`. The SQLAlchemy-typed implementation lives in `adapters/`.

### 3. SQLAlchemy `Table` objects constructed from catalog metadata, not via engine reflection

**Decision:** In M1, `InMemoryCatalogView` hand-constructs `sqlalchemy.Table` objects from fixture data. No engine, no reflection.

**Rationale:** The compiler needs `Table` objects to build expressions — not real database connectivity. Reflection (M2) is orthogonal to compilation (M1).

**Alternatives considered:** Using `MetaData.reflect(bind=engine)` — deferred to M2.

### 4. Render SQL without execution using `compile(dialect=...)`

**Decision:** Golden tests assert the string form of `stmt.compile(dialect=dialect_instance)` against checked-in expected SQL strings.

**Rationale:** SQLAlchemy's `compile()` produces the SQL template separately from execution — exactly the right split for preview/audit.

**MSSQL specifics:** `SELECT TOP N` instead of `LIMIT N`. SQLAlchemy's MSSQL dialect handles this automatically; no special-casing needed in the adapter.

**Param style:** Postgres → `:name`, MSSQL → `@name`. Both are handled by `compile(dialect=...)` transparently.

### 5. `count_distinct` mapped to `func.count(col.distinct())`

**Decision:** The `SelectField.func = "count_distinct"` case calls SQLAlchemy's `sa.func.count(col.distinct())`, not a raw string.

**Rationale:** Framework-idiomatic, dialect-agnostic, no string injection risk.

## Risks / Trade-offs

- **MSSQL `TOP N` placement** → SQLAlchemy handles it, but ORDER BY interaction requires `ORDER BY` to be present for MSSQL `TOP` to be deterministic. The compiler will always emit an `ORDER BY (SELECT NULL)` sentinel when `order_by` is empty and `limit` is set on MSSQL. Mitigation: add a golden test for limit-without-sort on MSSQL.

- **`CatalogView.sa_table()` returns `Any` in domain** → Type-checker cannot verify column resolution in the compiler. Mitigation: the compiler tests provide column-level coverage; type safety is enforced in the adapter layer where `Table` is a concrete type.

- **Golden SQL string fragility** → SQLAlchemy may reformat SQL across minor versions. Mitigation: normalise whitespace in assertions (strip + collapse); pin SQLAlchemy version in `pyproject.toml`.

## Open Questions

*(none — all design decisions resolved above)*
