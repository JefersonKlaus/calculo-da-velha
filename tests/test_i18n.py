import string

import pytest

from math_tic_tac_toe.i18n import (
    Language,
    TextKey,
    TextPiece,
    language_from_code,
    translator_for,
)
from math_tic_tac_toe.i18n.catalogs import CATALOGS


@pytest.mark.parametrize(
    ("code", "language"),
    [
        ("pt", Language.PORTUGUESE),
        ("pt-BR", Language.PORTUGUESE),
        ("pt_BR", Language.PORTUGUESE),
        (" PT-ao ", Language.PORTUGUESE),  # any case, spaces, any country
        ("en-US", Language.ENGLISH),
        ("es", Language.ENGLISH),  # any other language falls back to English
        ("ptx", Language.ENGLISH),  # starts like "pt" but is not Portuguese
        ("", Language.ENGLISH),
        (None, Language.ENGLISH),
    ],
)
def test_language_from_code(code: str | None, language: Language) -> None:
    assert language_from_code(code) is language


def test_every_language_translates_every_text() -> None:
    assert set(CATALOGS) == set(Language)
    for language, catalog in CATALOGS.items():
        assert set(catalog) == set(TextKey), language


def test_every_language_uses_the_same_placeholders() -> None:
    def placeholders(text: str) -> set[str]:
        return {name for _, name, _, _ in string.Formatter().parse(text) if name}

    for key in TextKey:
        expected = placeholders(CATALOGS[Language.ENGLISH][key])
        for language, catalog in CATALOGS.items():
            assert placeholders(catalog[key]) == expected, (language, key)


def test_translator_formats_values() -> None:
    assert translator_for(Language.ENGLISH).text(TextKey.TURN, player="O") == "O's turn"
    assert translator_for(Language.PORTUGUESE).text(TextKey.TURN, player="O") == "Vez de O"


def test_pieces_rebuild_the_same_text() -> None:
    values = {"player": "O"}
    for language in Language:
        translator = translator_for(language)
        for key in TextKey:
            pieces = translator.pieces(key, **values)
            rebuilt = "".join(piece.text for piece in pieces)
            assert rebuilt == translator.text(key, **values), (language, key)


def test_pieces_mark_the_filled_placeholders() -> None:
    pieces = translator_for(Language.PORTUGUESE).pieces(TextKey.RAN_OUT_OF_TIME, player="X")
    assert pieces == [TextPiece("X", "player"), TextPiece(" ficou sem tempo.")]
    pieces = translator_for(Language.ENGLISH).pieces(TextKey.TURN, player="O")
    assert pieces == [TextPiece("O", "player"), TextPiece("'s turn")]
