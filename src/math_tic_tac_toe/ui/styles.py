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

# Seed of the app's color theme. Filled buttons (board cells, answer choices
# and *selected* settings options) take their blue from it, and the settings
# screen tells players that blue means selected, so it is set explicitly
# instead of relying on Flet's default.
THEME_SEED_COLOR = ft.Colors.BLUE

WINNING_CELL_COLOR = "#FFC700"  # gold
WINNING_MARK_COLOR = "#4A3B00"  # dark gold, readable on the gold background

# Each player has a color, used for their marks and for messages about them.
PLAYER_COLORS = {
    Mark.X: "#1565C0",  # blue
    Mark.O: "#6A1B9A",  # purple
}

# Red for what needs attention: a wrong answer, a player out of time, a
# timer in its last seconds, and the hard mode button.
ALERT_COLOR = "#C62828"
HARD_MODE_COLOR = ALERT_COLOR
HARD_MODE_TEXT_COLOR = "#FFFFFF"
LOW_TIME_COLOR = ALERT_COLOR
# Light background of the running timer, in its player's color.
RUNNING_TIMER_COLORS = {
    Mark.X: "#E3F2FD",  # light blue
    Mark.O: "#F3E5F5",  # light purple
}

# Settings options: the chosen one keeps the normal filled (blue) look; the
# others are light, so the choice stands out.
UNSELECTED_OPTION_COLOR = "#DCE3EC"
UNSELECTED_OPTION_TEXT_COLOR = "#1B2A3A"
# The hint below the settings title is secondary text, softer than labels.
HINT_COLOR = ft.Colors.ON_SURFACE_VARIANT


def app_theme() -> ft.Theme:
    return ft.Theme(color_scheme_seed=THEME_SEED_COLOR)


def player_color(player: Mark | None) -> str | None:
    """Color of a player's marks and messages; ``None`` keeps the default."""
    return PLAYER_COLORS[player] if player else None


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


def hard_mode_button_style() -> ft.ButtonStyle:
    """Square style painted red: hard mode stands out from the normal game."""
    return ft.ButtonStyle(
        shape=ft.RoundedRectangleBorder(radius=0),
        padding=4,
        bgcolor=HARD_MODE_COLOR,
        color=HARD_MODE_TEXT_COLOR,
        icon_color=HARD_MODE_TEXT_COLOR,
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
