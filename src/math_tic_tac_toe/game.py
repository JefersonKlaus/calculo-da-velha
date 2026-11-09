"""Pure tic-tac-toe rules where each move requires solving a math question.

This module knows nothing about the interface or the user's language: it
reports *what happened* and the presentation layer decides how to say it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .questions import Question, QuestionFactory, QuestionGenerator, question_factory_for
from .settings import GameSettings


class Mark(str, Enum):
    X = "X"
    O = "O"  # noqa: E741 - the tic-tac-toe mark, not a variable that may look like 0


class GameStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    WON = "won"
    DRAW = "draw"


Position = int
Line = tuple[Position, Position, Position]


@dataclass(frozen=True)
class MoveResult:
    correct: bool
    position: Position
    status: GameStatus
    winner: Mark | None


class Game:
    BOARD_SIZE = 9
    WINNING_LINES: tuple[Line, ...] = (
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
        self.questions: list[Question] = []
        for position in range(self.BOARD_SIZE):
            self.questions.append(self._new_question(position))
        self.current_player = Mark.X
        self.status = GameStatus.IN_PROGRESS
        self.winner: Mark | None = None
        self.winning_line: Line | None = None

    @classmethod
    def with_settings(cls, settings: GameSettings) -> Game:
        """A new game whose questions follow ``settings``."""
        return cls(question_factory_for(settings))

    @staticmethod
    def difficulty_for(position: Position) -> int:
        Game._validate_position(position)
        return 3 if position == 4 else (2 if position in (1, 3, 5, 7) else 1)

    @property
    def is_over(self) -> bool:
        return self.status is not GameStatus.IN_PROGRESS

    def is_available(self, position: Position) -> bool:
        """Tells whether the cell can still be played in this match."""
        self._validate_position(position)
        return not self.is_over and self.board[position] is None

    def answer(self, position: Position, response: int) -> MoveResult:
        self._validate_position(position)
        if self.is_over:
            raise ValueError("The match is already over.")
        if self.board[position] is not None:
            raise ValueError("This cell is already taken.")

        question = self.questions[position]
        if not question.is_correct(response):
            self.questions[position] = self._new_question(position)
            return MoveResult(False, position, self.status, None)

        player = self.current_player
        self.board[position] = player
        self.winning_line = self._find_winning_line(player)
        if self.winning_line is not None:
            self.winner = player
            self.status = GameStatus.WON
        elif all(mark is not None for mark in self.board):
            self.status = GameStatus.DRAW
        else:
            self.current_player = Mark.O if player is Mark.X else Mark.X
        return MoveResult(True, position, self.status, self.winner)

    def _new_question(self, position: Position) -> Question:
        """A question for ``position`` that differs from every question on the
        open cells (including the one it replaces), when the pool allows it."""
        shown = {
            question.prompt
            for other, question in enumerate(self.questions)
            if self.board[other] is None
        }
        return self._question_factory(self.difficulty_for(position), shown)

    def _find_winning_line(self, player: Mark) -> Line | None:
        for line in self.WINNING_LINES:
            if all(self.board[position] is player for position in line):
                return line
        return None

    @staticmethod
    def _validate_position(position: Position) -> None:
        if not 0 <= position < Game.BOARD_SIZE:
            raise ValueError(f"Position must be between 0 and {Game.BOARD_SIZE - 1}.")
