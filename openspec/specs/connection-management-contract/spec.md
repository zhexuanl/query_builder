# connection-management-contract Specification

## Purpose
TBD - created by archiving change library-consumer-api. Update Purpose after archive.
## Requirements
### Requirement: Consumers register connections before executing queries
The library SHALL require consumers to register a `(connection_id, url)` pair via `IConnectionRepository.register()` before any `ExecuteQueryUseCase.execute()` call that references that `connection_id`. Attempting to execute against an unregistered `connection_id` MUST raise `CatalogMiss`. This is independent of the allowlist — both `IConnectionRepository` and `TableAllowlistPolicy` must know the connection.

#### Scenario: Execute against registered connection succeeds
- **WHEN** `conn_repo.register("pg-1", url)` is called before `execute_uc.execute(spec_for_pg1, ...)`
- **THEN** execution proceeds without `CatalogMiss`

#### Scenario: Execute against unregistered connection raises CatalogMiss
- **WHEN** `execute_uc.execute(spec, ...)` is called with `connection_id="pg-1"` and `conn_repo` has no entry for `"pg-1"`
- **THEN** `CatalogMiss` is raised before any SQL is compiled or executed

---

### Requirement: CipherBackedConnectionRepository encrypts URLs at rest
When consumers use `CipherBackedConnectionRepository`, registered URLs MUST be stored as ciphertext (`bytes`), never as plaintext strings. The plaintext URL MUST only exist in memory during `register()` (before encryption) and `get_url()` (after decryption). Neither the plaintext URL nor the `ICredentialCipher` key MUST be logged.

#### Scenario: Stored value is not the plaintext URL
- **WHEN** `register("id", "postgresql://user:secret@host/db")` is called
- **THEN** the internal store contains `bytes`, not the original string

#### Scenario: get_url returns plaintext
- **WHEN** `get_url("id")` is called after `register("id", url)`
- **THEN** the original `url` string is returned

---

### Requirement: TableAllowlistPolicy must be configured for each registered connection
When `TableAllowlistPolicy` is included in the policy list, it MUST be constructed with an entry for every `connection_id` that will be used. A `connection_id` absent from the allowlist raises `PolicyViolation` (closed-by-default). Consumers MUST configure both the connection repository and the allowlist for the same set of connections.

#### Scenario: Connection registered but not in allowlist raises PolicyViolation
- **WHEN** `conn_repo.register("pg-1", url)` is called but `TableAllowlistPolicy` has no entry for `"pg-1"`
- **THEN** `execute_uc.execute(spec, ...)` raises `PolicyViolation` identifying the missing allowlist entry

#### Scenario: Connection registered and in allowlist succeeds
- **WHEN** both `conn_repo.register("pg-1", url)` and `TableAllowlistPolicy({"pg-1": frozenset({"customers"})})` are configured
- **THEN** a spec referencing `"pg-1"` and `"customers"` passes policy validation

---

### Requirement: InMemoryConnectionRepository is the correct test double for unit tests
`InMemoryConnectionRepository` SHALL be used in all unit tests as the test double for `IConnectionRepository`. It stores plaintext URLs (no cipher). It MUST NOT be used in production deployments where credentials must be encrypted at rest. The consumer integration guide MUST document this distinction.

#### Scenario: InMemoryConnectionRepository used without cipher in unit tests
- **WHEN** `InMemoryConnectionRepository` is constructed and `register("id", url)` is called
- **THEN** `get_url("id")` returns the original plaintext URL without any encryption overhead

---

### Requirement: Consumer integration guide documents minimal wiring
The file `docs/consumer_guide.md` SHALL provide a copy-pasteable minimal wiring example that demonstrates: constructing all required components, registering a connection, building a `QuerySpec` using the DSL, compiling to SQL, and executing to retrieve rows. It MUST also include an error-handling section covering `PolicyViolation`, `CatalogMiss`, `CompilationError`, and `SourceConnectionError`.

#### Scenario: Wiring example is executable without modification
- **WHEN** the code block in `consumer_guide.md` is run against a live Postgres instance with the correct URL substituted
- **THEN** rows are returned without error

#### Scenario: Error handling section covers all four domain errors
- **WHEN** a consumer reads the guide
- **THEN** they find documented `try/except` patterns for `PolicyViolation`, `CatalogMiss`, `CompilationError`, and `SourceConnectionError`

