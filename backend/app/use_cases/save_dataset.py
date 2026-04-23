from domain.entities.dataset_definition import DatasetDefinition
from domain.interfaces.dataset_repository import IDatasetRepository
from domain.value_objects.dialect import Dialect
from use_cases.compile_query import CompileQueryUseCase


class SaveDatasetUseCase:
    """Validates a DatasetDefinition's spec then persists it.

    Calls ``CompileQueryUseCase.execute()`` as a dry-run to enforce all
    policies and catalog checks before saving.  Errors from compile propagate
    unchanged; ``IDatasetRepository.save()`` is only called on success.
    """

    def __init__(
        self,
        compile_use_case: CompileQueryUseCase,
        dataset_repo: IDatasetRepository,
    ) -> None:
        self._compile_use_case = compile_use_case
        self._dataset_repo = dataset_repo

    def execute(self, dataset: DatasetDefinition, dialect: Dialect) -> None:
        """Validate ``dataset.spec`` then persist ``dataset``.

        Args:
            dataset: The dataset definition to save.
            dialect: Dialect used for the dry-run compile validation.

        Raises:
            PolicyViolation: If the spec violates a governance rule.
            CatalogMiss: If a referenced table or column is absent.
            CompilationError: If the spec cannot be compiled.
        """
        self._compile_use_case.execute(dataset.spec, dialect)
        self._dataset_repo.save(dataset)
