"""Looks up and formats texts in a single language."""

from __future__ import annotations

from collections.abc import Mapping

from .catalogs import CATALOGS
from .language import Language
from .text_key import TextKey


class Translator:
    def __init__(self, language: Language, texts: Mapping[TextKey, str]) -> None:
        self.language = language
        self._texts = texts

    def text(self, key: TextKey, **values: object) -> str:
        return self._texts[key].format(**values)


def translator_for(language: Language) -> Translator:
    return Translator(language, CATALOGS[language])
