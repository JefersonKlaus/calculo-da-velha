"""Button that starts a new match, shown below the board once a match ends."""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from .layout import ScreenLayout
from .styles import square_button_style


class RestartButton:
    def __init__(self, label: str, on_restart: Callable[[], None], layout: ScreenLayout) -> None:
        self._label = ft.Text(label, weight=ft.FontWeight.BOLD)
        self.control = ft.FilledButton(
            content=self._label,
            icon=ft.Icons.REPLAY,
            style=square_button_style(),
            visible=False,
            on_click=lambda _: on_restart(),
        )
        self.apply_layout(layout)

    def set_visible(self, visible: bool) -> None:
        self.control.visible = visible

    def apply_layout(self, layout: ScreenLayout) -> None:
        """As wide as the board."""
        self.control.width = layout.board_width
        self.control.height = layout.restart_height
        self._label.size = layout.restart_font_size
