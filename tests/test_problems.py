import re

import pytest

from math_tic_tac_toe.problems import (
    AdditionProblems,
    DivisionProblems,
    MultiplicationProblems,
    SubtractionProblems,
    max_operand,
    problem_maker,
    problems_for,
)
from math_tic_tac_toe.settings import OPERATIONS, TABLES, Operation
from tests.support import settings_of

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


@pytest.mark.parametrize("table", [1, 7, 10])
def test_multiplication_of_one_table(table: int) -> None:
    problems = MultiplicationProblems([table]).problems(1)
    assert [prompt for prompt, _, _ in problems] == [f"{table} × {f}" for f in range(1, 11)]
    assert [answer for _, answer, _ in problems] == [table * f for f in range(1, 11)]
    assert {operation for _, _, operation in problems} == {MUL}
    # Every cell draws from the whole table, at every difficulty.
    assert MultiplicationProblems([table]).problems(3) == problems


@pytest.mark.parametrize("table", [1, 7, 10])
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
    [
        (ADD, AdditionProblems),
        (SUB, SubtractionProblems),
        (MUL, MultiplicationProblems),
        (DIV, DivisionProblems),
    ],
)
def test_problem_maker_per_operation(operation: Operation, kind: type) -> None:
    maker = problem_maker(operation, [7])
    assert isinstance(maker, kind)
    if operation.uses_table:
        assert maker.tables == (7,)


def test_problems_follow_the_settings_in_the_usual_order() -> None:
    makers = problems_for(settings_of([DIV, ADD], [5, 7]))
    assert [type(maker) for maker in makers] == [AdditionProblems, DivisionProblems]
    assert makers[1].tables == (5, 7)
