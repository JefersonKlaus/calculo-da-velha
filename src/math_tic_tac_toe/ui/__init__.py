"""Flet user interface layer.

Each module has a single responsibility:

- ``device_language``: asks the device which language it uses;
- ``orientation``: locks the app in portrait on phones;
- ``layout`` / ``responsive``: size the board to the screen (full width,
  without ever pushing the restart button off the screen) and resize it when
  the screen changes;
- ``presenter``: turns the game state into translated display data (no Flet);
- ``ports``: contracts the controller expects from the screen (no Flet);
- ``controller``: connects screen events to the game rules;
- ``styles`` / ``square_button``: shared look of the square buttons;
- ``board_view``: draws the 3x3 board across the full screen width;
- ``question_dialog``: shows the question and its answer choices in a modal;
- ``screens`` / ``navigator``: the screens' common frame, and switching
  between the settings and the game screens;
- ``settings_view``: the settings screen (operations and times tables);
- ``game_header`` / ``title_view``: the title (and settings button) on top;
- ``status_view``: shows whose turn it is and feedback on the last move;
- ``restart_button``: starts a new match once the current one ends.
"""
