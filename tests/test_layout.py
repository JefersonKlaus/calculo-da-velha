import pytest

from math_tic_tac_toe.ui.layout import (
    CELL_SPACING,
    DEFAULT_SCREEN_WIDTH,
    MESSAGE_SPACING,
    MIN_CELL_SIZE,
    MIN_TOUCH_TARGET,
    OPERATIONS_PER_ROW,
    PAGE_PADDING,
    SECTION_SPACING,
    TABLES_PER_ROW,
    ScreenSize,
    layout_for_cell,
    layout_for_screen,
    layout_for_width,
    text_height,
)


@pytest.mark.parametrize("width", [320, 360, 393, 412, 430, 600, 800, 1024])
def test_board_fills_the_screen_width(width: int) -> None:
    layout = layout_for_width(width)
    available = width - 2 * PAGE_PADDING
    assert layout.board_width <= available
    # Whole pixels per cell: at most 2 dp are left over, split by the centering.
    assert available - layout.board_width < 3


def test_small_phone_sizes() -> None:
    layout = layout_for_width(360)
    assert layout.cell_size == 109
    assert layout.cell_spacing == CELL_SPACING
    assert (layout.prompt_font_size, layout.mark_font_size) == (20, 59)
    assert (layout.restart_height, layout.restart_font_size) == (59, 21)
    assert (layout.title_font_size, layout.status_font_size) == (28, 22)
    assert layout.feedback_font_size == 18


def test_everything_grows_with_the_screen() -> None:
    phone, tablet = layout_for_width(360), layout_for_width(800)
    assert tablet.cell_size > phone.cell_size
    assert tablet.prompt_font_size > phone.prompt_font_size
    assert tablet.mark_font_size > phone.mark_font_size
    assert tablet.restart_height > phone.restart_height
    assert tablet.restart_font_size > phone.restart_font_size
    assert tablet.title_font_size > phone.title_font_size
    assert tablet.status_font_size > phone.status_font_size
    assert tablet.feedback_font_size > phone.feedback_font_size


@pytest.mark.parametrize("width", [None, 0, -10])
def test_unknown_width_falls_back_to_a_small_phone(width: float | None) -> None:
    assert layout_for_width(width) == layout_for_width(DEFAULT_SCREEN_WIDTH)


def test_tiny_screens_keep_a_minimum_cell_size() -> None:
    assert layout_for_width(100).cell_size == MIN_CELL_SIZE


# (width, height, top inset, bottom inset) of real screens, in dp.
# Tall enough for a full-width board:
TALL_SCREENS = [
    (360, 740, 24, 48),  # small Android phone with navigation buttons
    (393, 852, 59, 34),  # iPhone 15
    (412, 915, 24, 0),  # large Android phone with gesture navigation
    (430, 932, 59, 34),  # iPhone 15 Pro Max
    (800, 1280, 24, 48),  # Android tablet (portrait)
]
# Not tall enough: the board must shrink so the restart button stays visible.
WIDE_SCREENS = [
    (820, 1180, 24, 20),  # iPad Air (portrait)
    (884, 1104, 24, 0),  # unfolded foldable
    (800, 800, 0, 0),  # square window
    (1280, 720, 0, 0),  # landscape window (browser preview)
    (1024, 600, 24, 0),  # short landscape tablet
]


@pytest.mark.parametrize(("width", "height", "top", "bottom"), TALL_SCREENS + WIDE_SCREENS)
def test_everything_fits_on_the_screen(width: int, height: int, top: int, bottom: int) -> None:
    screen = ScreenSize(width, height, top, bottom)
    layout = layout_for_screen(screen)
    assert layout.board_width <= width - 2 * PAGE_PADDING
    assert screen.usable_height is not None
    # Includes the restart button, so it can never be pushed off the screen.
    assert layout.content_height <= screen.usable_height


@pytest.mark.parametrize(("width", "height", "top", "bottom"), TALL_SCREENS)
def test_tall_screens_still_get_a_full_width_board(
    width: int, height: int, top: int, bottom: int
) -> None:
    layout = layout_for_screen(ScreenSize(width, height, top, bottom))
    assert layout == layout_for_width(width)


@pytest.mark.parametrize(("width", "height", "top", "bottom"), WIDE_SCREENS)
def test_wide_screens_shrink_the_board_to_fit_the_height(
    width: int, height: int, top: int, bottom: int
) -> None:
    screen = ScreenSize(width, height, top, bottom)
    layout = layout_for_screen(screen)
    bigger = layout_for_cell(layout.cell_size + 1)
    assert layout.cell_size < layout_for_width(width).cell_size
    # As big as possible: one pixel more and it would no longer fit.
    assert screen.usable_height is not None
    assert bigger.content_height > screen.usable_height


def test_content_height_adds_up_every_part_of_the_screen() -> None:
    layout = layout_for_cell(100)
    expected = (
        layout.header_height
        + text_height(layout.status_font_size)
        + MESSAGE_SPACING
        + text_height(layout.feedback_font_size)
        + layout.board_width
        + layout.restart_height
        + 3 * SECTION_SPACING
    )
    assert layout.content_height == expected


def test_text_height_uses_the_fixed_line_height() -> None:
    assert text_height(20) == 25
    assert text_height(18) == 23  # 22.5 rounded up


@pytest.mark.parametrize("height", [None, 0, -5])
def test_unknown_height_only_uses_the_width(height: float | None) -> None:
    assert layout_for_screen(ScreenSize(1280, height)) == layout_for_width(1280)


def test_extremely_short_screens_keep_a_minimum_cell_size() -> None:
    assert layout_for_screen(ScreenSize(800, 200)).cell_size == MIN_CELL_SIZE


@pytest.mark.parametrize("cell", [MIN_CELL_SIZE, 80, 109, 200, 300])
def test_header_fits_the_title_and_a_comfortable_settings_button(cell: int) -> None:
    layout = layout_for_cell(cell)
    assert layout.header_height >= MIN_TOUCH_TARGET
    assert layout.header_height >= text_height(layout.title_font_size)


@pytest.mark.parametrize("cell", [MIN_CELL_SIZE, 109, 256])
def test_settings_buttons_fill_the_board_width(cell: int) -> None:
    layout = layout_for_cell(cell)
    for size, per_row in (
        (layout.operation_button_size, OPERATIONS_PER_ROW),
        (layout.table_button_size, TABLES_PER_ROW),
    ):
        row = per_row * size + (per_row - 1) * layout.cell_spacing
        assert layout.board_width - per_row < row <= layout.board_width
    assert layout.operation_button_size > layout.table_button_size
    assert 0 < layout.operation_font_size < layout.operation_button_size
    assert 0 < layout.table_font_size < layout.table_button_size


@pytest.mark.parametrize(("width", "height", "top", "bottom"), TALL_SCREENS + WIDE_SCREENS)
def test_settings_screen_always_fits_too(width: int, height: int, top: int, bottom: int) -> None:
    screen = ScreenSize(width, height, top, bottom)
    layout = layout_for_screen(screen)
    # Shorter than the game screen, which is already known to fit.
    assert layout.settings_content_height < layout.content_height
    assert screen.usable_height is not None
    assert layout.settings_content_height <= screen.usable_height
