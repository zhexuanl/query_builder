from dataclasses import dataclass, field

from ..value_objects.filters import FilterGroup
from ..value_objects.query_parts import JoinDef, SelectField, SortDef
from ..value_objects.refs import ColumnRef

_VERSION = 1


@dataclass
class QuerySpec:
    """
    Aggregate root for a dataset definition.

    Represents the complete intent of a query — source table, optional joins,
    filters, selected/aggregated columns, sorting, and a row limit.
    SQL is never stored here; it is compiled from this spec at runtime.
    """
    connection_id: str
    source: JoinDef
    select: tuple[SelectField, ...]
    joins: tuple[JoinDef, ...] = field(default_factory=tuple)
    where: FilterGroup | None = None
    group_by: tuple[ColumnRef, ...] = field(default_factory=tuple)
    order_by: tuple[SortDef, ...] = field(default_factory=tuple)
    limit: int | None = 1000
    version: int = _VERSION

    def __post_init__(self) -> None:
        if not self.connection_id:
            raise ValueError("QuerySpec.connection_id must not be empty")
        if not self.select:
            raise ValueError("QuerySpec must select at least one field")
        if self.limit is not None and self.limit <= 0:
            raise ValueError("QuerySpec.limit must be a positive integer")
        self._validate_group_by()

    def _validate_group_by(self) -> None:
        """Every non-aggregate select field must appear in group_by when any aggregate is present."""
        has_agg = any(f.kind == "agg" for f in self.select)
        if not has_agg:
            return
        grouped = set(self.group_by)
        for f in self.select:
            if f.kind == "column" and f.source not in grouped:
                raise ValueError(
                    f"Column '{f.source}' must appear in group_by because aggregates are present"
                )

    @property
    def all_table_aliases(self) -> frozenset[str]:
        """All aliases in play: source + every join."""
        return frozenset({self.source.alias} | {j.alias for j in self.joins})

    @property
    def is_aggregating(self) -> bool:
        return any(f.kind == "agg" for f in self.select)
