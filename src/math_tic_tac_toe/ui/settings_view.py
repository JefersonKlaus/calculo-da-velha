"""Settings screen: choose the operations and, for multiplication and
division, the times tables. The play button starts a match with them.

Everything starts selected; each tap selects or unselects one option.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import flet as ft

from ..settings import OPERATIONS, TABLES, GameSettings
from .layout import LINE_HEIGHT, SECTION_SPACING, TABLES_PER_ROW, ScreenLayout
from .square_button import square_button, square_label
from .styles import option_button_style, square_button_style
from .title_view import TitleView


@dataclass(frozen=True)
class SettingsLabels:
    title: str
    operation: str
    times_table: str
    play: str


class SettingsView:
    def __init__(
        self,
        labels: SettingsLabels,
        settings: GameSettings,
        on_play: Callable[[GameSettings], None],
        refresh: Callable[[], None],
        layout: ScreenLayout,
    ) -> None:
        self._settings = settings
        self._refresh = refresh
        self._layout = layout
        self._title = TitleView(labels.title, layout)
        self.operation_label = _section_label(labels.operation)
        self.table_label = _section_label(labels.times_table)
        self.operation_buttons = {
            operation: square_button(
                operation.symbol,
                layout.operation_button_size,
                layout.operation_font_size,
                on_click=lambda _, op=operation: self._change(self._settings.toggle_operation(op)),
            )
            for operation in OPERATIONS
        }
        self.table_buttons = {
            table: square_button(
                str(table),
                layout.table_button_size,
                layout.table_font_size,
                on_click=lambda _, number=table: self._change(self._settings.toggle_table(number)),
            )
            for table in TABLES
        }
        self._operation_row = ft.Row(list(self.operation_buttons.values()), tight=True)
        self._table_rows = [
            ft.Row(list(self.table_buttons.values())[start:start + TABLES_PER_ROW], tight=True)
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
            style=square_button_style(),
            on_click=lambda _: on_play(self._settings),
        )
        self.control = ft.Column(
            [
                self._title.control,
                self.operation_label,
                self._operation_row,
                self.table_section,
                self.play_button,
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
        self._play_label.size = layout.restart_font_size
        self._show_selection()

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


def _section_label(text: str) -> ft.Text:
    # Fixed line height and a single line: the layout relies on its height.
    return ft.Text(
        text,
        weight=ft.FontWeight.BOLD,
        style=ft.TextStyle(height=LINE_HEIGHT),
        max_lines=1,
    )
