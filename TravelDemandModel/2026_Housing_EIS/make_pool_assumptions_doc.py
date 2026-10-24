"""
Generate a Word document summarizing TRPA unit pool assumptions and parcel eligibility
criteria for the 2026 Housing EIS travel demand model forecast.
"""

from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from pathlib import Path

OUTPUT = Path(__file__).parent / "TRPA_Unit_Pool_Assumptions.docx"

# ── Styles / helpers ──────────────────────────────────────────────────────────

def set_col_width(cell, width_inches):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcW = OxmlElement('w:tcW')
    tcW.set(qn('w:w'), str(int(width_inches * 1440)))  # twips
    tcW.set(qn('w:type'), 'dxa')
    tcPr.append(tcW)

def shade_cell(cell, hex_color="003865"):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)

def header_row(table, cols, col_widths=None, bg="003865", fg="FFFFFF"):
    row = table.rows[0]
    for i, (cell, text) in enumerate(zip(row.cells, cols)):
        cell.text = text
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.runs[0]
        run.bold = True
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor.from_string(fg)
        shade_cell(cell, bg)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        if col_widths:
            set_col_width(cell, col_widths[i])

def data_row(table, values, col_widths=None, bold_first=False, bg=None, size=8.5):
    row = table.add_row()
    for i, (cell, text) in enumerate(zip(row.cells, values)):
        cell.text = str(text)
        p = cell.paragraphs[0]
        run = p.runs[0]
        run.font.size = Pt(size)
        if bold_first and i == 0:
            run.bold = True
        if bg:
            shade_cell(cell, bg)
        if col_widths:
            set_col_width(cell, col_widths[i])


# ── Document ──────────────────────────────────────────────────────────────────

doc = Document()

# Page margins
section = doc.sections[0]
section.left_margin   = Inches(1)
section.right_margin  = Inches(1)
section.top_margin    = Inches(1)
section.bottom_margin = Inches(1)

# Title
title = doc.add_heading("TRPA Unit Pool Assumptions", level=1)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
for run in title.runs:
    run.font.color.rgb = RGBColor(0, 56, 101)  # TRPA blue

doc.add_paragraph(
    "This document summarizes the forecast assumptions and parcel eligibility criteria "
    "for each TRPA residential unit pool used in the 2026 Housing EIS Travel Demand Model. "
    "Assumptions reflect the final Alternative configurations (configs_final, dated 04/28/2026)."
)

# ══════════════════════════════════════════════════════════════════════════════
# TABLE 1 – Pool-Level Assumptions
# ══════════════════════════════════════════════════════════════════════════════
doc.add_heading("Pool-Level Assumptions", level=2)
doc.add_paragraph(
    "The table below lists occupancy rate and household income distribution assumptions "
    "applied to each unit pool. These values are drawn from the scenario config JSON files "
    "and applied during the TAZ-level socioeconomic forecast."
)

cols1 = ["Unit Pool", "Administering\nJurisdiction", "Occupancy\nRate",
         "Income: Low\n(% occ. units)", "Income: Medium\n(% occ. units)", "Income: High\n(% occ. units)"]
widths1 = [1.5, 1.1, 0.9, 1.0, 1.05, 1.0]

pool_data = [
    # Pool name, Jurisdiction, Occ rate, Low, Med, High, notes
    ("General",                   "All",  "35%",  "1%",    "2%",    "97%"),
    ("Bonus Unit",                "All",  "100%", "40%",   "25%",   "35%"),
    ("ADU",                       "TRPA", "70%",  "65%",   "20%",   "15%"),
    ("JADU",                      "TRPA", "100%", "65%",   "20%",   "15%"),
    ("Affordable",                "TRPA", "100%", "100%",  "0%",    "0%"),
    ("Moderate",                  "TRPA", "100%", "0%",    "100%",  "0%"),
    ("Achievable Bonus",          "TRPA", "100%", "—",     "—",     "—"),
    ("Achievable General",        "TRPA", "100%", "—",     "—",     "—"),
    ("Achievable TC",             "TRPA", "100%", "—",     "—",     "—"),
    ("Affordable by Design",      "TRPA", "100%", "0%",    "50%",   "50%"),
    ("Affordable by Design TC",   "TRPA", "100%", "0%",    "50%",   "50%"),
    ("CTC",                       "TRPA", "100%", "100%",  "0%",    "0%"),
]

tbl1 = doc.add_table(rows=1, cols=len(cols1))
tbl1.style = 'Table Grid'
tbl1.alignment = WD_TABLE_ALIGNMENT.CENTER
header_row(tbl1, cols1, widths1)

for i, row in enumerate(pool_data):
    bg = "F2F2F2" if i % 2 == 0 else None
    data_row(tbl1, row, widths1, bold_first=True, bg=bg)

doc.add_paragraph()
doc.add_paragraph(
    "Notes: (1) 'General' occupancy of 35% reflects market-rate second-home dynamics at Lake Tahoe. "
    "(2) ADU/JADU income distribution reflects TRPA affordable housing policy assumptions. "
    "(3) 'Achievable' pools use 100% occupancy but share income proportions with their parent pool "
    "('Achievable Bonus' follows Bonus, 'Achievable General' and 'Achievable TC' follow General). "
    "(4) '—' indicates income proportions are inherited from the parent pool category and not "
    "separately specified in the config. "
    "(5) CTC = Community Town Center units."
)

# ══════════════════════════════════════════════════════════════════════════════
# TABLE 2 – Zone Type Proportions (Alt 2 default)
# ══════════════════════════════════════════════════════════════════════════════
doc.add_heading("Unit Type Distribution by Pool", level=2)
doc.add_paragraph(
    "New units in each pool are distributed across three development type categories: "
    "Multi-Family (MF), Single-Family (SF), and Infill. The proportions below reflect "
    "Alternative 2 final config assumptions and are applied before parcel-level allocation."
)

cols2 = ["Pool / Jurisdiction Override", "Multi-Family (MF)", "Single-Family (SF)", "Infill"]
widths2 = [2.2, 1.3, 1.3, 1.2]

zone_data = [
    ("Default (all pools / jurisdictions)", "35%", "50%", "15%"),
    ("TRPA Affordable (override)",          "100%", "0%", "0%"),
]

tbl2 = doc.add_table(rows=1, cols=len(cols2))
tbl2.style = 'Table Grid'
tbl2.alignment = WD_TABLE_ALIGNMENT.CENTER
header_row(tbl2, cols2, widths2)

for i, row in enumerate(zone_data):
    bg = "F2F2F2" if i % 2 == 0 else None
    data_row(tbl2, row, widths2, bold_first=True, bg=bg)

doc.add_paragraph()

# ══════════════════════════════════════════════════════════════════════════════
# TABLE 3 – Parcel Eligibility Criteria
# ══════════════════════════════════════════════════════════════════════════════
doc.add_heading("Parcel Eligibility Criteria by Pool", level=2)
doc.add_paragraph(
    "The following table defines the parcel-level eligibility conditions applied during "
    "the spatial allocation step. All pools require the parcel to be privately owned and "
    "not already assigned to a forecast reason (i.e., not yet allocated). Conditions are "
    "coded in the get_parcel_conditions() function in scripts/utils.py."
)

cols3 = [
    "Unit Pool",
    "Jurisdiction(s)",
    "Future Units\n(Alt 2)",
    "Bonus Unit\nBoundary\nRequired",
    "Town Center\nRequired",
    "Vacant Parcel\nRequired\n(MF/SF types)",
    "IPES Score\nThreshold\n(MF/SF types)",
    "Housing\nZoning",
    "ADU Allowed\n& Existing\nRes. Units",
    "Parcel\n≥ 0.15 ac.\n(non-condo)",
]
widths3 = [1.5, 0.9, 0.7, 0.7, 0.7, 0.8, 0.75, 0.95, 0.75, 0.65]

Y = "Yes"
N = "No"
NA = "—"

# Unit counts from alternative_2_04282026__config.json
# General totals by jurisdiction pool
gen_jx = {
    "CSLT": 395, "DG": 160, "EL": 281, "PL": 41, "WA": 196
}
bonus_jx = {
    "CSLT": 89, "DG": 67, "PL": 582, "WA": 120
}
gen_all   = sum(gen_jx.values()) + 948   # + TRPA General
bonus_all = sum(bonus_jx.values()) + 388  # + TRPA Bonus

# Format: Pool, Jurisdictions, FutureUnits, BonusBndy, TownCenter, Vacant(MF/SF),
#         IPES(MF/SF), Zoning, ADU+ExistingRes, ParcelSize
eligibility_data = [
    # ── Jurisdiction pools ──
    ("General",
     "CSLT, DG, EL,\nPL, WA, TRPA",
     f"{gen_all:,}",
     N, N, Y,
     "> 0\n(PL: > 726)",
     "SF/MF or\nMF only",
     N, Y),
    ("Bonus Unit",
     "CSLT, DG,\nPL, WA, TRPA",
     f"{bonus_all:,}",
     Y, N, Y,
     "> 0\n(PL: > 726)",
     "SF/MF or\nMF only",
     N, Y),
    # ── TRPA-only pools ──
    ("ADU",
     "TRPA", "110",
     N, N, N,
     NA,
     NA,
     Y, Y),
    ("JADU",
     "TRPA", "98",
     N, N, N,
     NA,
     NA,
     Y, Y),
    ("Affordable",
     "TRPA", "456",
     N, Y, Y,
     "> 0",
     "SF/MF or\nMF only",
     N, Y),
    ("Moderate",
     "TRPA", "285",
     Y, N, Y,
     "> 0",
     "SF/MF or\nMF only",
     N, Y),
    ("Achievable Bonus",
     "TRPA", "228",
     Y, N, Y,
     "> 0",
     "SF/MF or\nMF only",
     N, Y),
    ("Achievable General",
     "TRPA", "57",
     N, N, Y,
     "> 0",
     "SF/MF or\nMF only",
     N, Y),
    ("Achievable TC",
     "TRPA", "0",
     N, Y, Y,
     "> 0",
     "SF/MF or\nMF only",
     N, Y),
    ("Affordable by Design",
     "TRPA", "114",
     N, N, Y,
     "> 0",
     "SF/MF or\nMF only",
     N, Y),
    ("Affordable by Design TC",
     "TRPA", "0",
     N, Y, Y,
     "> 0",
     "SF/MF or\nMF only",
     N, Y),
]

tbl3 = doc.add_table(rows=1, cols=len(cols3))
tbl3.style = 'Table Grid'
tbl3.alignment = WD_TABLE_ALIGNMENT.CENTER
header_row(tbl3, cols3, widths3)

for i, row in enumerate(eligibility_data):
    bg = "F2F2F2" if i % 2 == 0 else None
    # Bold pool name and right-align future units
    data_row(tbl3, row, widths3, bold_first=True, bg=bg, size=8)
    # Right-align the Future Units column (index 2)
    tbl3.rows[-1].cells[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

# Total row
total_units = sum([gen_all, bonus_all, 110, 98, 456, 285, 228, 57, 0, 114, 0])
total_row = tbl3.add_row()
for i, (cell, text) in enumerate(zip(total_row.cells,
        ["", "TOTAL", f"{total_units:,}", "", "", "", "", "", "", ""])):
    cell.text = text
    p = cell.paragraphs[0]
    run = p.runs[0]
    run.bold = True
    run.font.size = Pt(8)
    shade_cell(cell, "D9E1F2")
    if widths3:
        set_col_width(cell, widths3[i])
total_row.cells[2].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

doc.add_paragraph()
doc.add_paragraph(
    "Notes: (1) All pools require: Private ownership AND parcel not already assigned to a forecast reason. "
    "(2) 'Vacant Parcel Required' applies only to MF and SF development sub-types; infill sub-types "
    "draw from parcels already carrying existing development but with remaining unit potential (POTENTIAL_UNITS field). "
    "(3) Parcel ≥ 0.15 ac. condition also excludes Condominium and Condominium Common Area land uses. "
    "(4) Placer County (PL) applies a higher IPES threshold of > 726 (vs. > 0 elsewhere) to reflect "
    "stricter environmental sensitivity constraints. "
    "(5) ADU and JADU pools require ADU_ALLOWED = Yes AND Residential_Units > 0 on the parcel. "
    "(6) 'Future Units' column shows pool totals summed across all applicable jurisdictions from the "
    "Alternative 2 (04/28/2026) config. Pools with 0 units are defined in the config but not activated "
    "under this alternative."
)

# ══════════════════════════════════════════════════════════════════════════════
# TABLE 4 – Unit Counts by Pool (Alt 2 final)
# ══════════════════════════════════════════════════════════════════════════════
doc.add_heading("Unit Counts by Pool — Alternative 2 (Final, 04/28/2026)", level=2)
doc.add_paragraph(
    "The table below shows the total forecasted units by jurisdiction and pool for Alternative 2, "
    "the primary scenario used in the EIS analysis."
)

cols4 = ["Jurisdiction", "Unit Pool", "Total Future Units"]
widths4 = [1.2, 1.8, 1.4]

unit_counts = [
    ("CSLT", "Bonus Unit",               89),
    ("CSLT", "General",                  395),
    ("DG",   "Bonus Unit",               67),
    ("DG",   "General",                  160),
    ("EL",   "General",                  281),
    ("PL",   "General",                  41),
    ("PL",   "Bonus Unit",               582),
    ("WA",   "General",                  196),
    ("WA",   "Bonus Unit",               120),
    ("TRPA", "General",                  948),
    ("TRPA", "Bonus Unit",               388),
    ("TRPA", "ADU",                      110),
    ("TRPA", "Affordable",               456),
    ("TRPA", "Moderate",                 285),
    ("TRPA", "Achievable Bonus",         228),
    ("TRPA", "Achievable General",       57),
    ("TRPA", "Achievable TC",            0),
    ("TRPA", "Affordable by Design",     114),
    ("TRPA", "Affordable by Design TC",  0),
    ("TRPA", "JADU",                     98),
]

tbl4 = doc.add_table(rows=1, cols=len(cols4))
tbl4.style = 'Table Grid'
tbl4.alignment = WD_TABLE_ALIGNMENT.CENTER
header_row(tbl4, cols4, widths4)

for i, row in enumerate(unit_counts):
    bg = "F2F2F2" if i % 2 == 0 else None
    data_row(tbl4, [row[0], row[1], f"{row[2]:,}"], widths4, bold_first=False, bg=bg)

# Total row
total = sum(r[2] for r in unit_counts)  # = 4,615
total_row = tbl4.add_row()
for i, (cell, text) in enumerate(zip(total_row.cells, ["", "TOTAL", f"{total:,}"])):
    cell.text = text
    p = cell.paragraphs[0]
    run = p.runs[0]
    run.bold = True
    run.font.size = Pt(8.5)
    shade_cell(cell, "D9E1F2")
    if widths4:
        set_col_width(cell, widths4[i])

doc.add_paragraph()

# Footer note
p = doc.add_paragraph()
p.add_run("Source: ").bold = True
p.add_run(
    "TravelDemandModel/2026_Housing_EIS/Forecast/configs_final/alternative_2_04282026__config.json; "
    "scripts/utils.py (get_parcel_conditions); scripts/forecast_functions.py. "
    "Generated 2026-06-04."
)
p.runs[-1].font.size = Pt(8)
p.runs[-1].font.color.rgb = RGBColor(89, 89, 89)

doc.save(OUTPUT)
print(f"Saved: {OUTPUT}")
