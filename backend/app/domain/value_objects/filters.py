from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .refs import ColumnRef, Operand

type Op = Literal[
    "=", "!=", ">", ">=", "<", "<=",
    "in", "not_in",
    "like", "not_like",
    "is_null", "is_not_null",
    "between",
]

_NULLARY_OPS: frozenset[str] = frozenset({"is_null", "is_not_null"})
_SCALAR_OPS: frozenset[str] = frozenset({"=", "!=", ">", ">=", "<", "<=", "like", "not_like"})
_TUPLE_OPS: frozenset[str] = frozenset({"in", "not_in", "between"})


@dataclass(frozen=True)
class Predicate:
    """A single filter condition: left op right."""
    left: ColumnRef
    op: Op
    right: Operand | tuple[Operand, ...] | None = None

    def __post_init__(self) -> None:
        if self.op in _NULLARY_OPS:
            if self.right is not None:
                raise ValueError(f"Op '{self.op}' takes no right operand")
        elif self.op in _SCALAR_OPS:
            if self.right is None:
                raise ValueError(f"Op '{self.op}' requires a right operand")
            if isinstance(self.right, tuple):
                raise ValueError(f"Op '{self.op}' requires a scalar right operand, not a tuple")
        elif self.op in _TUPLE_OPS:
            if not isinstance(self.right, tuple) or len(self.right) == 0:
                raise ValueError(f"Op '{self.op}' requires a non-empty tuple right operand")
            if self.op == "between" and len(self.right) != 2:
                raise ValueError("Op 'between' requires exactly 2 operands")


@dataclass(frozen=True)
class FilterGroup:
    """Recursive AND/OR group of predicates."""
    op: Literal["and", "or"]
    items: tuple[FilterGroup | Predicate, ...]

    def __post_init__(self) -> None:
        if not self.items:
            raise ValueError("FilterGroup must contain at least one item")
