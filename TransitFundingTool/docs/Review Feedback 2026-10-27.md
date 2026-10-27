# Review feedback, October 27, 2026

Feedback on the model page from TRPA review, and how each item was handled. All items were applied on October 27, 2026.

## Overall

| Feedback | What changed |
| --- | --- |
| Show what is today, what is the future, what can be changed, and which results change. Put all editable inputs and assumptions on one page. | Tabs are grouped as Today, Inputs you can change, Results and future, and Reference. Every editable input is on Inputs and assumptions, except route shares, which stay on Allocation and rules. |
| Add an "Existing Funding Conditions" tab with the Overview charts, and make the Overview an overview of the tool. | New Existing funding conditions tab, fixed to the FY 26-27 source data. Overview is four short tiles and a scenario status line. |
| Change the color palette to Connecting Tahoe. | Palette from the TRPA "Connecting Tahoe: Strengthening Transportation Resilience" StoryMap theme: navy #0B1F41, blue #007DC3, green #6EBE44, orange #F16022, button blue #007CB9, and warm gray #BEBDB1. All colors sit in one token block. No official style guide was found. Swap the block if one turns up. |
| Export scenario should be a spreadsheet, not JSON. | Export to Excel writes a ten-sheet workbook. Import reads it back. |
| The scenario presets dropdown does not seem to work. | It did apply changes, but gave no sign of it. Presets are now checkboxes on Inputs and assumptions. Each shows its effect, can be undone, and shows a chip in the scenario bar. |
| Surpluses in one fiscal year should carry over to the next. | Each agency's surplus carries forward. Deficits do not. There is a switch and an opening balance for each agency. |
| Make font sizes larger. | Base size raised from 14 to 16 pixels. Small labels have a floor. Charts and tables were enlarged to match. |
| Number the source files and use superscripts instead of repeating file names. | Numbered list on Assumptions and notes. Superscript numbers link to it throughout. |
| Do not cite Kira as a source; use TRPA. | Every citation reads TRPA (source 9: TRPA staff direction, Oct. 23, 2026). |
| TTD shows a surplus that does not seem right. | $1,137,363 of TTD's FY 26-27 federal money is above the federal share cap and has no eligible operating use. It is now left out of the balance. TTD's FY 26-27 surplus fell from $1,580,018 to $442,655. The rest depends on $2.42 million in one-time funds (5307 carryover, SB 125), and TTD is in deficit from FY 27-28. The consultants' Table A1 itself shows a TTD surplus of $935,638 for FY 26-27. |

## Overview tab

| Feedback | What changed |
| --- | --- |
| Remove the number widgets. | Removed. |
| Too much text. | Cut to two sentences and four tiles. |
| Remove mentions of Task 4a, 4b, and 4c, and the "Every number is traced..." sentence. | Removed everywhere in the page. |

## Allocation and rules

| Feedback | What changed |
| --- | --- |
| The "by service hours / by cost / by ridership" dropdown does not seem to filter. | It only worked with a selected row and a second button. Now: click a source row, pick a basis, and the split applies at once. A message lists the new shares, and the row flashes. |

## Agreements and risk

| Feedback | What changed |
| --- | --- |
| Remove the bullet starting "Multi-jurisdiction services without a cost-share formula." | Removed. |
| Use superscript numbers for the agreements list instead of naming Financial PlanG and its rows. | Each bullet ends with superscript source numbers only. The numbered list is on Assumptions and notes. |

## Flagged during the work, not yet changed

- **TNT/TMA revenue is 2.3 times its cost** ($2.43 million against $1.04 million in FY 26-27). The costs tab likely understates NLTE and Park & Ride costs (data note 7). This needs TNT/TMA's FY 26-27 budget costs.
- **Possible double count in Table A1.** TTD's base cost uses 35,680 VSH. That is the costs tab TTD total plus Route 30's 3,500 VSH. Route 30 is also added as its own $517,288 line. [Guessing] Confirm with TTD or the consultant.
- **Match test level.** TRPA chose per grant, per recipient. The engine still tests per service (see `Model Logic.md`).
