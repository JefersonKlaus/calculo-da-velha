from collections.abc import Collection
from itertools import count

import pytest

from math_tic_tac_toe.game import Game, GameStatus, Mark
from math_tic_tac_toe.questions import Question
from math_tic_tac_toe.settings import OPERATIONS, TABLES, Operation
from tests.support import question_factory, settings_of


def play(game: Game, positions: list[int]) -> None:
    for position in positions:
        game.answer(position, 1)


def test_draw() -> None:
    game = Game(question_factory)
    play(game, [0, 1, 2, 4, 3, 5, 7, 6, 8])
    assert game.status is GameStatus.DRAW
    assert game.winner is None
    assert game.winning_line is None


def test_wrong_answer_passes_turn_and_replaces_question() -> None:
    game = Game(question_factory)
    original = game.questions[0]
    result = game.answer(0, 999)
    assert not result.correct
    assert game.status is GameStatus.IN_PROGRESS
    assert game.board[0] is None  # the cell stays open...
    assert game.questions[0] is not original  # ...with a new question
    assert game.current_player is Mark.O  # and the other player plays now


def test_the_other_player_can_take_the_cell_after_a_wrong_answer() -> None:
    game = Game(question_factory)
    game.answer(4, 999)  # X is wrong
    game.answer(4, 1)  # O takes the center
    assert game.board[4] is Mark.O
    assert game.current_player is Mark.X


def test_a_new_match_is_not_in_progress_until_someone_answers() -> None:
    game = Game(question_factory)
    assert not game.is_in_progress
    assert not game.is_over
    game.answer(0, 999)  # even a wrong answer starts the match
    assert game.is_in_progress
    game.answer(0, 1)
    assert game.is_in_progress


def test_a_finished_match_is_no_longer_in_progress() -> None:
    won, drawn = Game(question_factory), Game(question_factory)
    play(won, [0, 3, 1, 4, 2])
    play(drawn, [0, 1, 2, 4, 3, 5, 7, 6, 8])
    assert won.is_over
    assert drawn.is_over
    assert not won.is_in_progress
    assert not drawn.is_in_progress


def test_correct_answer_changes_turn_and_occupies_cell() -> None:
    game = Game(question_factory)
    result = game.answer(0, 1)
    assert result.correct
    assert game.board[0] is Mark.X
    assert game.current_player is Mark.O


def test_is_available_until_cell_is_taken_or_game_ends() -> None:
    game = Game(question_factory)
    assert game.is_available(0)
    game.answer(0, 1)
    assert not game.is_available(0)
    play(game, [3, 1, 4, 2])
    assert game.status is GameStatus.WON
    assert not game.is_available(8)


@pytest.mark.parametrize("position", [-1, 9])
def test_rejects_positions_off_the_board(position: int) -> None:
    with pytest.raises(ValueError, match="Position must be between 0 and 8"):
        Game(question_factory).is_available(position)
    with pytest.raises(ValueError, match="Position must be between 0 and 8"):
        Game.difficulty_for(position)


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
    assert game.winner is (Mark.X if len(positions) % 2 else Mark.O)
    assert game.winning_line == line


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


def test_default_game_uses_the_real_question_generator() -> None:
    game = Game()
    assert len(game.questions) == 9
    for question in game.questions:
        assert question.answer in question.choices


def test_with_settings_asks_questions_of_the_chosen_table() -> None:
    game = Game.with_settings(settings_of([Operation.DIVISION], [7]))
    for question in game.questions:
        assert question.operation is Operation.DIVISION
        assert question.prompt.endswith("÷ 7")


@pytest.mark.parametrize(
    ("operations", "tables"),
    [
        # One times table has only 10 facts for the 9 cells: the tightest case.
        ([Operation.MULTIPLICATION], [1]),
        ([Operation.MULTIPLICATION], [10]),
        ([Operation.DIVISION], [1]),
        ([Operation.DIVISION], [10]),
        ([Operation.ADDITION], list(TABLES)),
        ([Operation.SUBTRACTION], list(TABLES)),
        ([Operation.ADDITION, Operation.DIVISION], [6, 7, 8]),
        (list(OPERATIONS), list(TABLES)),
    ],
)
def test_board_questions_are_all_different(operations: list[Operation], tables: list[int]) -> None:
    for _ in range(10):
        game = Game.with_settings(settings_of(operations, tables))
        prompts = [question.prompt for question in game.questions]
        assert len(set(prompts)) == Game.BOARD_SIZE


def test_a_wrong_answer_brings_a_question_not_on_the_board() -> None:
    game = Game.with_settings(settings_of([Operation.MULTIPLICATION], [7]))
    for _ in range(30):
        before = game.questions[4].prompt
        game.answer(4, -1)  # always wrong
        prompts = [question.prompt for question in game.questions]
        assert game.questions[4].prompt != before
        assert len(set(prompts)) == Game.BOARD_SIZE


def test_the_game_asks_to_avoid_the_questions_on_open_cells() -> None:
    asked: list[set[str]] = []
    numbers = count()

    def factory(difficulty: int, avoid: Collection[str]) -> Question:
        asked.append(set(avoid))
        return Question(f"q{next(numbers)}", 1, (1, 2, 3), Operation.ADDITION, difficulty)

    game = Game(factory)
    assert asked[0] == set()
    assert asked[-1] == {f"q{i}" for i in range(8)}  # the 8 cells already filled

    game.answer(0, 1)  # cell 0 is taken: its question is no longer on the board
    game.answer(4, 2)  # wrong: cell 4 gets a new question
    assert asked[-1] == {f"q{i}" for i in range(1, 9)}


def test_running_out_of_time_makes_the_other_player_win() -> None:
    game = Game(question_factory)
    game.answer(0, 1)  # X
    game.time_out(Mark.O)
    assert game.status is GameStatus.WON
    assert game.winner is Mark.X
    assert game.timed_out is Mark.O
    assert game.winning_line is None
    assert game.is_over
    assert not game.is_in_progress
    assert not game.is_available(4)


def test_time_out_is_only_possible_during_the_match() -> None:
    game = Game(question_factory)
    play(game, [0, 3, 1, 4, 2])
    with pytest.raises(ValueError, match="already over"):
        game.time_out(Mark.O)
    assert game.timed_out is None
