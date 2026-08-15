"""Date-window chunking for the DERQ API's 30-day request limit."""

from datetime import date

import pytest

from derq_client import build_date_chunks


def test_single_day():
    assert build_date_chunks("2025-09-07", "2025-09-07") == [
        ("2025-09-07", "2025-09-07")
    ]


def test_exactly_thirty_days_is_one_chunk():
    chunks = build_date_chunks("2025-09-01", "2025-09-30")
    assert chunks == [("2025-09-01", "2025-09-30")]


def test_thirty_one_days_splits():
    chunks = build_date_chunks("2025-09-01", "2025-10-01")
    assert chunks == [("2025-09-01", "2025-09-30"), ("2025-10-01", "2025-10-01")]


def test_chunks_are_contiguous_and_cover_the_window():
    chunks = build_date_chunks("2025-09-07", "2026-08-06")
    assert chunks[0][0] == "2025-09-07"
    assert chunks[-1][1] == "2026-08-06"
    for (_, prev_end), (next_start, _) in zip(chunks, chunks[1:]):
        assert date.fromisoformat(next_start) - date.fromisoformat(prev_end) == (
            date(2000, 1, 2) - date(2000, 1, 1)
        )


def test_no_chunk_exceeds_the_limit():
    for start, end in build_date_chunks("2025-09-07", "2026-08-06"):
        span = date.fromisoformat(end) - date.fromisoformat(start)
        assert span.days < 30


def test_already_up_to_date_returns_empty():
    """start after end is how 'nothing to fetch' is expressed."""
    assert build_date_chunks("2025-09-08", "2025-09-07") == []


def test_accepts_date_objects():
    assert build_date_chunks(date(2025, 9, 7), date(2025, 9, 8)) == [
        ("2025-09-07", "2025-09-08")
    ]


@pytest.mark.parametrize("max_days", [1, 7, 30])
def test_respects_custom_max_days(max_days):
    chunks = build_date_chunks("2025-01-01", "2025-03-01", max_days=max_days)
    for start, end in chunks:
        assert (date.fromisoformat(end) - date.fromisoformat(start)).days < max_days
