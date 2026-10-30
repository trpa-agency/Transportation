# Model logic

How the model page calculates, as of October 30, 2026. The code is the JavaScript at the bottom of `pipeline/template/transit-funding-model.template.html`. Section numbers in the code comments match the headings in parentheses below.

## Page and libraries

- **One self-contained HTML page.** The data is inlined as `window.TRANSIT_MODEL_DATA` by the pipeline. The template loads `data/model-data.js` instead.
- **Libraries (exact versions):** Plotly 2.35.2, AG Grid Community 33.3.2, and Calcite Components 5.0, all from CDNs. ExcelJS 4.4.0 loads from jsDelivr only when someone uses Export or Import.
- **Colors:** every color comes from the Connecting Tahoe token block in the page head (`--ct-*` and `--c-*` variables). Charts read the same tokens through `TOK()`. To change the palette, edit that block only.
- **Scenario storage:** edits save to browser local storage under `trpa-transit-funding-model`. Every edit is logged in the change log. A scenario saved on an older data build is rebased onto the new build: the new values load, then the scenario's edits are applied on top.

## Tabs

| Group | Tab | Changes with inputs? |
| --- | --- | --- |
| | Overview | No. Navigation and a draft caveat |
| Today | Existing funding conditions | No. Always the source data, FY 26-27 |
| Inputs users can change | Inputs and assumptions | These are the inputs |
| Inputs users can change | Allocation and rules | Shares are inputs; rule checks update |
| Results and future | One-year outlook, Five-year outlook, Agreements and risk | Yes |
| Reference | Sources and notes | No (sources, data notes, build) |

## Services and cost (engine, section 5)

- **Annual cost:** vehicle service hours times the operator's cost per hour. A service can override the rate or the annual cost.
- **Service plan elements:** these use a five-year cost schedule from Tables A1 and A2. They count only when "Include" is checked.
- **Later years:** each operator's escalator applies (4 percent; TART Connect 5 percent; My Ride to Work 3 percent).
- **Jurisdiction miles:** annual service miles by jurisdiction set each service's California and Nevada portions. The engine reads them as weights and normalizes each row. Until miles by jurisdiction arrive, each service's total service miles are split evenly as a placeholder, by TRPA direction. Entering miles for a service replaces its placeholder.

## Funding source amounts

The FY 26-27 amount comes from the financial plan, or from the FTA 5307 split for TTD's 5307. Later years follow the source's rule: growth rate, end year, cap, or a year value typed in, in that order of precedence.

## Allocation

- **Shares:** each source is split across services by shares. Manual shares come from Revenue %s or from the user. An automatic split divides the source by service hours, cost, ridership, service miles, or equally among the services its rules allow.
- **Unallocated money:** whatever is not applied stays with the receiving agency.
- **Fixed across years:** shares do not change by year. Check later years with the Fiscal year selector.
- **Suggest allocation:** a rules-based default, not an optimizer. Earmarked sources and fares go first. Federal funds follow, up to each route's share cap. Flexible funds then go to each route's remaining cost, most restricted first. Funds never move to another agency's services.

## Rule checks

| Check | Level | Rule |
| --- | --- | --- |
| Route, operator, urban or rural, service type, state, or jurisdiction restriction | Flag | Hard rules on the source (`rules` in the seed) |
| Federal eligibility | Flag | Federal money on a non-federalized service |
| Eligible portion | Flag | More than the California or Nevada (or jurisdiction) share of a partly eligible route |
| Over-allocated | Flag | Shares total more than 100 percent |
| Federal share cap | Flag | Federal funds on a service exceed the highest federal share among its federal sources, times net cost. ADA paratransit uses the ADA share (80 percent for 5307) |
| Local match | Flag | Non-federal match applied to the service is less than federal × (1 − share) / share |
| Intended use, state preference, jurisdiction preference | Note | "Ideally" conditions. TRPA allows these and wants them highlighted |
| Cross-agency use | Note | One agency's funds on another agency's service. Needs an interagency agreement |
| Unallocated, funding gap | Info | Money not applied; route cost with no funding |

Fares count as local match by TRPA direction. A fare line with "Counts as match" unchecked is treated as fare replacement: it lowers net cost instead.

**Known gap:** TRPA chose per-grant, per-recipient match testing (Oct. 23). The engine still tests match per service. Per-route testing can report shortfalls that a grant-level test would not. A grant-level test means summing each federal source's required match against the eligible non-federal funds of the same recipient. That change belongs in the `compute()` function.

## Agency balances

- **Revenue:** everything a receiving agency gets, applied to a service or not. Match-only credits are not revenue.
- **Federal funds above the share cap:**
  - Each federal source can pay at most its federal share times the net cost of the eligible services of the agency that receives it.
  - Sources are placed most-restricted first, and whatever cannot be placed has no eligible operating use.
  - That excess is left out of the balance by default. The Inputs page can switch this to "count."
  - In FY 26-27 this is $1,137,363 at TTD, mostly NDOT 5311 above what Routes 19X and 22 can use.
- **Ending balance:** surplus carried from the prior year, plus revenue, minus federal funds above the cap, minus the cost of services operated.
- **Carryover:** an ending surplus becomes revenue the next year, and deficits do not carry. The setting is off by default (TRPA review, Oct. 30, 2026), because modeled TART and TNT/TMA costs appear understated. Each agency has an opening balance for FY 26-27, default $0.
- **Region:** the sum of agency balances. It nets one agency's surplus against another's deficit, so findings report deficits by agency.

## Jurisdiction results

- **Cost:** service cost is split by jurisdiction shares.
- **Need:** each jurisdiction's need is its cost share minus the federal, state, private, and fare funds applied to that share.
- **Contributions:** local public sources tagged with a contributing jurisdiction.
- **Draft status:** these are drafts until real shares replace the placeholders.

## Scenario presets (Inputs and assumptions)

Each preset lists the values it sets. Checking it applies them as logged edits. Unchecking returns those values to the source data. Each card shows its effect against the source data before it is applied.

| Preset | What it sets |
| --- | --- |
| Meyers paratransit and microtransit pilot | Includes the SP-MEY service plan element. Its cost starts in FY 27-28 |
| TTD absorbs Lake Link | Lake Link services and all SSTMA sources move to TTD. Lake Link becomes federalized. TTD's combined sources are reallocated with the rules-based allocation, computed on the source data. Three assumptions apply only while the preset is on: SSTMA admin cost removed, the share of Lake Link private partner funds kept, and added federal compliance cost. Defaults ($0, 100 percent, $0) change nothing. The card compares separate and consolidated cases, both under the rules-based allocation: flags, notes, TTD federal funds above the share cap, and the combined TTD and Lake Link balance |
| All TART fixed routes at 30-minute peak frequency | Sets `peak30` on the TART Main Line (West Shore, North Shore, Nevada), Hwy 89, and Hwy 267. Adds the TART 2025 Systems Plan cost of $2,683,400 a year in FY 26-27, grown by TART's 4 percent escalator after that. The total is split across the routes by annual service hours, a placeholder until TART gives a route breakdown. Plan figures are in `etl/seed/model.yaml` under `scenarios.peak30` |

The TDA and SB 125 California-only preset and the Lake Link federalized preset were removed on October 30, 2026, per TRPA review.

## Export and import

- **Export to Excel:** writes ten readable sheets: Scenario, Outlook by agency, Results by service, Results by jurisdiction, Funding sources, Allocation shares, Services, Rule checks, Changes, and Sources.
- **Hidden scenario sheet:** a very hidden `_scenario` sheet holds the scenario JSON in 30,000-character cells.
- **Import:** reads that sheet back, or an older JSON scenario file. Edits typed into the workbook are not read back.

## Citations

- **Numbered sources:** source files are numbered once, on Sources and notes. 1 to 8 are the workbooks and fact sheets in a fixed order; 9 is TRPA direction of Oct. 23, 2026; 10 and up are published documents listed under `references` in `etl/seed/model.yaml`, currently the TART 2025 Systems Plan presentation (10) and staff report (11).
- **Seed text stays verbatim:** cite strings in the seed keep the full file name, tab, and cell. The page swaps the file name for a superscript number when it draws them: `citeHtml`, `citeText`, and `textHtml`.
- **TRPA direction:** write it in seed text as "per TRPA (Oct. 23, 2026)" or "(TRPA, Oct. 23, 2026)" and it becomes superscript 9.

## Testing the page

- **Headless test:** the page needs its CDN libraries. In a sandbox without CDN access, install the same versions from npm and route the CDN URLs to the local files. Then open the page with Playwright and run every tab.
- **Checks:** look for console errors. Compare `window.__model.SERIES()[0].tot` with the expected numbers.
- **Expected FY 26-27 values (source data):** 12 flags and 6 notes. TTD ending balance $442,655 with $1,137,363 federal above the cap.
