"""Modal that shows the question, its answer choices, the seconds left on
the turn and a cancel option.

Canceling only closes the modal: the game does not change, so the player
keeps the turn (and its running time) and can pick another cell (the cell
keeps its question). When the turn's time runs out, the game closes the
modal (it counts as wrong).
"""

from __future__ import annotations

from collections.abc import Callable
from functools import partial

import flet as ft

from ..questions import Question
from .events import ignoring_event
from .ports import AnswerHandler
from .presenter import TurnTime
from .square_button import square_button
from .styles import (
    CHOICE_FONT_SIZE,
    CHOICE_SIZE,
    CHOICE_SPACING,
    DIALOG_INSET_PADDING,
    SURFACE_COLOR,
    TURN_TIME_FONT_SIZE,
    dialog_shape,
)
from .turn_time_view import TurnTimeView


def build_question_dialog(
    question: Question,
    title: str,
    on_choice: AnswerHandler,
    cancel_label: str,
    on_cancel: Callable[[], None],
    turn_time: ft.Control | None = None,
) -> ft.AlertDialog:
    """Builds the modal (a navy card) with the seconds left on the turn (if
    given), the question, one square button per answer choice and a cancel
    button below them."""
    choices = [
        square_button(
            str(choice),
            CHOICE_SIZE,
            CHOICE_FONT_SIZE,
            on_click=ignoring_event(partial(on_choice, choice)),
        )
        for choice in question.choices
    ]
    return ft.AlertDialog(
        modal=True,
        inset_padding=DIALOG_INSET_PADDING,
        bgcolor=SURFACE_COLOR,
        shape=dialog_shape(),
        title=ft.Text(title, text_align=ft.TextAlign.CENTER),
        content=ft.Column(
            [
                *([turn_time] if turn_time else []),
                ft.Text(question.prompt, size=32, weight=ft.FontWeight.BOLD),
                ft.Row([*choices], spacing=CHOICE_SPACING, tight=True),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
            tight=True,
        ),
        actions=[ft.TextButton(content=cancel_label, on_click=lambda _: on_cancel())],
        actions_alignment=ft.MainAxisAlignment.CENTER,
    )


class QuestionDialog:
    """Opens the modal on the page and closes it once a choice is made, the
    player cancels, or the game closes it (the turn's time, or the hard mode
    time, ran out)."""

    def __init__(self, page: ft.Page, title: str, cancel_label: str) -> None:
        self._page = page
        self._title = title
        self._cancel_label = cancel_label
        self._is_open = False
        self._turn_time = TurnTimeView(TURN_TIME_FONT_SIZE)

    def ask(
        self, question: Question, on_answer: AnswerHandler, on_cancel: Callable[[], None]
    ) -> None:
        def choose(response: int) -> None:
            self.close()
            on_answer(response)

        def cancel() -> None:
            self.close()
            on_cancel()

        self._turn_time = TurnTimeView(TURN_TIME_FONT_SIZE)
        self._page.show_dialog(
            build_question_dialog(
                question,
                self._title,
                choose,
                self._cancel_label,
                cancel,
                self._turn_time.control,
            )
        )
        self._is_open = True

    def show_time(self, time: TurnTime) -> None:
        self._turn_time.show(time)

    def close(self) -> None:
        if self._is_open:
            self._is_open = False
            self._page.pop_dialog()
