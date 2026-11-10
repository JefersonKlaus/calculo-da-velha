from collections.abc import Sequence
from functools import partial

from math_tic_tac_toe.clock import ChessClock
from math_tic_tac_toe.game import Game, GameStatus, Mark
from math_tic_tac_toe.questions import Question
from math_tic_tac_toe.settings import (
    DEFAULT_SETTINGS,
    OPERATIONS,
    TABLES,
    GameSettings,
    Operation,
)
from math_tic_tac_toe.ui.controller import GameController
from math_tic_tac_toe.ui.ports import AnswerHandler, ConfirmHandler, Screen
from math_tic_tac_toe.ui.presenter import (
    CellState,
    FeedbackMessage,
    MessagePart,
    StatusMessage,
    TimerState,
)
from tests.support import FakeTime, english_presenter, question_factory, settings_of


class FakeBoard:
    def __init__(self) -> None:
        self.cells: list[CellState] = []

    def render(self, cells: Sequence[CellState]) -> None:
        self.cells = list(cells)


class FakeStatus:
    def __init__(self) -> None:
        self.status: StatusMessage | None = None
        self.feedback: FeedbackMessage | None = None

    def show_status(self, message: StatusMessage) -> None:
        self.status = message

    def show_feedback(self, message: FeedbackMessage | None) -> None:
        self.feedback = message

    @property
    def feedback_text(self) -> str | None:
        return self.feedback.text if self.feedback else None


class FakePrompt:
    def __init__(self) -> None:
        self.question: Question | None = None
        self.on_answer: AnswerHandler | None = None

        self.is_open = False

    def ask(self, question: Question, on_answer: AnswerHandler) -> None:
        self.question = question
        self.on_answer = on_answer
        self.is_open = True

    def choose(self, response: int) -> None:
        assert self.on_answer is not None
        self.is_open = False
        self.on_answer(response)

    def close(self) -> None:
        self.is_open = False


class FakeRestart:
    def __init__(self) -> None:
        self.label: str | None = None

    def set_label(self, label: str) -> None:
        self.label = label


class FakeConfirmation:
    def __init__(self) -> None:
        self.asked = 0
        self.on_confirm: ConfirmHandler | None = None

    def confirm(self, on_confirm: ConfirmHandler) -> None:
        self.asked += 1
        self.on_confirm = on_confirm

    def accept(self) -> None:
        assert self.on_confirm is not None
        self.on_confirm()


class FakeTimers:
    def __init__(self) -> None:
        self.timers: tuple[TimerState, ...] = ()
        self.shown = 0

    def show_timers(self, timers: Sequence[TimerState]) -> None:
        self.timers = tuple(timers)
        self.shown += 1

    def times(self) -> tuple[str, ...]:
        return tuple(timer.time for timer in self.timers)


class Harness:
    """A controller wired to fake screen parts, with a hand-driven clock."""

    def __init__(self, settings: GameSettings = DEFAULT_SETTINGS) -> None:
        self.board = FakeBoard()
        self.status = FakeStatus()
        self.prompt = FakePrompt()
        self.restart = FakeRestart()
        self.confirmation = FakeConfirmation()
        self.timers = FakeTimers()
        self.time = FakeTime()
        self.refreshes = 0
        self.games_created: list[GameSettings] = []
        self.controller = GameController(
            new_game=self._new_game,
            settings=settings,
            presenter=english_presenter(),
            screen=Screen(
                self.board,
                self.status,
                self.prompt,
                self.restart,
                self.confirmation,
                self.timers,
            ),
            refresh=self._refresh,
            new_clock=partial(ChessClock, now=self.time),
        )
        self.controller.start()

    def _new_game(self, settings: GameSettings) -> Game:
        self.games_created.append(settings)
        return Game(question_factory)

    def _refresh(self) -> None:
        self.refreshes += 1

    @property
    def game(self) -> Game:
        return self.controller.game

    def play(self, *positions: int, response: int = 1) -> None:
        for position in positions:
            self.controller.select_cell(position)
            self.prompt.choose(response)


def test_start_renders_board_status_and_offers_restart() -> None:
    harness = Harness()
    assert len(harness.board.cells) == 9
    assert harness.status.status == StatusMessage("X's turn", Mark.X)
    assert harness.status.feedback is None
    assert harness.restart.label == "Restart"
    assert harness.refreshes == 1


def test_selecting_cell_asks_its_question() -> None:
    harness = Harness()
    harness.controller.select_cell(4)
    assert harness.prompt.question is harness.game.questions[4]


def test_correct_choice_marks_cell_and_passes_turn() -> None:
    harness = Harness()
    harness.play(0)
    assert harness.game.board[0] is Mark.X
    assert harness.board.cells[0].label == "X"
    assert harness.status.status == StatusMessage("O's turn", Mark.O)
    assert harness.status.feedback is None  # a right answer needs no message


def test_a_right_answer_clears_the_last_wrong_answer_message() -> None:
    harness = Harness()
    harness.play(0, response=2)  # X is wrong
    assert harness.status.feedback_text == "Wrong answer."
    harness.play(0)  # O is right
    assert harness.status.feedback is None


def test_wrong_choice_shows_feedback_and_passes_turn() -> None:
    harness = Harness()
    harness.play(0, response=2)
    assert harness.game.board[0] is None
    assert harness.board.cells[0].enabled
    assert harness.status.status == StatusMessage("O's turn", Mark.O)
    assert harness.status.feedback_text == "Wrong answer."
    assert harness.restart.label == "Restart"


def test_unavailable_cell_does_not_open_the_prompt() -> None:
    harness = Harness()
    harness.play(0)
    harness.prompt.question = None
    harness.controller.select_cell(0)
    assert harness.prompt.question is None


def test_restart_becomes_play_again_when_the_game_ends() -> None:
    harness = Harness()
    harness.play(0, 3, 1, 4)
    assert harness.restart.label == "Restart"
    harness.play(2)
    assert harness.game.status is GameStatus.WON
    assert harness.restart.label == "Play again"


def test_restart_starts_a_fresh_game() -> None:
    harness = Harness()
    harness.play(0, 3, 1, 4, 2)
    finished = harness.game

    harness.controller.restart()

    assert harness.game is not finished
    assert harness.games_created == [DEFAULT_SETTINGS, DEFAULT_SETTINGS]
    assert harness.game.board == [None] * 9
    assert all(cell.enabled and not cell.highlighted for cell in harness.board.cells)
    assert harness.status.status == StatusMessage("X's turn", Mark.X)
    assert harness.status.feedback is None
    assert harness.restart.label == "Restart"


def test_play_starts_a_new_match_with_the_new_settings() -> None:
    harness = Harness()
    harness.play(0, 3)
    division_of_7 = settings_of([Operation.DIVISION], [7])

    harness.controller.play(division_of_7)

    assert harness.controller.settings == division_of_7
    assert harness.games_created[-1] == division_of_7
    assert harness.game.board == [None] * 9
    assert harness.status.status == StatusMessage("X's turn", Mark.X)
    assert harness.restart.label == "Restart"


def test_restart_button_asks_first_when_a_match_is_in_progress() -> None:
    harness = Harness()
    harness.play(0, 3)
    in_progress = harness.game

    harness.controller.request_restart()

    assert harness.confirmation.asked == 1
    assert harness.game is in_progress  # nothing happens until the player agrees
    assert harness.game.board[0] is Mark.X


def test_confirming_starts_a_fresh_match() -> None:
    harness = Harness()
    harness.play(0, 3)
    harness.controller.request_restart()

    harness.confirmation.accept()

    assert harness.game.board == [None] * 9
    assert harness.status.status == StatusMessage("X's turn", Mark.X)
    assert harness.status.feedback is None
    assert harness.games_created == [DEFAULT_SETTINGS, DEFAULT_SETTINGS]


def test_restart_button_does_not_ask_before_the_first_answer() -> None:
    harness = Harness()
    harness.controller.request_restart()
    assert harness.confirmation.asked == 0
    assert len(harness.games_created) == 2  # restarted right away


def test_play_again_does_not_ask_once_the_match_is_over() -> None:
    harness = Harness()
    harness.play(0, 3, 1, 4, 2)
    assert harness.restart.label == "Play again"

    harness.controller.request_restart()

    assert harness.confirmation.asked == 0
    assert harness.game.board == [None] * 9


def test_restart_keeps_the_current_settings() -> None:
    harness = Harness()
    everything = settings_of(OPERATIONS, TABLES)
    harness.controller.play(everything)
    harness.controller.restart()
    assert harness.games_created[-1] == everything


# ---- hard mode: the chess clock -------------------------------------------

HARD = DEFAULT_SETTINGS.with_time_limit(60)


def test_normal_mode_has_no_clock_and_no_timers() -> None:
    harness = Harness()
    assert harness.controller.clock is None
    assert harness.timers.timers == ()
    harness.time.advance(1000)
    refreshes = harness.refreshes
    harness.controller.stop_clock()  # leaving the game: nothing to stop
    harness.controller.tick()
    assert harness.refreshes == refreshes  # nothing to do
    assert harness.game.status is GameStatus.IN_PROGRESS


def test_hard_mode_starts_x_clock_with_the_chosen_time() -> None:
    harness = Harness(HARD)
    clock = harness.controller.clock
    assert clock is not None
    assert clock.running is Mark.X
    assert harness.timers.timers == (
        TimerState(Mark.X, "1:00", running=True, low=False),
        TimerState(Mark.O, "1:00", running=False, low=False),
    )


def test_only_the_player_whose_turn_it_is_loses_time() -> None:
    harness = Harness(HARD)
    harness.time.advance(15)
    harness.play(0)  # X answers right: now O's time runs
    harness.time.advance(20)
    harness.controller.tick()
    assert harness.timers.times() == ("0:45", "0:40")
    assert [timer.running for timer in harness.timers.timers] == [False, True]


def test_a_wrong_answer_also_passes_the_clock() -> None:
    harness = Harness(HARD)
    harness.play(0, response=2)  # X is wrong: O's turn, O's clock
    clock = harness.controller.clock
    assert clock is not None
    assert clock.running is Mark.O


def test_tick_redraws_only_when_the_shown_time_changes() -> None:
    harness = Harness(HARD)
    refreshes = harness.refreshes
    harness.time.advance(0.4)
    harness.controller.tick()  # 59.6 s still shows 1:00
    assert harness.refreshes == refreshes
    harness.time.advance(0.7)
    harness.controller.tick()  # 58.9 s shows 0:59
    assert harness.timers.times() == ("0:59", "1:00")
    assert harness.refreshes == refreshes + 1


def test_running_out_of_time_loses_the_match() -> None:
    harness = Harness(HARD)
    harness.play(0)  # X, then O's time runs out
    harness.controller.select_cell(4)  # O is thinking about the center...
    harness.status.feedback = FeedbackMessage((MessagePart("Wrong answer."),))
    harness.time.advance(60)

    harness.controller.tick()

    assert harness.game.status is GameStatus.WON
    assert harness.game.winner is Mark.X
    assert harness.game.timed_out is Mark.O
    assert harness.status.status == StatusMessage("Game over: X wins!", Mark.X)
    assert harness.status.feedback == FeedbackMessage(
        (MessagePart("O", Mark.O), MessagePart(" ran out of time."))
    )
    assert not harness.prompt.is_open  # the question closes
    assert not any(cell.enabled for cell in harness.board.cells)
    assert harness.restart.label == "Play again"
    assert harness.timers.times() == ("1:00", "0:00")
    assert [timer.running for timer in harness.timers.timers] == [False, False]


def test_an_answer_after_the_time_ran_out_does_not_count() -> None:
    harness = Harness(HARD)
    harness.controller.select_cell(4)
    harness.time.advance(61)
    harness.controller.tick()
    assert harness.prompt.on_answer is not None

    harness.prompt.on_answer(1)  # tapped right as the time ran out

    assert harness.game.board[4] is None
    assert harness.game.winner is Mark.O


def test_the_clock_stops_when_the_match_ends() -> None:
    harness = Harness(HARD)
    harness.play(0, 3, 1, 4, 2)  # X wins
    clock = harness.controller.clock
    assert clock is not None
    assert clock.running is None
    harness.time.advance(1000)
    harness.controller.tick()
    assert harness.game.timed_out is None


def test_restart_gives_both_players_their_full_time_again() -> None:
    harness = Harness(HARD)
    harness.time.advance(30)
    harness.play(0)
    harness.controller.restart()
    assert harness.timers.times() == ("1:00", "1:00")
    assert harness.games_created[-1] == HARD


def test_leaving_the_game_stops_the_clock() -> None:
    harness = Harness(HARD)
    harness.controller.stop_clock()
    harness.time.advance(1000)
    harness.controller.tick()
    assert harness.game.status is GameStatus.IN_PROGRESS


def test_play_switches_between_hard_and_normal_mode() -> None:
    harness = Harness()
    harness.controller.play(settings_of([Operation.ADDITION]).with_time_limit(30))
    assert harness.timers.times() == ("0:30", "0:30")
    harness.controller.play(settings_of([Operation.ADDITION]))
    assert harness.controller.clock is None
    assert harness.timers.timers == ()
