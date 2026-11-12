"""Turns the game state into translated data ready to be displayed.

This module knows nothing about Flet: it decides *what* to show (texts, which
player a message is about, whether an answer was right), not *how* it looks.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil

from ..cell_timers import CellTimers
from ..clock import ChessClock, Countdown
from ..game import Game, GameStatus, Mark, MoveResult, Position
from ..i18n import TextKey, Translator


@dataclass(frozen=True)
class CellState:
    label: str
    enabled: bool
    mark: Mark | None = None
    highlighted: bool = False
    # Best of N: whole seconds left before a played cell is open again (only
    # cells with a mark have them).
    seconds: int | None = None


@dataclass(frozen=True)
class StatusMessage:
    text: str
    player: Mark | None  # whose turn it is, or the winner; None on a draw
    won: bool = False  # the match is over and ``player`` won it


@dataclass(frozen=True)
class MessagePart:
    text: str
    player: Mark | None = None  # a player's symbol, shown in that player's color


@dataclass(frozen=True)
class FeedbackMessage:
    """The line below the status: red (an alert) unless ``alert`` is off,
    e.g. for a point scored. A player's symbol in it (e.g. the "O" of "O ran
    out of time.") keeps that player's color, so it is clear at a glance
    which player the message is about."""

    parts: tuple[MessagePart, ...]
    alert: bool = True

    @property
    def text(self) -> str:
        return "".join(part.text for part in self.parts)


# Hard mode: a timer turns red during its player's last seconds.
LOW_TIME_SECONDS = 10


@dataclass(frozen=True)
class TimerState:
    player: Mark
    time: str  # minutes:seconds, e.g. "0:59"
    running: bool  # it is this player's turn and their time is going down
    low: bool  # only a few seconds are left


@dataclass(frozen=True)
class ScoredLine:
    """Best of N: the line that just scored a point. The game has already
    cleared its cells; they are shown in gold, with the scorer's mark, for a
    moment before they disappear, so the players see where the point was."""

    cells: tuple[Position, ...]
    player: Mark


# The time left on a turn turns red during its last seconds.
LOW_TURN_SECONDS = 3


@dataclass(frozen=True)
class TurnTime:
    """Whole seconds left on the current turn to choose a cell and answer
    its question (10, 9, ... 1)."""

    seconds: int
    low: bool  # only a few seconds are left


@dataclass(frozen=True)
class ScoreState:
    player: Mark
    points: int


@dataclass(frozen=True)
class ScoreBoard:
    """Best of N: both players' points (X first) and what wins the match."""

    scores: tuple[ScoreState, ...]
    goal: str  # e.g. "First to 3 wins"


def clock_text(seconds: float) -> str:
    """``m:ss``, rounded up like a chess clock: it shows 0:00 only once the
    time is really over."""
    whole = ceil(seconds)
    return f"{whole // 60}:{whole % 60:02d}"


class GamePresenter:
    def __init__(self, translator: Translator) -> None:
        self._translator = translator

    def cells(
        self,
        game: Game,
        cell_timers: CellTimers | None = None,
        scored: ScoredLine | None = None,
    ) -> list[CellState]:
        """The board; the winner's cells are highlighted (gold): the winning
        line (or both, if the last move completed two), or every cell of the
        winner when the loser ran out of time.
        Best of N: played cells (only those) show their countdown while the
        match is on (rounded up: 32, 31, ... 1, and the cell is open again);
        and the line that just ``scored`` shows in gold while the whole board
        waits."""
        winning_cells = game.winning_cells
        cells = []
        for position, mark in enumerate(game.board):
            if scored is not None and position in scored.cells:
                cells.append(CellState(scored.player.value, False, scored.player, highlighted=True))
                continue
            won_on_time = game.timed_out is not None and mark is not None and mark is game.winner
            cells.append(
                CellState(
                    label=mark.value if mark else game.questions[position].prompt,
                    enabled=game.is_available(position) and scored is None,
                    mark=mark,
                    highlighted=position in winning_cells or won_on_time,
                    seconds=self._cell_seconds(game, position, cell_timers),
                )
            )
        return cells

    @staticmethod
    def _cell_seconds(game: Game, position: Position, cell_timers: CellTimers | None) -> int | None:
        """Best of N while the match is on: the countdown of a played cell;
        open cells have none."""
        if game.is_over or cell_timers is None:
            return None
        remaining = cell_timers.remaining(position)
        return None if remaining is None else ceil(remaining)

    def score_board(self, game: Game) -> ScoreBoard | None:
        """Best of N: the points of each player; ``None`` for a single game."""
        if not game.plays_for_points:
            return None
        return ScoreBoard(
            scores=tuple(ScoreState(player, game.scores[player]) for player in Mark),
            goal=self._translator.text(TextKey.POINTS_TO_WIN, points=game.points_to_win),
        )

    def status(self, game: Game) -> StatusMessage:
        if game.status is GameStatus.IN_PROGRESS:
            player = game.current_player
            return StatusMessage(self._translator.text(TextKey.TURN, player=player.value), player)
        if game.status is GameStatus.WON and game.winner is not None:
            winner = game.winner
            text = self._translator.text(TextKey.GAME_OVER_WIN, player=winner.value)
            return StatusMessage(text, winner, won=True)
        return StatusMessage(self._translator.text(TextKey.GAME_OVER_DRAW), None)

    def timers(self, clock: ChessClock | None) -> tuple[TimerState, ...]:
        """Both players' timers (X first) in hard mode; none otherwise."""
        if clock is None:
            return ()
        return tuple(
            TimerState(
                player=player,
                time=clock_text(clock.remaining(player)),
                running=clock.running is player,
                low=clock.remaining(player) <= LOW_TIME_SECONDS,
            )
            for player in Mark
        )

    def turn_time(self, countdown: Countdown) -> TurnTime:
        """Seconds left on the turn, rounded up: it shows 1 until the time
        is really over."""
        seconds = ceil(countdown.remaining())
        return TurnTime(seconds, low=seconds <= LOW_TURN_SECONDS)

    def restart_label(self, game: Game) -> str:
        """ "Restart" while the match is on; "Play again" once it is over."""
        key = TextKey.PLAY_AGAIN if game.is_over else TextKey.RESTART
        return self._translator.text(key)

    # Feedback: the red line below the status. It only speaks up when
    # something went wrong; a right answer needs no message.

    def ran_out_of_time(self, player: Mark) -> FeedbackMessage:
        """Why the match ended in hard mode (the status says who won), with
        the player's symbol in their color."""
        return FeedbackMessage(self._about(TextKey.RAN_OUT_OF_TIME, player))

    def feedback(self, result: MoveResult, missed: bool = False) -> FeedbackMessage | None:
        """ "Wrong answer." (red) after a wrong answer, or "Time's up!" when
        the player did not answer in time (``missed``); "Point for X!" (not
        an alert) after a line in a best of N ("2 points for X!" after two
        lines at once); nothing after other right ones. A wrong answer that
        gives the other player a point says both, in red: it is bad news for
        the player who answered."""
        wrong = MessagePart(
            self._translator.text(TextKey.TIME_UP if missed else TextKey.WRONG_ANSWER)
        )
        if result.point_for is not None:
            key = TextKey.POINTS_FOR if result.points > 1 else TextKey.POINT_FOR
            point = self._about(key, result.point_for, points=result.points)
            if result.correct:
                return FeedbackMessage(point, alert=False)
            return FeedbackMessage((wrong, MessagePart(" "), *point))
        if result.correct:
            return None
        return FeedbackMessage((wrong,))

    def time_up(self) -> FeedbackMessage:
        """The turn's time ran out before the player chose a cell."""
        return FeedbackMessage((MessagePart(self._translator.text(TextKey.TIME_UP)),))

    def _about(self, key: TextKey, player: Mark, **values: object) -> tuple[MessagePart, ...]:
        """The text of ``key`` with the player's symbol as its own part."""
        pieces = self._translator.pieces(key, player=player.value, **values)
        return tuple(
            MessagePart(piece.text, player if piece.field == "player" else None) for piece in pieces
        )
