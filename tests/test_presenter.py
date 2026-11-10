import pytest

from math_tic_tac_toe.clock import ChessClock
from math_tic_tac_toe.game import Game, Mark
from math_tic_tac_toe.i18n import Language, translator_for
from math_tic_tac_toe.ui.presenter import (
    CellState,
    FeedbackMessage,
    GamePresenter,
    MessagePart,
    StatusMessage,
    TimerState,
    clock_text,
)
from tests.support import FakeTime, english_presenter, question_factory


def won_game() -> Game:
    game = Game(question_factory)
    for position in [0, 3, 1, 4, 2]:
        game.answer(position, 1)
    return game


def won_by_o_game() -> Game:
    game = Game(question_factory)
    for position in [0, 6, 1, 7, 5, 8]:
        game.answer(position, 1)
    return game


def drawn_game() -> Game:
    game = Game(question_factory)
    for position in [0, 1, 2, 4, 3, 5, 7, 6, 8]:
        game.answer(position, 1)
    return game


def test_restart_label_is_restart_during_the_match_and_play_again_after() -> None:
    presenter = english_presenter()
    assert presenter.restart_label(Game(question_factory)) == "Restart"
    assert presenter.restart_label(won_game()) == "Play again"
    assert presenter.restart_label(drawn_game()) == "Play again"

    portuguese = GamePresenter(translator_for(Language.PORTUGUESE))
    assert portuguese.restart_label(Game(question_factory)) == "Recomeçar"
    assert portuguese.restart_label(won_by_o_game()) == "Jogar novamente"
    assert portuguese.restart_label(drawn_game()) == "Jogar novamente"


def test_empty_cells_show_their_question_and_are_enabled() -> None:
    cells = english_presenter().cells(Game(question_factory))
    assert len(cells) == 9
    assert cells[4] == CellState("question 3", enabled=True, mark=None)


def test_marked_cells_show_their_mark_and_are_disabled() -> None:
    game = Game(question_factory)
    game.answer(0, 1)
    game.answer(1, 1)
    cells = english_presenter().cells(game)
    assert cells[0] == CellState("X", enabled=False, mark=Mark.X)
    assert cells[1] == CellState("O", enabled=False, mark=Mark.O)


def test_all_cells_are_disabled_after_game_ends() -> None:
    assert not any(cell.enabled for cell in english_presenter().cells(won_game()))


def test_status_tells_whose_turn_it_is() -> None:
    presenter = english_presenter()
    game = Game(question_factory)
    assert presenter.status(game) == StatusMessage("X's turn", Mark.X)
    game.answer(0, 1)
    assert presenter.status(game) == StatusMessage("O's turn", Mark.O)


def test_status_names_the_winner_or_the_draw() -> None:
    presenter = english_presenter()
    assert presenter.status(won_game()) == StatusMessage("Game over: X wins!", Mark.X)
    assert presenter.status(won_by_o_game()) == StatusMessage("Game over: O wins!", Mark.O)
    assert presenter.status(drawn_game()) == StatusMessage("Game over: it's a draw!", None)


def test_status_in_portuguese() -> None:
    presenter = GamePresenter(translator_for(Language.PORTUGUESE))
    assert presenter.status(Game(question_factory)) == StatusMessage("Vez de X", Mark.X)
    assert presenter.status(won_game()).text == "Fim de jogo: X venceu!"
    assert presenter.status(drawn_game()).text == "Fim de jogo: empate!"


def test_feedback_only_speaks_up_for_a_wrong_answer() -> None:
    presenter = english_presenter()
    game = Game(question_factory)
    assert presenter.feedback(game.answer(0, 999)) == FeedbackMessage(
        (MessagePart("Wrong answer."),)
    )
    assert presenter.feedback(game.answer(0, 1)) is None  # right: nothing to say

    portuguese = GamePresenter(translator_for(Language.PORTUGUESE))
    wrong = portuguese.feedback(game.answer(1, 999))
    assert wrong is not None
    assert wrong.text == "Resposta incorreta."


def test_only_the_winning_line_is_highlighted() -> None:
    cells = english_presenter().cells(won_game())
    assert [position for position, cell in enumerate(cells) if cell.highlighted] == [0, 1, 2]


def test_nothing_is_highlighted_while_playing_or_on_draw() -> None:
    presenter = english_presenter()
    assert not any(cell.highlighted for cell in presenter.cells(Game(question_factory)))
    assert not any(cell.highlighted for cell in presenter.cells(drawn_game()))


@pytest.mark.parametrize(
    ("seconds", "text"),
    [
        (300, "5:00"),
        (59.01, "1:00"),  # rounds up: 0:59 only once a full second is gone
        (0.1, "0:01"),
        (0, "0:00"),
    ],
)
def test_clock_text_rounds_up_like_a_chess_clock(seconds: float, text: str) -> None:
    assert clock_text(seconds) == text


def test_no_timers_outside_hard_mode() -> None:
    assert english_presenter().timers(None) == ()


def test_timers_show_both_players_x_first() -> None:
    time = FakeTime()
    clock = ChessClock(60, now=time)
    clock.start(Mark.O)
    time.advance(51)
    assert english_presenter().timers(clock) == (
        TimerState(Mark.X, "1:00", running=False, low=False),
        TimerState(Mark.O, "0:09", running=True, low=True),
    )


def test_running_out_of_time_reads_as_a_normal_win() -> None:
    game = Game(question_factory)
    game.time_out(Mark.X)
    assert english_presenter().status(game) == StatusMessage("Game over: O wins!", Mark.O)
    portuguese = GamePresenter(translator_for(Language.PORTUGUESE))
    assert portuguese.status(game).text == "Fim de jogo: O venceu!"


def test_out_of_time_message_marks_the_player_symbol() -> None:
    assert english_presenter().ran_out_of_time(Mark.X) == FeedbackMessage(
        (MessagePart("X", Mark.X), MessagePart(" ran out of time."))
    )
    portuguese = GamePresenter(translator_for(Language.PORTUGUESE))
    message = portuguese.ran_out_of_time(Mark.O)
    assert message == FeedbackMessage((MessagePart("O", Mark.O), MessagePart(" ficou sem tempo.")))
    assert message.text == "O ficou sem tempo."


def test_all_cells_of_the_winner_turn_gold_when_the_time_runs_out() -> None:
    game = Game(question_factory)
    for position in (0, 3, 1, 4):  # X: 0, 1 / O: 3, 4
        game.answer(position, 1)
    game.time_out(Mark.X)  # X ran out of time: O wins

    cells = english_presenter().cells(game)

    assert [i for i, cell in enumerate(cells) if cell.highlighted] == [3, 4]
