import string

import pytest

from math_tic_tac_toe.i18n import Language, TextKey, language_from_code, translator_for
from math_tic_tac_toe.i18n.catalogs import CATALOGS


@pytest.mark.parametrize("code", ["pt", "pt-BR", "pt_BR", "pt-PT", "PT", " pt-ao "])
def test_portuguese_codes_map_to_portuguese(code: str) -> None:
    assert language_from_code(code) is Language.PORTUGUESE


@pytest.mark.parametrize("code", ["en", "en-US", "en_GB"])
def test_english_codes_map_to_english(code: str) -> None:
    assert language_from_code(code) is Language.ENGLISH


@pytest.mark.parametrize("code", ["es", "fr-FR", "de", "und", "", None, "ptx", "p"])
def test_any_other_language_falls_back_to_english(code: str | None) -> None:
    assert language_from_code(code) is Language.ENGLISH


def test_every_language_has_a_catalog() -> None:
    assert set(CATALOGS) == set(Language)


@pytest.mark.parametrize("language", list(Language))
def test_every_catalog_translates_every_key(language: Language) -> None:
    assert set(CATALOGS[language]) == set(TextKey)


@pytest.mark.parametrize("key", list(TextKey))
def test_every_language_uses_the_same_placeholders(key: TextKey) -> None:
    def placeholders(text: str) -> set[str]:
        return {name for _, name, _, _ in string.Formatter().parse(text) if name}

    expected = placeholders(CATALOGS[Language.ENGLISH][key])
    for catalog in CATALOGS.values():
        assert placeholders(catalog[key]) == expected


def test_translator_formats_values() -> None:
    assert translator_for(Language.ENGLISH).text(TextKey.TURN, player="O") == "O's turn"
    assert translator_for(Language.PORTUGUESE).text(TextKey.TURN, player="O") == "Vez de O"
