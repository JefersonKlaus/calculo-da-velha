"""Detects the language configured on the device running the app."""

from __future__ import annotations

import logging

import flet as ft

from ..i18n import DEFAULT_LANGUAGE, Language, language_from_code

logger = logging.getLogger(__name__)


async def detect_device_language(page: ft.Page) -> Language:
    """Returns the device's primary language, or the default one.

    Works the same on Android, iOS, desktop and web: Flet reports the locales
    configured on the device, ordered by preference.
    """
    try:
        info = await page.get_device_info()
    except Exception:  # The app must still start if the platform can't tell.
        logger.warning("Could not read the device language.", exc_info=True)
        return DEFAULT_LANGUAGE
    if info is None or not info.locales:
        return DEFAULT_LANGUAGE
    return language_from_code(info.locales[0].language_code)
