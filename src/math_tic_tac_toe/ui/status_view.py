"""Texts showing whose turn it is (in that player's color, with the seconds
left on the turn next to it) or, once the match is won, the winner in gold;
and, below it in red, a wrong answer or a player
out of time (that player's symbol keeps their color). A point scored in a
best of N is good news: it shows in light text."""

from __future__ import annotations

import flet as ft

from .layout import LINE_HEIGHT, MESSAGE_SPACING, ScreenLayout
from .presenter import FeedbackMessage, MessagePart, StatusMessage, TurnTime
from .styles import ALERT_COLOR, GOOD_NEWS_COLOR, WINNER_MESSAGE_COLOR, player_color
from .turn_time_view import TurnTimeView


class StatusView:
    def __init__(self, layout: ScreenLayout) -> None:
        # Fixed line height: the layout relies on knowing these heights.
        text_style = ft.TextStyle(height=LINE_HEIGHT)
        self._status = ft.Text(weight=ft.FontWeight.BOLD, style=text_style)
        self.turn_time = TurnTimeView(layout.status_font_size, LINE_HEIGHT)
        self.turn_time.show(None)
        # One line: whose turn it is, then its seconds.
        self._status_line = ft.Row(
            [self._status, self.turn_time.control],
            spacing=layout.cell_spacing,
            tight=True,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self._feedback = ft.Text(weight=ft.FontWeight.BOLD, style=text_style, color=ALERT_COLOR)
        self.control = ft.Column(
            [self._status_line, self._feedback],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=MESSAGE_SPACING,
            tight=True,
        )
        self.apply_layout(layout)

    def apply_layout(self, layout: ScreenLayout) -> None:
        self._status.size = layout.status_font_size
        self.turn_time.resize(layout.status_font_size)
        self._status_line.spacing = layout.cell_spacing
        self._feedback.size = layout.feedback_font_size

    def show_status(self, message: StatusMessage) -> None:
        """Whose turn it is, in their color; the winner's message in gold,
        like the winning cells."""
        self._status.value = message.text
        self._status.color = WINNER_MESSAGE_COLOR if message.won else player_color(message.player)

    def show_turn_time(self, time: TurnTime | None) -> None:
        """The seconds left on the turn, next to whose turn it is; hidden
        when no turn is running (e.g. the match is over)."""
        self.turn_time.show(time)

    def show_feedback(self, message: FeedbackMessage | None) -> None:
        """Shows a red message (wrong answer, out of time), or a light one if
        it is not an alert (a point scored), in which a player's symbol keeps
        that player's color; ``None`` clears it."""
        self._feedback.value = ""
        if message is None:
            self._feedback.spans = []
            return
        text_color = ALERT_COLOR if message.alert else GOOD_NEWS_COLOR
        self._feedback.spans = [_span(part, text_color) for part in message.parts]


def _span(part: MessagePart, text_color: str) -> ft.TextSpan:
    color = player_color(part.player) if part.player else text_color
    return ft.TextSpan(part.text, style=ft.TextStyle(color=color))
