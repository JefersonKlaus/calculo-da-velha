"""Supported languages and how a device language code maps to one of them."""

from __future__ import annotations

from enum import Enum


class Language(str, Enum):
    ENGLISH = "en"
    PORTUGUESE = "pt"


DEFAULT_LANGUAGE = Language.ENGLISH


def language_from_code(code: str | None) -> Language:
    """Maps a locale code such as ``"pt"``, ``"pt-BR"`` or ``"en_US"``.

    Only the language part matters, so every Portuguese variant (Brazil,
    Portugal, ...) maps to Portuguese. Anything unsupported or missing falls
    back to ``DEFAULT_LANGUAGE``.
    """
    primary = (code or "").replace("_", "-").split("-")[0].strip().lower()
    for language in Language:
        if language.value == primary:
            return language
    return DEFAULT_LANGUAGE
