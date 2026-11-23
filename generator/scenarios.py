"""The 20 scenarios and the code that builds one. Run `python -m generator.scenarios --seed N`
to write the feeds and labels.json for every scenario with that seed."""
import argparse
import json
from pathlib import Path

import numpy as np

from generator.feeds import build_base, load_profile, with_inventory
from generator.injectors import INJECTORS, WORLD_CASES

TEST_SEED = 99


def _inc(case, start, days, **params):
    return {"case": case, "start": start, "days": days, **params}


# Tuning: seeds 1-5, two scenarios each. Test: seed 99, ten scenarios (not run until Step 4).
SCENARIOS = {
    "s1a": {"seed": 1, "k": 0, "incidents": [_inc(1, 42, 5, n_stores=4)]},
    "s1b": {"seed": 1, "k": 1, "incidents": [_inc(12, 50, 7, n_products=2, lift=4.0)]},
    "s2a": {"seed": 2, "k": 0, "incidents": [_inc(3, 45, 3)]},
    "s2b": {"seed": 2, "k": 1, "incidents": [_inc(13, 55, 4, n_stores=2)]},
    "s3a": {"seed": 3, "k": 0, "incidents": [_inc(4, 40, 5, region="East", n_products=4)]},
    "s3b": {"seed": 3, "k": 1, "incidents": [_inc(4, 60, 4, region="West", n_products=3),
                                              _inc(12, 40, 7, n_products=2)]},
    "s4a": {"seed": 4, "k": 0, "incidents": [_inc(9, 50, 6, n_stores=5)]},
    "s4b": {"seed": 4, "k": 1, "incidents": [_inc(1, 38, 3, n_stores=2), _inc(13, 65, 4, n_stores=1)]},
    "s5a": {"seed": 5, "k": 0, "incidents": [_inc(17, 52, 5, region="West", n_products=4)]},
    "s5b": {"seed": 5, "k": 1, "incidents": [_inc(3, 70, 2), _inc(12, 45, 8, n_products=2, lift=3.0)]},
    "t00": {"seed": 99, "k": 0, "incidents": [_inc(1, 44, 4, n_stores=2)]},
    "t01": {"seed": 99, "k": 1, "incidents": [_inc(1, 60, 6, n_stores=6)]},
    "t02": {"seed": 99, "k": 2, "incidents": [_inc(3, 50, 1)]},
    "t03": {"seed": 99, "k": 3, "incidents": [_inc(4, 55, 5, n_products=5)]},
    "t04": {"seed": 99, "k": 4, "incidents": [_inc(9, 48, 5, n_stores=3)]},
    "t05": {"seed": 99, "k": 5, "incidents": [_inc(12, 62, 6, n_products=3, lift=5.0)]},
    "t06": {"seed": 99, "k": 6, "incidents": [_inc(13, 41, 5, n_stores=3)]},
    "t07": {"seed": 99, "k": 7, "incidents": [_inc(17, 58, 4, region="East", n_products=3)]},
    "t08": {"seed": 99, "k": 8, "incidents": [_inc(4, 36, 4, region="West", n_products=2),
                                               _inc(13, 68, 3, n_stores=2)]},
    "t09": {"seed": 99, "k": 9, "incidents": [_inc(9, 66, 7, n_stores=4), _inc(12, 42, 6, n_products=2)]},
}
TUNING = [n for n, s in SCENARIOS.items() if s["seed"] != TEST_SEED]
TEST = [n for n, s in SCENARIOS.items() if s["seed"] == TEST_SEED]


def build(name):
    """Return ({sales, inventory, master, promo}, labels) for one scenario."""
    spec, profile = SCENARIOS[name], load_profile()
    world = build_base(profile, np.random.default_rng([spec["seed"], spec["k"]]))
    labels = {}

    def apply(i, incident, world, truth):
        rng = np.random.default_rng([spec["seed"], spec["k"], 100 + i])
        world, label = INJECTORS[incident["case"]](world, truth, incident, rng)
        labels[i] = {"incident_id": f"{name}-{i + 1:02d}", **label}
        return world

    indexed = list(enumerate(spec["incidents"]))
    for i, inc in indexed:
        if inc["case"] in WORLD_CASES:
            world = apply(i, inc, world, world["sales"])
    world = with_inventory(world, profile)
    truth = world["sales"]
    for i, inc in indexed:
        if inc["case"] not in WORLD_CASES:
            world = apply(i, inc, world, truth)
    feeds = {k: world[k] for k in ("sales", "inventory", "master", "promo")}
    return feeds, [labels[i] for i, _ in indexed]


def write(name, out_dir):
    feeds, labels = build(name)
    folder = Path(out_dir) / name
    folder.mkdir(parents=True, exist_ok=True)
    for key, frame in feeds.items():
        frame.to_csv(folder / f"{key}.csv", index=False)
    (folder / "labels.json").write_text(json.dumps(labels, indent=2))
    return folder


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--out", default="data")
    args = parser.parse_args()
    for scenario in [n for n, s in SCENARIOS.items() if s["seed"] == args.seed]:
        print("wrote", write(scenario, args.out))
