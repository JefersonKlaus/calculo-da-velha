"""Shared colors, shapes and fixed sizes of the interface.

Sizes that depend on the screen width (board, restart button) live in
``layout``. The dialog keeps fixed sizes that fit small phones (360 dp wide):
its choices take 3 * 72 + 2 * 8 = 232 plus the dialog padding.
"""

from __future__ import annotations

import flet as ft

from ..game import Mark

CHOICE_SIZE = 72
CHOICE_SPACING = 8
CHOICE_FONT_SIZE = 24
DIALOG_INSET_PADDING = 24

WINNING_CELL_COLOR = "#FFC700"  # gold
WINNING_MARK_COLOR = "#4A3B00"  # dark gold, readable on the gold background

# Each player has a color, used for their marks and for messages about them.
PLAYER_COLORS = {
    Mark.X: "#1565C0",  # blue
    Mark.O: "#E65100",  # orange
}

CORRECT_ANSWER_COLOR = "#2E7D32"  # green
WRONG_ANSWER_COLOR = "#C62828"  # red

# Settings options: the chosen one keeps the normal filled look; the others
# are light, so the choice stands out.
UNSELECTED_OPTION_COLOR = "#DCE3EC"
UNSELECTED_OPTION_TEXT_COLOR = "#1B2A3A"


def player_color(player: Mark | None) -> str | None:
    """Color of a player's marks and messages; ``None`` keeps the default."""
    return PLAYER_COLORS[player] if player else None


def feedback_color(correct: bool) -> str:
    return CORRECT_ANSWER_COLOR if correct else WRONG_ANSWER_COLOR


def square_button_style() -> ft.ButtonStyle:
    """Button style with straight (not rounded) corners."""
    return ft.ButtonStyle(
        shape=ft.RoundedRectangleBorder(radius=0),
        padding=4,
    )


def option_button_style(selected: bool) -> ft.ButtonStyle:
    """Square style of a settings option; unselected options are light."""
    if selected:
        return square_button_style()
    return ft.ButtonStyle(
        shape=ft.RoundedRectangleBorder(radius=0),
        padding=4,
        bgcolor=UNSELECTED_OPTION_COLOR,
        color=UNSELECTED_OPTION_TEXT_COLOR,
    )


def winning_button_style() -> ft.ButtonStyle:
    """Square style painted gold for the cells of the winning line.

    Those cells are disabled once the game ends, so the colors are also set
    for the disabled state, which would otherwise render them grey.
    """
    every_state = (ft.ControlState.DEFAULT, ft.ControlState.DISABLED)
    return ft.ButtonStyle(
        shape=ft.RoundedRectangleBorder(radius=0),
        padding=4,
        bgcolor=dict.fromkeys(every_state, WINNING_CELL_COLOR),
        color=dict.fromkeys(every_state, WINNING_MARK_COLOR),
    )
