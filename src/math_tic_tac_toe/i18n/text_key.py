"""Identifiers of every text shown to the user."""

from __future__ import annotations

from enum import Enum


class TextKey(Enum):
    APP_TITLE = "app_title"
    TURN = "turn"
    GAME_OVER_WIN = "game_over_win"
    GAME_OVER_DRAW = "game_over_draw"
    CORRECT_ANSWER = "correct_answer"
    WRONG_ANSWER = "wrong_answer"
    SOLVE_QUESTION = "solve_question"
    RESTART = "restart"
    SETTINGS_TITLE = "settings_title"
    OPERATION = "operation"
    TIMES_TABLE = "times_table"
    PLAY = "play"
    OPEN_SETTINGS = "open_settings"
