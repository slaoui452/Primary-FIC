"""Import button: load the records of the selected Primary date."""
import logging
import time
from datetime import date

import pandas as pd

from packages import demo
from packages.common import Progress, no_progress, plural

log = logging.getLogger(__name__)


def run(primary_date: date, progress: Progress = no_progress) -> pd.DataFrame:
    """Return the records of ``primary_date``, one row per record.

    The DataFrame columns become the table columns. The filters look for the
    columns Filecode, Desk, Root Cause, Analyst and Booking Date. If yours have
    other names, update FILTER_COLUMNS in app/main_window.py.
    """
    # TODO: replace this demo with your real source (database query, Excel file, API...).
    log.info("Loading demo data for Primary %s", f"{primary_date:%d/%m/%Y}")
    progress(10, "Connecting")
    time.sleep(0.4)
    progress(35, "Loading records")
    records = demo.sample_records(primary_date)
    time.sleep(0.8)
    progress(80, "Checking records")
    time.sleep(0.3)
    log.info("%s loaded", plural(len(records), "record"))
    _warn_missing_root_causes(records)
    progress(100, "Done")
    return records


def _warn_missing_root_causes(records: pd.DataFrame) -> None:
    if "Root Cause" in records:
        missing = int((records["Root Cause"].fillna("") == "").sum())
        if missing:
            log.warning("%s without root cause yet", plural(missing, "record"))
