"""Safe Import button: import the Primary date again without losing the analysts' work."""
import logging
from datetime import date

import pandas as pd

from packages import import_data
from packages.common import Progress, no_progress, plural

log = logging.getLogger(__name__)

KEY = "Filecode"
KEPT_COLUMNS = ["Root Cause", "Analyst"]


def run(primary_date: date, current: pd.DataFrame, progress: Progress = no_progress) -> pd.DataFrame:
    """Re-import ``primary_date`` and keep the values already filled in ``current``.

    ``current`` holds every row of the table, including the analysts' edits.
    TODO: adapt the rules below to what Safe Import means in your process.
    """
    fresh = import_data.run(primary_date, progress=lambda percent, message: progress(percent * 0.8, message))
    progress(85, "Keeping existing root causes")
    merged = _keep_existing_values(fresh, current)
    progress(100, "Done")
    return merged


def _keep_existing_values(fresh: pd.DataFrame, current: pd.DataFrame) -> pd.DataFrame:
    """Copy the non-empty KEPT_COLUMNS values of ``current`` into ``fresh``, matching rows on KEY."""
    if current.empty or KEY not in current or KEY not in fresh:
        return fresh
    previous = current.drop_duplicates(KEY, keep="last").set_index(KEY)
    merged = fresh.copy()
    kept = 0
    for column in (c for c in KEPT_COLUMNS if c in previous and c in merged):
        old = merged[KEY].map(previous[column]).fillna("").astype(str)
        has_old = old.str.strip() != ""
        kept += int((has_old & (merged[column].fillna("").astype(str) != old)).sum())
        merged.loc[has_old, column] = old[has_old]
    log.info("Kept %s entered before the re-import", plural(kept, "value"))
    return merged
