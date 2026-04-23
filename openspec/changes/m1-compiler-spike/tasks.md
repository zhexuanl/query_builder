## 1. Domain ports

- [x] 1.1 Create `domain/interfaces/__init__.py` (empty)
- [x] 1.2 Create `domain/interfaces/catalog_repository.py` — define abstract `CatalogView` (with `sa_table(table_name) -> Any` and `column(alias, name) -> Any`) and `ICatalogRepository` ABC with `view_for(connection_id, table_names) -> CatalogView`
- [x] 1.3 Create `domain/interfaces/query_compiler.py` — define `CompiledQuery(NamedTuple)` with `(sql, params, dialect)` and `IQueryCompiler` ABC with synchronous `compile(spec, catalog, dialect) -> CompiledQuery`

Done signal: `from domain.interfaces.query_compiler import IQueryCompiler, CompiledQuery` imports cleanly with no framework dependencies.

## 2. SQLAlchemy dependency

- [x] 2.1 Add `sqlalchemy>=2.0` to `[project.dependencies]` in `backend/pyproject.toml`
- [x] 2.2 Create `adapters/__init__.py` and `adapters/compilers/__init__.py` (both empty)

Done signal: `python -c "import sqlalchemy"` succeeds inside the backend virtualenv.

## 3. In-memory catalog adapter (test helper)

- [x] 3.1 Create `tests/fakes/in_memory_catalog.py` — implement `InMemoryCatalogView(CatalogView)` that holds a `dict[str, sqlalchemy.Table]` keyed by alias; `sa_table(alias)` raises `CatalogMiss` if the key is absent; `column(alias, name)` raises `CatalogMiss` if the column is absent on the resolved table
- [x] 3.2 Add fixture helper `make_catalog(*table_defs)` that constructs an `InMemoryCatalogView` from a list of `(alias, table_name, [column_names])` tuples using `sqlalchemy.Table` with a throwaway `MetaData`
- [x] 3.3 Create `tests/fakes/__init__.py` (empty)

Done signal: unit test can construct `InMemoryCatalogView` and call `sa_table()` without any DB engine.

## 4. Core compiler implementation

- [x] 4.1 Create `adapters/compilers/sqlalchemy_core_compiler.py` with `SqlAlchemyCoreCompiler(IQueryCompiler)`
- [x] 4.2 Implement `_render_select(spec, aliases)` — maps each `SelectField` to a SQLAlchemy `Label`; `kind="column"` → `table_col.label(label)`; `kind="agg"` → `sa.func.<name>(col).label(label)` (special-case `count_distinct` → `sa.func.count(col.distinct())`)
- [x] 4.3 Implement `_render_from(spec, catalog)` — resolves source table via `catalog.sa_table()`; chains `.join()` / `.outerjoin()` for each `JoinDef`
- [x] 4.4 Implement `_render_predicate(pred, catalog)` — maps each `Predicate` op to a SQLAlchemy expression; `ValueRef` → `sa.bindparam(unique_name, value)`; `ParamRef` → `sa.bindparam(name)`; `ColumnRef` → `catalog.column(alias, name)`
- [x] 4.5 Implement `_render_filter(group_or_pred, catalog)` — recursive; `FilterGroup(op="and")` → `sa.and_(...)`; `FilterGroup(op="or")` → `sa.or_(...)`
- [x] 4.6 Implement `compile()` — assembles `sa.select()`, applies `.where()`, `.group_by()`, `.order_by()`, `.limit()`; calls `stmt.compile(dialect=_sa_dialect(dialect), compile_kwargs={"render_postcompile": True})`; returns `CompiledQuery(sql=str(compiled), params=dict(compiled.params), dialect=dialect)`
- [x] 4.7 Map `CompilationError` on `CatalogMiss` — wrap any `CatalogMiss` raised by the catalog inside a `CompilationError` at the `compile()` boundary

Done signal: `SqlAlchemyCoreCompiler().compile(spec, catalog, Dialect.postgres)` returns a `CompiledQuery` for a minimal single-table spec.

## 5. Golden tests

- [x] 5.1 Create `tests/unit/compilers/__init__.py` (empty) and `tests/unit/compilers/test_sqlalchemy_core_compiler.py`
- [x] 5.2 Write fixture `spec_single_table` — one source table `customers` aliased `c`, select `customer_id` and `email`, no filters, limit 100; assert Postgres SQL and MSSQL SQL (including `TOP 100`)
- [x] 5.3 Write fixture `spec_filter_and` — same source, `where` is `FilterGroup(op="and")` with `status = ValueRef("active")` and `age >= ValueRef(18)`; assert WHERE clause and bound params for both dialects
- [x] 5.4 Write fixture `spec_left_join_agg` — `customers c` LEFT JOIN `transactions t` on `c.customer_id = t.customer_id`; select `c.country` (column) and `count(t.id)` (agg); `group_by=(ColumnRef("c","country"),)`; assert GROUP BY and JOIN in SQL for both dialects
- [x] 5.5 Write fixture `spec_param_ref` — filter uses `ParamRef(name="status")` on the right-hand side; assert the SQL placeholder is present and `params["status"]` is None (param is unbound until caller provides value)
- [x] 5.6 Write fixture `spec_limit_no_sort_mssql` — `limit=50`, no `order_by`; assert MSSQL output has `SELECT TOP 50` and no `LIMIT` keyword, Postgres has `LIMIT`
- [x] 5.7 Write `test_compilation_error_unknown_alias` — `QuerySpec` references alias `"x"` not in `InMemoryCatalogView`; assert `CompilationError` is raised

Done signal: `pytest tests/unit/compilers/ -v` — all tests pass for both dialects.

## 6. Normalise SQL comparison helper

- [x] 6.1 Add `normalize_sql(sql: str) -> str` in `tests/helpers.py` — strips leading/trailing whitespace and collapses internal whitespace runs to single spaces; used in all golden assertions to avoid version-formatting fragility

Done signal: `normalize_sql("SELECT  foo  FROM bar ")` returns `"SELECT foo FROM bar"`.
