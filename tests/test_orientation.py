import asyncio

import flet as ft
import pytest

from math_tic_tac_toe.ui.orientation import lock_portrait
from support import FakePage


def lock(page: FakePage) -> None:
    asyncio.run(lock_portrait(page))  # type: ignore[arg-type]


@pytest.mark.parametrize("platform", [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS])
def test_phones_are_locked_in_portrait(platform: ft.PagePlatform) -> None:
    page = FakePage(platform=platform)
    lock(page)
    assert page.orientations == [ft.DeviceOrientation.PORTRAIT_UP]


@pytest.mark.parametrize(
    "platform",
    [ft.PagePlatform.WINDOWS, ft.PagePlatform.MACOS, ft.PagePlatform.LINUX, None],
)
def test_desktop_preview_is_left_alone(platform: ft.PagePlatform | None) -> None:
    page = FakePage(platform=platform)
    lock(page)  # would raise like Flet if it tried to lock
    assert page.orientations is None


def test_web_preview_is_left_alone_even_on_a_phone_browser() -> None:
    page = FakePage(platform=ft.PagePlatform.ANDROID, web=True)
    lock(page)
    assert page.orientations is None
