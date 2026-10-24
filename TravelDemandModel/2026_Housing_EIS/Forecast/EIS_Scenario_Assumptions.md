# Data and Forecasting for the 2026 Housing EIS

## INTRODUCTION

As part of the 2026 TRPA Housing Element Environmental Impact Statement (EIS), TRPA prepared regional and transportation forecasts for the years 2035 and 2050. The regional forecast includes changes in development, population demographics, and visitation. The regional forecast is implemented in the Tahoe travel demand model to allow planners to assess the transportation and land use effects of proposed housing policies and development alternatives.

Three EIS alternatives were developed to evaluate a range of policy outcomes, from a baseline consistent with the 2025 RTP assumptions (Alternative 1) to scenarios that reflect varying levels and types of new housing supply (Alternatives 2 and 3). All alternatives build upon the 2022 model base year, which serves as the starting point for all forecasted changes in land use, population, employment, and visitation.

---

## FORECAST METHODOLOGY

The forecasting approach follows the same methodology established for the 2025 RTP, applying the best available information about development rates, occupancy trends, and demographic characteristics. Each alternative uses a set of configuration assumptions that determine how residential units are distributed, how occupancy is estimated, and how the population is characterized. Key modeling flags include:

- **`adjust_taz_population`** — When enabled (Alternative 1 only), the model adjusts TAZ-level population to match region-wide population control totals, ensuring the baseline scenario reproduces the forecasted residential population from the 2025 RTP.
- **`adjust_for_occ_unit_emp`** — When enabled (Alternatives 2 and 3), the model applies a town-center employment adjustment using a TAZ-level employment CSV that reflects the increased concentration of jobs near new housing development in town centers. This flag is disabled in Alternative 1, which uses the standard RTP employment inputs without modification.
- **`adjust_occupancy`** — When enabled (Alternative 3 only), the model adds additional occupied units beyond those estimated by applying census-based occupancy rates to the housing stock. In Alternative 3, the adjustment is **332 units in 2035** and **855 units in 2050**, representing the phased effect of housing conversion initiatives that transition existing seasonal homes or short-term rentals to permanent resident occupancy. This occupancy boost grows over time as conversion programs mature.

All three alternatives share identical visitor assumptions, commercial floor area forecasts, and tourist accommodation unit projections. Differences across alternatives are driven by the quantity, type, and income targeting of new residential units and the occupancy assumptions applied to that stock.

---

## DEVELOPMENT FORECAST SUMMARY

The 2035 and 2050 forecasts describe the anticipated growth in residential units, occupied housing, population, employment, and school enrollment for each alternative. The table below summarizes the key regional outcomes. The 2022 base year contains approximately 49,424 residential units region-wide.

### Summary of Regional Outcomes

| Metric | Alternative 1 | Alternative 2 | Alternative 3 |
|---|---|---|---|
| **2035 Total Residential Units** | 51,062 | 51,469 | 51,062 |
| **2035 Occupied Units** | 24,687 | 24,997 | 25,019 |
| **2035 Full-Time Residents (Persons)** | 55,588 | 56,281 | 56,340 |
| **2035 Total Employment** | 27,150 | 27,294 | 27,249 |
| **2035 School Enrollment** | 9,383 | 9,444 | 9,449 |
| | | | |
| **2050 Total Residential Units** | 54,197 | 55,435 | 54,197 |
| **2050 Occupied Units** | 26,507 | 27,750 | 27,362 |
| **2050 Full-Time Residents (Persons)** | 57,608 | 60,244 | 59,472 |
| **2050 Total Employment** | 27,580 | 27,970 | 27,850 |
| **2050 School Enrollment** | 9,558 | 9,783 | 9,715 |

**Note:** Overnight visitor room counts (13,582 total: 5,213 hotel/motel, 3,634 resort, 2,718 casino, 2,017 campground) are identical across all alternatives, reflecting shared assumptions about tourist accommodation unit construction and visitor occupancy rates consistent with the 2025 RTP.

---

## RESIDENTIAL UNITS

### Alternative 1 — RTP Baseline

Alternative 1 represents the baseline housing development scenario, consistent with the development rights assumptions of the 2025 Regional Transportation Plan. Housing is allocated from existing jurisdiction-controlled General and Bonus Unit pools, plus TRPA-controlled ADU allocations. No new income-restricted pool types (Affordable, Moderate, Achievable Bonus, Achievable General, Achievable TC, Affordable by Design, Affordable by Design TC, or JADU) are utilized.

**New residential units by jurisdiction and pool:**

| Jurisdiction | Unit Pool | Future Units |
|---|---|---|
| TRPA | ADU | 110 |
| TRPA | Bonus Unit | 388 |
| TRPA | General | 948 |
| CSLT | Bonus Unit | 89 |
| CSLT | General | 395 |
| DG | Bonus Unit | 67 |
| DG | General | 160 |
| EL | General | 281 |
| PL | Bonus Unit | 41 |
| PL | General | 582 |
| WA | Bonus Unit | 120 |
| WA | General | 196 |
| **Total** | | **3,377** |

The housing stock grows from 49,424 units in 2022 to approximately 51,062 units by 2035 and 54,197 units by 2050, with population controlled to the 2025 RTP targets of 55,592 (2035) and 57,611 (2050).

### Alternative 2 — New Housing Program with Town Center Focus

Alternative 2 represents a scenario in which the region pursues new income-restricted and workforce-housing unit pools in addition to the baseline RTP allocations, with a spatial emphasis on town center locations. All Alternative 1 pools are retained, plus new TRPA-controlled income-restricted and workforce units are added.

**Additional TRPA new housing units beyond Alternative 1:**

| Unit Pool | Future Units |
|---|---|
| Affordable | 456 |
| Moderate | 285 |
| Achievable Bonus | 228 |
| Achievable General | 57 |
| Affordable by Design | 114 |
| JADU | 98 |
| **Additional total** | **1,238** |
| **Grand total (all pools)** | **4,615** |

All Affordable units are assumed to be 100% multi-family in spatial distribution, reflecting the typical form of deed-restricted affordable housing development in the region. The housing stock grows to approximately 51,469 units by 2035 and 55,435 units by 2050. A town-center employment adjustment is applied to account for the concentration of jobs near new housing clusters.

### Alternative 3 — Existing Stock Conversion

Alternative 3 carries the same physical unit inventory as Alternative 1 (3,377 new units; gross residential totals of 51,062 in 2035 and 54,197 in 2050). Rather than adding new income-restricted physical units, Alternative 3 applies a phased occupancy adjustment representing housing policy interventions that convert existing seasonal homes or short-term rentals into permanent resident-occupied units:

- **2035:** +332 additional occupied units
- **2050:** +855 additional occupied units

This phased approach reflects the expected ramp-up of conversion programs over time, with more significant impacts materializing by 2050. A town-center employment adjustment is also applied, using a scenario-specific TAZ-level employment file. Despite having the same physical unit count as Alternative 1, occupied units reach 25,019 by 2035 and 27,362 by 2050, and the full-time population reaches 56,340 by 2035 and 59,472 by 2050.

---

## RESIDENTIAL OCCUPANCY RATE

The proportion of housing units occupied by full-time residents drives the relationship between the physical housing stock and the forecasted residential population. The 2020 Decennial Census estimated that approximately 50% of Tahoe's housing units were occupied by full-time residents. The 2022 ACS estimated 23,141 occupied units out of 49,424 total (47%).

**Occupancy assumptions by unit pool:**

| Unit Pool | Occupancy Rate | Applies To |
|---|---|---|
| Bonus Unit | 100% | All alternatives |
| CTC | 100% | All alternatives |
| Affordable | 100% | Alternatives 1 and 2 |
| Moderate | 100% | Alternatives 1 and 2 |
| JADU | 100% | Alternatives 1 and 2 |
| Achievable Bonus | 100% | Alternative 2 |
| Achievable General | 100% | Alternative 2 |
| Affordable by Design | 100% | Alternative 2 |
| ADU | 70% | All alternatives |
| General | 35% | All alternatives |

These rates reflect the deed-restricted nature of Bonus, CTC, and income-restricted units (which are restricted from short-term rental or seasonal use), the typically higher occupancy of ADUs, and the mixed-market occupancy of General units. In Alternative 1, all income-restricted pools are set to zero units and therefore do not contribute occupied units.

In Alternative 3, the `adjust_occupancy` flag adds occupied units directly on top of the pool-based occupancy calculation. The adjustment grows from 332 units in 2035 to 855 units in 2050, analogous to the short-term rental regulation and housing conversion factors described in the 2025 RTP occupancy forecast.

**Forecasted occupied units and full-time population:**

| Alternative | 2035 Occupied Units | 2035 Persons | 2050 Occupied Units | 2050 Persons |
|---|---|---|---|---|
| Alternative 1 | 24,687 | 55,588 | 26,507 | 57,608 |
| Alternative 2 | 24,997 | 56,281 | 27,750 | 60,244 |
| Alternative 3 | 25,019 | 56,340 | 27,362 | 59,472 |

---

## EMPLOYMENT

The most recent regional estimate places summertime employment at approximately 26,777 jobs in 2022, down from 28,604 jobs in 2018. Employment categories include retail, service, recreation, gaming, and other.

**Alternative 1** uses the standard RTP employment inputs without modification (`adjust_for_occ_unit_emp: no`), projecting modest employment growth driven by new commercial floor area and tourist accommodation construction.

**Alternatives 2 and 3** apply a town-center employment adjustment (`adjust_for_occ_unit_emp: yes`) using a TAZ-level file that redistributes and slightly increases employment in town centers, reflecting the expected economic activity associated with new housing density in walkable, commercially active areas. Alternatives 2 and 3 use separate town-center employment files (`taz_towncenter_jobs_alt_2.csv` and `taz_towncenter_jobs_alt_3.csv` respectively), producing slightly different employment totals between the two scenarios.

**Regional employment by category (summer, peak day equivalent):**

| Employment Category | Alt 1 (2035) | Alt 1 (2050) | Alt 2 (2035) | Alt 2 (2050) | Alt 3 (2035) | Alt 3 (2050) |
|---|---|---|---|---|---|---|
| Retail | 3,778 | 3,855 | 3,778 | 3,855 | 3,778 | 3,855 |
| Service | 7,632 | 7,777 | 7,632 | 7,777 | 7,632 | 7,777 |
| Recreation | 2,286 | 2,318 | 2,286 | 2,318 | 2,286 | 2,318 |
| Gaming | 2,580 | 2,598 | 2,580 | 2,598 | 2,580 | 2,598 |
| Other | 10,874 | 11,032 | 11,018 | 11,422 | 10,973 | 11,302 |
| **Total** | **27,150** | **27,580** | **27,294** | **27,970** | **27,249** | **27,850** |

The increase in the "Other" employment category in Alternatives 2 and 3 reflects the town-center employment adjustment, which concentrates additional jobs in mixed-use and service-oriented TAZs near new housing clusters.

---

## VISITATION

Overnight visitor assumptions are identical across all three alternatives and consistent with the 2025 RTP visitation forecast. Visitor room counts reflect projected tourist accommodation construction, short-term rental regulations, and pre-Covid seasonal occupancy rate normalization.

**Overnight visitor room counts (all alternatives, both years):**

| Accommodation Type | Rooms |
|---|---|
| Hotel / Motel | 5,213 |
| Resort | 3,634 |
| Casino | 2,718 |
| Campground | 2,017 |
| **Total** | **13,582** |

Consistent with the 2025 RTP, the visitation forecast reflects a return to pre-Covid occupancy levels for seasonal homes, flat to modest growth in occupied short-term rental units under current jurisdiction-level STR caps, and slight growth in hotel/motel and resort occupancy from new TAU construction and mega-region population growth. Day visitation is modeled as a function of overnight visitation and is not directly varied across alternatives.

---

## SCHOOL ENROLLMENT

School enrollment in the Lake Tahoe region has declined over the past two decades, with California-side enrollment falling approximately 17% and Nevada-side enrollment falling approximately 46% between 2003 and 2022. The forecast projects modest enrollment growth across all alternatives as new residents attracted by affordable and workforce housing programs add school-aged children to the regional population.

**Total school enrollment by alternative:**

| Forecast Year | Alternative 1 | Alternative 2 | Alternative 3 |
|---|---|---|---|
| 2035 | 9,383 | 9,444 | 9,449 |
| 2050 | 9,558 | 9,783 | 9,715 |

Enrollment growth rates are lower than overall population growth rates, consistent with the 2025 RTP assumption that school enrollment increases at approximately one-half the rate of population growth. Alternative 2 projects the highest enrollment by 2050, driven by its larger net addition of new housing units and a broader income distribution among new residents—lower- and moderate-income households typically have higher rates of school-aged children relative to the region's current high-income resident profile.

---

## HOUSEHOLD INCOME

Household income characteristics influence travel behavior, including auto ownership rates, transit propensity, and trip generation by mode. All three alternatives assign income characteristics to new housing units based on unit pool type and an assumed income distribution for each pool.

### Income Distribution by Unit Pool

**Alternative 1** reflects income distributions aligned with the RTP baseline, where Bonus Units are predominantly low-income (consistent with deed-restriction requirements) and General Units are almost entirely high-income (consistent with Tahoe's market-rate trajectory). CTC units are 100% low-income.

| Unit Pool | Low Income | Medium Income | High Income |
|---|---|---|---|
| Bonus Unit | 78% | 20% | 2% |
| General | 1% | 2% | 97% |
| ADU | 65% | 20% | 15% |
| CTC | 100% | 0% | 0% |

**Alternative 2** applies distinct income distributions to each new pool type. Affordable units are 100% low-income and Moderate units are 100% medium-income, reflecting the deed-restriction requirements of each program. Bonus Unit income distribution shifts toward a broader mix compared to Alternative 1, and General units retain the market-rate profile.

| Unit Pool | Low Income | Medium Income | High Income |
|---|---|---|---|
| Bonus Unit | 40% | 25% | 35% |
| General | 1% | 2% | 97% |
| ADU | 65% | 20% | 15% |
| CTC | 100% | 0% | 0% |
| Affordable | 100% | 0% | 0% |
| Moderate | 0% | 100% | 0% |

**Alternative 3** uses the same income distributions as Alternative 1 for all unit pools, as no new income-restricted units are added. The income characteristics of the 332 (2035) and 855 (2050) additional occupied units from the conversion adjustment are applied proportionally based on the existing income mix of converted housing stock.

### Occupied Units by Income Category

| Alternative | Year | Low Income | Medium Income | High Income | Total Occupied |
|---|---|---|---|---|---|
| Alternative 1 | 2035 | 10,563 | 4,889 | 9,235 | 24,687 |
| Alternative 1 | 2050 | 11,441 | 5,142 | 9,924 | 26,507 |
| Alternative 2 | 2035 | 10,709 | 4,952 | 9,336 | 24,997 |
| Alternative 2 | 2050 | 11,650 | 5,607 | 10,493 | 27,750 |
| Alternative 3 | 2035 | 10,563 | 5,042 | 9,414 | 25,019 |
| Alternative 3 | 2050 | 11,441 | 5,556 | 10,365 | 27,362 |

Alternative 2 produces the most significant shift toward medium-income occupied units by 2050, driven by the 285 Moderate units assigned 100% medium-income occupancy. Alternative 3 shows a modest increase in medium- and high-income occupied units relative to Alternative 1 in both forecast years, reflecting the income characteristics assumed for units that transition from seasonal to permanent occupancy through conversion programs.

---

## ZONE PROPORTIONS

All alternatives apply spatial distribution assumptions for new housing units within each TAZ, allocating new development across three sub-types. A key distinction in Alternative 2 is that Affordable pool units are directed entirely to multi-family development, reflecting the typical construction form of deed-restricted affordable housing.

| Housing Sub-Type | Alt 1 & 3 Default | Alt 2 Default | Alt 2 Affordable Pool |
|---|---|---|---|
| Multi-Family | 35% | 35% | 100% |
| Single-Family | 50% | 50% | 0% |
| Infill | 15% | 15% | 0% |

This distinction ensures that income-restricted affordable units in Alternative 2 are modeled as compact multi-family development concentrated in town centers, consistent with observed affordable housing development patterns in the Tahoe Basin.

---

*Run identifier: `run_2026-04-29_131307` | Base year: 2022 | Forecast years: 2035, 2050 | Model: TRPA Travel Demand Model*
