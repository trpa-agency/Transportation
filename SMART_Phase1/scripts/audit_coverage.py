"""
Audit staged DERQ vehicle-count data for upstream quality problems:
missing stretches per camera, and data jumbled across locations.

Reads data/staging/full/TTD_SMART_VehicleCounts.csv (run stage_backfill.py
first). Reports:
1. Per-location coverage: first/last day, gap days, longest gap.
2. Monthly average-volume matrix (blank month = no data at all).
3. Month-over-month cliffs: >60% collapses / >150% jumps in daily volume.
4. Duplicate fingerprints: identical (day, volume, row-count) between two
   locations -- direct evidence of one camera's data landing under another.

Usage:
    python audit_coverage.py
"""
import sys
from pathlib import Path

import pandas as pd

STAGING = Path(__file__).resolve().parents[1] / "data" / "staging" / "full"

if not (STAGING / "TTD_SMART_VehicleCounts.csv").exists():
    sys.exit(f"No staged vehicle counts at {STAGING} -- run stage_backfill.py first.")

v = pd.read_csv(STAGING / "TTD_SMART_VehicleCounts.csv")
v["Date"] = pd.to_datetime(v["Date"])

daily = v.groupby(["LocationName", "Date"], as_index=False)["counts"].sum()

print("=" * 78)
print("1. PER-LOCATION COVERAGE (staged vehicle counts, 2025-03-10 .. 2026-08-08)")
print("=" * 78)
rows = []
for name, group in daily.groupby("LocationName"):
    days = group["Date"].dt.date
    span = pd.date_range(days.min(), days.max()).date
    present = set(days)
    gaps = [d for d in span if d not in present]
    # longest consecutive gap
    longest, run = 0, 0
    for d in span:
        run = run + 1 if d not in present else 0
        longest = max(longest, run)
    rows.append({
        "location": name.strip(), "first": days.min(), "last": days.max(),
        "days_present": len(present), "days_missing": len(gaps),
        "longest_gap_days": longest,
        "avg_daily": round(group["counts"].mean()),
    })
cov = pd.DataFrame(rows).sort_values("days_missing", ascending=False)
print(cov.to_string(index=False))

print()
print("=" * 78)
print("2. MONTHLY VOLUME SHIFTS (avg daily vehicles; blank = no data that month)")
print("=" * 78)
monthly = daily.assign(month=daily["Date"].dt.to_period("M"))
pivot = monthly.pivot_table(index="LocationName", columns="month",
                            values="counts", aggfunc="mean").round(0)
pivot.index = [i.strip()[:32] for i in pivot.index]
# print in two halves to stay readable
cols = list(pivot.columns)
for half in (cols[:len(cols)//2], cols[len(cols)//2:]):
    print(pivot[half].to_string())
    print()

print("=" * 78)
print("3. MONTH-OVER-MONTH CLIFFS (>60% drop or >150% jump in avg daily volume)")
print("=" * 78)
cliffs = []
for loc in pivot.index:
    series = pivot.loc[loc].dropna()
    for prev, cur in zip(series.index, series.index[1:]):
        a, b = series[prev], series[cur]
        if a >= 200:  # ignore tiny-volume noise
            change = (b - a) / a
            if change <= -0.6 or change >= 1.5:
                cliffs.append({"location": loc, "from": str(prev), "to": str(cur),
                               "avg_before": int(a), "avg_after": int(b),
                               "change": f"{change:+.0%}"})
if cliffs:
    print(pd.DataFrame(cliffs).to_string(index=False))
else:
    print("none found")

print()
print("=" * 78)
print("4. IDENTICAL DAY-PROFILES BETWEEN LOCATIONS (jumbled-data fingerprint)")
print("=" * 78)
# For each (location, day): a fingerprint of total volume + row count.
# Two different locations sharing the exact same fingerprint on the same day
# repeatedly is strong evidence of duplicated/misassigned feeds.
fp = v.groupby(["LocationName", "Date"]).agg(
    total=("counts", "sum"), rows=("counts", "size")
).reset_index()
merged = fp.merge(fp, on=["Date", "total", "rows"])
merged = merged[merged["LocationName_x"] < merged["LocationName_y"]]
merged = merged[merged["total"] > 500]  # ignore trivially-equal low-volume days
if merged.empty:
    print("none found")
else:
    pairs = (merged.groupby(["LocationName_x", "LocationName_y"])
             .agg(matching_days=("Date", "count"),
                  first=("Date", "min"), last=("Date", "max"))
             .reset_index().sort_values("matching_days", ascending=False))
    print(pairs[pairs["matching_days"] >= 3].to_string(index=False) or "no repeated pairs")
