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
  └── parcels.gdb/           ← one attributed parcel feature class per scenario
      └── <scenario_name>_parcels

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

import pyarrow  # noqa: F401 -- must load before arcpy, whose DLLs break pyarrow's
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
# Static parcel polygons joined to forecast output by APN (see make_parcel_geometry_snapshot.py)
PARCEL_GEOMETRY_FC = BASE_DATA_DIR / 'parcel_geometry.gdb' / 'parcel_geometry'

# ── EDIT: directory containing scenario config JSONs ──────────────────────────
# Every *.json file directly in this folder is treated as a scenario config.
SCENARIO_DIR = FORECAST_DIR / 'configs_wfh' / 'configs_10162026'
# ──────────────────────────────────────────────────────────────────────────────


# ── Occupancy adjustment ───────────────────────────────────────────────────────
INCOME_COLS = {
    "low":    "occ_units_low_inc",
    "medium": "occ_units_med_inc",
    "high":   "occ_units_high_inc",
}
DEFAULT_OCC_INCOME_DISTRIBUTION = {"low": 0.0, "medium": 0.5, "high": 0.5}


def _round_to_total(values, total):
    """Round non-negative floats to ints that sum exactly to total (largest remainder)."""
    values  = np.asarray(values, dtype=float)
    floored = np.floor(values).astype(int)
    short   = int(total - floored.sum())
    if short > 0:
        floored[np.argsort(-(values - floored), kind="stable")[:short]] += 1
    return floored


def _allocate_capped(total, weights, capacity):
    """
    Split total across rows in proportion to weights without exceeding each row's
    capacity. Units that would overflow a full row are re-spread over rows that
    still have room (falling back to remaining capacity as the weight when every
    weighted row is full). Returns ints summing exactly to total.
    """
    weights   = np.asarray(weights, dtype=float)
    capacity  = np.asarray(capacity, dtype=float)
    alloc     = np.zeros_like(capacity)
    remaining = float(total)
    while remaining > 1e-9:
        room      = capacity - alloc
        open_rows = room > 1e-9
        w = np.where(open_rows, weights, 0.0)
        if w.sum() <= 0:
            w = np.where(open_rows, room, 0.0)
        take = np.minimum(remaining * w / w.sum(), room)
        alloc     += take
        remaining -= take.sum()
    # Only round up rows with a whole unit of room left, so the cap still holds
    floored = np.floor(alloc + 1e-9).astype(int)
    short   = int(total - floored.sum())
    if short > 0:
        frac = np.where(capacity - floored >= 1, alloc - floored, -1.0)
        floored[np.argsort(-frac, kind="stable")[:short]] += 1
    return floored


def _controlled_round(x, row_totals, col_totals):
    """Round a float matrix to ints matching both row_totals and col_totals exactly."""
    out     = np.floor(x).astype(int)
    row_res = row_totals - out.sum(axis=1)
    col_res = col_totals - out.sum(axis=0)
    frac    = x - out
    for flat in np.argsort(-frac, axis=None, kind="stable"):
        i, j = np.unravel_index(flat, x.shape)
        if row_res[i] > 0 and col_res[j] > 0:
            out[i, j]  += 1
            row_res[i] -= 1
            col_res[j] -= 1
    # Leftovers: row and column residuals sum to the same amount, so greedy fill is always feasible
    for i in np.where(row_res > 0)[0]:
        while row_res[i] > 0:
            j = int(np.argmax(col_res))
            out[i, j]  += 1
            row_res[i] -= 1
            col_res[j] -= 1
    return out


def adjust_occupied_units(df, additional_units, label, income_distribution=None):
    """
    Add exactly additional_units occupied units to the basin, split across
    low/medium/high income according to income_distribution (e.g.
    {"low": 0.2, "medium": 0.3, "high": 0.5}; normalized to sum to 1, defaults to
    half medium / half high).

    Priority order:
      1. Basin total of added units equals additional_units exactly.
      2. Basin added units by income match income_distribution exactly (to the unit).
      3. No TAZ's occupied units exceed its residential units.
      4. Within those constraints, added units go to TAZs in proportion to their
         existing occupied units (overflow from full TAZs is re-spread to TAZs with
         room), and each TAZ's income mix follows the existing basin pattern as
         closely as the basin targets allow.
    """
    if income_distribution is None:
        income_distribution = DEFAULT_OCC_INCOME_DISTRIBUTION
    dist_total = sum(float(income_distribution.get(k, 0)) for k in INCOME_COLS)
    if dist_total <= 0:
        raise ValueError(f"{label}: income_distribution must have a positive total, got {income_distribution}")
    keys        = list(INCOME_COLS)
    income_cols = list(INCOME_COLS.values())
    dist        = np.array([float(income_distribution.get(k, 0)) / dist_total for k in keys])

    # ── Integer baseline: round occupied units and make income columns sum to them ──
    res      = df["total_residential_units"].round().astype(int).to_numpy()
    occ      = df["total_occ_units"].round().astype(int).to_numpy()
    base_inc = df[income_cols].to_numpy(dtype=float).clip(min=0)
    for i in range(len(df)):
        row_sum     = base_inc[i].sum()
        shares      = base_inc[i] / row_sum if row_sum > 0 else dist
        base_inc[i] = _round_to_total(shares * occ[i], occ[i])
    base_inc = base_inc.astype(int)

    capacity = np.clip(res - occ, 0, None)
    if capacity.sum() < additional_units:
        raise ValueError(
            f"{label}: cannot add {additional_units} occupied units; only {int(capacity.sum())} "
            f"unoccupied residential units are available across all TAZs")

    # ── Basin targets by income (exact integers) ─────────────────────────────
    income_targets = _round_to_total(dist * additional_units, additional_units)

    # ── Added units per TAZ: proportional to existing occupied units, capped ─
    added_taz = _allocate_capped(additional_units, occ, capacity)

    # ── Split each TAZ's added units across income to hit basin targets ──────
    # Seed with each TAZ's share of each category's existing basin units (occupied-unit
    # share when a category has none), then IPF to match TAZ totals and basin targets
    occ_share = occ / occ.sum() if occ.sum() > 0 else np.full(len(occ), 1 / len(occ))
    cat_sums  = base_inc.sum(axis=0)
    seed = np.column_stack([
        base_inc[:, j] / cat_sums[j] if cat_sums[j] > 0 else occ_share for j in range(len(keys))
    ]) * income_targets
    x = (seed + 1e-6) * (added_taz > 0)[:, None] * (income_targets > 0)[None, :]
    for _ in range(500):
        row = x.sum(axis=1)
        x   = x * np.divide(added_taz, row, out=np.zeros_like(row), where=row > 0)[:, None]
        col = x.sum(axis=0)
        x   = x * np.divide(income_targets, col, out=np.zeros_like(col), where=col > 0)[None, :]
        if np.abs(x.sum(axis=1) - added_taz).max() < 1e-6:
            break
    added_inc = _controlled_round(x, added_taz, income_targets)

    # ── Write back ───────────────────────────────────────────────────────────
    new_inc = base_inc + added_inc
    df["total_occ_units"] = occ + added_taz
    for j, col in enumerate(income_cols):
        df[col] = new_inc[:, j]
    df["total_persons"] = (df["total_occ_units"] * df["persons_per_occ_unit"]).round().astype(int)

    # ── Checks ───────────────────────────────────────────────────────────────
    n_full     = int(((added_taz > 0) & (added_taz == capacity)).sum())
    added_tot  = int(added_taz.sum())
    added_cat  = added_inc.sum(axis=0)
    over_cap   = int((df["total_occ_units"] > res).sum())
    mismatched = int((df[income_cols].sum(axis=1) != df["total_occ_units"]).sum())
    ok = (added_tot == additional_units and (added_cat == income_targets).all()
          and over_cap == 0 and mismatched == 0)
    split = ", ".join(f"{k}: +{int(a)}" for k, a in zip(keys, added_cat))
    if n_full:
        print(f"  {label}: {n_full} TAZ(s) filled to residential cap; overflow re-spread to TAZs with room")
    print(f"{label} — added occupied: {added_tot} (target: {additional_units})  |  {split}  |  "
          f"over cap: {over_cap}  |  income sum mismatches: {mismatched}  |  {'PASS' if ok else 'FAIL'}")
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

    # Forecast-year TAUs match the final 2025 RTP model inputs (RTP Data Archive:
    # 2035_FINAL_Scen3_Red_21Dec_2 and 2050_1_5PctInc), so the EIS uses the same TAUs as the RTP
    dfOvernightVisitors_2035 = pd.read_csv(DATA_DIR / 'inputs' / 'OvernightVisitorZonalData_Summer_2035.csv')
    dfOvernightVisitors_2050 = pd.read_csv(DATA_DIR / 'inputs' / 'OvernightVisitorZonalData_Summer_2050.csv')
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
        'dfOvernightVisitors_2035':  dfOvernightVisitors_2035,
        'dfOvernightVisitors_2050':  dfOvernightVisitors_2050,
        'dfVisitorOccupancy':        dfVisitorOccupancy,
        'dfEmployment_2035':         dfEmployment_2035,
        'dfEmployment_2050':         dfEmployment_2050,
    }


def _arcpy_field_type(series):
    """Map a pandas column to an ArcGIS field type and text length."""
    if pd.api.types.is_bool_dtype(series):
        return 'SHORT', None
    if pd.api.types.is_integer_dtype(series):
        vals = series.dropna()
        fits_long = vals.empty or (vals.min() >= -2**31 and vals.max() < 2**31)
        return ('LONG' if fits_long else 'DOUBLE'), None
    if pd.api.types.is_numeric_dtype(series):
        return 'DOUBLE', None
    max_len = series.dropna().astype(str).str.len().max()
    return 'TEXT', max(int(max_len) if pd.notna(max_len) else 0, 10)


def export_scenario_feature_classes(df_all, run_folder):
    """
    Export one fully attributed parcel feature class per scenario to
    <run_folder>/parcels.gdb, joining forecast rows to the static parcel
    geometry snapshot (base_data/parcel_geometry.gdb) by APN.
    Raises if the snapshot is missing or any APN has no geometry.
    """
    if not arcpy.Exists(str(PARCEL_GEOMETRY_FC)):
        raise FileNotFoundError(
            f"Parcel geometry snapshot not found: {PARCEL_GEOMETRY_FC}\n"
            "  Build it once with scripts/make_parcel_geometry_snapshot.py")

    with arcpy.da.SearchCursor(str(PARCEL_GEOMETRY_FC), ['APN', 'SHAPE@WKB']) as cur:
        geometry = {apn: bytes(wkb) for apn, wkb in cur}
    sr = arcpy.Describe(str(PARCEL_GEOMETRY_FC)).spatialReference

    missing = set(df_all['APN']) - set(geometry)
    if missing:
        raise ValueError(f"{len(missing)} APNs have no geometry in the snapshot, e.g. {sorted(missing)[:5]}")

    gdb = run_folder / 'parcels.gdb'
    if not gdb.exists():
        arcpy.management.CreateFileGDB(str(run_folder), gdb.name)

    field_specs = [(col, *_arcpy_field_type(df_all[col])) for col in df_all.columns]

    # Rows are inserted into memory and copied to the gdb in one pass —
    # row-by-row inserts straight into a file gdb are several times slower
    temp_fc = 'memory/scenario_parcels'
    cols    = [col for col, _, _ in field_specs]

    for scenario, df in df_all.groupby('SCENARIO', sort=False):
        fc_name = arcpy.ValidateTableName(f"{scenario}_parcels", str(gdb))
        arcpy.management.CreateFeatureclass('memory', 'scenario_parcels', 'POLYGON', spatial_reference=sr)
        arcpy.management.AddFields(temp_fc, [
            [col, ftype, col, length] if ftype == 'TEXT' else [col, ftype]
            for col, ftype, length in field_specs
        ])

        rows = df[cols].astype(object).where(df[cols].notna(), None).itertuples(index=False, name=None)
        with arcpy.da.InsertCursor(temp_fc, cols + ['SHAPE@WKB']) as cur:
            for row, apn in zip(rows, df['APN']):
                cur.insertRow(row + (geometry[apn],))

        arcpy.management.CopyFeatures(temp_fc, str(gdb / fc_name))
        arcpy.management.Delete(temp_fc)
        print(f"  {fc_name}: {len(df):,} parcels")

    print(f"  Feature classes exported to {gdb}")


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
    adjust_for_occ_unit_emp = config.get('adjust_for_occ_unit_emp', 'no').strip().lower() == 'yes'
    adjust_occupancy        = config.get('adjust_occupancy', 'no').strip().lower() == 'yes'
    adjust_taz_pop          = config.get('adjust_taz_population', 'no').strip().lower() == 'yes'
    zone_proportions        = config['zone_proportions']
    occupancy_rates         = config['occupancy_rates']
    income_proportions      = config['income_proportions']

    if adjust_occupancy:
        additional_occupied_units_2035 = int(config['adjust_occupancy_additional_units_2035'])
        additional_occupied_units_2050 = int(config['adjust_occupancy_additional_units_2050'])
        occ_income_distribution        = config.get('adjust_occupancy_income_distribution',
                                                    DEFAULT_OCC_INCOME_DISTRIBUTION)
    if adjust_taz_pop:
        target_population_2035 = int(config['target_population_2035'])
        target_population_2050 = int(config['target_population_2050'])

    print(f"  Scenario:              {scenario_name}")
    print(f"  Config:                {config_path}")
    print(f"  Occ unit emp adjust:   {adjust_for_occ_unit_emp}")
    print(f"  Occupancy adjust:      {adjust_occupancy}")
    if adjust_occupancy:
        print(f"  Additional occ units 2035: {additional_occupied_units_2035}")
        print(f"  Additional occ units 2050: {additional_occupied_units_2050}")
        print(f"  Additional occ income split: {occ_income_distribution}")
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
    total_future_units = dfPool['Future_Units'].sum()
    assigned_units = 874
    total_future_units = total_future_units + assigned_units

    # ── Forecast pipeline ─────────────────────────────────────────────────────
    df_res_assigned_lookup = DATA_DIR / 'inputs' / 'res_assigned_lookup.csv'
    conditions = get_parcel_conditions()
    sdfParcels, df_built_parcels = forecast_jurisdiction_pools(sdfParcels, dfPool, conditions)
    sdfParcels, df_built_parcels = forecast_trpa_pools(sdfParcels, dfPool, conditions, df_built_parcels)
    sdfParcels, df_built_parcels = assign_remainders(sdfParcels, conditions, df_built_parcels, target_units = total_future_units)
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
        df_taz_2035 = adjust_occupied_units(df_taz_2035, additional_occupied_units_2035, "2035", occ_income_distribution)
        df_taz_2050 = adjust_occupied_units(df_taz_2050, additional_occupied_units_2050, "2050", occ_income_distribution)
    else:
        print("  Occupancy adjustment skipped")

    # ── School enrollment ─────────────────────────────────────────────────────
    dfSchool_2035, dfSchool_2050 = adjust_school_enrollment(
        df_taz_2035, df_taz_2050, shared['dfSocio'], shared['dfSchool']
    )

    # ── Employment adjustment (always applied) ────────────────────────────────
    df_taz_2035 = update_employment_numbers(df_taz_2035, shared['dfEmployment_2035'])
    df_taz_2050 = update_employment_numbers(df_taz_2050, shared['dfEmployment_2050'])

    # ── Optional: add occupied-unit employment to emp_other ──────────────────
    if adjust_for_occ_unit_emp:
        occ_emp_csv = config.get('occ_unit_emp_csv', 'taz_towncenter_jobs.csv')
        dfOccEmp = pd.read_csv(DATA_DIR / 'inputs' / occ_emp_csv)
        dfOccEmp['TAZ'] = dfOccEmp['TAZ'].astype(int)
        df_taz_2035['TAZ'] = df_taz_2035['TAZ'].astype(int)
        df_taz_2050['TAZ'] = df_taz_2050['TAZ'].astype(int)
        df_taz_2035 = df_taz_2035.merge(dfOccEmp, on='TAZ', how='left')
        df_taz_2050 = df_taz_2050.merge(dfOccEmp, on='TAZ', how='left')
        df_taz_2035['emp_other'] = df_taz_2035['emp_other'] + (df_taz_2035['occ_unit_emp'].fillna(0) * 0.375).round()
        df_taz_2050['emp_other'] = df_taz_2050['emp_other'] + df_taz_2050['occ_unit_emp'].fillna(0)
        df_taz_2035.drop(columns=['occ_unit_emp'], inplace=True)
        df_taz_2050.drop(columns=['occ_unit_emp'], inplace=True)
        print(f"  Occupied-unit employment added to emp_other ({occ_emp_csv}): 37.5% for 2035, 100% for 2050")
    else:
        print("  Occupied-unit employment adjustment skipped")

    # Rename TAZ column for model input
    df_taz_2035.rename(columns={'TAZ': 'taz'}, inplace=True)
    df_taz_2050.rename(columns={'TAZ': 'taz'}, inplace=True)

    # ── Export final TAZ outputs ──────────────────────────────────────────────
    df_taz_2035.to_csv(folder_2035 / 'SocioEcon_Summer.csv',                        index=False)
    dfSchool_2035.to_csv(folder_2035 / 'SchoolEnrollment.csv',                      index=False)
    shared['dfOvernightVisitors_2035'].to_csv(folder_2035 / 'OvernightVisitorZonalData_Summer.csv', index=False)
    shared['dfVisitorOccupancy'].to_csv(folder_2035 / 'VisitorOccupancyRates_Summer.csv',      index=False)

    df_taz_2050.to_csv(folder_2050 / 'SocioEcon_Summer.csv',                        index=False)
    dfSchool_2050.to_csv(folder_2050 / 'SchoolEnrollment.csv',                      index=False)
    shared['dfOvernightVisitors_2050'].to_csv(folder_2050 / 'OvernightVisitorZonalData_Summer.csv', index=False)
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

        export_scenario_feature_classes(df_all, run_folder)

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
