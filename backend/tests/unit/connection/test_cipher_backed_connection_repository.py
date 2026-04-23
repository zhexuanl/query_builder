"""Unit tests for CipherBackedConnectionRepository."""
import pytest

from domain.errors import CatalogMiss
from infrastructure.connection.cipher_backed_connection_repository import CipherBackedConnectionRepository
from tests.fakes.fake_credential_cipher import FakeCredentialCipher


def _repo() -> CipherBackedConnectionRepository:
    return CipherBackedConnectionRepository(FakeCredentialCipher())


def test_register_and_get_url_roundtrip():
    repo = _repo()
    url = "postgresql://user:pass@host/db"
    repo.register("conn-1", url)
    assert repo.get_url("conn-1") == url


def test_unknown_connection_raises_catalog_miss():
    repo = _repo()
    with pytest.raises(CatalogMiss, match="conn-unknown"):
        repo.get_url("conn-unknown")


def test_url_is_stored_encrypted():
    cipher = FakeCredentialCipher()
    repo = CipherBackedConnectionRepository(cipher)
    url = "postgresql://secret@host/db"
    repo.register("conn-1", url)
    raw = repo._store["conn-1"]
    assert raw != url.encode()  # base64-encoded, not plaintext


def test_register_overwrites_existing():
    repo = _repo()
    repo.register("conn-1", "postgresql://old/db")
    repo.register("conn-1", "postgresql://new/db")
    assert repo.get_url("conn-1") == "postgresql://new/db"


def test_multiple_connections_independent():
    repo = _repo()
    repo.register("a", "url-a")
    repo.register("b", "url-b")
    assert repo.get_url("a") == "url-a"
    assert repo.get_url("b") == "url-b"
