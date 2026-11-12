"""Best of N: both players' points, shown below the title.

X's points on the left and O's on the right, in each player's color, with
what wins the match between them ("First to 3 wins"). It takes the place of
the hard mode timers (a match is never both), with the same height, so the
layout's space for the timers fits it too. Outside a best of N it is hidden.
"""

from __future__ import annotations

import flet as ft

from ..game import Mark
from .layout import (
    LINE_HEIGHT,
    TIMER_HORIZONTAL_PADDING,
    TIMER_VERTICAL_PADDING,
    ScreenLayout,
)
from .presenter import ScoreBoard
from .styles import MUTED_TEXT_COLOR, SURFACE_COLOR, player_color


class ScoreView:
    def __init__(self, layout: ScreenLayout) -> None:
        # One line with a fixed height, like the timers: the layout relies on it.
        self._points = {
            player: ft.Text(
                weight=ft.FontWeight.BOLD,
                color=player_color(player),
                style=ft.TextStyle(height=LINE_HEIGHT),
                max_lines=1,
            )
            for player in Mark
        }
        self.scores = {
            player: ft.Container(
                content=text,
                padding=ft.Padding.symmetric(
                    vertical=TIMER_VERTICAL_PADDING, horizontal=TIMER_HORIZONTAL_PADDING
                ),
                border_radius=ft.BorderRadius.all(8),
                bgcolor=SURFACE_COLOR,
            )
            for player, text in self._points.items()
        }
        # Between the points; shortened with "..." if a screen is too narrow.
        self.goal = ft.Text(
            color=MUTED_TEXT_COLOR,
            text_align=ft.TextAlign.CENTER,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
            expand=True,
        )
        self.control = ft.Row(
            [self.scores[Mark.X], self.goal, self.scores[Mark.O]],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            visible=False,
        )
        self.apply_layout(layout)

    def apply_layout(self, layout: ScreenLayout) -> None:
        """As wide as the board."""
        self.control.width = layout.board_width
        self.control.spacing = layout.cell_spacing
        for text in self._points.values():
            text.size = layout.status_font_size
        self.goal.size = layout.feedback_font_size

    def show_score(self, board: ScoreBoard | None) -> None:
        self.control.visible = board is not None
        if board is None:
            return
        for score in board.scores:
            self._points[score.player].value = f"{score.player.value}  {score.points}"
        self.goal.value = board.goal
