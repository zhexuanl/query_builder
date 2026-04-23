from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from domain.entities.query_spec import QuerySpec


@dataclass
class DatasetDefinition:
    """A named, persisted snapshot of a QuerySpec with metadata.

    Attributes:
        dataset_id: Unique identifier assigned by the caller (typically uuid4()).
        name: Human-readable name for the dataset.
        description: Optional free-text description.
        connection_id: Source database connection for this dataset.
        spec: Frozen QuerySpec captured at save time.
        created_at: UTC timestamp when the dataset was saved.
        created_by: Identifier of the user or system that created the dataset.
    """

    dataset_id: UUID
    name: str
    description: str
    connection_id: str
    spec: QuerySpec
    created_at: datetime
    created_by: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("DatasetDefinition.name must not be blank")
        if self.connection_id != self.spec.connection_id:
            raise ValueError(
                "DatasetDefinition.connection_id must match spec.connection_id"
            )
