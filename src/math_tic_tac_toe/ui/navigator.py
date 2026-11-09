"""Switches between the settings screen and the game screen.

The game screen is stacked on top of the settings screen, so the phone's
back button (or gesture) returns to the settings.
"""

from __future__ import annotations

from collections.abc import Callable

import flet as ft


class ScreenNavigator:
    def __init__(
        self,
        page: ft.Page,
        settings_screen: ft.View,
        game_screen: ft.View,
        refresh: Callable[[], None],
    ) -> None:
        self._page = page
        self._settings_screen = settings_screen
        self._game_screen = game_screen
        self._refresh = refresh
        page.on_view_pop = lambda _: self.show_settings()

    def show_settings(self) -> None:
        self._page.views[:] = [self._settings_screen]
        self._refresh()

    def show_game(self) -> None:
        self._page.views[:] = [self._settings_screen, self._game_screen]
        self._refresh()
