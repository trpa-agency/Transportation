"""
test_model.py
-------------
Verification that the Python model reproduces the R-Shiny TEPM arithmetic.

The expected values below are computed independently from the R expressions in
app.R rather than from this package, so the test is a real check on the
translation and not a snapshot of whatever the Python happens to produce.

Run with pytest, or directly:

    python test_model.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from config import load_config, validate_inputs, ConfigError, strip_comments   # noqa: E402
from data_sources import (build_census_where, apply_data_sources,              # noqa: E402
                          classify_trip_types, DataSourceError)
from model import ModelInputs, DerivedInputRules, compute, build_segments      # noqa: E402
from sensitivity import run_sensitivity                                        # noqa: E402

CONFIG_DIR = SCRIPTS_DIR.parent / "configs"
DEFAULT_CONFIG = CONFIG_DIR / "default_config.json"

TOLERANCE = 1e-6


def r_model_reference(p: dict) -> dict:
    """
    Transcription of the R value-box expressions, written to mirror app.R line by
    line rather than to be readable. Any refactor of model.py is checked against
    this, so it must stay a literal restatement of the original.
    """
    # on_vis_pop() reactive
    on_vis = (
        (((p["hot_rooms"] / 365) * p["veh_per_room_hot"]) * p["veh_occ_hot"])
        + (((((p["hot_rooms"] / 365) * p["veh_per_room_hot"]) / p["leng_stay_hot"]) * p["veh_occ_hot"]))
        + (((p["vhr_rooms"] / 365) * p["veh_per_room_str"]) * p["veh_occ_str"])
        + (((((p["vhr_rooms"] / 365) * p["veh_per_room_str"]) / p["leng_stay_str"]) * p["veh_occ_str"]))
        + (((p["camp_rented"] / 365) * p["veh_per_room_camp"]) * p["veh_occ_camp"])
        + (((((p["camp_rented"] / 365) * p["veh_per_room_camp"]) / p["leng_stay_camp"]) * p["veh_occ_camp"]))
    )

    # renderUI defaults for freight and discretionary trips
    freight = round(p["EI_vol"] * 0.03)
    discretionary = round(round(on_vis) * 0.07) + 5750

    # day_vis_output value box
    day_vis = (
        p["EI_vol"]
        - freight
        - discretionary
        - p["commuter"]
        - p["resident_commute"]
        - (((p["hot_rooms"] / 365) * p["veh_per_room_hot"]) / p["leng_stay_hot"])
        - (((p["vhr_rooms"] / 365) * p["veh_per_room_str"]) / p["leng_stay_str"])
        - (((p["seas"] * p["second_home_occ"]) * p["veh_per_room_sec"]) / p["leng_stay_str"])
        - (((p["camp_rented"] / 365) * p["veh_per_room_camp"]) / p["leng_stay_camp"])
    ) * p["veh_occ_day"]

    # seas_vis_output value box
    seas_vis = (
        ((p["seas"] * p["second_home_occ"]) * p["veh_occ_sec"])
        + ((((p["seas"] * p["second_home_occ"]) * p["veh_per_room_sec"]) / p["leng_stay_str"]) * p["veh_occ_sec"])
    )

    # eff_pop_output value box
    effective = p["res"] + p["commuter"] + round(day_vis + on_vis + seas_vis)

    return {
        "overnight": on_vis,
        "day": day_vis,
        "second_home": seas_vis,
        "effective": effective,
        "freight": freight,
        "discretionary": discretionary,
    }


# Shiny defaults, with entry_volume and second homes as recomputed from the
# original StreetLight export and the 2018 ACS.
R_DEFAULTS = {
    "EI_vol": 25281,
    "res": 51577,
    "commuter": 4949,
    "resident_commute": 1800,
    "veh_occ_day": 2.62,
    "seas": 20580,
    "second_home_occ": 0.19,
    "veh_per_room_sec": 1.27,
    "veh_occ_sec": 1.97,
    "vhr_rooms": 482940,
    "veh_per_room_str": 2.07,
    "leng_stay_str": 4.28,
    "veh_occ_str": 3.92,
    "hot_rooms": 1754130,
    "veh_per_room_hot": 1.08,
    "leng_stay_hot": 3.44,
    "veh_occ_hot": 3.26,
    "camp_rented": 99284,
    "veh_per_room_camp": 1.18,
    "leng_stay_camp": 3.64,
    "veh_occ_camp": 3.26,
}


def default_inputs() -> ModelInputs:
    p = R_DEFAULTS
    return ModelInputs(
        entry_volume=p["EI_vol"],
        resident_population=p["res"],
        nonresident_commuters=p["commuter"],
        resident_commuters=p["resident_commute"],
        freight_trips=None,
        discretionary_trips=None,
        day_visitor_vehicle_occupancy=p["veh_occ_day"],
        second_homes=p["seas"],
        second_home_occupancy=p["second_home_occ"],
        vehicles_per_second_home=p["veh_per_room_sec"],
        second_home_vehicle_occupancy=p["veh_occ_sec"],
        second_home_length_of_stay=None,
        str_units_rented_annual=p["vhr_rooms"],
        vehicles_per_str_unit=p["veh_per_room_str"],
        str_length_of_stay=p["leng_stay_str"],
        str_vehicle_occupancy=p["veh_occ_str"],
        hotel_units_rented_annual=p["hot_rooms"],
        vehicles_per_hotel_room=p["veh_per_room_hot"],
        hotel_length_of_stay=p["leng_stay_hot"],
        hotel_vehicle_occupancy=p["veh_occ_hot"],
        campsites_rented_annual=p["camp_rented"],
        vehicles_per_campsite=p["veh_per_room_camp"],
        campsite_length_of_stay=p["leng_stay_camp"],
        campsite_vehicle_occupancy=p["veh_occ_camp"],
    )


# ==============================================================================
# Tests
# ==============================================================================

def test_matches_r_model_at_defaults():
    """Every sub-population matches the transcribed R expressions."""
    expected = r_model_reference(R_DEFAULTS)
    results = compute(default_inputs(), DerivedInputRules(), "test")

    assert abs(results.overnight_visitor_population - expected["overnight"]) < TOLERANCE
    assert abs(results.day_visitor_population - expected["day"]) < TOLERANCE
    assert abs(results.second_home_population - expected["second_home"]) < TOLERANCE
    assert abs(results.freight_trips - expected["freight"]) < TOLERANCE
    assert abs(results.discretionary_trips - expected["discretionary"]) < TOLERANCE
    assert results.effective_population == expected["effective"]


def test_matches_r_model_at_perturbed_values():
    """
    The translation holds away from the defaults too, including where the R model
    treats second homes differently from the other overnight segments.
    """
    perturbed = dict(R_DEFAULTS)
    perturbed.update({
        "EI_vol": 31000,
        "seas": 24000,
        "second_home_occ": 0.31,
        "veh_occ_day": 2.31,
        "leng_stay_str": 3.10,
        "hot_rooms": 2100000,
        "camp_rented": 140000,
    })
    expected = r_model_reference(perturbed)

    inputs = default_inputs()
    inputs.entry_volume = perturbed["EI_vol"]
    inputs.second_homes = perturbed["seas"]
    inputs.second_home_occupancy = perturbed["second_home_occ"]
    inputs.day_visitor_vehicle_occupancy = perturbed["veh_occ_day"]
    inputs.str_length_of_stay = perturbed["leng_stay_str"]
    inputs.hotel_units_rented_annual = perturbed["hot_rooms"]
    inputs.campsites_rented_annual = perturbed["camp_rented"]

    results = compute(inputs, DerivedInputRules(), "test")

    assert abs(results.overnight_visitor_population - expected["overnight"]) < TOLERANCE
    assert abs(results.day_visitor_population - expected["day"]) < TOLERANCE
    assert abs(results.second_home_population - expected["second_home"]) < TOLERANCE
    assert results.effective_population == expected["effective"]


def test_entry_volume_accounting_reconciles():
    """Subtracted components plus the day-visitor residual reconstruct entry volume."""
    results = compute(default_inputs(), DerivedInputRules(), "test")
    rows = results.entry_volume_rows()

    total = next(r["vehicles"] for r in rows if r["role"] == "input")
    parts = sum(r["vehicles"] for r in rows if r["role"] in ("subtracted", "residual"))
    assert abs(total - parts) < TOLERANCE


def test_second_home_stay_population_omits_vehicles_per_home():
    """
    Quirk preserved from the R model: the second-home stay population uses
    occupied homes, not vehicles, as its basis. See model.py module docstring.
    """
    inputs = default_inputs()
    segment = next(s for s in build_segments(inputs) if s.name == "Second home")
    occupied = inputs.second_homes * inputs.second_home_occupancy

    assert abs(segment.stay_population - occupied * inputs.second_home_vehicle_occupancy) < TOLERANCE
    assert segment.stay_population != segment.vehicles_present * segment.vehicle_occupancy


def test_second_home_length_of_stay_defaults_to_str():
    """Null second_home_length_of_stay falls back to the STR value, as in R."""
    inputs = default_inputs()
    inputs.second_home_length_of_stay = None
    segment = next(s for s in build_segments(inputs) if s.name == "Second home")
    assert segment.length_of_stay == inputs.str_length_of_stay

    inputs.second_home_length_of_stay = 9.0
    segment = next(s for s in build_segments(inputs) if s.name == "Second home")
    assert segment.length_of_stay == 9.0


def test_explicit_freight_overrides_derivation():
    """A number in the config wins over the derived rule."""
    inputs = default_inputs()
    inputs.freight_trips = 1200
    results = compute(inputs, DerivedInputRules(), "test")
    assert results.freight_trips == 1200


def test_default_config_reproduces_dashboard():
    """The shipped example config runs and lands on the R dashboard's value."""
    scenario = load_config(DEFAULT_CONFIG, allow_data_sources=False)
    results = compute(scenario.inputs, scenario.rules, scenario.scenario_name)
    expected = r_model_reference(R_DEFAULTS)
    assert results.effective_population == expected["effective"]
    assert not results.warnings


def test_default_config_covers_every_input():
    """The example config supplies every ModelInputs field, so it works as a template."""
    with open(DEFAULT_CONFIG, "r", encoding="utf-8") as f:
        cfg = strip_comments(json.load(f))
    from dataclasses import fields
    expected = {f.name for f in fields(ModelInputs)}
    assert set(cfg["inputs"]) == expected


def test_validation_rejects_bad_configs():
    """Validation catches unknown keys, missing keys and out-of-range values."""
    with open(DEFAULT_CONFIG, "r", encoding="utf-8") as f:
        base = strip_comments(json.load(f))["inputs"]

    for mutate, fragment in [
        (lambda d: d.update({"not_a_real_input": 1}), "unknown input key"),
        (lambda d: d.pop("entry_volume"), "missing required input"),
        (lambda d: d.update({"second_home_occupancy": 1.4}), "between 0 and 1"),
        (lambda d: d.update({"str_length_of_stay": 0}), "greater than 0"),
        (lambda d: d.update({"entry_volume": -5}), "may not be negative"),
        (lambda d: d.update({"resident_population": None}), "may not be null"),
        (lambda d: d.update({"entry_volume": "lots"}), "must be a number"),
    ]:
        candidate = dict(base)
        mutate(candidate)
        try:
            validate_inputs(candidate)
        except ConfigError as e:
            assert fragment in str(e), f"expected {fragment!r} in: {e}"
        else:
            raise AssertionError(f"validation should have failed for {fragment!r}")


def test_negative_day_visitors_warns():
    """An entry volume too small to cover known trips is flagged, not silently returned."""
    inputs = default_inputs()
    inputs.entry_volume = 5000
    results = compute(inputs, DerivedInputRules(), "test")
    assert results.day_visitor_vehicles < 0
    assert any("negative" in w for w in results.warnings)


def test_sensitivity_reruns_derived_inputs():
    """
    Varying entry volume must move the derived freight trips with it, which only
    happens if the sweep starts from the pre-resolution inputs.
    """
    base = default_inputs()
    rows = run_sensitivity(base, DerivedInputRules(),
                           {"variation": 0.10, "parameters": ["entry_volume"]}, "test")
    assert len(rows) == 1
    row = rows[0]

    # entry_volume +/-10% changes day visitor vehicles by 10% of entry volume net
    # of the 3% that re-derives as freight, times day visitor vehicle occupancy.
    expected_swing = 0.2 * base.entry_volume * (1 - 0.03) * base.day_visitor_vehicle_occupancy
    assert abs(row["swing"] - expected_swing) < 5   # rounding in the derived freight trips
    assert row["low_effective_population"] < row["high_effective_population"]


def test_sensitivity_skips_null_inputs():
    """Inputs with no scenario value are skipped rather than crashing the sweep."""
    rows = run_sensitivity(default_inputs(), DerivedInputRules(),
                           {"variation": 0.10, "parameters": None}, "test")
    assert rows
    swept = {r["parameter"] for r in rows}
    assert "freight_trips" not in swept
    assert "entry_volume" in swept
    # Ordered largest swing first, so the table reads as a tornado.
    assert rows == sorted(rows, key=lambda r: r["swing"], reverse=True)


# ==============================================================================
# Data sources (offline: no network calls)
# ==============================================================================

def test_census_where_clause_pins_every_dimension():
    """
    The where clause must pin variable, dataset, sample level and vintage, or the
    long-format table returns the same geography more than once and the sum
    double counts.
    """
    where = build_census_where({
        "variable_code": "B25004_006E",
        "dataset": "acs/acs5",
        "sample_level": "tract",
        "year_sample": 2018,
    })
    for fragment in ["variable_code = 'B25004_006E'", "dataset = 'acs/acs5'",
                     "sample_level = 'tract'", "year_sample = 2018.0",
                     "delete_flag"]:
        assert fragment in where, f"{fragment!r} missing from: {where}"


def test_census_where_clause_escapes_and_extends():
    """Apostrophes are escaped, and an extra where fragment is carried through."""
    where = build_census_where({"variable_code": "O'Brien", "where": "GEO_ID <> '32031990000'"})
    assert "'O''Brien'" in where
    assert "(GEO_ID <> '32031990000')" in where


def test_census_where_clause_requires_a_variable():
    try:
        build_census_where({"dataset": "acs/acs5"})
    except DataSourceError as e:
        assert "variable_code" in str(e)
    else:
        raise AssertionError("a missing variable_code should raise")


def test_disabled_data_sources_leave_inputs_alone():
    """A disabled block must not reach the network or change a value."""
    inputs = {"entry_volume": 25281, "second_homes": 20580}
    out, provenance, notes = apply_data_sources(
        inputs,
        {"entry_volume": {"enabled": False, "od_csv": "nope.csv"},
         "second_homes": {"enabled": False}},
        Path("."),
    )
    assert out == inputs
    assert provenance == {}
    assert notes == []


def test_unknown_data_source_is_rejected():
    try:
        apply_data_sources({}, {"made_up_input": {"enabled": True}}, Path("."))
    except DataSourceError as e:
        assert "made_up_input" in str(e)
    else:
        raise AssertionError("an unknown data source key should raise")


def test_streetlight_trip_type_classification():
    """Pass-through flags map onto the II/EI/IE/EE classification the R app used."""
    import pandas as pd
    df = pd.DataFrame({
        "Origin Zone Is Pass-Through":      ["no", "yes", "no", "yes", "YES "],
        "Destination Zone Is Pass-Through": ["no", "no", "yes", "yes", "no"],
    })
    assert list(classify_trip_types(df)) == ["II", "EI", "IE", "EE", "EI"]


def test_default_config_data_sources_are_disabled():
    """
    The shipped config must run with no network access, so every data source is
    off and the literal values stand on their own.
    """
    with open(DEFAULT_CONFIG, "r", encoding="utf-8") as f:
        cfg = strip_comments(json.load(f))
    for name, spec in cfg["data_sources"].items():
        assert spec.get("enabled") is False, f"{name} ships enabled"


# ==============================================================================

def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"  PASS  {test.__name__}")
        except Exception as e:
            failures += 1
            print(f"  FAIL  {test.__name__}: {e}")

    print(f"\n{len(tests) - failures}/{len(tests)} passed")

    if failures == 0:
        results = compute(default_inputs(), DerivedInputRules(), "TEPM_2018_Baseline")
        print("\nDefault scenario:")
        for row in results.population_rows():
            print(f"  {row['component']:<24} {row['population']:>12,.0f}")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
