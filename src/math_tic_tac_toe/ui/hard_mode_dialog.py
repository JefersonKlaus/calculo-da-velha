"""Modal opened by the red "Hard mode" button: the players confirm (or
change) the time each of them has for the whole match, then start.

The time is chosen on a bar (a slider), so it is always valid: 1:00 by
default, from 0:05 to 5:00 in steps of 5 seconds. It is shown as
minutes:seconds, like the timers of the match.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import flet as ft

from ..settings import (
    DEFAULT_TIME_LIMIT,
    MAX_TIME_LIMIT,
    MIN_TIME_LIMIT,
    TIME_LIMIT_STEP,
    snap_time_limit,
)
from .presenter import clock_text
from .styles import HARD_MODE_COLOR, hard_mode_button_style

StartHandler = Callable[[int], None]

TIME_FONT_SIZE = 32
# Fits a small phone (360 dp): the dialog's inset and padding take the rest.
BAR_WIDTH = 240


@dataclass(frozen=True)
class HardModeLabels:
    title: str
    message: str
    time_per_player: str  # shown above the time
    cancel: str
    start: str


class TimeBar:
    """The chosen time, in large text, above a bar that changes it."""

    def __init__(self, seconds: int, on_change: Callable[[], None]) -> None:
        self._on_change = on_change
        self.time = ft.Text(size=TIME_FONT_SIZE, weight=ft.FontWeight.BOLD)
        self.bar = ft.Slider(
            min=MIN_TIME_LIMIT,
            max=MAX_TIME_LIMIT,
            divisions=(MAX_TIME_LIMIT - MIN_TIME_LIMIT) // TIME_LIMIT_STEP,
            value=seconds,
            active_color=HARD_MODE_COLOR,
            width=BAR_WIDTH,
            on_change=lambda _: self._changed(),
        )
        # The limits, under each end of the bar.
        self.limits = ft.Row(
            [ft.Text(clock_text(MIN_TIME_LIMIT)), ft.Text(clock_text(MAX_TIME_LIMIT))],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            width=BAR_WIDTH,
        )
        self.control = ft.Column(
            [self.time, self.bar, self.limits],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
            tight=True,
        )
        self._show()

    @property
    def seconds(self) -> int:
        return snap_time_limit(self.bar.value or MIN_TIME_LIMIT)

    def _changed(self) -> None:
        self._show()
        self._on_change()

    def _show(self) -> None:
        self.time.value = clock_text(self.seconds)


class HardModeDialog:
    """Opens the modal on the page; "Start" closes it and starts the match.

    The match (which switches to the game screen) only starts once the dialog
    has finished closing. Flutter keeps a dialog attached to the screen it
    was opened on: switching screens while it is still closing would leave
    it behind, and it would come back, stuck open, with the settings screen.
    """

    def __init__(self, page: ft.Page, labels: HardModeLabels, refresh: Callable[[], None]) -> None:
        self._page = page
        self._labels = labels
        self._refresh = refresh

    def ask(self, on_start: StartHandler) -> None:
        labels = self._labels
        time_bar = TimeBar(DEFAULT_TIME_LIMIT, on_change=self._refresh)
        chosen: list[int] = []  # the time, once "Start" is tapped

        def start() -> None:
            if chosen:
                return  # a second tap while the dialog is closing
            chosen.append(time_bar.seconds)
            self._page.pop_dialog()

        def closed() -> None:
            # The phone reports that the dialog is gone (after "Start" or
            # "Cancel"): now it is safe to switch to the game screen.
            if chosen:
                on_start(chosen[0])

        self._page.show_dialog(
            ft.AlertDialog(
                modal=True,
                on_dismiss=lambda _: closed(),
                title=ft.Text(labels.title),
                content=ft.Column(
                    [ft.Text(labels.message), ft.Text(labels.time_per_player), time_bar.control],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    tight=True,
                ),
                actions=[
                    ft.TextButton(
                        content=labels.cancel, on_click=lambda _: self._page.pop_dialog()
                    ),
                    ft.FilledButton(
                        content=labels.start,
                        icon=ft.Icons.TIMER,
                        style=hard_mode_button_style(),
                        on_click=lambda _: start(),
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )
