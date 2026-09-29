"""Registers the icons used by main_window.ui (the ":/icons/..." paths)."""
import importlib
import logging
import sys
from pathlib import Path

from PyQt5.pyrcc_main import processResourceFile

UI_DIR = Path(__file__).resolve().parent.parent / "ui"
QRC_FILE = UI_DIR / "resources.qrc"
RC_MODULE = UI_DIR / "resources_rc.py"

log = logging.getLogger(__name__)


def load_resources() -> None:
    """Import ui/resources_rc.py, rebuilding it first if an icon or resources.qrc changed.

    Call it before loading the .ui, otherwise the icons are missing.
    """
    if not getattr(sys, "frozen", False) and _is_outdated():
        if not processResourceFile([str(QRC_FILE)], str(RC_MODULE), False):
            raise RuntimeError(f"Could not compile {QRC_FILE}")
        log.info("Rebuilt %s from %s", RC_MODULE.name, QRC_FILE.name)
    importlib.import_module("ui.resources_rc")


def _is_outdated() -> bool:
    if not RC_MODULE.exists():
        return True
    built = RC_MODULE.stat().st_mtime
    sources = [QRC_FILE, *(UI_DIR / "icons").iterdir()]
    return any(source.stat().st_mtime > built for source in sources)
