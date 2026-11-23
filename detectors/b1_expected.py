"""B1: B0 plus expected vs actual per store and product, using day of week,
the promotion calendar and the store master. No LLM.

Expected units for a store and product = median of the same weekday over the
last 4 weeks, skipping promo days, closed days and stale files."""
import warnings

import numpy as np
import pandas as pd

from detectors.b0_rules import WARMUP_DAYS, make_alert
from detectors import b0_rules

# The five knobs that trade detection speed against false alerts. DEFAULT reproduces the
# original behavior exactly; strict and loose are the two ends of the sweep (evals/sweep.py).
DEFAULT = {
    "spike": 2.5,           # product total this many times expected is a spike...
    "spike_in_promo": 8,    # ...unless a calendar promotion explains it (promos reach about 5x)
    "low_sales": 0.3,       # store total under this share of expected
    "min_expected": 20,     # ignore totals too small to judge
    "frozen_share": 0.85,   # share of products with unchanged on_hand
}
PRESETS = {
    "strict": {**DEFAULT, "spike": 3.5, "spike_in_promo": 10, "low_sales": 0.2, "min_expected": 30, "frozen_share": 0.92},
    "default": DEFAULT,
    "loose": {**DEFAULT, "spike": 2.0, "spike_in_promo": 6, "min_expected": 10},   # picked by evals/sweep.py on tuning scenarios only
}
MIN_CELLS = 8


def _grid(frame, value, dates, store_idx, upc_idx):
    # get_indexer gives -1 for ids it does not know, and -1 would write into the last column
    frame = frame[frame.store_id.isin(store_idx) & frame.upc.isin(upc_idx)]
    grid = np.full((len(dates), len(store_idx), len(upc_idx)), np.nan)
    grid[dates.get_indexer(frame.file_date), store_idx.get_indexer(frame.store_id),
         upc_idx.get_indexer(frame.upc)] = frame[value].to_numpy()
    return grid


def _expected(units, hist, valid):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return np.nanmedian(np.where(valid, units[hist], np.nan), axis=0)


def run(feeds, params=None):
    k = {**DEFAULT, **(params or {})}
    out = b0_rules.run(feeds)
    sales, inv, master, promo = feeds["sales"], feeds["inventory"], feeds["master"], feeds["promo"]
    dates = pd.DatetimeIndex(sorted(sales.file_date.unique()))
    stores, upcs = pd.Index(master.store_id), pd.Index(sorted(sales.upc.unique()))
    units = _grid(sales, "units", dates, stores, upcs)
    on_hand = _grid(inv, "on_hand", dates, stores, upcs)

    present = ~np.isnan(units).all(axis=2)
    opened = dates.to_numpy()[:, None] >= master.open_date.to_numpy()[None, :]
    closed = ((dates.to_numpy()[:, None] >= master.closed_start.to_numpy()[None, :])
              & (dates.to_numpy()[:, None] <= master.closed_end.to_numpy()[None, :]))
    promoted = np.zeros((len(dates), len(upcs)), dtype=bool)
    for row in promo.itertuples():
        promoted[(dates >= row.start) & (dates <= row.end), upcs.get_loc(row.upc)] = True
    stale = np.array([any(a["symptom"] == "file_not_fresh" and a["file_date"] == d for a in out["alerts"]) for d in dates])

    alerts, suppressions = [], []
    for d in range(WARMUP_DAYS, len(dates)):
        if stale[d]:
            continue   # the data in a stale file is not trustworthy
        day, hist = dates[d], [d - 7, d - 14, d - 21, d - 28]
        valid = ~promoted[hist][:, None, :] & ~closed[hist][:, :, None] & ~stale[hist][:, None, None]
        expected, actual = _expected(units, hist, valid), units[d]
        cells = present[d][:, None] & opened[d][:, None] & ~np.isnan(expected) & ~np.isnan(actual)

        missing = opened[d] & ~present[d] & ~closed[d]
        if missing.any():
            alerts.append(make_alert(day, "stores_missing", "sales", stores=stores[missing].tolist()))

        exp_store = np.where(cells, expected, 0).sum(axis=1)
        act_store = np.where(cells, actual, 0).sum(axis=1)
        for s in np.where((exp_store >= k["min_expected"]) & (act_store < k["low_sales"] * exp_store))[0]:
            if closed[d, s]:
                suppressions.append({"file_date": day, "reason": "store_master", "stores": [stores[s]], "upcs": None})
            else:
                alerts.append(make_alert(day, "store_zero_sales", "sales", stores=[stores[s]]))

        open_cells = cells & ~closed[d][:, None]
        exp_upc = np.where(open_cells, expected, 0).sum(axis=0)
        act_upc = np.where(open_cells, actual, 0).sum(axis=0)
        ratio = np.divide(act_upc, exp_upc, out=np.zeros_like(act_upc), where=exp_upc >= k["min_expected"])
        limit = np.where(promoted[d], k["spike_in_promo"], k["spike"])
        spiking = (exp_upc >= k["min_expected"]) & (ratio >= limit)
        explained = (exp_upc >= k["min_expected"]) & promoted[d] & (ratio >= k["spike"]) & ~spiking
        if spiking.any():
            alerts.append(make_alert(day, "units_spike", "sales", upcs=upcs[spiking].tolist()))
        if explained.any():
            suppressions.append({"file_date": day, "reason": "promo_calendar", "stores": None,
                                 "upcs": upcs[explained].tolist()})

        eligible = open_cells & (np.nan_to_num(expected) >= 2)
        unchanged = (on_hand[d] == on_hand[d - 1]) & eligible
        n_eligible = eligible.sum(axis=1)
        share = unchanged.sum(axis=1) / np.maximum(n_eligible, 1)
        frozen = (n_eligible >= MIN_CELLS) & (share >= k["frozen_share"])
        if frozen.any():
            alerts.append(make_alert(day, "inventory_unchanged", "inventory", stores=stores[frozen].tolist()))

    named = {a["file_date"] for a in alerts if a["symptom"] == "stores_missing"}   # B1 names the stores, so drop B0's vaguer row-count alert that day
    kept = [a for a in out["alerts"] if not (a["symptom"] == "row_count_drop" and a["file_date"] in named)]
    return {"alerts": kept + alerts, "suppressions": suppressions}
