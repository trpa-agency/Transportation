# Transit funding model: data pipeline

Builds `model/transit-funding-model.html` from the source workbooks and the seed files. The workbooks stay the source of truth for amounts, hours, rates, shares, and match notes. The seed holds the judgment calls.

Rebuilt October 27, 2026. The October 22 pipeline was never saved to the repo. This version reproduces the page as of October 27 field for field. The only change is that TART 5307 now reads Table A2, which TRPA chose on October 23.

## Run it

1. Save the workbooks. By default the build reads `source-data/workbooks/`. To read the live copies, set `workbook_folder` in `etl/config.yaml` to the synced SharePoint folder "4. Funding Implementation Memo".
2. Double-click `build_data.bat`, or run `propy etl\build_model_data.py` from this folder.
3. Read `data/build-report.md`.
4. Copy `dist/transit-funding-model.html` to `model/transit-funding-model.html`, then upload it to the claude.ai Project.

Options: `--strict` fails the build when there are warnings. `--check` compares the build with `model/transit-funding-model.html` and lists every difference.

## Folders

| Path | What it is |
| --- | --- |
| `etl/build_model_data.py` | The build |
| `etl/config.yaml` | Workbook folder, file names, the costs tab and Revenue %s layout, and output paths |
| `etl/seed/services.yaml` | Services. Trips, hours, miles, and route conditions come from the costs tab |
| `etl/seed/operators.yaml` | Operator cost rates, from the VRH Rates tab |
| `etl/seed/sources.yaml` | Funding sources: amounts, year values, Revenue %s shares and match notes, plus every rule and note |
| `etl/seed/fta.yaml` | FTA 5307 split inputs, from the FTA Allocation Split (26-27) tab |
| `etl/seed/model.yaml` | Agencies, jurisdictions, and source file names |
| `etl/seed/notes.yaml` | Data notes and the agreements inventory |
| `template/transit-funding-model.template.html` | The page without data. It loads `data/model-data.js` |
| `data/` | Build output: `model-data.json`, `model-data.js`, `build-report.md` |
| `dist/` | Build output: the single-file page |

## How a value is found

Each workbook value has a `from` entry in the seed. For example:

```yaml
from:
  amount: {wb: plan, sheet: T2-4 A1 TTD LL Costs, row: FTA 5307 (Formally CMAQ Funds)1, near: 61, col: G}
```

- `row` is the label text in that row. The build searches for it, so inserting rows is safe.
- `occurrence` picks the nth match from the top when a label repeats, as in the route cost model.
- `near` is the row number when the seed was written. It only breaks ties.
- `cols` reads several columns: the five plan years G to K, or a range to sum with `sum: true`.
- If a label is renamed in the workbook, the build stops and names it. Update `row` in the seed.

## Holding a value over the workbook

A decision that overrides the workbook goes under `keep`:

```yaml
keep:
  amount:
    reason: Carried steady at the FY 25-26 amount per TRPA (Oct. 23, 2026); the plan shows $0 for FY 26-27
    workbook: 0.0
```

The build uses the seed value. `workbook` records what the workbook said when the decision was made. If the workbook later changes, the build warns so someone can decide again. The report lists every held value with its reason.

Current held values: 21. They cover the Oct. 23 TRPA decisions (private partners steady, 5310 at 80 percent federal, and the alternation years), the four Revenue %s rows with known problems, and two text fixes.

## What the build checks

- Costs tab rows and Revenue %s rows that no seed entry reads
- Revenue %s route columns with no service mapping
- Unknown agencies, operators, jurisdictions, or services named in rules and shares
- Shares above 100 percent, and jurisdiction shares that do not total 100 percent

## Changing the page

Edit `template/transit-funding-model.template.html`, then rebuild. Don't edit `model/transit-funding-model.html` directly. The next build replaces it.
