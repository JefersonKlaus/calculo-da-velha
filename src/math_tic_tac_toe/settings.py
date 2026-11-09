"""What the players choose before a match: which operations to practice and,
for multiplication and division, which times tables.

Everything is selected by default. Each tap selects or unselects one option,
so players can keep all of them, just one, or any combination.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from typing import TypeVar


class Operation(str, Enum):
    ADDITION = "addition"
    SUBTRACTION = "subtraction"
    MULTIPLICATION = "multiplication"
    DIVISION = "division"

    @property
    def symbol(self) -> str:
        return _SYMBOLS[self]

    @property
    def uses_table(self) -> bool:
        """Multiplication and division practice times tables."""
        return self in (Operation.MULTIPLICATION, Operation.DIVISION)


_SYMBOLS = {
    Operation.ADDITION: "+",
    Operation.SUBTRACTION: "−",
    Operation.MULTIPLICATION: "×",
    Operation.DIVISION: "÷",
}

OPERATIONS = tuple(Operation)
TABLES = tuple(range(1, 11))

Option = TypeVar("Option")


def toggle(selected: frozenset[Option], option: Option) -> frozenset[Option]:
    """New selection after tapping ``option``: unselects it if it was
    selected, selects it otherwise. The last selected option stays selected,
    so the game always has questions to ask."""
    if option in selected:
        return selected - {option} if len(selected) > 1 else selected
    return selected | {option}


@dataclass(frozen=True)
class GameSettings:
    """Defaults to everything: every operation and every times table."""

    operations: frozenset[Operation] = frozenset(OPERATIONS)
    # Kept even when no chosen operation uses tables, so choosing
    # multiplication or division again remembers the last chosen tables.
    tables: frozenset[int] = frozenset(TABLES)

    def __post_init__(self) -> None:
        # Accept any collection (e.g. a set or list) and store a frozenset.
        object.__setattr__(self, "operations", frozenset(self.operations))
        object.__setattr__(self, "tables", frozenset(self.tables))
        if not self.operations:
            raise ValueError("At least one operation must be chosen.")
        if not self.tables or not self.tables <= set(TABLES):
            raise ValueError(f"Choose at least one table between {TABLES[0]} and {TABLES[-1]}.")

    @property
    def uses_tables(self) -> bool:
        return any(operation.uses_table for operation in self.operations)

    def toggle_operation(self, operation: Operation) -> GameSettings:
        return GameSettings(toggle(self.operations, operation), self.tables)

    def toggle_table(self, table: int) -> GameSettings:
        return GameSettings(self.operations, toggle(self.tables, table))

    @classmethod
    def of(cls, operations: Iterable[Operation], tables: Iterable[int] = TABLES) -> GameSettings:
        return cls(frozenset(operations), frozenset(tables))


DEFAULT_SETTINGS = GameSettings()
