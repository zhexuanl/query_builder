## Context

M5 delivered a secure, audited execution pipeline. Two gaps remain for a shippable governed dataset builder: (1) compiled SQL is only validated by SQLAlchemy's dialect layer — ambiguous column references and unqualified identifiers are not caught until they hit the source DB at runtime; (2) `QuerySpec` definitions cannot be saved and retrieved by name, blocking MLOps pipelines from referencing stable training dataset definitions. M6 addresses both.

## Goals / Non-Goals

**Goals:**
- SQLGlot qualify pass as an opt-in post-compile step in `SqlAlchemyCoreCompiler`; qualify errors map to `CompilationError`
- `DatasetDefinition` frozen domain entity capturing a named `QuerySpec` snapshot with metadata
- `IDatasetRepository` port: `save`, `get`, `list`, `delete` — raises `DatasetNotFound` for unknown IDs
- `InMemoryDatasetRepository` for unit tests
- `SaveDatasetUseCase` and `GetDatasetUseCase` thin orchestration use cases
- Four `/datasets` FastAPI routes with Pydantic models and structured error responses

**Non-Goals:**
- Persistent dataset storage (database/S3)
- Dataset versioning, lineage, or diff
- JWT authentication or per-user dataset isolation
- Frontend UI

## Decisions

### Decision 1 — SQLGlot as an optional qualify-only pass, not a full transpiler

**Chosen:** `SqlAlchemyCoreCompiler` accepts `enable_sqlglot_qualify: bool = False`. When enabled, after SQLAlchemy emits the SQL string, the adapter calls `sqlglot.parse_one(sql).qualify(schema=schema_dict)` and re-renders. Errors from SQLGlot become `CompilationError`. SQLGlot is **not** used as the primary SQL emitter — SQLAlchemy Core remains authoritative for dialect-specific syntax.

Alternatives considered:
- Replace SQLAlchemy with SQLGlot as primary compiler: too large a contract change, risks losing M1–M4 golden test stability.
- Run SQLGlot qualify in a separate use-case step: leaks compiler internals into orchestration layer.

**Layer:** `adapters/compilers/sqlalchemy_core_compiler.py` — qualify helper as a private function `_sqlglot_qualify(sql, dialect, schema)`

No decision-gate needed: additive flag on an existing adapter, no port contract changes.

### Decision 2 — `DatasetDefinition` as a domain entity, not a value object

`DatasetDefinition` has identity (`dataset_id: UUID`) and is mutable over time (delete). It is a domain entity (not frozen), but its `spec: QuerySpec` field is itself frozen. It lives in `domain/entities/`.

**Port:**
```python
class IDatasetRepository(ABC):
    def save(self, dataset: DatasetDefinition) -> None: ...
    def get(self, dataset_id: UUID) -> DatasetDefinition: ...  # raises DatasetNotFound
    def list(self, connection_id: str | None = None) -> list[DatasetDefinition]: ...
    def delete(self, dataset_id: UUID) -> None: ...  # raises DatasetNotFound
```

**Layer:** `domain/interfaces/dataset_repository.py`; impl in `infrastructure/dataset/`

### Decision 3 — `DatasetNotFound` as a new domain error

Added to `domain/errors.py` alongside `CatalogMiss`, `PolicyViolation`, etc. Maps to HTTP 404 in the API layer.

### Decision 4 — Two thin use cases, not one CRUD use case

`SaveDatasetUseCase` and `GetDatasetUseCase` are separate: save validates the spec runs policy checks before persisting (reuses `CompileQueryUseCase` for dry-run validation); get is pure repository delegation. List and delete are handled directly in the route (no use case) — they have no business logic beyond the repository call.

Alternative: single `DatasetUseCase` with method-per-operation — rejected (god object).

### Decision 5 — `SaveDatasetUseCase` dry-run compiles before saving

Before persisting a `DatasetDefinition`, the use case calls `CompileQueryUseCase.execute()` against a mock/in-memory catalog to catch policy violations early. This prevents saving specs that are structurally invalid. It does **not** execute the spec against the source DB.

### Decision 6 — `/datasets` routes return structured errors

Same `{"error_code": ..., "detail": ...}` pattern as `/queries/execute`. `DatasetNotFound` → 404 with `error_code: "DATASET_NOT_FOUND"`.

## Risks / Trade-offs

- **SQLGlot qualify schema dict construction**: SQLGlot needs a `{table: [col, ...]}` dict for qualify. This is derived from `CatalogView` — requires adding a `table_names()` introspection method or a helper that iterates the catalog. Keep this logic in the adapter, not the domain port.
- **In-memory dataset repo loses data on restart**: Acceptable for M6; production persistence is post-M6. Document clearly.
- **SQLGlot version pinning**: SQLGlot's API changes frequently. Pin to a specific minor version in `pyproject.toml`.
- **Dry-run compile uses InMemoryCatalogView fakes**: For policy validation pre-save, the use case needs a catalog. Use the existing test fake pattern — pass `catalog_repo` into `SaveDatasetUseCase` and call `view_for()` normally.

## Migration Plan

Additive only — no existing routes, domain types, or port contracts change (except `domain/errors.py` gains `DatasetNotFound`).

1. Add `sqlglot` to `pyproject.toml`
2. Add `DatasetNotFound` to `domain/errors.py`
3. Implement `DatasetDefinition` entity and `IDatasetRepository` port
4. Implement SQLGlot qualify pass in compiler (off by default)
5. Implement use cases and in-memory repository
6. Add `/datasets` routes and wire `create_app()`
7. Run full test suite

## Open Questions

- Should `SaveDatasetUseCase` call `CompileQueryUseCase` for dry-run validation or just `DefaultQueryPolicy.validate()`? (Propose: full `CompileQueryUseCase` — catches catalog misses too)
- Should `list()` support filtering by `name` substring as well as `connection_id`? (Defer — not needed for M6 scope)
