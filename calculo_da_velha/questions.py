"""Geração de perguntas matemáticas do jogo."""

from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Iterable


@dataclass(frozen=True)
class Question:
    prompt: str
    answer: int
    choices: tuple[int, ...]
    operation: str
    difficulty: int

    def is_correct(self, response: int) -> bool:
        return response == self.answer


class QuestionGenerator:
    """Gera contas reproduzíveis quando um ``Random`` é fornecido."""

    def __init__(
        self,
        multiplication_tables: Iterable[int] = range(2, 11),
        random: Random | None = None,
    ) -> None:
        tables = tuple(sorted(set(multiplication_tables)))
        if not tables or any(table < 0 for table in tables):
            raise ValueError("É necessário informar tabuadas não negativas.")
        self._tables = tables
        self._random = random or Random()

    def generate(self, difficulty: int = 1) -> Question:
        if difficulty < 1:
            raise ValueError("A dificuldade deve ser positiva.")

        operation = self._random.choice(("multiplication", "division"))
        left = self._random.choice(self._tables)
        factor = self._random.randint(2, 5 + difficulty * 2)

        if operation == "multiplication":
            right = factor
            answer = left * right
            prompt = f"{left} × {right}"
        else:
            answer = left
            dividend = left * factor
            prompt = f"{dividend} ÷ {factor}"

        choices = self._make_choices(answer, difficulty)
        return Question(prompt, answer, choices, operation, difficulty)

    def _make_choices(self, answer: int, difficulty: int) -> tuple[int, ...]:
        spread = max(2, difficulty + 1)
        choices = {answer}
        while len(choices) < 4:
            offset = self._random.randint(-spread, spread)
            if offset:
                choices.add(max(0, answer + offset))
        shuffled = list(choices)
        self._random.shuffle(shuffled)
        return tuple(shuffled)
