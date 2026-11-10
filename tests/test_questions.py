import re
from collections import Counter
from random import Random

import pytest

from math_tic_tac_toe.problems import MultiplicationProblems, SubtractionProblems, problems_for
from math_tic_tac_toe.questions import QuestionGenerator, question_factory_for
from math_tic_tac_toe.settings import OPERATIONS, Operation
from tests.support import settings_of

ADD, SUB, MUL, DIV = OPERATIONS


def numbers(prompt: str) -> tuple[int, int]:
    left, right = re.findall(r"\d+", prompt)
    return int(left), int(right)


def test_question_factory_for_settings() -> None:
    question = question_factory_for(settings_of([DIV], [7]), Random(3))(2, ())
    assert question.operation is DIV
    assert question.difficulty == 2
    assert question.prompt.endswith("÷ 7")
    assert question.answer in question.choices


def test_every_chosen_operation_shows_up_about_equally() -> None:
    # Addition has hundreds of problems and a single table only 10, but each
    # question first picks an operation, so none of them drowns the others.
    generator = QuestionGenerator(problems_for(settings_of(OPERATIONS, [5])), Random(7))
    counts = Counter(generator.generate(3).operation for _ in range(4000))
    assert set(counts) == set(OPERATIONS)
    assert all(800 < count < 1200 for count in counts.values())


def test_every_chosen_table_shows_up() -> None:
    generator = QuestionGenerator(problems_for(settings_of([MUL], [3, 6, 9])), Random(2))
    tables = {numbers(generator.generate().prompt)[0] for _ in range(200)}
    assert tables == {3, 6, 9}


@pytest.mark.parametrize("operation", OPERATIONS)
def test_choices_include_one_correct_answer_and_are_distinct(operation: Operation) -> None:
    generator = QuestionGenerator(problems_for(settings_of([operation], [3])), Random(2))
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
    generator = QuestionGenerator(problems_for(settings_of([ADD, MUL], [7])), Random(4))
    taken = {f"7 × {factor}" for factor in range(1, 11)}
    for _ in range(20):
        assert generator.generate(1, avoid=taken).operation is ADD


def test_repeats_only_when_every_problem_is_avoided() -> None:
    generator = QuestionGenerator([MultiplicationProblems([7])], Random(4))
    everything = {f"7 × {factor}" for factor in range(1, 11)}
    assert generator.generate(1, avoid=everything).prompt in everything


def test_rejects_fewer_than_two_choices() -> None:
    with pytest.raises(ValueError, match="At least two answer choices"):
        QuestionGenerator(choice_count=1)


def test_rejects_an_empty_list_of_problem_makers() -> None:
    with pytest.raises(ValueError, match="At least one problem maker"):
        QuestionGenerator([])


def test_rejects_non_positive_difficulty() -> None:
    with pytest.raises(ValueError, match="Difficulty must be positive"):
        QuestionGenerator().generate(0)
