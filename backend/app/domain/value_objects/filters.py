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
_MAX_FILTER_DEPTH = 10


@dataclass(frozen=True)
class Predicate:
    """A single filter condition of the form ``left op right``.

    Arity rules enforced at construction:

    - Nullary ops (``is_null``, ``is_not_null``): ``right`` must be ``None``.
    - Scalar ops (``=``, ``!=``, ``>``, etc.): ``right`` must be a single ``Operand``.
    - Tuple ops (``in``, ``not_in``): ``right`` must be a non-empty tuple.
    - ``between``: ``right`` must be a tuple of exactly 2 operands.

    Attributes:
        left: The column being tested.
        op: The comparison operator.
        right: The right-hand operand(s), or ``None`` for nullary operators.

    Raises:
        ValueError: If the arity of ``right`` does not match ``op``.
    """

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
    """A recursive AND/OR group of filter conditions.

    Nesting is capped at ``10`` levels to prevent DoS via pathological inputs.

    Attributes:
        op: The logical combinator — ``"and"`` or ``"or"``.
        items: One or more predicates or nested groups.

    Raises:
        ValueError: If ``items`` is empty or nesting exceeds the depth limit.
    """

    op: Literal["and", "or"]
    items: tuple[FilterGroup | Predicate, ...]

    def __post_init__(self) -> None:
        if not self.items:
            raise ValueError("FilterGroup must contain at least one item")
        if _depth(self) > _MAX_FILTER_DEPTH:
            raise ValueError(
                f"FilterGroup nesting exceeds the maximum depth of {_MAX_FILTER_DEPTH}"
            )


def _depth(node: FilterGroup | Predicate) -> int:
    """Return the nesting depth of a filter node.

    Args:
        node: A ``FilterGroup`` or ``Predicate`` to measure.

    Returns:
        The depth as an integer, where a bare ``Predicate`` has depth 1.
    """
    if isinstance(node, Predicate):
        return 1
    return 1 + max((_depth(item) for item in node.items), default=0)
