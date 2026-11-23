"""Notices feed: free-text messages from the retailer. The text is untrusted data.
Most notices are harmless distractors, so the existence of a notice is not a signal."""
import pandas as pd

COLUMNS = ["notice_id", "date", "store_id", "upc", "text"]


def make_notices(profile, master, products, dates, rng):
    cfg = profile["notices"]
    rows = []
    for _ in range(cfg["distractors"]):
        kind = rng.choice(["all", "store", "product"])
        store = upc = None
        if kind == "all":
            text = rng.choice(cfg["all_stores"])
        elif kind == "store":
            store = rng.choice(master.store_id.to_numpy())
            text = rng.choice(cfg["one_store"]).format(store=store)
        else:
            upc = rng.choice(products.upc.to_numpy())
            text = rng.choice(cfg["one_product"]).format(upc=upc)
        rows.append({"date": dates[int(rng.integers(0, len(dates)))], "store_id": store, "upc": upc, "text": str(text)})
    rows.sort(key=lambda r: r["date"])
    return pd.DataFrame([{"notice_id": f"N{i + 1:03d}", **r} for i, r in enumerate(rows)], columns=COLUMNS)


def add_notice(notices, date, text, store_id=None, upc=None):
    """Return (new notices table, id of the added notice). Ids keep counting up."""
    notice_id = f"N{len(notices) + 1:03d}"
    row = pd.DataFrame([{"notice_id": notice_id, "date": date, "store_id": store_id, "upc": upc, "text": text}])
    return pd.concat([notices, row], ignore_index=True), notice_id
