"""Helpers shared by the button modules."""
import logging
from typing import Callable

Progress = Callable[[float, str], None]
"""Callback given to every ``run()``: ``progress(percent, "what is happening")``."""

SUCCESS = 25
"""Log level for a finished step, shown as a green OK in the Activity log."""
logging.addLevelName(SUCCESS, "SUCCESS")


def no_progress(percent: float, message: str) -> None:
    """Progress callback used when a ``run()`` is called outside the UI (scripts, tests)."""


def fmt_count(count: int) -> str:
    """1240 -> '1 240', the thousands separator used in the table."""
    return f"{count:,}".replace(",", " ")


def plural(count: int, word: str) -> str:
    """plural(1, "record") -> '1 record', plural(1240, "record") -> '1 240 records'."""
    return f"{fmt_count(count)} {word}{'' if count == 1 else 's'}"
