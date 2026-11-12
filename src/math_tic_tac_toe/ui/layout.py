"""Sizes of the game screen, computed from the screen size (no Flet).

The board is as big as possible: it fills the whole screen width (minus a
small margin) as long as everything still fits vertically. On screens that
are not tall enough for that (tablets, foldables, wide windows), the board
shrinks until the whole screen fits, so the restart button is never pushed
off the screen (it is always shown, during and after a match).

Every font grows with the cells, so the title and messages stay in proportion
with the board. Texts use a fixed line height so their height is known.

The settings screen reuses the board width: a hint of up to 2 lines below the
title, 4 operation buttons in one row, the times tables in rows of 5, the Play
button, and the two mode buttons (Best of 5 and Hard mode) side by side in one
row. It is always shorter than the game screen, so whatever fits the game
screen also fits the settings screen.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil, floor, isqrt

from ..game import Game

BOARD_SIDE = isqrt(Game.BOARD_SIZE)
PAGE_PADDING = 8
CELL_SPACING = 8
SECTION_SPACING = 10  # between title, messages, board and restart button
MESSAGE_SPACING = 4  # between the turn message and the answer feedback
TIMER_VERTICAL_PADDING = 2  # inside each hard mode timer, above and below its text
TIMER_HORIZONTAL_PADDING = 12
LINE_HEIGHT = 1.25  # line height of texts, as a multiple of the font size
# Absorbs sub-pixel rounding differences between platforms.
SAFETY_MARGIN = 8
MIN_CELL_SIZE = 48
MIN_TOUCH_TARGET = 48  # smallest comfortable size for a tappable icon
OPERATIONS_PER_ROW = 4
TABLES_PER_ROW = 5
# Used until the real screen size is known (a small phone is the safe guess).
DEFAULT_SCREEN_WIDTH = 360

# Sizes relative to the cell size, tuned on a small phone (109 dp cell).
PROMPT_FONT_RATIO = 0.18
MARK_FONT_RATIO = 0.54
RESTART_HEIGHT_RATIO = 0.54
RESTART_FONT_RATIO = 0.19
TITLE_FONT_RATIO = 0.26  # leaves room for the settings button
STATUS_FONT_RATIO = 0.2
FEEDBACK_FONT_RATIO = 0.165
SETTINGS_HINT_FONT_RATIO = 0.13
SETTINGS_HINT_MAX_LINES = 2  # the space for both lines is always reserved
# Best of N: the small countdown below the mark of a played cell.
CELL_TIMER_FONT_RATIO = 0.13
# The mode buttons share a row, so their icon and inner margins grow with the
# cells too: the longest label ("Modo difícil") then fits at every size.
MODE_BUTTON_PADDING_RATIO = 0.06


@dataclass(frozen=True)
class ScreenSize:
    """Screen size in logical pixels, plus the areas used by the system UI
    (status bar, notch, navigation bar) at the top and bottom."""

    width: float | None
    height: float | None = None
    top_inset: float = 0
    bottom_inset: float = 0

    @property
    def usable_height(self) -> float | None:
        if not self.height or self.height <= 0:
            return None
        return self.height - self.top_inset - self.bottom_inset - 2 * PAGE_PADDING - SAFETY_MARGIN


@dataclass(frozen=True)
class ScreenLayout:
    cell_size: int
    cell_spacing: int
    prompt_font_size: int
    mark_font_size: int
    restart_height: int
    restart_font_size: int
    title_font_size: int
    status_font_size: int
    feedback_font_size: int

    @property
    def board_width(self) -> int:
        return BOARD_SIDE * self.cell_size + (BOARD_SIDE - 1) * self.cell_spacing

    @property
    def header_height(self) -> int:
        """Title row of the game screen: the title and the settings button."""
        return max(text_height(self.title_font_size), MIN_TOUCH_TARGET)

    @property
    def timers_height(self) -> int:
        """Row of the two hard mode timers (text in the status font)."""
        return text_height(self.status_font_size) + 2 * TIMER_VERTICAL_PADDING

    @property
    def operation_button_size(self) -> int:
        return _buttons_per_row_size(self.board_width, OPERATIONS_PER_ROW, self.cell_spacing)

    @property
    def operation_font_size(self) -> int:
        return round(self.operation_button_size * 0.45)

    @property
    def table_button_size(self) -> int:
        return _buttons_per_row_size(self.board_width, TABLES_PER_ROW, self.cell_spacing)

    @property
    def settings_hint_font_size(self) -> int:
        return round(self.cell_size * SETTINGS_HINT_FONT_RATIO)

    @property
    def table_font_size(self) -> int:
        return round(self.table_button_size * 0.4)

    @property
    def cell_timer_font_size(self) -> int:
        return round(self.cell_size * CELL_TIMER_FONT_RATIO)

    @property
    def mode_button_width(self) -> int:
        """Two mode buttons side by side, as wide as the board together."""
        return _buttons_per_row_size(self.board_width, 2, self.cell_spacing)

    @property
    def mode_button_padding(self) -> int:
        """Inner margin on each side of a mode button's icon and label."""
        return round(self.cell_size * MODE_BUTTON_PADDING_RATIO)

    @property
    def content_height(self) -> int:
        """Height of everything on the game screen, restart button included.

        The hard mode timers are counted even when hidden, so both modes fit.
        """
        return (
            self.header_height
            + SECTION_SPACING
            + self.timers_height
            + SECTION_SPACING
            + text_height(self.status_font_size)
            + MESSAGE_SPACING
            + text_height(self.feedback_font_size)
            + SECTION_SPACING
            + self.board_width  # the board is square
            + SECTION_SPACING
            + self.restart_height
        )


def _buttons_per_row_size(row_width: int, count: int, spacing: int) -> int:
    return floor((row_width - (count - 1) * spacing) / count)


def text_height(font_size: int) -> int:
    """Height of a single line of text with the app's fixed line height."""
    return ceil(font_size * LINE_HEIGHT)


def layout_for_cell(cell: int) -> ScreenLayout:
    return ScreenLayout(
        cell_size=cell,
        cell_spacing=CELL_SPACING,
        prompt_font_size=round(cell * PROMPT_FONT_RATIO),
        mark_font_size=round(cell * MARK_FONT_RATIO),
        restart_height=round(cell * RESTART_HEIGHT_RATIO),
        restart_font_size=round(cell * RESTART_FONT_RATIO),
        title_font_size=round(cell * TITLE_FONT_RATIO),
        status_font_size=round(cell * STATUS_FONT_RATIO),
        feedback_font_size=round(cell * FEEDBACK_FONT_RATIO),
    )


def layout_for_screen(screen: ScreenSize) -> ScreenLayout:
    """Biggest layout that fits the screen width and, if known, its height."""
    width = screen.width if screen.width and screen.width > 0 else DEFAULT_SCREEN_WIDTH
    available = width - 2 * PAGE_PADDING - (BOARD_SIDE - 1) * CELL_SPACING
    cell = max(MIN_CELL_SIZE, floor(available / BOARD_SIDE))

    usable_height = screen.usable_height
    if usable_height is not None:
        while cell > MIN_CELL_SIZE and layout_for_cell(cell).content_height > usable_height:
            cell -= 1
    return layout_for_cell(cell)
