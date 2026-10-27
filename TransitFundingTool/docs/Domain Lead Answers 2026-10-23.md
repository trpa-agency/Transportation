# Domain lead answers, October 23, 2026

Transcript of `Transit Funding Tool - Questions for Kira - Answered 10-23.docx`. Kira is TRPA's transportation funding lead. The answers are quoted as written. The last column says how each one is applied in the model as of October 27, 2026.

In the model and in anything agency-facing, cite these decisions as TRPA direction (Oct. 23, 2026), not by name.

## 1. What the tool is for

| # | Question | Answer | In the model |
| --- | --- | --- | --- |
| 1.1 | Last three funding questions that took over an hour | No answer | |
| 1.2 | First decision the tool should support | "A case for a regional funding source. But creating a consistent, standard annual budgeting methodology and creating a starting place for partner cost-sharing negotiations are also critical." | Shapes the audience and outputs |
| 1.3 | Who opens it | "Primarily by TRPA, but a goal in creating a standardized methodology is that other regional operators can also use it. We'll also be showing the results to elected officials." | Plain-language outputs; Excel export |
| 1.4 | What gets handed over | "A table or chart that is somewhat easy to read and/or explain" | Results tables, charts, Excel export |
| 1.5 | How it is answered today | "Every operator has a separate methodology and we've never looked at everything all together." | |
| 1.6 | Time horizon | "Fiscal year and five-year forecast are the most important." RTP horizon is "somewhat irrelevant." | FY 26-27 to FY 30-31 |
| 1.7 | What the consultants got wrong and right | "It's too complicated and they claimed that showing match was impossible because TTD uses a different methodology. I like how they started to display the revenue %s applied to different routes." | Revenue %s shares drive the allocation matrix |

## 2. Funding rules

| # | Question | Answer | In the model |
| --- | --- | --- | --- |
| 2.1 | What "optimize" means | Keep: no optimizer; flag problems and show trade-offs | Suggest allocation is a rules-based default, not an optimizer |
| 2.2 | Where match is tested | Keep: per grant, per recipient | **Not yet.** The engine still tests match per service. See `docs/Model Logic.md` |
| 2.3 | NDOT 5311 federal share | "50% non-federal. Let's go with that for now and we can change it later." | 50 percent |
| 2.4 | Other federal shares | "5307 operating funds require a 50% non-federal match. 5310 might require 20% non-federal match which is what would be used to pay for ADA paratransit." | 5307 at 50 percent; 5310 at 80 percent federal (held in the seed; confirm with FTA) |
| 2.5 | Limits versus preferences | "Wherever the notes say 'ideally,' is just a preference... let's do it and highlight where those instances happen." | "Ideally" conditions are warnings; Results reports the total used outside a preference |
| 2.6 | California funds matching on Nevada routes | "Yes they can, but there's a lot of political pressure from the California side not to do this. I would like to show what it looks like when we ONLY use TDA and SB125 in CA." | Preset: TDA and SB 125 stay in California |
| 2.7 | Toll credits | "Super limited... Maybe let's assume we don't have this option anymore." | No toll credits |
| 2.8 | Free-fare payments | "Any fares should be thought of as match." | Fare lines count as local match |
| 2.9 | Cost split on multi-jurisdiction routes | "Keep this assumption and we can be more specific later on." | Even split, labeled placeholder |
| 2.10 | Capital | "Let's start with operating dollars and worry about capital in a future iteration." | Operating only |
| 2.11 | Planning and administration funds | "Fair game. Most of TTD's planning and administration is paid out of their transit operations budget." | $232,235 local appropriation to TTD included |

## 3. Data

| Item | Answer | In the model |
| --- | --- | --- |
| Revenue miles by route, jurisdiction, state, and UZA | "We can get this" | Still open; placeholders in use |
| Federalized status of Lake Link, My Ride to Work, and vanpools | "Currently non-federalized, but let's run a scenario where Lake Link is federalized" | Non-federalized; preset: Lake Link federalized |
| Actual FY 26-27 FTA apportionments | "Use example for now" | EXAMPLE figures from FTA Allocation Split (26-27) |
| TART 5307: $1,653,136 or $2,660,000 | "Use TART's numbers. They get extra 5307 from PCTPA" | $2,660,000 from Table A2 G59 |
| 5310 and LCTOP schedule | "We switch off between TTD and Placer County each year" | Alternation projected through FY 30-31 |
| Lake Link partners, NTCA, Martis | "Let's assume their contributions remain steady" | Held at FY 25-26 amounts ($839,273) |
| TDVA: $65,000 or $120,000 | "Use the plan" | $120,000 |
| Route 30 rate: $68.70 or $147.80 | "Use the higher cost" | $147.80/VSH, about $517,300 |
| Funding after SB 125 and the Route 30 pilot end | "No defined replacement funding yet. Highlight this as a gap and a need" | Funding cliffs callout on Five-year outlook |
| South Tahoe Transit JPA | "Not an operator and our assumption is that they will not become an operator." | South shore funding stays with TTD |
| Private and non-federalized operators | "We don't have this data yet, but will work on it." | Still open |

## 4. Concept mockups

- 4.1: "I would use all of these concepts. I'd also like to see a few different scenarios. For example... TTD and Lake Link remain as separate operators with separate revenue streams and one scenario in which TTD absorbs Lake Link and all of its revenue streams." Applied as the preset "TTD absorbs Lake Link."
- 4.2 to 4.5: no answers.

## 5. Test question

- 5.1: "Where are the biggest gaps in funding?" Use this to test any new version. The Results tab findings and the Five-year outlook should answer it plainly.
