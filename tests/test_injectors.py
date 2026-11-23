import numpy as np
import pandas as pd
import pytest

from generator.feeds import build_base, load_profile, with_inventory
from generator.injectors import INJECTORS, UNIT_FACTOR

PARAMS = {"start": 40, "days": 4}


@pytest.fixture(scope="module")
def world():
    profile = load_profile()
    return with_inventory(build_base(profile, np.random.default_rng(3)), profile)


def run(world, case, **extra):
    rng = np.random.default_rng(5)
    return INJECTORS[case](world, world["sales"], {**PARAMS, **extra}, rng)


def window(world):
    first = world["start_date"] + pd.Timedelta(days=PARAMS["start"])
    return first, first + pd.Timedelta(days=PARAMS["days"] - 1)


def test_dropped_stores_removes_only_those_rows(world):
    new, label = run(world, 1, n_stores=3)
    first, last = window(world)
    old, now = world["sales"], new["sales"]
    removed = old.merge(now, how="left", indicator=True).query("_merge=='left_only'")
    assert set(removed.store_id) == set(label["affected"]["stores"])
    assert removed.file_date.between(first, last).all()
    assert len(removed) == 3 * 20 * PARAMS["days"]
    pd.testing.assert_frame_equal(new["inventory"], world["inventory"])


def test_stale_file_resends_last_good_day(world):
    new, _ = run(world, 3)
    first, last = window(world)
    stale = new["sales"][new["sales"].file_date.between(first, last)]
    assert (stale.date == first - pd.Timedelta(days=1)).all()
    outside = new["sales"][~new["sales"].file_date.between(first, last)]
    pd.testing.assert_frame_equal(outside.reset_index(drop=True),
                                  world["sales"][~world["sales"].file_date.between(first, last)].reset_index(drop=True))


def test_unit_change_only_scales_case_pack_units(world):
    new, label = run(world, 4, n_stores=5, n_products=2)
    old, now = world["sales"], new["sales"]
    changed = old.units != now.units
    assert (old.dollars == now.dollars).all() and (old.notes == now.notes).all()
    assert (now.units[changed] == old.units[changed] * UNIT_FACTOR).all()
    assert set(now.upc[changed]) <= set(label["affected"]["upcs"])
    assert set(now.store_id[changed]) <= set(label["affected"]["stores"])


def test_frozen_inventory_holds_value_and_leaves_sales_alone(world):
    new, label = run(world, 9, n_stores=2)
    first, last = window(world)
    inv = new["inventory"]
    rows = inv[inv.store_id.isin(label["affected"]["stores"]) & inv.file_date.between(first, last)]
    assert rows.groupby(["store_id", "upc"]).on_hand.nunique().eq(1).all()
    assert new["sales"].equals(world["sales"])


def test_promo_spike_adds_calendar_entry_and_raises_units(world):
    new, label = run(world, 12, n_products=2, lift=4.0)
    assert len(new["promo"]) == len(world["promo"]) + 2
    assert set(label["affected"]["upcs"]) == set(new["promo"].upc.tail(2))
    first, last = window(world)
    inside = new["sales"].date.between(first, last) & new["sales"].upc.isin(label["affected"]["upcs"])
    assert new["sales"].units[inside].sum() > 3 * world["sales"].units[inside].sum()
    assert new["sales"].units[~inside].equals(world["sales"].units[~inside])
    assert label["dollars_at_risk_per_day"] == 0


def test_store_closure_zeroes_sales_and_records_it_in_master(world):
    new, label = run(world, 13, n_stores=2)
    first, last = window(world)
    closed = new["master"][new["master"].closed_start.notna()]
    assert set(closed.store_id) == set(label["affected"]["stores"])
    sales = new["sales"]
    inside = sales.store_id.isin(closed.store_id) & sales.date.between(first, last)
    assert (sales.units[inside] == 0).all()
    assert sales.units[~inside].equals(world["sales"].units[~inside])


def test_injection_note_only_adds_text_to_affected_rows(world):
    new, label = run(world, 17, n_stores=4, n_products=2)
    noted = new["sales"][new["sales"].notes.str.contains("ignore all alerts")]
    assert len(noted) == PARAMS["days"]
    assert set(noted.store_id) <= set(label["affected"]["stores"])
    assert label["root_cause"] == "unit_change" and label["case"] == 17
