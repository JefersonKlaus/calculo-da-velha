"""Top of the game screen: the title and a button to open the settings."""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from .layout import ScreenLayout
from .title_view import TitleView


class GameHeader:
    def __init__(
        self,
        title: str,
        settings_tooltip: str,
        on_open_settings: Callable[[], None],
        layout: ScreenLayout,
    ) -> None:
        self._title = TitleView(title, layout)
        self._title.control.expand = True  # the space between the two buttons
        self.settings_button = ft.IconButton(
            icon=ft.Icons.SETTINGS,
            tooltip=settings_tooltip,
            on_click=lambda _: on_open_settings(),
        )
        # Same size as the button on the other side, so the title stays centered.
        self._balance = ft.Container()
        self.control = ft.Row(
            [self._balance, self._title.control, self.settings_button],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
        )
        self.apply_layout(layout)

    def apply_layout(self, layout: ScreenLayout) -> None:
        """As wide as the board, never wider."""
        self.control.width = layout.board_width
        self._title.apply_layout(layout)
        size = layout.header_height
        self.settings_button.width = self.settings_button.height = size
        self.settings_button.icon_size = round(size * 0.6)
        self._balance.width = self._balance.height = size
