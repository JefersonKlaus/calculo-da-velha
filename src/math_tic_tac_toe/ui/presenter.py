"""Turns the game state into translated data ready to be displayed.

This module knows nothing about Flet: it decides *what* to show (texts, which
player a message is about, whether an answer was right), not *how* it looks.
"""

from __future__ import annotations

from dataclasses import dataclass

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
class FeedbackMessage:
    text: str
    correct: bool


class GamePresenter:
    def __init__(self, translator: Translator) -> None:
        self._translator = translator

    def cells(self, game: Game) -> list[CellState]:
        winning_line = game.winning_line or ()
        cells = []
        for position, mark in enumerate(game.board):
            cells.append(
                CellState(
                    label=mark.value if mark else game.questions[position].prompt,
                    enabled=game.is_available(position),
                    mark=mark,
                    highlighted=position in winning_line,
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

    def feedback(self, result: MoveResult) -> FeedbackMessage:
        key = TextKey.CORRECT_ANSWER if result.correct else TextKey.WRONG_ANSWER
        return FeedbackMessage(self._translator.text(key), result.correct)
