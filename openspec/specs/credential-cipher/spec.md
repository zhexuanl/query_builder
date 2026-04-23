## ADDED Requirements

### Requirement: ICredentialCipher port encrypts and decrypts credential strings
The `ICredentialCipher` port SHALL expose `encrypt(plaintext: str) -> bytes` and `decrypt(ciphertext: bytes) -> str`. Implementations MUST be deterministically reversible: `decrypt(encrypt(s)) == s` for all valid strings. The port MUST NOT import any cryptography framework.

#### Scenario: Round-trip encryption is lossless
- **WHEN** `decrypt(encrypt(plaintext))` is called with any non-empty string
- **THEN** the original `plaintext` is returned unchanged

#### Scenario: encrypt returns bytes, not str
- **WHEN** `encrypt()` is called with a string value
- **THEN** the return type is `bytes`

---

### Requirement: FernetCredentialCipher uses symmetric Fernet encryption
`FernetCredentialCipher` SHALL use the `cryptography.fernet.Fernet` algorithm with a key supplied at construction time. The key MUST be a valid URL-safe base64-encoded 32-byte key. Constructing with an invalid key MUST raise `ValueError` immediately (fail fast, not on first use).

#### Scenario: Valid key construction succeeds
- **WHEN** `FernetCredentialCipher(key=Fernet.generate_key())` is called
- **THEN** the instance is created without raising

#### Scenario: Invalid key raises ValueError at construction
- **WHEN** `FernetCredentialCipher(key=b"not-a-valid-key")` is called
- **THEN** `ValueError` is raised before any encrypt/decrypt call

#### Scenario: Tampered ciphertext raises on decrypt
- **WHEN** `decrypt()` is called with bytes that were not produced by `encrypt()`
- **THEN** an exception is raised (wrapping the underlying `InvalidToken`)
