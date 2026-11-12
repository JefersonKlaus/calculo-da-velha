import pytest

from math_tic_tac_toe.clock import ChessClock, Countdown
from math_tic_tac_toe.game import Game, Mark
from tests.support import FakeTime, question_factory


def make_clock(seconds: float = 60) -> tuple[ChessClock, FakeTime]:
    time = FakeTime()
    return ChessClock(seconds, now=time), time


def test_starts_stopped_with_the_full_time_for_both() -> None:
    clock, time = make_clock()
    time.advance(30)
    assert clock.running is None
    assert clock.remaining(Mark.X) == clock.remaining(Mark.O) == 60
    assert clock.expired() is None


def test_only_the_running_player_loses_time() -> None:
    clock, time = make_clock()
    clock.start(Mark.X)
    time.advance(12.5)
    assert clock.running is Mark.X
    assert clock.remaining(Mark.X) == pytest.approx(47.5)
    assert clock.remaining(Mark.O) == 60


def test_switching_keeps_what_each_player_has_left() -> None:
    clock, time = make_clock()
    clock.start(Mark.X)
    time.advance(10)
    clock.start(Mark.O)
    time.advance(25)
    clock.start(Mark.X)
    time.advance(5)
    assert clock.remaining(Mark.X) == pytest.approx(45)
    assert clock.remaining(Mark.O) == pytest.approx(35)


def test_stop_freezes_both_times() -> None:
    clock, time = make_clock()
    clock.start(Mark.O)
    time.advance(20)
    clock.stop()
    time.advance(100)
    assert clock.running is None
    assert clock.remaining(Mark.O) == pytest.approx(40)
    assert clock.expired() is None


def test_the_running_player_expires_at_zero_and_never_goes_negative() -> None:
    clock, time = make_clock(10)
    clock.start(Mark.X)
    time.advance(9.9)
    assert clock.expired() is None
    time.advance(5)
    assert clock.expired() is Mark.X
    assert clock.remaining(Mark.X) == 0


def test_uses_the_real_time_by_default() -> None:
    clock = ChessClock(60)
    clock.start(Mark.X)
    assert 59 < clock.remaining(Mark.X) <= 60


def test_follows_the_turn_of_the_match_and_stops_when_it_ends() -> None:
    clock, _ = make_clock()
    game = Game(question_factory)
    clock.follow(game)
    assert clock.running is Mark.X
    game.answer(0, 999)  # X is wrong: O's turn
    clock.follow(game)
    assert clock.running is Mark.O
    game.time_out(Mark.O)
    clock.follow(game)
    assert clock.running is None


def test_countdown_runs_from_its_creation() -> None:
    time = FakeTime()
    time.advance(50)
    countdown = Countdown(10, now=time)
    assert countdown.remaining() == 10
    assert not countdown.expired
    time.advance(9.5)
    assert countdown.remaining() == 0.5
    time.advance(0.5)
    assert countdown.expired
    time.advance(5)
    assert countdown.remaining() == 0  # never negative
