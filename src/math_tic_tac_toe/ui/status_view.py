"""Texts showing whose turn it is and feedback on the last move."""

from __future__ import annotations

import flet as ft

from .layout import LINE_HEIGHT, MESSAGE_SPACING, ScreenLayout
from .presenter import FeedbackMessage, StatusMessage
from .styles import feedback_color, player_color


class StatusView:
    def __init__(self, layout: ScreenLayout) -> None:
        # Fixed line height: the layout relies on knowing these heights.
        text_style = ft.TextStyle(height=LINE_HEIGHT)
        self._status = ft.Text(weight=ft.FontWeight.BOLD, style=text_style)
        self._feedback = ft.Text(weight=ft.FontWeight.BOLD, style=text_style)
        self.control = ft.Column(
            [self._status, self._feedback],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=MESSAGE_SPACING,
            tight=True,
        )
        self.apply_layout(layout)

    def apply_layout(self, layout: ScreenLayout) -> None:
        self._status.size = layout.status_font_size
        self._feedback.size = layout.feedback_font_size

    def show_status(self, message: StatusMessage) -> None:
        self._status.value = message.text
        self._status.color = player_color(message.player)

    def show_feedback(self, message: FeedbackMessage | None) -> None:
        """Shows the result of the last answer; ``None`` clears it."""
        self._feedback.value = message.text if message else ""
        self._feedback.color = feedback_color(message.correct) if message else None
