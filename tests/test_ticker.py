import asyncio

import pytest

from math_tic_tac_toe.ui.ticker import TICK_SECONDS, tick_forever


class StopTickingError(Exception):
    pass


def test_ticks_repeatedly_until_the_app_stops_it() -> None:
    ticks: list[None] = []

    def on_tick() -> None:
        ticks.append(None)
        if len(ticks) == 3:
            raise StopTickingError

    with pytest.raises(StopTickingError):
        asyncio.run(tick_forever(on_tick, interval=0))
    assert len(ticks) == 3


def test_ticks_often_enough_for_a_clock_shown_in_seconds() -> None:
    assert 0 < TICK_SECONDS <= 0.25
