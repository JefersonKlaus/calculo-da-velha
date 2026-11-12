import pytest

from math_tic_tac_toe.cell_timers import CellTimers
from math_tic_tac_toe.clock import ChessClock, Countdown
from math_tic_tac_toe.game import Game, Mark, MoveResult
from math_tic_tac_toe.i18n import Language, translator_for
from math_tic_tac_toe.ui.presenter import (
    CellState,
    FeedbackMessage,
    GamePresenter,
    MessagePart,
    ScoreBoard,
    ScoredLine,
    ScoreState,
    StatusMessage,
    TimerState,
    TurnTime,
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


def test_only_a_win_is_celebrated() -> None:
    presenter = english_presenter()
    assert presenter.status(won_game()).won
    assert not presenter.status(drawn_game()).won
    assert not presenter.status(Game(question_factory)).won


def test_status_names_the_winner_or_the_draw() -> None:
    presenter = english_presenter()
    assert presenter.status(won_game()) == StatusMessage("Game over: X wins!", Mark.X, won=True)
    assert presenter.status(won_by_o_game()) == StatusMessage(
        "Game over: O wins!", Mark.O, won=True
    )
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
    assert presenter.feedback(game.answer(1, 1)) is None  # right: nothing to say

    portuguese = GamePresenter(translator_for(Language.PORTUGUESE))
    wrong = portuguese.feedback(game.answer(2, 999))
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
    assert english_presenter().status(game) == StatusMessage("Game over: O wins!", Mark.O, won=True)
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


# ---- best of 5 -------------------------------------------------------------------


def test_a_single_game_has_no_score_board() -> None:
    assert english_presenter().score_board(Game(question_factory)) is None


def test_score_board_of_a_best_of_five() -> None:
    game = Game(question_factory, best_of=5)
    for position in [0, 3, 1, 4, 2]:  # X completes a line
        game.answer(position, 1)
    assert english_presenter().score_board(game) == ScoreBoard(
        (ScoreState(Mark.X, 1), ScoreState(Mark.O, 0)), "First to 3 wins"
    )
    portuguese = GamePresenter(translator_for(Language.PORTUGUESE)).score_board(game)
    assert portuguese is not None
    assert portuguese.goal == "Vence quem fizer 3"


def test_played_cells_show_whole_seconds_rounded_up() -> None:
    time = FakeTime()
    game = Game(question_factory, best_of=5)
    timers = CellTimers(now=time)
    game.answer(4, 1)  # the center: "question 3" lasts 3 seconds
    timers.follow(game)
    presenter = english_presenter()

    assert presenter.cells(game, timers)[4].seconds == 3
    time.advance(0.2)
    assert presenter.cells(game, timers)[4].seconds == 3  # 2.8 shows 3
    time.advance(1)
    assert presenter.cells(game, timers)[4].seconds == 2
    assert presenter.cells(game)[4].seconds is None  # no countdowns at all


def test_open_cells_of_a_best_of_show_no_seconds() -> None:
    time = FakeTime()
    game = Game(question_factory, best_of=5)
    timers = CellTimers(now=time)
    game.answer(4, 1)
    timers.follow(game)
    cells = english_presenter().cells(game, timers)
    assert [cell.seconds for cell in cells] == [None] * 4 + [3] + [None] * 4


def test_no_seconds_in_a_single_game_or_once_a_best_of_is_over() -> None:
    assert all(cell.seconds is None for cell in english_presenter().cells(won_game()))
    assert all(cell.seconds is None for cell in english_presenter().cells(Game(question_factory)))
    game = Game(question_factory, best_of=1)  # the first line wins
    for position in [0, 3, 1, 4, 2]:
        game.answer(position, 1)
    assert game.is_over
    assert all(cell.seconds is None for cell in english_presenter().cells(game))


def test_time_up_without_a_cell() -> None:
    assert english_presenter().time_up() == FeedbackMessage((MessagePart("Time's up!"),))


@pytest.mark.parametrize(
    ("language", "text"),
    [(Language.ENGLISH, "Point for O!"), (Language.PORTUGUESE, "Ponto para O!")],
)
def test_a_point_is_good_news_with_the_player_in_color(language: Language, text: str) -> None:
    message = GamePresenter(translator_for(language)).feedback(
        MoveResult(correct=True, point_for=Mark.O, points=1)
    )
    assert message is not None
    assert message.text == text
    assert not message.alert  # not red
    assert [part.player for part in message.parts if part.player] == [Mark.O]


# ---- 10 seconds to answer --------------------------------------------------------


@pytest.mark.parametrize(
    ("language", "text"),
    [(Language.ENGLISH, "Time's up!"), (Language.PORTUGUESE, "Tempo esgotado!")],
)
def test_not_answering_in_time_says_time_is_up_in_red(language: Language, text: str) -> None:
    message = GamePresenter(translator_for(language)).feedback(
        MoveResult(correct=False), missed=True
    )
    assert message == FeedbackMessage((MessagePart(text),))
    assert message.alert


def test_a_wrong_answer_that_scores_for_the_other_player_says_both_in_red() -> None:
    presenter = english_presenter()
    message = presenter.feedback(MoveResult(correct=False, point_for=Mark.O, points=1))
    assert message == FeedbackMessage(
        (
            MessagePart("Wrong answer."),
            MessagePart(" "),
            MessagePart("Point for "),
            MessagePart("O", Mark.O),
            MessagePart("!"),
        )
    )
    assert message.alert  # bad news for the player who answered
    missed = presenter.feedback(MoveResult(correct=False, point_for=Mark.O, points=1), missed=True)
    assert missed is not None
    assert missed.text == "Time's up! Point for O!"


def test_answer_time_is_whole_seconds_rounded_up_and_low_at_the_end() -> None:
    time = FakeTime()
    countdown = Countdown(10, now=time)
    presenter = english_presenter()
    assert presenter.turn_time(countdown) == TurnTime(10, low=False)
    time.advance(0.1)
    assert presenter.turn_time(countdown) == TurnTime(10, low=False)
    time.advance(6.9)
    assert presenter.turn_time(countdown) == TurnTime(3, low=True)
    time.advance(2.5)
    assert presenter.turn_time(countdown) == TurnTime(1, low=True)


def test_a_line_that_scored_shows_in_gold_while_the_board_waits() -> None:
    game = Game(question_factory, best_of=5)
    for position in [0, 3, 1, 4, 2]:  # X's top row scores and is cleared
        game.answer(position, 1)
    cells = english_presenter().cells(game, scored=ScoredLine((0, 1, 2), Mark.X))

    for position in (0, 1, 2):
        assert cells[position] == CellState("X", False, Mark.X, highlighted=True)
    assert cells[3] == CellState("O", False, Mark.O)
    assert cells[5].label == "question 2"
    assert not any(cell.enabled for cell in cells)  # nothing can be played yet

    after = english_presenter().cells(game)  # once it disappears
    assert [cell.label for cell in after[:3]] == ["question 1", "question 2", "question 1"]
    assert after[0].enabled


@pytest.mark.parametrize(
    ("language", "text"),
    [(Language.ENGLISH, "2 points for X!"), (Language.PORTUGUESE, "2 pontos para X!")],
)
def test_two_lines_at_once_say_two_points(language: Language, text: str) -> None:
    message = GamePresenter(translator_for(language)).feedback(
        MoveResult(correct=True, point_for=Mark.X, points=2)
    )
    assert message is not None
    assert message.text == text
    assert [part.player for part in message.parts if part.player] == [Mark.X]


def test_every_line_of_a_winning_move_is_highlighted() -> None:
    game = Game(question_factory)
    for position in [1, 4, 2, 5, 3, 7, 6, 8, 0]:  # X's last move completes two lines
        game.answer(position, 1)
    cells = english_presenter().cells(game)
    assert [p for p, cell in enumerate(cells) if cell.highlighted] == [0, 1, 2, 3, 6]
