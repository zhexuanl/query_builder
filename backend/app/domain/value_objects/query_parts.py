from dataclasses import dataclass
from typing import Literal

from .refs import ColumnRef
from .filters import Predicate


@dataclass(frozen=True)
class JoinDef:
    """Defines a join to a single table. Also used as the source (primary table) with empty on."""
    type: Literal["inner", "left"]
    table: str
    alias: str
    on: tuple[Predicate, ...]

    def __post_init__(self) -> None:
        if not self.table:
            raise ValueError("JoinDef.table must not be empty")
        if not self.alias:
            raise ValueError("JoinDef.alias must not be empty")


@dataclass(frozen=True)
class SelectField:
    """A single output column — either a plain column reference or an aggregate."""
    kind: Literal["column", "agg"]
    source: ColumnRef
    label: str
    func: Literal["count", "count_distinct", "sum", "avg", "min", "max"] | None = None

    def __post_init__(self) -> None:
        if not self.label:
            raise ValueError("SelectField.label must not be empty")
        if self.kind == "agg" and self.func is None:
            raise ValueError("SelectField with kind='agg' requires func to be set")
        if self.kind == "column" and self.func is not None:
            raise ValueError("SelectField with kind='column' must not set func")


@dataclass(frozen=True)
class SortDef:
    """Sort instruction referencing an output label from SelectField."""
    label: str
    direction: Literal["asc", "desc"] = "asc"

    def __post_init__(self) -> None:
        if not self.label:
            raise ValueError("SortDef.label must not be empty")
