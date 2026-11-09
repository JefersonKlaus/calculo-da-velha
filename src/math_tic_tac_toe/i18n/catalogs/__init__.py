"""Registry of the text catalog of each supported language."""

from __future__ import annotations

from collections.abc import Mapping

from ..language import Language
from ..text_key import TextKey
from . import english, portuguese

Catalog = Mapping[TextKey, str]

CATALOGS: Mapping[Language, Catalog] = {
    Language.ENGLISH: english.TEXTS,
    Language.PORTUGUESE: portuguese.TEXTS,
}
