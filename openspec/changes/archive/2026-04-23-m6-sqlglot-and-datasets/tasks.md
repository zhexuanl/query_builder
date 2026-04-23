## 1. Dependencies and Domain Additions

- [x] 1.1 Add `sqlglot` (pinned minor version) to `pyproject.toml` / `requirements.txt`; verify `import sqlglot` works
- [x] 1.2 Add `DatasetNotFound` exception to `domain/errors.py` alongside existing domain errors
- [x] 1.3 Create `domain/entities/dataset_definition.py` — `DatasetDefinition` class with fields: `dataset_id: UUID`, `name: str`, `description: str`, `connection_id: str`, `spec: QuerySpec`, `created_at: datetime`, `created_by: str`
- [x] 1.4 Create `domain/interfaces/dataset_repository.py` — `IDatasetRepository` ABC with `save`, `get`, `list`, `delete`; `get` and `delete` raise `DatasetNotFound`

## 2. SQLGlot Qualify Pass

- [x] 2.1 Add `enable_sqlglot_qualify: bool = False` parameter to `SqlAlchemyCoreCompiler.__init__()`
- [x] 2.2 Add private `_sqlglot_qualify(sql: str, dialect: Dialect) -> None` function in `adapters/compilers/sqlalchemy_core_compiler.py`; calls `sqlglot.parse_one(sql)` and raises `CompilationError` on parse/qualify failure; does not return modified SQL
- [x] 2.3 Call `_sqlglot_qualify()` at the end of `compile()` when `enable_sqlglot_qualify` is `True`
- [x] 2.4 Write tests in `tests/unit/compilers/test_sqlglot_qualify.py`:
  - Flag disabled by default: existing M1 golden tests unchanged (no new test needed, just confirm)
  - Flag enabled, valid SQL: no `CompilationError` raised
  - Flag enabled, ambiguous SQL: `CompilationError` raised with SQLGlot message

## 3. Dataset Repository

- [x] 3.1 Create `infrastructure/dataset/in_memory_dataset_repository.py` — `InMemoryDatasetRepository`: `dict[UUID, DatasetDefinition]` backing store; implements all four `IDatasetRepository` methods
- [x] 3.2 Write unit tests in `tests/unit/dataset/test_in_memory_dataset_repository.py`:
  - save → get round-trip
  - get unknown raises `DatasetNotFound`
  - list no filter returns all
  - list by `connection_id` returns subset
  - delete removes; subsequent get raises `DatasetNotFound`
  - delete unknown raises `DatasetNotFound`
  - save same `dataset_id` twice overwrites

## 4. Use Cases

- [x] 4.1 Create `use_cases/save_dataset.py` — `SaveDatasetUseCase.__init__(compile_use_case: CompileQueryUseCase, dataset_repo: IDatasetRepository)`; `execute(dataset: DatasetDefinition, dialect: Dialect) -> None`: calls `compile_use_case.execute(dataset.spec, dialect)` (dry-run), then `dataset_repo.save(dataset)` only on success
- [x] 4.2 Create `use_cases/get_dataset.py` — `GetDatasetUseCase.__init__(dataset_repo: IDatasetRepository)`; `execute(dataset_id: UUID) -> DatasetDefinition`: delegates to `dataset_repo.get()`; raises `DatasetNotFound` unchanged
- [x] 4.3 Write unit tests in `tests/unit/use_cases/test_save_dataset.py`:
  - Valid spec → `dataset_repo.save()` called once
  - `PolicyViolation` from compile → `save()` not called, error propagates
  - `CatalogMiss` from compile → `save()` not called, error propagates
- [x] 4.4 Write unit tests in `tests/unit/use_cases/test_get_dataset.py`:
  - Known ID → `DatasetDefinition` returned
  - Unknown ID → `DatasetNotFound` propagates

## 5. API Layer

- [x] 5.1 Create `infrastructure/api/models/dataset_models.py` — `SaveDatasetRequest` (name, description, connection_id, spec fields, created_by, dialect), `DatasetResponse` (all `DatasetDefinition` fields + spec)
- [x] 5.2 Create `infrastructure/api/routes/datasets.py` — `router = APIRouter(prefix="/datasets")`; implement all four routes; map `DatasetNotFound` → 404 with `error_code: "DATASET_NOT_FOUND"`; map `PolicyViolation`/`CompilationError`/`CatalogMiss` → 422 with structured `error_code`
- [x] 5.3 Write unit tests in `tests/unit/api/test_datasets_route.py` using `TestClient` with mocked use cases and repo:
  - POST 201 with generated `dataset_id`
  - POST 422 on `PolicyViolation`
  - GET 200 with full spec in response
  - GET 404 on unknown ID
  - GET list 200 with `connection_id` filter
  - DELETE 204 success
  - DELETE 404 on unknown ID

## 6. DI Wiring and Final Integration

- [x] 6.1 Update `infrastructure/app.py` — wire `InMemoryDatasetRepository`, `SaveDatasetUseCase`, `GetDatasetUseCase`; include `datasets` router; done signal: `create_app(config)` starts without raising
- [x] 6.2 Run full test suite (`pytest backend/tests/`) — all tests green before commit
