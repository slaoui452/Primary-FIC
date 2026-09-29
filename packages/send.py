"""Send button: share the results (e-mail, report...)."""
import logging
import time
from datetime import date

import pandas as pd

from packages.common import Progress, fmt_count, no_progress, plural

log = logging.getLogger(__name__)


def run(records: pd.DataFrame, primary_date: date, progress: Progress = no_progress) -> None:
    """Send the results of ``primary_date``.

    TODO: build and send your report. The demo only prepares a short summary.
    """
    progress(20, "Preparing the summary")
    time.sleep(0.6)
    missing = int((records["Root Cause"].fillna("") == "").sum()) if "Root Cause" in records else 0
    log.info("Summary for Primary %s: %s, %s without root cause",
             f"{primary_date:%d/%m/%Y}", plural(len(records), "record"), fmt_count(missing))
    progress(70, "Sending")
    time.sleep(0.6)
    progress(100, "Done")
    log.info("Demo mode: nothing was sent")
