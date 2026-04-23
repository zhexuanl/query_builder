## ADDED Requirements

### Requirement: Compile single-table projection to dialect SQL
The compiler SHALL translate a `QuerySpec` with a single source table and one or
more column projections into a `SELECT … FROM … AS …` statement for the target
dialect, returning a `CompiledQuery` with a SQL template string and an empty
bound-param dict.

#### Scenario: Single-table projection — Postgres
- **WHEN** a `QuerySpec` selects two columns from a source table with no joins, filters, or aggregates and dialect is `postgres`
- **THEN** the compiled SQL is `SELECT t0.col_a AS col_a, t0.col_b AS col_b FROM table_name AS t0` with no bound parameters

#### Scenario: Single-table projection — MSSQL
- **WHEN** the same `QuerySpec` is compiled with dialect `mssql`
- **THEN** the SQL is semantically identical but uses MSSQL quoting conventions (brackets) with no `LIMIT` clause

---

### Requirement: Compile filter predicates to a parameterised WHERE clause
The compiler SHALL translate a `FilterGroup` into a `WHERE` clause.  All
`ValueRef` operands MUST be emitted as bound parameters, never as inlined
literals.  `ColumnRef` operands MUST be emitted as qualified column references.
`ParamRef` operands MUST be emitted as named placeholders.

#### Scenario: AND filter with scalar equality — Postgres
- **WHEN** a `QuerySpec` has a `FilterGroup(op="and")` containing two `Predicate` nodes using `=` with `ValueRef` right-hand sides and dialect is `postgres`
- **THEN** the SQL contains `WHERE t0.col_a = :param_1 AND t0.col_b = :param_2` and the params dict maps those keys to the literal values

#### Scenario: OR filter group
- **WHEN** a `QuerySpec` has a `FilterGroup(op="or")` with two predicates
- **THEN** the SQL contains `WHERE (t0.col_a = :param_1 OR t0.col_b = :param_2)`

#### Scenario: IS NULL predicate
- **WHEN** a `Predicate` uses op `is_null`
- **THEN** the SQL renders `t0.col IS NULL` with no bound parameter for that predicate

#### Scenario: IN predicate with value tuple
- **WHEN** a `Predicate` uses op `in` with a tuple of three `ValueRef` values
- **THEN** the SQL renders `t0.col IN (:param_1, :param_2, :param_3)` with the three values bound

---

### Requirement: Compile LEFT JOIN to a JOIN … ON clause
The compiler SHALL translate each `JoinDef` in `QuerySpec.joins` into a SQL
`LEFT JOIN` or `INNER JOIN` clause.  The join `on` predicates MUST be rendered
as column-to-column comparisons (no value binding required for FK joins).

#### Scenario: Left join on a foreign key column
- **WHEN** a `QuerySpec` has one `JoinDef(type="left")` with a single `Predicate(op="=", left=ColumnRef(...), right=ColumnRef(...))`
- **THEN** the SQL contains `LEFT OUTER JOIN other_table AS t1 ON t0.id = t1.fk_id`

#### Scenario: Inner join
- **WHEN** a `JoinDef` has `type="inner"`
- **THEN** the SQL contains `JOIN … ON …` (no `OUTER` keyword for MSSQL; `INNER JOIN` for Postgres)

---

### Requirement: Compile aggregates and GROUP BY
The compiler SHALL translate `SelectField(kind="agg")` entries into aggregate
function calls and emit a `GROUP BY` clause for all `ColumnRef` entries in
`QuerySpec.group_by`.  Supported functions: `count`, `count_distinct`, `sum`,
`avg`, `min`, `max`.

#### Scenario: COUNT with GROUP BY
- **WHEN** a `QuerySpec` selects one column field and one `SelectField(kind="agg", func="count")` and `group_by` contains the column
- **THEN** the SQL contains `SELECT t0.col AS col, count(t1.id) AS total FROM … GROUP BY t0.col`

#### Scenario: count_distinct
- **WHEN** `SelectField.func` is `"count_distinct"`
- **THEN** the SQL renders `count(DISTINCT t1.id)` (Postgres-style) or dialect-equivalent

---

### Requirement: Compile ORDER BY and LIMIT
The compiler SHALL translate `QuerySpec.order_by` into an `ORDER BY` clause
referencing output labels and `QuerySpec.limit` into a row-count restriction.
The row-count restriction MUST use `LIMIT N` for Postgres and `SELECT TOP N` for
MSSQL, emitted by SQLAlchemy's dialect — no manual string construction.

#### Scenario: ORDER BY descending with LIMIT — Postgres
- **WHEN** a `QuerySpec` has `order_by=(SortDef(label="total", direction="desc"),)` and `limit=100` and dialect is `postgres`
- **THEN** the SQL ends with `ORDER BY total DESC LIMIT :param_1` (or equivalent rendered integer)

#### Scenario: LIMIT on MSSQL emits SELECT TOP
- **WHEN** a `QuerySpec` has `limit=100` and dialect is `mssql`
- **THEN** the SQL begins with `SELECT TOP [100]` or `SELECT TOP 100` (SQLAlchemy dialect output) and contains no `LIMIT` keyword

#### Scenario: No limit
- **WHEN** `QuerySpec.limit` is `None`
- **THEN** no `LIMIT` or `TOP` clause appears in the compiled SQL for either dialect

---

### Requirement: Return bound params as a dict keyed by placeholder name
The compiler SHALL return all bound values in a `dict[str, object]` paired with
the SQL template string.  The dict keys MUST correspond exactly to the
placeholder names in the SQL template.

#### Scenario: Params dict matches placeholders
- **WHEN** the compiled SQL contains `:status` and `:from_date` placeholders
- **THEN** the returned `params` dict has exactly the keys `"status"` and `"from_date"` mapped to the correct values

---

### Requirement: Compilation fails fast on unknown catalog reference
The compiler SHALL raise `CompilationError` immediately if a `ColumnRef` in the
spec references a table or column that is absent from the provided `CatalogView`.

#### Scenario: Unknown table alias raises CompilationError
- **WHEN** a `QuerySpec` references alias `"x"` but `CatalogView` contains no table for that alias
- **THEN** the compiler raises `CompilationError` before producing any SQL output

#### Scenario: Unknown column raises CompilationError
- **WHEN** a `ColumnRef.name` does not exist on the resolved table in `CatalogView`
- **THEN** the compiler raises `CompilationError` with a message identifying the missing column

---

## ADDED Requirements

### Requirement: SqlAlchemyCoreCompiler supports an optional SQLGlot qualify pass
`SqlAlchemyCoreCompiler` SHALL accept `enable_sqlglot_qualify: bool = False` at construction. When `True`, the adapter SHALL pass the emitted SQL string through SQLGlot's qualify rewriter after each `compile()` call. Qualify errors SHALL be raised as `CompilationError`. The `IQueryCompiler` port contract is unchanged.

#### Scenario: Compiler constructed without flag behaves identically to M1–M5
- **WHEN** `SqlAlchemyCoreCompiler()` is constructed without `enable_sqlglot_qualify`
- **THEN** all existing M1 golden tests pass without modification

#### Scenario: Qualify errors from SQLGlot raise CompilationError
- **WHEN** `SqlAlchemyCoreCompiler(enable_sqlglot_qualify=True).compile(spec, catalog, dialect)` produces SQL that SQLGlot cannot qualify
- **THEN** `CompilationError` is raised with a message from SQLGlot

#### Scenario: Successful qualify does not alter the returned SQL
- **WHEN** the qualify pass runs without error
- **THEN** the `CompiledQuery.sql` value is the original SQLAlchemy-emitted string (not SQLGlot's re-rendered output) to preserve dialect fidelity
