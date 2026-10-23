# Transit Funding Model: Rule Errors, Pitfalls, and Open Questions

Oct 19, 2026 · @Andy

## Summary

The draft allocation shares on Revenue %s break 11 eligibility and match rules at current route costs, and several source cells disagree with each other. Each item below cites its workbook cell so you can confirm or correct it; the numbered questions at the end are the decisions the model can't make without you.

The largest issues: the costs tab counts TART Main Line twice (about $2.5 million), federal funds on Routes 19X, 22, and 50 exceed the 50 percent operating share, and Route 30 and the TNT/TMA services look under-costed. Figures are FY 26-27 from the default scenario in the interactive model (transit-funding-model.html) unless noted.

## Rule errors in the draft shares

All 11 errors sit on TTD services. Most draft shares equal TTD's FY 24-25 route allocations (Actual Revenues tab), not shares of the current costs tab.

| Service | Rule broken | Detail | Likely cause |
| --- | --- | --- | --- |
| Route 19X | Federal share cap | FTA 5311 (NDOT) $610,099 is 126% of the $483,071 cost; cap is 50% | All $1.8 million of 5311 split across two routes that cost $1.43 million |
| Route 19X | Local match | Needs $610,099 non-federal; $234,859 applied | Follows from the cap overrun |
| Route 22 | Federal share cap | FTA 5311 (NDOT) $1,188,478 is 126% of the $946,565 cost | Same as Route 19X |
| Route 22 | Local match | Needs $1,188,478 non-federal; $457,740 applied | Follows from the cap overrun |
| Route 50 | Federal share cap | 5307 formula, former CMAQ, and carryover total $1,376,129, or 68% of the $2,021,797 cost | Three 5307 pots stacked on one route |
| Route 50 | Local match | Needs $1,376,129 non-federal; $1,172,818 applied | Follows from the cap overrun |
| Route 55 | Local match | Needs $774,050 non-federal; $746,308 applied ($27,742 short) | Non-federal shares slightly low |
| Route 30 | Federal share cap | Carbon Reduction Program $271,910 is 145% of net cost ($240,450 less $53,500 fares); cap is 88.53% | Route 30 cost likely understated (see data issues) |
| Route 19X | California-only source | LCTOP share of 7.0% on a Nevada route | Draft splits LCTOP by service hours across all TTD routes |
| Route 22 | California-only source | LCTOP share of 13.7% on a Nevada route | Same |
| Route 28 | California-only source | LCTOP share of 3.7% on a Nevada route | Same |

The model also raises 6 warnings: TDA LTF and STA on Routes 19X, 22, and 28, which Revenue %s B10 and B12 say are "ideally used in CA." The model's rules-based suggestion clears all 11 errors in FY 26-27, but shares are fixed across years, so the same split shows 5 errors by FY 30-31 as costs outgrow revenue.

## Pitfalls that affect any allocation

These hold no matter how the shares are set, because they come from the rules themselves or from the money available.

- **More NDOT 5311 than the rural routes can absorb.** TTD has $1,798,577 in 5311, but Routes 19X and 22 cost $1,429,636, so a 50% federal share uses only $714,818. TTD's own worksheet applies $912,052 (T2-4 Q146:R146). About $1.08 million needs another eligible use (administration, capital, or other rural service).
- **Unclear 5311 match rate.** Revenue %s C6 says 50% non-federal; partner notes (F64) say NDOT match is 20% for administration, 40% for operating, and 5% for capital. At 40%, the usable 5311 on 19X and 22 rises to $857,782.
- **ADA paratransit share.** Revenue %s AE3 says 5307 can cover 80% of ADA costs, while 5310 is listed at 50%. The model applies 80% only to 5307 on ADA services.
- **California funds on Nevada routes.** The fact sheets allow TDA in Nevada (operations only), but B10 says "ideally used in CA." Partner notes say TDA has to be used on Nevada routes and that losing it shifts the cost to Douglas County or other partners. Without TDA, Routes 19X and 22 can't meet their match.
- **LCTOP rule.** The State Funds fact sheet says LCTOP is California-only, while Revenue %s B15 says "ideally used in CA." The model treats it as California-only, which drives three of the errors.
- **Electrification credits.** Revenue %s B16 and C16 call them "not real money" usable only as match; the fact sheet lists $8,000 budgeted for TTD operations. The model counts them as match only.
- **Fares are not match.** Fares reduce the net cost that federal shares apply to. Only Route 30 ($5 one-way) and NLTE collect fares.
- **Jurisdiction-limited funds.** Douglas County and City of South Lake Tahoe money can fund only their own share of Lake Link. Both fit at the current one-third and two-thirds split, but a different zone split could break that.
- **One agency's funds on another agency's route.** This needs an interagency agreement; the model flags it as a warning.
- **Time-limited money.** $3.41 million (13 percent) of FY 26-27 revenue ends within the plan: 5307 carryover ($946,282), SB 125 for TTD ($825,000) and Lake Link ($750,000), Emerald Bay pilot funds ($619,796), the NLTE reserve ($240,000), and 5310 carryover ($30,277). The region-wide balance turns negative in FY 29-30 ($139,873 deficit) before any service plan elements.

## Data inconsistencies in the source files

Sixteen cells or values disagree with another source or contain a formula error; the first seven each move totals by $100,000 or more. Workbook references are Scenario (Example Transit Financial Scenario Workbook), PlanG (Financial PlanG), and V1G (Funding Model V1G).

| # | Issue | Where | Effect and how the model handles it |
| --- | --- | --- | --- |
| 1 | Total counts TART Main Line twice | Scenario costs K25 sums the Main Line subtotal (K16) and its segments (K13:K15) | $2,497,613 counted twice; the total is $20,581,100, not $23,078,713. Model counts segments once |
| 2 | Route 30 priced at the Lake Link rate | Scenario costs J7 looks up "Via" at $68.70/VSH | Cost shows $240,450; VRH Rates J10 lists $147.80/VSH (about $517,300) and PlanG T2-4 G20 budgets $517,288. Model keeps $240,450 |
| 3 | TNT/TMA costs far below budget | Scenario costs rows 22–24 vs PlanG TNTTMA $ F22, F43 | Costs tab: NLTE $241,181, Park & Ride $602,952. Budget: NLTE $694,260, Park & Ride $894,233. TNT/TMA shows a $900,200 surplus as a result |
| 4 | TART 5307 amount | PlanG Per Route Model E12 vs T5-7 G59 | $1,653,136 (earned-share split) vs $2,660,000 (TART plan). Model uses the split |
| 5 | TART service-hour total counts Main Line twice | PlanG Operating Stats F45 sums F19:F26 | TART 5307 shares on Revenue %s row 3 sum to 72%. V1G fixes it; model uses the V1G basis |
| 6 | TDA rows mislabeled and unused | PlanG Per Route Model D19, D21 | Labeled LTF and STA but hold TTD's rural third ($615,042) and urban two-thirds ($1,230,085) of LTF plus STA; no route formulas use them. Model uses LTF $1,263,326 and STA $581,801 (T2-4 G66:G67) |
| 7 | US 50 service added without removing 19X | PlanG T2-4 rows 21 and 29 | "Replace 19X" adds $476,500 with 19X's cost still counted |
| 8 | Washoe support may be counted twice | PlanG Revenue %s row 25 vs TNTTMA $ F11 | Draft gives 4.2% of Washoe RTC's $296,055 to NLTE, but TNT/TMA budgets Washoe County NLTE support separately ($12,500). Model applies RTC only to TART's Nevada segment |
| 9 | TDVA formula error | PlanG Per Route Model O28 | Multiplies the Nevada State Parks amount (D27, $85,000) instead of TDVA (D28, $120,000) |
| 10 | LCTOP and interest shares leave out Route 30 | PlanG Revenue %s rows 15, 20 | Divide by TTD hours including Route 30 but give it 0%, so shares sum to 90%. Model uses the V1G basis (F48) |
| 11 | Revenue %s check totals | PlanG Revenue %s row 53 and column AD | G53 onward sum only rows 37–51; AD10 sums F:K and skips the ADA column, so it shows 88% though the shares total 100% |
| 12 | Route 30 fares end a year early | PlanG T2-4 H72 | $0 fares in FY 27-28 though the pilot runs (cost $523,384 in H20). Model carries $54,570 |
| 13 | TART 5310 missing from TART plan | PlanG Per Route Model E17 (FTA split J35) | $75,225 to Placer in FY 26-27 is not in T5-7 Table A2 |
| 14 | Fact sheet items missing from the FY 26-27 plan | State Funds and Local Funds 1 fact sheets | Nevada State allocation $346,500, local appropriation $232,235, Martis Zones of Benefit $50,000 (all FY 25-26). Model lists them at $0 |
| 15 | Fact sheet and plan disagree | Local Funds 1 fact sheet | TDVA $65,000 (FY 25-26) vs $120,000 (FY 26-27 plan). The Travel North Tahoe Nevada card shows "TTD budgeted $8,000" though it funds NLTE |
| 16 | Copied and broken cells | PlanG Per Route Model row 1; Revenue %s H83; Actual Revenues G83 | Row 1 cost cells for Lake Link, Main Line, Hwy 89, 267, and TART Connect repeat TTD route values; H83 and G83 show #REF! |

The costs tab also notes that Lake Link hours are from the contract, not actuals (U12).

## Placeholders and assumptions to confirm

The model fills gaps in the source files with the values below. Each one can be changed in the model, and any change is logged.

| Assumption | Value used | Basis |
| --- | --- | --- |
| Jurisdiction shares on multi-jurisdiction routes | Equal split among the jurisdictions in costs tab column C | No allocation formula in the files; the SSTMA working model averages shares of miles, hours, stops, and ridership |
| Lake Link zone split | One-third Douglas County (Zone 1), two-thirds City of South Lake Tahoe (Zones 2–3) | Even split by zone in PlanG Operating Stats rows 16–18, marked "Example" |
| ADA paratransit service areas | TTD: CSLT, El Dorado, Douglas (follows Route 50). TART: Placer County | Costs tab lists no local conditions for either |
| Urban or rural class | 19X and 22 rural; other TTD routes urban; Route 30 urban; Hwy 89, Hwy 267, Park & Ride, NLTE, vanpools both | TTD classes from PlanG Operating Stats D41:D42; the rest are assumed |
| Sources the draft left unallocated | Split by service hours among eligible routes of the receiving agency | Applies to TART 5307 (corrected), 5311 Caltrans, TART TDA (four rows), SGR, Placer TOT for fixed route ($2,447,400), Town of Truckee, both North Shore partner rows, and Park & Ride partners |
| Placer TOT subcategories | Treated as one pool | T5-7 G68 lists $150,000, $1,874,954, $277,500, and $144,946 with no names or restrictions |
| Vanpools | Included at $195,800 | TNT/TMA FY 26-27 budget; not in the costs tab |
| TNT/TMA administration and marketing | Excluded, with their revenues | Not route costs; $321,870 and $223,823 in the TNT/TMA budget |
| "Additional Truckee" ($2,927) | Assumed to be Visit Truckee Tahoe | FY 25-26 per-route model lists Visit Truckee Tahoe at $2,932 |
| Cost escalation | 4% per year; TART Connect 5%; My Ride to Work 3% | VRH Rates notes; T5-7 escalates TNT/TMA at 4% |
| Revenue growth | FTA 1%; TDA 0.025%; Placer TOT 4%; Washoe RTC 2%; Tahoe Blue 6% to a $750,000 cap; Douglas $850,000 from FY 27-28; others flat | T2-4 Table A1 and T5-7 Table A2 notes |
| FY 26-27 FTA apportionment | FY 25-26 apportionment plus 1% | FTA Allocation Split (26-27), marked "EXAMPLE" |
| FTA 5310 rotation | Placer in FY 26-27; TTD in FY 27-28 and FY 29-30; later Placer years not projected | FTA split J35 and T2-4 row 63 |
| Lake Link private partners | $0 in FY 26-27 | T2-4 note 8: no commitment secured |

## Questions for you

Answers to the first five change the results the most.

1. Is Route 30's FY 26-27 cost $240,450 (costs tab) or about $517,000 (VRH Rates $147.80/VSH and the Emerald Bay budget)?
2. Which TNT/TMA costs should the model use: the costs tab estimates (NLTE $241,181, Park & Ride $602,952) or the FY 26-27 budget (NLTE $694,260, Park & Ride $894,233)?
3. Is TART's FY 26-27 FTA 5307 for operations $1,653,136 (earned-share split) or $2,660,000 (TART plan)?
4. Is the NDOT 5311 match for operating 50 percent (Revenue %s C6) or 40 percent (notes F64)?
5. How is the NDOT 5311 that Routes 19X and 22 can't absorb (about $1.08 million at 50 percent) used: administration, capital, or other service?
6. Should TDA on Nevada routes be allowed without a warning? Is LCTOP strictly California-only?
7. Are electrification credits cash for operations ($8,000) or match only?
8. How should costs on routes serving several jurisdictions be split? Is the SSTMA average of miles, hours, stops, and ridership the method partners want?
9. What share of Lake Link service hours falls in Zone 1 (Douglas County) versus Zones 2 and 3 (City of South Lake Tahoe)?
10. What restrictions apply to each of the four Placer TOT subcategories?
11. Which TART routes count as rural for Caltrans 5311: Hwy 89 and Hwy 267 only? Is Route 30 inside the Lake Tahoe urbanized area?
12. Does Washoe RTC's $296,055 include NLTE support, or is the $12,500 Washoe County NLTE contribution separate?
13. Should vanpools and TNT/TMA administration and marketing be in the model?
14. Are the Nevada State allocation ($346,500) and local appropriation ($232,235) still expected in FY 26-27, and for operations?
15. Do any Lake Link private partners have FY 26-27 commitments? This ties to the open question in PlanG: "What revenues can we count on for 27-28 for Lake Link?"
16. Does replacing 19X with US 50 service remove the 19X cost, and do Route 30 fares continue in FY 27-28?
17. Is "Additional Truckee" ($2,927) the same contribution as Visit Truckee Tahoe?

## Sources

All files are in the shared OneDrive folder (OneDrive\_1\_10-19-2026).

- Example Transit Financial Scenario Workbook.xlsx: costs and VRH Rates tabs
- Financial PlanG.xlsx: Revenue %s, Actual Revenues, Per Route Model, Operating Stats, FTA Allocation Split (26-27), T1 Summary Table, T2-4 A1 TTD LL Costs, T5-7 TART TNTTMA FinancialPlan, TNTTMA $, Questions
- Funding Model V1G.xlsx: Revenue %s and Operating Stats (corrected bases)
- SSTMA multijurisdiction transit services working model.xlsx: rt 19, 22, 28 Cost Share; Zone 1-5 Peak Vehicles
- Federal Funds, State Funds, Local Funds 1 of 2, and Local Funds 2 of 2 fact sheets (FINAL)
- transit-funding-model.html: the interactive model these figures come from
