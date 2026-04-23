from domain.errors import CatalogMiss
from domain.interfaces.connection_repository import IConnectionRepository


class InMemoryConnectionRepository(IConnectionRepository):
    """Dict-backed connection repository for local dev and tests."""

    def __init__(self, urls: dict[str, str]) -> None:
        self._urls = dict(urls)

    def register(self, connection_id: str, url: str) -> None:
        self._urls[connection_id] = url

    def get_url(self, connection_id: str) -> str:
        try:
            return self._urls[connection_id]
        except KeyError:
            raise CatalogMiss(f"Unknown connection: '{connection_id}'")
