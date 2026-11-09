"""Contracts the controller expects from the interface.

The controller depends on these abstractions instead of concrete Flet
classes (dependency inversion principle). This lets it be tested with fake
implementations, and the screens can change without touching it.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol

from ..questions import Question
from .presenter import CellState, FeedbackMessage, StatusMessage

AnswerHandler = Callable[[int], None]


class BoardDisplay(Protocol):
    def render(self, cells: Sequence[CellState]) -> None: ...


class StatusDisplay(Protocol):
    def show_status(self, message: StatusMessage) -> None: ...

    def show_feedback(self, message: FeedbackMessage | None) -> None: ...


class QuestionPrompt(Protocol):
    def ask(self, question: Question, on_answer: AnswerHandler) -> None: ...


class RestartOption(Protocol):
    def set_visible(self, visible: bool) -> None: ...


@dataclass(frozen=True)
class Screen:
    """The parts of the game screen the controller talks to."""

    board: BoardDisplay
    status: StatusDisplay
    prompt: QuestionPrompt
    restart: RestartOption
