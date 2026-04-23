# integration-test-suite Specification

## Purpose
TBD - created by archiving change qa-hardening. Update Purpose after archive.
## Requirements
### Requirement: Full compile→execute pipeline is verified against a real Postgres database
An integration test SHALL stand up a Postgres testcontainer, reflect the schema, compile a `QuerySpec`, execute it via `POST /queries/execute`, and assert the returned rows match the known seed data. The test MUST use a `TestClient(create_app(...))` to exercise the full HTTP stack. The Postgres container MUST be session-scoped (one container per test session).

#### Scenario: Single-table projection returns seeded rows
- **WHEN** a `QuerySpec` selecting two columns from a seeded table is posted to `/queries/execute`
- **THEN** HTTP 200 is returned and `rows` contains exactly the seeded records

#### Scenario: JOIN projection returns joined rows
- **WHEN** a `QuerySpec` with one `JoinDef` is posted and both tables are seeded
- **THEN** HTTP 200 is returned and rows reflect the correct join result

#### Scenario: Filter reduces result set
- **WHEN** a `QuerySpec` with a `FilterGroup` predicate is posted
- **THEN** only rows matching the predicate are returned

#### Scenario: Aggregate with GROUP BY returns one row per group
- **WHEN** a `QuerySpec` with `SelectField(kind="agg", func="count")` and `group_by` is posted
- **THEN** the returned rows contain one entry per distinct group value

#### Scenario: Audit event is recorded on success
- **WHEN** the pipeline completes successfully
- **THEN** `FakeAuditLog.events` contains exactly one event with `outcome="success"` and the correct `row_count`

---

### Requirement: Dataset save→retrieve→execute round-trip is verified
An integration test SHALL save a `DatasetDefinition` via `POST /datasets`, retrieve it via `GET /datasets/{id}`, and execute the retrieved spec via `POST /queries/execute` against a real Postgres database. The full spec MUST survive the save→retrieve round-trip unchanged.

#### Scenario: Retrieved spec produces identical SQL to the original
- **WHEN** the spec from `GET /datasets/{id}` is compiled
- **THEN** the resulting SQL is identical to compiling the original `QuerySpec` directly

---

### Requirement: Policy rejection flows return structured 422 responses
Integration tests SHALL verify that the closed-by-default allowlist, duplicate alias detection, and row-cap enforcement each produce HTTP 422 with the correct `error_code` without any database round-trip.

#### Scenario: Unknown connection_id returns 422 POLICY_VIOLATION
- **WHEN** a `QuerySpec` references a `connection_id` not in the allowlist
- **THEN** HTTP 422 with `error_code="POLICY_VIOLATION"` is returned before any catalog lookup

#### Scenario: Row cap exceeded returns 422 POLICY_VIOLATION
- **WHEN** the source table contains more than `_MAX_RESULT_ROWS` rows and no limit is set below the cap
- **THEN** HTTP 422 with `error_code="POLICY_VIOLATION"` is returned after execution

---

### Requirement: MSSQL SQL-string parity is verified without a live MSSQL instance
Tests SHALL compile a representative set of `QuerySpec` instances for `Dialect.mssql` and assert dialect-specific SQL patterns without a live MSSQL database. All assertions MUST use normalised (whitespace-collapsed) SQL strings.

#### Scenario: LIMIT replaced by SELECT TOP
- **WHEN** a `QuerySpec` with `limit=50` is compiled for `Dialect.mssql`
- **THEN** the SQL contains `TOP` and does not contain `LIMIT`

#### Scenario: Column identifiers use bracket quoting
- **WHEN** any `QuerySpec` is compiled for `Dialect.mssql`
- **THEN** column references use `[bracket]` quoting rather than `"double-quote"` style

#### Scenario: INNER JOIN renders without OUTER keyword
- **WHEN** a `QuerySpec` with `JoinDef(type="inner")` is compiled for `Dialect.mssql`
- **THEN** the SQL contains `JOIN` and does not contain `OUTER`

---

### Requirement: Edge cases in SQL generation are exercised
Unit/integration tests SHALL cover the boundary conditions of every compiler feature that is parameterised by input values.

#### Scenario: IS NULL predicate emits no bound parameter
- **WHEN** a `Predicate(op="is_null")` is compiled
- **THEN** the SQL contains `IS NULL` and the `params` dict does not gain an extra entry for that predicate

#### Scenario: IN predicate with three values binds all three
- **WHEN** a `Predicate(op="in", right=(...three ValueRef...))` is compiled
- **THEN** the SQL contains `IN (:p1, :p2, :p3)` and all three values appear in `params`

#### Scenario: Zero-row result returns empty rows list
- **WHEN** a query executes against a table that has no matching rows
- **THEN** `rows` is `[]`, `row_count` is `0`, and `columns` is `[]`

#### Scenario: Exactly three joins compile without PolicyViolation
- **WHEN** a `QuerySpec` has exactly `_MAX_JOINS` joins
- **THEN** `CompileQueryUseCase.execute()` succeeds without raising

#### Scenario: Nested OR inside AND filter group compiles correctly
- **WHEN** a `FilterGroup(op="and")` contains a nested `FilterGroup(op="or")`
- **THEN** the compiled SQL contains `(... OR ...)` wrapped inside the outer `AND` clause

