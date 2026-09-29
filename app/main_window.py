"""Main window: loads ui/main_window.ui and connects it to the button logic in packages/."""
import logging
import textwrap
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
from PyQt5 import uic
from PyQt5.QtCore import QDate, QEvent, QObject, Qt
from PyQt5.QtGui import QCloseEvent, QColor, QIcon, QTextCharFormat
from PyQt5.QtWidgets import QCalendarWidget, QLabel, QLineEdit, QMainWindow, QMessageBox, QStyledItemDelegate

from app import table
from app.logs import QtLogHandler, to_html
from app.tasks import Task
from packages import import_data, safe_import, save, send
from packages.common import SUCCESS, fmt_count

log = logging.getLogger(__name__)

UI_FILE = Path(__file__).resolve().parent.parent / "ui" / "main_window.ui"

# Table headers read by the filters. Change the names on the right if your data uses other ones.
FILTER_COLUMNS = {
    "filecode": "Filecode",
    "desk": "Desk",
    "root_cause": "Root Cause",
    "analyst": "Analyst",
    "booking_date": "Booking Date",
}
ALL = "All"
BLANK = "(Blank)"

EMPTY_TABLE_TEXT = (
    '<p style="font-size:15px; color:#475569">No data yet</p>'
    "<p>Pick a Primary date and click <b>Import</b>.</p>"
)
NO_MATCH_TEXT = '<p style="font-size:15px; color:#475569">No rows match your filters</p>'


class MainWindow(QMainWindow):
    def __init__(self, log_handler: QtLogHandler) -> None:
        super().__init__()
        uic.loadUi(str(UI_FILE), self)
        self._task = None
        self._combos = {
            "desk": self.deskCombo,
            "root_cause": self.rootCauseCombo,
            "analyst": self.analystCombo,
        }
        self._setup_icons()
        self._setup_dates()
        self._setup_filters()
        self._setup_table()
        self._setup_panels()
        self._set_status("idle", "Ready")
        self._update_row_count(0)
        log_handler.emitter.record.connect(self._append_log)

        self.importButton.clicked.connect(self._on_import)
        self.safeImportButton.clicked.connect(self._on_safe_import)
        self.saveButton.clicked.connect(self._on_save)
        self.sendButton.clicked.connect(self._on_send)

    # ------------------------------------------------------------------ setup

    def _setup_icons(self) -> None:
        # Designer loads these pixmaps at 1x: render them again from the SVGs so they stay sharp on HiDPI screens.
        self.appLogo.setPixmap(QIcon(":/icons/app.svg").pixmap(28, 28))
        self.logIcon.setPixmap(QIcon(":/icons/terminal.svg").pixmap(16, 16))
        self.filecodeEdit.addAction(QIcon(":/icons/search.svg"), QLineEdit.LeadingPosition)

    def _setup_dates(self) -> None:
        today = date.today()
        self.bookingFromDate.setDate(QDate(today.year, 1, 1))
        self.bookingToDate.setDate(QDate(today))
        self.primaryDate.setDate(QDate(previous_business_day(today)))
        for date_edit in (self.bookingFromDate, self.bookingToDate, self.primaryDate):
            _style_calendar(date_edit.calendarWidget())

    def _setup_filters(self) -> None:
        for combo in self._combos.values():
            combo.setItemDelegate(QStyledItemDelegate(combo))  # lets the stylesheet style the popup rows
            combo.currentIndexChanged.connect(self._apply_filters)
        self.filecodeEdit.textChanged.connect(self._apply_filters)
        self.bookingFromDate.dateChanged.connect(self._apply_filters)
        self.bookingToDate.dateChanged.connect(self._apply_filters)

    def _setup_table(self) -> None:
        header = self.tableWidget.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header.setSortIndicator(-1, Qt.AscendingOrder)
        self._viewport = self.tableWidget.viewport()
        self._empty_label = QLabel(self._viewport)
        self._empty_label.setObjectName("emptyStateLabel")
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._viewport.installEventFilter(self)

    def _setup_panels(self) -> None:
        self.mainSplitter.setStretchFactor(0, 1)  # the table takes the extra height, not the log
        self.mainSplitter.setStretchFactor(1, 0)
        self.mainSplitter.setSizes([560, 190])
        self.toggleLogButton.toggled.connect(self.logCard.setVisible)
        self.clearLogButton.clicked.connect(self.logView.clear)
        self.progressBar.hide()

    # ---------------------------------------------------------------- buttons

    def _on_import(self) -> None:
        self._start("Import", import_data.run, self._primary_date(), on_done=self._show_records)

    def _on_safe_import(self) -> None:
        current = table.read_table(self.tableWidget)
        self._start("Safe Import", safe_import.run, self._primary_date(), current, on_done=self._show_records)

    def _on_save(self) -> None:
        if self._has_records("save"):
            self._start("Save", save.run, table.read_table(self.tableWidget), self._primary_date())

    def _on_send(self) -> None:
        if self._has_records("send"):
            self._start("Send", send.run, table.read_table(self.tableWidget), self._primary_date())

    def _primary_date(self) -> date:
        return self.primaryDate.date().toPyDate()

    def _has_records(self, action: str) -> bool:
        if self.tableWidget.rowCount():
            return True
        log.warning("Nothing to %s yet: import data first", action)
        self._set_status("idle", f"Nothing to {action} yet")
        return False

    # ------------------------------------------------------------------ tasks

    def _start(self, name, function, *args, on_done=None) -> None:
        if self._task is not None:
            return
        task = Task(name, function, *args, parent=self)
        task.progressed.connect(self._on_progress)
        task.succeeded.connect(lambda result: self._on_succeeded(task, result, on_done))
        task.failed.connect(lambda error: self._on_failed(task, error))
        task.finished.connect(self._on_finished)
        self._task = task
        self._set_busy(True)
        self._set_status("busy", f"{name}…")
        log.info("%s started", name)
        task.start()

    def _on_progress(self, percent: int, message: str) -> None:
        name = self._task.name if self._task else ""
        self.progressBar.setValue(percent)
        self.statusLabel.setText(f"{name}: {message} ({percent}%)" if message else f"{name}… {percent}%")

    def _on_succeeded(self, task: Task, result, on_done) -> None:
        try:
            if on_done is not None:
                on_done(result)
        except Exception:
            log.exception("%s: couldn't show the result", task.name)
            self._set_status("error", f"{task.name} failed, see the activity log")
            return
        log.log(SUCCESS, "%s finished in %.1f s", task.name, task.elapsed)
        self._set_status("ok", f"{task.name} finished at {datetime.now():%H:%M}")

    def _on_failed(self, task: Task, error: str) -> None:
        self._set_status("error", f"{task.name} failed: {textwrap.shorten(error, 70, placeholder='…')}")

    def _on_finished(self) -> None:
        task, self._task = self._task, None
        self._set_busy(False)
        if task is not None:
            task.deleteLater()

    def _set_busy(self, busy: bool) -> None:
        for widget in (self.importButton, self.safeImportButton, self.saveButton, self.sendButton, self.primaryDate):
            widget.setEnabled(not busy)
        self.progressBar.setValue(0)
        self.progressBar.setVisible(busy)

    def _set_status(self, state: str, text: str) -> None:
        """state is idle, busy, ok or error: it picks the dot color in the stylesheet."""
        self.statusDot.setProperty("state", state)
        self.statusDot.style().unpolish(self.statusDot)  # re-apply the stylesheet for the new state
        self.statusDot.style().polish(self.statusDot)
        self.statusLabel.setText(text)

    # ------------------------------------------------------------------ table

    def _show_records(self, records: pd.DataFrame) -> None:
        if not isinstance(records, pd.DataFrame):
            raise TypeError(f"expected a pandas DataFrame, got {type(records).__name__}")
        table.fill_table(self.tableWidget, records)
        self._fit_columns()
        self._refresh_filter_choices()
        self._apply_filters()

    def _fit_columns(self) -> None:
        """Size the columns to their content, then share the spare width so the table fills its card."""
        grid = self.tableWidget
        header = grid.horizontalHeader()
        widths = [max(grid.sizeHintForColumn(column), header.sectionSizeHint(column)) + 16
                  for column in range(header.count())]
        needed = sum(widths)
        spare = grid.viewport().width() - grid.verticalScrollBar().sizeHint().width() - needed
        if spare > 0:
            widths = [width + spare * width // needed for width in widths]
        for column, width in enumerate(widths):
            header.resizeSection(column, width)

    def _refresh_filter_choices(self) -> None:
        """Fill Desk, Root Cause and Analyst with the values found in the table."""
        for key, combo in self._combos.items():
            column = table.find_column(self.tableWidget, FILTER_COLUMNS[key])
            values = table.column_values(self.tableWidget, column) if column >= 0 else set()
            current = combo.currentText()
            combo.blockSignals(True)
            combo.clear()
            combo.addItem(ALL)
            if "" in values:
                combo.addItem(BLANK)
            combo.addItems(sorted((value for value in values if value), key=str.casefold))
            combo.setCurrentIndex(max(combo.findText(current), 0))
            combo.setEnabled(bool(values))
            combo.blockSignals(False)

    def _apply_filters(self) -> None:
        grid = self.tableWidget
        columns = {key: table.find_column(grid, name) for key, name in FILTER_COLUMNS.items()}
        needle = self.filecodeEdit.text().strip().casefold()
        chosen = {key: combo.currentText() for key, combo in self._combos.items()
                  if combo.isEnabled() and combo.currentIndex() > 0 and columns[key] >= 0}
        first_day = self.bookingFromDate.date().toPyDate()
        last_day = self.bookingToDate.date().toPyDate()

        visible = 0
        for row in range(grid.rowCount()):
            shown = True
            if needle and columns["filecode"] >= 0:
                shown = needle in table.cell_text(grid, row, columns["filecode"]).casefold()
            for key, value in chosen.items():
                text = table.cell_text(grid, row, columns[key])
                shown = shown and (text == "" if value == BLANK else text == value)
            if shown and columns["booking_date"] >= 0:
                booked = table.parse_date(table.cell_text(grid, row, columns["booking_date"]))
                shown = booked is None or first_day <= booked <= last_day
            grid.setRowHidden(row, not shown)
            visible += shown
        self._update_row_count(visible)

    def _update_row_count(self, visible: int) -> None:
        total = self.tableWidget.rowCount()
        unit = "row" if total == 1 else "rows"
        if visible == total:
            self.rowCountBadge.setText(f"{fmt_count(total)} {unit}")
        else:
            self.rowCountBadge.setText(f"{fmt_count(visible)} of {fmt_count(total)} {unit}")
        self._empty_label.setText(EMPTY_TABLE_TEXT if total == 0 else NO_MATCH_TEXT)
        self._empty_label.setVisible(visible == 0)

    # -------------------------------------------------------------------- log

    def _append_log(self, level: int, timestamp: str, message: str) -> None:
        scrollbar = self.logView.verticalScrollBar()
        follow = scrollbar.value() >= scrollbar.maximum() - 4
        self.logView.appendHtml(to_html(level, timestamp, message))
        if follow:
            scrollbar.setValue(scrollbar.maximum())

    # ------------------------------------------------------------- Qt events

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched is self._viewport and event.type() == QEvent.Resize:
            self._empty_label.resize(event.size())
        return super().eventFilter(watched, event)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._task is not None:
            QMessageBox.information(self, "Margin Analyzer",
                                    f"{self._task.name} is still running. Wait for it to finish before closing.")
            event.ignore()
            return
        super().closeEvent(event)


def previous_business_day(day: date) -> date:
    """The weekday before ``day``. Weekends are skipped, public holidays aren't."""
    day -= timedelta(days=1)
    while day.weekday() >= 5:
        day -= timedelta(days=1)
    return day


def _style_calendar(calendar: QCalendarWidget) -> None:
    """Calendar popup settings that a stylesheet can't express."""
    popup = calendar.parentWidget()  # the popup window: its background (QCalendarPopup in the stylesheet)
    popup.setAttribute(Qt.WA_StyledBackground, True)  # shows through this 1px margin as a border
    popup.layout().setContentsMargins(1, 1, 1, 1)
    calendar.setMinimumSize(300, 240)
    calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
    calendar.setFirstDayOfWeek(Qt.Monday)
    calendar.setGridVisible(False)
    weekend = QTextCharFormat()
    weekend.setForeground(QColor("#94A3B8"))
    calendar.setWeekdayTextFormat(Qt.Saturday, weekend)
    calendar.setWeekdayTextFormat(Qt.Sunday, weekend)
    day_names = QTextCharFormat()
    day_names.setForeground(QColor("#64748B"))
    calendar.setHeaderTextFormat(day_names)
