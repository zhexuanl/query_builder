## MODIFIED Requirements

### Requirement: Table allowlist policy enforces per-connection data entitlements
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
