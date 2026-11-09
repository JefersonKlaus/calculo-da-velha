"""Checks how the Flet screens are built, without opening a window."""

import flet as ft
import pytest

from math_tic_tac_toe.game import Mark
from math_tic_tac_toe.questions import Question
from math_tic_tac_toe.settings import DEFAULT_SETTINGS, OPERATIONS, TABLES, GameSettings, Operation
from math_tic_tac_toe.ui.board_view import BoardView
from math_tic_tac_toe.ui.game_header import GameHeader
from math_tic_tac_toe.ui.layout import (
    LINE_HEIGHT,
    MESSAGE_SPACING,
    PAGE_PADDING,
    SECTION_SPACING,
    layout_for_width,
)
from math_tic_tac_toe.ui.navigator import ScreenNavigator
from math_tic_tac_toe.ui.presenter import CellState, FeedbackMessage, StatusMessage
from math_tic_tac_toe.ui.question_dialog import QuestionDialog, build_question_dialog
from math_tic_tac_toe.ui.restart_button import RestartButton
from math_tic_tac_toe.ui.screens import GAME_ROUTE, SETTINGS_ROUTE, screen
from math_tic_tac_toe.ui.settings_view import SettingsLabels, SettingsView
from math_tic_tac_toe.ui.status_view import StatusView
from math_tic_tac_toe.ui.styles import (
    CORRECT_ANSWER_COLOR,
    PLAYER_COLORS,
    UNSELECTED_OPTION_COLOR,
    WINNING_CELL_COLOR,
    WINNING_MARK_COLOR,
    WRONG_ANSWER_COLOR,
)
from math_tic_tac_toe.ui.title_view import TitleView
from support import FakePage, phone_layout


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
    board.cells[7].on_click(None)
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
    question = Question("6 × 7", 42, (40, 42, 44), "multiplication", 1)
    chosen: list[int] = []
    dialog = build_question_dialog(question, "Solve the question", chosen.append)

    assert dialog.modal
    assert dialog.title.value == "Solve the question"
    prompt, choices_row = dialog.content.controls
    assert prompt.value == "6 × 7"
    buttons = choices_row.controls
    assert [button.content.value for button in buttons] == ["40", "42", "44"]
    for button in buttons:
        assert_square(button)

    buttons[1].on_click(None)
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
    question = Question("6 × 7", 42, (40, 42, 44), "multiplication", 1)

    QuestionDialog(page, "Solve the question").ask(question, answers.append)  # type: ignore[arg-type]

    (dialog,) = page.dialogs
    assert dialog.title.value == "Solve the question"
    _, choices_row = dialog.content.controls
    choices_row.controls[2].on_click(None)
    assert page.dialogs == []
    assert answers == [44]


def test_status_view_shows_status_and_feedback() -> None:
    view = StatusView(phone_layout())
    view.show_status(StatusMessage("X's turn", Mark.X))
    view.show_feedback(FeedbackMessage("Correct answer.", correct=True))
    status, feedback = view.control.controls
    assert status.value == "X's turn"
    assert feedback.value == "Correct answer."


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


def test_feedback_is_bold_green_when_right_and_red_when_wrong() -> None:
    view = StatusView(phone_layout())
    _, feedback = view.control.controls
    assert feedback.weight == ft.FontWeight.BOLD
    assert feedback.size == phone_layout().feedback_font_size
    assert feedback.size > 14  # bigger than Flet's default text

    view.show_feedback(FeedbackMessage("Wrong answer.", correct=False))
    assert (feedback.value, feedback.color) == ("Wrong answer.", WRONG_ANSWER_COLOR)
    view.show_feedback(FeedbackMessage("Correct answer.", correct=True))
    assert (feedback.value, feedback.color) == ("Correct answer.", CORRECT_ANSWER_COLOR)

    view.show_feedback(None)
    assert (feedback.value, feedback.color) == ("", None)


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


def test_restart_button_is_hidden_until_shown_and_reports_taps() -> None:
    taps: list[None] = []
    button = RestartButton("Restart", on_restart=lambda: taps.append(None), layout=phone_layout())
    assert button.control.visible is False
    assert button.control.content.value == "Restart"
    assert button.control.style.shape.radius == 0

    button.set_visible(True)
    assert button.control.visible is True
    button.control.on_click(None)
    assert taps == [None]

    button.set_visible(False)
    assert button.control.visible is False


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
    button = RestartButton("Restart", on_restart=lambda: None, layout=phone_layout())
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
) -> tuple[SettingsView, list[GameSettings], list[None]]:
    played: list[GameSettings] = []
    refreshes: list[None] = []
    view = SettingsView(
        SettingsLabels("Settings", "Operation", "Times table", "Play"),
        settings,
        on_play=played.append,
        refresh=lambda: refreshes.append(None),
        layout=phone_layout(),
    )
    return view, played, refreshes


def selected_options(buttons: dict) -> list:
    return [key for key, button in buttons.items() if button.style.bgcolor is None]


def test_settings_view_starts_with_everything_selected() -> None:
    view, _, _ = make_settings_view()
    assert selected_options(view.operation_buttons) == list(OPERATIONS)
    assert selected_options(view.table_buttons) == list(TABLES)
    assert view.table_section.visible is True
    assert view.operation_label.value == "Operation"
    assert view.table_label.value == "Times table"


def test_settings_view_shows_the_current_choice() -> None:
    chosen = GameSettings.of([Operation.ADDITION, Operation.DIVISION], [5, 7])
    view, _, _ = make_settings_view(chosen)
    assert selected_options(view.operation_buttons) == [Operation.ADDITION, Operation.DIVISION]
    assert selected_options(view.table_buttons) == [5, 7]
    unselected = view.operation_buttons[Operation.SUBTRACTION].style
    assert unselected.bgcolor == UNSELECTED_OPTION_COLOR


def test_tapping_a_selected_option_unselects_only_that_one() -> None:
    view, _, refreshes = make_settings_view()  # everything selected
    view.table_buttons[5].on_click(None)
    view.operation_buttons[Operation.ADDITION].on_click(None)
    assert selected_options(view.table_buttons) == [t for t in TABLES if t != 5]
    assert selected_options(view.operation_buttons) == [
        Operation.SUBTRACTION,
        Operation.MULTIPLICATION,
        Operation.DIVISION,
    ]
    assert len(refreshes) == 2


def test_tapping_an_unselected_option_selects_it_again() -> None:
    view, _, _ = make_settings_view()
    view.table_buttons[5].on_click(None)
    view.table_buttons[5].on_click(None)
    assert view.settings == DEFAULT_SETTINGS


def test_the_last_selected_option_stays_selected() -> None:
    view, _, _ = make_settings_view(GameSettings.of([Operation.DIVISION], [7]))
    view.table_buttons[7].on_click(None)
    view.operation_buttons[Operation.DIVISION].on_click(None)
    assert view.settings == GameSettings.of([Operation.DIVISION], [7])


@pytest.mark.parametrize(
    ("operations", "visible"),
    [
        ([Operation.ADDITION], False),
        ([Operation.ADDITION, Operation.SUBTRACTION], False),
        ([Operation.MULTIPLICATION], True),
        ([Operation.ADDITION, Operation.DIVISION], True),
        (list(OPERATIONS), True),
    ],
)
def test_times_tables_only_show_when_multiplication_or_division_is_chosen(
    operations: list[Operation], visible: bool
) -> None:
    view, _, _ = make_settings_view(GameSettings.of(operations))
    assert view.table_section.visible is visible


def test_play_hands_over_the_chosen_settings() -> None:
    view, played, _ = make_settings_view()
    view.table_buttons[7].on_click(None)
    view.play_button.on_click(None)
    assert played == [GameSettings.of(OPERATIONS, [t for t in TABLES if t != 7])]


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
    for label in (view.operation_label, view.table_label):
        assert label.size == tablet.status_font_size
        assert label.style.height == LINE_HEIGHT
        assert label.max_lines == 1
    assert view.play_button.width == tablet.board_width
    assert view.play_button.height == tablet.restart_height


def test_game_header_has_a_settings_button_and_keeps_the_title_centered() -> None:
    opened: list[None] = []
    header = GameHeader(
        "Math Tic-Tac-Toe", "Settings", lambda: opened.append(None), phone_layout()
    )
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

    button.on_click(None)
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
    navigator = ScreenNavigator(
        page, settings_screen, game_screen, refresh=lambda: refreshes.append(None)  # type: ignore[arg-type]
    )

    navigator.show_settings()
    assert page.views == [settings_screen]
    navigator.show_game()
    assert page.views == [settings_screen, game_screen]
    page.press_back()
    assert page.views == [settings_screen]
    assert len(refreshes) == 3


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
