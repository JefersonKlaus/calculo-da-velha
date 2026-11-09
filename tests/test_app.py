"""End-to-end tests of the assembled app, driven through a fake page."""

import asyncio
import runpy
from pathlib import Path

import flet as ft
import pytest

import math_tic_tac_toe.app as app
from math_tic_tac_toe.game import Game, Mark
from math_tic_tac_toe.settings import (
    OPERATIONS,
    TABLES,
    GameSettings,
    Operation,
)
from math_tic_tac_toe.ui.layout import (
    PAGE_PADDING,
    ScreenSize,
    layout_for_screen,
    layout_for_width,
)
from math_tic_tac_toe.ui.styles import (
    CORRECT_ANSWER_COLOR,
    PLAYER_COLORS,
    WINNING_CELL_COLOR,
    WRONG_ANSWER_COLOR,
)
from support import FakePage, device, question_factory

MAIN_SCRIPT = Path(__file__).parents[1] / "src" / "main.py"


def content_of(view: ft.View) -> list[ft.Control]:
    """The controls inside a screen's frame (view > safe area > column)."""
    (safe_area,) = view.controls
    return safe_area.content.controls


class SettingsScreen:
    def __init__(self, view: ft.View) -> None:
        (column,) = content_of(view)
        self.title, self.operation_label, operations, self.tables, self.play = column.controls
        self.operations = dict(zip(OPERATIONS, operations.controls, strict=True))
        self.tables_label, *rows = self.tables.controls
        self.table_buttons = [button for row in rows for button in row.controls]

    def tap_operation(self, *operations: Operation) -> None:
        for operation in operations:
            self.operations[operation].on_click(None)

    def tap_table(self, *tables: int) -> None:
        for table in tables:
            self.table_buttons[table - 1].on_click(None)

    def selected_operations(self) -> list[Operation]:
        return [op for op, button in self.operations.items() if button.style.bgcolor is None]

    def selected_tables(self) -> list[int]:
        return [
            table
            for table, button in enumerate(self.table_buttons, start=1)
            if button.style.bgcolor is None
        ]


class RunningApp:
    """Starts ``app.main`` on a fake page; by default also taps "Play"."""

    def __init__(self, page: FakePage, play: bool = True) -> None:
        self.page = page
        asyncio.run(app.main(page))  # type: ignore[arg-type]
        self.settings = SettingsScreen(page.views[0])
        if play:
            self.play()

    def play(self) -> None:
        self.settings.play.on_click(None)
        header, status, board, self.restart = content_of(self.page.views[-1])
        _, self.title, self.settings_button = header.controls
        self.status, self.feedback = status.controls
        self.cells = [cell for row in board.controls for cell in row.controls]

    def routes(self) -> list[str]:
        return [view.route for view in self.page.views]

    def tap_cell(self, position: int) -> ft.AlertDialog:
        self.cells[position].on_click(None)
        return self.page.dialogs[-1]

    def answer(self, position: int, choice_index: int = 0) -> None:
        dialog = self.tap_cell(position)
        _, choices = dialog.content.controls
        choices.controls[choice_index].on_click(None)

    def labels(self) -> list[str]:
        return [cell.content.value for cell in self.cells]


@pytest.fixture(autouse=True)
def games(monkeypatch: pytest.MonkeyPatch) -> list[GameSettings]:
    """Predictable questions (the right answer is always the first choice);
    returns the settings of every game the app creates."""
    created: list[GameSettings] = []

    def with_settings(cls: type[Game], settings: GameSettings) -> Game:
        created.append(settings)
        return cls(question_factory)

    monkeypatch.setattr(Game, "with_settings", classmethod(with_settings))
    return created


def test_opens_on_the_settings_screen() -> None:
    running = RunningApp(FakePage(device("pt", "BR")), play=False)
    settings = running.settings
    assert running.routes() == ["/"]
    assert settings.title.value == "Configurações"
    assert settings.operation_label.value == "Operação"
    assert settings.tables_label.value == "Tabuada"
    assert settings.play.content.value == "Jogar"
    assert [button.content.value for button in settings.operations.values()] == [
        "+", "−", "×", "÷"
    ]
    assert [button.content.value for button in settings.table_buttons] == [
        str(table) for table in range(1, 11)
    ]


def test_everything_is_selected_when_the_app_opens(games: list[GameSettings]) -> None:
    running = RunningApp(FakePage(device("en")), play=False)
    assert running.settings.selected_operations() == list(OPERATIONS)
    assert running.settings.selected_tables() == list(TABLES)
    assert running.settings.tables.visible is True
    running.play()
    assert games[-1] == GameSettings.of(OPERATIONS, TABLES)


def test_tapping_one_option_when_all_are_selected_unselects_only_it(
    games: list[GameSettings],
) -> None:
    running = RunningApp(FakePage(device("en")), play=False)
    running.settings.tap_operation(Operation.ADDITION)
    running.settings.tap_table(5)
    assert running.settings.selected_operations() == [
        Operation.SUBTRACTION,
        Operation.MULTIPLICATION,
        Operation.DIVISION,
    ]
    assert running.settings.selected_tables() == [1, 2, 3, 4, 6, 7, 8, 9, 10]
    running.play()
    assert games[-1] == GameSettings.of(
        [Operation.SUBTRACTION, Operation.MULTIPLICATION, Operation.DIVISION],
        [1, 2, 3, 4, 6, 7, 8, 9, 10],
    )


def test_just_division_of_the_7_table(games: list[GameSettings]) -> None:
    running = RunningApp(FakePage(device("en")), play=False)
    running.settings.tap_operation(*(op for op in OPERATIONS if op is not Operation.DIVISION))
    running.settings.tap_table(*(table for table in TABLES if table != 7))
    running.settings.tap_table(7)  # the last selected one stays selected
    assert running.settings.selected_operations() == [Operation.DIVISION]
    assert running.settings.selected_tables() == [7]
    running.play()
    assert running.routes() == ["/", "/game"]
    assert games[-1] == GameSettings.of([Operation.DIVISION], [7])
    assert running.status.value == "X's turn"


def test_settings_button_goes_back_and_a_new_match_uses_new_settings(
    games: list[GameSettings],
) -> None:
    running = RunningApp(FakePage(device("en")))
    running.answer(0)
    assert running.settings_button.tooltip == "Settings"

    running.settings_button.on_click(None)
    assert running.routes() == ["/"]

    # + and − only: the times tables are hidden (and kept for later).
    running.settings.tap_operation(Operation.MULTIPLICATION, Operation.DIVISION)
    assert running.settings.tables.visible is False
    running.play()
    assert games[-1] == GameSettings.of([Operation.ADDITION, Operation.SUBTRACTION], TABLES)
    assert "X" not in running.labels()  # a brand new match


def test_phone_back_button_returns_to_the_settings() -> None:
    running = RunningApp(FakePage(device("en")))
    running.page.press_back()
    assert running.routes() == ["/"]


def test_starts_in_portuguese_on_a_portuguese_device() -> None:
    running = RunningApp(FakePage(device("pt", "BR")))
    assert running.page.title == "Cálculo da Velha"
    assert running.title.value == "Cálculo da Velha"
    assert running.settings_button.tooltip == "Configurações"
    assert running.status.value == "Vez de X"
    assert running.restart.content.value == "Jogar novamente"
    assert running.restart.visible is False


def test_starts_in_english_on_any_other_device() -> None:
    running = RunningApp(FakePage(device("de", "DE")))
    assert running.page.title == "Math Tic-Tac-Toe"
    assert running.settings.title.value == "Settings"
    assert running.settings.play.content.value == "Play"
    assert running.status.value == "X's turn"
    assert running.restart.content.value == "Restart"


def test_tapping_a_cell_opens_the_question_modal() -> None:
    running = RunningApp(FakePage(device("en")))
    dialog = running.tap_cell(4)
    assert dialog.modal
    assert dialog.title.value == "Solve the question"
    prompt, choices = dialog.content.controls
    assert prompt.value == "question 3"
    assert [button.content.value for button in choices.controls] == ["1", "2", "3"]


def test_choosing_an_answer_closes_the_modal_and_plays() -> None:
    running = RunningApp(FakePage(device("en")))
    running.answer(0)
    assert running.page.dialogs == []
    assert running.labels()[0] == "X"
    assert running.status.value == "O's turn"
    assert running.status.color == PLAYER_COLORS[Mark.O]
    assert running.feedback.value == "Correct answer."
    assert running.feedback.color == CORRECT_ANSWER_COLOR


def test_wrong_answer_is_shown_in_red_and_keeps_the_turn() -> None:
    running = RunningApp(FakePage(device("pt", "BR")))
    assert running.status.color == PLAYER_COLORS[Mark.X]
    running.answer(0, choice_index=1)  # choices are (1, 2, 3) and 1 is right
    assert running.feedback.value == "Resposta incorreta."
    assert running.feedback.color == WRONG_ANSWER_COLOR
    assert running.status.value == "Vez de X"
    assert running.status.color == PLAYER_COLORS[Mark.X]


def test_full_match_then_restart() -> None:
    running = RunningApp(FakePage(device("pt", "BR")))
    for position in (0, 3, 1, 4, 2):
        running.answer(position)

    assert running.status.value == "Fim de jogo: X venceu!"
    assert running.restart.visible is True
    gold = [i for i, cell in enumerate(running.cells) if cell.style.bgcolor is not None]
    assert gold == [0, 1, 2]
    assert all(cell.style.bgcolor[ft.ControlState.DISABLED] == WINNING_CELL_COLOR
               for cell in running.cells[:3])

    running.restart.on_click(None)

    assert running.restart.visible is False
    assert running.status.value == "Vez de X"
    assert running.feedback.value == ""
    assert "X" not in running.labels() and "O" not in running.labels()
    assert not any(cell.disabled for cell in running.cells)
    assert all(cell.style.bgcolor is None for cell in running.cells)


def test_mobile_entry_point_runs_the_app(monkeypatch: pytest.MonkeyPatch) -> None:
    started = []
    monkeypatch.setattr(ft, "run", started.append)
    runpy.run_path(str(MAIN_SCRIPT), run_name="__main__")
    assert started == [app.main]


def test_locks_the_phone_in_portrait() -> None:
    running = RunningApp(FakePage(device("en"), platform=ft.PagePlatform.IOS))
    assert running.page.orientations == [ft.DeviceOrientation.PORTRAIT_UP]


def test_board_fills_the_screen_width() -> None:
    running = RunningApp(FakePage(device("en"), width=412))
    layout = layout_for_width(412)
    for view in running.page.views:
        assert view.padding == PAGE_PADDING
        assert view.scroll == ft.ScrollMode.AUTO
    assert {cell.width for cell in running.cells} == {layout.cell_size}
    assert running.restart.width == layout.board_width


def test_board_follows_screen_size_changes() -> None:
    running = RunningApp(FakePage(device("en"), width=360))
    running.answer(0)
    updates = running.page.updates

    running.page.resize(800, 1280)

    tablet = layout_for_width(800)
    assert running.title.size == tablet.title_font_size
    assert running.status.size == tablet.status_font_size
    assert {cell.width for cell in running.cells} == {tablet.cell_size}
    assert running.cells[0].content.value == "X"
    assert running.cells[0].content.size == tablet.mark_font_size
    assert running.restart.width == tablet.board_width
    assert running.settings.play.width == tablet.board_width
    assert running.page.updates == updates + 1


def restart_fits(running: RunningApp, screen: ScreenSize) -> bool:
    """The whole screen, restart button included, fits the usable height
    (and so does the settings screen with its play button)."""
    layout = layout_for_screen(screen)
    assert running.restart.width == layout.board_width
    assert running.settings.play.width == layout.board_width
    assert {cell.width for cell in running.cells} == {layout.cell_size}
    usable = screen.usable_height
    return (
        usable is not None
        and layout.content_height <= usable
        and layout.settings_content_height <= usable
    )


@pytest.mark.parametrize(
    ("width", "height"),
    [(800, 800), (1280, 720), (884, 1000), (1024, 768)],
)
def test_restart_button_stays_on_screen_when_the_screen_is_wide(width: int, height: int) -> None:
    running = RunningApp(FakePage(device("en"), width=width, height=height, top_inset=24))
    for position in (0, 3, 1, 4, 2):
        running.answer(position)
    assert running.restart.visible is True
    assert restart_fits(running, ScreenSize(width, height, top_inset=24))


def test_restart_button_stays_on_screen_after_a_resize() -> None:
    running = RunningApp(FakePage(device("en"), width=360, height=740))
    running.page.resize(1280, 720)
    assert restart_fits(running, ScreenSize(1280, 720))


def test_layout_follows_the_system_bars() -> None:
    running = RunningApp(FakePage(device("en"), width=800, height=900))
    before = running.cells[0].width
    running.page.change_system_bars(top_inset=48, bottom_inset=48)
    assert running.cells[0].width < before
    assert restart_fits(running, ScreenSize(800, 900, top_inset=48, bottom_inset=48))
