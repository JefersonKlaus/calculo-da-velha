"""Checks how the Flet screens are built, without opening a window."""

from collections.abc import Callable, Mapping
from typing import TypeVar

import flet as ft
import pytest

from math_tic_tac_toe.game import Mark
from math_tic_tac_toe.questions import Question
from math_tic_tac_toe.settings import DEFAULT_SETTINGS, OPERATIONS, TABLES, GameSettings, Operation
from math_tic_tac_toe.ui.board_view import BoardView
from math_tic_tac_toe.ui.confirm_dialog import ConfirmDialog, ConfirmLabels, build_confirm_dialog
from math_tic_tac_toe.ui.game_header import GameHeader
from math_tic_tac_toe.ui.hard_mode_dialog import HardModeDialog, HardModeLabels
from math_tic_tac_toe.ui.layout import (
    LINE_HEIGHT,
    MESSAGE_SPACING,
    PAGE_PADDING,
    SECTION_SPACING,
    SETTINGS_HINT_MAX_LINES,
    TIMER_VERTICAL_PADDING,
)
from math_tic_tac_toe.ui.navigator import ScreenNavigator
from math_tic_tac_toe.ui.presenter import (
    CellState,
    FeedbackMessage,
    MessagePart,
    StatusMessage,
    TimerState,
)
from math_tic_tac_toe.ui.question_dialog import QuestionDialog, build_question_dialog
from math_tic_tac_toe.ui.restart_button import RestartButton
from math_tic_tac_toe.ui.screens import GAME_ROUTE, SETTINGS_ROUTE, screen
from math_tic_tac_toe.ui.settings_view import SettingsLabels, SettingsView
from math_tic_tac_toe.ui.status_view import StatusView
from math_tic_tac_toe.ui.styles import (
    ALERT_COLOR,
    HARD_MODE_COLOR,
    HINT_COLOR,
    LOW_TIME_COLOR,
    PLAYER_COLORS,
    RUNNING_TIMER_COLORS,
    UNSELECTED_OPTION_COLOR,
    WINNING_CELL_COLOR,
    WINNING_MARK_COLOR,
)
from math_tic_tac_toe.ui.timers_view import TimersView
from math_tic_tac_toe.ui.title_view import TitleView
from tests.support import FakePage, click, layout_for_width, phone_layout, settings_of, slide

Option = TypeVar("Option")


def assert_square(button: ft.FilledButton) -> None:
    assert button.width == button.height
    assert button.style.shape.radius == 0


def test_board_is_a_3x3_grid_of_square_buttons() -> None:
    board = BoardView(on_select=lambda _: None, layout=phone_layout())
    rows = board.control.controls
    assert len(rows) == 3
    assert all(len(row.controls) == 3 for row in rows)
    for button in board.cells:
        assert_square(button)


def test_board_reports_the_clicked_position() -> None:
    selected: list[int] = []
    board = BoardView(on_select=selected.append, layout=phone_layout())
    click(board.cells[7])
    assert selected == [7]


def test_board_render_updates_labels_and_disables_taken_cells() -> None:
    board = BoardView(on_select=lambda _: None, layout=phone_layout())
    states = [CellState(f"c{i}", True) for i in range(9)]
    states[2] = CellState("O", False, Mark.O)
    board.render(states)
    assert board.cells[0].content.value == "c0"
    assert board.cells[2].content.value == "O"
    assert board.cells[2].disabled
    assert not board.cells[0].disabled


def test_dialog_is_modal_with_one_square_button_per_choice() -> None:
    question = Question("6 × 7", 42, (40, 42, 44), Operation.MULTIPLICATION, 1)
    chosen: list[int] = []
    dialog = build_question_dialog(
        question, "Solve the question", chosen.append, "Cancel", lambda: None
    )

    assert dialog.modal
    assert dialog.title.value == "Solve the question"
    prompt, choices_row = dialog.content.controls
    assert prompt.value == "6 × 7"
    buttons = choices_row.controls
    assert [button.content.value for button in buttons] == ["40", "42", "44"]
    for button in buttons:
        assert_square(button)

    click(buttons[1])
    assert chosen == [42]


def test_board_paints_the_winning_line_gold_even_when_disabled() -> None:
    board = BoardView(on_select=lambda _: None, layout=phone_layout())
    states = [CellState("X", False, Mark.X, highlighted=i in (2, 4, 6)) for i in range(9)]
    board.render(states)

    for position in (2, 4, 6):
        style = board.cells[position].style
        assert style.bgcolor[ft.ControlState.DISABLED] == WINNING_CELL_COLOR
        assert style.bgcolor[ft.ControlState.DEFAULT] == WINNING_CELL_COLOR
        assert style.color[ft.ControlState.DISABLED] == WINNING_MARK_COLOR
        assert_square(board.cells[position])
    for position in (0, 1, 3, 5, 7, 8):
        assert board.cells[position].style.bgcolor is None
        assert_square(board.cells[position])


def test_question_dialog_opens_and_closes_on_the_page() -> None:
    page = FakePage()
    answers: list[int] = []
    question = Question("6 × 7", 42, (40, 42, 44), Operation.MULTIPLICATION, 1)

    QuestionDialog(page.as_page(), "Solve the question", "Cancel").ask(question, answers.append)

    (dialog,) = page.dialogs
    assert dialog.title.value == "Solve the question"
    _, choices_row = dialog.content.controls
    click(choices_row.controls[2])
    assert page.dialogs == []
    assert answers == [44]


def test_question_dialog_closes_without_answering_when_canceled() -> None:
    page = FakePage()
    answers: list[int] = []
    question = Question("6 × 7", 42, (40, 42, 44), Operation.MULTIPLICATION, 1)

    QuestionDialog(page.as_page(), "Solve the question", "Cancel").ask(question, answers.append)

    (dialog,) = page.dialogs
    (cancel,) = dialog.actions
    click(cancel)
    assert page.dialogs == []
    assert answers == []


def test_question_dialog_can_be_closed_by_the_game() -> None:
    page = FakePage()
    answers: list[int] = []
    question = Question("6 × 7", 42, (40, 42, 44), Operation.MULTIPLICATION, 1)
    prompt = QuestionDialog(page.as_page(), "Solve the question", "Cancel")
    other = ft.AlertDialog()

    prompt.ask(question, answers.append)
    prompt.close()
    assert page.dialogs == []

    page.show_dialog(other)
    prompt.close()  # already closed: leaves other dialogs alone
    assert page.dialogs == [other]
    assert answers == []


CONFIRM_LABELS = ConfirmLabels(
    "Restart the match?", "The current match will be lost.", "Cancel", "Restart"
)


def test_confirm_dialog_is_modal_with_cancel_and_a_filled_confirm_button() -> None:
    calls: list[str] = []
    dialog = build_confirm_dialog(
        CONFIRM_LABELS, lambda: calls.append("cancel"), lambda: calls.append("confirm")
    )

    assert dialog.modal
    assert dialog.title.value == "Restart the match?"
    assert dialog.content.value == "The current match will be lost."
    cancel, confirm = dialog.actions
    assert (cancel.content, confirm.content) == ("Cancel", "Restart")
    assert isinstance(cancel, ft.TextButton)
    assert isinstance(confirm, ft.FilledButton)

    click(cancel)
    click(confirm)
    assert calls == ["cancel", "confirm"]


def test_confirm_dialog_cancel_only_closes_it() -> None:
    page = FakePage()
    confirmed: list[None] = []
    ConfirmDialog(page.as_page(), CONFIRM_LABELS).confirm(lambda: confirmed.append(None))

    (dialog,) = page.dialogs
    cancel, _ = dialog.actions
    click(cancel)
    assert page.dialogs == []
    assert confirmed == []


def test_confirm_dialog_confirm_closes_it_and_confirms() -> None:
    page = FakePage()
    confirmed: list[int] = []
    # Records how many dialogs were open when the confirmation ran.
    ConfirmDialog(page.as_page(), CONFIRM_LABELS).confirm(
        lambda: confirmed.append(len(page.dialogs))
    )

    (dialog,) = page.dialogs
    _, confirm = dialog.actions
    click(confirm)
    assert page.dialogs == []
    assert confirmed == [0]  # closed first, then confirmed


def test_status_is_bold_in_the_color_of_the_player() -> None:
    view = StatusView(phone_layout())
    status, _ = view.control.controls
    assert status.weight == ft.FontWeight.BOLD

    view.show_status(StatusMessage("X's turn", Mark.X))
    assert status.color == PLAYER_COLORS[Mark.X]
    view.show_status(StatusMessage("O's turn", Mark.O))
    assert status.color == PLAYER_COLORS[Mark.O]
    view.show_status(StatusMessage("Game over: it's a draw!", None))
    assert status.color is None


def test_feedback_is_bold_and_red() -> None:
    view = StatusView(phone_layout())
    _, feedback = view.control.controls
    assert feedback.weight == ft.FontWeight.BOLD
    assert feedback.size == phone_layout().feedback_font_size
    assert feedback.size > 14  # bigger than Flet's default text

    view.show_feedback(FeedbackMessage((MessagePart("Wrong answer."),)))
    assert colored_spans(feedback) == [("Wrong answer.", ALERT_COLOR)]

    view.show_feedback(None)
    assert feedback.spans == []
    assert not feedback.value


@pytest.mark.parametrize("player", list(Mark))
def test_feedback_shows_a_player_symbol_in_that_player_color(player: Mark) -> None:
    view = StatusView(phone_layout())
    _, feedback = view.control.controls
    message = FeedbackMessage((MessagePart(player.value, player), MessagePart(" ran out of time.")))

    view.show_feedback(message)

    assert colored_spans(feedback) == [
        (player.value, PLAYER_COLORS[player]),  # X blue / O purple
        (" ran out of time.", ALERT_COLOR),  # the rest stays red
    ]
    # The pieces share the line's look: same size, weight and line height.
    assert all(span.style.size is None for span in feedback.spans)
    assert feedback.weight == ft.FontWeight.BOLD


def colored_spans(text: ft.Control) -> list[tuple[str | None, object]]:
    return [(span.text, span.style.color) for span in text.spans or []]


def test_players_are_blue_and_purple() -> None:
    assert PLAYER_COLORS == {Mark.X: "#1565C0", Mark.O: "#6A1B9A"}


def test_marks_use_the_player_color_and_dark_gold_when_winning() -> None:
    board = BoardView(on_select=lambda _: None, layout=phone_layout())
    states = [CellState(f"c{i}", True) for i in range(9)]
    states[0] = CellState("X", False, Mark.X)
    states[1] = CellState("O", False, Mark.O)
    states[2] = CellState("X", False, Mark.X, highlighted=True)
    board.render(states)

    assert board.cells[0].content.color == PLAYER_COLORS[Mark.X]
    assert board.cells[1].content.color == PLAYER_COLORS[Mark.O]
    assert board.cells[2].content.color == WINNING_MARK_COLOR
    assert board.cells[3].content.color is None  # questions keep the default look
    assert board.cells[0].content.weight == ft.FontWeight.BOLD


def test_restart_button_is_always_visible_shows_its_label_and_reports_taps() -> None:
    taps: list[None] = []
    button = RestartButton(on_restart=lambda: taps.append(None), layout=phone_layout())
    assert button.control.visible is True
    assert button.control.style.shape.radius == 0

    button.set_label("Restart")
    assert button.control.content.value == "Restart"
    click(button.control)
    assert taps == [None]

    button.set_label("Play again")
    assert button.control.content.value == "Play again"
    assert button.control.visible is True


def test_board_cells_use_the_layout_size() -> None:
    layout = phone_layout()
    board = BoardView(on_select=lambda _: None, layout=layout)
    assert {(cell.width, cell.height) for cell in board.cells} == {(layout.cell_size,) * 2}
    assert board.control.spacing == layout.cell_spacing
    assert {row.spacing for row in board.control.controls} == {layout.cell_spacing}


def test_board_grows_and_keeps_its_labels_when_the_layout_changes() -> None:
    board = BoardView(on_select=lambda _: None, layout=phone_layout())
    states = [CellState(f"c{i}", True) for i in range(9)]
    states[0] = CellState("X", False, Mark.X)
    board.render(states)

    tablet = layout_for_width(800)
    board.apply_layout(tablet)

    assert board.cells[4].width == board.cells[4].height == tablet.cell_size
    assert board.cells[0].content.value == "X"
    assert board.cells[0].content.size == tablet.mark_font_size
    assert board.cells[0].content.color == PLAYER_COLORS[Mark.X]
    assert board.cells[4].content.value == "c4"
    assert board.cells[4].content.size == tablet.prompt_font_size


def test_restart_button_is_as_wide_as_the_board() -> None:
    button = RestartButton(on_restart=lambda: None, layout=phone_layout())
    assert button.control.width == phone_layout().board_width
    assert button.control.height == phone_layout().restart_height

    tablet = layout_for_width(800)
    button.apply_layout(tablet)
    assert button.control.width == tablet.board_width
    assert button.control.height == tablet.restart_height
    assert button.control.content.size == tablet.restart_font_size


def test_title_and_messages_grow_with_the_layout() -> None:
    title = TitleView("Math Tic-Tac-Toe", phone_layout())
    status = StatusView(phone_layout())
    status_text, feedback_text = status.control.controls
    assert title.control.value == "Math Tic-Tac-Toe"
    assert title.control.weight == ft.FontWeight.BOLD
    assert title.control.size == phone_layout().title_font_size

    tablet = layout_for_width(800)
    title.apply_layout(tablet)
    status.apply_layout(tablet)
    assert title.control.size == tablet.title_font_size
    assert status_text.size == tablet.status_font_size
    assert feedback_text.size == tablet.feedback_font_size


def test_texts_use_the_fixed_line_height_the_layout_relies_on() -> None:
    title = TitleView("Math Tic-Tac-Toe", phone_layout())
    status = StatusView(phone_layout())
    assert status.control.spacing == MESSAGE_SPACING
    for text in (title.control, *status.control.controls):
        assert text.style.height == LINE_HEIGHT


def make_settings_view(
    settings: GameSettings = DEFAULT_SETTINGS,
    on_hard_mode: Callable[[GameSettings], None] = lambda _: None,
) -> tuple[SettingsView, list[GameSettings], list[None]]:
    played: list[GameSettings] = []
    refreshes: list[None] = []
    view = SettingsView(
        SettingsLabels(
            "Settings",
            "In blue: selected options. Tap an option to select or unselect it.",
            "Operation",
            "Times table",
            "Play",
            "Hard mode",
        ),
        settings,
        on_play=played.append,
        on_hard_mode=on_hard_mode,
        refresh=lambda: refreshes.append(None),
        layout=phone_layout(),
    )
    return view, played, refreshes


def selected_options(buttons: Mapping[Option, ft.FilledButton]) -> list[Option]:
    return [key for key, button in buttons.items() if button.style.bgcolor is None]


def test_settings_view_starts_with_everything_selected() -> None:
    view, _, _ = make_settings_view()
    assert selected_options(view.operation_buttons) == list(OPERATIONS)
    assert selected_options(view.table_buttons) == list(TABLES)
    assert view.table_section.visible is True
    assert view.operation_label.value == "Operation"
    assert view.table_label.value == "Times table"


def test_settings_view_explains_the_blue_options_below_the_title() -> None:
    view, _, _ = make_settings_view()
    title, hint, operation_label, *_ = view.control.controls
    assert title.value == "Settings"
    assert hint is view.hint
    assert hint.value == "In blue: selected options. Tap an option to select or unselect it."
    assert operation_label is view.operation_label
    # Small, soft and centered: it explains, it does not compete with the labels.
    assert hint.color == HINT_COLOR
    assert hint.text_align == ft.TextAlign.CENTER
    assert hint.size == phone_layout().settings_hint_font_size
    assert hint.size < view.operation_label.size
    assert hint.weight is None


def test_settings_view_shows_the_current_choice() -> None:
    chosen = settings_of([Operation.ADDITION, Operation.DIVISION], [5, 7])
    view, _, _ = make_settings_view(chosen)
    assert selected_options(view.operation_buttons) == [Operation.ADDITION, Operation.DIVISION]
    assert selected_options(view.table_buttons) == [5, 7]
    unselected = view.operation_buttons[Operation.SUBTRACTION].style
    assert unselected.bgcolor == UNSELECTED_OPTION_COLOR


def test_tapping_a_selected_option_unselects_only_that_one() -> None:
    view, _, refreshes = make_settings_view()  # everything selected
    click(view.table_buttons[5])
    click(view.operation_buttons[Operation.ADDITION])
    assert selected_options(view.table_buttons) == [t for t in TABLES if t != 5]
    assert selected_options(view.operation_buttons) == [
        Operation.SUBTRACTION,
        Operation.MULTIPLICATION,
        Operation.DIVISION,
    ]
    assert len(refreshes) == 2


def test_tapping_an_unselected_option_selects_it_again() -> None:
    view, _, _ = make_settings_view()
    click(view.table_buttons[5])
    click(view.table_buttons[5])
    assert view.settings == DEFAULT_SETTINGS


def test_the_last_selected_option_stays_selected() -> None:
    view, _, _ = make_settings_view(settings_of([Operation.DIVISION], [7]))
    click(view.table_buttons[7])
    click(view.operation_buttons[Operation.DIVISION])
    assert view.settings == settings_of([Operation.DIVISION], [7])


@pytest.mark.parametrize(
    ("operations", "visible"),
    [
        ([Operation.ADDITION, Operation.SUBTRACTION], False),
        ([Operation.ADDITION, Operation.DIVISION], True),
    ],
)
def test_times_tables_only_show_when_multiplication_or_division_is_chosen(
    operations: list[Operation], visible: bool
) -> None:
    view, _, _ = make_settings_view(settings_of(operations))
    assert view.table_section.visible is visible


def test_play_hands_over_the_chosen_settings() -> None:
    view, played, _ = make_settings_view()
    click(view.table_buttons[7])
    click(view.play_button)
    assert played == [settings_of(OPERATIONS, [t for t in TABLES if t != 7])]


def test_settings_buttons_are_square_and_follow_the_layout() -> None:
    view, _, _ = make_settings_view()
    tablet = layout_for_width(800)
    view.apply_layout(tablet)
    for button in view.operation_buttons.values():
        assert_square(button)
        assert button.width == tablet.operation_button_size
        assert button.content.size == tablet.operation_font_size
    for button in view.table_buttons.values():
        assert_square(button)
        assert button.width == tablet.table_button_size
    assert view.hint.size == tablet.settings_hint_font_size
    assert view.hint.width == tablet.board_width
    assert view.hint.style.height == LINE_HEIGHT
    assert view.hint.max_lines == SETTINGS_HINT_MAX_LINES
    for label in (view.operation_label, view.table_label):
        assert label.size == tablet.status_font_size
        assert label.style.height == LINE_HEIGHT
        assert label.max_lines == 1
    for button in (view.play_button, view.hard_mode_button):
        assert button.width == tablet.board_width
        assert button.height == tablet.restart_height
        assert button.content.size == tablet.restart_font_size


def test_game_header_has_a_settings_button_and_keeps_the_title_centered() -> None:
    opened: list[None] = []
    header = GameHeader("Math Tic-Tac-Toe", "Settings", lambda: opened.append(None), phone_layout())
    balance, title, button = header.control.controls
    assert title.value == "Math Tic-Tac-Toe"
    assert button.icon == ft.Icons.SETTINGS
    assert button.tooltip == "Settings"
    size = phone_layout().header_height
    assert (button.width, button.height) == (size, size)
    assert (balance.width, balance.height) == (size, size)

    assert header.control.width == phone_layout().board_width
    assert title.expand is True
    assert (title.max_lines, title.overflow) == (1, ft.TextOverflow.ELLIPSIS)

    click(button)
    assert opened == [None]

    tablet = layout_for_width(800)
    header.apply_layout(tablet)
    assert header.control.width == tablet.board_width
    assert button.width == tablet.header_height
    assert title.size == tablet.title_font_size


def test_navigator_stacks_the_game_on_top_of_the_settings() -> None:
    page = FakePage()
    refreshes: list[None] = []
    settings_screen, game_screen = screen(SETTINGS_ROUTE), screen(GAME_ROUTE)
    left: list[None] = []
    navigator = ScreenNavigator(
        page.as_page(),
        settings_screen,
        game_screen,
        refresh=lambda: refreshes.append(None),
        on_leave_game=lambda: left.append(None),
    )

    navigator.show_settings()
    assert page.views == [settings_screen]
    navigator.show_game()
    assert page.views == [settings_screen, game_screen]
    page.press_back()
    assert page.views == [settings_screen]
    assert len(refreshes) == 3
    assert len(left) == 2  # each time the settings are shown


def test_screens_share_the_same_frame() -> None:
    content = ft.Text("content")
    view = screen(GAME_ROUTE, content)
    assert view.route == GAME_ROUTE
    assert view.padding == PAGE_PADDING
    assert view.scroll == ft.ScrollMode.AUTO
    (safe_area,) = view.controls
    assert isinstance(safe_area, ft.SafeArea)
    assert safe_area.content.controls == [content]
    assert safe_area.content.spacing == SECTION_SPACING


# ---- hard mode ---------------------------------------------------------------


def test_settings_view_has_a_red_hard_mode_button_below_play() -> None:
    chosen: list[GameSettings] = []
    view, played, _ = make_settings_view(on_hard_mode=chosen.append)
    *_, play, hard_mode = view.control.controls
    assert play is view.play_button
    assert hard_mode is view.hard_mode_button
    assert hard_mode.content.value == "Hard mode"
    assert hard_mode.icon == ft.Icons.TIMER
    assert hard_mode.style.bgcolor == HARD_MODE_COLOR
    assert hard_mode.style.shape.radius == 0  # square corners, like Play

    click(view.table_buttons[7])
    click(hard_mode)
    assert chosen == [settings_of(OPERATIONS, [t for t in TABLES if t != 7])]
    assert played == []


HARD_MODE_LABELS = HardModeLabels(
    title="Hard mode",
    message="Each player has this time for the whole match.",
    time_per_player="Time per player",
    cancel="Cancel",
    start="Start",
)


class HardModeHarness:
    def __init__(self) -> None:
        self.page = FakePage()
        self.started: list[int] = []
        self.refreshes: list[None] = []
        HardModeDialog(
            self.page.as_page(), HARD_MODE_LABELS, refresh=lambda: self.refreshes.append(None)
        ).ask(self.started.append)
        (self.dialog,) = self.page.dialogs
        self.message, self.time_label, time_bar = self.dialog.content.controls
        self.time, self.bar, limits = time_bar.controls
        self.minimum, self.maximum = limits.controls
        self.cancel, self.start = self.dialog.actions


def test_hard_mode_dialog_offers_one_minute_by_default() -> None:
    harness = HardModeHarness()
    assert harness.dialog.modal
    assert harness.dialog.title.value == "Hard mode"
    assert harness.message.value == "Each player has this time for the whole match."
    assert harness.time_label.value == "Time per player"
    assert harness.time.value == "1:00"
    assert harness.bar.value == 60
    assert (harness.cancel.content, harness.start.content) == ("Cancel", "Start")
    assert harness.start.style.bgcolor == HARD_MODE_COLOR


def test_hard_mode_starts_only_once_the_dialog_has_finished_closing() -> None:
    harness = HardModeHarness()
    click(harness.start)
    assert harness.page.closing_dialogs == [harness.dialog]
    assert harness.started == []  # switching screens now would leave it behind
    harness.page.finish_closing_dialogs()
    assert harness.started == [60]
    assert harness.page.closing_dialogs == []


def test_a_double_tap_on_start_starts_one_match() -> None:
    harness = HardModeHarness()
    other = ft.AlertDialog()
    click(harness.start)
    harness.page.show_dialog(other)  # anything else on screen stays open
    click(harness.start)
    harness.page.finish_closing_dialogs()
    assert harness.started == [60]
    assert harness.page.dialogs == [other]


def test_hard_mode_time_is_a_bar_from_5_seconds_to_5_minutes() -> None:
    harness = HardModeHarness()
    assert isinstance(harness.bar, ft.Slider)
    assert (harness.bar.min, harness.bar.max) == (5, 300)
    assert harness.bar.divisions == 59  # a stop every 5 seconds
    assert harness.bar.active_color == HARD_MODE_COLOR
    assert (harness.minimum.value, harness.maximum.value) == ("0:05", "5:00")


def test_moving_the_bar_shows_and_starts_with_the_chosen_time() -> None:
    harness = HardModeHarness()
    slide(harness.bar, 90)
    assert harness.time.value == "1:30"
    slide(harness.bar, 300)
    assert harness.time.value == "5:00"
    slide(harness.bar, 5)
    assert harness.time.value == "0:05"
    slide(harness.bar, 132.2)  # between two stops: the nearest one
    assert harness.time.value == "2:10"
    assert len(harness.refreshes) == 4  # the screen is redrawn on each move

    click(harness.start)
    harness.page.finish_closing_dialogs()
    assert harness.started == [130]
    assert harness.page.dialogs == []


def test_the_bar_fits_a_small_phone_dialog() -> None:
    harness = HardModeHarness()
    assert harness.bar.width is not None
    assert harness.bar.width <= 360 - 2 * 24 - 2 * 24  # screen - inset - padding


def test_hard_mode_dialog_cancel_only_closes_it() -> None:
    harness = HardModeHarness()
    click(harness.cancel)
    harness.page.finish_closing_dialogs()
    assert harness.page.dialogs == []
    assert harness.started == []


def running(player: Mark, time: str, *, low: bool = False) -> TimerState:
    return TimerState(player, time, running=True, low=low)


def waiting(player: Mark, time: str, *, low: bool = False) -> TimerState:
    return TimerState(player, time, running=False, low=low)


def test_timers_are_hidden_outside_hard_mode() -> None:
    view = TimersView(phone_layout())
    assert view.control.visible is False
    view.show_timers([running(Mark.X, "1:00"), waiting(Mark.O, "1:00")])
    assert view.control.visible is True
    view.show_timers([])
    assert view.control.visible is False


def test_timers_show_each_player_in_their_color_and_highlight_the_running_one() -> None:
    view = TimersView(phone_layout())
    view.show_timers([waiting(Mark.X, "0:42"), running(Mark.O, "0:57")])
    x, o = view.timers[Mark.X], view.timers[Mark.O]
    assert x.content.value == "X  0:42"
    assert o.content.value == "O  0:57"
    assert x.content.color == PLAYER_COLORS[Mark.X]
    assert o.content.color == PLAYER_COLORS[Mark.O]
    assert x.bgcolor is None
    assert o.bgcolor == RUNNING_TIMER_COLORS[Mark.O]


def test_a_timer_turns_red_in_its_last_seconds() -> None:
    view = TimersView(phone_layout())
    view.show_timers([running(Mark.X, "0:09", low=True), waiting(Mark.O, "1:00")])
    assert view.timers[Mark.X].content.color == LOW_TIME_COLOR
    assert view.timers[Mark.O].content.color == PLAYER_COLORS[Mark.O]


def test_timers_follow_the_layout() -> None:
    view = TimersView(phone_layout())
    tablet = layout_for_width(800)
    view.apply_layout(tablet)
    for timer in view.timers.values():
        assert timer.content.size == tablet.status_font_size
        assert timer.content.style.height == LINE_HEIGHT
        assert timer.padding.top == timer.padding.bottom == TIMER_VERTICAL_PADDING
    assert view.control.spacing == tablet.cell_spacing
