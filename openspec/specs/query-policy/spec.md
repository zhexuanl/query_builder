## Purpose

Define and enforce governance rules on `QuerySpec` objects before compilation, ensuring structural validity, row-limit safety, and per-connection table entitlements.

## Requirements

### Requirement: Policy validation rejects structurally invalid QuerySpecs
The `IQueryPolicy` port SHALL expose a single `validate(spec, catalog)` method. Implementations MUST raise `PolicyViolation` for any rule violation and MUST return `None` on success. `PolicyViolation` messages MUST identify the violated rule and the offending value.

#### Scenario: Too many joins rejected
- **WHEN** a `QuerySpec` has more than 3 `JoinDef` entries in `joins`
- **THEN** `PolicyViolation` is raised with a message referencing the join count limit

#### Scenario: Three joins accepted
- **WHEN** a `QuerySpec` has exactly 3 `JoinDef` entries
- **THEN** `validate()` returns `None` without raising

#### Scenario: Missing row limit rejected
- **WHEN** `QuerySpec.limit` is `None`
- **THEN** `PolicyViolation` is raised requiring an explicit limit

#### Scenario: Limit exceeding maximum rejected
- **WHEN** `QuerySpec.limit` is greater than 10 000
- **THEN** `PolicyViolation` is raised referencing the maximum allowed limit

#### Scenario: Limit of exactly 10 000 accepted
- **WHEN** `QuerySpec.limit` is 10 000
- **THEN** `validate()` returns `None` without raising

#### Scenario: Duplicate output labels rejected
- **WHEN** two `SelectField` entries in `spec.select` share the same `label`
- **THEN** `PolicyViolation` is raised identifying the duplicate label

#### Scenario: Duplicate alias across source and joins rejected
- **WHEN** a `JoinDef` in `spec.joins` has the same `alias` as `spec.source`
- **THEN** `PolicyViolation` is raised identifying the conflicting alias

---

### Requirement: Table allowlist policy enforces per-connection data entitlements (closed-by-default)
`TableAllowlistPolicy` SHALL reject any `QuerySpec` that references a table not in the approved set for its `connection_id`. If `connection_id` is absent from the allowlist mapping, `PolicyViolation` MUST be raised (closed-by-default). The open-by-default behaviour is removed.

#### Scenario: Unapproved source table rejected
- **WHEN** `spec.source.table` is not in the allowlist for `spec.connection_id`
- **THEN** `PolicyViolation` is raised naming the unapproved table

#### Scenario: Unapproved join table rejected
- **WHEN** any `JoinDef.table` in `spec.joins` is not in the allowlist
- **THEN** `PolicyViolation` is raised naming the unapproved table

#### Scenario: All tables approved — passes
- **WHEN** every table in `spec.source` and `spec.joins` is in the allowlist
- **THEN** `validate()` returns `None` without raising

#### Scenario: Unknown connection_id — closed by default
- **WHEN** `spec.connection_id` has no entry in the allowlist mapping
- **THEN** `PolicyViolation` is raised with a message identifying the unknown connection

---

### Requirement: Multiple policies are evaluated in sequence
The use case SHALL apply each `IQueryPolicy` in the order they appear in its policy list. If any policy raises `PolicyViolation`, evaluation stops immediately and the violation propagates to the caller.

#### Scenario: First failing policy short-circuits
- **WHEN** the first policy raises `PolicyViolation` and a second policy would also fail
- **THEN** only the first `PolicyViolation` is raised; the second policy is not evaluated
