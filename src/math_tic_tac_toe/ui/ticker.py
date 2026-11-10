"""Background loop that drives the hard mode clock while the app runs."""

from __future__ import annotations

import asyncio
from collections.abc import Callable

# Often enough for the timers to change right on each second and for the
# match to end right when the time runs out; the screen itself is only
# redrawn when the shown time changes.
TICK_SECONDS = 0.1


async def tick_forever(on_tick: Callable[[], None], interval: float = TICK_SECONDS) -> None:
    """Calls ``on_tick`` every ``interval`` seconds, until the app closes."""
    while True:
        await asyncio.sleep(interval)
        on_tick()
