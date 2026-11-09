"""Helpers shared by the tests."""

from __future__ import annotations

from collections.abc import Callable, Collection
from dataclasses import dataclass, field
from typing import Any

import flet as ft

from math_tic_tac_toe.i18n import Language, translator_for
from math_tic_tac_toe.questions import Question
from math_tic_tac_toe.settings import Operation
from math_tic_tac_toe.ui.layout import ScreenLayout, layout_for_width
from math_tic_tac_toe.ui.presenter import GamePresenter


def question_factory(difficulty: int, avoid: Collection[str] = ()) -> Question:
    """Every question has answer 1 and choices (1, 2, 3)."""
    return Question(f"question {difficulty}", 1, (1, 2, 3), Operation.MULTIPLICATION, difficulty)


def english_presenter() -> GamePresenter:
    return GamePresenter(translator_for(Language.ENGLISH))


def phone_layout() -> ScreenLayout:
    """Layout of a small phone (360 dp wide)."""
    return layout_for_width(360)


@dataclass
class FakeDeviceInfo:
    locales: list[ft.Locale] = field(default_factory=list)


class FakePage:
    """Stands in for ``ft.Page``: records what the app does with the page.

    Defaults to an Android phone with a 360 x 740 dp screen and no system bars.
    """

    def __init__(
        self,
        info: FakeDeviceInfo | None = None,
        error: Exception | None = None,
        platform: ft.PagePlatform | None = ft.PagePlatform.ANDROID,
        web: bool = False,
        width: float | None = 360,
        height: float | None = 740,
        top_inset: float = 0,
        bottom_inset: float = 0,
    ) -> None:
        self._info = info
        self._error = error
        self.platform = platform
        self.web = web
        self.width = width
        self.height = height
        self.media = media_with_insets(top_inset, bottom_inset)
        self.title = ""
        self.theme_mode: ft.ThemeMode | None = None
        self.horizontal_alignment: ft.CrossAxisAlignment | None = None
        self.padding: int | None = None
        self.scroll: ft.ScrollMode | None = None
        self.on_resize: Callable[[Any], None] | None = None
        self.on_media_change: Callable[[Any], None] | None = None
        self.on_view_pop: Callable[[Any], None] | None = None
        self.views: list[ft.View] = [ft.View()]
        self.controls: list[ft.Control] = []
        self.dialogs: list[ft.AlertDialog] = []
        self.orientations: list[ft.DeviceOrientation] | None = None
        self.updates = 0

    async def set_allowed_device_orientations(
        self, orientations: list[ft.DeviceOrientation]
    ) -> None:
        # Same rule as Flet: only phones and tablets can lock the orientation.
        if self.platform is None or not self.platform.is_mobile():
            raise ft.FletUnsupportedPlatformException("only supported on mobile platforms")
        self.orientations = orientations

    def resize(self, width: float, height: float = 740) -> None:
        """Simulates the screen changing size, like Flet's resize event."""
        self.width, self.height = width, height
        assert self.on_resize is not None
        self.on_resize(ft.PageResizeEvent("resize", self, width=width, height=height))

    def press_back(self) -> None:
        """Simulates the phone's back button, like Flet's view pop event."""
        assert self.on_view_pop is not None
        self.on_view_pop(ft.ViewPopEvent("view_pop", self, route=self.views[-1].route))

    def change_system_bars(self, top_inset: float, bottom_inset: float) -> None:
        """Simulates the system bars changing, like Flet's media change event."""
        self.media = media_with_insets(top_inset, bottom_inset)
        assert self.on_media_change is not None
        self.on_media_change(self.media)

    async def get_device_info(self) -> FakeDeviceInfo | None:
        if self._error:
            raise self._error
        return self._info

    def add(self, *controls: ft.Control) -> None:
        self.controls.extend(controls)

    def update(self) -> None:
        self.updates += 1

    def show_dialog(self, dialog: ft.AlertDialog) -> None:
        self.dialogs.append(dialog)

    def pop_dialog(self) -> ft.AlertDialog | None:
        return self.dialogs.pop() if self.dialogs else None


def media_with_insets(top: float, bottom: float) -> ft.PageMediaData:
    insets = ft.Padding(top=top, bottom=bottom)
    return ft.PageMediaData(
        padding=insets,
        view_padding=insets,
        view_insets=ft.Padding.zero(),
        device_pixel_ratio=2.0,
        orientation=ft.Orientation.PORTRAIT,
    )


def device(language_code: str, country_code: str | None = None) -> FakeDeviceInfo:
    return FakeDeviceInfo([ft.Locale(language_code, country_code)])
