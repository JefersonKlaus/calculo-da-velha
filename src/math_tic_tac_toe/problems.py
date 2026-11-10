"""What the game can ask: every math problem of each operation.

One problem maker per operation: addition and subtraction with numbers that
grow with the difficulty, multiplication and division from the chosen times
tables. Prompts only use digits and math symbols, so they are the same in
every language.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import NamedTuple, Protocol

from .settings import OPERATIONS, GameSettings, Operation


class Problem(NamedTuple):
    prompt: str
    answer: int
    operation: Operation


class ProblemMaker(Protocol):
    def problems(self, difficulty: int) -> Sequence[Problem]:
        """Every problem this operation can ask at ``difficulty``."""
        ...


def max_operand(difficulty: int) -> int:
    """Addition/subtraction numbers: up to 10, 15 or 20 by difficulty."""
    return 5 + 5 * difficulty


# A times table has only 10 facts and the board has 9 cells, so every cell
# draws from the whole table; this keeps the questions on the board different.
TABLE_FACTORS = range(1, 11)


class AdditionProblems:
    def problems(self, difficulty: int) -> list[Problem]:
        numbers = range(1, max_operand(difficulty) + 1)
        return [
            Problem(f"{left} {Operation.ADDITION.symbol} {right}", left + right, Operation.ADDITION)
            for left in numbers
            for right in numbers
        ]


class SubtractionProblems:
    """The result is never negative."""

    def problems(self, difficulty: int) -> list[Problem]:
        return [
            Problem(
                f"{left} {Operation.SUBTRACTION.symbol} {right}",
                left - right,
                Operation.SUBTRACTION,
            )
            for left in range(1, max_operand(difficulty) + 1)
            for right in range(1, left + 1)
        ]


class MultiplicationProblems:
    def __init__(self, tables: Iterable[int]) -> None:
        self.tables = tuple(sorted(tables))

    def problems(self, difficulty: int) -> list[Problem]:
        return [
            Problem(
                f"{table} {Operation.MULTIPLICATION.symbol} {factor}",
                table * factor,
                Operation.MULTIPLICATION,
            )
            for table in self.tables
            for factor in TABLE_FACTORS
        ]


class DivisionProblems:
    """The division tables: multiples of a table divided by it (e.g. 21 ÷ 7)."""

    def __init__(self, tables: Iterable[int]) -> None:
        self.tables = tuple(sorted(tables))

    def problems(self, difficulty: int) -> list[Problem]:
        return [
            Problem(
                f"{table * quotient} {Operation.DIVISION.symbol} {table}",
                quotient,
                Operation.DIVISION,
            )
            for table in self.tables
            for quotient in TABLE_FACTORS
        ]


def problem_maker(operation: Operation, tables: Iterable[int]) -> ProblemMaker:
    if operation is Operation.ADDITION:
        return AdditionProblems()
    if operation is Operation.SUBTRACTION:
        return SubtractionProblems()
    if operation is Operation.MULTIPLICATION:
        return MultiplicationProblems(tables)
    return DivisionProblems(tables)


def problems_for(settings: GameSettings) -> list[ProblemMaker]:
    """One problem maker per chosen operation, in the usual + − × ÷ order."""
    return [
        problem_maker(operation, settings.tables)
        for operation in OPERATIONS
        if operation in settings.operations
    ]
