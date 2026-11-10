"""Identifiers of every text shown to the user."""

from __future__ import annotations

from enum import Enum


class TextKey(Enum):
    APP_TITLE = "app_title"
    TURN = "turn"
    GAME_OVER_WIN = "game_over_win"
    GAME_OVER_DRAW = "game_over_draw"
    RAN_OUT_OF_TIME = "ran_out_of_time"
    WRONG_ANSWER = "wrong_answer"
    SOLVE_QUESTION = "solve_question"
    CANCEL = "cancel"
    RESTART = "restart"
    PLAY_AGAIN = "play_again"
    CONFIRM_RESTART_TITLE = "confirm_restart_title"
    CONFIRM_RESTART_MESSAGE = "confirm_restart_message"
    SETTINGS_TITLE = "settings_title"
    SETTINGS_HINT = "settings_hint"
    OPERATION = "operation"
    TIMES_TABLE = "times_table"
    PLAY = "play"
    HARD_MODE = "hard_mode"
    HARD_MODE_MESSAGE = "hard_mode_message"
    TIME_PER_PLAYER = "time_per_player"
    START = "start"
    OPEN_SETTINGS = "open_settings"
