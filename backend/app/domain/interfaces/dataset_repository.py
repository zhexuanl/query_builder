from abc import ABC, abstractmethod
from uuid import UUID

from domain.entities.dataset_definition import DatasetDefinition
from domain.errors import DatasetNotFound


class IDatasetRepository(ABC):
    """Port for persisting and retrieving DatasetDefinition records."""

    @abstractmethod
    def save(self, dataset: DatasetDefinition) -> None:
        """Persist ``dataset``, overwriting any existing record with the same ID."""

    @abstractmethod
    def get(self, dataset_id: UUID) -> DatasetDefinition:
        """Return the dataset for ``dataset_id``.

        Raises:
            DatasetNotFound: If no dataset exists for ``dataset_id``.
        """

    @abstractmethod
    def list(self, connection_id: str | None = None) -> list[DatasetDefinition]:
        """Return all datasets, optionally filtered by ``connection_id``."""

    @abstractmethod
    def delete(self, dataset_id: UUID) -> None:
        """Remove the dataset for ``dataset_id``.

        Raises:
            DatasetNotFound: If no dataset exists for ``dataset_id``.
        """
