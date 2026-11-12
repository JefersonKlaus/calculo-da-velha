"""The seconds left on the turn: a timer icon and the seconds, in a soft
color that turns red during the last seconds. Shown next to whose turn it
is, and above the question while one is open."""

from __future__ import annotations

import flet as ft

from .presenter import TurnTime
from .styles import ALERT_COLOR, MUTED_TEXT_COLOR


class TurnTimeView:
    def __init__(self, size: int, line_height: float | None = None) -> None:
        self.icon = ft.Icon(ft.Icons.TIMER)
        self.seconds = ft.Text(
            weight=ft.FontWeight.BOLD, style=ft.TextStyle(height=line_height), max_lines=1
        )
        self.control = ft.Row(
            [self.icon, self.seconds],
            spacing=4,
            tight=True,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.resize(size)

    def resize(self, size: int) -> None:
        self.icon.size = self.seconds.size = size

    def show(self, time: TurnTime | None) -> None:
        """Shows the seconds; ``None`` hides the view (no turn running)."""
        self.control.visible = time is not None
        if time is None:
            return
        self.seconds.value = str(time.seconds)
        color = ALERT_COLOR if time.low else MUTED_TEXT_COLOR
        self.seconds.color = self.icon.color = color
