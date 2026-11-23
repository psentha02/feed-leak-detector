"""Existing tuning scenarios must stay byte-identical when the generator grows.
tests/golden.json was recorded before the notices feed and the new cases were added."""
import hashlib
import json
from pathlib import Path

import pytest

from generator.scenarios import build

GOLDEN = json.loads((Path(__file__).parent / "golden.json").read_text())


@pytest.mark.parametrize("name", sorted(GOLDEN["feeds"]))
def test_existing_scenario_feeds_are_byte_identical(name):
    feeds, _ = build(name)
    for key, expected in GOLDEN["feeds"][name].items():
        assert hashlib.sha256(feeds[key].to_csv(index=False).encode()).hexdigest() == expected, (name, key)


def _compare(system, run):
    from evals.score import score_scenario
    for name, golden in GOLDEN["results"][system].items():
        feeds, labels = build(name)
        records, false_alerts, _ = score_scenario(labels, run(feeds), feeds)
        got = [{k: r.get(k) for k in ("id", "alerted", "delay", "cause_ok", "suppressed_ok")} for r in records]
        assert got == golden["records"] and false_alerts == golden["false_alerts"], name


def test_b0_results_on_the_original_tuning_scenarios_are_unchanged():
    from detectors import b0_rules
    _compare("B0", b0_rules.run)


def test_b1_default_params_reproduce_the_original_tuning_results():
    from detectors import b1_expected
    _compare("B1", b1_expected.run)
    _compare("B1", lambda feeds: b1_expected.run(feeds, params=b1_expected.PRESETS["default"]))
