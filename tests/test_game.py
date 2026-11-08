from calculo_da_velha.game import Game, GameStatus, Mark
from calculo_da_velha.questions import Question


def question_factory(difficulty: int) -> Question:
    return Question(f"conta {difficulty}", 1, (1, 2, 3, 4), "multiplication", difficulty)


def play(game: Game, positions: list[int]) -> None:
    for position in positions:
        game.answer(position, 1)


def test_wins_in_row() -> None:
    game = Game(question_factory)
    play(game, [0, 3, 1, 4, 2])
    assert game.status is GameStatus.WON
    assert game.winner is Mark.X


def test_wins_in_column() -> None:
    game = Game(question_factory)
    play(game, [0, 1, 3, 2, 6])
    assert game.winner is Mark.X


def test_wins_in_diagonal() -> None:
    game = Game(question_factory)
    play(game, [0, 1, 4, 2, 8])
    assert game.winner is Mark.X


def test_draw() -> None:
    game = Game(question_factory)
    for position in [0, 1, 2, 4, 3, 5, 7, 6, 8]:
        game.answer(position, 1)
    assert game.status is GameStatus.DRAW
    assert game.winner is None


def test_wrong_answer_keeps_turn_and_replaces_question() -> None:
    game = Game(question_factory)
    original = game.questions[0]
    result = game.answer(0, 999)
    assert not result.correct
    assert game.board[0] is None
    assert game.current_player is Mark.X
    assert game.questions[0] is not original


def test_correct_answer_changes_turn_and_occupies_cell() -> None:
    game = Game(question_factory)
    game.answer(0, 1)
    assert game.board[0] is Mark.X
    assert game.current_player is Mark.O
