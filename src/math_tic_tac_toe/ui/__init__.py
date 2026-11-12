"""Flet user interface layer.

Each module has a single responsibility:

- ``device_language``: asks the device which language it uses;
- ``orientation``: locks the app in portrait on phones;
- ``layout`` / ``responsive``: size the board to the screen (full width,
  without ever pushing the restart button off the screen) and resize it when
  the screen changes;
- ``presenter``: turns the game state into translated display data (no Flet);
- ``ports``: contracts the controller expects from the screen (no Flet);
- ``controller``: connects screen events to the game rules and runs the
  hard mode clock;
- ``ticker``: calls the controller a few times per second for that clock;
- ``styles`` / ``square_button``: the design's colors (``docs/design``),
  the app theme and the shared look of the buttons and dialogs;
- ``events``: adapts Flet's event handlers to plain callbacks;
- ``board_view``: draws the 3x3 board across the full screen width;
- ``confirm_dialog``: asks before the restart or settings button throws
  away a match in progress;
- ``question_dialog``: shows the question and its answer choices in a modal,
  which can be canceled to choose another cell;
- ``screens`` / ``navigator``: the screens' common frame, and switching
  between the settings and the game screens;
- ``settings_view``: the settings screen (operations, times tables, Play,
  and the Best of 5 and Hard mode buttons);
- ``hard_mode_dialog``: asks the seconds per player before a hard mode match;
- ``timers_view``: the two players' timers in hard mode;
- ``score_view``: the two players' points in a best of 5;
- ``turn_time_view``: the seconds left on the turn;
- ``game_header`` / ``title_view``: the title (and settings button) on top;
- ``status_view``: shows whose turn it is and, in red, a wrong answer or a
  player out of time;
- ``restart_button``: starts a new match ("Restart" during a match, "Play
  again" once it ends).
"""
