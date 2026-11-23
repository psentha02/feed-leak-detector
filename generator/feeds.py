"""Build the clean (no failures) world: sales, inventory, store master, promo calendar."""
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from generator.demand import expected_units, make_promos
from generator.products import make_products
from generator.stores import make_stores

PROFILE_PATH = Path(__file__).resolve().parents[1] / "profiles" / "beverage_grocery.yaml"


def load_profile(path=PROFILE_PATH):
    with open(path) as f:
        return yaml.safe_load(f)


def build_inventory(units, par, profile, dates, store_ids, upcs):
    """On-hand after each day's sales; restock to par when stock gets low."""
    cfg = profile["inventory"]
    on_hand, out = par.copy(), np.empty_like(units)
    for d in range(units.shape[0]):
        on_hand = np.maximum(on_hand - units[d], 0)
        on_hand = np.where(on_hand <= cfg["reorder_fraction"] * par, par, on_hand)
        out[d] = on_hand
    n_days, n_stores, n_upcs = units.shape
    return pd.DataFrame({
        "date": dates.repeat(n_stores * n_upcs),
        "store_id": np.tile(np.repeat(store_ids, n_upcs), n_days),
        "upc": np.tile(upcs, n_days * n_stores),
        "on_hand": out.ravel(),
    }).assign(file_date=lambda df: df["date"])


def build_base(profile, rng):
    dates = pd.date_range(profile["start_date"], periods=profile["days"])
    master, sizes = make_stores(profile, rng)
    products = make_products(profile, rng)
    promo, lift = make_promos(profile, products, dates, rng)
    units = rng.poisson(expected_units(profile, products, sizes, dates, lift))

    n_days, n_stores, n_upcs = units.shape
    store_ids, upcs = master.store_id.to_numpy(), products.upc.to_numpy()
    notes = np.where(rng.random(units.size) < profile["notes"]["rate"],
                     rng.choice(profile["notes"]["benign"], units.size), "")
    sales = pd.DataFrame({
        "date": dates.repeat(n_stores * n_upcs),
        "store_id": np.tile(np.repeat(store_ids, n_upcs), n_days),
        "upc": np.tile(upcs, n_days * n_stores),
        "units": units.ravel(),
        "dollars": (units * products.price.to_numpy()[None, None, :]).round(2).ravel(),
        "notes": notes,
    }).assign(file_date=lambda df: df["date"])

    par = np.maximum(profile["inventory"]["par_floor"], np.ceil(
        profile["inventory"]["par_weeks"] * 7 * sizes[:, None] * products.base_rate.to_numpy()[None, :]))
    return {"sales": sales, "inventory": None, "master": master, "promo": promo,
            "products": products, "par": par, "start_date": dates[0], "dates": dates}


def with_inventory(world, profile):
    """Rebuild inventory from the true sales in the world."""
    shape = (len(world["dates"]), len(world["master"]), len(world["products"]))
    units = world["sales"].units.to_numpy().reshape(shape)
    inv = build_inventory(units, world["par"], profile, world["dates"],
                          world["master"].store_id.to_numpy(), world["products"].upc.to_numpy())
    return {**world, "inventory": inv}
