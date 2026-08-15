"""
The DERQ UTC-boundary workaround, end to end against a fake HTTP layer.

Simulates the API's verified live behaviour -- a request for [D1, D2] returns
partial day D1-1 (evening), complete days D1..D2-2, and partial day D2-1
(morning) -- and asserts that fetch_window returns exactly the complete days
requested, with no fragments and no seam duplicates across chunks.
"""

from datetime import date, timedelta

import pandas as pd
import pytest

import derq_client as D
from transforms import parse_day


class FakeDerqApi:
    """
    Emulates DERQ's boundary behaviour. Every local day has 96 fifteen-minute
    rows; a request [start, end] yields the last 28 rows of start-1, all rows
    of start..end-2, and the first 68 rows of end-1.
    """

    def day_rows(self, day, intervals):
        return [
            {"count": 1.0, "date": day.isoformat(), "timeInterval": f"i{i:02d}",
             "approach": "NB", "class": "passenger_vehicle", "lane": 1,
             "movement": "TH"}
            for i in intervals
        ]

    def respond(self, start: str, end: str) -> list[dict]:
        first, last = parse_day(start), parse_day(end)
        rows = []
        rows += self.day_rows(first - timedelta(days=1), range(68, 96))  # evening
        day = first
        while day <= last - timedelta(days=2):
            rows += self.day_rows(day, range(96))                        # complete
            day += timedelta(days=1)
        rows += self.day_rows(last - timedelta(days=1), range(68))       # morning
        return rows


@pytest.fixture
def client(settings, monkeypatch):
    api = FakeDerqApi()
    settings.derq_api_key = "fake-key-for-tests"
    settings.derq["request_delay_seconds"] = 0
    instance = D.DerqClient(settings)

    def fake_get(url, label):
        query = dict(part.split("=", 1) for part in url.split("?", 1)[1].split("&"))
        return api.respond(query["startDate"], query["endDate"])

    monkeypatch.setattr(instance, "_get", fake_get)
    return instance


@pytest.fixture
def one_location():
    return pd.DataFrame(
        [{"LocationId": "loc-1", "LocationName": "Cave Rock", "Status": "Permanent"}]
    )


def fetch(client, cfg, locations, start, end):
    return client.fetch_window("vehicle_counts", cfg, locations, start, end)


def test_requested_days_come_back_complete(client, vehicle_cfg, one_location):
    result = fetch(client, vehicle_cfg, one_location, "2025-09-02", "2025-09-05")
    per_day = result.groupby("date").size()
    assert per_day.index.tolist() == [
        "2025-09-02", "2025-09-03", "2025-09-04", "2025-09-05"
    ]
    assert (per_day == 96).all(), f"partial day leaked through: {per_day.to_dict()}"


def test_no_partial_boundary_days_leak(client, vehicle_cfg, one_location):
    """Without the pad-and-trim, day 2025-09-01 (evening fragment) would load."""
    result = fetch(client, vehicle_cfg, one_location, "2025-09-02", "2025-09-05")
    assert "2025-09-01" not in set(result["date"])
    assert "2025-09-06" not in set(result["date"])


def test_single_day_window_is_complete(client, vehicle_cfg, one_location):
    """The case that returned 0 records live before the fix."""
    result = fetch(client, vehicle_cfg, one_location, "2025-09-08", "2025-09-08")
    assert set(result["date"]) == {"2025-09-08"}
    assert len(result) == 96


def test_multi_chunk_window_has_no_seam_duplicates(client, vehicle_cfg, one_location):
    """
    Padded requests overlap at chunk seams; per-chunk trimming must keep each
    day exactly once. 90 days forces several chunks at the 28-day stride.
    """
    start, end = date(2025, 9, 2), date(2025, 11, 30)
    result = fetch(client, vehicle_cfg, one_location, start.isoformat(), end.isoformat())

    per_day = result.groupby("date").size()
    expected_days = (end - start).days + 1
    assert len(per_day) == expected_days
    assert (per_day == 96).all(), (
        "seam duplication or partial day: "
        f"{per_day[per_day != 96].to_dict()}"
    )


def test_padded_requests_stay_within_the_api_cap(client, vehicle_cfg, one_location, monkeypatch):
    """Every actual request span must be <= 30 days even after the +2 pad."""
    spans = []
    original = client._get

    def spying_get(url, label):
        query = dict(part.split("=", 1) for part in url.split("?", 1)[1].split("&"))
        spans.append(
            (parse_day(query["endDate"]) - parse_day(query["startDate"])).days + 1
        )
        return original(url, label)

    monkeypatch.setattr(client, "_get", spying_get)
    fetch(client, vehicle_cfg, one_location, "2025-09-02", "2025-12-31")
    assert spans and max(spans) <= 30


def test_speed_requests_are_not_trimmed(client, speed_cfg, one_location):
    """Speed has no date field; rows must pass through untrimmed."""
    result = client.fetch_window(
        "speed", speed_cfg, one_location, "2025-09-02", "2025-09-05"
    )
    # The fake returns dated rows; the point is that nothing was filtered out.
    assert len(result) > 0
    assert "2025-09-01" in set(result["date"])