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

    @property
    def opponent(self) -> Mark:
        return Mark.O if self is Mark.X else Mark.X


class GameStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    WON = "won"
    DRAW = "draw"


Position = int
Line = tuple[Position, Position, Position]


@dataclass(frozen=True)
class MoveResult:
    """How an answer went; the game itself holds the rest (board, turn,
    status, winner)."""

    correct: bool


class Game:
    BOARD_SIZE = 9
    # One line each for the rows, the columns and the diagonals.
    # fmt: off
    WINNING_LINES: tuple[Line, ...] = (
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6),
    )
    # fmt: on

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
        # Hard mode: the player who ran out of time (and lost the match).
        self.timed_out: Mark | None = None
        self._answers = 0

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

    @property
    def is_in_progress(self) -> bool:
        """Started (at least one answer, right or wrong) and not over yet:
        starting over would throw this match away."""
        return self._answers > 0 and not self.is_over

    def is_available(self, position: Position) -> bool:
        """Tells whether the cell can still be played in this match."""
        self._validate_position(position)
        return not self.is_over and self.board[position] is None

    def answer(self, position: Position, response: int) -> MoveResult:
        """Plays ``response`` to the question of ``position``.

        Right: the cell gets the current player's mark and, unless the match
        ends, the turn passes. Wrong: the cell stays open with a new question
        (the other player has seen the choices of the old one) and the turn
        passes too.
        """
        self._validate_position(position)
        if self.is_over:
            raise ValueError("The match is already over.")
        if self.board[position] is not None:
            raise ValueError("This cell is already taken.")

        self._answers += 1
        question = self.questions[position]
        if not question.is_correct(response):
            self.questions[position] = self._new_question(position)
            self._pass_turn()
            return MoveResult(correct=False)

        player = self.current_player
        self.board[position] = player
        self.winning_line = self._find_winning_line(player)
        if self.winning_line is not None:
            self.winner = player
            self.status = GameStatus.WON
        elif all(mark is not None for mark in self.board):
            self.status = GameStatus.DRAW
        else:
            self._pass_turn()
        return MoveResult(correct=True)

    def time_out(self, player: Mark) -> None:
        """``player`` ran out of time (hard mode): the other player wins."""
        if self.is_over:
            raise ValueError("The match is already over.")
        self.timed_out = player
        self.winner = player.opponent
        self.status = GameStatus.WON

    def _pass_turn(self) -> None:
        self.current_player = self.current_player.opponent

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
