## ADDED Requirements

### Requirement: IQueryExecutor port executes compiled SQL against a source database
The `IQueryExecutor` port SHALL expose a single `execute(query: CompiledQuery, connection_url: str) -> list[dict[str, Any]]` method. It MUST return each row as a plain Python dict keyed by column label. It MUST NOT return SQLAlchemy `Row` objects or any other framework type. It MUST raise `SourceConnectionError` if the source database is unreachable or the query fails.

#### Scenario: Successful execution returns list of dicts
- **WHEN** `execute()` is called with a valid `CompiledQuery` and a reachable `connection_url`
- **THEN** a `list[dict[str, Any]]` is returned where each dict key matches the `SelectField.label` values from the original spec

#### Scenario: Source database unreachable raises SourceConnectionError
- **WHEN** `execute()` is called with an unreachable `connection_url`
- **THEN** `SourceConnectionError` is raised with a message identifying the failure

#### Scenario: SQL execution error raises SourceConnectionError
- **WHEN** the compiled SQL is rejected by the database engine (e.g., permission denied, syntax error from dialect mismatch)
- **THEN** `SourceConnectionError` is raised; the original DB error is chained as the cause

---

### Requirement: SqlAlchemyQueryExecutor creates and disposes an engine per call
`SqlAlchemyQueryExecutor` SHALL create a new `Engine` for each `execute()` call using `sa.create_engine(connection_url)` and MUST call `engine.dispose()` in a `finally` block to release all pooled connections regardless of outcome.

#### Scenario: Engine disposed after successful execution
- **WHEN** `execute()` returns successfully
- **THEN** `engine.dispose()` has been called before the method returns

#### Scenario: Engine disposed after exception
- **WHEN** `execute()` raises `SourceConnectionError`
- **THEN** `engine.dispose()` has been called before the exception propagates

---

### Requirement: IConnectionRepository resolves connection URL from connection_id
The `IConnectionRepository` port SHALL expose `get_url(connection_id: str) -> str` and `register(connection_id: str, url: str) -> None`. `get_url()` MUST raise `CatalogMiss` if `connection_id` is not registered. `register()` MUST encrypt the URL via `ICredentialCipher` before storage; `get_url()` MUST decrypt before returning. Callers receive plaintext URLs; ciphertext MUST NOT be exposed outside the repository.

#### Scenario: Known connection_id returns plaintext URL
- **WHEN** `get_url()` is called with a `connection_id` that was previously registered
- **THEN** the original plaintext `connection_url` string is returned (decrypted)

#### Scenario: Unknown connection_id raises CatalogMiss
- **WHEN** `get_url()` is called with an unregistered `connection_id`
- **THEN** `CatalogMiss` is raised identifying the unknown connection

#### Scenario: Registered URL is stored encrypted
- **WHEN** `register(connection_id, url)` is called
- **THEN** the stored value is ciphertext (bytes), not the plaintext URL
