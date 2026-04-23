## MODIFIED Requirements

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
