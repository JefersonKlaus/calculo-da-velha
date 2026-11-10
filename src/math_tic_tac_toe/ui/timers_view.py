"""Hard mode: the two players' timers, shown below the title.

Each timer shows its player's mark and time in the player's color. The
running one (whose turn it is) gets a light background in that color, and a
timer turns red during its last seconds. Outside hard mode it is hidden.
"""

from __future__ import annotations

from collections.abc import Sequence

import flet as ft

from ..game import Mark
from .layout import (
    LINE_HEIGHT,
    TIMER_HORIZONTAL_PADDING,
    TIMER_VERTICAL_PADDING,
    ScreenLayout,
)
from .presenter import TimerState
from .styles import LOW_TIME_COLOR, RUNNING_TIMER_COLORS, player_color


class TimersView:
    def __init__(self, layout: ScreenLayout) -> None:
        # One line with a fixed height: the layout relies on it.
        self._texts = {
            player: ft.Text(
                weight=ft.FontWeight.BOLD,
                style=ft.TextStyle(height=LINE_HEIGHT),
                max_lines=1,
            )
            for player in Mark
        }
        self.timers = {
            player: ft.Container(
                content=text,
                padding=ft.Padding.symmetric(
                    vertical=TIMER_VERTICAL_PADDING, horizontal=TIMER_HORIZONTAL_PADDING
                ),
                border_radius=ft.BorderRadius.all(8),
            )
            for player, text in self._texts.items()
        }
        self.control = ft.Row(
            [*self.timers.values()],
            alignment=ft.MainAxisAlignment.CENTER,
            tight=True,
            visible=False,
        )
        self.apply_layout(layout)

    def apply_layout(self, layout: ScreenLayout) -> None:
        self.control.spacing = layout.cell_spacing
        for text in self._texts.values():
            text.size = layout.status_font_size

    def show_timers(self, timers: Sequence[TimerState]) -> None:
        self.control.visible = bool(timers)
        for timer in timers:
            text = self._texts[timer.player]
            text.value = f"{timer.player.value}  {timer.time}"
            text.color = LOW_TIME_COLOR if timer.low else player_color(timer.player)
            running_color = RUNNING_TIMER_COLORS[timer.player] if timer.running else None
            self.timers[timer.player].bgcolor = running_color
