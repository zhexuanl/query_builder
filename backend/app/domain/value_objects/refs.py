from dataclasses import dataclass


@dataclass(frozen=True)
class ColumnRef:
    """Reference to a specific column via its table alias and name."""
    alias: str
    name: str

    def __post_init__(self) -> None:
        if not self.alias:
            raise ValueError("ColumnRef.alias must not be empty")
        if not self.name:
            raise ValueError("ColumnRef.name must not be empty")

    def __str__(self) -> str:
        return f"{self.alias}.{self.name}"


@dataclass(frozen=True)
class ParamRef:
    """Runtime parameter — value supplied at execution time, never inlined."""
    name: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("ParamRef.name must not be empty")


@dataclass(frozen=True)
class ValueRef:
    """Literal scalar value embedded in the query spec."""
    value: str | int | float | bool | None


type Operand = ColumnRef | ParamRef | ValueRef
