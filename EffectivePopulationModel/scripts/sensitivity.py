"""
sensitivity.py
--------------
One-at-a-time sensitivity analysis over model inputs.

The Shiny app's purpose was to let a user nudge an assumption and watch effective
population move. Without a GUI, the equivalent is to sweep each assumption
programmatically and report how much the answer moves -- a tornado table.

Each parameter is run low and high while every other input holds at its scenario
value. Inputs left null in the config (freight and discretionary trips) are
re-derived inside each run, so varying entry_volume correctly carries through to
the freight trips that depend on it.
"""

from __future__ import annotations

import copy

from model import ModelInputs, DerivedInputRules, compute

# Inputs worth sweeping by default: the behavioral and volumetric assumptions,
# excluding structural constants and values that are themselves derived.
DEFAULT_PARAMETERS = [
    "entry_volume",
    "resident_population",
    "nonresident_commuters",
    "resident_commuters",
    "day_visitor_vehicle_occupancy",
    "second_homes",
    "second_home_occupancy",
    "vehicles_per_second_home",
    "second_home_vehicle_occupancy",
    "str_units_rented_annual",
    "vehicles_per_str_unit",
    "str_length_of_stay",
    "str_vehicle_occupancy",
    "hotel_units_rented_annual",
    "vehicles_per_hotel_room",
    "hotel_length_of_stay",
    "hotel_vehicle_occupancy",
    "campsites_rented_annual",
    "vehicles_per_campsite",
    "campsite_length_of_stay",
    "campsite_vehicle_occupancy",
]


class SensitivityError(ValueError):
    """Raised when a sensitivity block names an input the model does not have."""


def _normalize_parameters(spec: dict, base: ModelInputs) -> list:
    """
    Turn the parameters list into [(name, low_value, high_value), ...].

    An entry may be a bare input name, in which case the default variation is
    applied multiplicatively, or a dict with explicit low/high values:

        "entry_volume"
        {"input": "entry_volume", "low": 22000, "high": 28000}
        {"input": "str_length_of_stay", "variation": 0.25}
    """
    variation = float(spec.get("variation", 0.10))
    entries = spec.get("parameters") or DEFAULT_PARAMETERS
    out = []

    for entry in entries:
        if isinstance(entry, str):
            name, low, high, var = entry, None, None, variation
        elif isinstance(entry, dict):
            name = entry.get("input")
            low, high = entry.get("low"), entry.get("high")
            var = float(entry.get("variation", variation))
        else:
            raise SensitivityError(f"Unrecognized sensitivity parameter entry: {entry!r}")

        if not name or not hasattr(base, name):
            raise SensitivityError(f"Unknown sensitivity parameter: {name!r}")

        value = getattr(base, name)
        if value is None:
            # Derived inputs have no scenario value to scale; skip rather than fail,
            # since they move anyway through whatever drives them.
            continue

        if low is None:
            low = value * (1.0 - var)
        if high is None:
            high = value * (1.0 + var)

        out.append((name, float(low), float(high)))

    return out


def run_sensitivity(base_inputs: ModelInputs,
                    rules: DerivedInputRules,
                    spec: dict,
                    scenario_name: str = "scenario") -> list:
    """
    Sweep each parameter low and high and measure the effect on effective population.

    Parameters
    ----------
    base_inputs : ModelInputs
        The scenario's inputs BEFORE compute resolved any nulls. Pass a copy taken
        at load time so derived inputs are re-derived in every sweep run.
    rules : DerivedInputRules
        Same rules the base run used.
    spec : dict
        The config's sensitivity block.
    scenario_name : str

    Returns
    -------
    list of dict
        One row per parameter, sorted by absolute swing (largest first) so the
        table reads as a tornado chart.
    """
    baseline = compute(copy.deepcopy(base_inputs), rules, scenario_name).effective_population
    rows = []

    for name, low_value, high_value in _normalize_parameters(spec, base_inputs):
        base_value = getattr(base_inputs, name)
        results = {}

        for label, value in (("low", low_value), ("high", high_value)):
            trial = copy.deepcopy(base_inputs)
            setattr(trial, name, value)
            results[label] = compute(trial, rules, f"{scenario_name}__{name}_{label}")

        low_pop = results["low"].effective_population
        high_pop = results["high"].effective_population
        swing = abs(high_pop - low_pop)

        rows.append({
            "parameter":                   name,
            "base_value":                  base_value,
            "low_value":                   low_value,
            "high_value":                  high_value,
            "baseline_effective_population": baseline,
            "low_effective_population":    low_pop,
            "high_effective_population":   high_pop,
            "low_change":                  low_pop - baseline,
            "high_change":                 high_pop - baseline,
            "swing":                       swing,
            "swing_pct_of_baseline":       (swing / baseline) if baseline else float("nan"),
        })

    rows.sort(key=lambda r: r["swing"], reverse=True)
    return rows
