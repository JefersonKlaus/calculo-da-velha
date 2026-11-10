import flet as ft

from math_tic_tac_toe.ui.layout import ScreenLayout, ScreenSize, layout_for_screen
from math_tic_tac_toe.ui.responsive import ResponsiveLayout, screen_size_of
from tests.support import FakePage


class FakeView:
    def __init__(self) -> None:
        self.layouts: list[ScreenLayout] = []

    def apply_layout(self, layout: ScreenLayout) -> None:
        self.layouts.append(layout)


def test_fit_resizes_every_view_and_redraws() -> None:
    views = [FakeView(), FakeView()]
    refreshes: list[None] = []
    responsive = ResponsiveLayout(views, refresh=lambda: refreshes.append(None))

    screen = ScreenSize(800, 1280)
    layout = responsive.fit(screen)

    assert layout == layout_for_screen(screen)
    assert [view.layouts for view in views] == [[layout], [layout]]
    assert refreshes == [None]


def test_screen_size_is_read_from_the_page() -> None:
    page = FakePage(width=412, height=915, top_inset=24, bottom_inset=48)
    assert screen_size_of(page.as_page()) == ScreenSize(412, 915, top_inset=24, bottom_inset=48)


def test_event_values_take_precedence_over_the_page() -> None:
    page = FakePage(width=412, height=915, top_inset=24, bottom_inset=48)
    screen = screen_size_of(
        page.as_page(),
        width=1280,
        height=720,
        insets=ft.Padding(top=0, bottom=0),
    )
    assert screen == ScreenSize(1280, 720, top_inset=0, bottom_inset=0)
