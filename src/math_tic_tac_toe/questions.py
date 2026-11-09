"""Math questions of the game: one problem maker per operation, plus the
generator that picks a question and adds the answer choices.

Prompts only use digits and math symbols, so they are the same in every
language.
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Iterable, Sequence
from dataclasses import dataclass
from random import Random
from typing import NamedTuple, Protocol

from .settings import DEFAULT_SETTINGS, OPERATIONS, GameSettings, Operation

DEFAULT_CHOICE_COUNT = 3


@dataclass(frozen=True)
class Question:
    prompt: str
    answer: int
    choices: tuple[int, ...]
    operation: Operation
    difficulty: int

    def is_correct(self, response: int) -> bool:
        return response == self.answer


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
            Problem(f"{left} + {right}", left + right, Operation.ADDITION)
            for left in numbers
            for right in numbers
        ]


class SubtractionProblems:
    """The result is never negative."""

    def problems(self, difficulty: int) -> list[Problem]:
        return [
            Problem(f"{left} − {right}", left - right, Operation.SUBTRACTION)
            for left in range(1, max_operand(difficulty) + 1)
            for right in range(1, left + 1)
        ]


class MultiplicationProblems:
    def __init__(self, tables: Iterable[int]) -> None:
        self.tables = tuple(sorted(tables))

    def problems(self, difficulty: int) -> list[Problem]:
        return [
            Problem(f"{table} × {factor}", table * factor, Operation.MULTIPLICATION)
            for table in self.tables
            for factor in TABLE_FACTORS
        ]


class DivisionProblems:
    """The division tables: multiples of a table divided by it (e.g. 21 ÷ 7)."""

    def __init__(self, tables: Iterable[int]) -> None:
        self.tables = tuple(sorted(tables))

    def problems(self, difficulty: int) -> list[Problem]:
        return [
            Problem(f"{table * quotient} ÷ {table}", quotient, Operation.DIVISION)
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


class QuestionGenerator:
    """Turns problems into questions with answer choices.

    With several operations, each question first picks one of them at random,
    so they show up equally often (addition has hundreds of problems, a times
    table only 10). Reproducible when a ``Random`` is provided.
    """

    def __init__(
        self,
        makers: Sequence[ProblemMaker] | None = None,
        random: Random | None = None,
        choice_count: int = DEFAULT_CHOICE_COUNT,
    ) -> None:
        if choice_count < 2:
            raise ValueError("At least two answer choices are required.")
        if makers is not None and not makers:
            raise ValueError("At least one problem maker is required.")
        self._makers = makers or problems_for(DEFAULT_SETTINGS)
        self._random = random or Random()
        self._choice_count = choice_count

    def generate(self, difficulty: int = 1, avoid: Collection[str] = ()) -> Question:
        """A random question; avoids the prompts in ``avoid`` (e.g. the ones
        already on the board) unless every possible problem is in it."""
        if difficulty < 1:
            raise ValueError("Difficulty must be positive.")
        groups = [maker.problems(difficulty) for maker in self._makers]
        fresh = [[problem for problem in group if problem.prompt not in avoid] for group in groups]
        group = self._random.choice([group for group in fresh if group] or groups)
        prompt, answer, operation = self._random.choice(group)
        choices = self._make_choices(answer, difficulty)
        return Question(prompt, answer, choices, operation, difficulty)

    def _make_choices(self, answer: int, difficulty: int) -> tuple[int, ...]:
        # The range must fit every wrong choice, even when the answer is small
        # and negative values are clamped to zero.
        spread = max(self._choice_count - 1, difficulty + 1)
        choices = {answer}
        while len(choices) < self._choice_count:
            offset = self._random.randint(-spread, spread)
            if offset:
                choices.add(max(0, answer + offset))
        shuffled = list(choices)
        self._random.shuffle(shuffled)
        return tuple(shuffled)


QuestionFactory = Callable[[int, Collection[str]], Question]
"""Makes a question for a difficulty, avoiding the given prompts if possible."""


def question_factory_for(settings: GameSettings, random: Random | None = None) -> QuestionFactory:
    """Question factory for a game played with ``settings``."""
    return QuestionGenerator(problems_for(settings), random).generate
