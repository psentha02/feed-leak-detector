"""Product list: singles, 6-packs and 12-pack cases."""
import pandas as pd


def make_products(profile, rng):
    rows = []
    for pack, cfg in profile["packs"].items():
        for _ in range(cfg["count"]):
            rows.append({
                "pack": pack,
                "base_rate": rng.uniform(*cfg["base_rate"]),
                "price": round(rng.uniform(*cfg["price"]), 2),
            })
    products = pd.DataFrame(rows)
    products.insert(0, "upc", [f"8400000{i + 1:05d}" for i in range(len(products))])
    return products
