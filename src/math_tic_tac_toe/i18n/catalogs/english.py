"""English texts."""

from ..text_key import TextKey

TEXTS = {
    TextKey.APP_TITLE: "Math Tic-Tac-Toe",
    TextKey.TURN: "{player}'s turn",
    TextKey.GAME_OVER_WIN: "Game over: {player} wins!",
    TextKey.GAME_OVER_DRAW: "Game over: it's a draw!",
    TextKey.RAN_OUT_OF_TIME: "{player} ran out of time.",
    TextKey.WRONG_ANSWER: "Wrong answer.",
    TextKey.TIME_UP: "Time's up!",
    TextKey.SOLVE_QUESTION: "Solve the question",
    TextKey.CANCEL: "Cancel",
    TextKey.RESTART: "Restart",
    TextKey.PLAY_AGAIN: "Play again",
    TextKey.CONFIRM_RESTART_TITLE: "Restart the match?",
    TextKey.CONFIRM_LEAVE_TITLE: "Leave the match?",
    TextKey.MATCH_WILL_BE_LOST: "The current match will be lost.",
    TextKey.LEAVE: "Leave",
    TextKey.SETTINGS_TITLE: "Settings",
    TextKey.SETTINGS_HINT: "In pink: selected options. Tap an option to select or unselect it.",
    TextKey.OPERATION: "Operation",
    TextKey.TIMES_TABLE: "Times table",
    TextKey.PLAY: "Play",
    TextKey.HARD_MODE: "Hard mode",
    TextKey.HARD_MODE_MESSAGE: (
        "Each player has this time for the whole match. Whoever runs out of time loses."
    ),
    TextKey.TIME_PER_PLAYER: "Time per player",
    TextKey.START: "Start",
    TextKey.OPEN_SETTINGS: "Settings",
    TextKey.BEST_OF_FIVE: "Best of 5",
    TextKey.POINTS_TO_WIN: "First to {points} wins",
    TextKey.POINT_FOR: "Point for {player}!",
    TextKey.POINTS_FOR: "{points} points for {player}!",
}
