"""Demand = base rate x store size x day of week x promotion lift, then count noise."""
import numpy as np
import pandas as pd


def make_promos(profile, products, dates, rng):
    """Return the promotion calendar and a (days, products) lift array."""
    cfg = profile["base_promos"]
    upcs = products.upc.tolist()
    lift = np.ones((len(dates), len(upcs)))
    rows = []
    for _ in range(cfg["count"]):
        chosen = rng.choice(upcs, rng.integers(cfg["products"][0], cfg["products"][1] + 1), replace=False)
        length = int(rng.integers(cfg["days"][0], cfg["days"][1] + 1))
        first = int(rng.integers(0, len(dates) - length))
        factor = rng.uniform(*cfg["lift"])
        for upc in chosen.tolist():
            rows.append({"upc": upc, "start": dates[first], "end": dates[first + length - 1]})
            col = upcs.index(upc)
            lift[first:first + length, col] = np.maximum(lift[first:first + length, col], factor)
    return pd.DataFrame(rows), lift


def expected_units(profile, products, sizes, dates, lift):
    """Mean units for every (day, store, product)."""
    dow = np.array(profile["day_of_week"])[dates.day_of_week]
    return (dow[:, None, None] * sizes[None, :, None]
            * products.base_rate.to_numpy()[None, None, :] * lift[:, None, :])
