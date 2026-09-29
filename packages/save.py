"""Save button: store the table, including what the analysts typed."""
import logging
import time
from datetime import date

import pandas as pd

from packages.common import Progress, no_progress, plural

log = logging.getLogger(__name__)


def run(records: pd.DataFrame, primary_date: date, progress: Progress = no_progress) -> None:
    """Save ``records`` (every row of the table) for ``primary_date``.

    TODO: write to your database or shared folder. The demo only simulates the steps.
    """
    log.info("Saving %s for Primary %s", plural(len(records), "record"), f"{primary_date:%d/%m/%Y}")
    steps = ["Checking records", "Writing records", "Confirming"]
    for number, step in enumerate(steps):
        progress(number * 100 / len(steps), step)
        time.sleep(0.5)
    progress(100, "Done")
    log.info("Demo mode: nothing was written")
