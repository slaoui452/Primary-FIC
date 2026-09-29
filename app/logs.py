"""Sends Python log records to the Activity log panel."""
import html
import logging
import time

from PyQt5.QtCore import QObject, pyqtSignal

from packages.common import SUCCESS

TIME_COLOR = "#94A3B8"
ERROR_TEXT_COLOR = "#B91C1C"
# (lowest level, tag shown in the log, tag color), checked from top to bottom
LEVEL_STYLES = [
    (logging.ERROR, "ERROR", "#DC2626"),
    (logging.WARNING, "WARN", "#D97706"),
    (SUCCESS, "OK", "#16A34A"),
    (logging.INFO, "INFO", "#2563EB"),
    (logging.NOTSET, "DEBUG", "#94A3B8"),
]


class _Emitter(QObject):
    record = pyqtSignal(int, str, str)  # level, time, message


class QtLogHandler(logging.Handler):
    """Forwards log records through a Qt signal.

    Qt queues the signal when it's emitted from a worker thread, so code in
    packages/ can log from background tasks safely.
    """

    def __init__(self) -> None:
        super().__init__()
        self.emitter = _Emitter()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = record.getMessage()
            if record.exc_info:
                message += "\n" + logging.Formatter().formatException(record.exc_info)
            timestamp = time.strftime("%H:%M:%S", time.localtime(record.created))
            self.emitter.record.emit(record.levelno, timestamp, message)
        except Exception:
            self.handleError(record)


def setup_logging() -> QtLogHandler:
    """Log to the console and to the Activity log, which listens to the returned handler."""
    ui_handler = QtLogHandler()
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s", "%H:%M:%S"))
    logging.basicConfig(level=logging.INFO, handlers=[ui_handler, console], force=True)
    return ui_handler


def to_html(level: int, timestamp: str, message: str) -> str:
    """One Activity log line: time, colored level tag, then the message."""
    tag, color = next((tag, color) for lowest, tag, color in LEVEL_STYLES if level >= lowest)
    text_style = "white-space:pre-wrap;"
    if level >= logging.ERROR:
        text_style += f"color:{ERROR_TEXT_COLOR};"
    return (
        f'<span style="color:{TIME_COLOR}">{timestamp}</span>&nbsp;&nbsp;'
        f'<span style="color:{color}; font-weight:600">{tag.ljust(5).replace(" ", "&nbsp;")}</span>&nbsp;'
        f'<span style="{text_style}">{html.escape(message)}</span>'
    )
