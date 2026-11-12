"""Best of N: each played cell counts down, in real time, to being open again."""

from collections.abc import Collection

from math_tic_tac_toe.cell_timers import CellTimers
from math_tic_tac_toe.game import Game
from math_tic_tac_toe.questions import Question
from math_tic_tac_toe.settings import Operation
from tests.support import FakeTime


def seconds_factory(difficulty: int, avoid: Collection[str] = ()) -> Question:
    """Cells of difficulty 1, 2 and 3 last 10, 20 and 30 seconds."""
    prompt = f"{10 * difficulty} ÷ 1"
    return Question(prompt, 10 * difficulty, (10 * difficulty, 1), Operation.DIVISION, difficulty)


def setup() -> tuple[Game, CellTimers, FakeTime]:
    time = FakeTime()
    return Game(seconds_factory, best_of=5), CellTimers(now=time), time


def test_a_played_cell_counts_down_from_its_seconds() -> None:
    game, timers, time = setup()
    game.answer(0, 10)  # difficulty 1: 10 seconds
    timers.follow(game)
    assert timers.remaining(0) == 10
    assert timers.remaining(1) is None  # open cells do not count down

    time.advance(3.5)
    assert timers.remaining(0) == 6.5
    assert timers.expired() == []


def test_a_cell_expires_when_its_time_is_up() -> None:
    game, timers, time = setup()
    game.answer(4, 30)  # X in the center: 30 seconds
    timers.follow(game)
    game.answer(0, 10)  # O in a corner: 10 seconds, started later
    time.advance(2)
    timers.follow(game)

    time.advance(10)
    assert timers.expired() == [0]
    assert timers.remaining(0) == 0  # never negative
    time.advance(18)
    assert timers.expired() == [0, 4]


def test_following_does_not_restart_a_running_countdown() -> None:
    game, timers, time = setup()
    game.answer(0, 10)
    timers.follow(game)
    time.advance(4)
    game.answer(1, 20)  # another move
    timers.follow(game)
    assert timers.remaining(0) == 6
    assert timers.remaining(1) == 20


def test_an_open_cell_is_forgotten_and_starts_again_when_played() -> None:
    game, timers, time = setup()
    game.answer(0, 10)
    timers.follow(game)
    time.advance(10)
    game.reset_cell(0)
    timers.follow(game)
    assert timers.remaining(0) is None
    assert timers.expired() == []

    game.answer(1, 999)  # X is wrong; O plays the cell again
    game.answer(0, 10)
    timers.follow(game)
    assert timers.remaining(0) == 10  # a fresh countdown


def test_everything_stops_once_the_match_is_over() -> None:
    game, timers, time = setup()
    game.answer(0, 10)
    timers.follow(game)
    game.time_out(game.current_player)  # any end of the match
    timers.follow(game)
    time.advance(100)
    assert timers.remaining(0) is None
    assert timers.expired() == []


def test_stop_forgets_every_countdown() -> None:
    game, timers, time = setup()
    game.answer(0, 10)
    timers.follow(game)
    timers.stop()
    time.advance(100)
    assert timers.expired() == []
