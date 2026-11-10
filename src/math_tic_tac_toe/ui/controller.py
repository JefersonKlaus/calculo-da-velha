"""Connects interface events to the game rules.

In hard mode it also runs the chess clock: the player whose turn it is uses
up their time, and whoever runs out of time loses the match.
"""

from __future__ import annotations

from collections.abc import Callable

from ..clock import ChessClock
from ..game import Game, Position
from ..settings import GameSettings
from .ports import Screen
from .presenter import GamePresenter, TimerState

GameFactory = Callable[[GameSettings], Game]
ClockFactory = Callable[[float], ChessClock]


class GameController:
    def __init__(
        self,
        new_game: GameFactory,
        settings: GameSettings,
        presenter: GamePresenter,
        screen: Screen,
        refresh: Callable[[], None],
        new_clock: ClockFactory = ChessClock,
    ) -> None:
        self._new_game = new_game
        self._new_clock = new_clock
        self._settings = settings
        self._presenter = presenter
        self._screen = screen
        self._refresh = refresh
        self._game = new_game(settings)
        self._clock: ChessClock | None = None
        self._shown_timers: tuple[TimerState, ...] = ()

    @property
    def game(self) -> Game:
        return self._game

    @property
    def settings(self) -> GameSettings:
        return self._settings

    @property
    def clock(self) -> ChessClock | None:
        """The chess clock of the match in hard mode; ``None`` otherwise."""
        return self._clock

    def start(self) -> None:
        self._start_clock()
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

    def request_restart(self) -> None:
        """The player tapped the restart button: asks first if that would
        throw away a match in progress; otherwise starts over right away."""
        if self._game.is_in_progress:
            self._screen.confirm_restart.confirm(self.restart)
        else:
            self.restart()

    def restart(self) -> None:
        """Starts a new match with the current settings."""
        self._game = self._new_game(self._settings)
        self._screen.status.show_feedback(None)
        self.start()

    def stop_clock(self) -> None:
        """The players left the game screen: the match is abandoned, so its
        clock must not keep running (a new match starts when they return)."""
        if self._clock is not None:
            self._clock.stop()

    def tick(self) -> None:
        """Called a few times per second: ends the match when the running
        player's time is up, and redraws the timers when they change."""
        if self._clock is None:
            return
        loser = self._clock.expired()
        if loser is not None:
            self._clock.stop()
            self._game.time_out(loser)
            self._screen.prompt.close()
            self._screen.status.show_feedback(self._presenter.ran_out_of_time(loser))
            self._render()
        elif self._presenter.timers(self._clock) != self._shown_timers:
            self._show_timers()
            self._refresh()

    def _start_clock(self) -> None:
        limit = self._settings.time_limit
        self._clock = None if limit is None else self._new_clock(limit)
        self._update_clock()

    def _update_clock(self) -> None:
        if self._clock is not None:
            self._clock.follow(self._game)

    def _answer(self, position: Position, response: int) -> None:
        if not self._game.is_available(position):
            return  # the match ended (time ran out) while the question was open
        result = self._game.answer(position, response)
        self._update_clock()
        self._screen.status.show_feedback(self._presenter.feedback(result))
        self._render()

    def _show_timers(self) -> None:
        self._shown_timers = self._presenter.timers(self._clock)
        self._screen.timers.show_timers(self._shown_timers)

    def _render(self) -> None:
        self._screen.board.render(self._presenter.cells(self._game))
        self._screen.status.show_status(self._presenter.status(self._game))
        self._screen.restart.set_label(self._presenter.restart_label(self._game))
        self._show_timers()
        self._refresh()
