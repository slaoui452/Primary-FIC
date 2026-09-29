"""Shows a pandas DataFrame in the QTableWidget and reads it back."""
import numbers
from datetime import date, datetime
from typing import Any, Optional

import pandas as pd
from pandas.api import types as pd_types
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem

DATE_FORMAT = "%d/%m/%Y"
KIND_ROLE = Qt.UserRole + 1  # "number", "date" or "text": how a cell is sorted and read back
NEGATIVE_BRUSH = QBrush(QColor("#DC2626"))
ALIGN_LEFT = Qt.AlignLeft | Qt.AlignVCenter
ALIGN_RIGHT = Qt.AlignRight | Qt.AlignVCenter


class TableItem(QTableWidgetItem):
    """Cell that sorts numbers and dates by value, and text without case."""

    def __lt__(self, other: QTableWidgetItem) -> bool:
        return _sort_key(self) < _sort_key(other)


def fill_table(table: QTableWidget, data: pd.DataFrame) -> None:
    """Replace the table content, columns included, with ``data``."""
    kinds = [_kind(data[column]) for column in data.columns]
    sorting = table.isSortingEnabled()
    table.setSortingEnabled(False)  # sorting while inserting would scramble the rows
    table.setUpdatesEnabled(False)
    try:
        table.setRowCount(0)
        table.setColumnCount(len(kinds))
        table.setHorizontalHeaderLabels([str(column) for column in data.columns])
        for column, kind in enumerate(kinds):
            table.horizontalHeaderItem(column).setTextAlignment(ALIGN_RIGHT if kind == "number" else ALIGN_LEFT)
        table.setRowCount(len(data))
        for row, values in enumerate(data.itertuples(index=False, name=None)):
            for column, (value, kind) in enumerate(zip(values, kinds)):
                table.setItem(row, column, _make_item(value, kind))
    finally:
        table.horizontalHeader().setSortIndicator(-1, Qt.AscendingOrder)  # keep the order of ``data``
        table.setSortingEnabled(sorting)
        table.setUpdatesEnabled(True)


def read_table(table: QTableWidget) -> pd.DataFrame:
    """Every row of the table, hidden ones included, with the user's edits."""
    columns = []
    for column in range(table.columnCount()):
        header = table.horizontalHeaderItem(column)
        kind = _column_kind(table, column)
        values = [_cell_value(table.item(row, column), kind) for row in range(table.rowCount())]
        series = pd.Series(values, name=header.text() if header else str(column), dtype=object)
        if kind == "number":
            series = pd.to_numeric(series)
        elif kind == "date":
            series = pd.to_datetime(series)
        columns.append(series)
    return pd.concat(columns, axis=1) if columns else pd.DataFrame()


def find_column(table: QTableWidget, name: str) -> int:
    """Index of the column whose header is ``name`` (case-insensitive), or -1."""
    wanted = name.strip().casefold()
    for column in range(table.columnCount()):
        header = table.horizontalHeaderItem(column)
        if header is not None and header.text().strip().casefold() == wanted:
            return column
    return -1


def cell_text(table: QTableWidget, row: int, column: int) -> str:
    item = table.item(row, column)
    return item.text() if item is not None else ""


def column_values(table: QTableWidget, column: int) -> set:
    """Distinct texts of a column ("" for empty cells)."""
    return {cell_text(table, row, column) for row in range(table.rowCount())}


def format_number(value: Any) -> str:
    text = f"{value:,}" if isinstance(value, numbers.Integral) else f"{value:,.2f}"
    return text.replace(",", " ")


def parse_number(text: str) -> Optional[float]:
    """'12 450.00', '-3 210,5' or '1,234.5' -> float; None if empty or not a number."""
    text = text.replace(" ", "").replace("\xa0", "").replace(" ", "")
    text = text.replace(",", "") if "." in text else text.replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def parse_date(text: str) -> Optional[date]:
    try:
        return datetime.strptime(text.strip(), DATE_FORMAT).date()
    except ValueError:
        return None


def _kind(series: pd.Series) -> str:
    if pd_types.is_bool_dtype(series):
        return "text"
    if pd_types.is_numeric_dtype(series):
        return "number"
    if pd_types.is_datetime64_any_dtype(series):
        return "date"
    first = series.dropna().head(1)
    return "date" if len(first) and isinstance(first.iloc[0], date) else "text"


def _make_item(value: Any, kind: str) -> TableItem:
    missing = pd.isna(value)
    if missing:
        text = ""
    elif kind == "number":
        text = format_number(value)
    elif kind == "date":
        text = value.strftime(DATE_FORMAT)
    else:
        text = str(value)
    item = TableItem(text)
    item.setData(KIND_ROLE, kind)
    if kind == "number":
        item.setTextAlignment(ALIGN_RIGHT)
        if not missing and value < 0:
            item.setForeground(NEGATIVE_BRUSH)
    return item


def _column_kind(table: QTableWidget, column: int) -> str:
    for row in range(table.rowCount()):
        item = table.item(row, column)
        if item is not None:
            return item.data(KIND_ROLE) or "text"
    return "text"


def _cell_value(item: Optional[QTableWidgetItem], kind: str) -> Any:
    text = item.text() if item is not None else ""
    if kind == "number":
        return parse_number(text)
    if kind == "date":
        return parse_date(text)
    return text


def _sort_key(item: QTableWidgetItem) -> tuple:
    kind = item.data(KIND_ROLE)
    if kind == "number":
        value = parse_number(item.text())
    elif kind == "date":
        value = parse_date(item.text())
    else:
        return False, item.text().casefold()
    return value is None, value if value is not None else 0
