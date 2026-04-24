"""
run_scenarios.py
----------------
Batch-run EIS housing scenarios from JSON config files.

Each run creates a timestamped folder under data/processed_data/ with the structure:

  run_YYYY-MM-DD_HHMMSS/
  ├── <scenario_name>/
  │   ├── 2035/          ← SocioEcon, SchoolEnrollment, visitors, config copy
  │   └── 2050/
  ├── persons_per_occ_unit/   ← written only by scenarios with adjust_taz_population=yes
  │   ├── persons_per_occ_unit_2035.csv
  │   └── persons_per_occ_unit_2050.csv
  ├── configs/               ← copy of every scenario config run
  ├── all_scenarios_parcels.parquet
  └── all_scenarios_parcels.shp  (+ sidecar files)

Usage
-----
  # Edit SCENARIO_CONFIGS below and run with no arguments:
  python run_scenarios.py

  # Or pass config paths directly on the command line:
  python run_scenarios.py path/to/alt1_config.json path/to/alt2_config.json
"""

import sys
import json
import shutil
import traceback
from datetime import datetime
from pathlib import Path

import arcpy
import numpy as np
import pandas as pd

# ── Ensure this script's directory is on sys.path so utils/forecast_functions import ──
SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))
from utils import *
from forecast_functions import *

# ── pandas options ─────────────────────────────────────────────────────────────
pd.options.mode.copy_on_write = True
pd.options.mode.chained_assignment = None

# ── ArcPy environment ──────────────────────────────────────────────────────────
arcpy.env.workspace = 'memory'
arcpy.env.overwriteOutput = True

# ── Shared path roots (relative to this script's parent = Forecast/) ──────────
FORECAST_DIR  = SCRIPTS_DIR.parent
DATA_DIR      = FORECAST_DIR / 'data'
OUT_DIR       = FORECAST_DIR / 'data' / 'processed_data'
BASE_DATA_DIR = FORECAST_DIR / 'data' / 'processed_data' / 'base_data'
EIS_DIR       = FORECAST_DIR.parent  # 2026_Housing_EIS/

# ── EDIT: directory containing scenario config JSONs ──────────────────────────
# Every *.json file directly in this folder is treated as a scenario config.
SCENARIO_DIR = FORECAST_DIR / 'configs_final_04242026'
# ──────────────────────────────────────────────────────────────────────────────


# ── Occupancy adjustment ───────────────────────────────────────────────────────
def adjust_occupied_units(df, additional_units, label, rng):
    """
    Proportionally scale total_occ_units upward by additional_units, distributing
    the extra units equally between medium and high income. Recomputes total_persons,
    rounds all counts to integers, then corrects rounding residuals so regional totals
    and per-TAZ income sums match exactly.
    """
    target_sum      = int(df["total_occ_units"].sum()) + additional_units
    additional_med  = additional_units / 2
    additional_high = additional_units / 2

    occ_factor = target_sum / df["total_occ_units"].sum()
    df["total_occ_units"] = df["total_occ_units"] * occ_factor

    current_med = df["occ_units_med_inc"].sum()
    df["occ_units_med_inc"] = df["occ_units_med_inc"] * (current_med + additional_med) / current_med

    current_high = df["occ_units_high_inc"].sum()
    df["occ_units_high_inc"] = df["occ_units_high_inc"] * (current_high + additional_high) / current_high

    df["total_persons"] = (df["total_occ_units"] * df["persons_per_occ_unit"]).round().astype(int)

    for col in ["total_occ_units", "occ_units_med_inc", "occ_units_high_inc"]:
        df[col] = df[col].round().astype(int)

    diff = target_sum - df["total_occ_units"].sum()
    if diff != 0:
        direction = 1 if diff > 0 else -1
        eligible  = df.index if direction == 1 else df.index[df["total_occ_units"] > 0]
        chosen    = rng.choice(eligible, size=abs(diff), replace=False)
        df.loc[chosen, "total_occ_units"] += direction
        print(f"  {label} total_occ_units adjusted by {diff:+d} units across {abs(diff)} random TAZs")

    income_sum     = df["occ_units_low_inc"] + df["occ_units_med_inc"] + df["occ_units_high_inc"]
    taz_diff       = df["total_occ_units"] - income_sum
    mismatch_count = (taz_diff != 0).sum()
    if mismatch_count > 0:
        df["occ_units_high_inc"] = df["occ_units_high_inc"] + taz_diff
        print(f"  {label}: income mismatch corrected in {mismatch_count} TAZs (adjusted occ_units_high_inc)")

    income_sum = df["occ_units_low_inc"] + df["occ_units_med_inc"] + df["occ_units_high_inc"]
    bad = (income_sum != df["total_occ_units"]).sum()
    print(f"{label} — occupied: {df['total_occ_units'].sum()} (target: {target_sum})  |  "
          f"income sum check: {'PASS' if bad == 0 else f'FAIL — {bad} TAZs mismatched'}")
    return df


# ── TAZ field mapping (constant across all scenarios) ─────────────────────────
TAZ_FIELD_MAPPING = {
    'TAZ':                               'TAZ',
    'TOTAL_FORECASTED_RESIDENTIAL_UNITS':'total_residential_units',
    'NEW_OCCUPANCY_RATE':                'census_occ_rate',
    'TOTAL_FORECASTED_UNITS_OCCUPIED':   'total_occ_units',
    'TOTAL_FORECASTED_UNITS_LOW_INCOME': 'occ_units_low_inc',
    'TOTAL_FORECASTED_UNITS_MED_INCOME': 'occ_units_med_inc',
    'TOTAL_FORECASTED_UNITS_HIGH_INCOME':'occ_units_high_inc',
    'persons_per_occ_unit':              'persons_per_occ_unit',
    'TOTAL_FORECASTED_PERSONS':          'total_persons',
    'emp_retail':                        'emp_retail',
    'emp_srvc':                          'emp_srvc',
    'emp_rec':                           'emp_rec',
    'emp_game':                          'emp_game',
    'emp_other':                         'emp_other',
}


def load_shared_data():
    """Load base datasets that are identical across all scenarios."""
    print("Loading shared base data...")

    sdfParcels = pd.read_parquet(BASE_DATA_DIR / 'base_parcel_data.parquet')

    dfSocio = pd.read_csv(EIS_DIR / 'Base' / 'data' / 'processed_data' / 'SocioEcon_Summer.csv')
    dfSocio.rename(columns={'taz': 'TAZ'}, inplace=True)
    dfSocio['TAZ'] = dfSocio['TAZ'].astype(str)

    dfSchool = pd.read_csv(EIS_DIR / 'Base' / 'data' / 'processed_data' / 'SchoolEnrollment.csv')

    persons_per_occ_unit_2035 = pd.read_csv(BASE_DATA_DIR / 'persons_per_occ_unit_2035.csv')
    persons_per_occ_unit_2050 = pd.read_csv(BASE_DATA_DIR / 'persons_per_occ_unit_2050.csv')

    dfOvernightVisitors = pd.read_csv(DATA_DIR / 'inputs' / 'OvernightVisitorZonalData_Summer.csv')
    dfVisitorOccupancy  = pd.read_csv(EIS_DIR / 'Base' / 'data' / 'processed_data' / 'VisitorOccupancyRates_Summer.csv')

    dfEmployment_2035 = pd.read_csv(DATA_DIR / 'inputs' / 'employment_2035.csv')
    dfEmployment_2050 = pd.read_csv(DATA_DIR / 'inputs' / 'employment_2050.csv')

    print("Shared base data loaded.\n")
    return {
        'sdfParcels':                sdfParcels,
        'dfSocio':                   dfSocio,
        'dfSchool':                  dfSchool,
        'persons_per_occ_unit_2035': persons_per_occ_unit_2035,
        'persons_per_occ_unit_2050': persons_per_occ_unit_2050,
        'dfOvernightVisitors':       dfOvernightVisitors,
        'dfVisitorOccupancy':        dfVisitorOccupancy,
        'dfEmployment_2035':         dfEmployment_2035,
        'dfEmployment_2050':         dfEmployment_2050,
    }


def export_combined_shapefile(df_all, run_folder):
    """
    Export the combined parcel DataFrame as a shapefile using ArcGIS SEDF.
    Requires a SHAPE column with geometry objects. Fails gracefully if geometry
    is absent or the export errors.
    """
    if 'SHAPE' not in df_all.columns:
        print("  Shapefile skipped — no SHAPE column in combined parcel data.")
        return

    temp_fc = 'memory/all_scenarios_parcels'
    try:
        sedf = pd.DataFrame.spatial.from_df(df_all, geometry_column='SHAPE')
        sedf.spatial.to_featureclass(temp_fc)
        arcpy.conversion.FeatureClassToShapefile([temp_fc], str(run_folder))
        arcpy.management.Delete(temp_fc)
        print(f"  Shapefile exported to {run_folder / 'all_scenarios_parcels.shp'}")
    except Exception as e:
        print(f"  Shapefile export failed: {e}")
        try:
            arcpy.management.Delete(temp_fc)
        except Exception:
            pass


def run_scenario(config_path, shared, run_folder):
    """
    Run a single forecast scenario end-to-end.

    Parameters
    ----------
    config_path : str or Path
        Path to the scenario JSON config file.
    shared : dict
        Pre-loaded base datasets from load_shared_data(). Mutated in-place when
        adjust_taz_population=yes to make updated persons_per_occ_unit available
        to subsequent scenarios in the same batch.
    run_folder : Path
        Timestamped root folder for this batch run. All outputs go under here.

    Returns
    -------
    sdfParcels : pd.DataFrame
        Forecast-annotated parcel data with a SCENARIO column, for concatenation
        across scenarios.
    """
    config_path  = Path(config_path)
    config_fname = config_path.name

    with open(config_path, 'r') as f:
        config = json.load(f)

    scenario_name           = config['scenario_name']
    adjust_for_workfromhome = config.get('adjust_for_workfromhome', 'no').strip().lower() == 'yes'
    adjust_occupancy        = config.get('adjust_occupancy', 'no').strip().lower() == 'yes'
    adjust_taz_pop          = config.get('adjust_taz_population', 'no').strip().lower() == 'yes'
    zone_proportions        = config['zone_proportions']
    occupancy_rates         = config['occupancy_rates']
    income_proportions      = config['income_proportions']

    if adjust_occupancy:
        additional_occupied_units = int(config['adjust_occupancy_additional_units'])
    if adjust_taz_pop:
        target_population_2035 = int(config['target_population_2035'])
        target_population_2050 = int(config['target_population_2050'])

    print(f"  Scenario:              {scenario_name}")
    print(f"  Config:                {config_path}")
    print(f"  Work-from-home col:    {adjust_for_workfromhome}")
    print(f"  Occupancy adjust:      {adjust_occupancy}")
    if adjust_occupancy:
        print(f"  Additional occ units:  {additional_occupied_units}")
    print(f"  TAZ population adjust: {adjust_taz_pop}")
    if adjust_taz_pop:
        print(f"  Target pop 2035:       {target_population_2035}")
        print(f"  Target pop 2050:       {target_population_2050}")

    # ── Output folders inside the run folder ──────────────────────────────────
    scenario_folder = run_folder / scenario_name
    folder_2035     = scenario_folder / '2035'
    folder_2050     = scenario_folder / '2050'
    folder_2035.mkdir(parents=True, exist_ok=True)
    folder_2050.mkdir(parents=True, exist_ok=True)

    # ── Fresh copy of parcels so scenarios don't bleed into each other ────────
    sdfParcels = shared['sdfParcels'].copy()

    # ── Build residential unit lookup from config ─────────────────────────────
    dfResZoned = pd.DataFrame(config['residential_units'])
    dfPool     = pd.DataFrame(config['residential_units'])
    dfPool     = get_adjusted_future_units(dfPool, zone_proportions)

    # ── Forecast pipeline ─────────────────────────────────────────────────────
    df_res_assigned_lookup = DATA_DIR / 'inputs' / 'res_assigned_lookup.csv'
    conditions = get_parcel_conditions()
    sdfParcels, df_built_parcels = forecast_jurisdiction_pools(sdfParcels, dfPool, conditions)
    sdfParcels, df_built_parcels = forecast_trpa_pools(sdfParcels, dfPool, conditions, df_built_parcels)
    sdfParcels, df_built_parcels = assign_remainders(sdfParcels, conditions, df_built_parcels, adu_target=4385)
    df_forecast_check = check_forecast_results(sdfParcels, dfPool)
    sdfParcels = assign_development_year(sdfParcels, dfResZoned)
    sdfParcels, dfResAssigned = assign_occupancy_rate(sdfParcels, occupancy_rates, df_res_assigned_lookup)
    sdfParcels = assign_income_categories(sdfParcels, dfResAssigned, income_proportions)

    # Tag parcels with scenario name before returning for concatenation
    sdfParcels['SCENARIO'] = scenario_name

    # ── Build TAZ summaries ───────────────────────────────────────────────────
    dfTAZ_Summary_2035, dfTAZ_Summary_2050 = build_taz_summary(sdfParcels, shared['dfSocio'])

    # ── Clean TAZ summaries ───────────────────────────────────────────────────
    df_taz_2035 = clean_taz_summary(dfTAZ_Summary_2035, TAZ_FIELD_MAPPING)
    df_taz_2050 = clean_taz_summary(dfTAZ_Summary_2050, TAZ_FIELD_MAPPING)

    # ── Persons per occupied unit — two modes ─────────────────────────────────
    #   adjust_taz_population=yes  → fit to regional targets, then save the lookup
    #                                to run_folder AND update shared for downstream
    #   (default)                  → apply the existing persons_per_occ_unit lookup
    if adjust_taz_pop:
        df_taz_2035 = adjust_taz_population(df_taz_2035, target_population=target_population_2035)
        df_taz_2050 = adjust_taz_population(df_taz_2050, target_population=target_population_2050)

        ppu_2035 = df_taz_2035[['TAZ', 'persons_per_occ_unit']].copy()
        ppu_2050 = df_taz_2050[['TAZ', 'persons_per_occ_unit']].copy()

        # Save to run folder
        ppu_folder = run_folder / 'persons_per_occ_unit'
        ppu_folder.mkdir(exist_ok=True)
        ppu_2035.to_csv(ppu_folder / 'persons_per_occ_unit_2035.csv', index=False)
        ppu_2050.to_csv(ppu_folder / 'persons_per_occ_unit_2050.csv', index=False)

        # Save to base_data so it persists for future independent runs
        ppu_2035.to_csv(BASE_DATA_DIR / 'persons_per_occ_unit_2035.csv', index=False)
        ppu_2050.to_csv(BASE_DATA_DIR / 'persons_per_occ_unit_2050.csv', index=False)

        # Update shared so subsequent scenarios in this batch use the new values
        shared['persons_per_occ_unit_2035'] = ppu_2035
        shared['persons_per_occ_unit_2050'] = ppu_2050

        print(f"  persons_per_occ_unit saved to {ppu_folder} and {BASE_DATA_DIR}")
    else:
        df_taz_2035 = adjust_taz_persons_per_occ_unit(df_taz_2035, shared['persons_per_occ_unit_2035'])
        df_taz_2050 = adjust_taz_persons_per_occ_unit(df_taz_2050, shared['persons_per_occ_unit_2050'])

    # ── Optional: occupancy adjustment ────────────────────────────────────────
    if adjust_occupancy:
        rng = np.random.default_rng(seed=42)
        df_taz_2035 = adjust_occupied_units(df_taz_2035, additional_occupied_units, "2035", rng)
        df_taz_2050 = adjust_occupied_units(df_taz_2050, additional_occupied_units, "2050", rng)
    else:
        print("  Occupancy adjustment skipped")

    # ── School enrollment ─────────────────────────────────────────────────────
    dfSchool_2035, dfSchool_2050 = adjust_school_enrollment(
        df_taz_2035, df_taz_2050, shared['dfSocio'], shared['dfSchool']
    )

    # ── Employment adjustment (always applied) ────────────────────────────────
    df_taz_2035 = update_employment_numbers(df_taz_2035, shared['dfEmployment_2035'])
    df_taz_2050 = update_employment_numbers(df_taz_2050, shared['dfEmployment_2050'])

    # ── Optional: add work-from-home jobs to emp_other ───────────────────────
    if adjust_for_workfromhome:
        wfh_csv = config.get('work_from_home_csv', 'taz_work_from_home.csv')
        dfWFH = pd.read_csv(DATA_DIR / 'inputs' / wfh_csv)
        dfWFH['TAZ'] = dfWFH['TAZ'].astype(int)
        df_taz_2035['TAZ'] = df_taz_2035['TAZ'].astype(int)
        df_taz_2050['TAZ'] = df_taz_2050['TAZ'].astype(int)
        df_taz_2035 = df_taz_2035.merge(dfWFH, on='TAZ', how='left')
        df_taz_2050 = df_taz_2050.merge(dfWFH, on='TAZ', how='left')
        df_taz_2035['emp_other'] = df_taz_2035['emp_other'] + df_taz_2035['work_from_home'].fillna(0)
        df_taz_2050['emp_other'] = df_taz_2050['emp_other'] + df_taz_2050['work_from_home'].fillna(0)
        df_taz_2035.drop(columns=['work_from_home'], inplace=True)
        df_taz_2050.drop(columns=['work_from_home'], inplace=True)
        print(f"  Work-from-home jobs added to emp_other ({wfh_csv})")
    else:
        print("  Work-from-home adjustment skipped")

    # Rename TAZ column for model input
    df_taz_2035.rename(columns={'TAZ': 'taz'}, inplace=True)
    df_taz_2050.rename(columns={'TAZ': 'taz'}, inplace=True)

    # ── Export final TAZ outputs ──────────────────────────────────────────────
    df_taz_2035.to_csv(folder_2035 / 'SocioEcon_Summer.csv',                        index=False)
    dfSchool_2035.to_csv(folder_2035 / 'SchoolEnrollment.csv',                      index=False)
    shared['dfOvernightVisitors'].to_csv(folder_2035 / 'OvernightVisitorZonalData_Summer.csv', index=False)
    shared['dfVisitorOccupancy'].to_csv(folder_2035 / 'VisitorOccupancyRates_Summer.csv',      index=False)

    df_taz_2050.to_csv(folder_2050 / 'SocioEcon_Summer.csv',                        index=False)
    dfSchool_2050.to_csv(folder_2050 / 'SchoolEnrollment.csv',                      index=False)
    shared['dfOvernightVisitors'].to_csv(folder_2050 / 'OvernightVisitorZonalData_Summer.csv', index=False)
    shared['dfVisitorOccupancy'].to_csv(folder_2050 / 'VisitorOccupancyRates_Summer.csv',      index=False)

    # ── Copy config to run_folder/configs/ and both year folders ──────────────
    configs_folder = run_folder / 'configs'
    configs_folder.mkdir(exist_ok=True)
    shutil.copy(config_path, configs_folder / config_fname)
    shutil.copy(config_path, folder_2035 / config_fname)
    shutil.copy(config_path, folder_2050 / config_fname)

    print(f"  Output 2035: {folder_2035}")
    print(f"  Output 2050: {folder_2050}")

    return sdfParcels


def main(scenario_dir):
    scenario_dir = Path(scenario_dir)
    config_paths = sorted(scenario_dir.glob('*.json'))
    if not config_paths:
        print(f"No .json files found in: {scenario_dir}")
        sys.exit(1)
    print(f"Found {len(config_paths)} config(s):")
    for p in config_paths:
        print(f"  {p}")

    # ── Create timestamped run folder ─────────────────────────────────────────
    run_ts     = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_folder = OUT_DIR / f"run_{run_ts}"
    run_folder.mkdir(parents=True, exist_ok=True)
    print(f"\nRun folder: {run_folder}\n")

    shared      = load_shared_data()
    results     = {}
    all_parcels = []

    for config_path in config_paths:
        name = Path(config_path).stem
        print(f"\n{'='*60}")
        print(f"Running scenario: {name}")
        print(f"{'='*60}")
        try:
            sdfParcels_scenario = run_scenario(config_path, shared, run_folder)
            results[name] = 'PASS'
            all_parcels.append(sdfParcels_scenario)
        except Exception:
            results[name] = 'FAIL'
            traceback.print_exc()

    # ── Combine parcels and export ────────────────────────────────────────────
    if all_parcels:
        print(f"\n{'='*60}")
        print("Exporting combined parcel data...")
        df_all = pd.concat(all_parcels, ignore_index=True)

        parquet_path = run_folder / 'all_scenarios_parcels.parquet'
        df_all.to_parquet(parquet_path, index=False)
        print(f"  Parquet saved to {parquet_path}")

        export_combined_shapefile(df_all, run_folder)

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"Batch complete — run folder: {run_folder}")
    print("Results:")
    for name, status in results.items():
        print(f"  {status}  {name}")
    print(f"{'='*60}")

    failed = [n for n, s in results.items() if s == 'FAIL']
    if failed:
        sys.exit(1)


if __name__ == '__main__':
    # Pass a directory as the first argument, or rely on SCENARIO_DIR above.
    scenario_dir = sys.argv[1] if len(sys.argv) > 1 else SCENARIO_DIR
    main(scenario_dir)
