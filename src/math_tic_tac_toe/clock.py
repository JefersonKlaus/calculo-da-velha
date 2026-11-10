"""Chess clock for hard mode: each player has a fixed amount of time for the
whole match, and only the player whose turn it is uses it up.

Pure logic (no Flet): the current time comes from ``now``, so tests can
control it.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from .game import Game, Mark

TimeSource = Callable[[], float]


class ChessClock:
    def __init__(self, seconds: float, now: TimeSource = time.monotonic) -> None:
        self._now = now
        self._left = dict.fromkeys(Mark, float(seconds))
        self._running: Mark | None = None
        self._since = 0.0

    @property
    def running(self) -> Mark | None:
        """The player whose time is running, or ``None`` while stopped."""
        return self._running

    def start(self, player: Mark) -> None:
        """Stops the running player's time (if any) and runs ``player``'s."""
        self.stop()
        self._running = player
        self._since = self._now()

    def follow(self, game: Game) -> None:
        """Runs the time of the player whose turn it is in ``game``; stops
        once the match is over."""
        if game.is_over:
            self.stop()
        else:
            self.start(game.current_player)

    def stop(self) -> None:
        if self._running is not None:
            self._left[self._running] = self.remaining(self._running)
            self._running = None

    def remaining(self, player: Mark) -> float:
        """Seconds ``player`` still has (never negative)."""
        left = self._left[player]
        if player is self._running:
            left -= self._now() - self._since
        return max(0.0, left)

    def expired(self) -> Mark | None:
        """The running player, if their time is up."""
        if self._running is not None and self.remaining(self._running) <= 0:
            return self._running
        return None
