"""Builds the app's screens (Flet views) with the same frame: margins,
centered content kept clear of the phone's status bar and notch, and
scrolling as a safety net for unusual screens."""

from __future__ import annotations

import flet as ft

from .layout import PAGE_PADDING, SECTION_SPACING

SETTINGS_ROUTE = "/"
GAME_ROUTE = "/game"


def screen(route: str, *controls: ft.Control) -> ft.View:
    return ft.View(
        route=route,
        controls=[
            ft.SafeArea(
                content=ft.Column(
                    list(controls),
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=SECTION_SPACING,
                ),
            ),
        ],
        padding=PAGE_PADDING,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
