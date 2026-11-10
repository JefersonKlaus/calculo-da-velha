"""3x3 board of square buttons that fills the screen width."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from functools import partial

import flet as ft

from ..game import Game, Position
from .events import ignoring_event
from .layout import BOARD_SIDE, ScreenLayout
from .presenter import CellState
from .square_button import square_button, square_label
from .styles import WINNING_MARK_COLOR, player_color, square_button_style, winning_button_style


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
            button.content = square_label(state.label, *self._label_look(state))
            button.disabled = not state.enabled
            button.style = winning_button_style() if state.highlighted else square_button_style()

    def apply_layout(self, layout: ScreenLayout) -> None:
        self._layout = layout
        self.control.spacing = layout.cell_spacing
        for row in self._rows:
            row.spacing = layout.cell_spacing
        for button in self.cells:
            button.width = button.height = layout.cell_size
        if self._states:
            self.render(self._states)  # labels use font sizes from the layout

    def _label_look(self, state: CellState) -> tuple[int, str | None]:
        """Font size and color: questions in the default look, marks in the
        player's color (dark gold on the gold winning cells)."""
        if state.mark is None:
            return self._layout.prompt_font_size, None
        color = WINNING_MARK_COLOR if state.highlighted else player_color(state.mark)
        return self._layout.mark_font_size, color
