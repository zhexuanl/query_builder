from uuid import UUID

from domain.entities.dataset_definition import DatasetDefinition
from domain.interfaces.dataset_repository import IDatasetRepository


class GetDatasetUseCase:
    """Retrieves a DatasetDefinition by ID from the repository."""

    def __init__(self, dataset_repo: IDatasetRepository) -> None:
        self._dataset_repo = dataset_repo

    def execute(self, dataset_id: UUID) -> DatasetDefinition:
        """Return the dataset for ``dataset_id``.

        Raises:
            DatasetNotFound: If no dataset exists for ``dataset_id``.
        """
        return self._dataset_repo.get(dataset_id)
