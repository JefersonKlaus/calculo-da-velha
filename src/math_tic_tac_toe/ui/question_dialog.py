"""Modal that shows the question and its answer choices."""

from __future__ import annotations

import flet as ft

from ..questions import Question
from .ports import AnswerHandler
from .square_button import square_button
from .styles import CHOICE_FONT_SIZE, CHOICE_SIZE, CHOICE_SPACING, DIALOG_INSET_PADDING


def build_question_dialog(
    question: Question,
    title: str,
    on_choice: AnswerHandler,
) -> ft.AlertDialog:
    """Builds the modal with one square button per answer choice."""
    choices = [
        square_button(
            str(choice),
            CHOICE_SIZE,
            CHOICE_FONT_SIZE,
            on_click=lambda _, selected=choice: on_choice(selected),
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
                ft.Row(choices, spacing=CHOICE_SPACING, tight=True),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
            tight=True,
        ),
    )


class QuestionDialog:
    """Opens the modal on the page and closes it once a choice is made."""

    def __init__(self, page: ft.Page, title: str) -> None:
        self._page = page
        self._title = title

    def ask(self, question: Question, on_answer: AnswerHandler) -> None:
        def choose(response: int) -> None:
            self._page.pop_dialog()
            on_answer(response)

        self._page.show_dialog(build_question_dialog(question, self._title, choose))
