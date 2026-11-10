from collections.abc import Collection

import pytest

from math_tic_tac_toe.settings import (
    DEFAULT_SETTINGS,
    MAX_TIME_LIMIT,
    MIN_TIME_LIMIT,
    OPERATIONS,
    TABLES,
    GameSettings,
    Operation,
    snap_time_limit,
    toggle,
)
from tests.support import settings_of

ADD, SUB, MUL, DIV = OPERATIONS


def test_everything_is_selected_by_default_and_untimed() -> None:
    assert DEFAULT_SETTINGS.operations == set(OPERATIONS)
    assert DEFAULT_SETTINGS.tables == set(TABLES)
    assert DEFAULT_SETTINGS.time_limit is None
    assert DEFAULT_SETTINGS == GameSettings() == settings_of(OPERATIONS, TABLES)


@pytest.mark.parametrize(
    ("operation", "symbol", "uses_table"),
    [(ADD, "+", False), (SUB, "−", False), (MUL, "×", True), (DIV, "÷", True)],
)
def test_operations(operation: Operation, symbol: str, uses_table: bool) -> None:
    assert operation.symbol == symbol
    assert operation.uses_table is uses_table


# --- toggle: the selection rule shared by operations and tables ---


def test_toggle_selects_an_unselected_option() -> None:
    assert toggle(frozenset({5}), 7) == {5, 7}


def test_toggle_unselects_a_selected_option() -> None:
    assert toggle(frozenset({5, 7}), 7) == {5}


def test_toggle_with_everything_selected_unselects_only_that_option() -> None:
    assert toggle(frozenset(TABLES), 5) == set(TABLES) - {5}


def test_toggle_keeps_the_last_selected_option() -> None:
    assert toggle(frozenset({5}), 5) == {5}


# --- GameSettings ---


def test_unselecting_one_table_keeps_the_others() -> None:
    assert DEFAULT_SETTINGS.toggle_table(5).tables == set(TABLES) - {5}


def test_unselecting_one_operation_keeps_the_others() -> None:
    assert DEFAULT_SETTINGS.toggle_operation(ADD).operations == {SUB, MUL, DIV}


def test_changing_operations_keeps_the_tables() -> None:
    settings = settings_of([MUL], [7])
    back = settings.toggle_operation(ADD).toggle_operation(MUL)
    assert back == settings_of([ADD], [7])
    assert back.toggle_operation(DIV).tables == {7}


@pytest.mark.parametrize(
    ("operations", "uses_tables"),
    [([ADD], False), ([ADD, SUB], False), ([MUL], True), ([ADD, DIV], True), (OPERATIONS, True)],
)
def test_uses_tables_when_any_operation_needs_them(
    operations: Collection[Operation], uses_tables: bool
) -> None:
    assert settings_of(operations).uses_tables is uses_tables


def test_accepts_any_collection_and_stores_frozensets() -> None:
    settings = GameSettings([MUL, MUL], {5})  # type: ignore[arg-type]
    assert settings.operations == frozenset({MUL})
    assert settings.tables == frozenset({5})
    assert settings == settings_of([MUL], [5])


def test_needs_at_least_one_operation() -> None:
    with pytest.raises(ValueError, match="At least one operation"):
        settings_of([], [2])


@pytest.mark.parametrize("tables", [[], [0], [11], [5, 11]])
def test_needs_tables_between_1_and_10(tables: list[int]) -> None:
    with pytest.raises(ValueError, match="Choose at least one table between 1 and 10"):
        settings_of([MUL], tables)


def test_with_time_limit_keeps_the_other_choices() -> None:
    chosen = settings_of([MUL], [7])
    hard = chosen.with_time_limit(90)
    assert hard.time_limit == 90
    assert (hard.operations, hard.tables) == (chosen.operations, chosen.tables)
    assert hard.with_time_limit(None) == chosen


def test_toggles_keep_the_time_limit() -> None:
    hard = DEFAULT_SETTINGS.with_time_limit(45)
    assert hard.toggle_operation(ADD).time_limit == 45
    assert hard.toggle_table(3).time_limit == 45


@pytest.mark.parametrize("seconds", [MIN_TIME_LIMIT - 1, MAX_TIME_LIMIT + 1])
def test_rejects_a_time_limit_out_of_range(seconds: int) -> None:
    with pytest.raises(ValueError, match="The time limit must be from 5 to 300 seconds"):
        DEFAULT_SETTINGS.with_time_limit(seconds)


@pytest.mark.parametrize(
    ("value", "seconds"),
    [
        (60, 60),
        (62.4, 60),  # the nearest step
        (62.6, 65),
        (300, 300),
        (0, MIN_TIME_LIMIT),  # never below the minimum
        (301, MAX_TIME_LIMIT),  # never above the maximum
    ],
)
def test_snap_time_limit_turns_the_bar_position_into_a_valid_time(
    value: float, seconds: int
) -> None:
    assert snap_time_limit(value) == seconds
    assert DEFAULT_SETTINGS.with_time_limit(seconds).time_limit == seconds
