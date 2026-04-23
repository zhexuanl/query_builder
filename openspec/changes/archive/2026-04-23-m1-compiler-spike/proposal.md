## Why

M0 established the domain layer (QuerySpec AST + value objects). M1 proves the load-bearing technical risk: can that AST compile to correct, parameterised SQL for both Postgres and SQL Server via SQLAlchemy Core? Without this proof, the rest of the stack (executor, API, UI) has no verified foundation.

## What Changes

- Introduce the `IQueryCompiler` port and `CompiledQuery` result type in `domain/interfaces/`
- Implement `SqlAlchemyCoreCompiler` in `adapters/compilers/` — translates `QuerySpec` → SQLAlchemy `Select` → dialect SQL + bound params
- Add an `InMemoryCatalogRepository` test adapter providing table/column metadata without a live DB
- Write 5 golden-test fixtures (single-table, filters, left join + aggregate, multi-join, param substitution) asserting exact SQL per dialect (Postgres + MSSQL)
- Stub `ICatalogRepository` port with the minimum surface needed by the compiler

## Capabilities

### New Capabilities

- `query-compiler`: Translates a `QuerySpec` AST into a `CompiledQuery` (dialect SQL string + bound-param dict) using SQLAlchemy Core. Supports Postgres and MSSQL. Covers: column projection, left/inner joins, AND/OR filter trees, aggregates with GROUP BY, ORDER BY, LIMIT/TOP.

### Modified Capabilities

*(none — no existing spec-level requirements change)*

## Non-goals

- Execution against a real database (M4)
- Schema reflection from source DBs (M2)
- Policy/validation layer (M3)
- SQLGlot lint pass (M6)
- Any dialect beyond Postgres + MSSQL

## Impact

- **New files**: `domain/interfaces/query_compiler.py`, `domain/interfaces/catalog_repository.py` (stub), `adapters/compilers/sqlalchemy_core_compiler.py`, `tests/unit/compilers/test_sqlalchemy_core_compiler.py`, `tests/fixtures/query_specs/*.json`
- **Dependencies added**: `sqlalchemy>=2.0` to `pyproject.toml`
- **No breaking changes** to the domain value objects committed in M0
