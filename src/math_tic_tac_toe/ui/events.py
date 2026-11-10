"""Adapters between Flet's event handlers and the app's plain callbacks."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

ClickHandler = Callable[[Any], None]


def ignoring_event(action: Callable[[], None]) -> ClickHandler:
    """Click handler that runs ``action`` and ignores Flet's event.

    Pair it with ``functools.partial`` to pass values, e.g. the cell position.
    """
    return lambda _: action()
