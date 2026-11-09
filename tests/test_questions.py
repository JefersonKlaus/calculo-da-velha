import re
from collections import Counter
from random import Random

import pytest

from math_tic_tac_toe.questions import (
    AdditionProblems,
    DivisionProblems,
    MultiplicationProblems,
    QuestionGenerator,
    SubtractionProblems,
    max_operand,
    problem_maker,
    problems_for,
    question_factory_for,
)
from math_tic_tac_toe.settings import OPERATIONS, TABLES, GameSettings, Operation

ADD, SUB, MUL, DIV = OPERATIONS


def numbers(prompt: str) -> tuple[int, int]:
    left, right = re.findall(r"\d+", prompt)
    return int(left), int(right)


@pytest.mark.parametrize("difficulty", [1, 2, 3])
def test_addition(difficulty: int) -> None:
    problems = AdditionProblems().problems(difficulty)
    assert len(problems) == max_operand(difficulty) ** 2
    for prompt, answer, operation in problems:
        left, right = numbers(prompt)
        assert prompt == f"{left} + {right}"
        assert answer == left + right
        assert operation is ADD
        assert 1 <= left <= max_operand(difficulty)
        assert 1 <= right <= max_operand(difficulty)


@pytest.mark.parametrize("difficulty", [1, 2, 3])
def test_subtraction_never_goes_negative(difficulty: int) -> None:
    for prompt, answer, operation in SubtractionProblems().problems(difficulty):
        left, right = numbers(prompt)
        assert prompt == f"{left} − {right}"
        assert answer == left - right >= 0
        assert operation is SUB
        assert left <= max_operand(difficulty)


def test_operands_grow_with_difficulty() -> None:
    assert max_operand(1) < max_operand(2) < max_operand(3)


@pytest.mark.parametrize("table", TABLES)
def test_multiplication_of_one_table(table: int) -> None:
    problems = MultiplicationProblems([table]).problems(1)
    assert [prompt for prompt, _, _ in problems] == [f"{table} × {f}" for f in range(1, 11)]
    assert [answer for _, answer, _ in problems] == [table * f for f in range(1, 11)]
    assert {operation for _, _, operation in problems} == {MUL}
    # Every cell draws from the whole table, at every difficulty.
    assert MultiplicationProblems([table]).problems(3) == problems


@pytest.mark.parametrize("table", TABLES)
def test_division_of_one_table(table: int) -> None:
    problems = DivisionProblems([table]).problems(1)
    for prompt, answer, operation in problems:
        dividend, divisor = numbers(prompt)
        assert prompt == f"{dividend} ÷ {table}"
        assert (divisor, dividend) == (table, table * answer)
        assert operation is DIV
    assert [answer for _, answer, _ in problems] == list(range(1, 11))


def test_several_tables_combine_all_their_facts() -> None:
    problems = MultiplicationProblems([7, 5]).problems(1)
    assert len(problems) == 20
    assert {numbers(prompt)[0] for prompt, _, _ in problems} == {5, 7}
    assert len(DivisionProblems(TABLES).problems(1)) == 100


@pytest.mark.parametrize(
    ("operation", "kind"),
    [(ADD, AdditionProblems), (SUB, SubtractionProblems), (MUL, MultiplicationProblems),
     (DIV, DivisionProblems)],
)
def test_problem_maker_per_operation(operation: Operation, kind: type) -> None:
    maker = problem_maker(operation, [7])
    assert isinstance(maker, kind)
    if operation.uses_table:
        assert maker.tables == (7,)


def test_problems_follow_the_settings_in_the_usual_order() -> None:
    makers = problems_for(GameSettings.of([DIV, ADD], [5, 7]))
    assert [type(maker) for maker in makers] == [AdditionProblems, DivisionProblems]
    assert makers[1].tables == (5, 7)


def test_question_factory_for_settings() -> None:
    question = question_factory_for(GameSettings.of([DIV], [7]), Random(3))(2, ())
    assert question.operation is DIV
    assert question.difficulty == 2
    assert question.prompt.endswith("÷ 7")
    assert question.answer in question.choices


def test_default_generator_uses_every_operation() -> None:
    generator = QuestionGenerator(random=Random(1))
    assert {generator.generate().operation for _ in range(200)} == set(OPERATIONS)


def test_every_chosen_operation_shows_up_about_equally() -> None:
    # Addition has hundreds of problems and a single table only 10, but each
    # question first picks an operation, so none of them drowns the others.
    generator = QuestionGenerator(problems_for(GameSettings.of(OPERATIONS, [5])), Random(7))
    counts = Counter(generator.generate(3).operation for _ in range(4000))
    assert set(counts) == set(OPERATIONS)
    assert all(800 < count < 1200 for count in counts.values())


def test_every_chosen_table_shows_up() -> None:
    generator = QuestionGenerator(problems_for(GameSettings.of([MUL], [3, 6, 9])), Random(2))
    tables = {numbers(generator.generate().prompt)[0] for _ in range(200)}
    assert tables == {3, 6, 9}


@pytest.mark.parametrize("operation", OPERATIONS)
def test_choices_include_one_correct_answer_and_are_distinct(operation: Operation) -> None:
    generator = QuestionGenerator(problems_for(GameSettings.of([operation], [3])), Random(2))
    for difficulty in (1, 2, 3):
        question = generator.generate(difficulty)
        assert question.answer in question.choices
        assert len(question.choices) == len(set(question.choices)) == 3
        assert min(question.choices) >= 0


def test_choice_count_is_configurable() -> None:
    question = QuestionGenerator(random=Random(5), choice_count=5).generate()
    assert len(set(question.choices)) == 5
    assert question.answer in question.choices


def test_small_answers_still_get_enough_distinct_choices() -> None:
    generator = QuestionGenerator([SubtractionProblems()], Random(3), choice_count=4)
    for _ in range(50):
        assert len(set(generator.generate().choices)) == 4


def test_avoids_the_given_prompts_while_others_remain() -> None:
    generator = QuestionGenerator([MultiplicationProblems([7])], Random(4))
    taken = {f"7 × {factor}" for factor in range(1, 10)}  # everything but 7 × 10
    for _ in range(20):
        assert generator.generate(1, avoid=taken).prompt == "7 × 10"


def test_skips_an_operation_whose_problems_are_all_taken() -> None:
    generator = QuestionGenerator(problems_for(GameSettings.of([ADD, MUL], [7])), Random(4))
    taken = {f"7 × {factor}" for factor in range(1, 11)}
    for _ in range(20):
        assert generator.generate(1, avoid=taken).operation is ADD


def test_repeats_only_when_every_problem_is_avoided() -> None:
    generator = QuestionGenerator([MultiplicationProblems([7])], Random(4))
    everything = {f"7 × {factor}" for factor in range(1, 11)}
    assert generator.generate(1, avoid=everything).prompt in everything


def test_rejects_fewer_than_two_choices() -> None:
    with pytest.raises(ValueError):
        QuestionGenerator(choice_count=1)


def test_rejects_an_empty_list_of_problem_makers() -> None:
    with pytest.raises(ValueError):
        QuestionGenerator([])


def test_rejects_non_positive_difficulty() -> None:
    with pytest.raises(ValueError):
        QuestionGenerator().generate(0)
