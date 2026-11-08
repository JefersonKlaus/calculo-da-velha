"""Regras puras do jogo da velha com perguntas matemáticas."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

from .questions import Question, QuestionGenerator


class Mark(str, Enum):
    X = "X"
    O = "O"


class GameStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    WON = "won"
    DRAW = "draw"


Position = int
QuestionFactory = Callable[[int], Question]


@dataclass(frozen=True)
class MoveResult:
    correct: bool
    position: Position
    status: GameStatus
    winner: Mark | None
    message: str


class Game:
    BOARD_SIZE = 9
    WINNING_LINES = (
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6),
    )

    def __init__(
        self,
        question_factory: QuestionFactory | None = None,
    ) -> None:
        generator = QuestionGenerator()
        self._question_factory = question_factory or generator.generate
        self.board: list[Mark | None] = [None] * self.BOARD_SIZE
        self.questions: list[Question] = [
            self._question_factory(self.difficulty_for(position))
            for position in range(self.BOARD_SIZE)
        ]
        self.current_player = Mark.X
        self.status = GameStatus.IN_PROGRESS
        self.winner: Mark | None = None

    @staticmethod
    def difficulty_for(position: Position) -> int:
        if not 0 <= position < Game.BOARD_SIZE:
            raise ValueError("A posição deve estar entre 0 e 8.")
        return 3 if position == 4 else (2 if position in (1, 3, 5, 7) else 1)

    def answer(self, position: Position, response: int) -> MoveResult:
        self._validate_position(position)
        if self.status is not GameStatus.IN_PROGRESS:
            raise ValueError("A partida já terminou.")
        if self.board[position] is not None:
            raise ValueError("Essa casa já está ocupada.")

        question = self.questions[position]
        if not question.is_correct(response):
            self.questions[position] = self._question_factory(self.difficulty_for(position))
            return MoveResult(False, position, self.status, None, "Resposta incorreta.")

        player = self.current_player
        self.board[position] = player
        self.winner = player if self._has_won(player) else None
        if self.winner is not None:
            self.status = GameStatus.WON
            message = f"{player.value} venceu!"
        elif all(mark is not None for mark in self.board):
            self.status = GameStatus.DRAW
            message = "Empate!"
        else:
            self.current_player = Mark.O if player is Mark.X else Mark.X
            message = "Resposta correta."
        return MoveResult(True, position, self.status, self.winner, message)

    def _has_won(self, player: Mark) -> bool:
        return any(all(self.board[position] is player for position in line) for line in self.WINNING_LINES)

    @staticmethod
    def _validate_position(position: Position) -> None:
        if not 0 <= position < Game.BOARD_SIZE:
            raise ValueError("A posição deve estar entre 0 e 8.")
