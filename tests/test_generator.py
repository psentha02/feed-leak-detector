import numpy as np
import pandas as pd

from generator.feeds import build_base, load_profile, with_inventory


def make(seed):
    profile = load_profile()
    return with_inventory(build_base(profile, np.random.default_rng(seed)), profile)


def test_same_seed_gives_identical_feeds():
    a, b = make(7), make(7)
    for key in ("sales", "inventory", "master", "promo"):
        pd.testing.assert_frame_equal(a[key], b[key])


def test_different_seed_changes_sales():
    assert not make(7)["sales"].units.equals(make(8)["sales"].units)


def test_shape_and_columns():
    w = make(1)
    assert len(w["master"]) == 30 and len(w["products"]) == 20
    assert len(w["sales"]) == 30 * 20 * 90 == len(w["inventory"])
    assert set(w["products"].pack) == {"single", "6pack", "case12"}
    assert w["master"].groupby(["region", "format"]).size().min() >= 7   # 2 regions x 2 formats
    assert list(w["sales"].columns[:5]) == ["date", "store_id", "upc", "units", "dollars"]


def test_clean_world_has_no_closures_and_no_negative_stock():
    w = make(1)
    assert w["master"].closed_start.isna().all()
    assert (w["inventory"].on_hand >= 0).all()
