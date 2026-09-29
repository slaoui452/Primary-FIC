"""Margin Analyzer. Start the application with:  python main.py"""
import logging
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QPalette
from PyQt5.QtWidgets import QApplication

from app.logs import setup_logging
from app.main_window import MainWindow
from app.resources import load_resources

WINDOWS_APP_ID = "MarginAnalyzer.Desktop"


def main() -> int:
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    _use_own_taskbar_icon()

    app = QApplication(sys.argv)
    app.setApplicationName("Margin Analyzer")
    app.setStyle("Fusion")
    app.setPalette(_light_palette())
    app.setFont(QFont("Segoe UI", 10))

    log_handler = setup_logging()
    sys.excepthook = _log_unexpected_error
    load_resources()

    window = MainWindow(log_handler)
    screen = app.primaryScreen().availableGeometry()
    if window.width() > screen.width() or window.height() > screen.height():
        window.showMaximized()
    else:
        window.show()
    return app.exec_()


def _light_palette() -> QPalette:
    """Colors for what the stylesheet in the .ui can't reach (tooltips, placeholders, dialogs)."""
    palette = QPalette()
    for role, color in (
        (QPalette.Window, "#F4F6FA"),
        (QPalette.WindowText, "#1F2937"),
        (QPalette.Base, "#FFFFFF"),
        (QPalette.AlternateBase, "#FAFBFD"),
        (QPalette.Text, "#1F2937"),
        (QPalette.PlaceholderText, "#94A3B8"),
        (QPalette.Button, "#FFFFFF"),
        (QPalette.ButtonText, "#1F2937"),
        (QPalette.Highlight, "#2563EB"),
        (QPalette.HighlightedText, "#FFFFFF"),
        (QPalette.ToolTipBase, "#1F2937"),
        (QPalette.ToolTipText, "#FFFFFF"),
        (QPalette.Link, "#2563EB"),
    ):
        palette.setColor(role, QColor(color))
    return palette


def _use_own_taskbar_icon() -> None:
    """Without this, Windows groups the app under the python.exe icon in the taskbar."""
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(WINDOWS_APP_ID)


def _log_unexpected_error(exc_type, exc_value, exc_traceback) -> None:
    """Show unexpected errors in the Activity log instead of closing the application."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.getLogger("app").error("Unexpected error", exc_info=(exc_type, exc_value, exc_traceback))


if __name__ == "__main__":
    sys.exit(main())
