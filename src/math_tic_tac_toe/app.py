"""Builds the app: creates the screens and wires them together.

The app is started by ``src/main.py`` (used by ``flet run`` and ``flet build``).
It opens on the settings screen; "Play" starts a match on the game screen,
"Best of 5" starts one played for points (the first to 3 lines wins), and
"Hard mode" starts one where each player has a limited time (a chess clock).
"""

from __future__ import annotations

import flet as ft

from .cell_timers import CellTimers
from .clock import ChessClock, Countdown
from .game import Game
from .i18n import TextKey, translator_for
from .settings import BEST_OF_FIVE, DEFAULT_SETTINGS, GameSettings
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
from .ui.score_view import ScoreView
from .ui.screens import GAME_ROUTE, SETTINGS_ROUTE, screen
from .ui.settings_view import SettingsLabels, SettingsView
from .ui.status_view import StatusView
from .ui.styles import BACKGROUND_COLOR, app_theme
from .ui.ticker import tick_forever
from .ui.timers_view import TimersView


async def main(page: ft.Page) -> None:
    await lock_portrait(page)
    translator = translator_for(await detect_device_language(page))
    text = translator.text
    page.title = text(TextKey.APP_TITLE)
    # The design is dark (navy), whatever the phone's light/dark setting.
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = page.dark_theme = app_theme()
    page.bgcolor = BACKGROUND_COLOR
    layout = layout_for_screen(screen_size_of(page))
    refresh = page.update

    # Views only forward taps; the controller and the navigator decide.
    header = GameHeader(
        text(TextKey.APP_TITLE),
        text(TextKey.OPEN_SETTINGS),
        # Asks first if a match in progress would be lost.
        on_open_settings=lambda: controller.request_leave(navigator.show_settings),
        layout=layout,
    )
    timers = TimersView(layout)
    score = ScoreView(layout)
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
                    message=text(TextKey.MATCH_WILL_BE_LOST),
                    cancel=text(TextKey.CANCEL),
                    confirm=text(TextKey.RESTART),
                ),
            ),
            confirm_leave=ConfirmDialog(
                page,
                ConfirmLabels(
                    title=text(TextKey.CONFIRM_LEAVE_TITLE),
                    message=text(TextKey.MATCH_WILL_BE_LOST),
                    cancel=text(TextKey.CANCEL),
                    confirm=text(TextKey.LEAVE),
                ),
            ),
            timers=timers,
            score=score,
        ),
        refresh=refresh,
        new_clock=ChessClock,
        new_cell_timers=CellTimers,
        new_countdown=Countdown,
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
            best_of=text(TextKey.BEST_OF_FIVE),
            hard_mode=text(TextKey.HARD_MODE),
        ),
        DEFAULT_SETTINGS,
        on_play=lambda chosen: start_match(chosen),
        on_best_of=lambda chosen: start_match(chosen.with_best_of(BEST_OF_FIVE)),
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
            # Never both: hard mode shows the timers, a best of 5 the score.
            timers.control,
            score.control,
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
        [settings, header, timers, score, status, board, restart], refresh=refresh
    )
    # The screen size and the system bars (e.g. when the navigation bar shows
    # or hides) can change while the app runs.
    page.on_resize = lambda event: responsive.fit(
        screen_size_of(page, width=event.width, height=event.height)
    )
    page.on_media_change = lambda media: responsive.fit(screen_size_of(page, insets=media.padding))

    controller.start()
    navigator.show_settings()
    # Runs the hard mode clock, the best of 5 cells' countdowns and the time
    # to answer an open question.
    page.run_task(tick_forever, controller.tick)
