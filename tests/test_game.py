from itertools import count

import pytest

from math_tic_tac_toe.game import Game, GameStatus, Mark
from math_tic_tac_toe.questions import Question
from math_tic_tac_toe.settings import OPERATIONS, TABLES, GameSettings, Operation
from support import question_factory


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
    play(game, [0, 1, 2, 4, 3, 5, 7, 6, 8])
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
    result = game.answer(0, 1)
    assert result.correct
    assert game.board[0] is Mark.X
    assert game.current_player is Mark.O


def test_winning_move_reports_status_and_winner() -> None:
    game = Game(question_factory)
    play(game, [0, 3, 1, 4])
    result = game.answer(2, 1)
    assert result.status is GameStatus.WON
    assert result.winner is Mark.X


def test_is_available_until_cell_is_taken_or_game_ends() -> None:
    game = Game(question_factory)
    assert game.is_available(0)
    game.answer(0, 1)
    assert not game.is_available(0)
    play(game, [3, 1, 4, 2])
    assert game.status is GameStatus.WON
    assert not game.is_available(8)


def test_is_available_rejects_invalid_position() -> None:
    with pytest.raises(ValueError):
        Game(question_factory).is_available(9)


@pytest.mark.parametrize(
    ("positions", "line"),
    [
        ([0, 3, 1, 4, 2], (0, 1, 2)),  # row
        ([0, 1, 3, 2, 6], (0, 3, 6)),  # column
        ([0, 1, 4, 2, 8], (0, 4, 8)),  # diagonal
        ([2, 0, 4, 1, 6], (2, 4, 6)),  # anti-diagonal
        ([0, 6, 1, 7, 5, 8], (6, 7, 8)),  # won by O
    ],
)
def test_winning_line_is_recorded(positions: list[int], line: tuple[int, int, int]) -> None:
    game = Game(question_factory)
    play(game, positions)
    assert game.status is GameStatus.WON
    assert game.winning_line == line


def test_no_winning_line_while_playing_or_on_draw() -> None:
    game = Game(question_factory)
    play(game, [0, 1])
    assert game.winning_line is None
    play(game, [2, 4, 3, 5, 7, 6, 8])
    assert game.status is GameStatus.DRAW
    assert game.winning_line is None


def test_is_over_only_after_a_win_or_draw() -> None:
    game = Game(question_factory)
    assert not game.is_over
    play(game, [0, 3, 1, 4, 2])
    assert game.is_over


def test_cannot_answer_after_the_game_is_over() -> None:
    game = Game(question_factory)
    play(game, [0, 3, 1, 4, 2])
    with pytest.raises(ValueError, match="over"):
        game.answer(8, 1)


def test_cannot_answer_a_taken_cell() -> None:
    game = Game(question_factory)
    game.answer(0, 1)
    with pytest.raises(ValueError, match="taken"):
        game.answer(0, 1)


@pytest.mark.parametrize("position", [-1, 9])
def test_difficulty_rejects_invalid_position(position: int) -> None:
    with pytest.raises(ValueError):
        Game.difficulty_for(position)


def test_default_game_uses_the_real_question_generator() -> None:
    game = Game()
    assert len(game.questions) == 9
    for question in game.questions:
        assert question.answer in question.choices


def test_with_settings_asks_questions_of_the_chosen_table() -> None:
    game = Game.with_settings(GameSettings.of([Operation.DIVISION], [7]))
    for question in game.questions:
        assert question.operation is Operation.DIVISION
        assert question.prompt.endswith("÷ 7")


OPERATION_CHOICES = [[operation] for operation in OPERATIONS] + [
    list(OPERATIONS),
    [Operation.ADDITION, Operation.DIVISION],
]


@pytest.mark.parametrize("operations", OPERATION_CHOICES)
@pytest.mark.parametrize("tables", [[table] for table in TABLES] + [list(TABLES), [6, 7, 8]])
def test_board_questions_are_all_different(operations, tables) -> None:
    for _ in range(10):
        game = Game.with_settings(GameSettings.of(operations, tables))
        prompts = [question.prompt for question in game.questions]
        assert len(set(prompts)) == Game.BOARD_SIZE


def test_a_wrong_answer_brings_a_question_not_on_the_board() -> None:
    game = Game.with_settings(GameSettings.of([Operation.MULTIPLICATION], [7]))
    for _ in range(30):
        before = game.questions[4].prompt
        game.answer(4, -1)  # always wrong
        prompts = [question.prompt for question in game.questions]
        assert game.questions[4].prompt != before
        assert len(set(prompts)) == Game.BOARD_SIZE


def test_the_game_asks_to_avoid_the_questions_on_open_cells() -> None:
    asked: list[set[str]] = []
    numbers = count()

    def factory(difficulty: int, avoid) -> Question:
        asked.append(set(avoid))
        return Question(f"q{next(numbers)}", 1, (1, 2, 3), Operation.ADDITION, difficulty)

    game = Game(factory)
    assert asked[0] == set()
    assert asked[-1] == {f"q{i}" for i in range(8)}  # the 8 cells already filled

    game.answer(0, 1)  # cell 0 is taken: its question is no longer on the board
    game.answer(4, 2)  # wrong: cell 4 gets a new question
    assert asked[-1] == {f"q{i}" for i in range(1, 9)}


def test_with_several_tables_every_question_uses_one_of_them() -> None:
    game = Game.with_settings(GameSettings.of([Operation.MULTIPLICATION], [5, 7]))
    assert {question.prompt.split(" × ")[0] for question in game.questions} <= {"5", "7"}
