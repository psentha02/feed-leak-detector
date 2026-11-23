import pandas as pd

from detectors import b0_rules, b1_expected
from evals.score import score_scenario
from generator.scenarios import SCENARIOS, TEST, TUNING, build

LABEL_FIELDS = {"incident_id", "case", "start_date", "end_date", "affected",
                "dollars_at_risk_per_day", "root_cause", "expected_evidence"}


def test_twenty_scenarios_split_ten_and_ten():
    assert len(TUNING) == 10 and len(TEST) == 10
    assert {SCENARIOS[n]["seed"] for n in TUNING} == {1, 2, 3, 4, 5}
    assert {c["case"] for n in SCENARIOS for c in SCENARIOS[n]["incidents"]} == {1, 3, 4, 9, 12, 13, 17}


def test_labels_match_specs_and_stay_out_of_the_feeds():
    for name in ("s1a", "s3b", "s4b", "s5a"):
        feeds, labels = build(name)
        assert len(labels) == len(SCENARIOS[name]["incidents"])
        assert all(set(l) == LABEL_FIELDS for l in labels)
        assert len({l["incident_id"] for l in labels}) == len(labels)
        for label, spec in zip(labels, SCENARIOS[name]["incidents"]):
            start = pd.Timestamp("2026-01-05") + pd.Timedelta(days=spec["start"])
            assert label["case"] == spec["case"] and label["start_date"] == start.date().isoformat()
        assert not any("incident" in c or "label" in c for f in feeds.values() for c in f.columns)


def test_dropped_store_label_matches_missing_rows():
    feeds, (label,) = build("s1a")
    days = pd.date_range(label["start_date"], label["end_date"])
    sales = feeds["sales"]
    present = sales[sales.file_date.isin(days)].store_id.unique()
    assert set(label["affected"]["stores"]).isdisjoint(present)


def test_build_is_repeatable():
    a, _ = build("s3b")
    b, _ = build("s3b")
    pd.testing.assert_frame_equal(a["sales"], b["sales"])


def test_scoring_matches_alerts_to_the_right_incident():
    feeds, labels = build("s2a")   # one stale-file incident
    records, false_alerts, _ = score_scenario(labels, b0_rules.run(feeds), 90)
    assert records[0]["alerted"] and records[0]["delay"] == 0 and records[0]["cause_ok"]
    assert false_alerts == 0


def test_b1_stays_quiet_on_a_clean_promo_scenario():
    feeds, labels = build("s1b")   # large promo spike on the calendar
    result = b1_expected.run(feeds)
    records, false_alerts, _ = score_scenario(labels, result, 90)
    assert false_alerts == 0 and records[0]["suppressed_ok"]
