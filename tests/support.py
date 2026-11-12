"""Helpers shared by the tests."""

from __future__ import annotations

from collections.abc import Callable, Collection, Iterable
from dataclasses import dataclass, field
from math import ceil
from typing import Any, cast

import flet as ft

from math_tic_tac_toe.i18n import Language, translator_for
from math_tic_tac_toe.questions import Question
from math_tic_tac_toe.settings import TABLES, GameSettings, Operation
from math_tic_tac_toe.ui.layout import (
    SECTION_SPACING,
    SETTINGS_HINT_MAX_LINES,
    TABLES_PER_ROW,
    ScreenLayout,
    ScreenSize,
    layout_for_screen,
    text_height,
)
from math_tic_tac_toe.ui.presenter import GamePresenter


def click(control: ft.Control) -> None:
    """Taps ``control``: runs its click handler as Flet would, without an event."""
    handler: Callable[[object], object] | None = getattr(control, "on_click", None)
    assert handler is not None, f"{type(control).__name__} has no click handler"
    handler(None)


def background_of(button: ft.Control) -> object:
    """The background color of a tile button (cell, option or choice) at rest.
    Their styles set it for every state, disabled included."""
    style = getattr(button, "style", None)
    assert style is not None, f"{type(button).__name__} has no style"
    return style.bgcolor[ft.ControlState.DEFAULT]


def slide(bar: ft.Slider, value: float) -> None:
    """Moves ``bar`` to ``value`` as Flet does: updates the value, then runs
    the change handler."""
    bar.value = value
    handler: Callable[[object], object] | None = getattr(bar, "on_change", None)
    assert handler is not None, "the bar has no change handler"
    handler(None)


def question_factory(difficulty: int, avoid: Collection[str] = ()) -> Question:
    """Every question has answer 1 and choices (1, 2, 3)."""
    return Question(f"question {difficulty}", 1, (1, 2, 3), Operation.MULTIPLICATION, difficulty)


def settings_of(operations: Iterable[Operation], tables: Iterable[int] = TABLES) -> GameSettings:
    """Settings from any collections (tables default to all of them)."""
    return GameSettings(frozenset(operations), frozenset(tables))


def layout_for_width(screen_width: float | None) -> ScreenLayout:
    """Layout for a screen whose height is unknown or tall enough."""
    return layout_for_screen(ScreenSize(screen_width))


def settings_content_height(layout: ScreenLayout) -> int:
    """Height of everything on the settings screen, play button included,
    following how ``SettingsView`` stacks its parts."""
    table_rows = ceil(len(TABLES) / TABLES_PER_ROW)
    return (
        text_height(layout.title_font_size)
        + SECTION_SPACING
        + SETTINGS_HINT_MAX_LINES * text_height(layout.settings_hint_font_size)
        + SECTION_SPACING
        + text_height(layout.status_font_size)  # "Operation" label
        + SECTION_SPACING
        + layout.operation_button_size
        + SECTION_SPACING
        + text_height(layout.status_font_size)  # "Times table" label
        + layout.cell_spacing
        + table_rows * layout.table_button_size
        + (table_rows - 1) * layout.cell_spacing
        + SECTION_SPACING
        + layout.restart_height  # the play button has the restart button's size
        + SECTION_SPACING
        + layout.restart_height  # the row of mode buttons (Best of 5, Hard mode)
    )


class FakeTime:
    """Time source for the chess clock that the tests move forward by hand."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


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
        self.on_resize: Callable[[Any], None] | None = None
        self.on_media_change: Callable[[Any], None] | None = None
        self.on_view_pop: Callable[[Any], None] | None = None
        self.views: list[ft.View] = [ft.View()]
        # Like Flet: a closed dialog stays here until the phone reports that
        # its closing animation ended (see `finish_closing_dialogs`).
        self._dialog_stack: list[ft.AlertDialog] = []
        self._drawn_views: list[ft.View] = list(self.views)
        self.orientations: list[ft.DeviceOrientation] | None = None
        self.updates = 0
        # Background tasks started with `run_task`: (coroutine function, args).
        self.tasks: list[tuple[Callable[..., Any], tuple[Any, ...]]] = []

    async def set_allowed_device_orientations(
        self, orientations: list[ft.DeviceOrientation]
    ) -> None:
        # Same rule as Flet: only phones and tablets can lock the orientation.
        if self.platform is None or not self.platform.is_mobile():
            raise ft.FletUnsupportedPlatformException("only supported on mobile platforms")
        self.orientations = orientations

    def as_page(self) -> ft.Page:
        """This fake, typed as the real page the app code expects. It only has
        what the app uses, which the tests exercise."""
        return cast("ft.Page", self)

    def resize(self, width: float, height: float = 740) -> None:
        """Simulates the screen changing size, like Flet's resize event."""
        self.width, self.height = width, height
        assert self.on_resize is not None
        self.on_resize(ft.PageResizeEvent("resize", self.as_page(), width=width, height=height))

    def press_back(self) -> None:
        """Simulates the phone's back button, like Flet's view pop event."""
        assert self.on_view_pop is not None
        self.on_view_pop(ft.ViewPopEvent("view_pop", self.as_page(), route=self.views[-1].route))

    def change_system_bars(self, top_inset: float, bottom_inset: float) -> None:
        """Simulates the system bars changing, like Flet's media change event."""
        self.media = media_with_insets(top_inset, bottom_inset)
        assert self.on_media_change is not None
        self.on_media_change(self.media)

    async def get_device_info(self) -> FakeDeviceInfo | None:
        if self._error:
            raise self._error
        return self._info

    @property
    def dialogs(self) -> list[ft.AlertDialog]:
        """The dialogs on screen: opened and not closed yet."""
        return [dialog for dialog in self._dialog_stack if dialog.open]

    def update(self) -> None:
        """Draws the page. Fails if the screen changes while a dialog is still
        closing: Flutter keeps that dialog attached to the screen it was
        opened on, so it would show up again, stuck, when that screen
        returns."""
        self.updates += 1
        if self.views != self._drawn_views:
            closing = [dialog for dialog in self._dialog_stack if not dialog.open]
            assert not closing, "the screen changed while a dialog was still closing"
            self._drawn_views = list(self.views)

    def run_task(self, handler: Callable[..., Any], *args: Any) -> None:  # noqa: ANN401
        """Records the task instead of running it; tests drive it by hand."""
        self.tasks.append((handler, args))

    def show_dialog(self, dialog: ft.AlertDialog) -> None:
        if dialog in self._dialog_stack:
            raise RuntimeError("Dialog is already opened")  # same rule as Flet
        dialog.open = True
        self._dialog_stack.append(dialog)

    def pop_dialog(self) -> ft.AlertDialog | None:
        """Closes the top open dialog. Like Flet, it only starts closing: it
        leaves the page once the phone reports the end of the animation."""
        dialog = next((d for d in reversed(self._dialog_stack) if d.open), None)
        if dialog is not None:
            dialog.open = False
        return dialog

    @property
    def closing_dialogs(self) -> list[ft.AlertDialog]:
        """Closed dialogs still waiting for the end of their animation."""
        return [dialog for dialog in self._dialog_stack if not dialog.open]

    def finish_closing_dialogs(self) -> None:
        """Simulates the phone reporting that closed dialogs finished closing
        (Flet's dismiss event): they leave the page and their `on_dismiss`
        runs."""
        for dialog in [d for d in self._dialog_stack if not d.open]:
            self._dialog_stack.remove(dialog)
            handler: Callable[[object], object] | None = getattr(dialog, "on_dismiss", None)
            if handler is not None:
                handler(None)


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
