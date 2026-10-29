# Tahoe Transit Funding Model: Project Context Handoff

As of October 29, 2026. Prepared from the project files, the project chats (October 20 to 29), and the project memory. New readers: start with `CLAUDE.md` at the top of this folder.

Confidence tags: [Certain] means checked against a source cell or file. [Likely] means strong evidence. [Guessing] means a gap was filled.

## Read this first

- No partner has reviewed or endorsed the model. Stakeholder endorsement is TRPA's process. The tool can support it. [Certain]
- Kira answered the questionnaire on October 23, 2026 (`docs/Transit Funding Tool - Questions for Kira - Answered 10-23.docx`). Her answers are applied to the model page; see Open decisions below for what each one settled. [Certain]
- Jurisdiction splits stay even-split placeholders by her direction ("we can be more specific later on"). Treat jurisdiction-level results as drafts. [Certain]
- The South Tahoe Transit JPA is not an operator and the working assumption is that it will not become one (Kira, Oct. 23, 2026). South shore fixed route funding stays with TTD. [Certain]
- Task 4c (agreements inventory) cannot be finished from spreadsheets. The actual agreements must come from partners. [Certain]
- Match is still tested per service, though TRPA chose per grant, per recipient on October 23. See `docs/Model Logic.md`. [Certain]

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

Kira returned the questionnaire (`docs/Transit Funding Tool - Questions for Kira - Answered 10-23.docx`). Her answers were applied directly to `model/transit-funding-model.html` (the pipeline was not in the repo then; they are now in `pipeline/etl/seed/`):

- Data: TART 5307 at TART's $2,660,000; Route 30 at $147.80/VSH (about $517,300); the seven Lake Link private partners, NTCA, and Martis carried steady at FY 25-26 amounts ($839,273); the $232,235 planning and administration appropriation in scope; 5310 at 80 percent federal share with the TTD–Placer alternation projected through FY 30-31; Lake Link, My Ride to Work services, and vanpools marked non-federalized.
- Engine: fares count as local match (a fare line with "Counts as match" unchecked is fare replacement instead).
- Features: three scenario presets in the scenario bar (TDA and SB 125 stay in California; Lake Link federalized; TTD absorbs Lake Link); an Overview finding totaling money used outside a source's stated preference; a funding-cliffs callout on the Five-year outlook tab.
- Result: FY 26-27 regional balance $6,612,170 with 12 rule errors (was $4,810,649 with 11). The $1,801,521 increase reconciles to the four data changes above minus the higher Route 30 cost. The new errors are small TART federal share breaches that follow from using TART's larger 5307 number.

### October 27: Review feedback and pipeline rebuild

Review feedback was applied to the model page:

- **Tab structure.** Today, Inputs you can change, Results and future, and Reference. A new Existing funding conditions tab shows the source data. All editable inputs are on one Inputs and assumptions page.
- **Engine.** Federal funds above each source's federal share cap are left out of agency balances. Surpluses carry into the next fiscal year.
- **Interface.** The presets are checkboxes that can be undone. The allocation split applies when chosen. Export and Import use Excel.
- **Citations and look.** Sources are numbered, with superscripts throughout. TRPA is cited instead of Kira. The palette is Connecting Tahoe, and fonts are larger.

TTD's FY 26-27 surplus fell from $1,580,018 to $442,655 because $1,137,363 of its federal funds has no eligible operating use. The remaining surplus depends on $2.42 million in one-time funds. [Certain]

The October 22 pipeline zip was never saved to the repo. A new pipeline was written in `pipeline/`. It reproduces the October 27 page field for field. The one change: TART 5307 now reads Table A2 G59, which TRPA chose on October 23. A test with rows inserted in all eight source tabs still found every value. The October 23 decisions are recorded as `keep` entries in the seed, each with a reason. [Certain]

### October 28 and 29: Look, wording, and a public page

The project changed hands on October 27. These changes followed:

- **Palette.** Colors follow the Connecting Tahoe brand in the TRPA design system: blue #2B94D1, deep teal #044554, red #BA5B53, sage #54746A, green #98CA4D, and gold #E4CB3F. Text uses the darker text steps.
- **Chart colors.** Each funding level keeps one color across charts: federal blue, state green, local public red, private gold, fares sage, and other gray. Revenue by funding level shows FY 25-26 as lighter bars of the same colors. Commitment basis has its own scale, with teal and sage for firm sources and reds for at-risk sources. Ending balance bars are deep teal for surpluses and TRPA brick #9C3E27 for deficits. Operating cost by service is all deep teal, grouped by operator.
- **Overview.** New lead text, a draft caveat, and four boxes: Today, Inputs users can change, Results and future, and Reference. The Current scenario summary moved to the top of the One-year outlook and follows the selected year.
- **Names.** Results is now One-year outlook. Assumptions and notes is now Sources and notes. The Results year selector is now Fiscal year. Interface text says "users" instead of "you."
- **Public page.** `pipeline/editions/` builds two pages from `model/`. The public page shows only Existing funding conditions, retitled and marked DRAFT, with a link to the full model. The full page is a copy of the model page. Password protection is not set up. The repo is public, so both pages and the workbooks can be downloaded from GitHub. [Certain]
- **Cost per rider.** Left off. Same-year route costs exist only for six TTD services. See next steps 12 and 13. [Certain]

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
| 4b. Dynamic format | Partly met [Certain] | Editing, Excel scenario export and import, and a change log work. A pipeline rebuilds the page from the workbooks. Edits save to one browser's local storage; there is no shared version. |
| 4c. Inventory of existing agreements | Not met [Certain] | A 12-item list was inferred from spreadsheet notes. No agreements were reviewed. |
| 4c. Recommended agreement updates | Partly met [Certain] | The model generates a gap list. It is raw material for the deliverable. |

## Current tool and data pipeline

The model page is built by `pipeline/` (rebuilt October 27, 2026). The workbooks stay the source of truth. See `pipeline/README.md` for details.

- `pipeline/etl/build_model_data.py` reads the Scenario Workbook costs tab and Financial PlanG. It finds rows by label, so inserting rows is safe.
- `pipeline/etl/seed/*.yaml` holds the judgment calls: eligibility rules, commitment basis, jurisdiction shares, notes, and values held over the workbook (`keep`, each with a reason and the workbook value at the time).
- `pipeline/etl/config.yaml` holds the workbook folder, file names, and the costs tab and Revenue %s layouts.
- `pipeline/template/transit-funding-model.template.html` is the page without data. Change the page here, not in `model/`.
- The build writes `pipeline/data/` (data and build report) and `pipeline/dist/transit-funding-model.html`.
- `pipeline/editions/` builds the public and full pages from `model/`. See `pipeline/editions/README.md`.

To update after a workbook change:

1. Save the workbooks. To build from the live copies, set `workbook_folder` in `pipeline/etl/config.yaml` to the synced SharePoint folder "4. Funding Implementation Memo".
2. Run `pipeline/build_data.bat`, or `propy etl/build_model_data.py` from `pipeline/`.
3. Read `pipeline/data/build-report.md`. It lists warnings, workbook values that changed, and seed values held over the workbook.
4. Copy `pipeline/dist/transit-funding-model.html` to `model/`, then upload it to the Project.
5. Run `pipeline/build_editions.bat` to rebuild the public and full pages.

Validation on October 27 [Certain]:

- Field-by-field comparison with the October 27 page: one difference, the TART 5307 citation above.
- The build was run on Andy's computer against `source-data/workbooks/`: 0 warnings, 21 held values.
- Headless browser test of the built page: every tab renders with no console errors. FY 26-27 has 12 rule errors.

## Open decisions

Kira answered the questionnaire on October 23, 2026. Status of each decision, applied to the model page the same day:

1. **Audience: answered.** TRPA first, making the case for a regional funding source; also a standard annual budgeting methodology other operators can use, and a starting point for cost-share negotiations. Results will be shown to elected officials. Deliverable: an easy-to-read table or chart.
2. **JPA: answered.** The JPA is not an operator and the assumption is it will not become one. South shore funding stays with TTD.
3. **Optimize: answered.** No optimizer. The tool flags problems and shows trade-offs.
4. **Match test level: answered.** Per grant, per recipient. Not yet built: the engine still tests per service.
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
6. ~~Turn the funding lead's rule answers into the model.~~ Done October 23: answers applied to the model page's data and engine, with three scenario presets (TDA and SB 125 stay in CA, Lake Link federalized, TTD absorbs Lake Link). Every change is marked "per TRPA (Oct. 23, 2026)" in the page's notes and held as a `keep` entry in the pipeline seed.
7. ~~Put the pipeline in the repo.~~ Done October 27: `pipeline/` rebuilt, with the October 23 decisions in the seed and the October 27 engine in the template. Next, move the repo to a shared location so others can rebuild.
8. Confirm with FTA: the 5310 federal share (set to 80 percent per Kira, "might require 20% non-federal") and the NDOT 5311 operating rate (50 percent for now versus the 40 percent in partner notes).
9. Build per-grant, per-recipient match testing in the engine, as TRPA chose on October 23.
10. Get TNT/TMA's FY 26-27 operating costs. The costs tab estimates leave TNT/TMA revenue at 2.3 times cost.
11. Ask TTD or the consultant whether Table A1's 35,680 TTD service hours include Route 30, which is also added as its own line. [Guessing]
12. Get FY 25-26 route operating costs from TART, SSTMA, and TNT/TMA, plus ridership for the TNT/TMA services, so cost per rider can be shown with cost and ridership from the same year. The workbooks have same-year route costs only for six TTD services (FY 24-25, Per Route Model row 1). The TART and Lake Link columns in that row repeat the TTD values. Cost per rider is left off the model until this data arrives (TRPA direction, Oct. 29, 2026). [Certain]
13. Ask TTD or the consultant to reconcile TTD's FY 24-25 route costs with its hourly rate. The Per Route Model FY 24-25 costs imply $191 to $214 per service hour. The VRH Rates tab says the FY 26-27 rate of $214.66 is the FY 24-25 actual plus 4 percent a year, which implies about $198. [Certain]

## Links

Copies of all three live artifacts are in this folder (`docs/` and `mockups/`) and in the claude.ai Project as of October 23. The live versions below are private to Andy's account until shared from each page's Share menu. Edits to a live version do not update the Project copy.

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
- Every figure should cite its workbook, tab, and cell. In the page, file names become superscript numbers keyed to the numbered source list.
- Cite TRPA decisions as TRPA direction (Oct. 23, 2026), never a staff member by name.
- The model page uses the Connecting Tahoe palette. Each funding level keeps one color in every chart. Other agency material uses the TRPA brand (trpa-claude-skills repo).
- Code runs in the arcgispro-py3 environment. Settings live in config files. No secrets in code.
