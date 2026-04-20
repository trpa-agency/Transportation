"""
Scenario Generator Web App
--------------------------
Flask backend for the Housing EIS Scenario Generator.
Implements the Phase-2 pipeline (TAZ Summary → SocioEcon CSVs) without
requiring arcpy.  Phase 1 (parcel engineering) is represented by the
pre-generated TAZ_Summary_*.csv files in each alternative's data/ folder.
"""

import glob
import io
import json
import os
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from flask import Flask, jsonify, render_template, request, send_file

app = Flask(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────
FORECAST_DIR = Path(__file__).parent.parent          # .../Forecast/
BASE_DATA_DIR = FORECAST_DIR.parent / "Base" / "data" / "processed_data"
SHARED_DATA_DIR = FORECAST_DIR / "data"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Field mapping (same as notebooks) ─────────────────────────────────────────
TAZ_FIELD_MAPPING = {
    "TAZ": "TAZ",
    "TOTAL_FORECASTED_RESIDENTIAL_UNITS": "total_residential_units",
    "NEW_OCCUPANCY_RATE": "census_occ_rate",
    "TOTAL_FORECASTED_UNITS_OCCUPIED": "total_occ_units",
    "TOTAL_FORECASTED_UNITS_LOW_INCOME": "occ_units_low_inc",
    "TOTAL_FORECASTED_UNITS_MED_INCOME": "occ_units_med_inc",
    "TOTAL_FORECASTED_UNITS_HIGH_INCOME": "occ_units_high_inc",
    "persons_per_occ_unit": "persons_per_occ_unit",
    "TOTAL_FORECASTED_PERSONS": "total_persons",
    "emp_retail": "emp_retail",
    "emp_srvc": "emp_srvc",
    "emp_rec": "emp_rec",
    "emp_game": "emp_game",
    "emp_other": "emp_other",
}

# ── Pipeline helpers ──────────────────────────────────────────────────────────

def clean_taz_summary(df_taz: pd.DataFrame) -> pd.DataFrame:
    df_taz = df_taz[list(TAZ_FIELD_MAPPING.keys())].rename(columns=TAZ_FIELD_MAPPING)
    pop_fix = (df_taz["total_persons"] > 0) & (df_taz["total_occ_units"] == 0)
    df_taz.loc[pop_fix, "total_persons"] = 0
    for col in ["total_occ_units", "occ_units_high_inc", "occ_units_med_inc",
                "occ_units_low_inc", "total_residential_units", "total_persons"]:
        df_taz[col] = df_taz[col].round().astype(int)
    return df_taz


def adjust_persons_per_occ_unit(df_taz: pd.DataFrame, ppu_df: pd.DataFrame) -> pd.DataFrame:
    df_taz = df_taz.copy()
    ppu = ppu_df.copy()
    df_taz["TAZ"] = df_taz["TAZ"].astype(int)
    ppu["TAZ"] = ppu["TAZ"].astype(int)
    df_taz = df_taz.drop(columns=["persons_per_occ_unit"], errors="ignore")
    df_taz = df_taz.merge(ppu[["TAZ", "persons_per_occ_unit"]], on="TAZ", how="left")
    df_taz["total_persons"] = (
        df_taz["total_occ_units"] * df_taz["persons_per_occ_unit"]
    ).round().astype(int)
    return df_taz


def adjust_occupied_units(
    df: pd.DataFrame,
    target_sum: int,
    label: str,
    rng: np.random.Generator,
    med_split: float = 0.5,
) -> tuple[pd.DataFrame, list[str]]:
    """
    Scale total_occ_units to target_sum.  Additional units are distributed
    between medium and high income according to med_split (0–1); the remainder
    goes to high income.  Returns (adjusted_df, log_lines).
    """
    log = []
    df = df.copy()
    additional = target_sum - int(df["total_occ_units"].sum())
    additional_med = additional * med_split
    additional_high = additional * (1 - med_split)

    occ_factor = target_sum / df["total_occ_units"].sum()
    df["total_occ_units"] = df["total_occ_units"] * occ_factor

    current_med = df["occ_units_med_inc"].sum()
    df["occ_units_med_inc"] = df["occ_units_med_inc"] * (current_med + additional_med) / current_med

    current_high = df["occ_units_high_inc"].sum()
    df["occ_units_high_inc"] = df["occ_units_high_inc"] * (current_high + additional_high) / current_high

    df["total_persons"] = (df["total_occ_units"] * df["persons_per_occ_unit"]).round().astype(int)

    for col in ["total_occ_units", "occ_units_med_inc", "occ_units_high_inc"]:
        df[col] = df[col].round().astype(int)

    # Fix rounding residual
    diff = target_sum - df["total_occ_units"].sum()
    if diff != 0:
        direction = 1 if diff > 0 else -1
        eligible = df.index if direction == 1 else df.index[df["total_occ_units"] > 0]
        chosen = rng.choice(eligible, size=abs(diff), replace=False)
        df.loc[chosen, "total_occ_units"] += direction
        log.append(f"{label}: total_occ_units adjusted by {diff:+d} across {abs(diff)} TAZs")

    # Fix per-TAZ income mismatch
    income_sum = df["occ_units_low_inc"] + df["occ_units_med_inc"] + df["occ_units_high_inc"]
    taz_diff = df["total_occ_units"] - income_sum
    n_fix = (taz_diff != 0).sum()
    if n_fix > 0:
        df["occ_units_high_inc"] += taz_diff
        log.append(f"{label}: income mismatch fixed in {n_fix} TAZs")

    income_sum = df["occ_units_low_inc"] + df["occ_units_med_inc"] + df["occ_units_high_inc"]
    bad = (income_sum != df["total_occ_units"]).sum()
    status = "PASS" if bad == 0 else f"FAIL ({bad} TAZs)"
    log.append(f"{label}: occ={df['total_occ_units'].sum()} (target {target_sum}), income check: {status}")
    return df, log


def adjust_school_enrollment(
    df_taz_2035: pd.DataFrame,
    df_taz_2050: pd.DataFrame,
    df_socio_base: pd.DataFrame,
    df_school: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    base_pop = df_socio_base["total_persons"].sum()
    adj_2035 = ((df_taz_2035["total_persons"].sum() - base_pop) / base_pop) / 2
    adj_2050 = ((df_taz_2050["total_persons"].sum() - base_pop) / base_pop) / 2
    df_school_2035 = df_school.copy()
    df_school_2050 = df_school.copy()
    num_cols = df_school.select_dtypes(include="number").columns
    df_school_2035[num_cols] = (df_school[num_cols] * (1 + adj_2035)).round().astype(int)
    df_school_2050[num_cols] = (df_school[num_cols] * (1 + adj_2050)).round().astype(int)
    return df_school_2035, df_school_2050


def scale_residential_units(
    df: pd.DataFrame,
    new_zoned_total: int,
    old_zoned_total: int,
    base_res_total: int,
    label: str,
) -> tuple[pd.DataFrame, list[str]]:
    """
    Scale the residential-unit delta (above base year) by new/old zoned ratio.
    All housing counts (residential units, occupied units, income splits) are
    scaled proportionally; total_persons is recomputed from the updated occ units.

    Parameters
    ----------
    df               : TAZ DataFrame after clean + persons-per-occ-unit step
    new_zoned_total  : edited zoned unit total from the UI
    old_zoned_total  : original zoned unit total from the CSV
    base_res_total   : base-year total_residential_units (all alternatives share this)
    label            : "2035" or "2050" for log messages
    """
    log = []
    df = df.copy()

    if old_zoned_total == 0 or new_zoned_total == old_zoned_total:
        log.append(f"{label}: residential units unchanged (zoned total = {old_zoned_total})")
        return df, log

    scale = new_zoned_total / old_zoned_total

    # Scale the delta above base year for residential units
    old_res_total = int(df["total_residential_units"].sum())
    old_delta = old_res_total - base_res_total
    new_delta = round(old_delta * scale)
    new_res_total = base_res_total + new_delta

    # Apply proportional adjustment per TAZ (preserve TAZ share of delta)
    df["total_residential_units"] = (
        df["total_residential_units"] * (new_res_total / old_res_total)
    ).round().astype(int)

    # Scale all occupied / income columns by the same factor
    res_factor = new_res_total / old_res_total
    for col in ["total_occ_units", "occ_units_low_inc", "occ_units_med_inc", "occ_units_high_inc"]:
        df[col] = (df[col] * res_factor).round().astype(int)

    # Fix per-TAZ income mismatch after rounding (absorb into high_inc)
    income_sum = df["occ_units_low_inc"] + df["occ_units_med_inc"] + df["occ_units_high_inc"]
    taz_diff = df["total_occ_units"] - income_sum
    n_fix = (taz_diff != 0).sum()
    if n_fix > 0:
        df["occ_units_high_inc"] += taz_diff

    # Recompute persons
    df["total_persons"] = (df["total_occ_units"] * df["persons_per_occ_unit"]).round().astype(int)

    log.append(
        f"{label}: residential units {old_res_total} → {df['total_residential_units'].sum()} "
        f"(zoned {old_zoned_total} → {new_zoned_total}, scale {scale:.4f})"
    )
    return df, log


EMP_COLS = ["emp_retail", "emp_srvc", "emp_rec", "emp_game", "emp_other"]

def update_employment(df_taz: pd.DataFrame, emp_df: pd.DataFrame) -> pd.DataFrame:
    df_taz = df_taz.copy()
    emp = emp_df.copy()
    df_taz["TAZ"] = df_taz["TAZ"].astype(int)
    emp.rename(columns={"taz": "TAZ"}, inplace=True)
    emp["TAZ"] = emp["TAZ"].astype(int)
    cols_to_update = [c for c in EMP_COLS if c in emp.columns]
    df_taz = df_taz.drop(columns=cols_to_update, errors="ignore")
    df_taz = df_taz.merge(emp[["TAZ"] + cols_to_update], on="TAZ", how="left")
    return df_taz

# ── Data discovery ─────────────────────────────────────────────────────────────

def get_taz_files(alt: int) -> dict:
    """Return the most-recent 2035 and 2050 TAZ_Summary paths for an alternative."""
    alt_dir = FORECAST_DIR / f"Alternative_{alt}" / "data"
    files_35 = sorted(glob.glob(str(alt_dir / "TAZ_Summary_2035_*.csv")))
    files_50 = sorted(glob.glob(str(alt_dir / "TAZ_Summary_2050_*.csv")))
    return {
        "2035": files_35,
        "2050": files_50,
    }


def get_input_files(alt: int) -> dict:
    """Return paths to scenario input CSVs."""
    alt_dir = FORECAST_DIR / f"Alternative_{alt}"
    return {
        "zoned_units": str(alt_dir / "inputs" / "forecast_residential_zoned_units.csv"),
    }

# ── API routes ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/scenarios")
def api_scenarios():
    """Return available TAZ summary files per alternative."""
    result = {}
    for alt in [1, 2, 3, 4]:
        files = get_taz_files(alt)
        result[str(alt)] = {
            yr: [Path(f).name for f in file_list]
            for yr, file_list in files.items()
        }
    return jsonify(result)


BASE_RES_TOTAL = 49950   # base-year total_residential_units (all scenarios share this)

@app.route("/api/zoned_units/<int:alt>")
def api_zoned_units(alt: int):
    path = get_input_files(alt)["zoned_units"]
    if not os.path.exists(path):
        return jsonify({"error": "File not found"}), 404
    df = pd.read_csv(path)
    return jsonify(df.to_dict(orient="records"))


@app.route("/api/generate", methods=["POST"])
def api_generate():
    params = request.get_json()

    alt           = int(params["alternative"])
    file_2035     = params["file_2035"]
    file_2050     = params["file_2050"]
    add_occ       = int(params.get("additional_occupied_units", 0))
    med_split     = float(params.get("med_split", 0.5))
    scenario_name = params.get("scenario_name", f"Alternative_{alt}_custom")
    seed          = int(params.get("seed", 42))
    zoned_edits   = params.get("zoned_units", None)   # list of {Jurisdiction, Unit_Pool, Future_Units}

    alt_dir   = FORECAST_DIR / f"Alternative_{alt}"
    data_dir  = alt_dir / "data"

    # Load original zoned units to get old total
    orig_zoned_path = get_input_files(alt)["zoned_units"]
    df_zoned_orig = pd.read_csv(orig_zoned_path)
    old_zoned_total = int(df_zoned_orig["Future_Units"].sum())

    # Apply user edits to zoned units if provided
    if zoned_edits:
        df_zoned_new = pd.DataFrame(zoned_edits)
        df_zoned_new["Future_Units"] = pd.to_numeric(df_zoned_new["Future_Units"], errors="coerce").fillna(0).astype(int)
        new_zoned_total = int(df_zoned_new["Future_Units"].sum())
    else:
        df_zoned_new = df_zoned_orig.copy()
        new_zoned_total = old_zoned_total

    # Load TAZ summaries
    df_raw_2035 = pd.read_csv(data_dir / file_2035)
    df_raw_2050 = pd.read_csv(data_dir / file_2050)

    df_35 = clean_taz_summary(df_raw_2035)
    df_50 = clean_taz_summary(df_raw_2050)

    # Persons-per-occ-unit adjustment
    ppu_35 = pd.read_csv(SHARED_DATA_DIR / "processed_data" / "base_data" / "persons_per_occ_unit_2035.csv")
    ppu_50 = pd.read_csv(SHARED_DATA_DIR / "processed_data" / "base_data" / "persons_per_occ_unit_2050.csv")
    df_35 = adjust_persons_per_occ_unit(df_35, ppu_35)
    df_50 = adjust_persons_per_occ_unit(df_50, ppu_50)

    log = []

    # Residential unit scaling (if zoned targets changed)
    if new_zoned_total != old_zoned_total:
        df_35, log_35r = scale_residential_units(df_35, new_zoned_total, old_zoned_total, BASE_RES_TOTAL, "2035")
        df_50, log_50r = scale_residential_units(df_50, new_zoned_total, old_zoned_total, BASE_RES_TOTAL, "2050")
        log += log_35r + log_50r

    # Occupied-unit adjustment
    rng = np.random.default_rng(seed=seed)
    if add_occ != 0:
        target_35 = int(df_35["total_occ_units"].sum()) + add_occ
        target_50 = int(df_50["total_occ_units"].sum()) + add_occ
        df_35, log_35 = adjust_occupied_units(df_35, target_35, "2035", rng, med_split)
        df_50, log_50 = adjust_occupied_units(df_50, target_50, "2050", rng, med_split)
        log += log_35 + log_50

    # Employment
    emp_35 = pd.read_csv(SHARED_DATA_DIR / "inputs" / "employment_2035.csv")
    emp_50 = pd.read_csv(SHARED_DATA_DIR / "inputs" / "employment_2050.csv")
    df_35 = update_employment(df_35, emp_35)
    df_50 = update_employment(df_50, emp_50)

    # School enrollment
    df_socio_base = pd.read_csv(BASE_DATA_DIR / "SocioEcon_Summer.csv")
    df_socio_base.rename(columns={"taz": "TAZ"}, inplace=True)
    df_school_base = pd.read_csv(BASE_DATA_DIR / "SchoolEnrollment.csv")
    df_school_35, df_school_50 = adjust_school_enrollment(df_35, df_50, df_socio_base, df_school_base)

    # Rename TAZ column
    df_35.rename(columns={"TAZ": "taz"}, inplace=True)
    df_50.rename(columns={"TAZ": "taz"}, inplace=True)

    # Build summary for preview
    sum_vars = ["total_residential_units", "total_occ_units",
                "occ_units_low_inc", "occ_units_med_inc", "occ_units_high_inc",
                "total_persons", "emp_retail", "emp_srvc", "emp_rec", "emp_game", "emp_other"]

    def make_summary(df, label):
        return {v: int(df[v].sum()) for v in sum_vars if v in df.columns} | {"year": label}

    summary = {
        "2035": make_summary(df_35, "2035"),
        "2050": make_summary(df_50, "2050"),
    }

    # Write output zip
    zip_name = f"{scenario_name}.zip"
    zip_path = OUTPUT_DIR / zip_name
    with zipfile.ZipFile(zip_path, "w") as zf:
        def csv_bytes(df):
            buf = io.StringIO()
            df.to_csv(buf, index=False)
            return buf.getvalue().encode()

        zf.writestr(f"{scenario_name}_2035/SocioEcon_Summer.csv",    csv_bytes(df_35))
        zf.writestr(f"{scenario_name}_2035/SchoolEnrollment.csv",    csv_bytes(df_school_35))
        zf.writestr(f"{scenario_name}_2050/SocioEcon_Summer.csv",    csv_bytes(df_50))
        zf.writestr(f"{scenario_name}_2050/SchoolEnrollment.csv",    csv_bytes(df_school_50))
        # Always include the (possibly edited) zoned units CSV
        zf.writestr(f"{scenario_name}_inputs/forecast_residential_zoned_units.csv",
                    csv_bytes(df_zoned_new))

    return jsonify({
        "status": "ok",
        "log": log,
        "summary": summary,
        "download": f"/download/{zip_name}",
        "scenario_name": scenario_name,
        "zoned_totals": {"old": old_zoned_total, "new": new_zoned_total},
    })


@app.route("/download/<filename>")
def download(filename: str):
    path = OUTPUT_DIR / filename
    if not path.exists():
        return "File not found", 404
    return send_file(path, as_attachment=True, download_name=filename)


if __name__ == "__main__":
    app.run(debug=True, port=5050)
