"""Factory of the square button used on the board and for answer choices."""

from __future__ import annotations

import flet as ft

from .events import ClickHandler
from .styles import square_button_style


def square_button(
    label: str,
    size: int,
    font_size: int,
    on_click: ClickHandler,
    style: ft.ButtonStyle | None = None,
) -> ft.FilledButton:
    """Square button with rounded corners; a raised navy tile unless another
    ``style`` is given (board cells, settings options)."""
    return ft.FilledButton(
        content=square_label(label, font_size),
        width=size,
        height=size,
        style=style or square_button_style(),
        on_click=on_click,
    )


def square_label(label: str, font_size: int, color: str | None = None) -> ft.Text:
    return ft.Text(
        label,
        size=font_size,
        color=color,
        weight=ft.FontWeight.BOLD,
        text_align=ft.TextAlign.CENTER,
    )
