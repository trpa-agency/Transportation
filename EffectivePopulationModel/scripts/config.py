"""
config.py
---------
Load, validate and resolve Tahoe Effective Population Model scenario configs.

A scenario config is a single JSON file. Keys prefixed with an underscore
(_comment, _note, ...) are treated as documentation and ignored everywhere, which
lets configs carry inline explanation the way the 2026 Housing EIS forecast
configs do.

Config shape
------------
{
  "scenario_name":        "<label used for the output folder>",
  "description":          "<free text, optional>",
  "inputs":               { ... every ModelInputs field ... },
  "derived_input_rules":  { ... optional, defaults to the R model's rules ... },
  "data_sources":         { ... optional, recompute inputs from source data ... },
  "sensitivity":          { ... optional one-at-a-time parameter sweep ... },
  "outputs":              { ... optional output-format switches ... }
}

Resolution order for any one input
----------------------------------
    1. data_sources  (when enabled -- computed from StreetLight / Census)
    2. inputs        (the literal value in the config)
    3. derived rules (only for inputs explicitly set to null)

Every value carries a provenance label through to model_inputs.csv so a run can
be traced back to where each number came from.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Optional

from model import ModelInputs, DerivedInputRules, DAYS_PER_YEAR

# Inputs that may legitimately be null in a config; the model derives them.
NULLABLE_INPUTS = {"freight_trips", "discretionary_trips", "second_home_length_of_stay"}

# Inputs that must be strictly positive when supplied.
POSITIVE_INPUTS = {
    "day_visitor_vehicle_occupancy",
    "vehicles_per_second_home", "second_home_vehicle_occupancy",
    "vehicles_per_str_unit", "str_length_of_stay", "str_vehicle_occupancy",
    "vehicles_per_hotel_room", "hotel_length_of_stay", "hotel_vehicle_occupancy",
    "vehicles_per_campsite", "campsite_length_of_stay", "campsite_vehicle_occupancy",
}

# Inputs that must not be negative.
NONNEGATIVE_INPUTS = {
    "entry_volume", "resident_population", "nonresident_commuters", "resident_commuters",
    "freight_trips", "discretionary_trips", "second_homes",
    "str_units_rented_annual", "hotel_units_rented_annual", "campsites_rented_annual",
}


class ConfigError(ValueError):
    """Raised when a scenario config is missing or malformed."""


@dataclass
class ScenarioConfig:
    """A validated, fully resolved scenario ready to hand to model.compute."""

    scenario_name: str
    description: str
    inputs: ModelInputs
    rules: DerivedInputRules
    sensitivity: dict = field(default_factory=dict)
    outputs: dict = field(default_factory=dict)
    provenance: dict = field(default_factory=dict)   # input name -> source label
    notes: list = field(default_factory=list)
    config_path: Optional[Path] = None


# ==============================================================================
# Helpers
# ==============================================================================

def strip_comments(obj):
    """Recursively drop underscore-prefixed documentation keys."""
    if isinstance(obj, dict):
        return {k: strip_comments(v) for k, v in obj.items() if not k.startswith("_")}
    if isinstance(obj, list):
        return [strip_comments(v) for v in obj]
    return obj


def input_field_names() -> list:
    """Field names of ModelInputs, in declaration order."""
    return [f.name for f in fields(ModelInputs)]


# ==============================================================================
# Validation
# ==============================================================================

def validate_inputs(raw: dict) -> dict:
    """
    Check that the inputs block has every required key with a usable value.

    Raises
    ------
    ConfigError
        On unknown keys, missing keys, non-numeric values, nulls in fields that
        cannot be derived, or values outside their valid range. All problems are
        collected and reported together rather than one per run.
    """
    known = set(input_field_names())
    problems = []

    unknown = sorted(set(raw) - known)
    if unknown:
        problems.append(f"unknown input key(s): {', '.join(unknown)}")

    # days_per_year has a default on ModelInputs, so it is optional in the config.
    required = known - {"days_per_year"}
    missing = sorted(required - set(raw))
    if missing:
        problems.append(f"missing required input(s): {', '.join(missing)}")

    for name, value in raw.items():
        if name not in known:
            continue
        if value is None:
            if name not in NULLABLE_INPUTS:
                problems.append(
                    f"{name} may not be null "
                    f"(only {', '.join(sorted(NULLABLE_INPUTS))} may be null)"
                )
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            problems.append(f"{name} must be a number, got {value!r}")
            continue
        if name in POSITIVE_INPUTS and value <= 0:
            problems.append(f"{name} must be greater than 0, got {value}")
        if name in NONNEGATIVE_INPUTS and value < 0:
            problems.append(f"{name} may not be negative, got {value}")

    occ = raw.get("second_home_occupancy")
    if isinstance(occ, (int, float)) and not isinstance(occ, bool) and not 0.0 <= occ <= 1.0:
        problems.append(f"second_home_occupancy must be between 0 and 1, got {occ}")

    days = raw.get("days_per_year", DAYS_PER_YEAR)
    if isinstance(days, (int, float)) and not isinstance(days, bool) and days <= 0:
        problems.append(f"days_per_year must be greater than 0, got {days}")

    if problems:
        raise ConfigError("Invalid inputs block:\n  - " + "\n  - ".join(problems))

    return raw


# ==============================================================================
# Loading
# ==============================================================================

def load_config(config_path, data_dir=None, allow_data_sources=True) -> ScenarioConfig:
    """
    Read a scenario config JSON and return a validated ScenarioConfig.

    Parameters
    ----------
    config_path : str or Path
        Path to the scenario JSON.
    data_dir : Path, optional
        Root for resolving relative paths in the data_sources block. Defaults to
        <package root>/data.
    allow_data_sources : bool
        When False, enabled data_sources blocks are skipped and the literal
        values in the inputs block are used instead. Useful for a fast run with
        no network access or large source CSVs present.

    Raises
    ------
    ConfigError
        If the file is missing, is not valid JSON, or fails validation.
    """
    config_path = Path(config_path)
    if not config_path.is_file():
        raise ConfigError(f"Config file not found: {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigError(f"{config_path.name} is not valid JSON: {e}") from e

    cfg = strip_comments(raw)

    scenario_name = cfg.get("scenario_name") or config_path.stem
    description = cfg.get("description", "")

    if "inputs" not in cfg or not isinstance(cfg["inputs"], dict):
        raise ConfigError(f"{config_path.name} has no 'inputs' object.")

    raw_inputs = dict(cfg["inputs"])
    provenance = {k: "config" for k in raw_inputs}
    notes = []

    # -- Optional: recompute selected inputs from source data -----------------
    data_sources = cfg.get("data_sources", {})
    if allow_data_sources and data_sources:
        # Imported lazily: data_sources pulls in pandas/urllib only when used.
        from data_sources import apply_data_sources

        if data_dir is None:
            data_dir = Path(__file__).resolve().parent.parent / "data"
        raw_inputs, ds_prov, ds_notes = apply_data_sources(raw_inputs, data_sources, Path(data_dir))
        provenance.update(ds_prov)
        notes.extend(ds_notes)
    elif data_sources and not allow_data_sources:
        enabled = [k for k, v in data_sources.items() if isinstance(v, dict) and v.get("enabled")]
        if enabled:
            notes.append(
                f"data_sources skipped (--no-data-sources): {', '.join(enabled)}. "
                f"Literal config values used instead."
            )

    validate_inputs(raw_inputs)

    # Nullable fields absent from the config are treated as explicit nulls.
    for name in NULLABLE_INPUTS:
        raw_inputs.setdefault(name, None)
        provenance.setdefault(name, "config")

    inputs = ModelInputs(**raw_inputs)

    # -- Derived input rules --------------------------------------------------
    rule_cfg = cfg.get("derived_input_rules", {})
    known_rules = {f.name for f in fields(DerivedInputRules)}
    unknown_rules = sorted(set(rule_cfg) - known_rules)
    if unknown_rules:
        raise ConfigError(
            f"{config_path.name}: unknown derived_input_rules key(s): {', '.join(unknown_rules)}"
        )
    rules = DerivedInputRules(**rule_cfg)

    return ScenarioConfig(
        scenario_name=scenario_name,
        description=description,
        inputs=inputs,
        rules=rules,
        sensitivity=cfg.get("sensitivity", {}),
        outputs=cfg.get("outputs", {}),
        provenance=provenance,
        notes=notes,
        config_path=config_path,
    )
