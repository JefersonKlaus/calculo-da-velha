"""Modal that asks the player to confirm before a match in progress is
thrown away by the restart button."""

from __future__ import annotations

from dataclasses import dataclass

import flet as ft

from .ports import ConfirmHandler


@dataclass(frozen=True)
class ConfirmLabels:
    title: str
    message: str
    cancel: str
    confirm: str


def build_confirm_dialog(
    labels: ConfirmLabels,
    on_cancel: ConfirmHandler,
    on_confirm: ConfirmHandler,
) -> ft.AlertDialog:
    """Modal with a question, a short explanation, and two buttons: cancel
    (plain) and confirm (filled, the one that acts)."""
    return ft.AlertDialog(
        modal=True,
        title=ft.Text(labels.title),
        content=ft.Text(labels.message),
        actions=[
            ft.TextButton(content=labels.cancel, on_click=lambda _: on_cancel()),
            ft.FilledButton(content=labels.confirm, on_click=lambda _: on_confirm()),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )


class ConfirmDialog:
    """Opens the modal on the page; either button closes it."""

    def __init__(self, page: ft.Page, labels: ConfirmLabels) -> None:
        self._page = page
        self._labels = labels

    def confirm(self, on_confirm: ConfirmHandler) -> None:
        def cancel() -> None:
            self._page.pop_dialog()

        def accept() -> None:
            self._page.pop_dialog()
            on_confirm()

        self._page.show_dialog(build_confirm_dialog(self._labels, cancel, accept))
