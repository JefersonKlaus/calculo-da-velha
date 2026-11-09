"""Internationalization: supported languages and translated texts.

Nothing in this package depends on Flet, so it can be tested in isolation.
To add a language: add it to ``Language``, create a catalog in ``catalogs/``
and register it in ``catalogs/__init__.py``.
"""

from .language import DEFAULT_LANGUAGE, Language, language_from_code
from .text_key import TextKey
from .translator import Translator, translator_for

__all__ = [
    "DEFAULT_LANGUAGE",
    "Language",
    "TextKey",
    "Translator",
    "language_from_code",
    "translator_for",
]
