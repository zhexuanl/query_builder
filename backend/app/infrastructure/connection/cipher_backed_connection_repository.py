from domain.errors import CatalogMiss
from domain.interfaces.connection_repository import IConnectionRepository
from domain.interfaces.credential_cipher import ICredentialCipher


class CipherBackedConnectionRepository(IConnectionRepository):
    """Connection repository that encrypts URLs at rest using a cipher."""

    def __init__(self, cipher: ICredentialCipher) -> None:
        self._cipher = cipher
        self._store: dict[str, bytes] = {}

    def register(self, connection_id: str, url: str) -> None:
        self._store[connection_id] = self._cipher.encrypt(url)

    def get_url(self, connection_id: str) -> str:
        try:
            return self._cipher.decrypt(self._store[connection_id])
        except KeyError:
            raise CatalogMiss(f"Unknown connection: '{connection_id}'")
