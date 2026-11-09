"""Keeps the screen's views sized to the current screen."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Protocol

import flet as ft

from .layout import ScreenLayout, ScreenSize, layout_for_screen


class Resizable(Protocol):
    def apply_layout(self, layout: ScreenLayout) -> None: ...


def screen_size_of(
    page: ft.Page,
    width: float | None = None,
    height: float | None = None,
    insets: ft.Padding | None = None,
) -> ScreenSize:
    """Reads the screen size from the page; event values take precedence."""
    padding = insets or page.media.padding
    return ScreenSize(
        width=width if width is not None else page.width,
        height=height if height is not None else page.height,
        top_inset=padding.top or 0,
        bottom_inset=padding.bottom or 0,
    )


class ResponsiveLayout:
    def __init__(self, views: Sequence[Resizable], refresh: Callable[[], None]) -> None:
        self._views = views
        self._refresh = refresh

    def fit(self, screen: ScreenSize) -> ScreenLayout:
        """Resizes every view for ``screen`` and redraws it."""
        layout = layout_for_screen(screen)
        for view in self._views:
            view.apply_layout(layout)
        self._refresh()
        return layout
