"""Best of N: the countdown of each played cell.

A mark only lasts ``Game.cell_seconds`` (the biggest number of the calculation
answered there, at most 60). Its countdown starts when the cell is played and
runs in real time for both players; when it reaches zero the cell is open
again (``Game.reset_cell``).

Pure logic (no Flet): the current time comes from ``now``, so tests can
control it.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from .game import Game, Position

TimeSource = Callable[[], float]


class CellTimers:
    def __init__(self, now: TimeSource = time.monotonic) -> None:
        self._now = now
        self._deadlines: dict[Position, float] = {}

    def follow(self, game: Game) -> None:
        """Starts the countdown of every newly played cell and forgets the
        cells that are open again; stops everything once the match is over."""
        if game.is_over:
            self.stop()
            return
        for position, mark in enumerate(game.board):
            if mark is None:
                self._deadlines.pop(position, None)
            elif position not in self._deadlines:
                self._deadlines[position] = self._now() + game.cell_seconds(position)

    def stop(self) -> None:
        """The match is over or abandoned: no cell counts down anymore."""
        self._deadlines.clear()

    def remaining(self, position: Position) -> float | None:
        """Seconds left on a played cell (never negative); ``None`` if that
        cell is not counting down."""
        deadline = self._deadlines.get(position)
        return None if deadline is None else max(0.0, deadline - self._now())

    def expired(self) -> list[Position]:
        """The played cells whose time is up, in board order."""
        now = self._now()
        return sorted(position for position, deadline in self._deadlines.items() if deadline <= now)
