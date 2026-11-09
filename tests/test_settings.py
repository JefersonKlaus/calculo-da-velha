import pytest

from math_tic_tac_toe.settings import (
    DEFAULT_SETTINGS,
    OPERATIONS,
    TABLES,
    GameSettings,
    Operation,
    toggle,
)

ADD, SUB, MUL, DIV = OPERATIONS


def test_tables_go_from_1_to_10() -> None:
    assert tuple(range(1, 11)) == TABLES


def test_everything_is_selected_by_default() -> None:
    assert DEFAULT_SETTINGS.operations == set(OPERATIONS)
    assert DEFAULT_SETTINGS.tables == set(TABLES)
    assert DEFAULT_SETTINGS == GameSettings() == GameSettings.of(OPERATIONS, TABLES)


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


def test_just_the_5_table() -> None:
    settings = DEFAULT_SETTINGS
    for table in TABLES:
        if table != 5:
            settings = settings.toggle_table(table)
    assert settings.tables == {5}
    assert settings.toggle_table(5).tables == {5}  # the last one stays


def test_selecting_again_after_unselecting() -> None:
    assert DEFAULT_SETTINGS.toggle_table(5).toggle_table(5) == DEFAULT_SETTINGS


def test_changing_operations_keeps_the_tables() -> None:
    settings = GameSettings.of([MUL], [7])
    back = settings.toggle_operation(ADD).toggle_operation(MUL)
    assert back == GameSettings.of([ADD], [7])
    assert back.toggle_operation(DIV).tables == {7}


@pytest.mark.parametrize(
    ("operations", "uses_tables"),
    [([ADD], False), ([ADD, SUB], False), ([MUL], True), ([ADD, DIV], True), (OPERATIONS, True)],
)
def test_uses_tables_when_any_operation_needs_them(operations, uses_tables: bool) -> None:
    assert GameSettings.of(operations).uses_tables is uses_tables


def test_accepts_any_collection_and_stores_frozensets() -> None:
    settings = GameSettings([MUL, MUL], {5})  # type: ignore[arg-type]
    assert settings.operations == frozenset({MUL})
    assert settings.tables == frozenset({5})
    assert settings == GameSettings.of([MUL], [5])


def test_needs_at_least_one_operation() -> None:
    with pytest.raises(ValueError):
        GameSettings.of([], [2])


@pytest.mark.parametrize("tables", [[], [0], [11], [5, 11]])
def test_needs_tables_between_1_and_10(tables: list[int]) -> None:
    with pytest.raises(ValueError):
        GameSettings.of([MUL], tables)
