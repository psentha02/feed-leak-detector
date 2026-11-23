"""B0: rules only. Schema, row count against the last 7 days, and file freshness."""
import pandas as pd

WARMUP_DAYS = 28   # every detector stays quiet until it has 4 weeks of history
EXPECTED_COLUMNS = {
    "sales": {"date", "store_id", "upc", "units", "dollars", "notes", "file_date"},
    "inventory": {"date", "store_id", "upc", "on_hand", "file_date"},
}
ROW_DROP = 0.9   # alert when a file has under 90% of the usual rows


def make_alert(day, symptom, feed, stores=None, upcs=None, detail=""):
    """A detector reports what it SAW (a symptom), never why. Diagnosis is a separate job."""
    return {"file_date": day, "symptom": symptom, "feed": feed, "stores": stores, "upcs": upcs, "detail": detail}


def run(feeds):
    alerts = []
    for name, columns in EXPECTED_COLUMNS.items():
        frame = feeds[name]
        days = pd.DatetimeIndex(sorted(frame.file_date.unique()))
        counts = frame.groupby("file_date").size().reindex(days, fill_value=0)
        newest = frame.groupby("file_date").date.max()
        if not columns <= set(frame.columns):
            alerts += [make_alert(d, "schema_change", name) for d in days[WARMUP_DAYS:]]
            continue
        for day in days[WARMUP_DAYS:]:
            usual = counts[day - pd.Timedelta(days=7):day - pd.Timedelta(days=1)].median()
            if counts[day] < ROW_DROP * usual:
                alerts.append(make_alert(day, "row_count_drop", name, detail=f"{counts[day]} rows, usual {usual:.0f}"))
            if newest[day] != day:
                alerts.append(make_alert(day, "file_not_fresh", name, detail=f"newest date in file is {newest[day].date()}"))
    return {"alerts": alerts, "suppressions": []}
