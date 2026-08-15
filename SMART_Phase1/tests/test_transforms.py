"""
Transforms between the DERQ payload shape and the ArcGIS layer schema.

The regression these guard against: the previous ETL pushed DERQ's `count` and
`date` columns straight at a layer whose fields are `counts` and `Date`, so
every count and timestamp would have been written null.
"""

import json

import pandas as pd
import pytest

import transforms as T


# --- sample payloads, shaped exactly as the DERQ API returns them ----------


def derq_vehicle_frame():
    return pd.DataFrame(
        [
            {"count": 3.0, "date": "2025-06-30", "timeInterval": "02:30 PM - 02:44 PM",
             "movement": "TH", "lane": 1, "approach": "NB",
             "class": "passenger_vehicle"},
            {"count": 7.0, "date": "2025-06-30", "timeInterval": "02:30 PM - 02:44 PM",
             "movement": "TH", "lane": 2, "approach": "NB",
             "class": "passenger_vehicle"},
            {"count": 5.0, "date": "2025-07-01", "timeInterval": "08:00 AM - 08:14 AM",
             "movement": "LT", "lane": 1, "approach": "SB", "class": "bus"},
        ]
    ).assign(LocationId="662a21668158988de375fe1b", LocationName="US50 @ Cave Rock")


def derq_safety_frame():
    return pd.DataFrame(
        [
            {"EventType": "STPV", "EventId": "685fdf60", "DetectionArea": None,
             "TimeAtSite": "2025-06-28T05:26:08.316", "Direction": None,
             "CameraId": 0, "Object1Class": None, "Object2Class": None,
             "Movement": None},
        ]
    ).assign(LocationId="662b77297fef510a4a70c205", LocationName="US50 @ Zephyr Cove")


# --- field mapping ---------------------------------------------------------


def test_vehicle_counts_renamed_to_layer_fields(vehicle_cfg):
    """count -> counts and date -> Date. This is the core bug fix."""
    mapped = T.map_to_layer_schema(derq_vehicle_frame(), "vehicle_counts", vehicle_cfg)
    assert "counts" in mapped.columns and "count" not in mapped.columns
    assert "Date" in mapped.columns and "date" not in mapped.columns
    assert mapped["counts"].tolist() == [3.0, 7.0, 5.0]


def test_unmappable_fields_are_dropped(vehicle_cfg):
    """lane and movement have no target field on the frozen layer schema."""
    mapped = T.map_to_layer_schema(derq_vehicle_frame(), "vehicle_counts", vehicle_cfg)
    assert "lane" not in mapped.columns
    assert "movement" not in mapped.columns


def test_row_granularity_is_preserved(vehicle_cfg):
    """
    Dropping lane/movement must not collapse rows -- the published 450k rows
    and the DOI-archived dataset are at per-lane granularity.
    """
    source = derq_vehicle_frame()
    mapped = T.map_to_layer_schema(source, "vehicle_counts", vehicle_cfg)
    assert len(mapped) == len(source)
    assert mapped["counts"].sum() == source["count"].sum()


def test_location_columns_pass_through(vehicle_cfg):
    mapped = T.map_to_layer_schema(derq_vehicle_frame(), "vehicle_counts", vehicle_cfg)
    assert mapped["LocationId"].unique().tolist() == ["662a21668158988de375fe1b"]
    assert mapped["LocationName"].unique().tolist() == ["US50 @ Cave Rock"]


def test_output_columns_match_target_fields_exactly(vehicle_cfg):
    mapped = T.map_to_layer_schema(derq_vehicle_frame(), "vehicle_counts", vehicle_cfg)
    assert list(mapped.columns) == T.target_fields(vehicle_cfg)


def test_missing_derq_field_becomes_a_null_column(vehicle_cfg):
    """An API that stops sending a field must yield nulls, not a missing column."""
    source = derq_vehicle_frame().drop(columns=["approach"])
    mapped = T.map_to_layer_schema(source, "vehicle_counts", vehicle_cfg)
    assert "approach" in mapped.columns
    assert mapped["approach"].isna().all()


def test_unrecognised_field_is_dropped_with_warning(vehicle_cfg, caplog):
    source = derq_vehicle_frame().assign(brandNewField="surprise")
    mapped = T.map_to_layer_schema(source, "vehicle_counts", vehicle_cfg)
    assert "brandNewField" not in mapped.columns
    assert "brandNewField" in caplog.text


def test_empty_frame_returns_empty_with_target_columns(vehicle_cfg):
    mapped = T.map_to_layer_schema(pd.DataFrame(), "vehicle_counts", vehicle_cfg)
    assert mapped.empty
    assert list(mapped.columns) == T.target_fields(vehicle_cfg)


def test_safety_insights_is_an_identity_mapping(safety_cfg):
    mapped = T.map_to_layer_schema(derq_safety_frame(), "safety_insights", safety_cfg)
    assert list(mapped.columns) == T.target_fields(safety_cfg)
    assert mapped["EventType"].tolist() == ["STPV"]


def locations_frame():
    return pd.DataFrame(
        [
            {"LocationId": "662b77297fef510a4a70c205",
             "LocationName": "US50 @ Zephyr Cove", "Status": "Permanent"},
            {"LocationId": "6787d5c1555c462a1532abea",
             "LocationName": "Hwy 50 and Lake Pkwy", "Status": "Temporary"},
        ]
    )


def test_camera_status_is_joined_from_the_locations_layer(safety_cfg):
    """
    Camera_Status is not a DERQ field -- it is the camera's Status, populated on
    every one of the 24,244 existing rows. New rows must match.
    """
    mapped = T.map_to_layer_schema(
        derq_safety_frame(), "safety_insights", safety_cfg, locations_frame()
    )
    assert mapped["Camera_Status"].tolist() == ["Permanent"]


def test_camera_status_reflects_a_temporary_camera(safety_cfg):
    source = derq_safety_frame().assign(LocationId="6787d5c1555c462a1532abea")
    mapped = T.map_to_layer_schema(
        source, "safety_insights", safety_cfg, locations_frame()
    )
    assert mapped["Camera_Status"].tolist() == ["Temporary"]


def test_enriched_field_is_null_without_locations(safety_cfg, caplog):
    mapped = T.map_to_layer_schema(derq_safety_frame(), "safety_insights", safety_cfg)
    assert "Camera_Status" in mapped.columns
    assert mapped["Camera_Status"].isna().all()
    assert "cannot enrich" in caplog.text


def test_unmatched_location_leaves_camera_status_null(safety_cfg, caplog):
    source = derq_safety_frame().assign(LocationId="a-camera-not-in-the-layer")
    mapped = T.map_to_layer_schema(
        source, "safety_insights", safety_cfg, locations_frame()
    )
    assert mapped["Camera_Status"].isna().all()
    assert "no locations match" in caplog.text


def test_enriched_field_is_a_target_field(safety_cfg):
    assert "Camera_Status" in T.target_fields(safety_cfg)


def test_validate_flags_enrichment_colliding_with_field_map():
    cfg = {
        "layer_id": 1,
        "date_field": "TimeAtSite",
        "field_map": {"Camera_Status": "Camera_Status"},
        "enrich_from_locations": {"Camera_Status": "Status"},
    }
    problems = T.validate_field_map(
        "safety_insights", cfg,
        {"Camera_Status", "TimeAtSite", "LocationId", "LocationName"},
    )
    assert any("enrich_from_locations" in p for p in problems)


# --- field map validation --------------------------------------------------


def test_validate_field_map_accepts_the_real_schema(vehicle_cfg):
    live = {"OBJECTID", "counts", "timeInterval", "approach", "class",
            "LocationId", "LocationName", "Date"}
    assert T.validate_field_map("vehicle_counts", vehicle_cfg, live) == []


def test_validate_field_map_catches_the_original_bug():
    """A config mapping onto `count`/`date` must be rejected before any write."""
    broken = {
        "layer_id": 3,
        "date_field": "Date",
        "field_map": {"count": "count", "date": "date"},
    }
    live = {"counts", "Date", "LocationId", "LocationName"}
    problems = T.validate_field_map("vehicle_counts", broken, live)
    assert len(problems) == 2
    assert any("'count'" in p for p in problems)
    assert any("'date'" in p for p in problems)


def test_validate_field_map_catches_a_missing_date_field():
    cfg = {"layer_id": 3, "date_field": "ObservedOn", "field_map": {"count": "counts"}}
    problems = T.validate_field_map(
        "vehicle_counts", cfg, {"counts", "Date", "LocationId", "LocationName"}
    )
    assert any("ObservedOn" in p for p in problems)


# --- epoch conversion ------------------------------------------------------


def test_date_only_maps_to_utc_midnight():
    # 1751241600000 == 2025-06-30T00:00:00Z, matching how existing rows are stored.
    assert T.to_epoch_ms(pd.Series(["2025-06-30"])).tolist() == [1751241600000]


def test_timestamp_with_millis_round_trips():
    result = T.to_epoch_ms(pd.Series(["2025-06-28T05:26:08.316"])).iloc[0]
    assert pd.Timestamp(result, unit="ms", tz="UTC") == pd.Timestamp(
        "2025-06-28T05:26:08.316", tz="UTC"
    )


def test_nulls_and_garbage_become_na_not_int64_min():
    """A naive .astype('int64') turns NaT into INT64_MIN and writes year -292275055."""
    result = T.to_epoch_ms(pd.Series(["2025-06-30", None, "not a date"]))
    assert result.notna().tolist() == [True, False, False]
    assert result.dtype == "Int64"


def test_naive_timestamps_are_read_as_utc():
    naive = T.to_epoch_ms(pd.Series(["2025-06-30T12:00:00"])).iloc[0]
    explicit = T.to_epoch_ms(pd.Series(["2025-06-30T12:00:00+00:00"])).iloc[0]
    assert naive == explicit


# --- feature payloads ------------------------------------------------------


def test_features_are_json_serialisable(vehicle_cfg):
    mapped = T.map_to_layer_schema(derq_vehicle_frame(), "vehicle_counts", vehicle_cfg)
    features = T.to_arcgis_features(mapped, vehicle_cfg["target_date_fields"])
    json.dumps(features)  # numpy scalars would raise here


def test_features_carry_dates_as_epoch_ms(vehicle_cfg):
    mapped = T.map_to_layer_schema(derq_vehicle_frame(), "vehicle_counts", vehicle_cfg)
    features = T.to_arcgis_features(mapped, vehicle_cfg["target_date_fields"])
    assert features[0]["attributes"]["Date"] == 1751241600000
    assert features[0]["attributes"]["counts"] == 3.0


def test_nulls_become_none_not_nan(safety_cfg):
    mapped = T.map_to_layer_schema(derq_safety_frame(), "safety_insights", safety_cfg)
    attributes = T.to_arcgis_features(mapped, safety_cfg["target_date_fields"])[0][
        "attributes"
    ]
    assert attributes["DetectionArea"] is None
    assert "nan" not in json.dumps(attributes).lower()


def test_empty_frame_yields_no_features(vehicle_cfg):
    assert T.to_arcgis_features(pd.DataFrame(), ["Date"]) == []


# --- derived datasets ------------------------------------------------------


def test_daily_counts_totals_match_source(vehicle_cfg, daily_cfg):
    mapped = T.map_to_layer_schema(derq_vehicle_frame(), "vehicle_counts", vehicle_cfg)
    daily = T.compute_daily_counts(mapped, daily_cfg)
    assert daily["counts"].sum() == mapped["counts"].sum()


def test_daily_counts_collapses_to_one_row_per_day_and_location(vehicle_cfg, daily_cfg):
    mapped = T.map_to_layer_schema(derq_vehicle_frame(), "vehicle_counts", vehicle_cfg)
    daily = T.compute_daily_counts(mapped, daily_cfg)
    assert len(daily) == 2
    assert daily.loc[daily["Date"] == pd.Timestamp("2025-06-30"), "counts"].iloc[0] == 10.0


def test_daily_counts_groups_without_location_id(daily_cfg):
    """Layer 5 has no LocationId field, so it must not appear in the output."""
    assert "LocationId" not in daily_cfg["group_by"]
    mapped = T.map_to_layer_schema(
        derq_vehicle_frame(), "vehicle_counts",
        {"field_map": {"count": "counts", "date": "Date"}},
    )
    daily = T.compute_daily_counts(mapped, daily_cfg)
    assert "LocationId" not in daily.columns


def test_daily_counts_empty_input(daily_cfg):
    daily = T.compute_daily_counts(pd.DataFrame(), daily_cfg)
    assert daily.empty
    assert list(daily.columns) == ["Date", "LocationName", "counts"]


def test_speed_aggregates_across_chunk_boundaries(speed_cfg):
    """Two 30-day chunks covering the same interval must sum, not duplicate."""
    chunk = pd.DataFrame(
        [{"speedinterval": "25+ mph", "approach": "NB", "counts": 100.0,
          "LocationId": "abc", "LocationName": "Cave Rock"}]
    )
    aggregated = T.aggregate_speed([chunk, chunk.assign(counts=50.0)], speed_cfg)
    assert len(aggregated) == 1
    assert aggregated["counts"].iloc[0] == 150.0


def test_speed_keeps_distinct_intervals_separate(speed_cfg):
    frame = pd.DataFrame(
        [
            {"speedinterval": "20-24 mph", "approach": "NB", "counts": 3.0,
             "LocationId": "abc", "LocationName": "Cave Rock"},
            {"speedinterval": "25+ mph", "approach": "NB", "counts": 22984.0,
             "LocationId": "abc", "LocationName": "Cave Rock"},
        ]
    )
    aggregated = T.aggregate_speed([frame], speed_cfg)
    assert len(aggregated) == 2


def test_speed_empty_input(speed_cfg):
    assert T.aggregate_speed([], speed_cfg).empty
    assert T.aggregate_speed([pd.DataFrame()], speed_cfg).empty


# --- day selection ---------------------------------------------------------
#
# Day-precision selection cannot use timestamp literals on this service (the
# database compares stored UTC epochs as PST). Selection is: wide candidate
# clause -> read raw epochs -> exact epoch bounds.


def test_epoch_day_bounds_are_utc_midnights():
    start, end = T.epoch_day_bounds("2025-09-08")
    assert start == 1757289600000  # 2025-09-08T00:00:00Z
    assert end - start == 86_400_000


def test_epoch_day_bounds_are_half_open():
    _, end_of_sep8 = T.epoch_day_bounds("2025-09-08")
    start_of_sep9, _ = T.epoch_day_bounds("2025-09-09")
    assert end_of_sep8 == start_of_sep9


def test_candidate_clause_is_wide_enough_for_any_timezone():
    """+/-2 days covers any interpretation offset within +/-24h."""
    clause = T.candidate_day_clause("Date", "2025-09-08")
    assert "2025-09-06 00:00:00" in clause
    assert "2025-09-11 00:00:00" in clause


def test_candidate_clause_scoped_to_locations():
    """
    The delete must never be broader than the data replacing it, or a camera
    that had an API outage loses that day's existing rows.
    """
    clause = T.candidate_day_clause("Date", "2025-09-07", "LocationId", ["b", "a", "a"])
    assert "LocationId IN ('a', 'b')" in clause


def test_candidate_clause_escapes_quotes():
    clause = T.candidate_day_clause("Date", "2025-09-07", "LocationName", ["O'Brien Ave"])
    assert "'O''Brien Ave'" in clause


def test_candidate_clause_rolls_over_month_and_year_ends():
    assert "2025-10-03" in T.candidate_day_clause("Date", "2025-09-30")
    assert "2026-01-03" in T.candidate_day_clause("Date", "2025-12-31")


def test_sql_quote_escapes_embedded_quotes():
    assert T.sql_quote("O'Brien") == "'O''Brien'"


# --- boundary-day trimming -------------------------------------------------
#
# The DERQ API filters at UTC midnight but stamps data in Pacific local time,
# so both edge days of any request come back partial (verified live:
# 28/96 evening intervals before the window, 68/96 morning intervals on the
# last day). These guard the trim that keeps fragments out of day_replace.


def _dated_frame(dates):
    return pd.DataFrame({"date": dates, "count": [1.0] * len(dates)})


def test_trim_drops_rows_outside_the_window():
    frame = _dated_frame(["2025-09-01", "2025-09-02", "2025-09-03", "2025-09-04"])
    trimmed = T.trim_to_window(frame, "date", "2025-09-02", "2025-09-03")
    assert trimmed["date"].tolist() == ["2025-09-02", "2025-09-03"]


def test_trim_is_inclusive_of_both_endpoints():
    frame = _dated_frame(["2025-09-02", "2025-09-03"])
    trimmed = T.trim_to_window(frame, "date", "2025-09-02", "2025-09-03")
    assert len(trimmed) == 2


def test_trim_handles_full_timestamps():
    """Safety insights trim on TimeAtSite, a millisecond timestamp."""
    frame = pd.DataFrame(
        {"TimeAtSite": ["2025-09-01T23:59:59.999", "2025-09-02T00:00:00.000",
                        "2025-09-03T17:45:00.000"]}
    )
    trimmed = T.trim_to_window(frame, "TimeAtSite", "2025-09-02", "2025-09-02")
    assert trimmed["TimeAtSite"].tolist() == ["2025-09-02T00:00:00.000"]


def test_trim_empty_frame_is_a_noop():
    empty = pd.DataFrame()
    assert T.trim_to_window(empty, "date", "2025-09-01", "2025-09-02") is empty


# --- day iteration ---------------------------------------------------------


def test_iter_days_is_inclusive():
    days = [d.isoformat() for d in T.iter_days("2025-09-07", "2025-09-09")]
    assert days == ["2025-09-07", "2025-09-08", "2025-09-09"]


def test_iter_days_single_day():
    assert len(list(T.iter_days("2025-09-07", "2025-09-07"))) == 1


def test_iter_days_reversed_window_is_empty():
    assert list(T.iter_days("2025-09-09", "2025-09-07")) == []


@pytest.mark.parametrize(
    "value", ["2025-09-07", "2025-09-07T13:45:00", pd.Timestamp("2025-09-07")]
)
def test_parse_day_accepts_common_forms(value):
    assert T.parse_day(value).isoformat() == "2025-09-07"
