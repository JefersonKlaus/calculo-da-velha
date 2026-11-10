"""What the players choose before a match: which operations to practice and,
for multiplication and division, which times tables.

Everything is selected by default. Each tap selects or unselects one option,
so players can keep all of them, just one, or any combination.

Hard mode adds a time limit: each player has that many seconds for the whole
match, like a chess clock.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
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

# Hard mode: seconds each player has for the whole match.
DEFAULT_TIME_LIMIT = 60
MIN_TIME_LIMIT = 5
MAX_TIME_LIMIT = 5 * 60
TIME_LIMIT_STEP = 5  # the time bar moves in steps of this many seconds

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
    # Hard mode: seconds per player for the whole match; None plays untimed.
    time_limit: int | None = None

    def __post_init__(self) -> None:
        # Accept any collection (e.g. a set or list) and store a frozenset.
        object.__setattr__(self, "operations", frozenset(self.operations))
        object.__setattr__(self, "tables", frozenset(self.tables))
        if not self.operations:
            raise ValueError("At least one operation must be chosen.")
        if not self.tables or not self.tables <= set(TABLES):
            raise ValueError(f"Choose at least one table between {TABLES[0]} and {TABLES[-1]}.")
        if self.time_limit is not None and not is_valid_time_limit(self.time_limit):
            raise ValueError(
                f"The time limit must be from {MIN_TIME_LIMIT} to {MAX_TIME_LIMIT} seconds."
            )

    @property
    def uses_tables(self) -> bool:
        return any(operation.uses_table for operation in self.operations)

    def toggle_operation(self, operation: Operation) -> GameSettings:
        return replace(self, operations=toggle(self.operations, operation))

    def toggle_table(self, table: int) -> GameSettings:
        return replace(self, tables=toggle(self.tables, table))

    def with_time_limit(self, seconds: int | None) -> GameSettings:
        """The same choices in hard mode with ``seconds`` per player, or
        untimed with ``None``."""
        return replace(self, time_limit=seconds)


def is_valid_time_limit(seconds: int) -> bool:
    return MIN_TIME_LIMIT <= seconds <= MAX_TIME_LIMIT


def snap_time_limit(value: float) -> int:
    """The time bar's position as a valid time limit: the nearest multiple of
    ``TIME_LIMIT_STEP``, from ``MIN_TIME_LIMIT`` to ``MAX_TIME_LIMIT``."""
    snapped = round(value / TIME_LIMIT_STEP) * TIME_LIMIT_STEP
    return max(MIN_TIME_LIMIT, min(MAX_TIME_LIMIT, snapped))


DEFAULT_SETTINGS = GameSettings()
