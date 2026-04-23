## ADDED Requirements

### Requirement: query_builder exposes a versioned public API via __init__.py
The package SHALL export all DSL types, errors, ports, reference implementations, and use cases from `query_builder/__init__.py` in four named tiers (DSL types, Errors, Ports, Reference implementations). Any symbol not exported from `__init__.py` is considered private and MAY change without notice. Consumers MUST NOT import from sub-modules directly.

#### Scenario: DSL types importable from package root
- **WHEN** a consumer writes `from query_builder import QuerySpec, JoinDef, SelectField, ColumnRef, Dialect`
- **THEN** all five names resolve without `ImportError`

#### Scenario: Errors importable from package root
- **WHEN** a consumer writes `from query_builder import PolicyViolation, CompilationError, CatalogMiss, SourceConnectionError, DatasetNotFound`
- **THEN** all five names resolve without `ImportError`

#### Scenario: Ports importable from package root
- **WHEN** a consumer writes `from query_builder import IQueryCompiler, IQueryExecutor, IQueryPolicy, IConnectionRepository, IAuditLog`
- **THEN** all five names resolve without `ImportError`

#### Scenario: Reference implementations importable from package root
- **WHEN** a consumer writes `from query_builder import SqlAlchemyCoreCompiler, DefaultQueryPolicy, InMemoryConnectionRepository, CipherBackedConnectionRepository`
- **THEN** all four names resolve without `ImportError`

#### Scenario: create_app() is NOT exported at root — requires fastapi extra
- **WHEN** a consumer writes `from query_builder import create_app` without the `[fastapi]` extra installed
- **THEN** `ImportError` is raised, directing them to install `query-builder[fastapi]`

---

### Requirement: FastAPI routes are an optional dependency, not a core requirement
`pyproject.toml` SHALL declare `fastapi`, `uvicorn[standard]`, and `httpx` under `[project.optional-dependencies]` key `"fastapi"`. Installing `query-builder` without extras MUST NOT pull in FastAPI. Core dependencies MUST be limited to `sqlalchemy>=2.0`, `cryptography`, and `sqlglot`.

#### Scenario: Core install has no FastAPI
- **WHEN** `pip install query-builder` is run (no extras)
- **THEN** `import fastapi` raises `ModuleNotFoundError`; `import query_builder` succeeds

#### Scenario: fastapi extra installs FastAPI
- **WHEN** `pip install "query-builder[fastapi]"` is run
- **THEN** `from query_builder.infrastructure.app import create_app` succeeds

---

### Requirement: Package ships the QuerySpec JSON Schema as package data
The file `query_builder/schemas/queryspec.v1.json` SHALL be included in the distributed package via `pyproject.toml` `[tool.setuptools.package-data]`. Consumers SHALL be able to locate it via `importlib.resources`.

#### Scenario: Schema file accessible via importlib.resources
- **WHEN** `importlib.resources.files("query_builder").joinpath("schemas/queryspec.v1.json").read_text()` is called
- **THEN** valid JSON is returned without `FileNotFoundError`
