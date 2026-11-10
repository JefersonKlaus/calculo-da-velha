"""Looks up and formats texts in a single language."""

from __future__ import annotations

import string
from collections.abc import Mapping
from dataclasses import dataclass

from .catalogs import CATALOGS
from .language import Language
from .text_key import TextKey


@dataclass(frozen=True)
class TextPiece:
    """Part of a translated text; ``field`` names the placeholder it filled
    (e.g. ``"player"``), or is ``None`` for the text around placeholders."""

    text: str
    field: str | None = None


class Translator:
    def __init__(self, language: Language, texts: Mapping[TextKey, str]) -> None:
        self.language = language
        self._texts = texts

    def text(self, key: TextKey, **values: object) -> str:
        return self._texts[key].format(**values)

    def pieces(self, key: TextKey, **values: object) -> list[TextPiece]:
        """The same text as ``text``, split so that each filled placeholder is
        its own piece (to show it differently, e.g. in another color)."""
        pieces = []
        for literal, field, _, _ in string.Formatter().parse(self._texts[key]):
            if literal:
                pieces.append(TextPiece(literal))
            if field is not None:
                pieces.append(TextPiece(str(values[field]), field))
        return pieces


def translator_for(language: Language) -> Translator:
    return Translator(language, CATALOGS[language])
