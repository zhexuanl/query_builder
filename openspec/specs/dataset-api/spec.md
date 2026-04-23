## ADDED Requirements

### Requirement: POST /datasets saves a named QuerySpec definition
The endpoint SHALL accept `POST /datasets` with a `SaveDatasetRequest` body and return `DatasetResponse` with HTTP 201 on success. The route MUST delegate to `SaveDatasetUseCase`. `dataset_id` MUST be generated server-side (UUID4).

#### Scenario: Valid request returns 201 with dataset_id
- **WHEN** `POST /datasets` is called with a valid `SaveDatasetRequest`
- **THEN** HTTP 201 is returned with a `DatasetResponse` containing the generated `dataset_id`, `name`, and `created_at`

#### Scenario: PolicyViolation returns 422
- **WHEN** the spec fails policy validation
- **THEN** HTTP 422 is returned with `{"error_code": "POLICY_VIOLATION", "detail": "<message>"}`

#### Scenario: CatalogMiss returns 422
- **WHEN** the catalog cannot resolve the spec's tables
- **THEN** HTTP 422 is returned with `{"error_code": "CATALOG_MISS", "detail": "<message>"}`

---

### Requirement: GET /datasets/{dataset_id} retrieves a saved dataset
The endpoint SHALL accept `GET /datasets/{dataset_id}` and return `DatasetResponse` with HTTP 200. It MUST raise HTTP 404 with `error_code: "DATASET_NOT_FOUND"` for unknown IDs.

#### Scenario: Known dataset_id returns 200
- **WHEN** `GET /datasets/{dataset_id}` is called with a registered ID
- **THEN** HTTP 200 is returned with the full `DatasetResponse`

#### Scenario: Unknown dataset_id returns 404
- **WHEN** `GET /datasets/{dataset_id}` is called with an unregistered ID
- **THEN** HTTP 404 is returned with `{"error_code": "DATASET_NOT_FOUND"}`

---

### Requirement: GET /datasets lists all datasets with optional connection_id filter
The endpoint SHALL accept `GET /datasets` with an optional `?connection_id=` query parameter and return `list[DatasetResponse]` with HTTP 200. An empty list is a valid response.

#### Scenario: No filter returns all datasets
- **WHEN** `GET /datasets` is called with no query parameters
- **THEN** HTTP 200 is returned with all saved datasets

#### Scenario: connection_id filter returns subset
- **WHEN** `GET /datasets?connection_id=conn-a` is called
- **THEN** HTTP 200 is returned with only datasets whose `connection_id == "conn-a"`

---

### Requirement: DELETE /datasets/{dataset_id} removes a saved dataset
The endpoint SHALL accept `DELETE /datasets/{dataset_id}` and return HTTP 204 on success. It MUST return HTTP 404 with `error_code: "DATASET_NOT_FOUND"` for unknown IDs.

#### Scenario: Known dataset_id returns 204
- **WHEN** `DELETE /datasets/{dataset_id}` is called with a registered ID
- **THEN** HTTP 204 is returned and the dataset is no longer retrievable

#### Scenario: Unknown dataset_id returns 404
- **WHEN** `DELETE /datasets/{dataset_id}` is called with an unregistered ID
- **THEN** HTTP 404 is returned with `{"error_code": "DATASET_NOT_FOUND"}`

---

### Requirement: DatasetResponse exposes all DatasetDefinition fields except the full spec
`DatasetResponse` SHALL be a Pydantic v2 model with `dataset_id: UUID`, `name: str`, `description: str`, `connection_id: str`, `created_at: datetime`, `created_by: str`. The full `spec: QuerySpec` MUST also be included in the response for `GET` endpoints but MAY be omitted from `POST` list responses.

#### Scenario: GET response includes full spec
- **WHEN** `GET /datasets/{dataset_id}` returns successfully
- **THEN** the response body contains the full `spec` object matching the saved `QuerySpec`
