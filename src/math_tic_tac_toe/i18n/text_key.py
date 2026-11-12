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
    TIME_UP = "time_up"
    SOLVE_QUESTION = "solve_question"
    CANCEL = "cancel"
    RESTART = "restart"
    PLAY_AGAIN = "play_again"
    CONFIRM_RESTART_TITLE = "confirm_restart_title"
    CONFIRM_LEAVE_TITLE = "confirm_leave_title"
    MATCH_WILL_BE_LOST = "match_will_be_lost"  # message of both confirmations
    LEAVE = "leave"
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
    BEST_OF_FIVE = "best_of_five"
    POINTS_TO_WIN = "points_to_win"
    POINT_FOR = "point_for"
    POINTS_FOR = "points_for"
