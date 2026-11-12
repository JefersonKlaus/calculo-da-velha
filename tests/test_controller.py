from collections.abc import Callable, Sequence
from functools import partial

from math_tic_tac_toe.cell_timers import CellTimers
from math_tic_tac_toe.clock import ChessClock, Countdown
from math_tic_tac_toe.game import TURN_SECONDS, Game, GameStatus, Mark
from math_tic_tac_toe.questions import Question
from math_tic_tac_toe.settings import (
    DEFAULT_SETTINGS,
    OPERATIONS,
    TABLES,
    GameSettings,
    Operation,
)
from math_tic_tac_toe.ui.controller import POINT_SECONDS, GameController
from math_tic_tac_toe.ui.ports import AnswerHandler, ConfirmHandler, Screen
from math_tic_tac_toe.ui.presenter import (
    CellState,
    FeedbackMessage,
    MessagePart,
    ScoreBoard,
    StatusMessage,
    TimerState,
    TurnTime,
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
        self.turn_time: TurnTime | None = None

    def show_status(self, message: StatusMessage) -> None:
        self.status = message

    def show_turn_time(self, time: TurnTime | None) -> None:
        self.turn_time = time

    def show_feedback(self, message: FeedbackMessage | None) -> None:
        self.feedback = message

    @property
    def feedback_text(self) -> str | None:
        return self.feedback.text if self.feedback else None


class FakePrompt:
    def __init__(self) -> None:
        self.question: Question | None = None
        self.on_answer: AnswerHandler | None = None
        self.on_cancel: Callable[[], None] | None = None
        self.time: TurnTime | None = None
        self.is_open = False

    def ask(
        self, question: Question, on_answer: AnswerHandler, on_cancel: Callable[[], None]
    ) -> None:
        self.question = question
        self.on_answer = on_answer
        self.on_cancel = on_cancel
        self.is_open = True

    def show_time(self, time: TurnTime) -> None:
        self.time = time

    def cancel(self) -> None:
        assert self.on_cancel is not None
        self.is_open = False
        self.on_cancel()

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


class FakeScore:
    def __init__(self) -> None:
        self.board: ScoreBoard | None = None

    def show_score(self, board: ScoreBoard | None) -> None:
        self.board = board

    def points(self) -> tuple[int, ...]:
        assert self.board is not None
        return tuple(score.points for score in self.board.scores)


class Harness:
    """A controller wired to fake screen parts, with a hand-driven clock."""

    def __init__(self, settings: GameSettings = DEFAULT_SETTINGS) -> None:
        self.board = FakeBoard()
        self.status = FakeStatus()
        self.prompt = FakePrompt()
        self.restart = FakeRestart()
        self.confirmation = FakeConfirmation()
        self.leave_confirmation = FakeConfirmation()
        self.timers = FakeTimers()
        self.score = FakeScore()
        self.time = FakeTime()
        self.refreshes = 0
        self.games_created: list[GameSettings] = []
        self.controller = GameController(
            new_game=self._new_game,
            settings=settings,
            presenter=english_presenter(),
            screen=Screen(
                board=self.board,
                status=self.status,
                prompt=self.prompt,
                restart=self.restart,
                confirm_restart=self.confirmation,
                confirm_leave=self.leave_confirmation,
                timers=self.timers,
                score=self.score,
            ),
            refresh=self._refresh,
            new_clock=partial(ChessClock, now=self.time),
            new_cell_timers=partial(CellTimers, now=self.time),
            new_countdown=partial(Countdown, now=self.time),
        )
        self.controller.start()

    def _new_game(self, settings: GameSettings) -> Game:
        self.games_created.append(settings)
        return Game(question_factory, best_of=settings.best_of)

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
    harness.play(1)  # O is right
    assert harness.status.feedback is None


def test_wrong_choice_gives_the_cell_to_the_other_player_and_passes_turn() -> None:
    harness = Harness()
    harness.play(0, response=2)
    assert harness.game.board[0] is Mark.O
    assert harness.board.cells[0].mark is Mark.O
    assert not harness.board.cells[0].enabled
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


class Exit:
    """Records when the controller lets the player leave the game screen."""

    def __init__(self) -> None:
        self.left = 0

    def __call__(self) -> None:
        self.left += 1


def test_leaving_a_match_in_progress_asks_first() -> None:
    harness = Harness()
    harness.play(0, 3)
    in_progress = harness.game
    leave = Exit()

    harness.controller.request_leave(leave)

    assert harness.leave_confirmation.asked == 1
    assert harness.confirmation.asked == 0  # its own question, not the restart one
    assert leave.left == 0  # nothing happens until the player agrees
    assert harness.game is in_progress

    harness.leave_confirmation.accept()
    assert leave.left == 1


def test_leaving_does_not_ask_before_the_first_answer() -> None:
    harness = Harness()
    leave = Exit()
    harness.controller.request_leave(leave)
    assert harness.leave_confirmation.asked == 0
    assert leave.left == 1


def test_leaving_does_not_ask_once_the_match_is_over() -> None:
    harness = Harness()
    harness.play(0, 3, 1, 4, 2)
    leave = Exit()
    harness.controller.request_leave(leave)
    assert harness.leave_confirmation.asked == 0
    assert leave.left == 1


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
    harness.time.advance(8)
    harness.play(0)  # X answers right: now O's time runs
    harness.time.advance(9)
    harness.controller.tick()
    assert harness.timers.times() == ("0:52", "0:51")
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
    assert harness.status.status == StatusMessage("Game over: X wins!", Mark.X, won=True)
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


# ---- best of 5 -------------------------------------------------------------------
# The test questions ("question 1", "question 2", "question 3") make corners
# last 1 second, edges 2 and the center 3.

BEST_OF_FIVE = settings_of(OPERATIONS, TABLES).with_best_of(5)


def best_of_five() -> Harness:
    harness = Harness()
    harness.controller.play(BEST_OF_FIVE)
    return harness


def test_a_single_game_shows_no_score_and_no_countdowns() -> None:
    harness = Harness()
    assert harness.score.board is None
    assert harness.controller.cell_timers is None
    harness.play(0)
    assert harness.board.cells[0].seconds is None


def test_best_of_five_shows_the_score_and_what_wins() -> None:
    harness = best_of_five()
    assert harness.score.points() == (0, 0)
    assert harness.score.board is not None
    assert harness.score.board.goal == "First to 3 wins"


def test_a_played_cell_shows_its_countdown_and_redraws_each_second() -> None:
    harness = best_of_five()
    harness.play(4)  # the center: 3 seconds
    assert harness.board.cells[4].seconds == 3
    refreshes = harness.refreshes

    harness.time.advance(0.5)
    harness.controller.tick()
    assert harness.refreshes == refreshes  # still "3": nothing to redraw

    harness.time.advance(0.6)
    harness.controller.tick()
    assert harness.board.cells[4].seconds == 2
    assert harness.refreshes == refreshes + 1


def test_a_cell_is_open_again_when_its_countdown_ends() -> None:
    harness = best_of_five()
    harness.play(4, 0)  # X in the center (3 s), O in a corner (1 s)
    harness.time.advance(1)
    harness.controller.tick()

    assert harness.game.board[0] is None  # O's corner is open again
    assert harness.board.cells[0].mark is None
    assert harness.board.cells[0].enabled
    assert harness.game.board[4] is Mark.X
    assert harness.board.cells[4].seconds == 2
    assert harness.status.status == StatusMessage("X's turn", Mark.X)  # turn unchanged

    harness.time.advance(2)
    harness.controller.tick()
    assert harness.game.board[4] is None


def test_a_line_scores_a_point_with_a_message() -> None:
    harness = best_of_five()
    harness.play(0, 3, 1, 4, 2)  # X completes the top row

    assert harness.score.points() == (1, 0)
    assert harness.game.board[:3] == [None, None, None]
    assert harness.status.feedback == FeedbackMessage(
        (MessagePart("Point for "), MessagePart("X", Mark.X), MessagePart("!")), alert=False
    )
    assert harness.status.status == StatusMessage("O's turn", Mark.O)
    assert harness.restart.label == "Restart"  # the match goes on

    harness.play(8)  # a right answer without a line clears the message
    assert harness.status.feedback is None


def test_the_third_point_ends_the_match_and_stops_the_countdowns() -> None:
    harness = best_of_five()
    # X answers right; O answers wrong, which puts X's symbol on the board.
    harness.play(0)
    harness.play(1, response=999)
    harness.play(2)  # top row: X 1
    harness.time.advance(2)  # the line shows in gold, then disappears
    harness.controller.tick()
    harness.play(3, response=999)
    harness.play(4)
    harness.play(5, response=999)  # O's wrong answer completes X's middle row
    assert harness.status.feedback_text == "Wrong answer. Point for X!"
    harness.time.advance(2)
    harness.controller.tick()
    harness.play(6)
    harness.play(7, response=999)
    harness.play(8)  # bottom row: the third point

    assert harness.score.points() == (3, 0)
    assert harness.status.status == StatusMessage("Game over: X wins!", Mark.X, won=True)
    assert harness.restart.label == "Play again"
    assert [p for p, cell in enumerate(harness.board.cells) if cell.highlighted] == [6, 7, 8]
    assert all(cell.seconds is None for cell in harness.board.cells)
    harness.time.advance(100)
    harness.controller.tick()
    assert harness.game.board[6:9] == [Mark.X, Mark.X, Mark.X]  # nothing resets anymore


def test_restarting_a_best_of_keeps_the_mode_with_a_fresh_score() -> None:
    harness = best_of_five()
    harness.play(0, 3, 1, 4, 2)
    harness.controller.restart()
    assert harness.games_created[-1] == BEST_OF_FIVE
    assert harness.score.points() == (0, 0)


def test_leaving_stops_the_countdowns() -> None:
    harness = best_of_five()
    harness.play(0)
    harness.controller.stop_clock()
    harness.time.advance(100)
    harness.controller.tick()
    assert harness.game.board[0] is Mark.X


def test_play_after_a_best_of_is_a_single_game_again() -> None:
    harness = best_of_five()
    harness.controller.play(DEFAULT_SETTINGS)
    assert harness.score.board is None
    assert harness.controller.cell_timers is None


# ---- 10 seconds per turn, to choose a cell and answer --------------------------------


def test_each_turn_shows_10_seconds_next_to_whose_turn_it_is() -> None:
    harness = Harness()
    assert TURN_SECONDS == 10
    assert harness.status.turn_time == TurnTime(10, low=False)
    refreshes = harness.refreshes

    harness.time.advance(0.5)
    harness.controller.tick()
    assert harness.status.turn_time == TurnTime(10, low=False)  # still 10: no redraw
    assert harness.refreshes == refreshes

    harness.time.advance(0.5)
    harness.controller.tick()
    assert harness.status.turn_time == TurnTime(9, low=False)
    assert harness.refreshes == refreshes + 1

    harness.time.advance(6)
    harness.controller.tick()
    assert harness.status.turn_time == TurnTime(3, low=True)  # the last seconds: red


def test_the_time_to_choose_a_cell_counts_too() -> None:
    harness = Harness()
    harness.time.advance(6)  # X takes 6 seconds to choose
    refreshes = harness.refreshes
    harness.controller.select_cell(4)
    assert harness.prompt.time == TurnTime(4, low=False)  # 4 left to answer
    assert harness.refreshes == refreshes + 1  # drawn with the question
    harness.time.advance(1)
    harness.controller.tick()
    assert harness.prompt.time == TurnTime(3, low=True)
    assert harness.status.turn_time == TurnTime(3, low=True)


def test_when_the_time_runs_out_the_cell_goes_to_the_other_player() -> None:
    harness = Harness()
    harness.controller.select_cell(4)  # X opens the center... and thinks too long
    harness.time.advance(10)
    harness.controller.tick()

    assert not harness.prompt.is_open  # the question closed
    assert harness.game.board[4] is Mark.O  # like a wrong answer
    assert harness.status.feedback_text == "Time's up!"
    assert harness.status.feedback is not None
    assert harness.status.feedback.alert
    assert harness.status.status == StatusMessage("O's turn", Mark.O)
    assert harness.status.turn_time == TurnTime(10, low=False)  # O's turn, 10 new seconds


def test_when_the_time_runs_out_before_choosing_the_turn_passes() -> None:
    harness = Harness()
    harness.time.advance(10)
    harness.controller.tick()

    assert harness.game.board == [None] * 9  # nothing to give away
    assert harness.status.status == StatusMessage("O's turn", Mark.O)
    assert harness.status.feedback_text == "Time's up!"
    assert harness.status.turn_time == TurnTime(10, low=False)
    assert not harness.game.is_in_progress  # nobody answered yet: nothing to lose


def test_each_turn_gets_10_new_seconds() -> None:
    harness = Harness()
    harness.time.advance(7)
    harness.play(0)  # X answers with 3 seconds left
    assert harness.status.turn_time == TurnTime(10, low=False)  # O's turn
    harness.time.advance(9)
    harness.controller.tick()
    assert harness.status.status == StatusMessage("O's turn", Mark.O)


def test_canceling_does_not_stop_the_time() -> None:
    harness = Harness()
    harness.controller.select_cell(0)
    harness.time.advance(4)
    harness.prompt.cancel()  # X changes their mind...
    harness.controller.select_cell(1)
    assert harness.prompt.time == TurnTime(6, low=False)  # ...with the time left
    harness.prompt.cancel()
    harness.time.advance(6)
    harness.controller.tick()
    assert harness.game.board == [None] * 9  # no question open: the turn passes
    assert harness.status.status == StatusMessage("O's turn", Mark.O)


def test_no_turn_time_once_the_match_is_over() -> None:
    harness = Harness()
    harness.play(0, 3, 1, 4, 2)
    assert harness.status.turn_time is None
    harness.time.advance(100)
    harness.controller.tick()
    assert harness.status.status == StatusMessage("Game over: X wins!", Mark.X, won=True)


def test_time_up_that_completes_the_other_players_line_ends_the_match() -> None:
    harness = Harness()
    harness.play(3, 0, 4, 1)  # O holds 0 and 1
    harness.controller.select_cell(2)  # X runs out of time on the last cell of O's row
    harness.time.advance(10)
    harness.controller.tick()
    assert harness.status.status == StatusMessage("Game over: O wins!", Mark.O, won=True)
    assert harness.status.feedback_text == "Time's up!"


def test_hard_mode_time_running_out_first_ends_the_match_and_the_question() -> None:
    harness = Harness()
    harness.controller.play(DEFAULT_SETTINGS.with_time_limit(5))
    harness.controller.select_cell(0)
    harness.time.advance(5)  # X's 5 seconds of hard mode end before the 10
    harness.controller.tick()
    assert not harness.prompt.is_open
    assert harness.game.timed_out is Mark.X

    harness.time.advance(10)
    harness.controller.tick()  # the question's time no longer counts
    assert harness.game.board == [None] * 9


def test_leaving_stops_the_turn_time() -> None:
    harness = Harness()
    harness.controller.select_cell(0)
    harness.controller.stop_clock()
    harness.time.advance(100)
    harness.controller.tick()
    assert harness.game.board == [None] * 9
    assert harness.status.status == StatusMessage("X's turn", Mark.X)


def test_the_next_turn_starts_after_a_point_is_shown() -> None:
    harness = best_of_five()
    harness.play(0, 3, 1, 4, 2)  # X scores: the line shows in gold
    assert harness.status.turn_time is None  # the board waits: no time runs
    harness.time.advance(2)
    harness.controller.tick()
    assert harness.status.turn_time == TurnTime(10, low=False)  # O's turn starts now


# ---- a point shows in gold before it disappears -------------------------------------


def test_a_point_shows_its_line_in_gold_for_1_second() -> None:
    harness = best_of_five()
    harness.play(0, 3, 1, 4, 2)  # X completes the top row
    assert POINT_SECONDS == 1
    gold = [p for p, cell in enumerate(harness.board.cells) if cell.highlighted]
    assert gold == [0, 1, 2]
    assert [harness.board.cells[p].mark for p in gold] == [Mark.X] * 3
    assert not any(cell.enabled for cell in harness.board.cells)  # the board waits
    assert harness.game.board[:3] == [None, None, None]  # the rule already cleared them

    harness.prompt.question = None
    harness.controller.select_cell(5)  # taps are ignored meanwhile
    assert harness.prompt.question is None

    harness.time.advance(0.9)
    harness.controller.tick()
    assert harness.board.cells[0].highlighted  # still gold
    refreshes = harness.refreshes
    harness.controller.tick()
    assert harness.refreshes == refreshes  # nothing changed: no redraw

    harness.time.advance(0.1)
    harness.controller.tick()
    assert not any(cell.highlighted for cell in harness.board.cells)
    assert harness.board.cells[0].label == "question 1"
    assert harness.board.cells[0].enabled
    harness.controller.select_cell(5)
    assert harness.prompt.question is not None  # playable again


def test_the_winning_point_stays_gold() -> None:
    harness = best_of_five()
    harness.play(0, 1, 3, 4)
    harness.game.scores[Mark.X] = 2  # one point away from winning
    harness.play(6)  # X completes the left column: the match is won
    harness.time.advance(100)
    harness.controller.tick()
    gold = [p for p, cell in enumerate(harness.board.cells) if cell.highlighted]
    assert gold == [0, 3, 6]
    assert harness.status.status == StatusMessage("Game over: X wins!", Mark.X, won=True)


def test_restarting_or_leaving_forgets_the_point_being_shown() -> None:
    harness = best_of_five()
    harness.play(0, 3, 1, 4, 2)
    harness.controller.restart()
    assert not any(cell.highlighted for cell in harness.board.cells)
    assert all(cell.enabled for cell in harness.board.cells)

    harness.play(0, 3, 1, 4, 2)
    harness.controller.stop_clock()  # left for the settings
    harness.controller.select_cell(5)
    assert harness.prompt.question is not None


def test_two_lines_at_once_show_both_in_gold_and_score_two() -> None:
    harness = best_of_five()
    harness.play(1, 4, 2, 5, 3, 7, 6, 8, 0)  # X: top row and left column at once
    assert harness.score.points() == (2, 0)
    assert harness.status.feedback_text == "2 points for X!"
    gold = [p for p, cell in enumerate(harness.board.cells) if cell.highlighted]
    assert gold == [0, 1, 2, 3, 6]
    harness.time.advance(1)
    harness.controller.tick()
    assert not any(cell.highlighted for cell in harness.board.cells)
