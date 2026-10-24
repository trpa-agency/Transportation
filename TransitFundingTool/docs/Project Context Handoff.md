# Tahoe Transit Funding Model: Project Context Handoff

As of October 23, 2026. Prepared from the project files, three project chats (October 20 to 22), and the project memory.

Confidence tags: [Certain] means checked against a source cell or file. [Likely] means strong evidence. [Guessing] means a gap was filled.

## Read this first

- No partner has reviewed or endorsed the model. Stakeholder endorsement is TRPA's process. The tool can support it. [Certain]
- Kira answered the questionnaire on October 23, 2026 (`docs/Transit Funding Tool - Questions for Kira - Answered 10-23.docx`). Her answers are applied to the model page; see Open decisions below for what each one settled. [Certain]
- Jurisdiction splits stay even-split placeholders by her direction ("we can be more specific later on"). Treat jurisdiction-level results as drafts. [Certain]
- The South Tahoe Transit JPA is not an operator and the working assumption is that it will not become one (Kira, Oct. 23, 2026). South shore fixed route funding stays with TTD. [Certain]
- Task 4c (agreements inventory) cannot be finished from spreadsheets. The actual agreements must come from partners. [Certain]

## Purpose

The funding lead's directive is in the project doc **Overall Directive**. It quotes RFP Task 4: Funding and Implementation Strategy.

- **4a.** Document existing transit funding: amounts, match requirements, and stipulations. Cover federal, state, local, and private sources. Deliverable: fact sheet or report.
- **4b.** Formalize the draft regional transit funding model with stakeholder coordination and endorsement. Include strategies for private and non-federalized operators such as ski and airport shuttles. Use a dynamic format that allows future changes. Deliverable: updated funding model.
- **4c.** Evaluate existing agreements and recommend new agreements or MOUs. Review TRPA handbooks, policies, plans, and procedures. Deliverables: inventory of existing agreements and requirements, and recommended updates.

Her notes on the source data:

- The **costs** tab of the Example Transit Financial Scenario Workbook has the most current operator costs per route. She added state and local route conditions.
- The **Revenue %s** tab of Financial PlanG applies each revenue source by percent to routes. The consultants started it. The percentages are probably not accurate. She is filling in conditions and match requirements for each source.

Stakeholders named in the RFP: TTD, TART, South Tahoe Transit JPA, SSTMA, TNT/TMA, City of South Lake Tahoe, El Dorado County, Placer County, Douglas County, Washoe County, and Town of Truckee.

## People and roles

| Person | Role on this project |
| --- | --- |
| Funding lead | Domain expert in transportation funding. Wrote the Overall Directive. Owns funding rules and match requirements. |
| Andy | Data engineer and programmer. Tasked with building the tool the consultants have not delivered. Needs to learn from the funding lead what the tool must do. |

## What is in the Project

| Item | Type | What it is |
| --- | --- | --- |
| Overall Directive | Doc | The funding lead's email and the RFP Task 4 text |
| transit-funding-model.html | Doc | Current model page, single file, data inlined. Open it in a browser. Marked Beta. |
| Project Context Handoff | Doc | This document |
| Funding App - Information Needed | Doc | Full gap list: matching rules, cost and revenue conflicts, service data, policy decisions, with owners and priorities |
| Questions for the Domain Lead | Doc | Meeting guide for the funding lead: purpose, rules only she can set, data to request, reactions to concepts |
| Rule Errors, Pitfalls, and Open Questions | Doc | October 19 review of the first model: the 11 rule errors, 16 source data conflicts with cell references, placeholder assumptions, and 17 questions |
| Transit Funding Tool Concepts.html | Doc | The three concept mockups as one standalone page. Open it in a browser. The Concept C toggles work. |
| Example Transit Financial Scenario Workbook.xlsx | File | Costs tab: trips, hours, miles, rates, and route conditions for 21 services |
| Financial PlanG.xlsx | File | Revenue %s, Per Route Model, Tables A1 and A2, five-year plan, capital plan, Questions tab |
| Funding Model V1G.xlsx | File | Earlier consultant funding model |
| SSTMA multijurisdiction working model.xlsx | File | Weighted cost-share formula (rt 19,22,28 Cost Share tab), JPA assumptions, FY27 forecast |
| Federal, State, and Local Funds FINAL.pdf (4 files) | File | Task 4a fact sheets |

A local copy of everything above, plus the prototype app in `funding-model/`, is in `C:\Users\amcclary\Documents\GitHub\Transportation\TransitFundingTool`. Its `README.md` maps the folders.

## Work history

### October 19: Review of the first model

Claude reviewed the first interactive model against the workbooks. The draft Revenue %s shares break 11 eligibility and match rules, all on TTD services. The costs tab counts TART Main Line twice, about $2.5 million. Sixteen source cells conflict or contain formula errors. [Certain]

Output: **Rule Errors, Pitfalls, and Open Questions**, now in the Project.

### October 20: Gap list from the working folder

Claude reviewed the local OneDrive folder (`OneDrive_1_10-19-2026`). It held the fact sheets, workbooks, and an earlier prototype app in `funding-model/`. That app has 21 services, 7 service plan options, 63 funding lines, 52 rules, and an optimizer. Its calculations check out. Its inputs are the weak spot. [Certain]

Output: **Funding App - Information Needed**, now in the Project. A copy is in the OneDrive folder.

### October 21: Goal clarification, meeting guide, and concept mockups

Draft goal statement: build one shared, auditable model of how Tahoe transit operations are funded, route by route. Partners use it to test funding scenarios before committing. It should:

1. Inventory every operating funding source with amount, match, restrictions, and commitment basis (4a).
2. Check each source's use against eligibility, federal share caps, and match (4b).
3. Project agency and regional balances five years out (4b).
4. Identify existing and needed agreements (4c).

"Optimize matching" has no agreed definition yet. The current Suggest allocation button is a rules-based default. [Certain]

Claude then made two items for the meeting with the funding lead:

- **Questions for the Domain Lead** (now in the Project). Order of the meeting: her decisions first, then rules, then data, then mockups last.
- **Transit Funding Tool Concepts**, a canvas of three narrow tool mockups using real FY 26-27 figures. Each figure cites its workbook cell.

| Concept | Question it answers | Finding it surfaces |
| --- | --- | --- |
| A. Funding source lookup | Can this source pay for this service, and what does it require? | The draft puts $1,798,577 of NDOT 5311 on Routes 19X and 22. Those routes cost $1,429,636 to run. At a 50 percent federal share, $1,083,759 has no eligible operating use. The workbook lists both 50 and 40 percent match for this source. [Certain] |
| B. Route match check | Is this route fully funded, with federal money under its cap and enough match? | TTD's $1,845,127 in TDA and $265,506 in LCTOP are not applied to any route in the Per Route Model. Route 55 shows a $418,797 match shortfall that may disappear under per-grant testing. [Certain] |
| C. Five-year scenario | What happens to each agency's balance if a source ends, a partner drops out, or service is added? | The region shows a surplus through FY 28-29 only because TART's surplus offsets deficits at TTD and Lake Link. Those deficits start in FY 27-28. [Certain] |

### October 22: Gap analysis and data pipeline

Claude compared the model against the directive and RFP. Results are in the next section.

Claude then moved all data out of the page's JavaScript into a build pipeline. Details are under Current tool and data pipeline.

### October 23: Kira's answers applied

Kira returned the questionnaire (`docs/Transit Funding Tool - Questions for Kira - Answered 10-23.docx`). Her answers were applied directly to `model/transit-funding-model.html` (the pipeline is not in this repo yet):

- Data: TART 5307 at TART's $2,660,000; Route 30 at $147.80/VSH (about $517,300); the seven Lake Link private partners, NTCA, and Martis carried steady at FY 25-26 amounts ($839,273); the $232,235 planning and administration appropriation in scope; 5310 at 80 percent federal share with the TTD–Placer alternation projected through FY 30-31; Lake Link, My Ride to Work services, and vanpools marked non-federalized.
- Engine: fares count as local match (a fare line with "Counts as match" unchecked is fare replacement instead).
- Features: three scenario presets in the scenario bar (TDA and SB 125 stay in California; Lake Link federalized; TTD absorbs Lake Link); an Overview finding totaling money used outside a source's stated preference; a funding-cliffs callout on the Five-year outlook tab.
- Result: FY 26-27 regional balance $6,612,170 with 12 rule errors (was $4,810,649 with 11). The $1,801,521 increase reconciles to the four data changes above minus the higher Route 30 cost. The new errors are small TART federal share breaches that follow from using TART's larger 5307 number.

## Status against the RFP

| Item | Status | Evidence |
| --- | --- | --- |
| Costs tab as the cost source | Met [Certain] | All 21 service rows match the model. The Main Line subtotal is excluded to avoid double counting. |
| Revenue %s shares, conditions, and match | Partly met [Certain] | Shares load and are labeled unreliable. Her in-progress updates now flow in through the pipeline. |
| 4a. Existing funding at all four levels | Met [Likely] | Fact sheets exist. The model restates FY 25-26 and FY 26-27 amounts with a citation per value. Not every fact sheet amount was reconciled. |
| 4b. Funding, costs across partners, future needs | Mostly met [Certain] | Five-year outlook and agency balances work. Jurisdiction cost shares are equal-split placeholders. The SSTMA weighted formula is mentioned but not used. |
| 4b. Stakeholder coordination and endorsement | Not met [Certain] | No partner review recorded. |
| 4b. Named stakeholders | Partly met [Certain] | Ten of eleven appear. The JPA is absent. |
| 4b. Private and non-federalized operators | Not met [Certain] | The model can block federal funds from a non-federalized service. No ski or airport shuttles are entered. No strategy is written. |
| 4b. Dynamic format | Partly met [Certain] | Editing, scenario export, and a change log work. Edits save to one browser's local storage. There is no shared version. |
| 4c. Inventory of existing agreements | Not met [Certain] | A 12-item list was inferred from spreadsheet notes. No agreements were reviewed. |
| 4c. Recommended agreement updates | Partly met [Certain] | The model generates a gap list. It is raw material for the deliverable. |

## Current tool and data pipeline

The model page reads its data from a build step. The workbooks stay the source of truth.

How it works:

- `etl/build_model_data.py` reads the Scenario Workbook costs tab and Financial PlanG. It finds cells by row and column label. Inserting rows in the workbooks does not break the build.
- Hand-maintained YAML seed files in `etl/seed/` hold judgment calls: eligibility rules, commitment basis, jurisdiction shares, notes, and known data overrides.
- The build writes `data/model-data.json`, `data/model-data.js`, a build report, and `dist/transit-funding-model.html`. The `dist` file is a single page with data inlined. That file is what lives in the Project.
- Workbook paths, table names, and column maps are in `etl/config.yaml`.

Where each value comes from:

| Value | Source |
| --- | --- |
| Trips, hours, miles, operator, route conditions | Scenario Workbook, costs tab |
| Operator cost per hour | Scenario Workbook, VRH Rates column J |
| FY 26-27 amounts and later years | Financial PlanG: Tables A1 and A2, Per Route Model, TNTTMA $, Actual Revenues |
| Conditions, match text, federal share, route shares | Financial PlanG, Revenue %s |
| Service plan element costs | Financial PlanG, Tables A1 and A2 |
| FTA sub-allocation inputs | Financial PlanG, FTA Allocation Split (26-27) |
| Eligibility rules, commitment, jurisdiction shares, FY 25-26 fact sheet amounts | `etl/seed/*.yaml`, edited by hand |

To update after a workbook change:

1. Save the workbooks in the SharePoint folder "4. Funding Implementation Memo".
2. Run `build_data.bat`, or `propy etl/build_model_data.py` from ArcGIS Pro Python (3.11).
3. Read `data/build-report.md`. Fix warnings in the workbooks or seed, then rebuild.
4. Upload `dist/transit-funding-model.html` to the Project to replace the old page.

Validation done on October 22 [Certain]:

- Field-by-field diff against the values previously hardcoded in the page: zero discrepancies.
- Five-year projection regression: balances, costs, and revenues match the original to the penny. Rule error and warning counts are identical.
- Headless browser test: every tab renders. Saved scenarios rebase onto new builds.
- Current build: FY 26-27 regional balance of $4,810,649, with 11 rule errors.

The pipeline code was delivered as `transit-funding-model.zip` in the October 22 chat. The zip is not in the Project. Andy holds the working copy. Source workbooks are excluded from the zip.

## Open decisions

Kira answered the questionnaire on October 23, 2026. Status of each decision, applied to the model page the same day:

1. **Audience: answered.** TRPA first, making the case for a regional funding source; also a standard annual budgeting methodology other operators can use, and a starting point for cost-share negotiations. Results will be shown to elected officials. Deliverable: an easy-to-read table or chart.
2. **JPA: answered.** The JPA is not an operator and the assumption is it will not become one. South shore funding stays with TTD.
3. **Optimize: answered.** No optimizer. The tool flags problems and shows trade-offs.
4. **Match test level: answered.** Per grant, per recipient.
5. **Federal shares: answered for now.** NDOT 5311 at 50 percent non-federal (change later if needed); 5307 operating at 50 percent non-federal; 5310 might be 20 percent non-federal and pays ADA paratransit (to confirm with FTA).
6. **Cross-state match: answered.** CA funds can match NV routes, with political pressure not to; the "TDA and SB 125 stay in California" scenario preset shows what that costs. Toll credits: assume unavailable.
7. **Free fares: answered.** Any fares should be thought of as match. The engine now counts fare lines as local match.
8. **Cost-share method: deferred.** Keep the even-split placeholder; be more specific later.
9. **Scope: answered.** Capital out for this iteration; planning and administration funds in.

Still open for partners: actual agreements (Task 4c), revenue miles by route split by jurisdiction, state, and UZA, actual FY 26-27 FTA apportionments (using the EXAMPLE figures for now), and the private operator list with service statistics.

## Recommended next steps

1. ~~Move the data out of the page.~~ Done October 22.
2. ~~Add the JPA as a receiving agency.~~ Resolved October 23: the JPA is not an operator and will not become one (Kira). No model change needed.
3. Replace placeholder jurisdiction splits with the SSTMA weighted formula. Partners set the weights. (Kira, Oct. 23: keep the placeholder for now.)
4. Ask partners for the actual agreements for Task 4c.
5. Get the private operator list and service statistics from the funding lead (Kira, Oct. 23: "we don't have this data yet, but will work on it").
6. ~~Turn the funding lead's rule answers into the model.~~ Done October 23: answers applied to the model page's data and engine, with three scenario presets (TDA and SB 125 stay in CA, Lake Link federalized, TTD absorbs Lake Link). Every change is marked "per Kira (Oct. 23, 2026)" in the page's notes.
7. Move the pipeline repo to a shared location so others can rebuild. **Important:** the October 23 changes were made directly in `model/transit-funding-model.html` because the pipeline is not in this repo. When `pipeline/` lands, mirror them in `etl/seed/*.yaml` (and the engine template) before the next rebuild, or the rebuild will overwrite them.
8. Confirm with FTA: the 5310 federal share (set to 80 percent per Kira, "might require 20% non-federal") and the NDOT 5311 operating rate (50 percent for now versus the 40 percent in partner notes).

## Links

Copies of all three live artifacts are in this Project as of October 23. The live versions below are private to Andy's account until shared from each page's Share menu. Edits to a live version do not update the Project copy.

- Rule Errors, Pitfalls, and Open Questions (live doc): https://claude.ai/artifact/GjdizhpPwYiAEGAtPyYRma
- Questions for the Domain Lead (live doc): https://claude.ai/artifact/WWpPqKdssPTfjXedhSLQ4T
- Transit Funding Tool Concepts (mockup canvas): https://claude.ai/artifact/M98FUpuDF69vXfNMMzm84Z

The three source chats are in Andy's account and are not visible to others:

- Funding scenarios HTML app requirements (October 20)
- Project goal clarification (October 21)
- Tahoe transit funding outline review (October 22)

## Working conventions

- Agency-facing material uses TRPA brand and writing style. The mockups use Open Sans and TRPA blues.
- Writing defaults to the Microsoft Writing Style Guide. Plain language for committee, board, and leadership audiences.
- One idea per sentence. No em dashes. Oxford commas. No filler.
- Every figure should cite its workbook, tab, and cell.
- Code runs in the arcgispro-py3 environment. Settings live in config files. No secrets in code.
