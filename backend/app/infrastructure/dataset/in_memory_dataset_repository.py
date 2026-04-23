from uuid import UUID

from domain.entities.dataset_definition import DatasetDefinition
from domain.errors import DatasetNotFound
from domain.interfaces.dataset_repository import IDatasetRepository


class InMemoryDatasetRepository(IDatasetRepository):
    """In-memory implementation of IDatasetRepository backed by a plain dict.

    Data is lost on process restart. Intended for unit tests and development only.
    Not thread-safe by design — production persistence is post-M6.
    """

    def __init__(self) -> None:
        self._store: dict[UUID, DatasetDefinition] = {}

    def save(self, dataset: DatasetDefinition) -> None:
        self._store[dataset.dataset_id] = dataset

    def get(self, dataset_id: UUID) -> DatasetDefinition:
        try:
            return self._store[dataset_id]
        except KeyError:
            raise DatasetNotFound(f"Dataset '{dataset_id}' not found")

    def list(self, connection_id: str | None = None) -> list[DatasetDefinition]:
        datasets = list(self._store.values())
        if connection_id is not None:
            datasets = [d for d in datasets if d.connection_id == connection_id]
        return datasets

    def delete(self, dataset_id: UUID) -> None:
        try:
            del self._store[dataset_id]
        except KeyError:
            raise DatasetNotFound(f"Dataset '{dataset_id}' not found")
