## M6: SQLGlot Qualify Pass + Named Dataset Persistence

## Why

Two gaps remain before the system is a complete governed dataset builder: (1) compiled SQL is never independently validated — a malformed or ambiguous column reference only fails at execution time against the source DB; (2) there is no way to save a `QuerySpec` as a named, versioned dataset definition that MLOps pipelines can reference by name. M6 closes both.

## What Changes

- SQLGlot qualify pass added as an optional post-compile validation step in `SqlAlchemyCoreCompiler`: transpiles the compiled SQL through SQLGlot's qualify rewriter to catch unqualified column references and ambiguous aliases before the query reaches the source DB
- New `IDatasetRepository` port: create, get, list, and delete named `DatasetDefinition` records (a `QuerySpec` + metadata snapshot)
- New `DatasetDefinition` domain entity: frozen dataclass holding `dataset_id`, `name`, `description`, `connection_id`, `spec: QuerySpec`, `created_at`, `created_by`
- New `InMemoryDatasetRepository` adapter for unit tests
- Four new FastAPI routes under `/datasets`: `POST /datasets`, `GET /datasets/{dataset_id}`, `GET /datasets`, `DELETE /datasets/{dataset_id}`
- `SaveDatasetUseCase` and `GetDatasetUseCase` — thin orchestration use cases

## Capabilities

### New Capabilities
- `sqlglot-qualify-pass`: Optional SQLGlot qualify/lint step wired into the compiler; raises `CompilationError` on ambiguous or unqualified SQL
- `dataset-repository`: `IDatasetRepository` port + `InMemoryDatasetRepository`; `DatasetDefinition` entity; CRUD semantics
- `dataset-api`: FastAPI `/datasets` routes with Pydantic request/response models; error mapping for `DatasetNotFound`

### Modified Capabilities
- `query-compiler`: `SqlAlchemyCoreCompiler` gains an optional `enable_sqlglot_qualify: bool` flag; qualify errors map to `CompilationError`

## Impact

- New files: `domain/entities/dataset_definition.py`, `domain/interfaces/dataset_repository.py`, `domain/errors.py` (add `DatasetNotFound`), `adapters/sqlglot_qualify.py`, `infrastructure/dataset/in_memory_dataset_repository.py`, `use_cases/save_dataset.py`, `use_cases/get_dataset.py`, `infrastructure/api/routes/datasets.py`, `infrastructure/api/models/dataset_models.py`
- Modified: `adapters/compilers/sqlalchemy_core_compiler.py`, `infrastructure/app.py`
- New dependency: `sqlglot`

## Non-goals

- Persistent dataset storage (database/file — post-M6)
- Dataset versioning or lineage tracking
- Dataset sharing or access-control beyond connection allowlist
- Frontend UI for dataset management
- JWT authentication (post-M6)
- Streaming or paginated dataset result execution
