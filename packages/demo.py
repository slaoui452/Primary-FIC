"""Sample records used by Import and Safe Import until the real data source is plugged in.

Delete this module once packages/import_data.py reads your real data.
"""
import random
from datetime import date, timedelta

import pandas as pd

DESKS = ["Rates", "Credit", "FX", "EM", "Structured"]
ROOT_CAUSES = ["Price mismatch", "Late booking", "Missing trade", "Static data", "FX rate"]
ANALYSTS = ["S. Martin", "L. Chen", "K. Haddad", "A. Rossi"]


def sample_records(primary_date: date) -> pd.DataFrame:
    """Random but repeatable records: the same Primary date always gives the same rows."""
    rng = random.Random(primary_date.toordinal())
    first_day = date(primary_date.year, 1, 1)
    days = (primary_date - first_day).days
    rows = []
    for number in range(rng.randint(900, 1400)):
        booking = first_day + timedelta(days=rng.randint(0, days))
        analysed = rng.random() > 0.15
        rows.append({
            "Filecode": f"FC-{booking:%m%d}-{number:04d}",
            "Desk": rng.choice(DESKS),
            "Root Cause": rng.choice(ROOT_CAUSES) if analysed else "",
            "Analyst": rng.choice(ANALYSTS) if analysed else "",
            "Booking Date": pd.Timestamp(booking),
            "Amount": round(rng.uniform(-50_000, 80_000), 2),
        })
    return pd.DataFrame(rows).sort_values("Booking Date", ascending=False, ignore_index=True)
