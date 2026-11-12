"""Connects interface events to the game rules.

Each turn has a few seconds (``TURN_SECONDS``) to choose a cell and answer
its question; the controller keeps that time. When it runs out, an open
question counts as a miss (the cell gets the other player's mark); with no
question open, the turn passes. In a best of N, a line that scores shows in
gold for ``POINT_SECONDS`` (the board waits) before its cells disappear; the
next turn's time starts after that.

In hard mode it also runs the chess clock: the player whose turn it is uses
up their time, and whoever runs out of time loses the match. In a best of N
it runs the countdown of each played cell, which is open again at zero.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from ..cell_timers import CellTimers
from ..clock import ChessClock, Countdown
from ..game import TURN_SECONDS, Game, MoveResult, Position
from ..settings import GameSettings
from .ports import Screen
from .presenter import CellState, GamePresenter, ScoredLine, TimerState, TurnTime

GameFactory = Callable[[GameSettings], Game]
ClockFactory = Callable[[float], ChessClock]
CellTimersFactory = Callable[[], CellTimers]
CountdownFactory = Callable[[float], Countdown]

# Best of N: how long a line that scored stays in gold before it disappears.
POINT_SECONDS = 1


@dataclass(frozen=True)
class ShownPoint:
    """The line that just scored, in gold until ``countdown`` ends."""

    line: ScoredLine
    countdown: Countdown


class GameController:
    def __init__(
        self,
        new_game: GameFactory,
        settings: GameSettings,
        presenter: GamePresenter,
        screen: Screen,
        refresh: Callable[[], None],
        new_clock: ClockFactory = ChessClock,
        new_cell_timers: CellTimersFactory = CellTimers,
        new_countdown: CountdownFactory = Countdown,
    ) -> None:
        self._new_game = new_game
        self._new_clock = new_clock
        self._new_cell_timers = new_cell_timers
        self._new_countdown = new_countdown
        self._settings = settings
        self._presenter = presenter
        self._screen = screen
        self._refresh = refresh
        self._game = new_game(settings)
        self._clock: ChessClock | None = None
        self._shown_timers: tuple[TimerState, ...] = ()
        self._cell_timers: CellTimers | None = None
        self._shown_cells: list[CellState] = []
        self._shown_point: ShownPoint | None = None
        # The current turn's time (None while no turn runs: match over, a
        # point shown, screen left) and the cell whose question is open.
        self._turn_time: Countdown | None = None
        self._shown_turn_time: TurnTime | None = None
        self._open_position: Position | None = None
        # While ticking, redraws wait for the end of the tick: one per tick.
        self._ticking = False
        self._redraw_pending = False

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

    @property
    def cell_timers(self) -> CellTimers | None:
        """The cells' countdowns in a best of N; ``None`` otherwise."""
        return self._cell_timers

    def start(self) -> None:
        self._shown_point = None
        self._open_position = None
        self._start_clock()
        self._start_turn()
        self._render()

    def select_cell(self, position: Position) -> None:
        """Opens the cell's question, within the turn's time (it keeps
        running, even if the player cancels to choose another cell). Nothing
        opens while a point is shown."""
        if self._shown_point is not None or not self._game.is_available(position):
            return
        self._open_position = position
        self._screen.prompt.ask(
            self._game.questions[position],
            on_answer=lambda response: self._answer(position, response),
            on_cancel=self._question_closed,
        )
        self._show_turn_time()
        self._redraw()  # the seconds show as soon as the question does

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

    def request_leave(self, leave: Callable[[], None]) -> None:
        """The player wants to leave the game screen (settings button): asks
        first if that would throw away a match in progress; otherwise leaves
        right away."""
        if self._game.is_in_progress:
            self._screen.confirm_leave.confirm(leave)
        else:
            leave()

    def restart(self) -> None:
        """Starts a new match with the current settings."""
        self._game = self._new_game(self._settings)
        self._screen.status.show_feedback(None)
        self.start()

    def stop_clock(self) -> None:
        """The players left the game screen: the match is abandoned, so its
        clock and its cells' countdowns must not keep running (a new match
        starts when they return)."""
        if self._clock is not None:
            self._clock.stop()
        if self._cell_timers is not None:
            self._cell_timers.stop()
        self._turn_time = None
        self._open_position = None
        self._shown_point = None

    def tick(self) -> None:
        """Called a few times per second: runs the hard mode clock, the gold
        of a point, the best of N cells' countdowns and the turn's time. The
        screen is redrawn once at most, whatever changed."""
        self._ticking = True
        try:
            self._tick_all()
        finally:
            self._ticking = False
        if self._redraw_pending:
            self._redraw_pending = False
            self._refresh()

    def _redraw(self) -> None:
        """Redraws the screen now, or at the end of the running tick."""
        if self._ticking:
            self._redraw_pending = True
        else:
            self._refresh()

    def _tick_all(self) -> None:
        if self._clock is not None:
            self._tick_clock(self._clock)
        if self._shown_point is not None and self._shown_point.countdown.expired:
            self._shown_point = None  # the line disappears; the board is playable
            self._start_turn()
            self._render()
        if self._cell_timers is not None:
            self._tick_cells(self._cell_timers)
        if self._turn_time is not None:
            self._tick_turn_time(self._turn_time)

    def _tick_turn_time(self, countdown: Countdown) -> None:
        """When the turn's time runs out: an open question closes and counts
        as a miss (the cell gets the other player's mark); with no question
        open, the turn passes. Otherwise the seconds are redrawn when they
        change."""
        if not countdown.expired:
            if self._presenter.turn_time(countdown) != self._shown_turn_time:
                self._show_turn_time()
                self._redraw()
            return
        position = self._open_position
        if position is not None:
            self._open_position = None
            self._screen.prompt.close()
            self._played(self._game.miss(position), missed=True)
            return
        self._game.skip_turn()
        self._update_clock()
        self._screen.status.show_feedback(self._presenter.time_up())
        self._start_turn()
        self._render()

    def _start_turn(self) -> None:
        """A new turn gets ``TURN_SECONDS``; none runs once the match is over
        or while a point is shown."""
        if self._game.is_over or self._shown_point is not None:
            self._turn_time = None
        else:
            self._turn_time = self._new_countdown(TURN_SECONDS)

    def _show_turn_time(self) -> None:
        countdown = self._turn_time
        self._shown_turn_time = None if countdown is None else self._presenter.turn_time(countdown)
        self._screen.status.show_turn_time(self._shown_turn_time)
        if self._open_position is not None and self._shown_turn_time is not None:
            self._screen.prompt.show_time(self._shown_turn_time)

    def _question_closed(self) -> None:
        """The player canceled: the turn (and its time) goes on."""
        self._open_position = None

    def _tick_clock(self, clock: ChessClock) -> None:
        """Ends the match when the running player's time is up, and redraws
        the timers when they change."""
        loser = clock.expired()
        if loser is not None:
            clock.stop()
            self._game.time_out(loser)
            self._turn_time = None
            self._open_position = None
            self._screen.prompt.close()
            self._screen.status.show_feedback(self._presenter.ran_out_of_time(loser))
            self._render()
        elif self._presenter.timers(clock) != self._shown_timers:
            self._show_timers()
            self._redraw()

    def _tick_cells(self, cell_timers: CellTimers) -> None:
        """Opens the cells whose time is up, and redraws the countdowns when
        the shown seconds change."""
        expired = cell_timers.expired()
        if expired:
            for position in expired:
                self._game.reset_cell(position)
            self._update_clock()
            self._render()
        elif self._board_cells() != self._shown_cells:
            self._show_board()
            self._redraw()

    def _start_clock(self) -> None:
        limit = self._settings.time_limit
        self._clock = None if limit is None else self._new_clock(limit)
        self._cell_timers = self._new_cell_timers() if self._game.plays_for_points else None
        self._update_clock()

    def _update_clock(self) -> None:
        if self._clock is not None:
            self._clock.follow(self._game)
        if self._cell_timers is not None:
            self._cell_timers.follow(self._game)

    def _answer(self, position: Position, response: int) -> None:
        self._open_position = None
        if not self._game.is_available(position):
            return  # the match ended (time ran out) while the question was open
        self._played(self._game.answer(position, response))

    def _played(self, result: MoveResult, missed: bool = False) -> None:
        """Shows how a move went. A point that does not end the match shows
        its line in gold for ``POINT_SECONDS`` before it disappears."""
        self._update_clock()
        if result.point_for is not None and not self._game.is_over:
            self._shown_point = ShownPoint(
                ScoredLine(result.scored_cells, result.point_for),
                self._new_countdown(POINT_SECONDS),
            )
        self._screen.status.show_feedback(self._presenter.feedback(result, missed=missed))
        self._start_turn()
        self._render()

    def _show_timers(self) -> None:
        self._shown_timers = self._presenter.timers(self._clock)
        self._screen.timers.show_timers(self._shown_timers)

    def _board_cells(self) -> list[CellState]:
        line = self._shown_point.line if self._shown_point else None
        return self._presenter.cells(self._game, self._cell_timers, line)

    def _show_board(self) -> None:
        self._shown_cells = self._board_cells()
        self._screen.board.render(self._shown_cells)

    def _render(self) -> None:
        self._show_board()
        self._screen.score.show_score(self._presenter.score_board(self._game))
        self._screen.status.show_status(self._presenter.status(self._game))
        self._screen.restart.set_label(self._presenter.restart_label(self._game))
        self._show_timers()
        self._show_turn_time()
        self._redraw()
