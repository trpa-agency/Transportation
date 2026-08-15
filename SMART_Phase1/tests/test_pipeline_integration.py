"""
End-to-end exercise of the load path, using the committed Phase 1 CSVs as
stand-in DERQ payloads and a fake ArcGIS client that records every call.

Covers the parts that can be verified without credentials: that a real DERQ
payload survives mapping, that the delete matches the add, and that running the
same window twice issues identical calls.
"""

from pathlib import Path

import pandas as pd
import pytest

import transforms as T
from run_etl import load_day_replace, load_full_replace

DATA_DIR = Path(__file__).resolve().parents[1] / "Data"
SAMPLE = "vehicle_counts_06_28_2025_to_07_14_2025.csv"


class FakeClient:
    """Records replace_day / truncate / add_features calls instead of issuing them."""

    def __init__(self):
        self.calls = []
        self.deleted_rows = 0

    def replace_day(self, layer_id, date_field, day, features, label,
                    scope_field=None, scope_values=None):
        self.calls.append(
            ("replace_day", layer_id, date_field, str(day), len(features),
             scope_field, tuple(sorted(set(scope_values or []))))
        )
        return len(features), len(features)

    def truncate(self, layer_id):
        self.calls.append(("truncate", layer_id))
        return self.deleted_rows

    def add_features(self, layer_id, features):
        self.calls.append(("add_features", layer_id, len(features)))
        return len(features)


@pytest.fixture(scope="module")
def derq_payload():
    """A real DERQ vehicle-counts payload, as saved during Phase 1."""
    path = DATA_DIR / SAMPLE
    if not path.exists():
        pytest.skip(f"{SAMPLE} not present")
    df = pd.read_csv(path)
    # Trim to two locations to keep the test quick but still multi-location.
    keep = df["LocationId"].unique()[:2]
    return df[df["LocationId"].isin(keep)].reset_index(drop=True)


def test_real_payload_maps_without_loss(derq_payload, vehicle_cfg):
    mapped = T.map_to_layer_schema(derq_payload, "vehicle_counts", vehicle_cfg)
    assert len(mapped) == len(derq_payload)
    assert mapped["counts"].sum() == derq_payload["count"].sum()
    assert mapped["counts"].notna().all()
    assert mapped["Date"].notna().all()


def test_one_replace_call_per_day(derq_payload, vehicle_cfg):
    mapped = T.map_to_layer_schema(derq_payload, "vehicle_counts", vehicle_cfg)
    client = FakeClient()
    totals = load_day_replace(client, vehicle_cfg, mapped, "vehicle_counts", dry_run=False)

    expected_days = mapped["Date"].nunique()
    assert totals["days"] == expected_days
    assert len(client.calls) == expected_days


def test_every_fetched_row_is_added(derq_payload, vehicle_cfg):
    mapped = T.map_to_layer_schema(derq_payload, "vehicle_counts", vehicle_cfg)
    client = FakeClient()
    load_day_replace(client, vehicle_cfg, mapped, "vehicle_counts", dry_run=False)
    assert sum(call[4] for call in client.calls) == len(mapped)


def test_delete_is_scoped_to_locations_that_returned_data(derq_payload, vehicle_cfg):
    """
    The delete must never be broader than the data replacing it, or a camera
    with an API outage that day loses its existing rows.
    """
    mapped = T.map_to_layer_schema(derq_payload, "vehicle_counts", vehicle_cfg)
    client = FakeClient()
    load_day_replace(client, vehicle_cfg, mapped, "vehicle_counts", dry_run=False)

    for _, _, _, day, _, scope_field, scope_values in client.calls:
        present = set(mapped.loc[
            pd.to_datetime(mapped["Date"]).dt.date.astype(str) == day, "LocationId"
        ])
        assert scope_field == "LocationId"
        assert set(scope_values) == present


def test_rerunning_the_same_window_issues_identical_calls(derq_payload, vehicle_cfg):
    """
    Idempotency at the call level: same input, same deletes, same adds. The
    live equivalent is re-running one day and seeing the row count unchanged.
    """
    mapped = T.map_to_layer_schema(derq_payload, "vehicle_counts", vehicle_cfg)

    first, second = FakeClient(), FakeClient()
    load_day_replace(first, vehicle_cfg, mapped, "vehicle_counts", dry_run=False)
    load_day_replace(second, vehicle_cfg, mapped, "vehicle_counts", dry_run=False)

    assert first.calls == second.calls


def test_dry_run_issues_no_calls(derq_payload, vehicle_cfg):
    mapped = T.map_to_layer_schema(derq_payload, "vehicle_counts", vehicle_cfg)
    client = FakeClient()
    load_day_replace(client, vehicle_cfg, mapped, "vehicle_counts", dry_run=True)
    assert client.calls == []


def test_empty_fetch_writes_nothing(vehicle_cfg):
    """An API outage must not delete anything."""
    client = FakeClient()
    totals = load_day_replace(
        client, vehicle_cfg, pd.DataFrame(), "vehicle_counts", dry_run=False
    )
    assert client.calls == []
    assert totals == {"days": 0, "deleted": 0, "added": 0}


def test_undated_rows_are_skipped_not_written(vehicle_cfg, caplog):
    mapped = pd.DataFrame(
        {
            "counts": [1.0, 2.0],
            "Date": ["2025-06-30", None],
            "timeInterval": ["a", "b"],
            "approach": ["NB", "NB"],
            "class": ["passenger_vehicle", "passenger_vehicle"],
            "LocationId": ["x", "x"],
            "LocationName": ["Cave Rock", "Cave Rock"],
        }
    )
    client = FakeClient()
    load_day_replace(client, vehicle_cfg, mapped, "vehicle_counts", dry_run=False)
    assert sum(call[4] for call in client.calls) == 1
    assert "unparseable" in caplog.text


def test_daily_counts_derive_and_load(derq_payload, vehicle_cfg, daily_cfg):
    mapped = T.map_to_layer_schema(derq_payload, "vehicle_counts", vehicle_cfg)
    daily = T.compute_daily_counts(mapped, daily_cfg)

    client = FakeClient()
    load_day_replace(client, daily_cfg, daily, "daily_counts", dry_run=False)

    assert all(call[1] == daily_cfg["layer_id"] for call in client.calls)
    # Layer 5 has no LocationId, so the delete scopes by name.
    assert all(call[5] == "LocationName" for call in client.calls)
    assert daily["counts"].sum() == mapped["counts"].sum()


def test_speed_full_replace_truncates_then_loads(speed_cfg):
    mapped = pd.DataFrame(
        [{"speedinterval": "25+ mph", "approach": "NB", "counts": 100.0,
          "LocationId": "abc", "LocationName": "Cave Rock"}]
    )
    client = FakeClient()
    load_full_replace(client, speed_cfg, mapped, "speed", dry_run=False)
    assert [call[0] for call in client.calls] == ["truncate", "add_features"]


def test_speed_refuses_to_truncate_on_an_empty_fetch(speed_cfg, caplog):
    """A DERQ outage must not wipe the Speed layer."""
    client = FakeClient()
    load_full_replace(client, speed_cfg, pd.DataFrame(), "speed", dry_run=False)
    assert client.calls == []
    assert "refusing to truncate" in caplog.text
