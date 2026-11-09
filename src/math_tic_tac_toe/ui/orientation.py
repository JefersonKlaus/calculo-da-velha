"""Locks the app in portrait (vertical) orientation on phones."""

from __future__ import annotations

import flet as ft

PORTRAIT_ONLY = [ft.DeviceOrientation.PORTRAIT_UP]


async def lock_portrait(page: ft.Page) -> None:
    """Keeps the app vertical, even if the phone is rotated.

    Only phones and tablets support this; on the web or desktop preview it
    does nothing (Flet raises an error there).
    """
    if page.web or page.platform is None or not page.platform.is_mobile():
        return
    await page.set_allowed_device_orientations(PORTRAIT_ONLY)
