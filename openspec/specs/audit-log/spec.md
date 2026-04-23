## ADDED Requirements

### Requirement: IAuditLog port appends structured execution events
The `IAuditLog` port SHALL expose `append(event: AuditEvent) -> None`. Implementations MUST NOT raise exceptions — log failures MUST be swallowed (logged to stderr at most) so that audit failures never surface to the API caller. `AuditEvent` SHALL be a frozen dataclass in `domain/` with fields: `caller_id: str`, `connection_id: str`, `table_names: frozenset[str]`, `dialect: str`, `outcome: Literal[...]`, `row_count: int | None`, `duration_ms: int`, `timestamp: datetime`.

#### Scenario: append does not raise on success
- **WHEN** `append()` is called with a valid `AuditEvent`
- **THEN** the method returns `None` without raising

#### Scenario: append does not propagate internal failures
- **WHEN** the underlying storage mechanism raises an exception
- **THEN** `append()` swallows the exception and returns `None`

---

### Requirement: AuditEvent outcome field covers all terminal states
The `outcome` field SHALL be one of: `"success"`, `"policy_violation"`, `"compilation_error"`, `"catalog_miss"`, `"source_error"`, `"row_cap_exceeded"`. No other values are permitted. `row_count` MUST be `None` for all non-`"success"` outcomes.

#### Scenario: Success event has non-None row_count
- **WHEN** an `AuditEvent` with `outcome="success"` is created
- **THEN** `row_count` is an integer ≥ 0

#### Scenario: Failure event has None row_count
- **WHEN** an `AuditEvent` with any non-success outcome is created
- **THEN** `row_count` is `None`

---

### Requirement: InMemoryAuditLog accumulates events for test inspection
`InMemoryAuditLog` SHALL store all appended `AuditEvent` instances in a `events: list[AuditEvent]` attribute, accessible for test assertions. It MUST implement `IAuditLog`.

#### Scenario: Events are retrievable after append
- **WHEN** `append(event)` is called N times
- **THEN** `audit_log.events` contains exactly N events in append order

---

### Requirement: JsonStdoutAuditLog emits one JSON line per event
`JsonStdoutAuditLog` SHALL write each `AuditEvent` as a single-line JSON object to stdout. The JSON MUST include all `AuditEvent` fields. `timestamp` MUST be serialized as an ISO-8601 string. `table_names` MUST be serialized as a sorted JSON array.

#### Scenario: Single JSON line emitted per event
- **WHEN** `append(event)` is called
- **THEN** exactly one line is written to stdout, parseable as JSON with all AuditEvent fields present
