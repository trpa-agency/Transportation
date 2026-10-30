# Tahoe Regional Transit Funding Model: start here

This folder holds everything needed to continue the TRPA regional transit funding model. It covers RFP Task 4, Funding and Implementation Strategy. The model is one HTML page. It shows how transit operations in the Lake Tahoe Region are funded route by route, checks each use of funds against its rules, and projects agency balances five years out.

## Read in this order

1. `docs/Project Context Handoff.md`: purpose, work history, status against the RFP, decisions, and next steps.
2. `docs/Domain Lead Answers 2026-10-23.md`: the funding rules and data decisions TRPA made. Most of the model follows from these.
3. `docs/Model Logic.md`: how the page calculates, including known gaps.
4. `docs/Review Feedback 2026-10-27.md`: the latest review and what changed.
5. `pipeline/README.md`: how the page is built from the workbooks.

Older working papers in `docs/` are dated records. Don't update them to match later decisions:

- **Rule Errors, Pitfalls, and Open Questions:** Oct. 19.
- **Funding App - Information Needed:** Oct. 20.
- **Questions for the Domain Lead:** Oct. 21.
- **The two Kira questionnaires:** Oct. 23.
- **Overall Directive:** the original request and the RFP text.

## Folder map

| Path | What it is |
| --- | --- |
| `model/transit-funding-model.html` | The current model page. Built by the pipeline; never edit it by hand |
| `model/archive/` | Earlier versions of the page |
| `pipeline/` | Build: `etl/build_model_data.py`, `etl/config.yaml`, `etl/seed/*.yaml`, and the page template |
| `pipeline/editions/` | Builds the public page (Existing funding conditions only) and the full page from `model/` |
| `source-data/workbooks/` | Copies of the four source workbooks. The live copies are in the TRPA SharePoint folder "4. Funding Implementation Memo" |
| `source-data/fact-sheets/` | Federal, State, and Local Funds fact sheets (FINAL) |
| `docs/` | Context, decisions, and working papers |
| `mockups/` | The three Oct. 21 concept mockups |
| `funding-model/` | An earlier prototype (Oct. 20). Not used by the current page |

## Rules for working here

- **Change data in the workbooks or the seed, then rebuild.** Run `pipeline/build_data.bat` or `propy etl/build_model_data.py`. Read `pipeline/data/build-report.md`, then copy `pipeline/dist/transit-funding-model.html` to `model/`.
- **Change the page in `pipeline/template/transit-funding-model.template.html`.** Never edit `model/` directly; the next build overwrites it.
- **A decision that overrides a workbook value goes under `keep` in the seed,** with a `reason` and the `workbook` value at the time. Don't hardcode it anywhere else.
- **Verify with `--check`.** `propy etl/build_model_data.py --check` compares the build with the page in `model/` and lists every difference. Explain each one before replacing the page.
- **After a template change, test the page.** Open every tab, check for console errors, and confirm the key numbers in `docs/Model Logic.md` (Testing the page).
- **Keep the previous page.** Before replacing `model/transit-funding-model.html`, copy the old one to `model/archive/` with its date.
- **Python** runs in ArcGIS Pro's `arcgispro-py3` environment (`propy`). Settings live in `etl/config.yaml`. No secrets in code.

## Writing and design conventions

- **Style:** Microsoft Writing Style Guide. Plain language for committee, board, and leadership audiences, including elected officials.
- **Sentences:** one idea per sentence. No em dashes. Oxford commas. No filler or hype. Don't tack a justifying clause onto a sentence after a comma.
- **Citations:** cite TRPA decisions as TRPA direction (Oct. 23, 2026). Never cite a staff member by name. In the page, sources are numbered on the Sources and notes tab and cited with superscripts. Don't repeat file names in the page.
- **Figures:** every figure traces to a workbook tab and cell. That detail lives in the seed and in each source's Details dialog.
- **Confidence tags** in analysis and handoff notes: [Certain] means checked against a source; [Likely] means strong evidence; [Guessing] means a gap was filled.
- **Palette:** the page uses the Connecting Tahoe palette (token block in the template head). For other TRPA work, use the trpa-claude-skills repo (github.com/trpa-agency/trpa-claude-skills): `trpa-brand`, `trpa-dashboard-stack`, and `trpa-dashboard-qa`. The page follows the dashboard stack: Plotly, Calcite, and AG Grid.

## Decisions in force (Oct. 23 and 27, 2026)

- **Audience and horizon:** TRPA first, to make the case for a regional funding source. Also a standard budgeting method other operators can use, and a starting point for cost-share talks. Results go to elected officials. The horizon is the fiscal year and five years.
- **No optimizer:** the tool flags problems and shows trade-offs.
- **Federal shares:** NDOT 5311 and 5307 operating at 50 percent; 5310 at 80 percent, to confirm with FTA. No toll credits.
- **Fares and preferences:** fares count as local match. "Ideally used in" conditions are preferences: warn and total them, but allow.
- **Placeholders and scope:** jurisdiction shares stay even-split placeholders. Operating only; capital is out. Planning and administration funds are in.
- **TART 5307:** $2,660,000 from TART's plan.
- **Private partners:** Lake Link partners, NTCA, and Martis are held steady at FY 25-26 amounts.
- **JPA and service status:** the South Tahoe Transit JPA is not an operator. Lake Link, My Ride to Work, and vanpools are non-federalized.
- **Federal funds and surpluses:** federal funds above the share cap are left out of balances. Agency surpluses do not carry into the next year by default (Oct. 30, 2026). Carryover is a setting.

## Open items

- **Match testing:** TRPA chose per grant, per recipient. The engine still tests per service. This is the largest gap between the decisions and the code.
- **Missing data:** revenue miles by route, jurisdiction, state, and UZA; actual FY 26-27 FTA apportionments; the private and non-federalized operator list; and the actual agreements for Task 4c.
- **TNT/TMA costs:** revenue is 2.3 times cost, so the costs tab likely understates NLTE and Park & Ride.
- **FTA confirmations:** the 5310 federal share and the NDOT 5311 operating rate.
- **Stakeholder review:** no partner has reviewed or endorsed the model yet.
- **Test question:** TRPA's own test for any version is "Where are the biggest gaps in funding?"
