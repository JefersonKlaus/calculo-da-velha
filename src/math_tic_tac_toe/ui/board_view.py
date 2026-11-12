"""3x3 board of square buttons that fills the screen width.

Cells are navy tiles; a played cell is outlined in its player's color and the
winning line turns gold. In a best of N, a played cell also shows, very small
below its mark and in its mark's color, the seconds left (counting down)
before it is open again; open cells show none."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from functools import partial

import flet as ft

from ..game import Game, Position
from .events import ignoring_event
from .layout import BOARD_SIDE, ScreenLayout
from .presenter import CellState
from .square_button import square_button, square_label
from .styles import (
    WINNING_MARK_COLOR,
    cell_button_style,
    player_color,
    winning_button_style,
)


class BoardView:
    def __init__(self, on_select: Callable[[Position], None], layout: ScreenLayout) -> None:
        self._layout = layout
        self._states: list[CellState] = []
        self.cells = [
            square_button(
                "",
                layout.cell_size,
                layout.prompt_font_size,
                on_click=ignoring_event(partial(on_select, position)),
                style=cell_button_style(),
            )
            for position in range(Game.BOARD_SIZE)
        ]
        self._rows = [
            ft.Row([*self.cells[start : start + BOARD_SIDE]], tight=True)
            for start in range(0, Game.BOARD_SIZE, BOARD_SIDE)
        ]
        self.control = ft.Column([*self._rows], tight=True)
        self.apply_layout(layout)

    def render(self, cells: Sequence[CellState]) -> None:
        self._states = list(cells)
        for button, state in zip(self.cells, self._states, strict=True):
            button.content = self._content(state)
            button.disabled = not state.enabled
            button.style = (
                winning_button_style() if state.highlighted else cell_button_style(state.mark)
            )

    def apply_layout(self, layout: ScreenLayout) -> None:
        self._layout = layout
        self.control.spacing = layout.cell_spacing
        for row in self._rows:
            row.spacing = layout.cell_spacing
        for button in self.cells:
            button.width = button.height = layout.cell_size
        if self._states:
            self.render(self._states)  # labels use font sizes from the layout

    def _content(self, state: CellState) -> ft.Control:
        """The question or the mark; in a best of N, a played cell's
        countdown goes below its mark, in the mark's color."""
        label = square_label(state.label, *self._label_look(state))
        if state.seconds is None:
            return label
        countdown = ft.Text(
            str(state.seconds),
            size=self._layout.cell_timer_font_size,
            color=player_color(state.mark),
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
            style=ft.TextStyle(height=1),
        )
        return ft.Column(
            [label, countdown],
            spacing=0,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        )

    def _label_look(self, state: CellState) -> tuple[int, str | None]:
        """Font size and color: questions in the cell's text color (muted once
        the match is over), marks in the player's color (dark navy on the gold
        winning cells)."""
        if state.mark is None:
            return self._layout.prompt_font_size, None
        color = WINNING_MARK_COLOR if state.highlighted else player_color(state.mark)
        return self._layout.mark_font_size, color
