"""Factory of the square button used on the board and for answer choices."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import flet as ft

from .styles import square_button_style

ClickHandler = Callable[[Any], None]


def square_button(label: str, size: int, font_size: int, on_click: ClickHandler) -> ft.FilledButton:
    return ft.FilledButton(
        content=square_label(label, font_size),
        width=size,
        height=size,
        style=square_button_style(),
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
