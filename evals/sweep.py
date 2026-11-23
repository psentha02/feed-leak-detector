"""Sweep B1's five thresholds on the TUNING scenarios only and pick the loose setting.
Rule, fixed before looking: loose = lowest mean days to detect on small incidents among
settings with at most MAX_FALSE_PER_WEEK false alerts per week; ties go to fewer false alerts."""
from itertools import product

from detectors import b1_expected
from evals.score import score_scenario, summarize
from generator.scenarios import TUNING, build

MAX_FALSE_PER_WEEK = 10
GRID = {
    "spike": [1.5, 2.0, 2.5],
    "spike_in_promo": [6, 8],
    "low_sales": [0.3, 0.5],
    "min_expected": [10, 20],
    "frozen_share": [0.7, 0.85],
}


def sweep():
    built = {name: build(name) for name in TUNING}
    rows = []
    for values in product(*GRID.values()):
        params = dict(zip(GRID, values))
        scored = [score_scenario(labels, b1_expected.run(feeds, params=params), feeds) for feeds, labels in built.values()]
        rows.append((params, summarize(scored)))
    return rows


if __name__ == "__main__":
    rows = sweep()
    ok = [r for r in rows if r[1]["false_alerts_per_week"] <= MAX_FALSE_PER_WEEK]
    ok.sort(key=lambda r: (r[1]["mean_days_small"], r[1]["false_alerts_per_week"]))
    print(f"{len(rows)} settings, {len(ok)} within {MAX_FALSE_PER_WEEK} false alerts/week")
    print("days_small  false/wk  missed  24h$   params")
    for params, m in sorted(rows, key=lambda r: (r[1]["mean_days_small"], r[1]["false_alerts_per_week"]))[:12]:
        print(f"{m['mean_days_small']:9.2f}  {m['false_alerts_per_week']:8.2f}  {m['missed_failures']:>6}  {m['dollar_detection_24h']:.0%}  {params}")
    print("CHOSEN LOOSE:", ok[0][0])
