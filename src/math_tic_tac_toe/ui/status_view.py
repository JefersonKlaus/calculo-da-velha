"""Texts showing whose turn it is (in that player's color) and, below it in
red, a wrong answer or a player out of time (that player's symbol keeps their
color)."""

from __future__ import annotations

import flet as ft

from .layout import LINE_HEIGHT, MESSAGE_SPACING, ScreenLayout
from .presenter import FeedbackMessage, MessagePart, StatusMessage
from .styles import ALERT_COLOR, player_color


class StatusView:
    def __init__(self, layout: ScreenLayout) -> None:
        # Fixed line height: the layout relies on knowing these heights.
        text_style = ft.TextStyle(height=LINE_HEIGHT)
        self._status = ft.Text(weight=ft.FontWeight.BOLD, style=text_style)
        self._feedback = ft.Text(weight=ft.FontWeight.BOLD, style=text_style, color=ALERT_COLOR)
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
        """Shows a red message (wrong answer, out of time) in which a player's
        symbol keeps that player's color; ``None`` clears it."""
        self._feedback.value = ""
        self._feedback.spans = [_span(part) for part in message.parts] if message else []


def _span(part: MessagePart) -> ft.TextSpan:
    color = player_color(part.player) if part.player else ALERT_COLOR
    return ft.TextSpan(part.text, style=ft.TextStyle(color=color))
