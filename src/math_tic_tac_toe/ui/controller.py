"""Connects interface events to the game rules."""

from __future__ import annotations

from collections.abc import Callable

from ..game import Game, Position
from ..settings import GameSettings
from .ports import Screen
from .presenter import GamePresenter

GameFactory = Callable[[GameSettings], Game]


class GameController:
    def __init__(
        self,
        new_game: GameFactory,
        settings: GameSettings,
        presenter: GamePresenter,
        screen: Screen,
        refresh: Callable[[], None],
    ) -> None:
        self._new_game = new_game
        self._settings = settings
        self._presenter = presenter
        self._screen = screen
        self._refresh = refresh
        self._game = new_game(settings)

    @property
    def game(self) -> Game:
        return self._game

    @property
    def settings(self) -> GameSettings:
        return self._settings

    def start(self) -> None:
        self._render()

    def select_cell(self, position: Position) -> None:
        if not self._game.is_available(position):
            return
        question = self._game.questions[position]
        self._screen.prompt.ask(question, lambda response: self._answer(position, response))

    def play(self, settings: GameSettings) -> None:
        """Starts a new match with new settings."""
        self._settings = settings
        self.restart()

    def restart(self) -> None:
        """Starts a new match with the current settings."""
        self._game = self._new_game(self._settings)
        self._screen.status.show_feedback(None)
        self._render()

    def _answer(self, position: Position, response: int) -> None:
        result = self._game.answer(position, response)
        self._screen.status.show_feedback(self._presenter.feedback(result))
        self._render()

    def _render(self) -> None:
        self._screen.board.render(self._presenter.cells(self._game))
        self._screen.status.show_status(self._presenter.status(self._game))
        self._screen.restart.set_visible(self._game.is_over)
        self._refresh()
