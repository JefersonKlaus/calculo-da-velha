"""The game title shown at the top of the screen."""

from __future__ import annotations

import flet as ft

from .layout import LINE_HEIGHT, ScreenLayout


class TitleView:
    def __init__(self, title: str, layout: ScreenLayout) -> None:
        # One line only: the layout relies on its height. Sizes leave room for
        # the title; "..." only shows if a translation were ever too long.
        self.control = ft.Text(
            title,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
            style=ft.TextStyle(height=LINE_HEIGHT),
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        self.apply_layout(layout)

    def apply_layout(self, layout: ScreenLayout) -> None:
        self.control.size = layout.title_font_size
