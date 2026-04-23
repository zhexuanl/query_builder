## MODIFIED Requirements

### Requirement: POST /queries/execute accepts a QuerySpec and returns rows
The endpoint SHALL accept `POST /queries/execute` with a JSON body matching the `QuerySpecRequest` schema and return a `QueryResultResponse` on success with HTTP 200. The route MUST delegate all business logic to `ExecuteQueryUseCase`; it MUST NOT contain compilation or validation logic itself.

#### Scenario: Valid request returns 200 with rows
- **WHEN** `POST /queries/execute` is called with a valid `QuerySpecRequest` body including `caller_id`
- **THEN** HTTP 200 is returned with a `QueryResultResponse` containing `columns`, `rows`, and `row_count`

#### Scenario: PolicyViolation returns 422 with error_code
- **WHEN** the use case raises `PolicyViolation`
- **THEN** HTTP 422 is returned with `{"error_code": "POLICY_VIOLATION", "detail": "<message>"}`

#### Scenario: CompilationError returns 422 with error_code
- **WHEN** the use case raises `CompilationError`
- **THEN** HTTP 422 is returned with `{"error_code": "COMPILATION_ERROR", "detail": "<message>"}`

#### Scenario: CatalogMiss returns 422 with error_code
- **WHEN** the use case raises `CatalogMiss`
- **THEN** HTTP 422 is returned with `{"error_code": "CATALOG_MISS", "detail": "<message>"}`

#### Scenario: SourceConnectionError returns 502 with opaque error_code
- **WHEN** the use case raises `SourceConnectionError`
- **THEN** HTTP 502 is returned with `{"error_code": "SOURCE_UNAVAILABLE"}`; the internal error detail MUST NOT be exposed

---

### Requirement: QuerySpecRequest requires caller_id
`QuerySpecRequest` SHALL include a mandatory `caller_id: str` field in addition to all M4 fields. Requests missing `caller_id` MUST result in HTTP 422 from FastAPI validation before the use case is called.

#### Scenario: Missing caller_id returns 422
- **WHEN** the request body omits `caller_id`
- **THEN** HTTP 422 is returned by FastAPI validation before the use case is called

#### Scenario: caller_id is passed to the use case
- **WHEN** a valid request with `caller_id` is received
- **THEN** `ExecuteQueryUseCase.execute()` is called with the exact `caller_id` value from the request
