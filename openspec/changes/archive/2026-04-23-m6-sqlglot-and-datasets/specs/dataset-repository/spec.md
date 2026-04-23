## ADDED Requirements

### Requirement: DatasetDefinition captures a named QuerySpec snapshot
`DatasetDefinition` SHALL be a domain entity (not frozen) with fields: `dataset_id: UUID`, `name: str`, `description: str`, `connection_id: str`, `spec: QuerySpec`, `created_at: datetime`, `created_by: str`. The `spec` field MUST be the frozen `QuerySpec` value at save time. `dataset_id` MUST be assigned by the caller (typically `uuid4()`).

#### Scenario: DatasetDefinition stores the full QuerySpec
- **WHEN** a `DatasetDefinition` is created with a `QuerySpec`
- **THEN** `dataset.spec` is identical to the original `QuerySpec` (by value equality)

---

### Requirement: IDatasetRepository provides CRUD operations for DatasetDefinition
The `IDatasetRepository` port SHALL expose: `save(dataset: DatasetDefinition) -> None`, `get(dataset_id: UUID) -> DatasetDefinition`, `list(connection_id: str | None = None) -> list[DatasetDefinition]`, `delete(dataset_id: UUID) -> None`. `get()` and `delete()` MUST raise `DatasetNotFound` for unknown `dataset_id`. `save()` on an existing `dataset_id` MUST overwrite (upsert semantics). `list()` with `connection_id=None` MUST return all datasets.

#### Scenario: save then get returns the same dataset
- **WHEN** `save(dataset)` is called followed by `get(dataset.dataset_id)`
- **THEN** the returned `DatasetDefinition` is equal to the saved one

#### Scenario: get with unknown dataset_id raises DatasetNotFound
- **WHEN** `get(unknown_id)` is called
- **THEN** `DatasetNotFound` is raised identifying the unknown ID

#### Scenario: list with no filter returns all datasets
- **WHEN** `list()` is called with no arguments after saving N datasets
- **THEN** a list of N `DatasetDefinition` instances is returned

#### Scenario: list filtered by connection_id returns subset
- **WHEN** `list(connection_id="conn-a")` is called after saving datasets for multiple connections
- **THEN** only datasets whose `connection_id == "conn-a"` are returned

#### Scenario: delete removes the dataset
- **WHEN** `delete(dataset.dataset_id)` is called after `save(dataset)`
- **THEN** `get(dataset.dataset_id)` subsequently raises `DatasetNotFound`

#### Scenario: delete with unknown dataset_id raises DatasetNotFound
- **WHEN** `delete(unknown_id)` is called
- **THEN** `DatasetNotFound` is raised

#### Scenario: save overwrites existing dataset
- **WHEN** `save(dataset)` is called twice with the same `dataset_id` but different `name`
- **THEN** `get(dataset.dataset_id).name` returns the second `name`

---

### Requirement: SaveDatasetUseCase validates the spec before persisting
`SaveDatasetUseCase.execute(dataset)` SHALL call `CompileQueryUseCase.execute()` in dry-run mode (compile only, no SQL execution) to validate the spec passes all policies and catalog checks. Only if validation succeeds SHALL `IDatasetRepository.save()` be called. `PolicyViolation`, `CompilationError`, and `CatalogMiss` MUST propagate unchanged without saving.

#### Scenario: Valid spec is saved
- **WHEN** `execute(dataset)` is called with a spec that compiles without error
- **THEN** `IDatasetRepository.save()` is called once with the dataset

#### Scenario: PolicyViolation prevents save
- **WHEN** the spec fails policy validation
- **THEN** `PolicyViolation` propagates and `IDatasetRepository.save()` is NOT called

#### Scenario: CatalogMiss prevents save
- **WHEN** the catalog cannot resolve the spec's tables
- **THEN** `CatalogMiss` propagates and `IDatasetRepository.save()` is NOT called
