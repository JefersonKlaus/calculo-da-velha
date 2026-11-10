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
from .presenter import CellState, FeedbackMessage, StatusMessage, TimerState

AnswerHandler = Callable[[int], None]
ConfirmHandler = Callable[[], None]


class BoardDisplay(Protocol):
    def render(self, cells: Sequence[CellState]) -> None: ...


class StatusDisplay(Protocol):
    def show_status(self, message: StatusMessage) -> None: ...

    def show_feedback(self, message: FeedbackMessage | None) -> None:
        """Shows a red message below the status; ``None`` clears it."""
        ...


class QuestionPrompt(Protocol):
    def ask(self, question: Question, on_answer: AnswerHandler) -> None: ...

    def close(self) -> None:
        """Closes the question if it is still open (e.g. the time ran out)."""
        ...


class TimerDisplay(Protocol):
    def show_timers(self, timers: Sequence[TimerState]) -> None:
        """Shows the players' timers; an empty sequence hides them."""
        ...


class RestartOption(Protocol):
    def set_label(self, label: str) -> None: ...


class RestartConfirmation(Protocol):
    def confirm(self, on_confirm: ConfirmHandler) -> None:
        """Asks the player; calls ``on_confirm`` only if they agree."""
        ...


@dataclass(frozen=True)
class Screen:
    """The parts of the game screen the controller talks to."""

    board: BoardDisplay
    status: StatusDisplay
    prompt: QuestionPrompt
    restart: RestartOption
    confirm_restart: RestartConfirmation
    timers: TimerDisplay
