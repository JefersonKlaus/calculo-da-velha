"""Turns the game state into translated data ready to be displayed.

This module knows nothing about Flet: it decides *what* to show (texts, which
player a message is about, whether an answer was right), not *how* it looks.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil

from ..clock import ChessClock
from ..game import Game, GameStatus, Mark, MoveResult
from ..i18n import TextKey, Translator


@dataclass(frozen=True)
class CellState:
    label: str
    enabled: bool
    mark: Mark | None = None
    highlighted: bool = False


@dataclass(frozen=True)
class StatusMessage:
    text: str
    player: Mark | None  # whose turn it is, or the winner; None on a draw


@dataclass(frozen=True)
class MessagePart:
    text: str
    player: Mark | None = None  # a player's symbol, shown in that player's color


@dataclass(frozen=True)
class FeedbackMessage:
    """The red line below the status. A player's symbol in it (e.g. the "O"
    of "O ran out of time.") keeps that player's color, so it is clear at a
    glance which player the message is about."""

    parts: tuple[MessagePart, ...]

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


def clock_text(seconds: float) -> str:
    """``m:ss``, rounded up like a chess clock: it shows 0:00 only once the
    time is really over."""
    whole = ceil(seconds)
    return f"{whole // 60}:{whole % 60:02d}"


class GamePresenter:
    def __init__(self, translator: Translator) -> None:
        self._translator = translator

    def cells(self, game: Game) -> list[CellState]:
        """The board; the winner's cells are highlighted (gold): the winning
        line, or every cell of the winner when the loser ran out of time."""
        winning_line = game.winning_line or ()
        cells = []
        for position, mark in enumerate(game.board):
            won_on_time = game.timed_out is not None and mark is not None and mark is game.winner
            cells.append(
                CellState(
                    label=mark.value if mark else game.questions[position].prompt,
                    enabled=game.is_available(position),
                    mark=mark,
                    highlighted=position in winning_line or won_on_time,
                )
            )
        return cells

    def status(self, game: Game) -> StatusMessage:
        if game.status is GameStatus.IN_PROGRESS:
            player = game.current_player
            return StatusMessage(self._translator.text(TextKey.TURN, player=player.value), player)
        if game.status is GameStatus.WON and game.winner is not None:
            winner = game.winner
            text = self._translator.text(TextKey.GAME_OVER_WIN, player=winner.value)
            return StatusMessage(text, winner)
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

    def restart_label(self, game: Game) -> str:
        """ "Restart" while the match is on; "Play again" once it is over."""
        key = TextKey.PLAY_AGAIN if game.is_over else TextKey.RESTART
        return self._translator.text(key)

    # Feedback: the red line below the status. It only speaks up when
    # something went wrong; a right answer needs no message.

    def ran_out_of_time(self, player: Mark) -> FeedbackMessage:
        """Why the match ended in hard mode (the status says who won), with
        the player's symbol in their color."""
        pieces = self._translator.pieces(TextKey.RAN_OUT_OF_TIME, player=player.value)
        return FeedbackMessage(
            tuple(
                MessagePart(piece.text, player if piece.field == "player" else None)
                for piece in pieces
            )
        )

    def feedback(self, result: MoveResult) -> FeedbackMessage | None:
        """ "Wrong answer." after a wrong answer; nothing after a right one."""
        if result.correct:
            return None
        return FeedbackMessage((MessagePart(self._translator.text(TextKey.WRONG_ANSWER)),))
