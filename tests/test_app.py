"""End-to-end tests of the assembled app, driven through a fake page."""

import asyncio
import runpy
from functools import partial
from pathlib import Path

import flet as ft
import pytest

import math_tic_tac_toe.app as app
from math_tic_tac_toe.cell_timers import CellTimers
from math_tic_tac_toe.clock import ChessClock, Countdown
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
)
from math_tic_tac_toe.ui.styles import (
    ACCENT_COLOR,
    ALERT_COLOR,
    BACKGROUND_COLOR,
    PLAYER_COLORS,
    SELECTED_OPTION_COLOR,
    THEME_SEED_COLOR,
    WINNER_MESSAGE_COLOR,
    WINNING_CELL_COLOR,
)
from tests.support import (
    FakePage,
    FakeTime,
    background_of,
    click,
    device,
    layout_for_width,
    question_factory,
    settings_content_height,
    settings_of,
    slide,
)

MAIN_SCRIPT = Path(__file__).parents[1] / "src" / "main.py"


def content_of(view: ft.View) -> list[ft.Control]:
    """The controls inside a screen's frame (view > safe area > column)."""
    (safe_area,) = view.controls
    return safe_area.content.controls


class SettingsScreen:
    def __init__(self, view: ft.View) -> None:
        (column,) = content_of(view)
        (
            self.title,
            self.hint,
            self.operation_label,
            operations,
            self.tables,
            self.play,
            modes,
        ) = column.controls
        self.best_of, self.hard_mode = modes.controls
        self.operations = dict(zip(OPERATIONS, operations.controls, strict=True))
        self.tables_label, *rows = self.tables.controls
        self.table_buttons = [button for row in rows for button in row.controls]

    def tap_operation(self, *operations: Operation) -> None:
        for operation in operations:
            click(self.operations[operation])

    def tap_table(self, *tables: int) -> None:
        for table in tables:
            click(self.table_buttons[table - 1])

    def selected_operations(self) -> list[Operation]:
        return [
            op
            for op, button in self.operations.items()
            if background_of(button) == SELECTED_OPTION_COLOR
        ]

    def selected_tables(self) -> list[int]:
        return [
            table
            for table, button in enumerate(self.table_buttons, start=1)
            if background_of(button) == SELECTED_OPTION_COLOR
        ]


class RunningApp:
    """Starts ``app.main`` on a fake page; by default also taps "Play"."""

    def __init__(self, page: FakePage, play: bool = True) -> None:
        self.page = page
        asyncio.run(app.main(page.as_page()))
        self.settings = SettingsScreen(page.views[0])
        if play:
            self.play()

    def play(self) -> None:
        click(self.settings.play)
        self.find_game_controls()

    def play_best_of(self) -> None:
        click(self.settings.best_of)
        self.find_game_controls()

    def cell_countdown(self, position: int) -> tuple[str, str]:
        """A cell of a best of 5: its question or mark and, below it, its
        seconds."""
        label, countdown = self.cells[position].content.controls
        return label.value, countdown.value

    def play_hard_mode(self, seconds: int | None = None) -> None:
        """Taps "Hard mode", optionally moves the bar to ``seconds``, and
        taps "Start"."""
        click(self.settings.hard_mode)
        *_, time_bar = self.page.dialogs[-1].content.controls
        _, bar, _ = time_bar.controls
        if seconds is not None:
            slide(bar, seconds)
        _, start = self.page.dialogs[-1].actions
        click(start)
        self.page.finish_closing_dialogs()  # the match starts once it is gone
        self.find_game_controls()

    def find_game_controls(self) -> None:
        header, self.timers, self.score, status, board, self.restart = content_of(
            self.page.views[-1]
        )
        _, self.title, self.settings_button = header.controls
        status_line, self.feedback = status.controls
        self.status, self.turn_time = status_line.controls
        self.cells = [cell for row in board.controls for cell in row.controls]

    def tick(self) -> None:
        """Runs one step of the app's background clock task."""
        (task,) = self.page.tasks
        _, (on_tick,) = task
        on_tick()

    def timer_texts(self) -> list[str]:
        return [timer.content.value for timer in self.timers.controls]

    def routes(self) -> list[str]:
        return [view.route for view in self.page.views]

    def tap_cell(self, position: int) -> ft.AlertDialog:
        click(self.cells[position])
        return self.page.dialogs[-1]

    def answer(self, position: int, choice_index: int = 0) -> None:
        dialog = self.tap_cell(position)
        *_, choices = dialog.content.controls
        click(choices.controls[choice_index])
        self.page.finish_closing_dialogs()

    def cancel(self, position: int) -> None:
        dialog = self.tap_cell(position)
        (cancel,) = dialog.actions
        click(cancel)
        self.page.finish_closing_dialogs()

    def feedback_text(self) -> str:
        """The red line below the status, as the player reads it."""
        return "".join(span.text for span in self.feedback.spans or [])

    def feedback_colors(self) -> list[tuple[str, str | None]]:
        """Each piece of the red line with its color."""
        return [(span.text, span.style.color) for span in self.feedback.spans or []]

    def labels(self) -> list[str]:
        """Each cell's question or mark (without a best of 5's seconds)."""
        return [label_of(cell) for cell in self.cells]


def label_of(cell: ft.Control) -> str:
    """A cell's question or mark; in a best of 5 its seconds go below it."""
    content = cell.content
    return content.controls[0].value if isinstance(content, ft.Column) else content.value


@pytest.fixture(autouse=True)
def time(monkeypatch: pytest.MonkeyPatch) -> FakeTime:
    """The hard mode clock runs on a fake time that tests move by hand."""
    fake = FakeTime()
    monkeypatch.setattr(app, "ChessClock", partial(ChessClock, now=fake))
    monkeypatch.setattr(app, "CellTimers", partial(CellTimers, now=fake))
    monkeypatch.setattr(app, "Countdown", partial(Countdown, now=fake))
    return fake


@pytest.fixture(autouse=True)
def games(monkeypatch: pytest.MonkeyPatch) -> list[GameSettings]:
    """Predictable questions (the right answer is always the first choice);
    returns the settings of every game the app creates."""
    created: list[GameSettings] = []

    def with_settings(cls: type[Game], settings: GameSettings) -> Game:
        created.append(settings)
        return cls(question_factory, best_of=settings.best_of)

    monkeypatch.setattr(Game, "with_settings", classmethod(with_settings))
    return created


def test_opens_on_the_settings_screen() -> None:
    running = RunningApp(FakePage(device("pt", "BR")), play=False)
    settings = running.settings
    assert running.routes() == ["/"]
    assert settings.title.value == "Configurações"
    assert settings.hint.value == (
        "Em rosa: opções selecionadas. Toque em uma opção para marcar ou desmarcar."
    )
    assert settings.operation_label.value == "Operação"
    assert settings.tables_label.value == "Tabuada"
    assert settings.play.content.value == "Jogar"
    assert settings.hard_mode.content.value == "Modo difícil"
    assert [button.content.value for button in settings.operations.values()] == ["+", "−", "×", "÷"]
    assert [button.content.value for button in settings.table_buttons] == [
        str(table) for table in range(1, 11)
    ]
    # Everything starts selected.
    assert settings.selected_operations() == list(OPERATIONS)
    assert settings.selected_tables() == list(TABLES)


def test_the_theme_is_dark_navy_with_the_pink_the_settings_hint_talks_about() -> None:
    running = RunningApp(FakePage(device("en")), play=False)
    page = running.page
    # The design is dark, whatever the phone's setting.
    assert page.theme_mode == ft.ThemeMode.DARK
    assert page.dark_theme is page.theme
    assert page.bgcolor == BACKGROUND_COLOR
    assert all(view.bgcolor == BACKGROUND_COLOR for view in page.views)
    # Selected options are pink, the theme's accent: "In pink" must be true.
    assert SELECTED_OPTION_COLOR == ACCENT_COLOR == THEME_SEED_COLOR == "#FF5D98"
    assert page.theme.color_scheme_seed == THEME_SEED_COLOR
    assert page.theme.color_scheme.primary == ACCENT_COLOR
    assert page.theme.color_scheme.surface == BACKGROUND_COLOR


def test_just_division_of_the_7_table(games: list[GameSettings]) -> None:
    running = RunningApp(FakePage(device("en")), play=False)
    running.settings.tap_operation(*(op for op in OPERATIONS if op is not Operation.DIVISION))
    running.settings.tap_table(*(table for table in TABLES if table != 7))
    running.settings.tap_table(7)  # the last selected one stays selected
    assert running.settings.selected_operations() == [Operation.DIVISION]
    assert running.settings.selected_tables() == [7]
    running.play()
    assert running.routes() == ["/", "/game"]
    assert games[-1] == settings_of([Operation.DIVISION], [7])
    assert running.status.value == "X's turn"


def test_settings_button_goes_back_and_a_new_match_uses_new_settings(
    games: list[GameSettings],
) -> None:
    running = RunningApp(FakePage(device("en")))
    assert running.settings_button.tooltip == "Settings"

    click(running.settings_button)  # nobody answered yet: nothing to lose
    assert running.page.dialogs == []
    assert running.routes() == ["/"]

    # + and − only: the times tables are hidden (and kept for later).
    running.settings.tap_operation(Operation.MULTIPLICATION, Operation.DIVISION)
    assert running.settings.tables.visible is False
    running.play()
    assert games[-1] == settings_of([Operation.ADDITION, Operation.SUBTRACTION], TABLES)
    assert "X" not in running.labels()  # a brand new match


def tap_settings(running: RunningApp) -> ft.AlertDialog | None:
    """Taps the settings button; returns the confirmation, if one opened."""
    open_before = len(running.page.dialogs)
    click(running.settings_button)
    return running.page.dialogs[-1] if len(running.page.dialogs) > open_before else None


def test_settings_button_in_the_middle_of_a_match_asks_for_confirmation() -> None:
    running = RunningApp(FakePage(device("pt", "BR")))
    running.answer(0)

    dialog = tap_settings(running)

    assert dialog is not None
    assert dialog.modal
    assert dialog.title.value == "Sair da partida?"
    assert dialog.content.value == "A partida atual será perdida."
    cancel, confirm = dialog.actions
    assert (cancel.content, confirm.content) == ("Cancelar", "Sair")
    assert running.routes() == ["/", "/game"]  # nothing happens until they agree


def test_canceling_the_settings_confirmation_keeps_the_match() -> None:
    running = RunningApp(FakePage(device("en")))
    running.answer(0)
    dialog = tap_settings(running)
    assert dialog is not None
    cancel, _ = dialog.actions

    click(cancel)
    running.page.finish_closing_dialogs()

    assert running.page.dialogs == []
    assert running.routes() == ["/", "/game"]
    assert running.labels()[0] == "X"  # the match goes on
    assert running.status.value == "O's turn"


def test_confirming_goes_to_the_settings_once_the_dialog_is_gone() -> None:
    running = RunningApp(FakePage(device("en")))
    running.answer(0)
    dialog = tap_settings(running)
    assert dialog is not None
    _, confirm = dialog.actions

    click(confirm)
    click(confirm)  # a second tap while it is closing changes nothing
    # Switching screens while the dialog is still closing would leave it
    # behind, stuck open (the fake page fails if that happens).
    assert running.routes() == ["/", "/game"]
    running.page.finish_closing_dialogs()

    assert running.routes() == ["/"]
    assert running.page.dialogs == []
    running.play()
    assert "X" not in running.labels()  # Play starts a brand new match


def test_settings_button_does_not_ask_once_the_match_is_over() -> None:
    running = RunningApp(FakePage(device("en")))
    for position in (0, 3, 1, 4, 2):
        running.answer(position)
    assert tap_settings(running) is None
    assert running.routes() == ["/"]


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
    assert running.restart.content.value == "Recomeçar"
    assert running.restart.visible is True


def test_starts_in_english_on_any_other_device() -> None:
    running = RunningApp(FakePage(device("de", "DE")))
    assert running.page.title == "Math Tic-Tac-Toe"
    assert running.settings.title.value == "Settings"
    assert running.settings.hint.value == (
        "In pink: selected options. Tap an option to select or unselect it."
    )
    assert running.settings.play.content.value == "Play"
    assert running.status.value == "X's turn"
    assert running.restart.content.value == "Restart"


def test_tapping_a_cell_opens_the_question_modal() -> None:
    running = RunningApp(FakePage(device("en")))
    dialog = running.tap_cell(4)
    assert dialog.modal
    assert dialog.title.value == "Solve the question"
    answer_time, prompt, choices = dialog.content.controls
    _, seconds = answer_time.controls
    assert seconds.value == "10"  # seconds left to answer
    assert prompt.value == "question 3"
    assert [button.content.value for button in choices.controls] == ["1", "2", "3"]
    (cancel,) = dialog.actions
    assert cancel.content == "Cancel"


def test_canceling_closes_the_modal_and_changes_nothing() -> None:
    running = RunningApp(FakePage(device("en")))
    running.answer(0, choice_index=1)  # X is wrong: now it is O's turn
    labels = running.labels()

    running.cancel(4)

    assert running.page.dialogs == []
    assert running.labels() == labels  # no mark, and the cell keeps its question
    assert running.status.value == "O's turn"
    assert running.feedback_text() == "Wrong answer."  # still about the last answer

    running.answer(1)  # O can choose another cell
    assert running.labels()[1] == "O"


def test_choosing_an_answer_closes_the_modal_and_plays() -> None:
    running = RunningApp(FakePage(device("en")))
    assert running.status.color == PLAYER_COLORS[Mark.X]
    running.answer(0)
    assert running.page.dialogs == []
    assert running.labels()[0] == "X"
    assert running.cells[0].content.color == PLAYER_COLORS[Mark.X]
    # The turn message changes to the next player's color.
    assert running.status.value == "O's turn"
    assert running.status.color == PLAYER_COLORS[Mark.O]
    assert running.feedback_text() == ""  # a right answer shows no message


def test_wrong_answer_is_shown_in_red_and_passes_the_turn() -> None:
    running = RunningApp(FakePage(device("pt", "BR")))
    assert running.status.color == PLAYER_COLORS[Mark.X]
    running.answer(0, choice_index=1)  # choices are (1, 2, 3) and 1 is right
    assert running.page.dialogs == []
    assert running.feedback_colors() == [("Resposta incorreta.", ALERT_COLOR)]
    # The cell gets the other player's symbol, in their color.
    assert running.labels()[0] == "O"
    assert running.cells[0].content.color == PLAYER_COLORS[Mark.O]
    assert running.status.value == "Vez de O"
    assert running.status.color == PLAYER_COLORS[Mark.O]


def tap_restart(running: RunningApp) -> ft.AlertDialog | None:
    """Taps the restart button; returns the confirmation, if one opened."""
    open_before = len(running.page.dialogs)
    click(running.restart)
    return running.page.dialogs[-1] if len(running.page.dialogs) > open_before else None


def test_restart_in_the_middle_of_a_match_asks_for_confirmation() -> None:
    running = RunningApp(FakePage(device("pt", "BR")))
    running.answer(0)  # X
    running.answer(4, choice_index=1)  # O is wrong
    assert running.restart.content.value == "Recomeçar"

    dialog = tap_restart(running)

    assert dialog is not None
    assert dialog.modal
    assert dialog.title.value == "Recomeçar a partida?"
    assert dialog.content.value == "A partida atual será perdida."
    cancel, confirm = dialog.actions
    assert (cancel.content, confirm.content) == ("Cancelar", "Recomeçar")
    assert running.labels()[0] == "X"  # nothing changed yet


def test_confirming_restarts_the_match() -> None:
    running = RunningApp(FakePage(device("pt", "BR")))
    running.answer(0)
    running.answer(4, choice_index=1)

    dialog = tap_restart(running)
    assert dialog is not None
    _, confirm = dialog.actions
    click(confirm)
    running.page.finish_closing_dialogs()  # it acts once the dialog is gone

    assert running.page.dialogs == []
    assert running.restart.content.value == "Recomeçar"
    assert running.status.value == "Vez de X"
    assert running.feedback_text() == ""
    assert "X" not in running.labels()
    assert "O" not in running.labels()


def test_full_match_then_restart() -> None:
    running = RunningApp(FakePage(device("pt", "BR")))
    for position in (0, 3, 1, 4, 2):
        running.answer(position)

    assert running.status.value == "Fim de jogo: X venceu!"
    assert running.status.color == WINNER_MESSAGE_COLOR
    assert running.restart.content.value == "Jogar novamente"
    assert running.restart.visible is True
    gold = [i for i, cell in enumerate(running.cells) if background_of(cell) == WINNING_CELL_COLOR]
    assert gold == [0, 1, 2]
    assert all(
        cell.style.bgcolor[ft.ControlState.DISABLED] == WINNING_CELL_COLOR
        for cell in running.cells[:3]
    )

    assert tap_restart(running) is None  # the match is over: nothing to lose

    assert running.restart.content.value == "Recomeçar"
    assert running.restart.visible is True
    assert running.status.value == "Vez de X"
    assert running.feedback_text() == ""
    assert "X" not in running.labels()
    assert "O" not in running.labels()
    assert not any(cell.disabled for cell in running.cells)
    assert all(background_of(cell) != WINNING_CELL_COLOR for cell in running.cells)


def test_mobile_entry_point_runs_the_app(monkeypatch: pytest.MonkeyPatch) -> None:
    started: list[object] = []
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
    assert running.settings.hard_mode.width == layout.mode_button_width
    assert {cell.width for cell in running.cells} == {layout.cell_size}
    usable = screen.usable_height
    return (
        usable is not None
        and layout.content_height <= usable
        and settings_content_height(layout) <= usable
    )


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


# ---- hard mode ---------------------------------------------------------------


def test_hard_mode_asks_for_the_time_first() -> None:
    running = RunningApp(FakePage(device("pt", "BR")), play=False)
    click(running.settings.hard_mode)
    dialog = running.page.dialogs[-1]
    assert dialog.title.value == "Modo difícil"
    message, time_label, time_bar = dialog.content.controls
    assert message.value.startswith("Cada jogador tem este tempo")
    assert time_label.value == "Tempo por jogador"
    time, bar, _ = time_bar.controls
    assert time.value == "1:00"
    assert isinstance(bar, ft.Slider)
    cancel, start = dialog.actions
    assert (cancel.content, start.content) == ("Cancelar", "Começar")
    assert running.routes() == ["/"]  # the match only starts with "Começar"


def test_hard_mode_starts_a_timed_match(games: list[GameSettings]) -> None:
    running = RunningApp(FakePage(device("en")), play=False)
    running.settings.tap_table(7)
    running.play_hard_mode()

    assert running.routes() == ["/", "/game"]
    assert games[-1] == settings_of(OPERATIONS, [t for t in TABLES if t != 7]).with_time_limit(60)
    assert running.timers.visible is True
    assert running.timer_texts() == ["X  1:00", "O  1:00"]


def test_the_timers_run_for_the_player_whose_turn_it_is(time: FakeTime) -> None:
    running = RunningApp(FakePage(device("en")), play=False)
    running.play_hard_mode(90)
    time.advance(9)
    running.tick()
    assert running.timer_texts() == ["X  1:21", "O  1:30"]

    running.answer(0)  # X answers: O's time runs
    time.advance(9)
    running.tick()
    assert running.timer_texts() == ["X  1:21", "O  1:21"]


def test_the_player_who_runs_out_of_time_loses(time: FakeTime) -> None:
    running = RunningApp(FakePage(device("pt", "BR")), play=False)
    running.play_hard_mode()
    running.answer(0)  # X
    running.answer(3)  # O
    running.answer(1)  # X
    running.tap_cell(4)  # O opens a question... and thinks too long
    time.advance(60)

    running.tick()

    assert running.page.dialogs == []  # the question closed
    assert running.status.value == "Fim de jogo: X venceu!"
    assert running.status.color == WINNER_MESSAGE_COLOR  # the winner, in gold
    assert running.feedback_text() == "O ficou sem tempo."
    # Only the symbol keeps its player's color (pink O); the rest is red.
    assert running.feedback_colors() == [
        ("O", PLAYER_COLORS[Mark.O]),
        (" ficou sem tempo.", ALERT_COLOR),
    ]
    # Every cell of the winner turns gold; the loser's cell does not.
    gold = [i for i, cell in enumerate(running.cells) if background_of(cell) == WINNING_CELL_COLOR]
    assert gold == [0, 1]
    assert all(
        cell.style.bgcolor[ft.ControlState.DISABLED] == WINNING_CELL_COLOR
        for cell in (running.cells[0], running.cells[1])
    )
    assert running.timer_texts() == ["X  1:00", "O  0:00"]
    assert all(cell.disabled for cell in running.cells)
    assert running.restart.content.value == "Jogar novamente"


def test_leaving_the_game_stops_the_clock(time: FakeTime) -> None:
    running = RunningApp(FakePage(device("en")), play=False)
    running.play_hard_mode()
    click(running.settings_button)
    time.advance(1000)
    running.tick()
    assert running.routes() == ["/"]
    assert running.status.value == "X's turn"  # nobody lost while away


def test_play_after_hard_mode_is_a_normal_match_again(games: list[GameSettings]) -> None:
    running = RunningApp(FakePage(device("en")), play=False)
    running.play_hard_mode()
    assert running.timers.visible is True
    click(running.settings_button)
    running.play()
    assert games[-1].time_limit is None
    assert running.timers.visible is False  # normal matches have no timers


def test_hard_mode_dialog_is_gone_when_returning_to_the_settings() -> None:
    """Regression: starting hard mode switched to the game screen while its
    dialog was still closing, so the dialog came back, stuck open, on the
    settings screen."""
    running = RunningApp(FakePage(device("pt", "BR")), play=False)
    click(running.settings.hard_mode)
    _, start = running.page.dialogs[-1].actions
    click(start)
    assert running.routes() == ["/"]  # waits for the dialog to finish closing

    running.page.finish_closing_dialogs()
    assert running.routes() == ["/", "/game"]
    running.find_game_controls()
    click(running.settings_button)  # back to the settings

    assert running.routes() == ["/"]
    assert running.page.dialogs == []
    assert running.page.closing_dialogs == []  # nothing left behind

    # The button still works: a new dialog opens, and it can be closed.
    click(running.settings.hard_mode)
    assert len(running.page.dialogs) == 1
    cancel, _ = running.page.dialogs[-1].actions
    click(cancel)
    running.page.finish_closing_dialogs()
    assert running.page.dialogs == []
    assert running.routes() == ["/"]


# ---- best of 5 -------------------------------------------------------------------
# The test questions make corners last 1 second, edges 2 and the center 3.


def test_best_of_five_from_the_settings(games: list[GameSettings], time: FakeTime) -> None:
    running = RunningApp(FakePage(device("pt", "BR")), play=False)
    assert running.settings.best_of.content.value == "Melhor de 5"
    running.play_best_of()

    assert games[-1] == GameSettings(best_of=5)
    assert running.routes() == ["/", "/game"]
    assert running.timers.visible is False
    assert running.score.visible is True
    x, goal, o = running.score.controls
    assert (x.content.value, goal.value, o.content.value) == ("X  0", "Vence quem fizer 3", "O  0")

    # A played cell counts down below its mark, then is open again.
    running.answer(4)  # X in the center: 3 seconds
    assert running.cell_countdown(4) == ("X", "3")
    time.advance(1)
    running.tick()
    assert running.cell_countdown(4) == ("X", "2")

    # A line scores a point, with a message: first it turns gold...
    running.answer(0)  # O: 1 second
    running.answer(1)  # X
    running.answer(2)  # O: 1 second
    running.answer(7)  # X completes the middle column
    assert x.content.value == "X  1"
    assert running.feedback_text() == "Ponto para X!"
    assert running.status.value == "Vez de O"
    gold = [p for p, cell in enumerate(running.cells) if background_of(cell) == WINNING_CELL_COLOR]
    assert gold == [1, 4, 7]
    assert [running.labels()[p] for p in gold] == ["X", "X", "X"]
    assert all(cell.disabled for cell in running.cells)  # the board waits
    assert running.restart.content.value == "Recomeçar"

    time.advance(1)  # O's corners run out of time meanwhile
    running.tick()
    assert running.labels()[0] == "question 1"

    time.advance(1)  # ...then the gold line disappears
    running.tick()
    cleared = [running.labels()[p] for p in (1, 4, 7)]
    assert cleared == ["question 2", "question 3", "question 2"]
    assert not any(background_of(cell) == WINNING_CELL_COLOR for cell in running.cells)
    assert not any(cell.disabled for cell in running.cells)
    assert running.status.value == "Vez de O"  # the turn does not change


def test_best_of_five_is_won_at_3_points(time: FakeTime) -> None:
    running = RunningApp(FakePage(device("en")), play=False)
    running.play_best_of()
    # O's wrong answers put X's symbol on the board.
    running.answer(0)  # X
    running.answer(1, choice_index=1)  # O is wrong: X's symbol
    running.answer(2)  # X completes the top row
    assert running.score.controls[0].content.value == "X  1"
    time.advance(2)  # the line shows in gold, then disappears
    running.tick()
    running.answer(3, choice_index=1)  # O is wrong
    running.answer(4)  # X
    running.answer(5, choice_index=1)  # O is wrong and completes X's middle row
    assert running.score.controls[0].content.value == "X  2"
    assert running.feedback_text() == "Wrong answer. Point for X!"
    assert running.status.value == "X's turn"
    time.advance(2)
    running.tick()
    running.answer(6)  # X
    running.answer(7, choice_index=1)  # O is wrong
    running.answer(8)  # X completes the bottom row: the third point

    assert running.status.value == "Game over: X wins!"
    assert running.score.controls[0].content.value == "X  3"
    assert running.restart.content.value == "Play again"
    gold = [i for i, cell in enumerate(running.cells) if background_of(cell) == WINNING_CELL_COLOR]
    assert gold == [6, 7, 8]
    assert running.cells[6].content.value == "X"  # no countdown once it is over

    assert tap_restart(running) is None  # over: nothing to lose
    assert running.score.controls[0].content.value == "X  0"  # a fresh best of 5


def test_play_after_a_best_of_five_is_a_single_game_again(games: list[GameSettings]) -> None:
    running = RunningApp(FakePage(device("en")), play=False)
    running.play_best_of()
    click(running.settings_button)  # nobody answered: leaves right away
    running.play()
    assert games[-1].best_of is None
    assert running.score.visible is False


# ---- 10 seconds per turn -----------------------------------------------------------


def test_each_turn_has_10_seconds_to_choose_and_answer(time: FakeTime) -> None:
    running = RunningApp(FakePage(device("pt", "BR")))
    _, seconds = running.turn_time.controls
    assert seconds.value == "10"  # next to "Vez de X"

    time.advance(6)
    running.tick()
    assert seconds.value == "4"
    dialog = running.tap_cell(0)  # the same time goes on in the question
    turn_time, _, _ = dialog.content.controls
    assert turn_time.controls[1].value == "4"

    time.advance(4)
    running.tick()
    assert running.page.dialogs == []  # time's up: the cell goes to O
    assert running.labels()[0] == "O"
    assert running.feedback_text() == "Tempo esgotado!"
    assert running.status.value == "Vez de O"
    assert seconds.value == "10"

    time.advance(10)  # O does not even choose a cell: the turn passes
    running.tick()
    assert running.status.value == "Vez de X"
    assert running.labels().count("O") == 1


def test_only_cells_with_a_symbol_show_seconds_in_a_best_of_five(time: FakeTime) -> None:
    running = RunningApp(FakePage(device("en")), play=False)
    running.play_best_of()
    assert all(isinstance(cell.content, ft.Text) for cell in running.cells)  # no seconds yet
    running.answer(4)  # X takes it: its seconds show, in blue, and run
    _, seconds = running.cells[4].content.controls
    assert running.cell_countdown(4) == ("X", "3")
    assert seconds.color == PLAYER_COLORS[Mark.X]
    time.advance(1)
    running.tick()
    assert running.cell_countdown(4) == ("X", "2")
