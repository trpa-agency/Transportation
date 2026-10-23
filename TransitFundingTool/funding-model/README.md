# Regional Transit Funding Model

The Lake Tahoe Region transit funding model for RFP Task 4b: one calculation engine and one dataset, with a simple view and three front ends that put different work first.

## Open it

Open `index.html` in Chrome or Edge. Every page also opens directly from disk. The pages load Plotly and AG Grid from public CDNs, so they need an internet connection.

| Page | For | What it puts first |
| --- | --- | --- |
| `simple.html` | Anyone checking the numbers | Every cost and funding input with its source cell, and what changes when dollars change |
| `apps/budget-scenarios.html` | Decision makers | Funding presets, sliders, the value of more money, and saved scenarios side by side |
| `apps/allocation-workbench.html` | Staff | Editable source-by-service shares, rule findings, and the match arithmetic for each service |
| `apps/partner-cost-share.html` | Partners | Cost and local share by jurisdiction, a cost-share formula builder, and commitments |

Edits are saved in the browser. The simple view exports and imports the full dataset as JSON in the database layout.

## How it is built

| Path | What it is |
| --- | --- |
| `engine/funding-engine.js` | All funding logic: costs, revenue projections, eligibility, federal share and match, the fixed-share and rules-based allocations, checks, results, and sensitivity. No UI code. Runs in a browser or in Node. |
| `RULES.md` | Every rule the engine applies (52 general rules) and the rule parameters of each of the 63 funding sources. Generated from the engine and the data. |
| `schema.sql` | Database schema. SQLite syntax that maps directly to PostgreSQL. |
| `data/seed.json` | The data as normalized tables matching the schema. `seed.js` is the same data for the pages; `funding_model.sqlite` and `seed.sql` are the same data loaded into the schema. |
| `tools/seed_source.py` | Where data values and their citations are kept and edited. |
| `tools/build.py` | Rebuilds the data files and loads the SQLite database, checking every key and constraint. |
| `tools/rules_doc.py` | Rebuilds `RULES.md`. |
| `tools/verify.py` | Independent checks in Python: re-reads values from the workbooks and re-solves the optimizer with separate code. |
| `tests/engine-tests.html` | Browser test suite for the engine. |
| `ui/` | Shared page styles and helpers (formatting, grids, charts). |

## The two allocation methods

- **Draft shares** apply the split written for each source (the consultant draft from `Financial PlanG › Revenue %s`, with placeholder splits for sources it left out). The engine checks the result against every rule.
- **Rules-based** lets the engine allocate every source. It maximizes funded service subject to all required rules, eligible portions, no over-funding, and match on every service. Second, it spreads any shortfall as evenly as the rules allow. Third, it breaks ties: fares first, then federal funds, earmarked funds, and time-limited funds, holding back flexible recurring money. Each solution is proven optimal with a duality certificate.

## Change the data

1. Edit `tools/seed_source.py`.
2. Run `python -P tools/build.py`, then `python -P tools/rules_doc.py`.
3. Open `tests/engine-tests.html` (served over http, or from disk) and confirm every check passes.
4. Run `python -P tools/verify.py ".."` with the folder that holds the source workbooks.

## Verification status (Oct. 19, 2026)

- 54 of 54 engine tests pass. They include an exact match with the first model (`transit-funding-model.html`): costs, revenue, dollars on each of 21 services, the same 11 rule errors and 6 warnings, and five-year balances.
- In 200 random funding scenarios, every rules-based allocation was certified optimal and broke no rule.
- 122 of 122 seeded values match their workbook cells.
- A separately written Python optimizer gives the same funded service in all five comparison scenarios.
