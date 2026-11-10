"""Builds the app: creates the screens and wires them together.

The app is started by ``src/main.py`` (used by ``flet run`` and ``flet build``).
It opens on the settings screen; "Play" starts a match on the game screen, and
"Hard mode" starts one where each player has a limited time (a chess clock).
"""

from __future__ import annotations

import flet as ft

from .clock import ChessClock
from .game import Game
from .i18n import TextKey, translator_for
from .settings import DEFAULT_SETTINGS, GameSettings
from .ui.board_view import BoardView
from .ui.confirm_dialog import ConfirmDialog, ConfirmLabels
from .ui.controller import GameController
from .ui.device_language import detect_device_language
from .ui.game_header import GameHeader
from .ui.hard_mode_dialog import HardModeDialog, HardModeLabels
from .ui.layout import layout_for_screen
from .ui.navigator import ScreenNavigator
from .ui.orientation import lock_portrait
from .ui.ports import Screen
from .ui.presenter import GamePresenter
from .ui.question_dialog import QuestionDialog
from .ui.responsive import ResponsiveLayout, screen_size_of
from .ui.restart_button import RestartButton
from .ui.screens import GAME_ROUTE, SETTINGS_ROUTE, screen
from .ui.settings_view import SettingsLabels, SettingsView
from .ui.status_view import StatusView
from .ui.styles import app_theme
from .ui.ticker import tick_forever
from .ui.timers_view import TimersView


async def main(page: ft.Page) -> None:
    await lock_portrait(page)
    translator = translator_for(await detect_device_language(page))
    text = translator.text
    page.title = text(TextKey.APP_TITLE)
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = app_theme()
    layout = layout_for_screen(screen_size_of(page))
    refresh = page.update

    # Views only forward taps; the controller and the navigator decide.
    header = GameHeader(
        text(TextKey.APP_TITLE),
        text(TextKey.OPEN_SETTINGS),
        on_open_settings=lambda: navigator.show_settings(),
        layout=layout,
    )
    timers = TimersView(layout)
    status = StatusView(layout)
    board = BoardView(on_select=lambda position: controller.select_cell(position), layout=layout)
    restart = RestartButton(on_restart=lambda: controller.request_restart(), layout=layout)
    controller = GameController(
        new_game=Game.with_settings,
        settings=DEFAULT_SETTINGS,
        presenter=GamePresenter(translator),
        screen=Screen(
            board=board,
            status=status,
            prompt=QuestionDialog(page, text(TextKey.SOLVE_QUESTION), text(TextKey.CANCEL)),
            restart=restart,
            confirm_restart=ConfirmDialog(
                page,
                ConfirmLabels(
                    title=text(TextKey.CONFIRM_RESTART_TITLE),
                    message=text(TextKey.CONFIRM_RESTART_MESSAGE),
                    cancel=text(TextKey.CANCEL),
                    confirm=text(TextKey.RESTART),
                ),
            ),
            timers=timers,
        ),
        refresh=refresh,
        new_clock=ChessClock,
    )
    hard_mode = HardModeDialog(
        page,
        HardModeLabels(
            title=text(TextKey.HARD_MODE),
            message=text(TextKey.HARD_MODE_MESSAGE),
            time_per_player=text(TextKey.TIME_PER_PLAYER),
            cancel=text(TextKey.CANCEL),
            start=text(TextKey.START),
        ),
        refresh=refresh,
    )
    settings = SettingsView(
        SettingsLabels(
            title=text(TextKey.SETTINGS_TITLE),
            hint=text(TextKey.SETTINGS_HINT),
            operation=text(TextKey.OPERATION),
            times_table=text(TextKey.TIMES_TABLE),
            play=text(TextKey.PLAY),
            hard_mode=text(TextKey.HARD_MODE),
        ),
        DEFAULT_SETTINGS,
        on_play=lambda chosen: start_match(chosen),
        on_hard_mode=lambda chosen: hard_mode.ask(
            lambda seconds: start_match(chosen.with_time_limit(seconds))
        ),
        refresh=refresh,
        layout=layout,
    )
    navigator = ScreenNavigator(
        page,
        settings_screen=screen(SETTINGS_ROUTE, settings.control),
        game_screen=screen(
            GAME_ROUTE,
            header.control,
            timers.control,
            status.control,
            board.control,
            restart.control,
        ),
        refresh=refresh,
        on_leave_game=lambda: controller.stop_clock(),
    )

    def start_match(chosen: GameSettings) -> None:
        controller.play(chosen)
        navigator.show_game()

    responsive = ResponsiveLayout(
        [settings, header, timers, status, board, restart], refresh=refresh
    )
    # The screen size and the system bars (e.g. when the navigation bar shows
    # or hides) can change while the app runs.
    page.on_resize = lambda event: responsive.fit(
        screen_size_of(page, width=event.width, height=event.height)
    )
    page.on_media_change = lambda media: responsive.fit(screen_size_of(page, insets=media.padding))

    controller.start()
    navigator.show_settings()
    # Runs the hard mode clock; it does nothing while no timed match is on.
    page.run_task(tick_forever, controller.tick)
