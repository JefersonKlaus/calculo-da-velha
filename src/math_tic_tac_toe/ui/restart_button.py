"""Button below the board that starts a new match. It is always shown:
"Restart" while the match is on, "Play again" once it ends."""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from .layout import ScreenLayout
from .styles import square_button_style


class RestartButton:
    def __init__(self, on_restart: Callable[[], None], layout: ScreenLayout) -> None:
        # The text is set by the controller, which knows if the match is over.
        self._label = ft.Text(weight=ft.FontWeight.BOLD)
        self.control = ft.FilledButton(
            content=self._label,
            icon=ft.Icons.REPLAY,
            style=square_button_style(),
            on_click=lambda _: on_restart(),
        )
        self.apply_layout(layout)

    def set_label(self, label: str) -> None:
        self._label.value = label

    def apply_layout(self, layout: ScreenLayout) -> None:
        """As wide as the board."""
        self.control.width = layout.board_width
        self.control.height = layout.restart_height
        self._label.size = layout.restart_font_size
