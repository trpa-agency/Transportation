# Transit Funding Tool

TRPA regional transit funding model for RFP Task 4 (Funding and Implementation Strategy). Handoff package assembled October 23, 2026, and updated October 27, 2026.

Start with `CLAUDE.md`. It gives the reading order, the rules for changing the model, the decisions in force, and open items. `docs/Project Context Handoff.md` has the full history. To set up a new Claude Project, follow `docs/Claude Project Setup.md`.

## Folder layout

| Path | What it is |
| --- | --- |
| `CLAUDE.md` | Entry point for Claude and for people: reading order, working rules, decisions, open items |
| `docs/Project Context Handoff.md` | Full project context and work history |
| `docs/Domain Lead Answers 2026-10-23.md` | TRPA's Oct. 23 decisions, quoted, with how each is applied |
| `docs/Model Logic.md` | How the model page calculates, and known gaps |
| `docs/Review Feedback 2026-10-27.md` | Oct. 27 review feedback and what changed |
| `docs/Claude Project Setup.md` | Files and instructions for a new Claude Project |
| `docs/Overall Directive.md` | Kira's email and the RFP Task 4 text |
| `docs/Rule Errors, Pitfalls, and Open Questions.md` | October 19 review: 11 rule errors, 16 source data conflicts with cell references, 17 questions |
| `docs/Funding App - Information Needed.md` | October 20 gap list with owners and priorities |
| `docs/Questions for the Domain Lead.md` | October 21 meeting guide |
| `docs/Transit Funding Tool - Questions for Kira.docx` | Fill-in questionnaire for Kira, built from the meeting guide |
| `docs/Transit Funding Tool - Questions for Kira - Answered 10-23.docx` | Kira's answers (Oct. 23, 2026). Applied to the model page the same day; see the handoff doc's Open decisions. |
| `model/transit-funding-model.html` | Current model page, single file with data inlined. Built by `pipeline/`; do not edit by hand. Open in Chrome or Edge. |
| `model/archive/` | Earlier versions of the model page |
| `pipeline/` | Build pipeline: reads the workbooks and seed files, writes the model page. See its README. Rebuilt October 27, 2026. |
| `mockups/Transit Funding Tool Concepts.html` | Three concept mockups for discussion. Concept C toggles work. |
| `source-data/workbooks/` | Example Transit Financial Scenario Workbook, Financial PlanG, Funding Model V1G, SSTMA working model |
| `source-data/fact-sheets/` | Federal, State, and Local Funds FINAL fact sheets (Task 4a) |
| `funding-model/` | Earlier prototype app: engine, three front ends, SQLite and JSON seed data, rules doc, tests. See its own README. |

## Not in this folder

- **Live source workbooks.** The workbooks in `source-data/` are copies from October 19. The source of truth is the SharePoint folder "4. Funding Implementation Memo."
- **Live claude.ai items.** The claude.ai Project "Tahoe Transportation Funding Model" holds the same docs. The live doc and canvas artifacts are linked in the handoff.
