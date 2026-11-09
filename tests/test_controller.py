from collections.abc import Sequence

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
from math_tic_tac_toe.ui.ports import AnswerHandler, Screen
from math_tic_tac_toe.ui.presenter import CellState, FeedbackMessage, StatusMessage
from support import english_presenter, question_factory


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


class FakePrompt:
    def __init__(self) -> None:
        self.question: Question | None = None
        self.on_answer: AnswerHandler | None = None

    def ask(self, question: Question, on_answer: AnswerHandler) -> None:
        self.question = question
        self.on_answer = on_answer

    def choose(self, response: int) -> None:
        assert self.on_answer is not None
        self.on_answer(response)


class FakeRestart:
    def __init__(self) -> None:
        self.visible: bool | None = None

    def set_visible(self, visible: bool) -> None:
        self.visible = visible


class Harness:
    """A controller wired to fake screen parts."""

    def __init__(self) -> None:
        self.board = FakeBoard()
        self.status = FakeStatus()
        self.prompt = FakePrompt()
        self.restart = FakeRestart()
        self.refreshes = 0
        self.games_created: list[GameSettings] = []
        self.controller = GameController(
            new_game=self._new_game,
            settings=DEFAULT_SETTINGS,
            presenter=english_presenter(),
            screen=Screen(self.board, self.status, self.prompt, self.restart),
            refresh=self._refresh,
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


def test_start_renders_board_status_and_hides_restart() -> None:
    harness = Harness()
    assert len(harness.board.cells) == 9
    assert harness.status.status == StatusMessage("X's turn", Mark.X)
    assert harness.status.feedback is None
    assert harness.restart.visible is False
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
    assert harness.status.feedback == FeedbackMessage("Correct answer.", correct=True)


def test_wrong_choice_keeps_turn_and_shows_feedback() -> None:
    harness = Harness()
    harness.play(0, response=2)
    assert harness.game.board[0] is None
    assert harness.board.cells[0].enabled
    assert harness.status.status == StatusMessage("X's turn", Mark.X)
    assert harness.status.feedback == FeedbackMessage("Wrong answer.", correct=False)


def test_unavailable_cell_does_not_open_the_prompt() -> None:
    harness = Harness()
    harness.play(0)
    harness.prompt.question = None
    harness.controller.select_cell(0)
    assert harness.prompt.question is None


def test_restart_is_offered_only_when_the_game_ends() -> None:
    harness = Harness()
    harness.play(0, 3, 1, 4)
    assert harness.restart.visible is False
    harness.play(2)
    assert harness.game.status is GameStatus.WON
    assert harness.restart.visible is True


def test_restart_is_offered_after_a_draw() -> None:
    harness = Harness()
    harness.play(0, 1, 2, 4, 3, 5, 7, 6, 8)
    assert harness.game.status is GameStatus.DRAW
    assert harness.restart.visible is True


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
    assert harness.restart.visible is False


def test_play_starts_a_new_match_with_the_new_settings() -> None:
    harness = Harness()
    harness.play(0, 3)
    division_of_7 = GameSettings.of([Operation.DIVISION], [7])

    harness.controller.play(division_of_7)

    assert harness.controller.settings == division_of_7
    assert harness.games_created[-1] == division_of_7
    assert harness.game.board == [None] * 9
    assert harness.status.status == StatusMessage("X's turn", Mark.X)
    assert harness.restart.visible is False


def test_restart_keeps_the_current_settings() -> None:
    harness = Harness()
    everything = GameSettings.of(OPERATIONS, TABLES)
    harness.controller.play(everything)
    harness.controller.restart()
    assert harness.games_created[-1] == everything
