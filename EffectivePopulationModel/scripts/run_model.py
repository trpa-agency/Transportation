r"""
run_model.py
------------
Batch-run Tahoe Effective Population Model (TEPM) scenarios from JSON configs.

This is the non-interactive replacement for the TEPM R-Shiny dashboard. Instead
of moving sliders and reading value boxes, you write a scenario config and run
it; the model writes the same sub-population breakdown to CSV, plus the entry
volume accounting and input provenance the dashboard never exposed.

Each run creates a timestamped folder under data/processed_data/:

  run_YYYY-MM-DD_HHMMSS/
  |- <scenario_name>/
  |  |- effective_population_summary.csv   sub-population breakdown
  |  |- entry_volume_accounting.csv        how entry volume splits into trip groups
  |  |- overnight_segments.csv             per-segment vehicles and population
  |  |- model_inputs.csv                   every input with its value and provenance
  |  |- sensitivity_tornado.csv            only when sensitivity.enabled is true
  |  |- results.json                       machine-readable full result
  |  \- <config file name>                 copy of the config that produced it
  |- configs/                              copy of every config in the batch
  |- all_scenarios_summary.csv             one row per scenario, for comparison
  \- run_log.txt                           console output of the run

Usage
-----
  # Run every *.json in the default configs/ folder:
  python run_model.py

  # Run a specific config, or a folder of them:
  python run_model.py ../configs/default_config.json
  python run_model.py ../configs/sensitivity_test/

  # Ignore data_sources blocks and use the literal values in each config:
  python run_model.py --no-data-sources

  # Write outputs somewhere other than data/processed_data:
  python run_model.py --out-dir /path/to/output
"""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import sys
import traceback
from datetime import datetime
from pathlib import Path

import pandas as pd

# -- Ensure this script's directory is on sys.path so sibling modules import ----
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from config import load_config, ConfigError            # noqa: E402
from model import compute                              # noqa: E402
from sensitivity import run_sensitivity                # noqa: E402

# -- Shared path roots (relative to this script's parent = EffectivePopulationModel/) --
PACKAGE_DIR = SCRIPTS_DIR.parent
DATA_DIR = PACKAGE_DIR / "data"
OUT_DIR = DATA_DIR / "processed_data"
CONFIG_DIR = PACKAGE_DIR / "configs"


# ==============================================================================
# Input reporting metadata
# ==============================================================================

# Units and plain-language labels for model_inputs.csv, so the provenance table
# reads without cross-referencing the code.
INPUT_METADATA = {
    "entry_volume":                  ("vehicles/day", "Annual average daily inbound (EI) vehicles crossing an entry station"),
    "resident_population":           ("persons",      "Full-time resident population"),
    "nonresident_commuters":         ("persons/day",  "Workers commuting into the basin from outside"),
    "resident_commuters":            ("persons/day",  "Residents commuting out of the basin"),
    "freight_trips":                 ("vehicles/day", "Freight vehicles among the entry trips"),
    "discretionary_trips":           ("vehicles/day", "Residents and overnight visitors leaving and re-entering the basin"),
    "day_visitor_vehicle_occupancy": ("persons/veh",  "Average people per day visitor vehicle"),
    "second_homes":                  ("units",        "Seasonal/recreational/occasional housing units, net of short-term rentals"),
    "second_home_occupancy":         ("share 0-1",    "Share of second homes occupied on an average day"),
    "vehicles_per_second_home":      ("vehicles/unit", "Average vehicles per occupied second home"),
    "second_home_vehicle_occupancy": ("persons/veh",  "Average people per second home vehicle"),
    "second_home_length_of_stay":    ("nights",       "Average second home stay length (null uses the STR length of stay)"),
    "str_units_rented_annual":       ("unit-nights",  "Annual short-term rental unit-nights rented"),
    "vehicles_per_str_unit":         ("vehicles/unit", "Average vehicles per rented STR unit"),
    "str_length_of_stay":            ("nights",       "Average STR stay length"),
    "str_vehicle_occupancy":         ("persons/veh",  "Average people per STR visitor vehicle"),
    "hotel_units_rented_annual":     ("room-nights",  "Annual hotel/motel/resort/casino room-nights rented"),
    "vehicles_per_hotel_room":       ("vehicles/room", "Average vehicles per rented hotel room"),
    "hotel_length_of_stay":          ("nights",       "Average hotel stay length"),
    "hotel_vehicle_occupancy":       ("persons/veh",  "Average people per hotel visitor vehicle"),
    "campsites_rented_annual":       ("site-nights",  "Annual campsite-nights rented"),
    "vehicles_per_campsite":         ("vehicles/site", "Average vehicles per rented campsite"),
    "campsite_length_of_stay":       ("nights",       "Average campsite stay length"),
    "campsite_vehicle_occupancy":    ("persons/veh",  "Average people per campground vehicle"),
    "days_per_year":                 ("days",         "Days used to convert annual unit-nights to an average day"),
}


class Tee:
    """Write console output to stdout and a run log at the same time."""

    def __init__(self, path):
        self._file = open(path, "w", encoding="utf-8")
        self._stdout = sys.stdout

    def write(self, text):
        self._stdout.write(text)
        self._file.write(text)

    def flush(self):
        self._stdout.flush()
        self._file.flush()

    def close(self):
        self._file.close()


def build_inputs_table(scenario, results, pristine_inputs) -> pd.DataFrame:
    """
    Every model input with its resolved value, unit, description and provenance.

    Provenance is "config" for a literal, "data_source" for a value computed from
    StreetLight or the Census API, and "derived" for a null the model filled in
    from derived_input_rules.

    pristine_inputs must be the pre-compute copy of the inputs: compute() resolves
    nulls in place, so the scenario's own inputs no longer show which were null.
    """
    resolved = results.inputs
    rows = []
    for name, (unit, description) in INPUT_METADATA.items():
        value = getattr(resolved, name, None)
        source = scenario.provenance.get(name, "config")
        # A value the config left null but the model filled is derived, not config.
        if source != "data_source" and getattr(pristine_inputs, name, None) is None and value is not None:
            source = "derived"
        rows.append({
            "input":       name,
            "value":       value,
            "unit":        unit,
            "source":      source,
            "description": description,
        })
    return pd.DataFrame(rows)


def format_population_report(results) -> str:
    """Render the sub-population breakdown the way the dashboard's value boxes read."""
    lines = []
    width = 30
    for row in results.population_rows():
        name, value = row["component"], row["population"]
        if name == "Effective population":
            lines.append("  " + "-" * (width + 14))
            lines.append(f"  {name:<{width}} {value:>13,.0f}")
        else:
            lines.append(f"  {name:<{width}} {value:>13,.0f}   ({row['share_of_total']:>5.1%})")
    lines.append(f"  {'Peaking ratio (eff/resident)':<{width}} {results.peaking_ratio:>13.2f}")
    return "\n".join(lines)


# ==============================================================================
# Single scenario
# ==============================================================================

def run_scenario(config_path, run_folder, allow_data_sources=True):
    """
    Load, run and write out one scenario.

    Parameters
    ----------
    config_path : Path
        Scenario config JSON.
    run_folder : Path
        Timestamped root folder for this batch. Outputs go in a subfolder named
        after the scenario.
    allow_data_sources : bool
        Passed through to the config loader.

    Returns
    -------
    ModelResults
    """
    config_path = Path(config_path)
    scenario = load_config(config_path, data_dir=DATA_DIR, allow_data_sources=allow_data_sources)

    print(f"  Scenario:  {scenario.scenario_name}")
    print(f"  Config:    {config_path}")
    if scenario.description:
        print(f"  Purpose:   {scenario.description}")
    for note in scenario.notes:
        print(f"  Source:    {note}")

    # Keep a pre-resolution copy: compute() fills nulls in place, and the
    # sensitivity sweep needs the original nulls so they re-derive each run.
    pristine_inputs = copy.deepcopy(scenario.inputs)

    results = compute(scenario.inputs, scenario.rules, scenario.scenario_name)

    for warning in results.warnings:
        print(f"  WARNING:   {warning}")

    print()
    print(format_population_report(results))
    print()

    # -- Output folder ---------------------------------------------------------
    scenario_folder = run_folder / scenario.scenario_name
    scenario_folder.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(results.population_rows()).to_csv(
        scenario_folder / "effective_population_summary.csv", index=False)
    pd.DataFrame(results.entry_volume_rows()).to_csv(
        scenario_folder / "entry_volume_accounting.csv", index=False)
    pd.DataFrame(results.segment_rows()).to_csv(
        scenario_folder / "overnight_segments.csv", index=False)
    build_inputs_table(scenario, results, pristine_inputs).to_csv(
        scenario_folder / "model_inputs.csv", index=False)

    # -- Optional sensitivity sweep -------------------------------------------
    sens_spec = scenario.sensitivity or {}
    if sens_spec.get("enabled"):
        rows = run_sensitivity(pristine_inputs, scenario.rules, sens_spec, scenario.scenario_name)
        pd.DataFrame(rows).to_csv(scenario_folder / "sensitivity_tornado.csv", index=False)
        print(f"  Sensitivity: {len(rows)} parameters swept "
              f"(+/-{sens_spec.get('variation', 0.10):.0%} unless overridden)")
        for row in rows[:5]:
            print(f"    {row['parameter']:<32} swing {row['swing']:>8,.0f} "
                  f"({row['swing_pct_of_baseline']:>5.1%} of baseline)")
        print()

    # -- Machine-readable result and config copy ------------------------------
    payload = results.to_dict()
    payload["config_file"] = config_path.name
    payload["description"] = scenario.description
    payload["source_notes"] = scenario.notes
    with open(scenario_folder / "results.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    shutil.copy(config_path, scenario_folder / config_path.name)

    configs_folder = run_folder / "configs"
    configs_folder.mkdir(exist_ok=True)
    shutil.copy(config_path, configs_folder / config_path.name)

    print(f"  Output:    {scenario_folder}")
    return results


# ==============================================================================
# Batch
# ==============================================================================

def collect_configs(targets) -> list:
    """Expand a mix of directories and file paths into a sorted list of configs."""
    paths = []
    for target in targets:
        target = Path(target)
        if target.is_dir():
            paths.extend(sorted(target.glob("*.json")))
        elif target.is_file():
            paths.append(target)
        else:
            raise ConfigError(f"Config path not found: {target}")
    return paths


def main(targets, out_dir=OUT_DIR, allow_data_sources=True) -> int:
    config_paths = collect_configs(targets)
    if not config_paths:
        print(f"No .json config files found in: {', '.join(str(t) for t in targets)}")
        return 1

    run_ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_folder = Path(out_dir) / f"run_{run_ts}"
    run_folder.mkdir(parents=True, exist_ok=True)

    tee = Tee(run_folder / "run_log.txt")
    stdout = sys.stdout
    sys.stdout = tee

    try:
        print(f"Tahoe Effective Population Model")
        print(f"Run started {datetime.now():%Y-%m-%d %H:%M:%S}")
        print(f"Run folder:  {run_folder}")
        print(f"Data sources: {'enabled' if allow_data_sources else 'disabled (--no-data-sources)'}")
        print(f"\nFound {len(config_paths)} config(s):")
        for p in config_paths:
            print(f"  {p}")

        statuses = {}
        summary_rows = []

        for config_path in config_paths:
            name = config_path.stem
            print(f"\n{'=' * 70}")
            print(f"Running scenario: {name}")
            print(f"{'=' * 70}")
            try:
                results = run_scenario(config_path, run_folder, allow_data_sources)
                statuses[name] = "PASS"
                summary_rows.append(results.summary_row())
            except Exception:
                statuses[name] = "FAIL"
                traceback.print_exc(file=sys.stdout)

        # -- Cross-scenario comparison ----------------------------------------
        if summary_rows:
            df = pd.DataFrame(summary_rows)
            # Difference from the first scenario, which acts as the baseline.
            baseline = df.loc[0, "effective_population"]
            df["change_from_baseline"] = df["effective_population"] - baseline
            df["pct_change_from_baseline"] = df["change_from_baseline"] / baseline if baseline else float("nan")
            df.to_csv(run_folder / "all_scenarios_summary.csv", index=False)
            print(f"\n{'=' * 70}")
            print("Scenario comparison (baseline = first scenario)")
            print(f"{'=' * 70}")
            for _, row in df.iterrows():
                print(f"  {row['scenario_name']:<40} "
                      f"{row['effective_population']:>10,.0f}  "
                      f"{row['change_from_baseline']:>+9,.0f}")

        # -- Summary ----------------------------------------------------------
        print(f"\n{'=' * 70}")
        print(f"Batch complete -- run folder: {run_folder}")
        print("Results:")
        for name, status in statuses.items():
            print(f"  {status}  {name}")
        print(f"{'=' * 70}")

        return 1 if any(s == "FAIL" for s in statuses.values()) else 0
    finally:
        sys.stdout = stdout
        tee.close()


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Run Tahoe Effective Population Model scenarios from JSON configs.")
    parser.add_argument(
        "configs", nargs="*", default=[str(CONFIG_DIR)],
        help=f"Config files or folders of configs. Default: {CONFIG_DIR}")
    parser.add_argument(
        "--out-dir", default=str(OUT_DIR),
        help=f"Where the timestamped run folder is written. Default: {OUT_DIR}")
    parser.add_argument(
        "--no-data-sources", action="store_true",
        help="Ignore data_sources blocks and use the literal values in each config.")
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    try:
        sys.exit(main(args.configs, Path(args.out_dir), not args.no_data_sources))
    except ConfigError as e:
        print(f"Config error: {e}", file=sys.stderr)
        sys.exit(2)
