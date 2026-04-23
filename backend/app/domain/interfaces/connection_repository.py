from abc import ABC, abstractmethod


class IConnectionRepository(ABC):
    """Port: resolves a connection URL from a connection ID."""

    @abstractmethod
    def register(self, connection_id: str, url: str) -> None:
        """Register a connection URL under ``connection_id``.

        Args:
            connection_id: Identifier to associate with the URL.
            url: SQLAlchemy-compatible connection URL string.
        """

    @abstractmethod
    def get_url(self, connection_id: str) -> str:
        """Return the connection URL for ``connection_id``.

        Args:
            connection_id: Identifier of the registered connection.

        Returns:
            SQLAlchemy-compatible connection URL string.

        Raises:
            CatalogMiss: If ``connection_id`` is not registered.
        """
