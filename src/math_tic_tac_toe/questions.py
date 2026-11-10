"""How the game asks: picks a problem (see ``problems``) for a cell and adds
the answer choices, one right and the others close to it."""

from __future__ import annotations

from collections.abc import Callable, Collection, Sequence
from dataclasses import dataclass
from random import Random

from .problems import ProblemMaker, problems_for
from .settings import DEFAULT_SETTINGS, GameSettings, Operation

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
