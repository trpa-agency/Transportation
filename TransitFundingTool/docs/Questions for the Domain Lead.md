# Transit Funding Tool: Questions for the Domain Lead

Oct 21, 2026 · @Andy

## Purpose

The consultants' model answers questions nobody confirmed she is asking. This meeting starts from her decisions. Leave with the first question the tool must answer, who uses it, and the rules only she can set.

Parts 1 and 2 need her in the room. Part 3 can go to partners as a request list. Show Part 4 last. The mockups could steer her earlier answers.

## Part 1: What the tool is for

These answers set the scope. Ask them before showing anything.

1. What are the last three transit funding questions someone asked you that took more than an hour to answer? Who asked?
2. What decision should the tool support first? For example, annual budget allocation, RTP financial constraint, a case for a regional funding source, partner cost-share negotiation, or grant applications.
3. Who opens it, and how often? You alone, the four operators, partner jurisdictions, or committee and board members?
4. What do you hand to someone at the end? A table in a staff report, a chart for a slide, a single number in a grant application?
5. How do you answer these questions today? Which workbook and tab, and which steps are manual?
6. What time horizon matters: one fiscal year, the five-year plan, or the RTP horizon?
7. What did the consultants' tool get wrong? What did it get right?

## Part 2: Rules only she can set

Each answer changes the calculation. The last column is built if there is no answer yet.

| Decision | Why it changes the code | Default if unanswered |
| --- | --- | --- |
| What "optimize" means: most federal money drawn, least local share, least money left unused, or fair jurisdiction shares | Each is a different objective function. Some conflict. | No optimizer. The tool flags problems. |
| Where match is tested: per route, per grant, or per recipient per program | Per-route testing reports shortfalls that per-grant testing would not | Per grant, per recipient |
| Federal share by program and state (5307 operating 50 percent, ADA 80 percent, NDOT 5311 operating) | Revenue %s says 50 percent for NDOT 5311; partner notes say 40 percent match for operating | Revenue %s rates, flagged as unconfirmed |
| Which fact sheet conditions are legal limits and which are preferences (for example, "ideally used in CA") | Limits block an allocation; preferences only warn | Fact sheet "Restrictions" are limits; "Revenue Conditions" notes are preferences |
| Can California funds (TDA, SB 125) match federal funds on Nevada routes? Are toll credits available? | Changes how much federal money each route can draw | Yes to cross-state match per the Revenue %s note; no toll credits |
| Are North Shore free-fare payments fare replacement or local match? | Fares reduce net cost and are not match; local funds are match | Local match |
| Cost-share method for multi-jurisdiction routes: SSTMA average of miles, hours, stops, and ridership, or percent of miles per month | Drives every jurisdiction result and state-restricted fund | Even split, labeled as a placeholder |
| Is capital in scope? The capital plan needs about $7.3 million and draws match from the same local dollars | Capital match competes with operating match | Operating only |
| Are planning and administration funds in scope (for example, the $232,235 local appropriation to TTD)? | They are revenue with no route to apply to | Out of scope |

## Part 3: Data to confirm or request

Ask which items she already knows and who owns the rest. Most can go out as one request per partner.

| Item | Why it matters | Likely owner |
| --- | --- | --- |
| Revenue miles by route, split by jurisdiction, state, and inside or outside the Lake Tahoe UZA | Replaces the placeholder splits; decides 5307 versus 5311 eligibility on mixed routes | Each operator |
| Federalized status of Lake Link, My Ride to Work services, and vanpools | Non-federalized services cannot take FTA funds | SSTMA, TNT/TMA |
| Actual FY 26-27 FTA apportionments | The financial plan marks the FY 26-27 figures as "EXAMPLE" | TRPA |
| TART 5307 amount: $1,653,136 from the earned-share split or $2,660,000 in TART's own plan | A $1.0 million difference on one line | TRPA, Placer County |
| Five-year schedule for rotating funds (5310 and LCTOP alternate between TTD and TART) | Changes each agency's balance year to year | TTD, Placer County |
| FY 26-27 commitments from partners who gave about $839,000 in FY 25-26 and are at $0 now: Lake Link partners ($302,100), North Tahoe Community Alliance ($487,173), Martis Zones of Benefit ($50,000) | The largest swing in the near-term outlook | SSTMA, TNT/TMA, Placer County |
| Conflicting figures: TDVA $65,000 (fact sheet) or $120,000 (plan); Route 30 cost rate $68.70 or $147.80 per hour | Route-level results depend on them | TTD |
| Replacement funding after SB 125 (ends after FY 26-27) and the Route 30 pilot funds (end after FY 27-28) | Defines the five-year gap | TTD, TRPA |

The full list with priorities is in **Funding App - Information Needed.md** from the earlier review.

## Part 4: Reacting to the three concepts

The mockups show three narrow tools. Each answers one question. They use real FY 26-27 figures from the project files.

| Concept | Question it answers | Main view |
| --- | --- | --- |
| A. Funding source lookup | Can this source pay for this service, and what does it require? | Searchable list of sources with rules, match, and commitment |
| B. Route match check | Is this route fully funded, and is federal money within its share cap with enough match? | One route's funding stack, with pass or fail checks |
| C. Five-year scenario | What happens to each agency's balance if a source ends, a partner drops out, or a service is added? | Toggles on the left, balance by agency and year on the right |

Questions for her:

1. Which one would you open next week? For what?
2. What is missing that you would need before trusting it?
3. What would you remove?
4. Which numbers look wrong to you?
5. Who else would you show it to?

## What to leave with

- [ ] The one decision the first version must support
- [ ] Who the primary users are
- [ ] Her ranked pick of the three concepts, with what to add or cut
- [ ] An answer or an owner for each rule in Part 2
- [ ] An owner and a date for each data item in Part 3
- [ ] One real question she will use to test the first version
- [ ] A date for the next check-in
