import asyncio

import flet as ft

from math_tic_tac_toe.i18n import Language
from math_tic_tac_toe.ui.device_language import detect_device_language
from support import FakeDeviceInfo, FakePage, device


def detect(page: FakePage) -> Language:
    return asyncio.run(detect_device_language(page))  # type: ignore[arg-type]


def test_portuguese_device_uses_portuguese() -> None:
    page = FakePage(FakeDeviceInfo([ft.Locale("pt", "BR"), ft.Locale("en", "US")]))
    assert detect(page) is Language.PORTUGUESE


def test_english_device_uses_english() -> None:
    assert detect(FakePage(device("en", "US"))) is Language.ENGLISH


def test_other_languages_use_english() -> None:
    assert detect(FakePage(device("es", "ES"))) is Language.ENGLISH


def test_only_the_primary_language_counts() -> None:
    page = FakePage(FakeDeviceInfo([ft.Locale("fr", "FR"), ft.Locale("pt", "BR")]))
    assert detect(page) is Language.ENGLISH


def test_missing_information_uses_english() -> None:
    assert detect(FakePage(None)) is Language.ENGLISH
    assert detect(FakePage(FakeDeviceInfo([]))) is Language.ENGLISH


def test_platform_error_uses_english() -> None:
    assert detect(FakePage(error=TimeoutError())) is Language.ENGLISH
