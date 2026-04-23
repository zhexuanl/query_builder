from abc import ABC, abstractmethod


class IConnectionRepository(ABC):
    """Port: resolves a connection URL from a connection ID.

    Lifecycle: ``register()`` MUST be called before any ``ExecuteQueryUseCase.execute()``
    that references the same ``connection_id``.  Attempting to execute against an
    unregistered ID raises ``CatalogMiss``.

    ``TableAllowlistPolicy`` must also be configured for every ``connection_id``
    registered here — both guards must know about the connection.

    Implementations:
    - ``InMemoryConnectionRepository`` — test double; stores plaintext URLs; NOT
      suitable for production where credentials must be encrypted at rest.
    - ``CipherBackedConnectionRepository`` — production default; encrypts URLs via
      ``ICredentialCipher`` before storing, decrypts on retrieval.
    """

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
