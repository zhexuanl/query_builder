## ADDED Requirements

### Requirement: POST /queries/execute accepts a QuerySpec and returns rows
The endpoint SHALL accept `POST /queries/execute` with a JSON body matching the `QuerySpecRequest` schema and return a `QueryResultResponse` on success with HTTP 200. The route MUST delegate all business logic to `ExecuteQueryUseCase`; it MUST NOT contain compilation or validation logic itself.

#### Scenario: Valid request returns 200 with rows
- **WHEN** `POST /queries/execute` is called with a valid `QuerySpecRequest` body
- **THEN** HTTP 200 is returned with a `QueryResultResponse` containing `columns`, `rows`, and `row_count`

#### Scenario: PolicyViolation returns 422
- **WHEN** the use case raises `PolicyViolation`
- **THEN** HTTP 422 is returned with the violation message in the response body

#### Scenario: CompilationError returns 422
- **WHEN** the use case raises `CompilationError`
- **THEN** HTTP 422 is returned with the error message in the response body

#### Scenario: CatalogMiss returns 422
- **WHEN** the use case raises `CatalogMiss`
- **THEN** HTTP 422 is returned with the error message in the response body

#### Scenario: SourceConnectionError returns 502
- **WHEN** the use case raises `SourceConnectionError`
- **THEN** HTTP 502 is returned; the internal error detail MUST NOT be exposed to the client

---

### Requirement: QuerySpecRequest mirrors QuerySpec structure as a Pydantic model
`QuerySpecRequest` SHALL be a Pydantic v2 model that captures `connection_id`, `source`, `joins`, `select`, `filters`, `sort`, `limit`, and `dialect`. It MUST be validated by FastAPI before the route handler is invoked. Invalid payloads MUST result in HTTP 422 from FastAPI's default validation.

#### Scenario: Missing required field returns 422
- **WHEN** the request body omits `connection_id` or `source`
- **THEN** HTTP 422 is returned by FastAPI validation before the use case is called

#### Scenario: Unknown dialect value returns 422
- **WHEN** the request body contains an unrecognised `dialect` string
- **THEN** HTTP 422 is returned by FastAPI validation

---

### Requirement: QueryResultResponse exposes columns, rows, and row_count
`QueryResultResponse` SHALL be a Pydantic v2 model with `columns: list[str]`, `rows: list[dict[str, Any]]`, and `row_count: int`. `columns` MUST be derived from the keys of the first row (or empty if no rows returned).

#### Scenario: Response shape matches spec labels
- **WHEN** the use case returns rows with keys matching `SelectField.label` values
- **THEN** `columns` contains those labels in consistent order and `rows` contains the raw dicts

#### Scenario: Empty result set returns empty columns and rows
- **WHEN** the use case returns an empty list
- **THEN** `columns` is `[]`, `rows` is `[]`, and `row_count` is `0`

---

### Requirement: create_app() wires all dependencies and registers the route
The `create_app()` factory function in `infrastructure/app.py` SHALL return a fully-configured `FastAPI` application with `POST /queries/execute` registered and all use-case dependencies injected. It MUST accept a configuration object so that test instances can inject in-memory fakes.

#### Scenario: App factory returns a FastAPI instance
- **WHEN** `create_app()` is called with a valid configuration
- **THEN** a `FastAPI` instance is returned with the `/queries/execute` route registered
