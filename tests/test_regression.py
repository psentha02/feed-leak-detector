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
