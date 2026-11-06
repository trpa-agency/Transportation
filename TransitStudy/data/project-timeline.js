/* Project timeline for the Home tab, from Project_Timeline.xlsx (Nov. 2026).
   start and end are YYYY-MM. An item with no end covers one month.
   The page draws one column per month from `from` to `to` and marks today's date. */

window.PROJECT_TIMELINE = {
  from: "2026-02",
  to: "2027-04",
  lanes: [
    {
      name: "Tahoe Transit Study",
      kind: "study",
      items: [
        { label: "Existing Conditions Memo", start: "2026-02" },
        { label: "Draft Governance Framework Memo", start: "2026-05" },
        { label: "Draft Service Alternatives Memo", start: "2026-07" },
        { label: "Draft Funding and Implementation Strategies Memo", start: "2026-09" },
        { label: "Draft Tahoe Transit Study", start: "2026-10" },
        { label: "Final Tahoe Transit Study (expected)", start: "2027-03" }
      ]
    },
    {
      name: "Stakeholder engagement",
      kind: "stakeholder",
      items: [
        { label: "Transit Working Group review", start: "2026-02", end: "2026-09" },
        { label: "Stakeholder review and meetings", start: "2027-01", end: "2027-03" }
      ]
    },
    {
      name: "Public outreach",
      kind: "public",
      items: [
        { label: "Public survey", start: "2026-11", end: "2027-01" }
      ]
    },
    {
      name: "Board meeting updates",
      kind: "board",
      items: [
        { label: "TRPA Board and Douglas County BOCC", start: "2026-02" },
        { label: "TTD Board", start: "2026-03" },
        { label: "South Tahoe Transit JPA", start: "2026-04" },
        { label: "South Tahoe Transit JPA", start: "2026-07" },
        { label: "TTD Board and SSTMA Board", start: "2026-08" },
        { label: "South Tahoe Transit JPA", start: "2026-10" },
        { label: "TRPA Board", start: "2026-11" },
        { label: "TTD Board and SSTMA Board", start: "2026-12" },
        { label: "TNT/TMA and Douglas County BOCC", start: "2027-01" },
        { label: "Final endorsements", start: "2027-03", end: "2027-04" }
      ]
    }
  ]
};
