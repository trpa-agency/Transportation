/* Responsibility matrix data for the Draft recommendations tab.
   Service and governance: Tahoe Transit Study Executive Summary, Table 3 (Service Strategies
   Implementation Timeline) and Table 4 (Governance Alternatives Implementation Timeline).
   Wording and agencies follow those tables, with typos and number style fixed.
   Funding: draft Funding Memo, v2 (unchanged from the earlier explorer).
   lead and partners are keys into AG. term is the table's timeframe column. */

window.REC_MATRIX = {
  source: "Sources: Tahoe Transit Study Executive Summary, Tables 3 and 4 (service and governance), and Tahoe Transit Study Funding Memo, Draft v2 (funding).",

  groups: ["Transit operators", "Regional and planning", "Local jurisdictions", "State and federal", "Private, nonprofit, and other", "General groups"],

  AG: {
    TTD:    { n: "Tahoe Transportation District (TTD)", s: "TTD", g: "Transit operators" },
    PC:     { n: "Placer County (operates TART)", s: "Placer County", g: "Transit operators" },
    EDT:    { n: "El Dorado Transit", s: "El Dorado Transit", g: "Transit operators" },
    TRPA:   { n: "Tahoe Regional Planning Agency (TRPA)", s: "TRPA", g: "Regional and planning" },
    SSTMA:  { n: "South Shore Transportation Management Association (SSTMA)", s: "SSTMA", g: "Regional and planning" },
    TNT:    { n: "Truckee North Tahoe Transportation Management Association (TNT/TMA)", s: "TNT/TMA", g: "Regional and planning" },
    STTJPA: { n: "South Tahoe Transit Joint Powers Authority (STTJPA)", s: "STTJPA", g: "Regional and planning" },
    RTCW:   { n: "Regional Transportation Commission of Washoe County (Washoe RTC)", s: "Washoe RTC", g: "Regional and planning" },
    CAMPO:  { n: "Carson Area Metropolitan Planning Organization (CAMPO)", s: "CAMPO", g: "Regional and planning" },
    CSLT:   { n: "City of South Lake Tahoe", s: "City of South Lake Tahoe", g: "Local jurisdictions" },
    EDC:    { n: "El Dorado County", s: "El Dorado County", g: "Local jurisdictions" },
    DC:     { n: "Douglas County", s: "Douglas County", g: "Local jurisdictions" },
    WC:     { n: "Washoe County", s: "Washoe County", g: "Local jurisdictions" },
    CC:     { n: "Carson City", s: "Carson City", g: "Local jurisdictions" },
    TRK:    { n: "Town of Truckee", s: "Town of Truckee", g: "Local jurisdictions" },
    NC:     { n: "Nevada County", s: "Nevada County", g: "Local jurisdictions" },
    NDOT:   { n: "Nevada Department of Transportation (NDOT)", s: "NDOT", g: "State and federal" },
    CT:     { n: "Caltrans", s: "Caltrans", g: "State and federal" },
    NVSP:   { n: "Nevada State Parks", s: "Nevada State Parks", g: "State and federal" },
    CASP:   { n: "California State Parks", s: "CA State Parks", g: "State and federal" },
    USFS:   { n: "U.S. Forest Service (USFS)", s: "USFS", g: "State and federal" },
    LTCC:   { n: "Lake Tahoe Community College (LTCC)", s: "LTCC", g: "Private, nonprofit, and other" },
    IVCBVB: { n: "Incline Village Crystal Bay Visitors Bureau (IVCBVB)", s: "IVCBVB", g: "Private, nonprofit, and other" },
    HEAV:   { n: "Heavenly", s: "Heavenly", g: "Private, nonprofit, and other" },
    TBEC:   { n: "Tahoe Blue Event Center", s: "Tahoe Blue Event Center", g: "Private, nonprofit, and other" },
    LJ:     { n: "Local jurisdictions", s: "Local jurisdictions", g: "General groups" },
    TMAS:   { n: "Transportation management associations (TMAs)", s: "TMAs", g: "General groups" },
    RES:    { n: "Resorts", s: "Resorts", g: "General groups" },
    EMP:    { n: "Employers", s: "Employers", g: "General groups" }
  },

  recs: [
    /* ---------- Service: Executive Summary Table 3 ---------- */
    { type: "service", term: "Short", title: "Discontinue LTCC deviation on TTD Route 50 during the summer season and weekends", lead: ["TTD"], partners: ["LTCC", "SSTMA"] },
    { type: "service", term: "Short", title: "Increase vanpools between Reno and Truckee/North Lake Tahoe", lead: ["TNT"], partners: ["TRK", "RTCW", "EMP", "RES"] },
    { type: "service", term: "Medium", title: "Discontinue TTD's operation of Route 19X and reimplement US 50 service between South Shore and Carson City", lead: ["TTD"], partners: ["NDOT", "CC", "DC", "CAMPO"] },
    { type: "service", term: "Medium", title: "Continue summer service from South Lake Y to Sugar Pine (Emerald Bay Shuttle)", lead: ["TTD"], partners: ["EDC", "CSLT", "USFS", "CASP", "PC", "CT", "TRPA"] },
    { type: "service", term: "Medium", title: "Expand microtransit zone to Meyers commingled with paratransit", lead: ["TTD", "SSTMA"], partners: ["EDC", "STTJPA", "TRPA"] },
    { type: "service", term: "Medium to long", title: "Reimplement TART Connect service in Incline Village", lead: ["PC"], partners: ["WC", "IVCBVB", "TRPA"] },
    { type: "service", term: "Long", title: "Expand seasonal service of Route 28 to Spooner Mobility Hub", lead: ["TTD"], partners: ["NDOT", "NVSP"] },
    { type: "service", term: "Long", title: "Increase frequency on TART fixed routes to 30 minutes during peak summer and winter", lead: ["PC"], partners: ["RES", "TNT"] },
    { type: "service", term: "Long", title: "Provide Placer TART evening service (6 to 8 p.m.)", lead: ["PC"], partners: ["RES", "TNT"] },

    /* ---------- Governance: Executive Summary Table 4 ---------- */
    { type: "governance", term: "Short", title: "Maintain existing North Shore transit governance structure and formalize through agreements", lead: ["PC"], partners: ["WC", "RTCW", "TRK", "NC", "RES", "TNT"] },
    { type: "governance", term: "Short", title: "Establish a South Shore Transit Advisory Committee within TTD", lead: ["TTD"], partners: ["CSLT", "EDC", "DC", "SSTMA"] },
    { type: "governance", term: "Short", title: "Define the future role of STTJPA", lead: ["STTJPA"], partners: ["EDC", "CSLT"] },
    { type: "governance", term: "Short", title: "Establish a Tahoe Basin Transit Network Manager", lead: ["TTD"], partners: ["TRPA", "PC", "LJ", "TMAS"] },
    { type: "governance", term: "Short to medium", title: "Establish cost-sharing agreements for shared transit facilities", lead: ["TTD"], partners: ["HEAV", "CSLT", "SSTMA"] },
    { type: "governance", term: "Short to medium", title: "Establish a unified Tahoe regional transit brand", lead: ["SSTMA", "TNT"], partners: ["TTD", "PC", "TRPA", "RES", "EMP"] },
    { type: "governance", term: "Medium", title: "Establish a unified regional transit trip planning platform", lead: ["TTD"], partners: ["TMAS", "PC", "TRPA"] },
    { type: "governance", term: "Medium", title: "Ensure sustainability of North Lake Tahoe Express", lead: ["TNT"], partners: ["LJ", "RES", "EMP"] },
    { type: "governance", term: "Medium", title: "Transfer ownership of the TTD operating and maintenance facility to TTD", lead: ["CSLT"], partners: ["TTD", "TRPA"] },
    { type: "governance", term: "Medium to long", title: "Formalize regional transit service and funding agreements", lead: ["TTD"], partners: ["LJ", "TMAS"] },
    { type: "governance", term: "Medium to long", title: "Transition Lake Link operations from SSTMA to TTD", lead: ["TTD", "SSTMA"], partners: ["TRPA", "DC", "CSLT", "TBEC"] },
    { type: "governance", term: "Medium to long", title: "Define future role of SSTMA", lead: ["SSTMA"], partners: ["EMP", "RES", "LJ"] },
    { type: "governance", term: "Long", title: "Develop or secure workforce housing", lead: ["TTD", "PC"], partners: ["TRPA", "LJ"] },

    /* ---------- Funding: draft Funding Memo v2 (unchanged) ---------- */
    { type: "funding", term: "", title: "Pursue a Transit Business Improvement District in South Lake Tahoe", lead: ["SSTMA", "TTD"], partners: ["CSLT", "STTJPA"] },
    { type: "funding", term: "", title: "Increase transient occupancy tax (TOT) contributions to South Shore transit", lead: ["SSTMA", "TTD"], partners: ["CSLT", "EDC", "DC"] },
    { type: "funding", term: "", title: "Consider regional sales tax initiative", lead: ["TTD"], partners: [] },
    { type: "funding", term: "", title: "Establish sublease agreements between TTD and facility users", lead: ["TTD"], partners: ["HEAV", "EDT"] },
    { type: "funding", term: "", title: "Pursue funding agreement with El Dorado County", lead: ["TTD"], partners: ["SSTMA", "EDC", "STTJPA"] },
    { type: "funding", term: "", title: "Implement transit zone of benefit programs in additional jurisdictions", lead: ["EDC", "DC", "WC"], partners: ["TRPA"] },  // leads from the study text: El Dorado County could codify one; Douglas and Washoe need legal research
    { type: "funding", term: "", title: "Continue escalating funding agreements with local jurisdictions and private entities for Lake Link", lead: ["SSTMA"], partners: ["DC", "CSLT"] }
  ]
};
