# Setting up a new Claude Project for this work

Use this to set up a claude.ai Project, or a Claude Code session, that can pick up the funding model. Everything it needs is in this folder.

## Files to add as Project knowledge

Add these from this folder. They are listed in priority order. The first five give a new session the full context.

1. `CLAUDE.md`
2. `docs/Project Context Handoff.md`
3. `docs/Domain Lead Answers 2026-10-23.md`
4. `docs/Model Logic.md`
5. `docs/Review Feedback 2026-10-27.md`
6. `docs/Overall Directive.md`
7. `pipeline/README.md`
8. `model/transit-funding-model.html`: the current page
9. `source-data/workbooks/Financial PlanG.xlsx` and `source-data/workbooks/Example Transit Financial Scenario Workbook.xlsx`
10. `source-data/fact-sheets/` (four PDFs)
11. Optional, as background: `docs/Rule Errors, Pitfalls, and Open Questions.md`, `docs/Funding App - Information Needed.md`, `source-data/workbooks/Funding Model V1G.xlsx`, and the SSTMA working model

The pipeline seed files (`pipeline/etl/seed/*.yaml`) and the template are code. Work on them in Claude Code with this folder open, not as Project knowledge.

## Custom instructions to paste

> This Project continues TRPA's regional transit funding model (RFP Task 4). Start from CLAUDE.md and the Project Context Handoff. TRPA's decisions are in Domain Lead Answers 2026-10-23. Treat them as settled unless the user says otherwise. The model page is built by a pipeline from the workbooks and seed files. Change data in the workbooks or seed and the page in the template, then rebuild. Never hand-edit the built page. Cite TRPA decisions as TRPA direction (Oct. 23, 2026), never a staff member by name. Write in plain language for leadership and elected officials: one idea per sentence, no em dashes, Oxford commas, and no filler. Tag confidence on key claims as [Certain], [Likely], or [Guessing]. Trace every figure to a workbook tab and cell.

## Working with Claude Code

Open this folder as the working directory. Claude Code reads `CLAUDE.md` automatically. The build needs ArcGIS Pro Python (`propy`) with PyYAML and openpyxl. Both ship with `arcgispro-py3`.

## What does not carry over

- **The original chats** from Oct. 20 to 27 are in Andy's claude.ai account. Their conclusions are in the handoff doc and the files above.
- **Three live artifacts** linked in the handoff doc are private to Andy's account until he shares them. Copies are in this folder: the Rule Errors and Questions docs in `docs/`, and the concept mockups in `mockups/`.
- **Browser state:** scenarios saved in someone's browser stay in that browser. Export to Excel to pass a scenario along. Import reloads it.
