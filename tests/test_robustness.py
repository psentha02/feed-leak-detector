import numpy as np
import pandas as pd

from detectors.b1_expected import _grid


def test_rows_with_unknown_store_ids_are_ignored_not_written_to_the_last_store():
    dates = pd.DatetimeIndex(["2026-01-05", "2026-01-06"])
    stores, upcs = pd.Index(["S01", "S02"]), pd.Index(["u1"])
    rows = pd.DataFrame({"file_date": dates[[0, 0, 0]], "store_id": ["S01", "S02", "S99"],
                         "upc": "u1", "units": [1, 2, 777]})
    grid = _grid(rows, "units", dates, stores, upcs)
    assert grid[0, :, 0].tolist() == [1, 2]          # S99 did not overwrite S02
    assert np.isnan(grid[1]).all()
