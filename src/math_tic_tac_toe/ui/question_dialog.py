"""Modal that shows the question, its answer choices and a cancel option.

Canceling only closes the modal: the game does not change, so the player
keeps the turn and can pick another cell (the cell keeps its question).
"""

from __future__ import annotations

from collections.abc import Callable
from functools import partial

import flet as ft

from ..questions import Question
from .events import ignoring_event
from .ports import AnswerHandler
from .square_button import square_button
from .styles import CHOICE_FONT_SIZE, CHOICE_SIZE, CHOICE_SPACING, DIALOG_INSET_PADDING


def build_question_dialog(
    question: Question,
    title: str,
    on_choice: AnswerHandler,
    cancel_label: str,
    on_cancel: Callable[[], None],
) -> ft.AlertDialog:
    """Builds the modal with one square button per answer choice and a
    cancel button below them."""
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
        title=ft.Text(title, text_align=ft.TextAlign.CENTER),
        content=ft.Column(
            [
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
    player cancels, or the game closes it (hard mode: the time ran out)."""

    def __init__(self, page: ft.Page, title: str, cancel_label: str) -> None:
        self._page = page
        self._title = title
        self._cancel_label = cancel_label
        self._is_open = False

    def ask(self, question: Question, on_answer: AnswerHandler) -> None:
        def choose(response: int) -> None:
            self.close()
            on_answer(response)

        self._page.show_dialog(
            build_question_dialog(question, self._title, choose, self._cancel_label, self.close)
        )
        self._is_open = True

    def close(self) -> None:
        if self._is_open:
            self._is_open = False
            self._page.pop_dialog()
