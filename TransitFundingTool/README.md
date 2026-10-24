# Transit Funding Tool

TRPA regional transit funding model for RFP Task 4 (Funding and Implementation Strategy). Handoff package assembled October 23, 2026.

Start with `docs/Project Context Handoff.md`. It covers the purpose, work history, status against the RFP, open decisions, and next steps.

## Folder layout

| Path | What it is |
| --- | --- |
| `docs/Project Context Handoff.md` | Full project context. Read first. |
| `docs/Overall Directive.md` | Kira's email and the RFP Task 4 text |
| `docs/Rule Errors, Pitfalls, and Open Questions.md` | October 19 review: 11 rule errors, 16 source data conflicts with cell references, 17 questions |
| `docs/Funding App - Information Needed.md` | October 20 gap list with owners and priorities |
| `docs/Questions for the Domain Lead.md` | October 21 meeting guide |
| `docs/Transit Funding Tool - Questions for Kira.docx` | Fill-in questionnaire for Kira, built from the meeting guide |
| `docs/Transit Funding Tool - Questions for Kira - Answered 10-23.docx` | Kira's answers (Oct. 23, 2026). Applied to the model page the same day; see the handoff doc's Open decisions. |
| `model/transit-funding-model.html` | Current model page, single file with data inlined. Open in Chrome or Edge. |
| `mockups/Transit Funding Tool Concepts.html` | Three concept mockups for discussion. Concept C toggles work. |
| `source-data/workbooks/` | Example Transit Financial Scenario Workbook, Financial PlanG, Funding Model V1G, SSTMA working model |
| `source-data/fact-sheets/` | Federal, State, and Local Funds FINAL fact sheets (Task 4a) |
| `funding-model/` | Earlier prototype app: engine, three front ends, SQLite and JSON seed data, rules doc, tests. See its own README. |

## Not in this folder

- **ETL pipeline.** The October 22 build pipeline (`etl/build_model_data.py`, `etl/config.yaml`, `etl/seed/*.yaml`, `build_data.bat`) produces `model/transit-funding-model.html`. It was delivered as `transit-funding-model.zip`. Add it here as `pipeline/` to make the model rebuildable. **Note:** Kira's October 23 answers were applied directly to the model HTML because the pipeline is not here; mirror them in the seed files before the next rebuild, or they will be overwritten.
- **Live source workbooks.** The workbooks in `source-data/` are copies from October 19. The source of truth is the SharePoint folder "4. Funding Implementation Memo."
- **Live claude.ai items.** The claude.ai Project "Tahoe Transportation Funding Model" holds the same docs. The live doc and canvas artifacts are linked in the handoff.
