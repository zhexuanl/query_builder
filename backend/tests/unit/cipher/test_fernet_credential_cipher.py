"""Unit tests for FernetCredentialCipher."""
import pytest
from cryptography.fernet import Fernet

from adapters.cipher.fernet_credential_cipher import FernetCredentialCipher


def _cipher() -> FernetCredentialCipher:
    return FernetCredentialCipher(Fernet.generate_key())


def test_roundtrip():
    cipher = _cipher()
    plaintext = "postgresql://user:secret@host/db"
    assert cipher.decrypt(cipher.encrypt(plaintext)) == plaintext


def test_empty_string_roundtrip():
    cipher = _cipher()
    assert cipher.decrypt(cipher.encrypt("")) == ""


def test_invalid_token_raises_value_error():
    cipher = _cipher()
    with pytest.raises(ValueError, match="Decryption failed"):
        cipher.decrypt(b"not-a-valid-token")


def test_wrong_key_raises_value_error():
    plaintext = "secret-url"
    ciphertext = FernetCredentialCipher(Fernet.generate_key()).encrypt(plaintext)
    with pytest.raises(ValueError, match="Decryption failed"):
        FernetCredentialCipher(Fernet.generate_key()).decrypt(ciphertext)


def test_invalid_key_raises_at_construction():
    with pytest.raises(Exception):
        FernetCredentialCipher(b"not-a-valid-key")
