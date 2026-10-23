-- Lake Tahoe Region transit funding model: database schema
-- SQLite syntax; every type maps directly to PostgreSQL (TEXT, INTEGER, REAL -> double precision).
-- Booleans are INTEGER 0/1. Money is US dollars, nominal. Shares and rates are fractions (0.5 = 50%).
-- tools/build.py loads data/seed.json into this schema and checks every key and constraint.

PRAGMA foreign_keys = ON;

-- ── Reference tables ─────────────────────────────────────────────────────────

CREATE TABLE source_document (
  document_id   TEXT PRIMARY KEY,                -- short key used by citations, e.g. 'plan'
  file_name     TEXT NOT NULL,
  description   TEXT
);

CREATE TABLE fiscal_year (
  fy_index      INTEGER PRIMARY KEY,             -- 0 = base year (FY 26-27)
  label         TEXT NOT NULL UNIQUE
);

CREATE TABLE agency (
  agency_id     TEXT PRIMARY KEY,                -- receiving or operating agency
  name          TEXT NOT NULL,
  short_name    TEXT NOT NULL
);

CREATE TABLE jurisdiction (
  jurisdiction_id TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  short_name    TEXT NOT NULL,
  state         TEXT NOT NULL CHECK (state IN ('CA', 'NV'))
);

-- ── Costs ────────────────────────────────────────────────────────────────────

CREATE TABLE operator (
  operator_id      TEXT PRIMARY KEY,
  name             TEXT NOT NULL,
  cost_per_vsh     REAL NOT NULL CHECK (cost_per_vsh >= 0),   -- fully allocated operating cost per vehicle service hour
  annual_escalator REAL NOT NULL,                              -- cost growth per year
  basis            TEXT
);

CREATE TABLE service (
  service_id            TEXT PRIMARY KEY,
  name                  TEXT NOT NULL,
  short_name            TEXT NOT NULL,
  agency_id             TEXT NOT NULL REFERENCES agency (agency_id),
  operator_id           TEXT NOT NULL REFERENCES operator (operator_id),
  service_group         TEXT,
  area_class            TEXT NOT NULL CHECK (area_class IN ('urban', 'rural', 'mixed')),
  service_type          TEXT NOT NULL CHECK (service_type IN ('fixed', 'seasonal', 'paratransit', 'microtransit', 'airport', 'vanpool')),
  federalized           INTEGER NOT NULL DEFAULT 1 CHECK (federalized IN (0, 1)),
  is_plan_element       INTEGER NOT NULL DEFAULT 0 CHECK (is_plan_element IN (0, 1)),
  included              INTEGER NOT NULL DEFAULT 1 CHECK (included IN (0, 1)),
  passenger_trips       REAL,
  vsh                   REAL CHECK (vsh IS NULL OR vsh >= 0),   -- annual vehicle service hours
  vsm                   REAL,                                   -- annual vehicle service miles
  data_year             TEXT,
  cost_per_vsh_override REAL,                                   -- replaces the operator rate for this service
  annual_cost_override  REAL,                                   -- replaces VSH x rate for this service (base year)
  reference_cost        REAL,                                   -- financial plan cost, shown for comparison only
  adjusts_service_id    TEXT REFERENCES service (service_id),   -- plan element whose cost is added to another service's cost
  state_conditions      TEXT,
  local_conditions      TEXT,
  notes                 TEXT
);

-- Year-specific activity and scheduled costs. A service with no row for a year is active
-- and costed as VSH x rate escalated. scheduled_cost replaces that calculation (service plan elements).
CREATE TABLE service_year (
  service_id      TEXT NOT NULL REFERENCES service (service_id),
  fy_index        INTEGER NOT NULL REFERENCES fiscal_year (fy_index),
  active          INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
  scheduled_cost  REAL,
  PRIMARY KEY (service_id, fy_index)
);

-- Share of each service attributed to each jurisdiction. Shares are normalized to sum to 1 when used.
-- They set a service's California and Nevada portions (state-restricted funds), cap jurisdiction-restricted
-- funds, and drive the jurisdiction results.
CREATE TABLE service_jurisdiction (
  service_id      TEXT NOT NULL REFERENCES service (service_id),
  jurisdiction_id TEXT NOT NULL REFERENCES jurisdiction (jurisdiction_id),
  share           REAL NOT NULL CHECK (share > 0),
  is_placeholder  INTEGER NOT NULL DEFAULT 1 CHECK (is_placeholder IN (0, 1)),
  PRIMARY KEY (service_id, jurisdiction_id)
);

-- ── Funding ──────────────────────────────────────────────────────────────────

CREATE TABLE funding_program (
  program_id    TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  level         TEXT NOT NULL CHECK (level IN ('federal', 'state', 'local', 'private', 'fare', 'other')),
  grantor       TEXT
);

-- One program as received by one agency, e.g. FTA 5307 as received by TTD.
CREATE TABLE funding_line (
  line_id                     TEXT PRIMARY KEY,
  program_id                  TEXT NOT NULL REFERENCES funding_program (program_id),
  recipient_agency_id         TEXT NOT NULL REFERENCES agency (agency_id),
  name                        TEXT NOT NULL,
  administered_by             TEXT,                                             -- who passes the money through
  base_amount                 REAL NOT NULL DEFAULT 0 CHECK (base_amount >= 0),  -- base-year budget amount
  amount_method               TEXT NOT NULL DEFAULT 'fixed' CHECK (amount_method IN ('fixed', 'fta_5307_formula')),
  prior_year_amount           REAL,                                             -- FY 25-26, from the fact sheets
  growth_rate                 REAL NOT NULL DEFAULT 0,
  last_fy_index               INTEGER REFERENCES fiscal_year (fy_index),       -- no revenue after this year
  annual_cap                  REAL,
  status                      TEXT NOT NULL CHECK (status IN ('budgeted', 'factsheet', 'none', 'capital', 'proposed')),
  commitment_basis            TEXT NOT NULL CHECK (commitment_basis IN ('formula', 'agreement', 'budget', 'earned', 'onetime', 'none', 'proposed')),
  commitment_note             TEXT,
  contributor_jurisdiction_id TEXT REFERENCES jurisdiction (jurisdiction_id),  -- whose local money it is
  federal_share_cap           REAL CHECK (federal_share_cap IS NULL OR (federal_share_cap > 0 AND federal_share_cap <= 1)),
  federal_share_cap_ada       REAL CHECK (federal_share_cap_ada IS NULL OR (federal_share_cap_ada > 0 AND federal_share_cap_ada <= 1)),
  counts_as_match             INTEGER NOT NULL DEFAULT 1 CHECK (counts_as_match IN (0, 1)),
  match_only                  INTEGER NOT NULL DEFAULT 0 CHECK (match_only IN (0, 1)),  -- non-cash credit
  enabled                     INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),
  purpose                     TEXT,
  match_text                  TEXT,     -- match requirement as written in the sources
  condition_text              TEXT,     -- revenue conditions as written (Revenue %s column B)
  restriction_text            TEXT,     -- restrictions as written on the fact sheet
  notes                       TEXT
);

-- Year-by-year amounts that replace the projection rule for that year.
CREATE TABLE funding_line_year (
  line_id   TEXT NOT NULL REFERENCES funding_line (line_id),
  fy_index  INTEGER NOT NULL REFERENCES fiscal_year (fy_index) CHECK (fy_index > 0),
  amount    REAL NOT NULL CHECK (amount >= 0),
  PRIMARY KEY (line_id, fy_index)
);

-- Eligibility rules. Rows with the same line, type, and strength form one OR set
-- (e.g. state = CA or NV). 'required' rules make a service ineligible; 'preferred' rules raise warnings.
-- value: service_id, agency_id, area class, service type, state ('CA'/'NV'), or jurisdiction_id.
CREATE TABLE eligibility_rule (
  rule_row_id INTEGER PRIMARY KEY,
  line_id     TEXT NOT NULL REFERENCES funding_line (line_id),
  rule_type   TEXT NOT NULL CHECK (rule_type IN ('service', 'agency', 'area_class', 'service_type', 'state', 'jurisdiction_share')),
  strength    TEXT NOT NULL CHECK (strength IN ('required', 'preferred')),
  value       TEXT NOT NULL,
  UNIQUE (line_id, rule_type, strength, value)
);

-- ── FTA 5307 sub-allocation between TTD and Placer County ───────────────────

CREATE TABLE fta_suballocation (
  fy_index               INTEGER PRIMARY KEY REFERENCES fiscal_year (fy_index),
  apportionment_5307     REAL NOT NULL,
  apportionment_5339     REAL,
  apportionment_5310     REAL,
  operations_share       REAL NOT NULL CHECK (operations_share BETWEEN 0 AND 1),
  weight_revenue_miles   REAL NOT NULL DEFAULT 1,
  weight_population      REAL NOT NULL DEFAULT 1,
  weight_ridership       REAL NOT NULL DEFAULT 1
);

CREATE TABLE fta_earned_share_factor (
  agency_id            TEXT PRIMARY KEY REFERENCES agency (agency_id),
  urban_revenue_miles  REAL NOT NULL,
  population           REAL NOT NULL,
  ridership            REAL NOT NULL
);

-- ── Allocation scenarios (how sources are split across services) ───────────

CREATE TABLE allocation_scenario (
  scenario_id   TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  method        TEXT NOT NULL CHECK (method IN ('fixed_shares', 'optimized')),
  description   TEXT
);

-- Per line in a fixed-shares scenario: 'shares' uses allocation_share rows; 'auto' splits the line
-- among eligible services (or allocation_target services) in proportion to auto_basis.
CREATE TABLE allocation_rule (
  scenario_id TEXT NOT NULL REFERENCES allocation_scenario (scenario_id),
  line_id     TEXT NOT NULL REFERENCES funding_line (line_id),
  method      TEXT NOT NULL CHECK (method IN ('shares', 'auto')),
  auto_basis  TEXT CHECK (auto_basis IN ('vsh', 'vsm', 'trips', 'cost', 'equal')),
  PRIMARY KEY (scenario_id, line_id)
);

CREATE TABLE allocation_share (
  scenario_id TEXT NOT NULL REFERENCES allocation_scenario (scenario_id),
  line_id     TEXT NOT NULL REFERENCES funding_line (line_id),
  service_id  TEXT NOT NULL REFERENCES service (service_id),
  share       REAL NOT NULL CHECK (share > 0),
  PRIMARY KEY (scenario_id, line_id, service_id)
);

CREATE TABLE allocation_target (
  scenario_id TEXT NOT NULL REFERENCES allocation_scenario (scenario_id),
  line_id     TEXT NOT NULL REFERENCES funding_line (line_id),
  service_id  TEXT NOT NULL REFERENCES service (service_id),
  PRIMARY KEY (scenario_id, line_id, service_id)
);

-- ── Provenance, agreements, and data issues ─────────────────────────────────

-- One row per source reference behind a value. field names the attribute (amount, prior_year_amount,
-- match, restrictions, allocation, projection, cost, reference_cost, rate, ...).
CREATE TABLE citation (
  citation_id  INTEGER PRIMARY KEY,
  entity_type  TEXT NOT NULL CHECK (entity_type IN ('service', 'operator', 'funding_line', 'fta', 'agreement', 'data_issue')),
  entity_id    TEXT NOT NULL,
  field        TEXT NOT NULL,
  document_id  TEXT REFERENCES source_document (document_id),   -- NULL when the note is not tied to a file
  locator      TEXT NOT NULL                                     -- sheet and cell, or fact sheet card
);

CREATE TABLE agreement (
  agreement_id TEXT PRIMARY KEY,
  title        TEXT NOT NULL,
  description  TEXT
);

CREATE TABLE data_issue (
  issue_id     TEXT PRIMARY KEY,
  title        TEXT NOT NULL,
  description  TEXT NOT NULL
);

-- Edits made in a scenario, for the change log.
CREATE TABLE scenario_change (
  change_id    INTEGER PRIMARY KEY,
  scenario_id  TEXT NOT NULL REFERENCES allocation_scenario (scenario_id),
  changed_at   TEXT NOT NULL,
  entity_type  TEXT NOT NULL,
  entity_id    TEXT NOT NULL,
  field        TEXT NOT NULL,
  old_value    TEXT,
  new_value    TEXT
);

CREATE INDEX ix_citation_entity ON citation (entity_type, entity_id);
CREATE INDEX ix_rule_line ON eligibility_rule (line_id);
CREATE INDEX ix_service_agency ON service (agency_id);
CREATE INDEX ix_line_recipient ON funding_line (recipient_agency_id);
