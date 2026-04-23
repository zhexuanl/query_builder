from abc import ABC, abstractmethod


class IConnectionRepository(ABC):
    """Port: resolves a connection URL from a connection ID."""

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
