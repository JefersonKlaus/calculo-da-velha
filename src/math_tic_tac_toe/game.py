"""Pure tic-tac-toe rules where each move requires solving a math question.

Getting it wrong (or not answering in time) is costly: the cell gets the
other player's mark.

A single game ends with the first line (or a draw). "Best of N" plays for
points instead: each line scores a point (two lines at once, two points) and
its cells are cleared, played cells only last a few seconds (see
``cell_seconds``), and the first player to reach the majority of N points
wins.

This module knows nothing about the interface or the user's language: it
reports *what happened* and the presentation layer decides how to say it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .questions import Question, QuestionFactory, QuestionGenerator, question_factory_for
from .settings import GameSettings, points_to_win


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

# Best of N: a played cell keeps its mark for as many seconds as the biggest
# number of its calculation (32 for 4 × 8 = 32), but never more than this.
MAX_CELL_SECONDS = 60

# Seconds a player has, on each turn, to choose a cell and answer its
# question. Time up with a question open counts as a wrong answer (see
# ``Game.miss``); without one, the turn passes (``Game.skip_turn``). The
# interface keeps the time.
TURN_SECONDS = 10


@dataclass(frozen=True)
class MoveResult:
    """How an answer went; the game itself holds the rest (board, turn,
    status, winner, scores)."""

    correct: bool
    # Best of N: the player who scored with this answer (a line); after a
    # wrong answer, the other player (their mark completed the line).
    point_for: Mark | None = None
    # Best of N: how many points it scored, one per completed line.
    points: int = 0
    # Best of N: the cells of the line(s) that scored, in board order (cleared
    # unless the point won the match).
    scored_cells: tuple[Position, ...] = ()


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
        best_of: int | None = None,
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
        # Every cell of the line(s) that won: a move may complete two at once.
        self.winning_cells: tuple[Position, ...] = ()
        # Hard mode: the player who ran out of time (and lost the match).
        self.timed_out: Mark | None = None
        # Best of N (None for a single game): points scored, one per line.
        self.best_of = best_of
        self.points_to_win = points_to_win(best_of)
        self.scores = dict.fromkeys(Mark, 0)
        self._answers = 0

    @classmethod
    def with_settings(cls, settings: GameSettings) -> Game:
        """A new game whose questions and mode follow ``settings``."""
        return cls(question_factory_for(settings), best_of=settings.best_of)

    @property
    def plays_for_points(self) -> bool:
        """Best of N: lines score points and are cleared."""
        return self.best_of is not None

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

        Right: the cell gets the current player's mark. Wrong: it gets the
        *other* player's mark. Either way, that mark counts like any other (it
        may complete a line) and, unless the match ends, the turn passes.

        Best of N: a line scores a point and its cells are cleared, unless
        that point wins the match (its line then stays, like a normal win).
        There is no draw: on a full board, played cells free up with time.
        """
        self._start_move(position)
        if not self.questions[position].is_correct(response):
            return self._mark(position, self.current_player.opponent, correct=False)
        return self._mark(position, self.current_player, correct=True)

    def miss(self, position: Position) -> MoveResult:
        """The current player's time (``TURN_SECONDS``) ran out while the
        question of ``position`` was open: it counts as a wrong answer, so the
        cell gets the other player's mark."""
        self._start_move(position)
        return self._mark(position, self.current_player.opponent, correct=False)

    def skip_turn(self) -> None:
        """The current player's time (``TURN_SECONDS``) ran out before they
        chose a cell: the turn passes. Nothing was answered, so this alone
        does not start the match (``is_in_progress``)."""
        if self.is_over:
            raise ValueError("The match is already over.")
        self._pass_turn()

    def cell_seconds(self, position: Position) -> int:
        """Best of N: how long a mark on ``position`` lasts, in seconds (or
        will last, for an open cell): the biggest number of its question, at
        most ``MAX_CELL_SECONDS``."""
        self._validate_position(position)
        return min(self.questions[position].largest_number, MAX_CELL_SECONDS)

    def reset_cell(self, position: Position) -> None:
        """Best of N: the time of a played cell ran out, so it is open again
        with a new question. The turn does not change."""
        self._validate_position(position)
        if not self.plays_for_points:
            raise ValueError("Only best of N matches reset cells.")
        if self.is_over:
            raise ValueError("The match is already over.")
        if self.board[position] is None:
            raise ValueError("This cell has no mark.")
        self._clear([position])

    def time_out(self, player: Mark) -> None:
        """``player`` ran out of time (hard mode): the other player wins."""
        if self.is_over:
            raise ValueError("The match is already over.")
        self.timed_out = player
        self.winner = player.opponent
        self.status = GameStatus.WON

    def _start_move(self, position: Position) -> None:
        self._validate_position(position)
        if self.is_over:
            raise ValueError("The match is already over.")
        if self.board[position] is not None:
            raise ValueError("This cell is already taken.")
        self._answers += 1

    def _mark(self, position: Position, player: Mark, correct: bool) -> MoveResult:
        """Puts ``player``'s mark on ``position`` (the current player's after a
        right answer, the other one's after a wrong one) and plays it out."""
        self.board[position] = player
        if self.plays_for_points:
            return self._score_lines(player, correct)
        lines = self._completed_lines(player)
        if lines:
            self._win(player, lines)
        elif all(mark is not None for mark in self.board):
            self.status = GameStatus.DRAW
        else:
            self._pass_turn()
        return MoveResult(correct=correct)

    def _score_lines(self, player: Mark, correct: bool) -> MoveResult:
        """Best of N, after ``player``'s mark was placed: one point per line it
        completed (two lines at once: two points). Reaching the points to win
        ends the match and keeps the lines (the score stops there); any other
        point clears the lines' cells."""
        lines = self._completed_lines(player)
        if not lines:
            self._pass_turn()
            return MoveResult(correct=correct)
        self.scores[player] = min(self.scores[player] + len(lines), self.points_to_win)
        scored = _cells_of(lines)
        if self.scores[player] >= self.points_to_win:
            self._win(player, lines)
        else:
            self._clear(list(scored))
            self._pass_turn()
        return MoveResult(correct=correct, point_for=player, points=len(lines), scored_cells=scored)

    def _win(self, player: Mark, lines: list[Line]) -> None:
        self.winner = player
        self.winning_line = lines[0]
        self.winning_cells = _cells_of(lines)
        self.status = GameStatus.WON

    def _clear(self, positions: list[Position]) -> None:
        """Opens ``positions`` again, each with a new question."""
        for position in positions:
            self.board[position] = None
        for position in positions:
            self.questions[position] = self._new_question(position)

    def _completed_lines(self, player: Mark) -> list[Line]:
        """The lines full of ``player``'s marks (a move may complete two)."""
        return [
            line
            for line in self.WINNING_LINES
            if all(self.board[position] is player for position in line)
        ]

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

    @staticmethod
    def _validate_position(position: Position) -> None:
        if not 0 <= position < Game.BOARD_SIZE:
            raise ValueError(f"Position must be between 0 and {Game.BOARD_SIZE - 1}.")


def _cells_of(lines: list[Line]) -> tuple[Position, ...]:
    """Every cell of ``lines``, once each, in board order."""
    return tuple(sorted({position for line in lines for position in line}))
