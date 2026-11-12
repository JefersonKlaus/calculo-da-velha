"""Shared colors, shapes and fixed sizes of the interface.

The colors follow the app's design (``docs/design``): a dark navy background,
navy cards outlined in a lighter navy, light text, a pink accent for what is
selected or starts something, one color per player (blue and pink), gold for
the winner and a soft red for what needs attention.

Sizes that depend on the screen width (board, restart button) live in
``layout``. The dialog keeps fixed sizes that fit small phones (360 dp wide):
its choices take 3 * 72 + 2 * 8 = 232 plus the dialog padding. Nothing here
changes a size: borders are drawn on the buttons' shapes, inside them.
"""

from __future__ import annotations

import flet as ft

from ..game import Mark

CHOICE_SIZE = 72
CHOICE_SPACING = 8
CHOICE_FONT_SIZE = 24
TURN_TIME_FONT_SIZE = 20  # the seconds left to answer, above the question
DIALOG_INSET_PADDING = 24

# ---- palette (docs/design) ---------------------------------------------------

BACKGROUND_COLOR = "#10182F"  # dark navy: every screen
SURFACE_COLOR = "#202E56"  # navy: cards, dialogs, board cells, secondary buttons
RAISED_SURFACE_COLOR = "#2A3B6B"  # lighter navy: buttons inside a card (answer choices)
OUTLINE_COLOR = "#394A79"  # border of the navy surfaces
TEXT_COLOR = "#E1E2E8"  # near white: titles, questions, labels on navy
MUTED_TEXT_COLOR = "#7E89AB"  # greyish blue: hints and section labels
ACCENT_COLOR = "#FF5D98"  # pink: selected options and the main buttons
ON_ACCENT_COLOR = "#FFFFFF"  # text on the pink accent
GOLD_COLOR = "#FFCF69"

# Seed of the app's color theme: the pink accent. The color scheme below
# sets every role the app uses, so the seed only fills in the rest.
THEME_SEED_COLOR = ACCENT_COLOR

WINNING_CELL_COLOR = GOLD_COLOR
WINNING_MARK_COLOR = BACKGROUND_COLOR  # dark navy, readable on the gold background
WINNER_MESSAGE_COLOR = GOLD_COLOR  # "Game over: X wins!", like the winning cells

# Each player has a color, used for their marks and for messages about them.
PLAYER_COLORS = {
    Mark.X: "#65B5FF",  # blue
    Mark.O: ACCENT_COLOR,  # pink
}

# Soft red for texts that need attention: a wrong answer, a player out of
# time, a timer in its last seconds.
ALERT_COLOR = "#FF7A7A"
LOW_TIME_COLOR = ALERT_COLOR
# Hard mode (its button, the Start button and the time bar) is painted red,
# a deeper red than the texts so that white text reads well on it.
HARD_MODE_COLOR = "#DC3545"
HARD_MODE_TEXT_COLOR = "#FFFFFF"
# "Best of 5" plays for points: its button is gold, the color of winning.
BEST_OF_COLOR = GOLD_COLOR
BEST_OF_TEXT_COLOR = BACKGROUND_COLOR
# "Point for X!" below the status: a good message, not an alert.
GOOD_NEWS_COLOR = TEXT_COLOR
# Background of the running timer: its player's color at 20% over the navy
# background, dark enough for the player's color (and the red) to read on it.
RUNNING_TIMER_COLORS = {
    Mark.X: "#213759",  # dark blue
    Mark.O: "#402644",  # dark pink
}

# Settings options: the chosen ones are pink; the others are navy, outlined,
# so the choice stands out.
SELECTED_OPTION_COLOR = ACCENT_COLOR
SELECTED_OPTION_TEXT_COLOR = ON_ACCENT_COLOR
UNSELECTED_OPTION_COLOR = SURFACE_COLOR
UNSELECTED_OPTION_TEXT_COLOR = TEXT_COLOR
# The hint below the settings title is secondary text, softer than labels.
HINT_COLOR = MUTED_TEXT_COLOR
SECTION_LABEL_COLOR = MUTED_TEXT_COLOR
# The question of a cell once the match is over: it can no longer be played.
FINISHED_QUESTION_COLOR = MUTED_TEXT_COLOR

# ---- shapes --------------------------------------------------------------------

TILE_RADIUS = 12  # rounded corners of square buttons (cells, options, choices)
DIALOG_RADIUS = 20
BORDER_WIDTH = 1.5
CELL_BORDER_WIDTH = 2  # a played cell is outlined in its player's color
# Inside the pill buttons: room around the text when a pill is only as wide
# as its text (dialog buttons); full-width pills center it anyway.
PILL_PADDING = ft.Padding.symmetric(vertical=4, horizontal=16)

_EVERY_STATE = (ft.ControlState.DEFAULT, ft.ControlState.DISABLED)


def app_theme() -> ft.Theme:
    """Dark navy theme with the pink accent of the design."""
    return ft.Theme(
        color_scheme_seed=THEME_SEED_COLOR,
        color_scheme=ft.ColorScheme(
            primary=ACCENT_COLOR,
            on_primary=ON_ACCENT_COLOR,
            secondary=PLAYER_COLORS[Mark.X],
            on_secondary=BACKGROUND_COLOR,
            error=ALERT_COLOR,
            on_error=BACKGROUND_COLOR,
            surface=BACKGROUND_COLOR,
            on_surface=TEXT_COLOR,
            on_surface_variant=MUTED_TEXT_COLOR,
            surface_container_lowest=BACKGROUND_COLOR,
            surface_container_low=SURFACE_COLOR,
            surface_container=SURFACE_COLOR,
            surface_container_high=SURFACE_COLOR,
            surface_container_highest=RAISED_SURFACE_COLOR,
            surface_tint=ft.Colors.TRANSPARENT,
            outline=OUTLINE_COLOR,
            outline_variant=OUTLINE_COLOR,
        ),
        scaffold_bgcolor=BACKGROUND_COLOR,
        # Texts keep Flutter's dialog sizes; their color comes from on_surface.
        dialog_theme=ft.DialogTheme(bgcolor=SURFACE_COLOR, shape=dialog_shape()),
        # The phone's status and navigation bars blend with the navy screens.
        system_overlay_style=ft.SystemOverlayStyle(
            status_bar_color=BACKGROUND_COLOR,
            system_navigation_bar_color=BACKGROUND_COLOR,
            status_bar_icon_brightness=ft.Brightness.LIGHT,
            system_navigation_bar_icon_brightness=ft.Brightness.LIGHT,
        ),
    )


def player_color(player: Mark | None) -> str | None:
    """Color of a player's marks and messages; ``None`` keeps the default."""
    return PLAYER_COLORS[player] if player else None


def dialog_shape() -> ft.RoundedRectangleBorder:
    """Rounded navy card outlined in a lighter navy, like the design's cards."""
    return ft.RoundedRectangleBorder(
        radius=DIALOG_RADIUS, side=ft.BorderSide(BORDER_WIDTH, OUTLINE_COLOR)
    )


def _tile_style(
    bgcolor: str,
    color: str,
    border: str | None = None,
    border_width: float = BORDER_WIDTH,
    disabled_color: str | None = None,
) -> ft.ButtonStyle:
    """Square button with rounded corners. The colors are also set for the
    disabled state (taken cells, the board once the match is over), which
    would otherwise render grey."""
    return ft.ButtonStyle(
        shape=ft.RoundedRectangleBorder(radius=TILE_RADIUS),
        padding=4,
        bgcolor=dict.fromkeys(_EVERY_STATE, bgcolor),
        color={
            ft.ControlState.DEFAULT: color,
            ft.ControlState.DISABLED: disabled_color or color,
        },
        side=ft.BorderSide(border_width, border) if border else None,
    )


def square_button_style() -> ft.ButtonStyle:
    """Raised navy tile (the answer choices inside the question dialog)."""
    return _tile_style(RAISED_SURFACE_COLOR, TEXT_COLOR, border=OUTLINE_COLOR)


def cell_button_style(player: Mark | None = None) -> ft.ButtonStyle:
    """A board cell: a navy tile; once played, outlined in its player's color.
    Questions that can no longer be played (match over) are muted."""
    if player is None:
        return _tile_style(
            SURFACE_COLOR,
            TEXT_COLOR,
            border=OUTLINE_COLOR,
            disabled_color=FINISHED_QUESTION_COLOR,
        )
    return _tile_style(
        SURFACE_COLOR,
        PLAYER_COLORS[player],
        border=PLAYER_COLORS[player],
        border_width=CELL_BORDER_WIDTH,
    )


def option_button_style(selected: bool) -> ft.ButtonStyle:
    """Square style of a settings option: pink when selected, navy otherwise."""
    if selected:
        return _tile_style(SELECTED_OPTION_COLOR, SELECTED_OPTION_TEXT_COLOR)
    return _tile_style(UNSELECTED_OPTION_COLOR, UNSELECTED_OPTION_TEXT_COLOR, border=OUTLINE_COLOR)


def winning_button_style() -> ft.ButtonStyle:
    """Square style painted gold for the cells of the winning line.

    Those cells are disabled once the game ends, so the colors are also set
    for the disabled state, which would otherwise render them grey.
    """
    return _tile_style(WINNING_CELL_COLOR, WINNING_MARK_COLOR)


def primary_button_style() -> ft.ButtonStyle:
    """Pink pill: the main action of a screen (Play) or of a dialog."""
    return ft.ButtonStyle(
        shape=ft.StadiumBorder(),
        padding=PILL_PADDING,
        bgcolor=ACCENT_COLOR,
        color=ON_ACCENT_COLOR,
        icon_color=ON_ACCENT_COLOR,
    )


def secondary_button_style() -> ft.ButtonStyle:
    """Navy pill outlined in a lighter navy (the restart button)."""
    return ft.ButtonStyle(
        shape=ft.StadiumBorder(),
        padding=PILL_PADDING,
        bgcolor=SURFACE_COLOR,
        color=TEXT_COLOR,
        icon_color=TEXT_COLOR,
        side=ft.BorderSide(BORDER_WIDTH, OUTLINE_COLOR),
    )


def hard_mode_button_style(
    padding: ft.Padding = PILL_PADDING, icon_size: int | None = None
) -> ft.ButtonStyle:
    """Red pill with white text: hard mode stands out from the normal game,
    and from the pink Play button above it."""
    return _filled_pill(HARD_MODE_COLOR, HARD_MODE_TEXT_COLOR, padding, icon_size)


def best_of_button_style(
    padding: ft.Padding = PILL_PADDING, icon_size: int | None = None
) -> ft.ButtonStyle:
    """Gold pill with dark navy text: the "Best of 5" mode."""
    return _filled_pill(BEST_OF_COLOR, BEST_OF_TEXT_COLOR, padding, icon_size)


def mode_button_padding(horizontal: int) -> ft.Padding:
    """Inner margins of a mode button; the sides grow with the screen."""
    return ft.Padding.symmetric(vertical=4, horizontal=horizontal)


def _filled_pill(
    bgcolor: str, color: str, padding: ft.Padding, icon_size: int | None
) -> ft.ButtonStyle:
    return ft.ButtonStyle(
        shape=ft.StadiumBorder(),
        padding=padding,
        bgcolor=bgcolor,
        color=color,
        icon_color=color,
        icon_size=icon_size,
    )


def icon_button_style() -> ft.ButtonStyle:
    """Round navy button outlined in a lighter navy (the settings button)."""
    return ft.ButtonStyle(
        shape=ft.CircleBorder(),
        bgcolor=SURFACE_COLOR,
        icon_color=TEXT_COLOR,
        side=ft.BorderSide(BORDER_WIDTH, OUTLINE_COLOR),
    )
