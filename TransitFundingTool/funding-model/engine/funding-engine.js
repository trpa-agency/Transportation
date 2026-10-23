/* Lake Tahoe Region transit funding model: calculation engine.
 *
 * Pure functions with no DOM access, shared by every front end. Load in a page with
 *   <script src="engine/funding-engine.js"></script>   → window.FundingEngine
 * or in Node with require('./engine/funding-engine.js').
 *
 * Every calculation and check cites a rule ID from RULES (also listed in RULES.md).
 * Money is US dollars. Shares and rates are fractions. Fiscal years are indexes (0 = FY 26-27).
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.FundingEngine = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const VERSION = '2.0.0';
  const LEVELS = ['federal', 'state', 'local', 'private', 'fare', 'other'];
  const RISKY = new Set(['onetime', 'none', 'proposed']);
  const TOL = 1;              // dollars: differences below this are rounding
  const SCALE = 1e-6;         // the optimizer works in millions of dollars

  /* ── Rule registry ─────────────────────────────────────────────────────────
     kind: calc (a calculation), required (makes a use ineligible), preference (raises a warning),
     check (validation applied to any allocation), optimizer (how the rules-based allocation works),
     result (how outputs are derived). severity applies to checks and eligibility rules. */
  const RULES = [
    { id: 'COST-01', kind: 'calc', title: 'Base annual cost', text: 'Annual operating cost in the base year = vehicle service hours (VSH) × cost per VSH. The operator\'s fully allocated rate applies unless the service has its own rate.', source: 'Scenario workbook › costs K = H × J; lookup W31:W36' },
    { id: 'COST-02', kind: 'calc', title: 'Entered annual cost', text: 'An annual cost entered for a service replaces VSH × rate for that service (used for vanpools).', source: 'TNTTMA $ K43' },
    { id: 'COST-03', kind: 'calc', title: 'Cost escalation', text: 'Cost in a later year = base-year cost × (1 + the operator\'s annual escalator) ^ years from the base year.', source: 'VRH Rates notes, column L' },
    { id: 'COST-04', kind: 'calc', title: 'Scheduled costs', text: 'A cost scheduled for a year (service plan elements) replaces the calculation for that year. A plan element that adjusts another service adds its scheduled cost, which may be negative, to that service.', source: 'Financial PlanG › T2-4 rows 29–33, T5-7 rows 36–37' },
    { id: 'COST-05', kind: 'calc', title: 'Inactive and excluded services', text: 'A service costs nothing in a year it is inactive (Route 30 after the FY 27-28 pilot) or when it is excluded from the scenario.', source: 'T2-4 G20:K20' },
    { id: 'COST-06', kind: 'calc', title: 'Scenario cost multiplier', text: 'A scenario may scale costs for all services or one service; scaling applies after COST-01 to COST-05.', source: 'Model setting' },
    { id: 'REV-01', kind: 'calc', title: 'Base-year amount', text: 'A source\'s base-year amount is its FY 26-27 budget amount, or for FTA 5307 formula lines the sub-allocation result (REV-02). A scenario may replace the base amount.', source: 'Per Route Model columns D–G; T2-4 Table A1; T5-7 Table A2; TNTTMA $' },
    { id: 'REV-02', kind: 'calc', title: 'FTA 5307 sub-allocation', text: 'Operating amount = UZA apportionment × earned share × operations share (75%). Earned share = weighted average of the agency\'s shares of urban revenue miles, population, and ridership (equal weights).', source: 'FTA Allocation Split (26-27) F28:G35' },
    { id: 'REV-03', kind: 'calc', title: 'Projection', text: 'In each later year, a year value entered for the source replaces the rule; otherwise amount = prior year × (1 + growth rate).', source: 'T2-4 Table A1 notes 1–8; T5-7 Table A2 notes' },
    { id: 'REV-04', kind: 'calc', title: 'Annual cap', text: 'Each year\'s amount is limited to the source\'s annual cap (Tahoe Blue mitigation fee, $750,000).', source: 'T2-4 H88' },
    { id: 'REV-05', kind: 'calc', title: 'End year', text: 'A source provides nothing after its last year (SB 125, 5307 carryover, Emerald Bay pilot funds, NLTE reserve).', source: 'T2-4 Table A1; T5-7 Table 7' },
    { id: 'REV-06', kind: 'calc', title: 'Excluded sources', text: 'Disabled sources and capital-only sources (FTA 5339) provide no operating revenue.', source: 'Federal Funds fact sheet' },
    { id: 'REV-07', kind: 'calc', title: 'Match-only credits', text: 'A match-only credit (electrification credits) can count toward non-federal match but is not revenue and pays no cost.', source: 'Revenue %s B16:C16' },
    { id: 'REV-08', kind: 'calc', title: 'Scenario funding changes', text: 'A scenario may multiply amounts by funding level, receiving agency, or source, and may add dollars to a source in the year evaluated. Changes apply after REV-01 to REV-05.', source: 'Model setting' },
    { id: 'ELIG-01', kind: 'required', severity: 'error', title: 'Service restriction', text: 'A source restricted to listed services may be applied only to those services.', source: 'Fact sheet restrictions; Revenue %s column B' },
    { id: 'ELIG-02', kind: 'required', severity: 'error', title: 'Operating agency restriction', text: 'A source restricted to an agency\'s operations may be applied only to that agency\'s services.', source: 'Local Funds 1 fact sheet (North Shore partners)' },
    { id: 'ELIG-03', kind: 'required', severity: 'error', title: 'Urban or rural restriction', text: 'Urbanized-area funds (FTA 5307) need an urban or mixed service; rural funds (FTA 5311) need a rural or mixed service.', source: 'Federal Funds fact sheet; Revenue %s B6:B7' },
    { id: 'ELIG-04', kind: 'required', severity: 'error', title: 'Service type restriction', text: 'A source restricted to a service type (FTA 5310: ADA paratransit) may be applied only to that type.', source: 'Federal Funds fact sheet; Revenue %s B8:B9' },
    { id: 'ELIG-05', kind: 'required', severity: 'error', title: 'State restriction', text: 'A state-restricted source can fund only the share of a service in that state, taken from its jurisdiction shares. A service with no share in the state is ineligible; a partly eligible service is capped at that share × cost.', source: 'Fact sheets (LCTOP, FTA 5311, Nevada State)' },
    { id: 'ELIG-06', kind: 'required', severity: 'error', title: 'Jurisdiction restriction', text: 'A jurisdiction-restricted source can fund at most that jurisdiction\'s share × the service cost.', source: 'Local Funds 2 fact sheet (Douglas County, City of South Lake Tahoe)' },
    { id: 'ELIG-07', kind: 'required', severity: 'error', title: 'Federalized services only', text: 'Federal funds may be applied only to services marked federalized; private or non-federalized operators are excluded.', source: 'RFP Task 4b (non-federalized operators)' },
    { id: 'PREF-01', kind: 'preference', severity: 'warning', title: 'Intended services', text: 'A source intended for listed services raises a warning when applied elsewhere.', source: 'Local Funds 1 fact sheet (TDVA, Route 51)' },
    { id: 'PREF-02', kind: 'preference', severity: 'warning', title: 'Preferred state', text: 'A source "ideally used" in one state raises a warning on a service with no share in that state.', source: 'Revenue %s column B ("ideally used in CA/NV")' },
    { id: 'PREF-03', kind: 'preference', severity: 'warning', title: 'Preferred jurisdiction', text: 'A source "ideally used" in one jurisdiction raises a warning on a service with no share there.', source: 'Revenue %s B28, B34, B35' },
    { id: 'PREF-04', kind: 'preference', severity: 'warning', title: 'Receiving agency', text: 'One agency\'s funds applied to another agency\'s service raise a warning: the use needs an interagency agreement.', source: 'RFP Task 4c' },
    { id: 'FED-01', kind: 'calc', title: 'Net cost', text: 'Net cost of a service = cost − fares applied to it. Federal shares apply to net cost.', source: 'FTA operating assistance practice; Revenue %s AE3' },
    { id: 'FED-02', kind: 'check', severity: 'error', title: 'Federal share cap per source', text: 'Each federal source on a service ≤ its federal share cap × (net cost + match-only credits applied to the service). Credits stand in for cash match the way toll credits do, so they widen the base. ADA paratransit uses the source\'s ADA cap when it has one (FTA 5307: 80%).', source: 'Revenue %s columns C, AE; D57 (toll credits)' },
    { id: 'FED-03', kind: 'check', severity: 'error', title: 'Combined federal share cap', text: 'When two or more federal sources fund a service, their total ≤ the highest cap among them × (net cost + match-only credits applied).', source: 'Revenue %s columns C, AE' },
    { id: 'MATCH-01', kind: 'calc', title: 'Match required', text: 'Non-federal match required on a service = Σ over federal sources of amount × (1 − cap) ÷ cap (50% cap → $1 of match per federal $1; 80% → $0.25; 88.53% → $0.1296).', source: 'Revenue %s column C' },
    { id: 'MATCH-02', kind: 'calc', title: 'Match available', text: 'Match available = state, local, private, and other funds applied to the service that count as match, plus match-only credits. Federal funds and fares never count as match; each dollar matches only once.', source: 'Revenue %s B10, C16' },
    { id: 'MATCH-03', kind: 'check', severity: 'error', title: 'Match met', text: 'Match available ≥ match required on every service.', source: 'Revenue %s column C' },
    { id: 'ALLOC-01', kind: 'calc', title: 'Fixed shares', text: 'In a fixed-shares allocation, dollars to a service = amount × share. Shares to a service that is inactive that year stay unallocated.', source: 'Revenue %s × Per Route Model' },
    { id: 'ALLOC-02', kind: 'calc', title: 'Automatic split', text: 'An automatic split divides a source among its target services (or, with no targets, among services that pass every required and preferred rule) in proportion to the chosen basis × eligible portion. Basis: service hours by default.', source: 'Revenue %s (VSH-based shares)' },
    { id: 'ALLOC-03', kind: 'check', severity: 'error', title: 'Shares within 100 percent', text: 'A source\'s shares may not total more than 100 percent.', source: 'Model check' },
    { id: 'ALLOC-04', kind: 'check', severity: 'info', title: 'Unallocated funds', text: 'Any part of a source not applied to a service stays with the receiving agency and is reported.', source: 'Model check' },
    { id: 'SVC-01', kind: 'check', severity: 'info', title: 'Funding gap', text: 'Gap = cost − funds applied, when positive.', source: 'Model check' },
    { id: 'SVC-02', kind: 'check', severity: 'warning', title: 'Funds above cost', text: 'Funds applied above a service\'s cost cannot be spent on it; the excess is reported.', source: 'Model check' },
    { id: 'OPT-01', kind: 'optimizer', title: 'Objective', text: 'The rules-based allocation maximizes funded service: the sum over services of funds applied, never above cost.', source: 'Model method' },
    { id: 'OPT-02', kind: 'optimizer', title: 'Constraints', text: 'Each source applies no more than its amount; only uses that pass every required rule (ELIG-01 to ELIG-07) are allowed, within eligible portions; no service receives more than its cost; match is met on every service (MATCH-03). With no over-funding and match met, the federal caps (FED-02, FED-03) hold automatically.', source: 'Model method' },
    { id: 'OPT-03', kind: 'optimizer', title: 'Funds stay with the receiving agency', text: 'By default a source is applied only to its receiving agency\'s services. With interagency transfers allowed, it may fund other agencies\' services at a small penalty, each flagged under PREF-04.', source: 'Model setting' },
    { id: 'OPT-04', kind: 'optimizer', title: 'Preferences', text: 'Uses that break a preference (PREF-01 to PREF-03) are allowed but avoided (OPT-06), so they occur only when they fund service, or spread a shortfall, that the preferred uses cannot. In strict mode they are not allowed.', source: 'Model setting' },
    { id: 'OPT-05', kind: 'optimizer', title: 'Shortfalls spread evenly', text: 'When funds cannot cover every service, the engine keeps total funded service at its maximum and then raises the lowest share of cost funded on any service as high as the rules allow, so gaps are spread rather than concentrated. This setting can be turned off.', source: 'Model method (lexicographic, max-min coverage)' },
    { id: 'OPT-06', kind: 'optimizer', title: 'Tie-breaks', text: 'Among allocations that fund the same service equally evenly, the engine applies fares first, then federal funds, then funds earmarked to specific services, then time-limited funds, and holds back flexible recurring funds; uses that break a preference are avoided. Tie-breaks never reduce funded service or evenness.', source: 'Model method (lexicographic optimization)' },
    { id: 'OPT-07', kind: 'optimizer', title: 'Proof of optimality', text: 'Each solution is checked for primal feasibility, dual feasibility, and zero duality gap on funded service. A solution that fails is reported, not used silently.', source: 'Model method' },
    { id: 'OPT-08', kind: 'optimizer', title: 'Why funds go unused', text: 'An unused amount is explained as: no eligible service, eligible services already fully funded, not enough non-federal match, or an eligible-portion cap.', source: 'Model method' },
    { id: 'OPT-09', kind: 'optimizer', title: 'Each year solved separately', text: 'The rules-based allocation is solved independently for each fiscal year.', source: 'Model method' },
    { id: 'RES-01', kind: 'result', title: 'Funded service', text: 'Funded service = Σ over services of the lesser of funds applied and cost.', source: 'Model output' },
    { id: 'RES-02', kind: 'result', title: 'Agency balance', text: 'Agency balance = revenue the agency receives − cost of the services it operates.', source: 'T1 Summary Table structure' },
    { id: 'RES-03', kind: 'result', title: 'Jurisdiction attribution', text: 'Each jurisdiction is attributed its share of each service\'s cost and of the non-local funds applied; local share = attributed cost − attributed non-local funds; contributions = local sources tagged with that contributing jurisdiction.', source: 'SSTMA cost-share method (rt 19, 22, 28 Cost Share)' },
    { id: 'RES-04', kind: 'result', title: 'Time-limited share', text: 'Time-limited share = funds applied from one-time, uncommitted, or proposed sources ÷ all funds applied.', source: 'T2-4 notes 5, 8' },
    { id: 'SENS-01', kind: 'result', title: 'Value of more funding', text: 'Marginal value of a source = change in funded service when the source gets a set amount more (default $100,000), re-solving the rules-based allocation. The dual price gives the same measure for the first dollar.', source: 'Model method' },
    { id: 'SENS-02', kind: 'result', title: 'Cost of losing a source', text: 'Loss impact = change in funded service when the source is removed, re-solving the rules-based allocation; the services that lose funding are listed.', source: 'Model method' }
  ];
  const RULE = Object.fromEntries(RULES.map(r => [r.id, r]));

  /* ── Loading and indexing ─────────────────────────────────────────────── */
  const bool = v => v === true || v === 1 || v === '1';
  function load(seed) {
    const t = seed.tables;
    const byKey = (rows, key) => { const o = {}; for (const r of rows) (o[r[key]] = o[r[key]] || []).push(r); return o; };
    const sj = byKey(t.service_jurisdiction, 'service_id'), sy = byKey(t.service_year, 'service_id');
    const ly = byKey(t.funding_line_year, 'line_id'), er = byKey(t.eligibility_rule, 'line_id');
    const prog = Object.fromEntries(t.funding_program.map(p => [p.program_id, p]));
    const m = {
      meta: Object.assign({}, seed.meta),
      years: t.fiscal_year.slice().sort((a, b) => a.fy_index - b.fy_index).map(r => r.label),
      documents: t.source_document.map(r => Object.assign({}, r)),
      agencies: t.agency.map(r => Object.assign({}, r)),
      jurisdictions: t.jurisdiction.map(r => Object.assign({}, r)),
      operators: t.operator.map(r => Object.assign({}, r)),
      programs: t.funding_program.map(r => Object.assign({}, r)),
      services: t.service.map(r => {
        const s = Object.assign({}, r, { federalized: bool(r.federalized), is_plan_element: bool(r.is_plan_element), included: bool(r.included) });
        s.juris = {}; s.juris_placeholder = false;
        for (const x of (sj[r.service_id] || [])) { s.juris[x.jurisdiction_id] = x.share; if (bool(x.is_placeholder)) s.juris_placeholder = true; }
        s.years = {};
        for (const x of (sy[r.service_id] || [])) s.years[x.fy_index] = { active: bool(x.active), scheduled_cost: x.scheduled_cost };
        return s;
      }),
      lines: t.funding_line.map(r => {
        const p = prog[r.program_id] || {};
        const l = Object.assign({}, r, { enabled: bool(r.enabled), match_only: bool(r.match_only), counts_as_match: bool(r.counts_as_match), level: p.level, program_name: p.name });
        l.years = {};
        for (const x of (ly[r.line_id] || [])) l.years[x.fy_index] = x.amount;
        l.required = {}; l.preferred = {};
        for (const x of (er[r.line_id] || [])) { const g = x.strength === 'required' ? l.required : l.preferred; (g[x.rule_type] = g[x.rule_type] || []).push(x.value); }
        return l;
      }),
      fta: Object.assign({}, t.fta_suballocation.find(r => r.fy_index === 0) || t.fta_suballocation[0]),
      ftaFactors: Object.fromEntries(t.fta_earned_share_factor.map(r => [r.agency_id, Object.assign({}, r)])),
      draft: {},
      citations: {},
      agreements: t.agreement.map(r => Object.assign({}, r)),
      dataIssues: t.data_issue.map(r => Object.assign({}, r))
    };
    const scen = (t.allocation_scenario.find(r => r.method === 'fixed_shares') || {}).scenario_id;
    for (const r of t.allocation_rule.filter(x => x.scenario_id === scen)) m.draft[r.line_id] = { method: r.method, basis: r.auto_basis || 'vsh', shares: {}, targets: [] };
    for (const r of t.allocation_share.filter(x => x.scenario_id === scen)) (m.draft[r.line_id] = m.draft[r.line_id] || { method: 'shares', basis: 'vsh', shares: {}, targets: [] }).shares[r.service_id] = r.share;
    for (const r of t.allocation_target.filter(x => x.scenario_id === scen)) if (m.draft[r.line_id]) m.draft[r.line_id].targets.push(r.service_id);
    for (const c of t.citation) { const k = c.entity_type + '|' + c.entity_id; (m.citations[k] = m.citations[k] || []).push({ field: c.field, document_id: c.document_id, locator: c.locator }); }
    return m;
  }

  // Inverse of load: normalized tables matching schema.sql (for export and database loading)
  function toSeed(m) {
    const T = { source_document: m.documents, fiscal_year: m.years.map((label, i) => ({ fy_index: i, label })), agency: m.agencies, jurisdiction: m.jurisdictions, operator: m.operators,
      service: [], service_year: [], service_jurisdiction: [], funding_program: m.programs, funding_line: [], funding_line_year: [], eligibility_rule: [],
      fta_suballocation: [Object.assign({}, m.fta, { fy_index: 0 })], fta_earned_share_factor: Object.values(m.ftaFactors),
      allocation_scenario: [{ scenario_id: 'draft', name: 'Fixed shares', method: 'fixed_shares', description: 'Exported from the model' }, { scenario_id: 'optimized', name: 'Rules-based optimized allocation', method: 'optimized', description: 'Computed by the engine' }],
      allocation_rule: [], allocation_share: [], allocation_target: [], citation: [], agreement: m.agreements, data_issue: m.dataIssues, scenario_change: [] };
    const svcCols = ['service_id', 'name', 'short_name', 'agency_id', 'operator_id', 'service_group', 'area_class', 'service_type', 'passenger_trips', 'vsh', 'vsm', 'data_year', 'cost_per_vsh_override', 'annual_cost_override', 'reference_cost', 'adjusts_service_id', 'state_conditions', 'local_conditions', 'notes'];
    for (const s of m.services) {
      const r = {}; for (const c of svcCols) r[c] = s[c] ?? null; r.federalized = +s.federalized; r.is_plan_element = +s.is_plan_element; r.included = +s.included; T.service.push(r);
      for (const [y, v] of Object.entries(s.years || {})) T.service_year.push({ service_id: s.service_id, fy_index: +y, active: +v.active, scheduled_cost: v.scheduled_cost ?? null });
      for (const [j, sh] of Object.entries(s.juris || {})) if (sh > 0) T.service_jurisdiction.push({ service_id: s.service_id, jurisdiction_id: j, share: sh, is_placeholder: +!!s.juris_placeholder });
    }
    const lineCols = ['line_id', 'program_id', 'recipient_agency_id', 'name', 'administered_by', 'base_amount', 'amount_method', 'prior_year_amount', 'growth_rate', 'last_fy_index', 'annual_cap', 'status', 'commitment_basis', 'commitment_note', 'contributor_jurisdiction_id', 'federal_share_cap', 'federal_share_cap_ada', 'purpose', 'match_text', 'condition_text', 'restriction_text', 'notes'];
    for (const l of m.lines) {
      const r = {}; for (const c of lineCols) r[c] = l[c] ?? null; r.counts_as_match = +l.counts_as_match; r.match_only = +l.match_only; r.enabled = +l.enabled; T.funding_line.push(r);
      for (const [y, v] of Object.entries(l.years || {})) if (v != null && +y > 0) T.funding_line_year.push({ line_id: l.line_id, fy_index: +y, amount: v });
      for (const [strength, g] of [['required', l.required], ['preferred', l.preferred]]) for (const [type, vals] of Object.entries(g || {})) for (const v of vals) T.eligibility_rule.push({ rule_row_id: T.eligibility_rule.length + 1, line_id: l.line_id, rule_type: type, strength, value: v });
      const d = m.draft[l.line_id];
      if (d) {
        T.allocation_rule.push({ scenario_id: 'draft', line_id: l.line_id, method: d.method, auto_basis: d.method === 'auto' ? d.basis : null });
        if (d.method === 'shares') for (const [sid, sh] of Object.entries(d.shares)) if (sh > 0) T.allocation_share.push({ scenario_id: 'draft', line_id: l.line_id, service_id: sid, share: sh });
        for (const sid of d.targets || []) T.allocation_target.push({ scenario_id: 'draft', line_id: l.line_id, service_id: sid });
      }
    }
    for (const [k, list] of Object.entries(m.citations)) { const [entity_type, entity_id] = k.split('|'); for (const c of list) T.citation.push({ citation_id: T.citation.length + 1, entity_type, entity_id, field: c.field, document_id: c.document_id, locator: c.locator }); }
    return { meta: m.meta, tables: T };
  }

  const IX = new WeakMap();
  function ix(m) {
    let x = IX.get(m);
    if (!x) {
      x = { svc: {}, line: {}, op: {}, ag: {}, jur: {}, adjusters: {} };
      for (const s of m.services) { x.svc[s.service_id] = s; if (s.adjusts_service_id) (x.adjusters[s.adjusts_service_id] = x.adjusters[s.adjusts_service_id] || []).push(s); }
      for (const l of m.lines) x.line[l.line_id] = l;
      for (const o of m.operators) x.op[o.operator_id] = o;
      for (const a of m.agencies) x.ag[a.agency_id] = a;
      for (const j of m.jurisdictions) x.jur[j.jurisdiction_id] = j;
      IX.set(m, x);
    }
    return x;
  }
  function reindex(m) { IX.delete(m); return ix(m); }
  function clone(m) { return JSON.parse(JSON.stringify(m)); }
  const citations = (m, type, id) => m.citations[type + '|' + id] || [];

  /* ── Scenario defaults ─────────────────────────────────────────────────── */
  function scenario(o) {
    return Object.assign({ year: 0, method: 'optimized', allowTransfers: false, strictPreferences: false, spreadShortfall: true,
      baseAmount: {}, scale: { level: {}, agency: {}, line: {} }, add: {}, costScale: { all: 1, service: {} }, include: {} }, o || {},
      { scale: Object.assign({ level: {}, agency: {}, line: {} }, (o || {}).scale || {}), costScale: Object.assign({ all: 1, service: {} }, (o || {}).costScale || {}) });
  }

  /* ── Costs (COST-01 … COST-06) ─────────────────────────────────────────── */
  function isIncluded(s, sc) { const v = sc && sc.include && sc.include[s.service_id]; return v == null ? !!s.included : !!v; }
  function serviceRate(m, s) { if (s.cost_per_vsh_override != null) return +s.cost_per_vsh_override; const o = ix(m).op[s.operator_id]; return o ? +o.cost_per_vsh : 0; }
  function ownCost(m, s, y, sc) {
    if (!isIncluded(s, sc)) return 0;                                                  // COST-05
    const yr = s.years && s.years[y];
    if (yr && yr.active === false) return 0;                                           // COST-05
    if (yr && yr.scheduled_cost != null) return +yr.scheduled_cost;                    // COST-04
    if (s.is_plan_element) return 0;
    const o = ix(m).op[s.operator_id];
    const base = s.annual_cost_override != null ? +s.annual_cost_override : (+s.vsh || 0) * serviceRate(m, s);   // COST-01, COST-02
    return base * Math.pow(1 + (o ? +o.annual_escalator : 0), y);                      // COST-03
  }
  function serviceCost(m, s, y, sc) {
    if (s.adjusts_service_id) return 0;                                                // counted on the service it adjusts
    let c = ownCost(m, s, y, sc);
    if (c && (!(s.years && s.years[y]) || s.years[y].active !== false)) for (const a of (ix(m).adjusters[s.service_id] || [])) c += ownCost(m, a, y, sc);   // COST-04
    const k = (sc && sc.costScale) ? (+sc.costScale.all || 1) * (sc.costScale.service && sc.costScale.service[s.service_id] != null ? +sc.costScale.service[s.service_id] : 1) : 1;
    return c * k;                                                                      // COST-06
  }
  function realServices(m) { return m.services.filter(s => !s.adjusts_service_id); }

  /* ── Revenue (REV-01 … REV-08) ─────────────────────────────────────────── */
  function ftaShares(m) {
    const f = m.fta, a = m.ftaFactors.TTD || {}, b = m.ftaFactors.TART || {};
    const part = k => { const t = (+a[k] || 0) + (+b[k] || 0); return t ? (+a[k] || 0) / t : 0.5; };
    const fac = { miles: part('urban_revenue_miles'), pop: part('population'), riders: part('ridership') };
    const w = [+f.weight_revenue_miles || 0, +f.weight_population || 0, +f.weight_ridership || 0]; const W = w[0] + w[1] + w[2] || 1;
    const ttd = (w[0] * fac.miles + w[1] * fac.pop + w[2] * fac.riders) / W;
    return { TTD: ttd, TART: 1 - ttd, factors: fac };
  }
  function ftaOperating(m, agency) { const sh = ftaShares(m)[agency]; return sh == null ? 0 : (+m.fta.apportionment_5307) * sh * (+m.fta.operations_share); }   // REV-02
  function lineBase(m, l, sc) {
    if (sc && sc.baseAmount && sc.baseAmount[l.line_id] != null) return +sc.baseAmount[l.line_id];
    return l.amount_method === 'fta_5307_formula' ? ftaOperating(m, l.recipient_agency_id) : (+l.base_amount || 0);   // REV-01
  }
  function projectedAmount(m, l, y, sc) {
    if (!l.enabled || l.status === 'capital') return 0;                                // REV-06
    if (l.last_fy_index != null && y > +l.last_fy_index) return 0;                     // REV-05
    const cap = l.annual_cap != null ? +l.annual_cap : Infinity;
    let a = Math.min(lineBase(m, l, sc), cap);
    for (let i = 1; i <= y; i++) {
      const ov = l.years ? l.years[i] : null;
      a = Math.min(ov != null ? +ov : a * (1 + (+l.growth_rate || 0)), cap);           // REV-03, REV-04
    }
    return a;
  }
  function lineAmount(m, l, y, sc) {
    let a = projectedAmount(m, l, y, sc);
    if (sc) {                                                                          // REV-08
      const s = sc.scale || {};
      a *= (s.level && s.level[l.level] != null ? +s.level[l.level] : 1) * (s.agency && s.agency[l.recipient_agency_id] != null ? +s.agency[l.recipient_agency_id] : 1) * (s.line && s.line[l.line_id] != null ? +s.line[l.line_id] : 1);
      if (sc.add && sc.add[l.line_id]) a += +sc.add[l.line_id];
    }
    return Math.max(0, a);
  }
  function projectionText(l) {
    const p = [];
    if (l.amount_method === 'fta_5307_formula') p.push('FTA split formula');
    if (+l.growth_rate) p.push((l.growth_rate > 0 ? '+' : '') + (+(l.growth_rate * 100).toFixed(3)) + '%/yr');
    if (l.annual_cap != null) p.push('cap $' + Math.round(l.annual_cap).toLocaleString('en-US'));
    if (Object.values(l.years || {}).some(v => v != null)) p.push('year values set');
    if (l.last_fy_index != null) p.push(+l.last_fy_index === 0 ? 'base year only' : 'ends after year ' + (+l.last_fy_index + 1));
    return p.join(', ') || 'flat';
  }

  /* ── Eligibility (ELIG-01 … ELIG-07, PREF-01 … PREF-04) ───────────────── */
  function jurTotal(s) { let t = 0; for (const v of Object.values(s.juris || {})) t += +v || 0; return t; }
  function stateShare(m, s, states) {
    const t = jurTotal(s); if (!t) return 1;
    let a = 0; const J = ix(m).jur;
    for (const [k, v] of Object.entries(s.juris)) if (J[k] && states.includes(J[k].state)) a += +v || 0;
    return a / t;
  }
  function jurShare(s, j) { const t = jurTotal(s); return t ? (+(s.juris || {})[j] || 0) / t : 0; }
  function stateText(m, s) { if (!jurTotal(s)) return 'no listed jurisdiction'; const ca = stateShare(m, s, ['CA']); return ca >= 0.999 ? 'California' : ca <= 0.001 ? 'Nevada' : `both states (${Math.round(ca * 100)}% California)`; }
  function names(m, ids, kind) { const X = ix(m); return ids.map(id => kind === 'svc' ? (X.svc[id] || {}).short_name || id : kind === 'ag' ? (X.ag[id] || {}).short_name || id : kind === 'jur' ? (X.jur[id] || {}).name || id : id).join(', '); }

  /** Evaluate one source-on-service use. Returns { ok, cap, hard[], soft[] } where cap is the eligible portion of cost. */
  function checkUse(m, l, s) {
    const R = l.required || {}, P = l.preferred || {}, hard = [], soft = []; let cap = 1, capRule = null;
    if (R.service && R.service.length && !R.service.includes(s.service_id)) hard.push({ rule: 'ELIG-01', msg: `Restricted to ${names(m, R.service, 'svc')}` });
    if (R.agency && R.agency.length && !R.agency.includes(s.agency_id)) hard.push({ rule: 'ELIG-02', msg: `Restricted to ${names(m, R.agency, 'ag')} services` });
    if (R.area_class && R.area_class.length && !R.area_class.includes(s.area_class)) hard.push({ rule: 'ELIG-03', msg: `Needs ${R.area_class.join(' or ')} service; ${s.short_name} is ${s.area_class}` });
    if (R.service_type && R.service_type.length && !R.service_type.includes(s.service_type)) hard.push({ rule: 'ELIG-04', msg: `Restricted to ${R.service_type.join(', ')} service` });
    if (R.state && R.state.length) {
      const f = stateShare(m, s, R.state);
      if (f <= 1e-6) hard.push({ rule: 'ELIG-05', msg: `${R.state.join('/')} only; ${s.short_name} operates in ${stateText(m, s)}` });
      else if (f < 1 - 1e-9) { cap = Math.min(cap, f); capRule = 'ELIG-05'; }
    }
    if (R.jurisdiction_share && R.jurisdiction_share.length) {
      let f = 0; for (const j of R.jurisdiction_share) f += jurShare(s, j);
      if (f <= 1e-6) hard.push({ rule: 'ELIG-06', msg: `Limited to the ${names(m, R.jurisdiction_share, 'jur')} share; ${s.short_name} has none` });
      else if (f < cap - 1e-9) { cap = f; capRule = 'ELIG-06'; }
    }
    if (l.level === 'federal' && s.federalized === false) hard.push({ rule: 'ELIG-07', msg: `${s.short_name} is not a federalized service` });
    if (P.service && P.service.length && !P.service.includes(s.service_id)) soft.push({ rule: 'PREF-01', msg: `Intended for ${names(m, P.service, 'svc')}` });
    if (P.state && P.state.length && stateShare(m, s, P.state) <= 1e-6) soft.push({ rule: 'PREF-02', msg: `Ideally used in ${P.state.join('/')}; ${s.short_name} operates in ${stateText(m, s)}` });
    if (P.jurisdiction_share && P.jurisdiction_share.length) { let f = 0; for (const j of P.jurisdiction_share) f += jurShare(s, j); if (f <= 1e-6) soft.push({ rule: 'PREF-03', msg: `Ideally used in ${names(m, P.jurisdiction_share, 'jur')}` }); }
    if (l.recipient_agency_id && l.recipient_agency_id !== 'REGION' && s.agency_id !== l.recipient_agency_id) soft.push({ rule: 'PREF-04', msg: `${names(m, [l.recipient_agency_id], 'ag')} funds on a ${names(m, [s.agency_id], 'ag')} service need an interagency agreement` });
    return { ok: hard.length === 0, cap, capRule, hard, soft };
  }
  function fedCap(l, s) {
    if (l.federal_share_cap == null) return 1;
    if (s.service_type === 'paratransit' && l.federal_share_cap_ada != null) return +l.federal_share_cap_ada;   // FED-02
    return +l.federal_share_cap;
  }
  function rulesText(m, l) {
    const R = l.required || {}, P = l.preferred || {}, a = [];
    if (R.service) a.push('only ' + names(m, R.service, 'svc'));
    if (R.agency) a.push('only ' + names(m, R.agency, 'ag') + ' services');
    if (R.state) a.push(R.state.join('/') + ' only');
    if (R.area_class) a.push(R.area_class.join(' or ') + ' service');
    if (R.service_type) a.push(R.service_type.join(', ') + ' only');
    if (R.jurisdiction_share) a.push('up to the ' + names(m, R.jurisdiction_share, 'jur') + ' share');
    if (P.service) a.push('intended for ' + names(m, P.service, 'svc'));
    if (P.state) a.push('prefer ' + P.state.join('/'));
    if (P.jurisdiction_share) a.push('prefer ' + names(m, P.jurisdiction_share, 'jur'));
    if (l.federal_share_cap != null) a.push('federal share ≤ ' + (+(l.federal_share_cap * 100).toFixed(2)) + '%' + (l.federal_share_cap_ada != null ? ' (ADA ' + Math.round(l.federal_share_cap_ada * 100) + '%)' : ''));
    if (l.match_only) a.push('match only');
    if (!l.counts_as_match && l.level !== 'federal') a.push('not match');
    return a.join('; ') || 'none';
  }

  /* ── Fixed-shares allocation (ALLOC-01, ALLOC-02) ──────────────────────── */
  function basisValue(m, s, basis, sc) { switch (basis) { case 'vsh': return +s.vsh || 0; case 'vsm': return +s.vsm || 0; case 'trips': return +s.passenger_trips || 0; case 'cost': return serviceCost(m, s, 0, sc); default: return 1; } }
  function draftShares(m, l, active, sc) {
    const d = m.draft[l.line_id]; if (!d) return {};
    const ids = new Set(active.map(s => s.service_id)), out = {};
    if (d.method === 'shares') { for (const [sid, p] of Object.entries(d.shares || {})) if (ids.has(sid) && +p) out[sid] = +p; return out; }
    const hasT = d.targets && d.targets.length;
    let c = hasT ? active.filter(s => d.targets.includes(s.service_id)) : active.slice();
    c = c.filter(s => checkUse(m, l, s).ok);
    if (!hasT) { const pref = c.filter(s => checkUse(m, l, s).soft.length === 0); if (pref.length) c = pref; }
    let w = c.map(s => basisValue(m, s, d.basis || 'vsh', sc) * checkUse(m, l, s).cap), W = w.reduce((a, b) => a + b, 0);
    if (!W && c.length) { w = c.map(() => 1); W = c.length; }
    c.forEach((s, i) => { if (w[i] > 0) out[s.service_id] = w[i] / W; });
    return out;
  }
  function allocateFixed(m, y, sc) {
    const active = realServices(m).filter(s => serviceCost(m, s, y, sc) > 0), alloc = {};
    for (const l of m.lines) {
      const amt = lineAmount(m, l, y, sc); if (!amt) continue;
      const p = draftShares(m, l, active, sc), a = {};
      for (const [sid, sh] of Object.entries(p)) a[sid] = amt * sh;
      alloc[l.line_id] = a;
    }
    return alloc;
  }

  /* ── Linear programming: dense simplex with lexicographic objectives ────
     maximize objectives[0]·x, then objectives[1]·x over the optimal face of the first, and so on;
     subject to A x ≤ b, x ≥ 0, b ≥ 0 (so x = 0 is feasible). Rows are sparse arrays of [col, value].
     Dantzig pricing with Bland's rule after repeated degenerate pivots. Returns x, the duals of the
     first objective, and status. */
  function simplex(nVars, rows, b, objectives, opts) {
    opts = opts || {};
    const m = rows.length, n = nVars, N = n + m, W = N + 1, K = objectives.length, EPS = 1e-9, maxIt = opts.maxIterations || 200000;
    const T = new Float64Array((m + K) * W);
    for (let i = 0; i < m; i++) { for (const [j, v] of rows[i]) T[i * W + j] += v; T[i * W + n + i] = 1; T[i * W + N] = b[i]; }
    for (let k = 0; k < K; k++) for (let j = 0; j < n; j++) T[(m + k) * W + j] = -(objectives[k][j] || 0);
    const basis = new Int32Array(m); for (let i = 0; i < m; i++) basis[i] = n + i;
    let it = 0, bland = false, degen = 0;
    const pivot = (r, e) => {
      const pr = r * W, pv = T[pr + e];
      for (let q = 0; q < W; q++) T[pr + q] /= pv;
      for (let i = 0; i < m + K; i++) {
        if (i === r) continue; const ir = i * W, f = T[ir + e]; if (f === 0) continue;
        for (let q = 0; q < W; q++) { const v = T[pr + q]; if (v !== 0) T[ir + q] -= f * v; }
        T[ir + e] = 0;
      }
      basis[r] = e;
    };
    for (let phase = 0; phase < K; phase++) {
      const orow = (m + phase) * W; bland = false; degen = 0;
      while (it < maxIt) {
        let e = -1, best = -EPS;
        for (let j = 0; j < N; j++) {
          let onFace = true;                                                   // stay on the optimal face of earlier objectives
          for (let q = 0; q < phase; q++) if (T[(m + q) * W + j] > 1e-8) { onFace = false; break; }
          if (!onFace) continue;
          const d = T[orow + j];
          if (d < -EPS) { if (bland) { e = j; break; } if (d < best) { best = d; e = j; } }
        }
        if (e < 0) break;
        let r = -1, rmin = Infinity;
        for (let i = 0; i < m; i++) {
          const a = T[i * W + e];
          if (a > EPS) { const q = T[i * W + N] / a; if (q < rmin - 1e-12 || (r >= 0 && Math.abs(q - rmin) <= 1e-12 && basis[i] < basis[r])) { rmin = q; r = i; } }
        }
        if (r < 0) return { status: 'unbounded', iterations: it };
        if (rmin < 1e-12) { if (++degen > 40) bland = true; } else { degen = 0; bland = false; }
        pivot(r, e); it++;
      }
    }
    const x = new Float64Array(n);
    for (let i = 0; i < m; i++) if (basis[i] < n) x[basis[i]] = Math.max(0, T[i * W + N]);
    const y = new Float64Array(m); for (let i = 0; i < m; i++) y[i] = T[m * W + n + i];
    const objectiveValues = []; for (let k = 0; k < K; k++) objectiveValues.push(T[(m + k) * W + N]);
    return { status: it >= maxIt ? 'iteration_limit' : 'optimal', x, y, iterations: it, objective: objectiveValues[0], objectiveValues };
  }
  // OPT-07: primal feasible, dual feasible, zero gap (for the primary objective)
  function certify(nVars, rows, b, c, x, y) {
    const tol = 1e-7; let primal = 0, dual = 0, cx = 0, by = 0;
    for (let i = 0; i < rows.length; i++) { let s = 0; for (const [j, v] of rows[i]) s += v * x[j]; primal = Math.max(primal, s - b[i]); by += b[i] * y[i]; dual = Math.max(dual, -y[i]); }
    const at = new Float64Array(nVars); for (let i = 0; i < rows.length; i++) for (const [j, v] of rows[i]) at[j] += v * y[i];
    for (let j = 0; j < nVars; j++) { cx += (c[j] || 0) * x[j]; dual = Math.max(dual, (c[j] || 0) - at[j]); primal = Math.max(primal, -x[j]); }
    const gap = Math.abs(cx - by);
    return { ok: primal <= tol && dual <= tol && gap <= tol * (1 + Math.abs(cx)), primalViolation: primal, dualViolation: dual, gap, primalObjective: cx, dualObjective: by };
  }

  /* ── Rules-based allocation (OPT-01 … OPT-09) ──────────────────────────── */
  function buildLP(m, y, sc) {
    const svcs = realServices(m).filter(s => serviceCost(m, s, y, sc) > 0);
    const cost = {}; for (const s of svcs) cost[s.service_id] = serviceCost(m, s, y, sc);
    const vars = [], supplyRow = {}, lines = [];
    for (const l of m.lines) {
      if (!l.enabled || l.status === 'capital') continue;
      if (l.last_fy_index != null && y > +l.last_fy_index && !(sc.add && sc.add[l.line_id])) continue;
      const amt = lineAmount(m, l, y, sc);
      lines.push({ l, amt });
      for (const s of svcs) {
        const ev = checkUse(m, l, s); if (!ev.ok) continue;                              // OPT-02 (ELIG-01 … ELIG-07)
        const cross = l.recipient_agency_id !== 'REGION' && s.agency_id !== l.recipient_agency_id;
        if (cross && !sc.allowTransfers) continue;                                        // OPT-03
        const softN = ev.soft.filter(v => v.rule !== 'PREF-04').length;
        if (softN && sc.strictPreferences) continue;                                      // OPT-04
        vars.push({ l, s, cap: ev.cap, softN, cross });
      }
    }
    const rows = [], b = [], rowInfo = [];
    const add = (cells, rhs, info) => { rows.push(cells); b.push(rhs); rowInfo.push(info); return rows.length - 1; };
    for (const { l, amt } of lines) { const cells = []; vars.forEach((v, j) => { if (v.l === l) cells.push([j, 1]); }); if (cells.length) supplyRow[l.line_id] = add(cells, amt * SCALE, { type: 'supply', line: l.line_id }); }
    for (const s of svcs) {
      const sid = s.service_id, costCells = [], match = []; let anyFed = false;
      vars.forEach((v, j) => {
        if (v.s !== s) return;
        if (!v.l.match_only) costCells.push([j, 1]);
        if (v.l.level === 'federal') { const k = fedCap(v.l, s); match.push([j, (1 - k) / k]); anyFed = true; }
        else if (v.l.level !== 'fare' && (v.l.counts_as_match || v.l.match_only)) match.push([j, -1]);
      });
      if (costCells.length) add(costCells, cost[sid] * SCALE, { type: 'cost', service: sid });
      if (anyFed) add(match, 0, { type: 'match', service: sid });                           // MATCH-03
    }
    vars.forEach((v, j) => { if (v.cap < 1 - 1e-9) add([[j, 1]], v.cap * cost[v.s.service_id] * SCALE, { type: 'portion', service: v.s.service_id, line: v.l.line_id }); });
    // OPT-05: coverage variable t = lowest share of cost funded on any service that has an eligible source
    const tCol = vars.length, nCols = vars.length + 1;
    if (sc.spreadShortfall !== false) {
      for (const s of svcs) {
        const cells = []; vars.forEach((v, j) => { if (v.s === s && !v.l.match_only) cells.push([j, -1]); });
        if (cells.length) { cells.push([tCol, cost[s.service_id] * SCALE]); add(cells, 0, { type: 'coverage', service: s.service_id }); }
      }
      add([[tCol, 1]], 1, { type: 'coverage-max' });
    } else add([[tCol, 1]], 0, { type: 'coverage-off' });
    // OPT-01 primary objective, OPT-05 evenness, OPT-06 tie-breaks
    const c1 = vars.map(v => v.l.match_only ? 0 : 1).concat([0]);
    const cEven = vars.map(() => 0).concat([1]);
    const c2 = vars.map(v => {
      if (v.l.match_only) return 0;
      let w = 0;
      if (v.l.level === 'fare') w += 10;
      if (v.l.level === 'federal') w += 4;
      if (v.l.required && v.l.required.service && v.l.required.service.length) w += 3;
      if (RISKY.has(v.l.commitment_basis)) w += 2;
      w -= 5 * v.softN; if (v.cross) w -= 20;
      return w;
    }).concat([0]);
    return { vars, nCols, tCol, rows, b, objectives: [c1, cEven, c2], c1, rowInfo, supplyRow, cost, svcs, lines };
  }
  function allocateOptimal(m, y, sc) {
    const lp = buildLP(m, y, sc);
    const res = simplex(lp.nCols, lp.rows, lp.b, lp.objectives);
    const alloc = {};
    if (res.status !== 'optimal') return { alloc, lp, status: res.status, certificate: null };
    lp.vars.forEach((v, j) => { const d = res.x[j] / SCALE; if (d > 0.005) { (alloc[v.l.line_id] = alloc[v.l.line_id] || {})[v.s.service_id] = d; } });
    const cert = certify(lp.nCols, lp.rows, lp.b, lp.c1, res.x, res.y);
    const shadow = {}; for (const [lid, r] of Object.entries(lp.supplyRow)) shadow[lid] = res.y[r];   // SENS-01 (dual price)
    return { alloc, lp, status: res.status, iterations: res.iterations, certificate: cert, shadow, funded: res.objective / SCALE, minCoverage: res.x[lp.tCol] };
  }

  /* ── Evaluation and checks (FED, MATCH, ALLOC, SVC, RES) ───────────────── */
  function evaluate(m, y, sc, alloc) {
    const X = ix(m), R = { year: y, services: {}, lines: {}, agencies: {}, jurisdictions: {}, totals: {}, issues: [] };
    const issue = (severity, rule, msg, line, svc, amount) => R.issues.push({ severity, rule, title: (RULE[rule] || {}).title || rule, message: msg, line: line || null, service: svc || null, agency: svc ? (X.svc[svc] || {}).agency_id : line ? (X.line[line] || {}).recipient_agency_id : null, amount: amount || 0 });
    for (const s of realServices(m)) {
      const cost = serviceCost(m, s, y, sc);
      if (!cost && !isIncluded(s, sc)) continue;
      R.services[s.service_id] = { id: s.service_id, name: s.name, short: s.short_name, agency: s.agency_id, cost, fares: 0, byLevel: Object.fromEntries(LEVELS.map(k => [k, 0])), cash: 0, credits: 0, fed: 0, matchReq: 0, matchAvail: 0, fedCap: 0, risk: 0, lines: {}, errors: 0, warnings: 0 };
    }
    for (const l of m.lines) {
      const amt = lineAmount(m, l, y, sc), a = alloc[l.line_id] || {};
      const L = R.lines[l.line_id] = { id: l.line_id, name: l.name, level: l.level, agency: l.recipient_agency_id, amount: amt, allocated: 0, unallocated: 0, services: {} };
      for (const [sid, d] of Object.entries(a)) {
        const sv = R.services[sid]; if (!sv || d <= 0) continue; const s = X.svc[sid];
        L.allocated += d; L.services[sid] = d; sv.lines[l.line_id] = d;
        if (l.match_only) sv.credits += d; else { sv.byLevel[l.level] += d; sv.cash += d; if (RISKY.has(l.commitment_basis)) sv.risk += d; }
        if (l.level === 'federal' && !l.match_only) { const k = fedCap(l, s); sv.fed += d; sv.matchReq += d * (1 - k) / k; sv.fedCap = Math.max(sv.fedCap, k); }   // MATCH-01
        else if (l.level === 'fare') sv.fares += d;                                                                                                       // FED-01
        else if (l.counts_as_match || l.match_only) sv.matchAvail += d;                                                                                   // MATCH-02
        if (d > TOL) {
          const ev = checkUse(m, l, s);
          for (const h of ev.hard) issue('error', h.rule, h.msg, l.line_id, sid, d);
          if (ev.ok && ev.cap < 1 && d > ev.cap * sv.cost + TOL) issue('error', ev.capRule, `${money(d)} exceeds the eligible ${Math.round(ev.cap * 100)}% of ${s.short_name}'s ${money(sv.cost)} cost`, l.line_id, sid, d - ev.cap * sv.cost);
          for (const p of ev.soft) issue('warning', p.rule, p.msg, l.line_id, sid, d);
        }
      }
      L.unallocated = amt - L.allocated;
      if (L.allocated > amt + Math.max(TOL, amt * 1e-6)) issue('error', 'ALLOC-03', `${money(L.allocated)} applied from a ${money(amt)} source`, l.line_id, null, L.allocated - amt);
      else if (L.unallocated > TOL) issue('info', 'ALLOC-04', `${money(L.unallocated)} not applied to a service`, l.line_id, null, L.unallocated);
    }
    for (const sv of Object.values(R.services)) {
      sv.net = Math.max(0, sv.cost - sv.fares);
      const tol = Math.max(5, sv.net * 5e-4);
      const basisFed = sv.net + sv.credits;                                              // FED-02: credits widen the base
      for (const [lid, d] of Object.entries(sv.lines)) {
        const l = X.line[lid]; if (l.level !== 'federal' || l.federal_share_cap == null) continue;
        const k = fedCap(l, X.svc[sv.id]);
        if (d > k * basisFed + tol) issue('error', 'FED-02', `${l.name}: ${money(d)} is ${pctTxt(basisFed ? d / basisFed : 1)} of net cost${sv.credits ? ' plus credits' : ''}; its cap is ${pctTxt(k)}`, lid, sv.id, d - k * basisFed);
      }
      const nFed = Object.keys(sv.lines).filter(lid => X.line[lid].level === 'federal' && !X.line[lid].match_only).length;
      if (nFed > 1 && sv.fedCap < 1 && sv.fed > sv.fedCap * basisFed + tol) issue('error', 'FED-03', `Federal funds of ${money(sv.fed)} are ${pctTxt(basisFed ? sv.fed / basisFed : 1)} of net cost${sv.credits ? ' plus credits' : ''}; the cap is ${pctTxt(sv.fedCap)}`, null, sv.id, sv.fed - sv.fedCap * basisFed);
      if (sv.matchReq > sv.matchAvail + Math.max(5, sv.matchReq * 5e-4)) issue('error', 'MATCH-03', `Needs ${money(sv.matchReq)} in non-federal match; ${money(sv.matchAvail)} applied`, null, sv.id, sv.matchReq - sv.matchAvail);
      sv.funded = Math.max(0, Math.min(sv.cash, sv.cost));                              // RES-01
      sv.gap = Math.max(0, sv.cost - sv.cash); sv.excess = Math.max(0, sv.cash - Math.max(0, sv.cost));
      if (sv.gap > TOL) issue('info', 'SVC-01', `${money(sv.gap)} of ${money(sv.cost)} has no funding applied`, null, sv.id, sv.gap);
      if (sv.excess > TOL) issue('warning', 'SVC-02', `${money(sv.excess)} applied above the ${money(sv.cost)} cost`, null, sv.id, sv.excess);
      sv.riskShare = sv.cash ? sv.risk / sv.cash : 0;                                   // RES-04
    }
    for (const it of R.issues) if (it.service && R.services[it.service]) { if (it.severity === 'error') R.services[it.service].errors++; else if (it.severity === 'warning') R.services[it.service].warnings++; }
    // RES-02 agencies
    for (const a of m.agencies) R.agencies[a.agency_id] = { id: a.agency_id, name: a.name, short: a.short_name, cost: 0, funded: 0, gap: 0, rev: Object.fromEntries(LEVELS.map(k => [k, 0])), revenue: 0, credits: 0, applied: 0, unallocated: 0, risk: 0, commit: {}, services: 0 };
    for (const sv of Object.values(R.services)) { const A = R.agencies[sv.agency]; if (!A) continue; A.cost += sv.cost; A.funded += sv.funded; A.gap += sv.gap; A.services++; }
    for (const L of Object.values(R.lines)) {
      const l = X.line[L.id]; const A = R.agencies[L.agency] || R.agencies.REGION; if (!L.amount || !A) continue;
      if (l.match_only) { A.credits += L.amount; continue; }
      A.rev[l.level] += L.amount; A.revenue += L.amount; A.applied += L.allocated; A.unallocated += Math.max(0, L.unallocated);
      A.commit[l.commitment_basis] = (A.commit[l.commitment_basis] || 0) + L.amount; if (RISKY.has(l.commitment_basis)) A.risk += L.amount;
    }
    for (const A of Object.values(R.agencies)) A.balance = A.revenue - A.cost;
    // RES-03 jurisdictions
    for (const j of m.jurisdictions) R.jurisdictions[j.jurisdiction_id] = { id: j.jurisdiction_id, name: j.name, short: j.short_name, state: j.state, cost: 0, nonLocal: 0, local: 0, contributions: 0 };
    for (const sv of Object.values(R.services)) {
      const s = X.svc[sv.id], t = jurTotal(s); if (!t) continue;
      for (const [jid, sh] of Object.entries(s.juris)) { const J = R.jurisdictions[jid]; if (!J) continue; const f = (+sh || 0) / t; J.cost += sv.cost * f; J.nonLocal += (sv.cash - sv.byLevel.local) * f; J.local += sv.byLevel.local * f; }
    }
    for (const L of Object.values(R.lines)) { const l = X.line[L.id]; if (l.contributor_jurisdiction_id && R.jurisdictions[l.contributor_jurisdiction_id] && !l.match_only) R.jurisdictions[l.contributor_jurisdiction_id].contributions += L.amount; }
    for (const J of Object.values(R.jurisdictions)) { J.localShare = J.cost - J.nonLocal; J.difference = J.contributions - J.localShare; }
    // totals
    const T = R.totals, svs = Object.values(R.services), ags = Object.values(R.agencies);
    T.cost = sum(svs.map(s => s.cost)); T.funded = sum(svs.map(s => s.funded)); T.gap = sum(svs.map(s => s.gap)); T.excess = sum(svs.map(s => s.excess));
    T.rev = Object.fromEntries(LEVELS.map(k => [k, sum(ags.map(a => a.rev[k]))])); T.revenue = sum(ags.map(a => a.revenue)); T.credits = sum(ags.map(a => a.credits));
    T.applied = sum(ags.map(a => a.applied)); T.unallocated = sum(ags.map(a => a.unallocated)); T.balance = T.revenue - T.cost; T.risk = sum(ags.map(a => a.risk));
    T.fedUnallocated = sum(Object.values(R.lines).filter(L => L.level === 'federal').map(L => Math.max(0, L.unallocated)));
    T.errors = R.issues.filter(i => i.severity === 'error').length; T.warnings = R.issues.filter(i => i.severity === 'warning').length;
    T.planNotIncluded = sum(m.services.filter(s => s.is_plan_element && !isIncluded(s, sc)).map(s => { const yr = s.years && s.years[y]; return yr && yr.scheduled_cost != null ? +yr.scheduled_cost : 0; }));
    T.services = svs.filter(s => s.cost > 0).length; T.sources = Object.values(R.lines).filter(L => L.amount > 0 && !X.line[L.id].match_only).length;
    return R;
  }

  // OPT-08: explain unused amounts of an optimized allocation
  function explainUnused(m, R, lp) {
    const X = ix(m);
    for (const L of Object.values(R.lines)) {
      if (L.unallocated <= TOL) continue;
      const vs = lp.vars.filter(v => v.l.line_id === L.id);
      if (!vs.length) { L.reason = 'No eligible service'; L.reasonDetail = 'Its required rules exclude every active service it may fund'; continue; }
      const open = vs.filter(v => (R.services[v.s.service_id] || {}).gap > TOL);
      if (!open.length) { L.reason = 'Eligible services fully funded'; L.reasonDetail = 'Every service it may fund already has its full cost covered'; continue; }
      if (X.line[L.id].level === 'federal') { L.reason = 'Not enough non-federal match'; L.reasonDetail = `Services with gaps (${open.map(v => v.s.short_name).join(', ')}) lack the match to use more`; continue; }
      L.reason = 'Eligible-portion cap'; L.reasonDetail = 'Limited to the state or jurisdiction share of its eligible services';
    }
  }

  /* ── Running a scenario ─────────────────────────────────────────────────── */
  function run(m, scIn) {
    const sc = scenario(scIn), y = sc.year;
    let alloc, opt = null;
    if (sc.method === 'optimized') { opt = allocateOptimal(m, y, sc); alloc = opt.alloc; } else alloc = sc.allocation || allocateFixed(m, y, sc);
    const results = evaluate(m, y, sc, alloc);
    if (opt) { explainUnused(m, results, opt.lp); results.optimizer = { status: opt.status, iterations: opt.iterations, certificate: opt.certificate, shadow: opt.shadow, minCoverage: opt.minCoverage, variables: opt.lp.vars.length, constraints: opt.lp.rows.length }; }
    return { scenario: sc, year: y, method: sc.method, alloc, results };
  }
  function runYears(m, scIn) { return m.years.map((_, y) => run(m, Object.assign({}, scIn, { year: y }))); }

  /* ── Sensitivity (SENS-01, SENS-02) ─────────────────────────────────────── */
  function sensitivity(m, scIn, opts) {
    opts = opts || {}; const step = opts.step || 100000;
    const sc = scenario(Object.assign({}, scIn, { method: 'optimized' }));
    const base = run(m, sc), F0 = base.results.totals.funded, out = [];
    const ids = opts.lines || m.lines.filter(l => l.enabled && l.status !== 'capital' && !l.match_only).map(l => l.line_id);
    for (const id of ids) {
      const l = ix(m).line[id]; const amt = lineAmount(m, l, sc.year, sc);
      const add = Object.assign({}, sc.add, { [id]: ((sc.add || {})[id] || 0) + step });
      const up = run(m, Object.assign({}, sc, { add }));
      const sh0 = (base.results.optimizer.shadow || {})[id];
      const row = { line: id, name: l.name, agency: l.recipient_agency_id, level: l.level, amount: amt, shadow: sh0 == null ? null : sh0,
        plusFunded: up.results.totals.funded - F0, perDollar: (up.results.totals.funded - F0) / step, lossFunded: 0, lossServices: [] };
      if (amt > TOL) {
        const scale = Object.assign({}, sc.scale, { line: Object.assign({}, sc.scale.line, { [id]: 0 }) });
        const dn = run(m, Object.assign({}, sc, { scale, add: Object.assign({}, sc.add, { [id]: 0 }) }));
        row.lossFunded = dn.results.totals.funded - F0;
        row.lossServices = Object.values(dn.results.services).map(s => ({ id: s.id, short: s.short, delta: s.funded - (base.results.services[s.id] || {}).funded })).filter(s => s.delta < -TOL).sort((a, b) => a.delta - b.delta);
      }
      out.push(row);
    }
    return { base, rows: out, step };
  }

  /* ── Small helpers ──────────────────────────────────────────────────────── */
  function sum(a) { let t = 0; for (const v of a) t += +v || 0; return t; }
  function money(v) { if (v == null || isNaN(v)) return '—'; const r = Math.round(v); return (r < 0 ? '−' : '') + '$' + Math.abs(r).toLocaleString('en-US'); }
  function pctTxt(p) { return (Math.round(p * 1000) / 10) + '%'; }

  return { VERSION, LEVELS, RULES, RULE, load, toSeed, clone, reindex, ix, citations, scenario,
    serviceCost, serviceRate, realServices, ftaShares, ftaOperating, lineBase, lineAmount, projectionText,
    checkUse, fedCap, stateShare, jurShare, stateText, rulesText, draftShares, allocateFixed, allocateOptimal, buildLP, simplex, certify,
    evaluate, run, runYears, sensitivity, money };
});
