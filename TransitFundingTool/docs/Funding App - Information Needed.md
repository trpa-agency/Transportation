# Tahoe Transit Funding App: Information Still Needed

**Purpose:** This is a list of what we still need before the funding app can be trusted to (1) explore funding scenarios, (2) optimize how local match is used, and (3) flag matching problems.

**Reviewed:** All files in `OneDrive_1_10-19-2026`: the four fact sheets, the four workbooks, the first HTML model, and the `funding-model/` app (engine, three apps, `RULES.md`, data).

**Where things stand:** A working app already exists in `funding-model/`. It has 21 services, 7 service-plan options, 63 funding lines, 52 rules, and an optimizer. The calculations check out. The weak spots are the inputs: many values are placeholders, assumptions, or numbers where two sources disagree. This list covers only what is missing. It does not repeat what is already done.

**Priority key**
- **P1:** Blocks matching results. The app cannot tell whether match is met until this is answered.
- **P2:** Changes the dollar results noticeably.
- **P3:** Improves the app but does not block it.

---

## 1. Matching rules to confirm (most important)

The app's match logic is only as good as these rules. Today, most match rates come from one column of the `Revenue %s` tab. The fact sheets only say "Match Required? Yes/No".

| # | Question | Why it matters | Current assumption | Ask | Pri |
|---|---|---|---|---|---|
| M1 | Is match tested **per route** or **per grant/agency**? | FTA tests match at the grant level. The app tests it on every route, which can show shortfalls that don't really exist, or hide ones that do. | Per route (MATCH-03) | TTD and TART finance staff | P1 |
| M2 | What is the federal share for each program **in each state**? | This sets how much local match each federal dollar needs. | 5307 = 50% (ADA 80%); 5311 CA and NV = 50%; 5310 = 50%; CRP = 88.53% | Caltrans, NDOT, FTA Region 9 | P1 |
| M3 | What is the NDOT 5311 match rate? | Partner notes say 40% for operating, but the workbook uses 50% (DI-17). | 50% | NDOT / TTD | P1 |
| M4 | Are **toll credits** available, and how much? | Partner notes say toll credits used to cover FTA match and now more cash match is needed. Toll credits would free up local dollars. | Not modeled | Caltrans, TRPA | P1 |
| M5 | Do **electrification credits** count as match? | The workbook says they are "not real money, only used as match," and the fact sheet budgets $8,000 (DI-18). | Match-only credit | Caltrans / FTA | P2 |
| M6 | Can **California funds** (TDA, LCTOP, SB 125) match federal funds on **Nevada routes**, and can Nevada funds match on California routes? | This controls cross-state matching. Partner notes say "TDA has to be used on Nevada routes," but the fact sheets list TDA as "CA and NV (operations only)." | CA-only use is treated as a preference (warning only) | TRPA, Caltrans, NDOT | P1 |
| M7 | Which local and private funds are **allowed** as match? Is any of them federally derived? | Federal dollars can't match federal dollars. Some partner agreements may also limit use. | Every non-federal, non-fare line counts as match | Each funding partner | P1 |
| M8 | Are the North Shore "free fares" payments **fare replacement** or **local match**? | Fare replacement reduces net cost, which lowers the federal cap. Local match raises the match available. These are very different results. | Counted as local match | Placer County / TART | P1 |
| M9 | Should **preventive maintenance** and **ADA paratransit** be treated as capital (80% federal)? | This is a common way to stretch match. It needs maintenance cost by route and the 10%-of-5307 ADA limit. | ADA at 80% with no 10% limit; preventive maintenance not modeled | TTD, TART | P2 |
| M10 | How much local match is needed for **capital**? | The capital plan has $6.75M in service-plan capital and $0.54M in governance capital, but **no funding sources**. Capital match uses the same local dollars as operating match. | Capital not modeled | TTD, TRPA | P1 |

## 2. Cost data to fix

| # | Item | Issue | Ask | Pri |
|---|---|---|---|---|
| C1 | Route 30 (Emerald Bay Shuttle) rate | Priced at $68.70/hr (Lake Link rate). VRH Rates shows $147.80/hr, and the budget is $517,288 (DI-02). | TTD | P2 |
| C2 | NLTE and Park & Ride costs | Costs tab shows $241K and $603K. TNT/TMA budget shows $694K and $894K (DI-03). | TNT/TMA | P2 |
| C3 | Lake Link hours | Contract hours are used, not actual hours (DI-19). | SSTMA | P3 |
| C4 | TTD FY 26-27 budget | The "TTD FY27 budget" tab is **empty**. | TTD | P2 |
| C5 | Admin/overhead and TNT/TMA memberships | $325K of "Memberships/Management" revenue and the related admin costs are not in the app. | TNT/TMA | P3 |
| C6 | Which costs are FTA-eligible | The app uses fully allocated cost per hour. We need eligible vs. ineligible operating cost (e.g., depreciation) to set the federal cap correctly. | TTD, TART | P2 |
| C7 | Service-plan option costs | These are planning estimates. For example, the US 50 replacement is added without removing Route 19X (DI-07). | Consultant | P3 |

## 3. Revenue data to confirm

| # | Item | Issue | Ask | Pri |
|---|---|---|---|---|
| R1 | FY 26-27 FTA apportionments | The values used are marked "EXAMPLE" (FY 25-26 plus 1%). | FTA / TRPA | P1 |
| R2 | 5307 split between TTD and Placer County | The earned-share formula uses FY 22-23 ridership and the 2020 Census. TART's 5307 is $1.65M in the model vs. $2.66M in its own plan (DI-04, AG-06). | TRPA (MPO), TTD, Placer | P1 |
| R3 | 5307 carryover and lapse dates | We need to know how long unused federal money stays available before it is lost. This is needed to flag "federal money lost for lack of match." | TTD, FTA | P1 |
| R4 | Rotating funds | 5310 and LCTOP alternate between TTD and TART each year. We need the confirmed schedule for all 5 years. | TTD, TART | P2 |
| R5 | Partner money with no FY 26-27 commitment | Lake Link private partners ($302K last year), North Tahoe Community Alliance ($487K), and Martis ($50K) are all set to $0. | SSTMA, TNT/TMA, Placer | P2 |
| R6 | Fact sheet items missing from the plan | Nevada State allocation ($346,500) and local appropriation ($232,235) are set to $0 (DI-14). | TTD | P2 |
| R7 | Conflicting amounts | TDVA is $65K on the fact sheet vs. $120K in the plan (DI-15). Washoe support to NLTE may be counted twice (DI-08). | TTD, TNT/TMA, Washoe RTC | P2 |
| R8 | Time-limited funds after they end | SB 125 ends after FY 26-27, Route 30 pilot funds end after FY 27-28, and partner notes mention a "fiscal cliff in '31." Is any replacement funding expected? CMAQ grants are noted as "coming." | TTD, TRPA | P2 |
| R9 | Growth rates for later years | Most lines are held flat or use a simple growth rate. Partners need to confirm. | Each agency | P3 |
| R10 | Cash timing | TDA arrives in late Feb or early March, and partners say "it's hard to bridge a couple months." Monthly timing is needed only if the app should show cash-flow gaps. | TTD | P3 |

## 4. Service information

| # | Item | Issue | Ask | Pri |
|---|---|---|---|---|
| S1 | **Jurisdiction cost shares** | These are even-split **placeholders** on 19X, 50, 51, 55, TTD ADA, Lake Link, Hwy 89, Hwy 267, TART ADA, Park & Ride, NLTE, Vanpools, and the plan options. They drive the jurisdiction- and state-restricted funds and the partner cost-share results. Partners describe a "% of miles per month" method. | Revenue miles by route and jurisdiction | P1 |
| S2 | **Urban vs. rural split** for mixed routes | Hwy 89, Hwy 267, Park & Ride, NLTE, and Vanpools are marked "mixed." This decides whether 5307 or 5311 can pay. | Revenue miles inside vs. outside the UZA | P1 |
| S3 | **State split** for bi-state routes | TTD ADA, Lake Link, NLTE, and Routes 50 and 51 ("portion in NV") need a CA/NV share for state-restricted funds. | Revenue miles by state | P1 |
| S4 | **Federalized or not** | All 21 services are marked federalized. Confirm this for Lake Link (Via/SSTMA), My Ride to Work services, and vanpools. Non-federalized services can't take FTA money. | SSTMA, TNT/TMA, FTA | P1 |

## 5. Decisions the app needs from the group (policy, not data)

1. **What should "optimize" mean?** Right now the app (a) funds as much service as possible, (b) spreads any shortfall evenly, and (c) uses fares, federal, earmarked, and one-time money first. Other goals are possible: lowest local contribution, fairest split among jurisdictions, or least reliance on one-time money. Which goals, and in what order?
2. **Can one agency's funds pay for another agency's service?** If so, which pairs? This needs interagency agreements.
3. **One year at a time or multi-year?** Should unused money or reserves carry forward to the next year?
4. **Cost-share formula** for jurisdictions: miles, hours, trips, population, or "who benefits"?
5. **"Ideally used in CA/NV"**: should this be a hard rule or a warning?
6. **New revenue ideas to include as scenarios.** For example, fares (the workbook asks whether to keep $0 fares) and a transportation user fee (on the Questions tab). Each one needs an estimated amount and its eligibility rules.

## 6. Matching problems the app should flag, and what each one needs

| Problem to flag | Can the app do it now? | What's needed |
|---|---|---|
| Match short on a service or grant | Yes, per route | M1 (grant-level test) |
| Federal share over the cap | Yes | M2, M3, C6 |
| Same local dollar used as match twice (operating and capital, or two grants) | No | M10, plus a grant-level match ledger |
| Federal money left unused because there isn't enough match | Partly (it explains unused funds) | R3 (lapse dates) |
| Match relies on one-time or uncommitted money | Partly (flags time-limited funds) | R5, R8 |
| Federal money used to match federal money | No | M7 (where each fund comes from) |
| Cross-state match not allowed | Warning only | M6 |
| Match lost when a partner pulls out | Yes (sensitivity tool) | R5 |

## 7. Suggested first asks (the short list)

1. **TTD and TART finance:** the match test level (M1), "free fares" treatment (M8), FTA-eligible costs (C6), and the TTD FY 26-27 budget (C4).
2. **Caltrans / NDOT / FTA Region 9:** federal share by program and state (M2, M3), toll credits (M4), and cross-state match rules (M6).
3. **TRPA (MPO):** actual FY 26-27 apportionments and the 5307 split (R1, R2), and capital funding sources (M10).
4. **Each operator:** revenue miles by route split by jurisdiction, state, and urban/rural (S1 to S3), plus federalized status (S4).
5. **SSTMA, TNT/TMA, and private partners:** FY 26-27 and later commitments (R5).
