"""Store master: 30 stores, 2 regions x 2 formats."""
import numpy as np
import pandas as pd


def make_stores(profile, rng):
    formats = list(profile["formats"])
    regions = profile["regions"]
    open_date = pd.Timestamp(profile["start_date"]) - pd.Timedelta(days=365)
    rows, sizes = [], []
    for i in range(profile["n_stores"]):
        fmt = formats[i % len(formats)]
        rows.append({
            "store_id": f"S{i + 1:02d}",
            "region": regions[(i // len(formats)) % len(regions)],
            "format": fmt,
            "open_date": open_date,
            "closed_start": pd.NaT,
            "closed_end": pd.NaT,
        })
        sizes.append(rng.uniform(*profile["formats"][fmt]["size"]))
    return pd.DataFrame(rows), np.array(sizes)
