from math_tic_tac_toe.game import Game, Mark
from math_tic_tac_toe.i18n import Language, translator_for
from math_tic_tac_toe.ui.presenter import (
    CellState,
    FeedbackMessage,
    GamePresenter,
    StatusMessage,
)
from support import english_presenter, question_factory


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


def test_feedback_tells_if_the_answer_was_right() -> None:
    presenter = english_presenter()
    game = Game(question_factory)
    assert presenter.feedback(game.answer(0, 999)) == FeedbackMessage("Wrong answer.", False)
    assert presenter.feedback(game.answer(0, 1)) == FeedbackMessage("Correct answer.", True)

    portuguese = GamePresenter(translator_for(Language.PORTUGUESE))
    assert portuguese.feedback(game.answer(1, 999)) == FeedbackMessage(
        "Resposta incorreta.", False
    )


def test_only_the_winning_line_is_highlighted() -> None:
    cells = english_presenter().cells(won_game())
    assert [position for position, cell in enumerate(cells) if cell.highlighted] == [0, 1, 2]


def test_nothing_is_highlighted_while_playing_or_on_draw() -> None:
    presenter = english_presenter()
    assert not any(cell.highlighted for cell in presenter.cells(Game(question_factory)))
    assert not any(cell.highlighted for cell in presenter.cells(drawn_game()))
