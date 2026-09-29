"""Runs the button logic (packages/) in a background thread so the window stays responsive."""
import logging
import time
from typing import Any, Callable

from PyQt5.QtCore import QObject, QThread, pyqtSignal

log = logging.getLogger(__name__)


class Task(QThread):
    """Calls ``function(*args, progress=...)`` in a worker thread and reports back with signals."""

    progressed = pyqtSignal(int, str)  # percent, message
    succeeded = pyqtSignal(object)     # what the function returned
    failed = pyqtSignal(str)           # error message (the traceback goes to the log)

    def __init__(self, name: str, function: Callable[..., Any], *args: Any, parent: QObject = None) -> None:
        super().__init__(parent)
        self.name = name
        self.elapsed = 0.0
        self._function = function
        self._args = args

    def run(self) -> None:
        start = time.perf_counter()
        try:
            result = self._function(*self._args, progress=self._report)
        except Exception as error:
            self.elapsed = time.perf_counter() - start
            log.exception("%s failed", self.name)
            self.failed.emit(str(error) or type(error).__name__)
            return
        self.elapsed = time.perf_counter() - start
        self.succeeded.emit(result)

    def _report(self, percent: float, message: str = "") -> None:
        self.progressed.emit(max(0, min(100, int(percent))), message)
