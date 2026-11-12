"""Settings screen: choose the operations and, for multiplication and
division, the times tables. The play button starts a match with them.

Everything starts selected; each tap selects or unselects one option. A hint
below the title explains that the options in pink are the selected ones.
Below the pink "Play" button, two other modes share a row: the gold "Best of
5" button (points: the first to 3 lines wins) and the red "Hard mode" button
(a timed match).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from functools import partial

import flet as ft

from ..settings import OPERATIONS, TABLES, GameSettings, Operation
from .events import ignoring_event
from .layout import (
    LINE_HEIGHT,
    SECTION_SPACING,
    SETTINGS_HINT_MAX_LINES,
    TABLES_PER_ROW,
    ScreenLayout,
)
from .square_button import square_button, square_label
from .styles import (
    HINT_COLOR,
    SECTION_LABEL_COLOR,
    best_of_button_style,
    hard_mode_button_style,
    mode_button_padding,
    option_button_style,
    primary_button_style,
)
from .title_view import TitleView


@dataclass(frozen=True)
class SettingsLabels:
    title: str
    hint: str
    operation: str
    times_table: str
    play: str
    best_of: str
    hard_mode: str


class SettingsView:
    def __init__(
        self,
        labels: SettingsLabels,
        settings: GameSettings,
        on_play: Callable[[GameSettings], None],
        on_best_of: Callable[[GameSettings], None],
        on_hard_mode: Callable[[GameSettings], None],
        refresh: Callable[[], None],
        layout: ScreenLayout,
    ) -> None:
        self._settings = settings
        self._refresh = refresh
        self._layout = layout
        self._title = TitleView(labels.title, layout)
        # Up to 2 lines (the layout reserves both), centered under the title.
        self.hint = ft.Text(
            labels.hint,
            color=HINT_COLOR,
            text_align=ft.TextAlign.CENTER,
            style=ft.TextStyle(height=LINE_HEIGHT),
            max_lines=SETTINGS_HINT_MAX_LINES,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        self.operation_label = _section_label(labels.operation)
        self.table_label = _section_label(labels.times_table)
        self.operation_buttons = {
            operation: square_button(
                operation.symbol,
                layout.operation_button_size,
                layout.operation_font_size,
                on_click=ignoring_event(partial(self._toggle_operation, operation)),
            )
            for operation in OPERATIONS
        }
        self.table_buttons = {
            table: square_button(
                str(table),
                layout.table_button_size,
                layout.table_font_size,
                on_click=ignoring_event(partial(self._toggle_table, table)),
            )
            for table in TABLES
        }
        self._operation_row = ft.Row([*self.operation_buttons.values()], tight=True)
        table_buttons = list(self.table_buttons.values())
        self._table_rows = [
            ft.Row([*table_buttons[start : start + TABLES_PER_ROW]], tight=True)
            for start in range(0, len(TABLES), TABLES_PER_ROW)
        ]
        self.table_section = ft.Column(
            [self.table_label, *self._table_rows],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            tight=True,
        )
        self._play_label = ft.Text(labels.play, weight=ft.FontWeight.BOLD)
        self.play_button = ft.FilledButton(
            content=self._play_label,
            icon=ft.Icons.PLAY_ARROW,
            style=primary_button_style(),
            on_click=lambda _: on_play(self._settings),
        )
        self._best_of_label = _mode_label(labels.best_of)
        self.best_of_button = ft.FilledButton(
            content=self._best_of_label,
            icon=ft.Icons.EMOJI_EVENTS,
            style=best_of_button_style(),
            on_click=lambda _: on_best_of(self._settings),
        )
        self._hard_mode_label = _mode_label(labels.hard_mode)
        self.hard_mode_button = ft.FilledButton(
            content=self._hard_mode_label,
            icon=ft.Icons.TIMER,
            style=hard_mode_button_style(),
            on_click=lambda _: on_hard_mode(self._settings),
        )
        # Side by side: together as wide (and as tall) as the Play button.
        self._mode_row = ft.Row([self.best_of_button, self.hard_mode_button], tight=True)
        self.control = ft.Column(
            [
                self._title.control,
                self.hint,
                self.operation_label,
                self._operation_row,
                self.table_section,
                self.play_button,
                self._mode_row,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=SECTION_SPACING,
        )
        self.apply_layout(layout)

    @property
    def settings(self) -> GameSettings:
        return self._settings

    def apply_layout(self, layout: ScreenLayout) -> None:
        self._layout = layout
        self._title.apply_layout(layout)
        self.hint.size = layout.settings_hint_font_size
        self.hint.width = layout.board_width
        for label in (self.operation_label, self.table_label):
            label.size = layout.status_font_size
        self._operation_row.spacing = layout.cell_spacing
        for button in self.operation_buttons.values():
            button.width = button.height = layout.operation_button_size
        self.table_section.spacing = layout.cell_spacing
        for row in self._table_rows:
            row.spacing = layout.cell_spacing
        for button in self.table_buttons.values():
            button.width = button.height = layout.table_button_size
        self.play_button.width = layout.board_width
        self.play_button.height = layout.restart_height
        self._mode_row.spacing = layout.cell_spacing
        # Icons and margins grow with the screen, so the labels always fit.
        padding = mode_button_padding(layout.mode_button_padding)
        self.best_of_button.style = best_of_button_style(padding, layout.restart_font_size)
        self.hard_mode_button.style = hard_mode_button_style(padding, layout.restart_font_size)
        for button in (self.best_of_button, self.hard_mode_button):
            button.width = layout.mode_button_width
            button.height = layout.restart_height
        for label in (self._play_label, self._best_of_label, self._hard_mode_label):
            label.size = layout.restart_font_size
        self._show_selection()

    def _toggle_operation(self, operation: Operation) -> None:
        self._change(self._settings.toggle_operation(operation))

    def _toggle_table(self, table: int) -> None:
        self._change(self._settings.toggle_table(table))

    def _change(self, settings: GameSettings) -> None:
        self._settings = settings
        self._show_selection()
        self._refresh()

    def _show_selection(self) -> None:
        """Highlights the chosen options; tables only matter for × and ÷."""
        settings = self._settings
        for operation, button in self.operation_buttons.items():
            button.style = option_button_style(operation in settings.operations)
            button.content = square_label(operation.symbol, self._layout.operation_font_size)
        for table, button in self.table_buttons.items():
            button.style = option_button_style(table in settings.tables)
            button.content = square_label(str(table), self._layout.table_font_size)
        self.table_section.visible = settings.uses_tables


def _mode_label(text: str) -> ft.Text:
    # One line: the mode buttons are sized so that their labels fit.
    return ft.Text(text, weight=ft.FontWeight.BOLD, max_lines=1, no_wrap=True)


def _section_label(text: str) -> ft.Text:
    # Fixed line height and a single line: the layout relies on its height.
    return ft.Text(
        text,
        weight=ft.FontWeight.BOLD,
        color=SECTION_LABEL_COLOR,
        style=ft.TextStyle(height=LINE_HEIGHT),
        max_lines=1,
    )
