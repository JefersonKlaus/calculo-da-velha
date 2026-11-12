from collections.abc import Collection
from itertools import count

import pytest

from math_tic_tac_toe.game import TURN_SECONDS, Game, GameStatus, Mark, MoveResult
from math_tic_tac_toe.questions import Question, question_factory_for
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


def test_a_wrong_answer_gives_the_cell_to_the_other_player() -> None:
    game = Game(question_factory)
    asked = game.questions[0]
    result = game.answer(0, 999)  # X is wrong
    assert result == MoveResult(correct=False)
    assert game.board[0] is Mark.O  # the other player's symbol
    assert game.questions[0] is asked
    assert not game.is_available(0)
    assert game.status is GameStatus.IN_PROGRESS
    assert game.current_player is Mark.O  # and the other player plays now


def test_a_wrong_answer_can_complete_the_other_players_line() -> None:
    game = Game(question_factory)
    play(game, [0, 3, 1, 4])  # O holds 3 and 4
    game.answer(5, 999)  # X is wrong on the last cell of O's row
    assert game.status is GameStatus.WON
    assert game.winner is Mark.O
    assert game.winning_line == (3, 4, 5)


def test_not_answering_in_time_is_like_a_wrong_answer() -> None:
    game = Game(question_factory)
    assert TURN_SECONDS == 10
    result = game.miss(4)
    assert result == MoveResult(correct=False)
    assert game.board[4] is Mark.O
    assert game.current_player is Mark.O
    assert game.is_in_progress
    with pytest.raises(ValueError, match="already taken"):
        game.miss(4)
    play(game, [3, 0, 5])  # O completes the middle row
    assert game.winner is Mark.O
    with pytest.raises(ValueError, match="already over"):
        game.miss(8)


def test_a_new_match_is_not_in_progress_until_someone_answers() -> None:
    game = Game(question_factory)
    assert not game.is_in_progress
    assert not game.is_over
    game.answer(0, 999)  # even a wrong answer starts the match
    assert game.is_in_progress
    game.answer(1, 1)
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


def test_a_cell_open_again_gets_a_question_not_on_the_board() -> None:
    game = Game(question_factory_for(settings_of([Operation.MULTIPLICATION], [7])), best_of=5)
    for _ in range(30):
        before = game.questions[4].prompt
        game.answer(4, game.questions[4].answer)  # the players take turns on it
        game.reset_cell(4)  # its time ran out
        prompts = [question.prompt for question in game.questions]
        assert game.questions[4].prompt != before
        assert len(set(prompts)) == Game.BOARD_SIZE


def test_the_game_asks_to_avoid_the_questions_on_open_cells() -> None:
    asked: list[set[str]] = []
    numbers = count()

    def factory(difficulty: int, avoid: Collection[str]) -> Question:
        asked.append(set(avoid))
        return Question(f"q{next(numbers)}", 1, (1, 2, 3), Operation.ADDITION, difficulty)

    game = Game(factory, best_of=5)
    assert asked[0] == set()
    assert asked[-1] == {f"q{i}" for i in range(8)}  # the 8 cells already filled

    game.answer(0, 1)  # cell 0 is taken: its question is no longer on the board
    game.answer(4, 1)
    game.reset_cell(4)  # open again: cell 4 gets a new question
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


# ---- best of 5 -------------------------------------------------------------------


def best_of_five() -> Game:
    return Game(question_factory, best_of=5)


def x_completes(game: Game, line: tuple[int, int, int]) -> None:
    """X's symbol fills ``line``: X answers right, O answers wrong."""
    for position in line:
        game.answer(position, 1 if game.current_player is Mark.X else 999)


def test_a_single_game_does_not_play_for_points() -> None:
    game = Game(question_factory)
    assert not game.plays_for_points
    assert game.points_to_win == 1


def test_best_of_five_is_won_with_3_points() -> None:
    game = best_of_five()
    assert game.plays_for_points
    assert game.points_to_win == 3
    assert game.scores == {Mark.X: 0, Mark.O: 0}


def test_with_settings_plays_the_chosen_best_of() -> None:
    game = Game.with_settings(settings_of(OPERATIONS).with_best_of(5))
    assert game.best_of == 5
    assert game.points_to_win == 3
    assert Game.with_settings(settings_of(OPERATIONS)).best_of is None


def test_a_line_scores_a_point_and_clears_its_cells() -> None:
    game = best_of_five()
    play(game, [0, 3, 1, 4])
    before = list(game.questions)
    result = game.answer(2, 1)  # X completes the top row

    assert result == MoveResult(correct=True, point_for=Mark.X, points=1, scored_cells=(0, 1, 2))
    assert game.scores == {Mark.X: 1, Mark.O: 0}
    assert game.board == [None, None, None, Mark.O, Mark.O, None, None, None, None]
    assert all(game.questions[p] is not before[p] for p in (0, 1, 2))  # new questions
    assert game.questions[5] is before[5]  # the other cells do not change
    # The match goes on, with the other player's turn.
    assert game.status is GameStatus.IN_PROGRESS
    assert game.winning_line is None
    assert game.current_player is Mark.O


def test_a_right_answer_without_a_line_scores_nothing() -> None:
    game = best_of_five()
    assert game.answer(0, 1) == MoveResult(correct=True)
    assert game.scores == {Mark.X: 0, Mark.O: 0}


def test_both_players_score() -> None:
    game = best_of_five()
    play(game, [0, 3, 1, 4, 8, 5])  # O completes the middle row
    assert game.scores == {Mark.X: 0, Mark.O: 1}
    assert game.board[3:6] == [None, None, None]
    assert game.board[0] is Mark.X  # X's cells stay


def test_the_third_point_wins_and_keeps_its_line() -> None:
    game = best_of_five()
    x_completes(game, (0, 1, 2))
    x_completes(game, (3, 4, 5))
    assert game.scores[Mark.X] == 2
    assert not game.is_over

    x_completes(game, (6, 7, 8))

    assert game.scores == {Mark.X: 3, Mark.O: 0}
    assert game.status is GameStatus.WON
    assert game.winner is Mark.X
    # Like a normal win, the winning line stays on the board (in gold).
    assert game.winning_line == (6, 7, 8)
    assert game.board[6:9] == [Mark.X, Mark.X, Mark.X]
    assert not game.is_in_progress


def test_a_move_that_completes_two_lines_scores_two_points_and_clears_both() -> None:
    game = best_of_five()
    play(game, [1, 4, 2, 5, 3, 7, 6, 8])
    result = game.answer(0, 1)  # X: top row and left column at once

    assert result.points == 2
    assert game.scores == {Mark.X: 2, Mark.O: 0}
    assert not game.is_over
    for position in (0, 1, 2, 3, 6):
        assert game.board[position] is None
    for position in (4, 5, 7, 8):
        assert game.board[position] is Mark.O


def test_a_wrong_answer_can_score_for_the_other_player() -> None:
    game = best_of_five()
    play(game, [0, 3, 1, 4])  # O holds 3 and 4
    result = game.answer(5, 999)  # X is wrong: O's symbol completes O's row
    assert result == MoveResult(correct=False, point_for=Mark.O, points=1, scored_cells=(3, 4, 5))
    assert game.scores == {Mark.X: 0, Mark.O: 1}
    assert game.board[3:6] == [None, None, None]
    assert game.current_player is Mark.O


def test_a_full_board_is_not_a_draw_in_a_best_of() -> None:
    game = best_of_five()
    play(game, [0, 1, 2, 4, 3, 5, 7, 6, 8])  # a draw in a single game
    assert all(mark is not None for mark in game.board)
    assert game.status is GameStatus.IN_PROGRESS
    assert game.current_player is Mark.O  # waits for a cell to free up


@pytest.mark.parametrize(
    ("prompt", "answer", "seconds"),
    [
        ("4 × 8", 32, 32),  # the result is the biggest number
        ("15 − 9", 6, 15),  # the first number is
        ("2 + 3", 5, 5),
        ("70 ÷ 7", 10, 60),  # 70 is more than the 60 seconds allowed
        ("9 × 9", 81, 60),
    ],
)
def test_a_played_cell_lasts_as_many_seconds_as_its_biggest_number(
    prompt: str, answer: int, seconds: int
) -> None:
    def factory(difficulty: int, avoid: Collection[str] = ()) -> Question:
        return Question(prompt, answer, (answer, answer + 1), Operation.MULTIPLICATION, difficulty)

    game = Game(factory, best_of=5)
    game.answer(0, answer)
    assert game.cell_seconds(0) == seconds


def test_an_open_cell_tells_how_long_a_mark_would_last() -> None:
    game = best_of_five()
    assert game.board[4] is None
    assert game.cell_seconds(4) == 3  # "question 3": 3 seconds


def test_skipping_a_turn_passes_it_without_starting_the_match() -> None:
    game = Game(question_factory)
    game.skip_turn()  # X's time ran out before choosing a cell
    assert game.current_player is Mark.O
    assert game.board == [None] * 9
    assert not game.is_in_progress
    play(game, [0, 3, 1, 4, 2])  # O wins
    with pytest.raises(ValueError, match="already over"):
        game.skip_turn()


def test_resetting_a_cell_opens_it_with_a_new_question() -> None:
    game = best_of_five()
    play(game, [0, 4])
    answered = game.questions[0]

    game.reset_cell(0)

    assert game.board[0] is None
    assert game.questions[0] is not answered
    assert game.is_available(0)
    assert game.current_player is Mark.X  # the turn does not change
    assert game.board[4] is Mark.O


def test_only_a_played_cell_of_a_running_best_of_can_be_reset() -> None:
    single = Game(question_factory)
    single.answer(0, 1)
    with pytest.raises(ValueError, match="Only best of N"):
        single.reset_cell(0)
    with pytest.raises(ValueError, match="no mark"):
        best_of_five().reset_cell(0)
    won = best_of_five()
    for line in ((0, 1, 2), (3, 4, 5), (6, 7, 8)):
        x_completes(won, line)
    with pytest.raises(ValueError, match="already over"):
        won.reset_cell(6)


def test_the_result_tells_which_cells_scored() -> None:
    game = best_of_five()
    play(game, [1, 4, 2, 5, 3, 7, 6, 8])
    result = game.answer(0, 1)  # two lines at once
    assert result.scored_cells == (0, 1, 2, 3, 6)
    assert Game(question_factory).answer(0, 1).scored_cells == ()  # no point, no cells


def test_a_winning_move_keeps_every_line_it_completed() -> None:
    single = Game(question_factory)
    play(single, [1, 4, 2, 5, 3, 7, 6, 8, 0])  # X: top row and left column at once
    assert single.winner is Mark.X
    assert single.winning_line == (0, 1, 2)
    assert single.winning_cells == (0, 1, 2, 3, 6)


def test_two_points_can_win_and_the_score_stops_at_3() -> None:
    game = best_of_five()
    game.scores[Mark.X] = 2
    play(game, [1, 4, 2, 5, 3, 7, 6, 8])
    result = game.answer(0, 1)  # two lines: 2 + 2, but 3 already wins
    assert result.points == 2
    assert game.scores == {Mark.X: 3, Mark.O: 0}
    assert game.winner is Mark.X
    assert game.winning_cells == (0, 1, 2, 3, 6)  # both lines stay, in gold
