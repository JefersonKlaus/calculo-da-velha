"""Modal that asks the player to confirm before a match in progress is
thrown away: by the restart button, or by leaving for the settings."""

from __future__ import annotations

from dataclasses import dataclass

import flet as ft

from .ports import ConfirmHandler
from .styles import SURFACE_COLOR, dialog_shape, primary_button_style


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
    """Modal (a navy card) with a question, a short explanation, and two
    buttons: cancel (plain) and confirm (the pink pill, the one that acts)."""
    return ft.AlertDialog(
        modal=True,
        bgcolor=SURFACE_COLOR,
        shape=dialog_shape(),
        title=ft.Text(labels.title),
        content=ft.Text(labels.message),
        actions=[
            ft.TextButton(content=labels.cancel, on_click=lambda _: on_cancel()),
            ft.FilledButton(
                content=labels.confirm,
                style=primary_button_style(),
                on_click=lambda _: on_confirm(),
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )


class ConfirmDialog:
    """Opens the modal on the page; either button closes it.

    The confirmed action only runs once the dialog has finished closing, as
    it may switch screens (leaving for the settings): Flutter keeps a dialog
    attached to the screen it was opened on, so switching while it is still
    closing would leave it behind, stuck open.
    """

    def __init__(self, page: ft.Page, labels: ConfirmLabels) -> None:
        self._page = page
        self._labels = labels

    def confirm(self, on_confirm: ConfirmHandler) -> None:
        confirmed: list[bool] = []  # set once "confirm" is tapped

        def cancel() -> None:
            self._page.pop_dialog()

        def accept() -> None:
            if confirmed:
                return  # a second tap while the dialog is closing
            confirmed.append(True)
            self._page.pop_dialog()

        def closed() -> None:
            # The phone reports that the dialog is gone: now it is safe to act.
            if confirmed:
                on_confirm()

        dialog = build_confirm_dialog(self._labels, cancel, accept)
        dialog.on_dismiss = lambda _: closed()
        self._page.show_dialog(dialog)
