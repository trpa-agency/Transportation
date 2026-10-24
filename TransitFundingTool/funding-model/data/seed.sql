BEGIN TRANSACTION;
CREATE TABLE agency (
  agency_id     TEXT PRIMARY KEY,                -- receiving or operating agency
  name          TEXT NOT NULL,
  short_name    TEXT NOT NULL
);
INSERT INTO "agency" VALUES('TTD','Tahoe Transportation District','TTD');
INSERT INTO "agency" VALUES('SSTMA','South Shore TMA (Lake Link)','Lake Link');
INSERT INTO "agency" VALUES('TART','Placer County TART','TART');
INSERT INTO "agency" VALUES('TNTTMA','Truckee North Tahoe TMA','TNT/TMA');
INSERT INTO "agency" VALUES('REGION','Regional or new (not yet assigned)','Regional');
CREATE TABLE agreement (
  agreement_id TEXT PRIMARY KEY,
  title        TEXT NOT NULL,
  description  TEXT
);
INSERT INTO "agreement" VALUES('AG-01','Lake Link funding agreements with Douglas County and the City of South Lake Tahoe','The only two written Lake Link contracts. The plan assumes support continues at existing levels after the current terms end.');
INSERT INTO "agreement" VALUES('AG-02','SSTMA operating contract for Lake Link (Downtowner/Via)','Sets the Lake Link hourly cost and the 2027 contract service hours.');
INSERT INTO "agreement" VALUES('AG-03','Emerald Bay Shuttle (Route 30) pilot: TTD–Via contract and pilot funding','Keep Tahoe Blue, Carbon Reduction Program, El Dorado County, and Placer County funds committed through FY 27-28.');
INSERT INTO "agreement" VALUES('AG-04','Placer County TART Connect contract','Contract-specified escalation of 5 percent per year.');
INSERT INTO "agreement" VALUES('AG-05','My Ride to Work contracts with TART and TNT/TMA','Bus and van rates for Park & Ride shuttles and NLTE; the MRTW contract is listed at $488,320.');
INSERT INTO "agreement" VALUES('AG-06','FTA 5307, 5339, and 5310 sub-allocation between TTD and Placer County','Earned-share worksheet based on revenue miles, population, and ridership. FTA expects the MPO and designated recipients to set the split through a "fair and rational" process.');
INSERT INTO "agreement" VALUES('AG-07','TRPA TDA apportionment (LTF and STA) to TTD and TART','The plan assumes no change in the TRPA TDA split; TTD applies one-third to rural and two-thirds to urban routes.');
INSERT INTO "agreement" VALUES('AG-08','LCTOP rotation between TTD and TART','LCTOP alternates every other year based on ridership.');
INSERT INTO "agreement" VALUES('AG-09','NDOT 5311 subrecipient agreement with TTD','Partner notes record NDOT match at 20 percent for administration, 40 percent for operating, and 5 percent for capital.');
INSERT INTO "agreement" VALUES('AG-10','Tahoe Blue Events Center transportation mitigation fee','A $3 ticket surcharge allocated to transit, with an annual attendee cap.');
INSERT INTO "agreement" VALUES('AG-11','Partner cost-sharing practices on TTD routes','Costs are allocated by route by percent of miles per month, utility costs are pooled systemwide by partner agreement, and whoever receives a route''s benefit gets its urban or rural benefit.');
INSERT INTO "agreement" VALUES('AG-12','Lake Link private partners','SLTTID, Heavenly, Caesars, Round Hill Pines, Advance Learning, LTVA, and LTCC contributed in FY 25-26 with no FY 26-27 commitment.');
CREATE TABLE allocation_rule (
  scenario_id TEXT NOT NULL REFERENCES allocation_scenario (scenario_id),
  line_id     TEXT NOT NULL REFERENCES funding_line (line_id),
  method      TEXT NOT NULL CHECK (method IN ('shares', 'auto')),
  auto_basis  TEXT CHECK (auto_basis IN ('vsh', 'vsm', 'trips', 'cost', 'equal')),
  PRIMARY KEY (scenario_id, line_id)
);
INSERT INTO "allocation_rule" VALUES('draft','ttd-5307','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','ttd-5307cmaq','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','ttd-5307co','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','ttd-5311nv','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','ttd-5310','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','ttd-5310co','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','ttd-ltf','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','ttd-sta','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','ttd-lctop','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','ttd-elec','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','ttd-sb125','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','ttd-nvparks','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','ttd-nvstate','auto','vsh');
INSERT INTO "allocation_rule" VALUES('draft','ttd-localapp','auto','vsh');
INSERT INTO "allocation_rule" VALUES('draft','ttd-tdva','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','ttd-interest','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','ttd-ktb','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','ttd-crp','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','ttd-eldebs','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','ttd-plaebs','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','ttd-fares30','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','ll-sb125','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','ll-douglas','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','ll-cslt','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','ll-tahoeblue','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','ll-slttid','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','ll-heavenly','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','ll-caesars','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','ll-roundhill','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','ll-advlearn','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','ll-ltva','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','ll-ltcc','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','tart-5307','auto','vsh');
INSERT INTO "allocation_rule" VALUES('draft','tart-5310','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','tart-5311ca','auto','vsh');
INSERT INTO "allocation_rule" VALUES('draft','tart-ltf-trpa','auto','vsh');
INSERT INTO "allocation_rule" VALUES('draft','tart-ltf-pctpa','auto','vsh');
INSERT INTO "allocation_rule" VALUES('draft','tart-sta-trpa','auto','vsh');
INSERT INTO "allocation_rule" VALUES('draft','tart-sta-pctpa','auto','vsh');
INSERT INTO "allocation_rule" VALUES('draft','tart-sgr','auto','vsh');
INSERT INTO "allocation_rule" VALUES('draft','tart-tot-tc','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','tart-tot-fr','auto','vsh');
INSERT INTO "allocation_rule" VALUES('draft','tart-washoe','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','tart-truckee','auto','vsh');
INSERT INTO "allocation_rule" VALUES('draft','tart-nsrp','auto','vsh');
INSERT INTO "allocation_rule" VALUES('draft','tart-nslp','auto','vsh');
INSERT INTO "allocation_rule" VALUES('draft','tart-martis','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','tnt-tot-nlte','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','tnt-tot-pr','auto','vsh');
INSERT INTO "allocation_rule" VALUES('draft','tnt-tot-van','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','tnt-tntn','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','tnt-washoe','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','tnt-rtaa','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','tnt-truckee','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','tnt-truckee2','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','tnt-nevco','auto','vsh');
INSERT INTO "allocation_rule" VALUES('draft','tnt-northstar','auto','vsh');
INSERT INTO "allocation_rule" VALUES('draft','tnt-palisades','auto','vsh');
INSERT INTO "allocation_rule" VALUES('draft','tnt-ntca','auto','vsh');
INSERT INTO "allocation_rule" VALUES('draft','tnt-fares','shares',NULL);
INSERT INTO "allocation_rule" VALUES('draft','tnt-reserve','shares',NULL);
CREATE TABLE allocation_scenario (
  scenario_id   TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  method        TEXT NOT NULL CHECK (method IN ('fixed_shares', 'optimized')),
  description   TEXT
);
INSERT INTO "allocation_scenario" VALUES('draft','Consultant draft shares','fixed_shares','Shares from Financial PlanG Revenue %s; sources the draft left unallocated are split by service hours as placeholders.');
INSERT INTO "allocation_scenario" VALUES('optimized','Rules-based optimized allocation','optimized','The engine allocates every source to maximize funded service subject to all required rules, federal share caps, and match.');
CREATE TABLE allocation_share (
  scenario_id TEXT NOT NULL REFERENCES allocation_scenario (scenario_id),
  line_id     TEXT NOT NULL REFERENCES funding_line (line_id),
  service_id  TEXT NOT NULL REFERENCES service (service_id),
  share       REAL NOT NULL CHECK (share > 0),
  PRIMARY KEY (scenario_id, line_id, service_id)
);
INSERT INTO "allocation_share" VALUES('draft','ttd-5307','28',4.229383567917443382e-02);
INSERT INTO "allocation_share" VALUES('draft','ttd-5307','50',5.150124315394017938e-01);
INSERT INTO "allocation_share" VALUES('draft','ttd-5307','55',2.024812214318355841e-01);
INSERT INTO "allocation_share" VALUES('draft','ttd-5307','51',6.151125712848622488e-03);
INSERT INTO "allocation_share" VALUES('draft','ttd-5307','ADA-TTD',2.340613856367397272e-01);
INSERT INTO "allocation_share" VALUES('draft','ttd-5307cmaq','50',0.368122);
INSERT INTO "allocation_share" VALUES('draft','ttd-5307cmaq','55',0.295802);
INSERT INTO "allocation_share" VALUES('draft','ttd-5307cmaq','ADA-TTD',0.336076);
INSERT INTO "allocation_share" VALUES('draft','ttd-5307co','50',0.368122);
INSERT INTO "allocation_share" VALUES('draft','ttd-5307co','55',0.295802);
INSERT INTO "allocation_share" VALUES('draft','ttd-5307co','ADA-TTD',0.336076);
INSERT INTO "allocation_share" VALUES('draft','ttd-5311nv','19X',3.39211981000285101e-01);
INSERT INTO "allocation_share" VALUES('draft','ttd-5311nv','22',6.607880189997148434e-01);
INSERT INTO "allocation_share" VALUES('draft','ttd-5310','ADA-TTD',1.0);
INSERT INTO "allocation_share" VALUES('draft','ttd-5310co','ADA-TTD',1.0);
INSERT INTO "allocation_share" VALUES('draft','ttd-ltf','19X',1.16046049937567869e-01);
INSERT INTO "allocation_share" VALUES('draft','ttd-ltf','22',2.260494520132803886e-01);
INSERT INTO "allocation_share" VALUES('draft','ttd-ltf','28',0.000379024230270383);
INSERT INTO "allocation_share" VALUES('draft','ttd-ltf','50',3.542112896979253689e-01);
INSERT INTO "allocation_share" VALUES('draft','ttd-ltf','55',1.692836788071976073e-01);
INSERT INTO "allocation_share" VALUES('draft','ttd-ltf','51',1.162812952400116284e-02);
INSERT INTO "allocation_share" VALUES('draft','ttd-ltf','ADA-TTD',1.224023757897571563e-01);
INSERT INTO "allocation_share" VALUES('draft','ttd-sta','19X',1.16046049937567869e-01);
INSERT INTO "allocation_share" VALUES('draft','ttd-sta','22',2.260494520132803886e-01);
INSERT INTO "allocation_share" VALUES('draft','ttd-sta','28',0.000379024230270383);
INSERT INTO "allocation_share" VALUES('draft','ttd-sta','50',3.542112896979253689e-01);
INSERT INTO "allocation_share" VALUES('draft','ttd-sta','55',1.692836788071976073e-01);
INSERT INTO "allocation_share" VALUES('draft','ttd-sta','51',1.162812952400116284e-02);
INSERT INTO "allocation_share" VALUES('draft','ttd-sta','ADA-TTD',1.224023757897571563e-01);
INSERT INTO "allocation_share" VALUES('draft','ttd-lctop','19X',6.993272114234218296e-02);
INSERT INTO "allocation_share" VALUES('draft','ttd-lctop','22',1.370313398281514661e-01);
INSERT INTO "allocation_share" VALUES('draft','ttd-lctop','28',3.706396929722338696e-02);
INSERT INTO "allocation_share" VALUES('draft','ttd-lctop','50',2.926894451436473644e-01);
INSERT INTO "allocation_share" VALUES('draft','ttd-lctop','55',2.893829922776923191e-01);
INSERT INTO "allocation_share" VALUES('draft','ttd-lctop','51',5.189639366677542727e-03);
INSERT INTO "allocation_share" VALUES('draft','ttd-lctop','ADA-TTD',1.687098929442657492e-01);
INSERT INTO "allocation_share" VALUES('draft','ttd-elec','19X',1.141709171720364513e-01);
INSERT INTO "allocation_share" VALUES('draft','ttd-elec','22',2.250593364676135578e-01);
INSERT INTO "allocation_share" VALUES('draft','ttd-elec','28',3.076817731070858112e-02);
INSERT INTO "allocation_share" VALUES('draft','ttd-elec','50',3.069142915275666072e-01);
INSERT INTO "allocation_share" VALUES('draft','ttd-elec','55',1.702517353772001474e-01);
INSERT INTO "allocation_share" VALUES('draft','ttd-elec','51',2.153657270410683222e-02);
INSERT INTO "allocation_share" VALUES('draft','ttd-elec','ADA-TTD',1.312989694407680486e-01);
INSERT INTO "allocation_share" VALUES('draft','ttd-sb125','50',5.258405599999999013e-01);
INSERT INTO "allocation_share" VALUES('draft','ttd-sb125','55',4.24914820000000082e-01);
INSERT INTO "allocation_share" VALUES('draft','ttd-sb125','51',4.924462000000001672e-02);
INSERT INTO "allocation_share" VALUES('draft','ttd-nvparks','28',1.0);
INSERT INTO "allocation_share" VALUES('draft','ttd-tdva','51',1.0);
INSERT INTO "allocation_share" VALUES('draft','ttd-interest','19X',6.993272114234218296e-02);
INSERT INTO "allocation_share" VALUES('draft','ttd-interest','22',1.370313398281514661e-01);
INSERT INTO "allocation_share" VALUES('draft','ttd-interest','28',3.706396929722338696e-02);
INSERT INTO "allocation_share" VALUES('draft','ttd-interest','50',2.926894451436473644e-01);
INSERT INTO "allocation_share" VALUES('draft','ttd-interest','55',2.893829922776923191e-01);
INSERT INTO "allocation_share" VALUES('draft','ttd-interest','51',5.189639366677542727e-03);
INSERT INTO "allocation_share" VALUES('draft','ttd-interest','ADA-TTD',1.687098929442657492e-01);
INSERT INTO "allocation_share" VALUES('draft','ttd-ktb','30',1.0);
INSERT INTO "allocation_share" VALUES('draft','ttd-crp','30',1.0);
INSERT INTO "allocation_share" VALUES('draft','ttd-eldebs','30',1.0);
INSERT INTO "allocation_share" VALUES('draft','ttd-plaebs','30',1.0);
INSERT INTO "allocation_share" VALUES('draft','ttd-fares30','30',1.0);
INSERT INTO "allocation_share" VALUES('draft','ll-sb125','LL',1.0);
INSERT INTO "allocation_share" VALUES('draft','ll-douglas','LL',1.0);
INSERT INTO "allocation_share" VALUES('draft','ll-cslt','LL',1.0);
INSERT INTO "allocation_share" VALUES('draft','ll-tahoeblue','LL',1.0);
INSERT INTO "allocation_share" VALUES('draft','ll-slttid','LL',1.0);
INSERT INTO "allocation_share" VALUES('draft','ll-heavenly','LL',1.0);
INSERT INTO "allocation_share" VALUES('draft','ll-caesars','LL',1.0);
INSERT INTO "allocation_share" VALUES('draft','ll-roundhill','LL',1.0);
INSERT INTO "allocation_share" VALUES('draft','ll-advlearn','LL',1.0);
INSERT INTO "allocation_share" VALUES('draft','ll-ltva','LL',1.0);
INSERT INTO "allocation_share" VALUES('draft','ll-ltcc','LL',1.0);
INSERT INTO "allocation_share" VALUES('draft','tart-5310','ADA-PLA',1.0);
INSERT INTO "allocation_share" VALUES('draft','tart-tot-tc','TC',1.0);
INSERT INTO "allocation_share" VALUES('draft','tart-washoe','TART-NV',1.0);
INSERT INTO "allocation_share" VALUES('draft','tart-martis','267',1.0);
INSERT INTO "allocation_share" VALUES('draft','tnt-tot-nlte','NLTE',1.0);
INSERT INTO "allocation_share" VALUES('draft','tnt-tot-van','VAN',1.0);
INSERT INTO "allocation_share" VALUES('draft','tnt-tntn','NLTE',1.0);
INSERT INTO "allocation_share" VALUES('draft','tnt-washoe','NLTE',1.0);
INSERT INTO "allocation_share" VALUES('draft','tnt-rtaa','NLTE',1.0);
INSERT INTO "allocation_share" VALUES('draft','tnt-truckee','NLTE',1.0);
INSERT INTO "allocation_share" VALUES('draft','tnt-truckee2','NLTE',1.0);
INSERT INTO "allocation_share" VALUES('draft','tnt-fares','NLTE',1.0);
INSERT INTO "allocation_share" VALUES('draft','tnt-reserve','NLTE',1.0);
CREATE TABLE allocation_target (
  scenario_id TEXT NOT NULL REFERENCES allocation_scenario (scenario_id),
  line_id     TEXT NOT NULL REFERENCES funding_line (line_id),
  service_id  TEXT NOT NULL REFERENCES service (service_id),
  PRIMARY KEY (scenario_id, line_id, service_id)
);
INSERT INTO "allocation_target" VALUES('draft','tart-5307','TART-WS');
INSERT INTO "allocation_target" VALUES('draft','tart-5307','TART-NS');
INSERT INTO "allocation_target" VALUES('draft','tart-5307','TART-NV');
INSERT INTO "allocation_target" VALUES('draft','tart-5307','89');
INSERT INTO "allocation_target" VALUES('draft','tart-5307','267');
INSERT INTO "allocation_target" VALUES('draft','tart-5307','NIGHT');
INSERT INTO "allocation_target" VALUES('draft','tart-5307','ADA-PLA');
INSERT INTO "allocation_target" VALUES('draft','tart-ltf-trpa','TART-WS');
INSERT INTO "allocation_target" VALUES('draft','tart-ltf-trpa','TART-NS');
INSERT INTO "allocation_target" VALUES('draft','tart-ltf-trpa','89');
INSERT INTO "allocation_target" VALUES('draft','tart-ltf-trpa','267');
INSERT INTO "allocation_target" VALUES('draft','tart-ltf-trpa','NIGHT');
INSERT INTO "allocation_target" VALUES('draft','tart-ltf-trpa','ADA-PLA');
INSERT INTO "allocation_target" VALUES('draft','tart-ltf-pctpa','TART-WS');
INSERT INTO "allocation_target" VALUES('draft','tart-ltf-pctpa','TART-NS');
INSERT INTO "allocation_target" VALUES('draft','tart-ltf-pctpa','89');
INSERT INTO "allocation_target" VALUES('draft','tart-ltf-pctpa','267');
INSERT INTO "allocation_target" VALUES('draft','tart-ltf-pctpa','NIGHT');
INSERT INTO "allocation_target" VALUES('draft','tart-ltf-pctpa','ADA-PLA');
INSERT INTO "allocation_target" VALUES('draft','tart-sta-trpa','TART-WS');
INSERT INTO "allocation_target" VALUES('draft','tart-sta-trpa','TART-NS');
INSERT INTO "allocation_target" VALUES('draft','tart-sta-trpa','89');
INSERT INTO "allocation_target" VALUES('draft','tart-sta-trpa','267');
INSERT INTO "allocation_target" VALUES('draft','tart-sta-trpa','NIGHT');
INSERT INTO "allocation_target" VALUES('draft','tart-sta-trpa','ADA-PLA');
INSERT INTO "allocation_target" VALUES('draft','tart-sta-pctpa','TART-WS');
INSERT INTO "allocation_target" VALUES('draft','tart-sta-pctpa','TART-NS');
INSERT INTO "allocation_target" VALUES('draft','tart-sta-pctpa','89');
INSERT INTO "allocation_target" VALUES('draft','tart-sta-pctpa','267');
INSERT INTO "allocation_target" VALUES('draft','tart-sta-pctpa','NIGHT');
INSERT INTO "allocation_target" VALUES('draft','tart-sta-pctpa','ADA-PLA');
INSERT INTO "allocation_target" VALUES('draft','tart-sgr','TART-WS');
INSERT INTO "allocation_target" VALUES('draft','tart-sgr','TART-NS');
INSERT INTO "allocation_target" VALUES('draft','tart-sgr','89');
INSERT INTO "allocation_target" VALUES('draft','tart-sgr','267');
INSERT INTO "allocation_target" VALUES('draft','tart-sgr','NIGHT');
INSERT INTO "allocation_target" VALUES('draft','tart-sgr','ADA-PLA');
INSERT INTO "allocation_target" VALUES('draft','tart-tot-fr','TART-WS');
INSERT INTO "allocation_target" VALUES('draft','tart-tot-fr','TART-NS');
INSERT INTO "allocation_target" VALUES('draft','tart-tot-fr','89');
INSERT INTO "allocation_target" VALUES('draft','tart-tot-fr','267');
INSERT INTO "allocation_target" VALUES('draft','tart-tot-fr','NIGHT');
INSERT INTO "allocation_target" VALUES('draft','tart-tot-fr','ADA-PLA');
INSERT INTO "allocation_target" VALUES('draft','tart-truckee','89');
INSERT INTO "allocation_target" VALUES('draft','tart-truckee','267');
INSERT INTO "allocation_target" VALUES('draft','tart-nsrp','TART-WS');
INSERT INTO "allocation_target" VALUES('draft','tart-nsrp','TART-NS');
INSERT INTO "allocation_target" VALUES('draft','tart-nsrp','TART-NV');
INSERT INTO "allocation_target" VALUES('draft','tart-nsrp','89');
INSERT INTO "allocation_target" VALUES('draft','tart-nsrp','267');
INSERT INTO "allocation_target" VALUES('draft','tart-nsrp','NIGHT');
INSERT INTO "allocation_target" VALUES('draft','tart-nslp','TART-WS');
INSERT INTO "allocation_target" VALUES('draft','tart-nslp','TART-NS');
INSERT INTO "allocation_target" VALUES('draft','tart-nslp','TART-NV');
INSERT INTO "allocation_target" VALUES('draft','tart-nslp','89');
INSERT INTO "allocation_target" VALUES('draft','tart-nslp','267');
INSERT INTO "allocation_target" VALUES('draft','tart-nslp','NIGHT');
INSERT INTO "allocation_target" VALUES('draft','tnt-tot-pr','PR-W');
INSERT INTO "allocation_target" VALUES('draft','tnt-tot-pr','PR-S');
INSERT INTO "allocation_target" VALUES('draft','tnt-nevco','PR-W');
INSERT INTO "allocation_target" VALUES('draft','tnt-nevco','PR-S');
INSERT INTO "allocation_target" VALUES('draft','tnt-northstar','PR-W');
INSERT INTO "allocation_target" VALUES('draft','tnt-northstar','PR-S');
INSERT INTO "allocation_target" VALUES('draft','tnt-palisades','PR-W');
INSERT INTO "allocation_target" VALUES('draft','tnt-palisades','PR-S');
INSERT INTO "allocation_target" VALUES('draft','tnt-ntca','PR-W');
INSERT INTO "allocation_target" VALUES('draft','tnt-ntca','PR-S');
CREATE TABLE citation (
  citation_id  INTEGER PRIMARY KEY,
  entity_type  TEXT NOT NULL CHECK (entity_type IN ('service', 'operator', 'funding_line', 'fta', 'agreement', 'data_issue')),
  entity_id    TEXT NOT NULL,
  field        TEXT NOT NULL,
  document_id  TEXT REFERENCES source_document (document_id),   -- NULL when the note is not tied to a file
  locator      TEXT NOT NULL                                     -- sheet and cell, or fact sheet card
);
INSERT INTO "citation" VALUES(1,'operator','TTD','rate','scen','VRH Rates J7, L7');
INSERT INTO "citation" VALUES(2,'operator','Via','rate','scen','VRH Rates J9, L9');
INSERT INTO "citation" VALUES(3,'operator','TART','rate','scen','VRH Rates J14, L14');
INSERT INTO "citation" VALUES(4,'operator','Placer Via','rate','scen','VRH Rates J15, L15');
INSERT INTO "citation" VALUES(5,'operator','Truckee','rate','scen','VRH Rates J16, L16');
INSERT INTO "citation" VALUES(6,'operator','MRTW','rate','scen','VRH Rates J20, L20; costs X35');
INSERT INTO "citation" VALUES(7,'operator','BUDGET','rate','plan','T2-4 O1 (4% general escalator)');
INSERT INTO "citation" VALUES(8,'service','19X','cost','scen','costs row 4');
INSERT INTO "citation" VALUES(9,'service','19X','reference_cost','plan','T2-4 A1 TTD LL Costs G142 (route cost incl. allocated fixed cost)');
INSERT INTO "citation" VALUES(10,'service','22','cost','scen','costs row 5');
INSERT INTO "citation" VALUES(11,'service','22','reference_cost','plan','T2-4 A1 TTD LL Costs G151 (route cost incl. allocated fixed cost)');
INSERT INTO "citation" VALUES(12,'service','28','cost','scen','costs row 6');
INSERT INTO "citation" VALUES(13,'service','28','reference_cost','plan','T2-4 A1 TTD LL Costs G160 (route cost incl. allocated fixed cost)');
INSERT INTO "citation" VALUES(14,'service','30','cost','scen','costs row 7');
INSERT INTO "citation" VALUES(15,'service','30','reference_cost','plan','T2-4 A1 TTD LL Costs G169 (route cost incl. allocated fixed cost)');
INSERT INTO "citation" VALUES(16,'service','30','reference_cost','plan','T2-4 Table 2 row 20');
INSERT INTO "citation" VALUES(17,'service','50','cost','scen','costs row 8');
INSERT INTO "citation" VALUES(18,'service','50','reference_cost','plan','T2-4 A1 TTD LL Costs G175 (route cost incl. allocated fixed cost)');
INSERT INTO "citation" VALUES(19,'service','51','cost','scen','costs row 9');
INSERT INTO "citation" VALUES(20,'service','51','reference_cost','plan','T2-4 A1 TTD LL Costs G186 (route cost incl. allocated fixed cost)');
INSERT INTO "citation" VALUES(21,'service','55','cost','scen','costs row 10');
INSERT INTO "citation" VALUES(22,'service','55','reference_cost','plan','T2-4 A1 TTD LL Costs G196 (route cost incl. allocated fixed cost)');
INSERT INTO "citation" VALUES(23,'service','ADA-TTD','cost','scen','costs row 11');
INSERT INTO "citation" VALUES(24,'service','ADA-TTD','reference_cost','plan','T2-4 A1 TTD LL Costs G206 (route cost incl. allocated fixed cost)');
INSERT INTO "citation" VALUES(25,'service','LL','cost','scen','costs row 12');
INSERT INTO "citation" VALUES(26,'service','LL','reference_cost','plan','T2-4 G26 (contract plus fixed costs)');
INSERT INTO "citation" VALUES(27,'service','TART-WS','cost','scen','costs row 13');
INSERT INTO "citation" VALUES(28,'service','TART-NS','cost','scen','costs row 14');
INSERT INTO "citation" VALUES(29,'service','TART-NV','cost','scen','costs row 15');
INSERT INTO "citation" VALUES(30,'service','89','cost','scen','costs row 17');
INSERT INTO "citation" VALUES(31,'service','267','cost','scen','costs row 18');
INSERT INTO "citation" VALUES(32,'service','NIGHT','cost','scen','costs row 19');
INSERT INTO "citation" VALUES(33,'service','ADA-PLA','cost','scen','costs row 20');
INSERT INTO "citation" VALUES(34,'service','TC','cost','scen','costs row 21');
INSERT INTO "citation" VALUES(35,'service','TC','reference_cost','plan','T5-7 G26');
INSERT INTO "citation" VALUES(36,'service','PR-W','cost','scen','costs row 22');
INSERT INTO "citation" VALUES(37,'service','PR-W','reference_cost','plan','TNTTMA $ F43 (winter and summer combined)');
INSERT INTO "citation" VALUES(38,'service','PR-S','cost','scen','costs row 23');
INSERT INTO "citation" VALUES(39,'service','NLTE','cost','scen','costs row 24');
INSERT INTO "citation" VALUES(40,'service','NLTE','reference_cost','plan','TNTTMA $ F22');
INSERT INTO "citation" VALUES(41,'service','VAN','cost','plan','TNTTMA $ K36:K43');
INSERT INTO "citation" VALUES(42,'service','VAN','reference_cost','plan','TNTTMA $ K43');
INSERT INTO "citation" VALUES(43,'service','SP-US50','cost','plan','T2-4 row 29');
INSERT INTO "citation" VALUES(44,'service','SP-28','cost','plan','T2-4 row 30');
INSERT INTO "citation" VALUES(45,'service','SP-EBS','cost','plan','T2-4 row 31');
INSERT INTO "citation" VALUES(46,'service','SP-MEY','cost','plan','T2-4 row 32');
INSERT INTO "citation" VALUES(47,'service','SP-LTCC','cost','plan','T2-4 row 33');
INSERT INTO "citation" VALUES(48,'service','SP-INC','cost','plan','T5-7 row 36');
INSERT INTO "citation" VALUES(49,'service','SP-VAN','cost','plan','T5-7 row 37');
INSERT INTO "citation" VALUES(50,'funding_line','ttd-5307','allocation','plan','Revenue %s row 3 (TTD FY 24-25 route allocations, Actual Revenues row 3)');
INSERT INTO "citation" VALUES(51,'funding_line','ttd-5307','amount','plan','Per Route Model D12 = FTA Allocation Split (26-27) G34 (75% of TTD earned share)');
INSERT INTO "citation" VALUES(52,'funding_line','ttd-5307','prior_year_amount','fed','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(53,'funding_line','ttd-5307','match','plan','Revenue %s row 3 C3, AE3');
INSERT INTO "citation" VALUES(54,'funding_line','ttd-5307','restrictions','fed','FTA 5307');
INSERT INTO "citation" VALUES(55,'funding_line','ttd-5307','projection','plan','T2-4 Table A1 O60: 1% increase annually');
INSERT INTO "citation" VALUES(56,'funding_line','ttd-5307cmaq','allocation','plan','Revenue %s row 4 (TTD FY 24-25 CMAQ route allocations, Actual Revenues row 4)');
INSERT INTO "citation" VALUES(57,'funding_line','ttd-5307cmaq','amount','plan','Per Route Model D13');
INSERT INTO "citation" VALUES(58,'funding_line','ttd-5307cmaq','amount','plan','T2-4 Table A1 G61');
INSERT INTO "citation" VALUES(59,'funding_line','ttd-5307cmaq','match','plan','Revenue %s row 4 C4');
INSERT INTO "citation" VALUES(60,'funding_line','ttd-5307cmaq','projection','plan','T2-4 Table A1 O61: 1% increase annually');
INSERT INTO "citation" VALUES(61,'funding_line','ttd-5307co','allocation','plan','Revenue %s row 5');
INSERT INTO "citation" VALUES(62,'funding_line','ttd-5307co','amount','plan','Per Route Model D14');
INSERT INTO "citation" VALUES(63,'funding_line','ttd-5307co','amount','plan','T2-4 Table A1 G62');
INSERT INTO "citation" VALUES(64,'funding_line','ttd-5307co','match','plan','Revenue %s row 5 C5');
INSERT INTO "citation" VALUES(65,'funding_line','ttd-5307co','projection','plan','T1 Summary Table M32');
INSERT INTO "citation" VALUES(66,'funding_line','ttd-5311nv','allocation','plan','Revenue %s row 6');
INSERT INTO "citation" VALUES(67,'funding_line','ttd-5311nv','amount','plan','Per Route Model D15');
INSERT INTO "citation" VALUES(68,'funding_line','ttd-5311nv','amount','plan','T2-4 Table A1 G65');
INSERT INTO "citation" VALUES(69,'funding_line','ttd-5311nv','prior_year_amount','fed','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(70,'funding_line','ttd-5311nv','match','plan','Revenue %s row 6 B6, C6');
INSERT INTO "citation" VALUES(71,'funding_line','ttd-5311nv','restrictions','fed','FTA 5311 (NV DOT)');
INSERT INTO "citation" VALUES(72,'funding_line','ttd-5311nv','projection','plan','T2-4 Table A1 O65: 1% increase yearly');
INSERT INTO "citation" VALUES(73,'funding_line','ttd-5310','allocation','plan','Revenue %s row 8');
INSERT INTO "citation" VALUES(74,'funding_line','ttd-5310','amount','plan','T2-4 Table A1 G63:K63');
INSERT INTO "citation" VALUES(75,'funding_line','ttd-5310','amount','plan','Per Route Model D17');
INSERT INTO "citation" VALUES(76,'funding_line','ttd-5310','prior_year_amount','fed','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(77,'funding_line','ttd-5310','match','plan','Revenue %s row 8 B8, C8');
INSERT INTO "citation" VALUES(78,'funding_line','ttd-5310','restrictions','fed','FTA 5310');
INSERT INTO "citation" VALUES(79,'funding_line','ttd-5310','projection','plan','T2-4 Table A1 H63, J63');
INSERT INTO "citation" VALUES(80,'funding_line','ttd-5310co','allocation','plan','Revenue %s row 9');
INSERT INTO "citation" VALUES(81,'funding_line','ttd-5310co','amount','plan','Per Route Model D18');
INSERT INTO "citation" VALUES(82,'funding_line','ttd-5310co','amount','plan','T2-4 Table A1 G64');
INSERT INTO "citation" VALUES(83,'funding_line','ttd-5310co','match','plan','Revenue %s row 9');
INSERT INTO "citation" VALUES(84,'funding_line','ttd-ltf','allocation','plan','Revenue %s row 10 (TTD FY 24-25 TDA route allocations, Actual Revenues row 10)');
INSERT INTO "citation" VALUES(85,'funding_line','ttd-ltf','amount','plan','T2-4 Table A1 G66 (Per Route Model D19 holds the rural one-third of LTF plus STA, $615,042, under this label)');
INSERT INTO "citation" VALUES(86,'funding_line','ttd-ltf','prior_year_amount','state','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(87,'funding_line','ttd-ltf','match','plan','Revenue %s row 10 B10, C10');
INSERT INTO "citation" VALUES(88,'funding_line','ttd-ltf','restrictions','state','Local Transportation Funds (LTF)');
INSERT INTO "citation" VALUES(89,'funding_line','ttd-ltf','projection','plan','T2-4 Table A1 note 2: RTP projected population change, 0.025% per year');
INSERT INTO "citation" VALUES(90,'funding_line','ttd-sta','allocation','plan','Revenue %s row 12');
INSERT INTO "citation" VALUES(91,'funding_line','ttd-sta','amount','plan','T2-4 Table A1 G67 (Per Route Model D21 holds the urban two-thirds of LTF plus STA, $1,230,085, under this label)');
INSERT INTO "citation" VALUES(92,'funding_line','ttd-sta','prior_year_amount','state','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(93,'funding_line','ttd-sta','match','plan','Revenue %s row 12');
INSERT INTO "citation" VALUES(94,'funding_line','ttd-sta','restrictions','state','State Transportation Assistance (STA)');
INSERT INTO "citation" VALUES(95,'funding_line','ttd-sta','projection','plan','T2-4 Table A1 note 2');
INSERT INTO "citation" VALUES(96,'funding_line','ttd-lctop','allocation','plan','Revenue %s row 15: share of TTD service hours on the V1G basis that leaves out Route 30 so shares sum to 100%; the draft assigns shares to Nevada routes 19X, 22, and 28');
INSERT INTO "citation" VALUES(97,'funding_line','ttd-lctop','amount','plan','Per Route Model D24');
INSERT INTO "citation" VALUES(98,'funding_line','ttd-lctop','amount','plan','T2-4 Table A1 G73:K73');
INSERT INTO "citation" VALUES(99,'funding_line','ttd-lctop','prior_year_amount','state','LCTOP (used for capital, FY 25-26)');
INSERT INTO "citation" VALUES(100,'funding_line','ttd-lctop','match','plan','Revenue %s row 15');
INSERT INTO "citation" VALUES(101,'funding_line','ttd-lctop','restrictions','state','LCTOP: "CA only"');
INSERT INTO "citation" VALUES(102,'funding_line','ttd-lctop','projection','plan','T2-4 Table A1 O73: TTD gets every other year');
INSERT INTO "citation" VALUES(103,'funding_line','ttd-elec','allocation','plan','Revenue %s row 16');
INSERT INTO "citation" VALUES(104,'funding_line','ttd-elec','amount','plan','Per Route Model D25');
INSERT INTO "citation" VALUES(105,'funding_line','ttd-elec','amount','plan','T2-4 Table A1 G74');
INSERT INTO "citation" VALUES(106,'funding_line','ttd-elec','prior_year_amount','state','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(107,'funding_line','ttd-elec','match','plan','Revenue %s row 16 B16, C16');
INSERT INTO "citation" VALUES(108,'funding_line','ttd-sb125','allocation','plan','Revenue %s row 17');
INSERT INTO "citation" VALUES(109,'funding_line','ttd-sb125','amount','plan','Per Route Model D26');
INSERT INTO "citation" VALUES(110,'funding_line','ttd-sb125','amount','plan','T2-4 Table A1 G75');
INSERT INTO "citation" VALUES(111,'funding_line','ttd-sb125','prior_year_amount','state','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(112,'funding_line','ttd-sb125','match','plan','Revenue %s row 17');
INSERT INTO "citation" VALUES(113,'funding_line','ttd-sb125','restrictions','state','SB 125 Operating');
INSERT INTO "citation" VALUES(114,'funding_line','ttd-sb125','projection','plan','T2-4 Table A1 H75:K75 = 0');
INSERT INTO "citation" VALUES(115,'funding_line','ttd-nvparks','allocation','plan','Revenue %s row 18');
INSERT INTO "citation" VALUES(116,'funding_line','ttd-nvparks','amount','plan','Per Route Model D27');
INSERT INTO "citation" VALUES(117,'funding_line','ttd-nvparks','amount','plan','T2-4 Table A1 G76');
INSERT INTO "citation" VALUES(118,'funding_line','ttd-nvparks','prior_year_amount','loc1','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(119,'funding_line','ttd-nvparks','match','plan','Revenue %s row 18');
INSERT INTO "citation" VALUES(120,'funding_line','ttd-nvparks','restrictions','loc1','Nevada State Parks');
INSERT INTO "citation" VALUES(121,'funding_line','ttd-nvparks','projection','plan','T2-4 Table A1 note 4: no annual change');
INSERT INTO "citation" VALUES(122,'funding_line','ttd-nvstate','amount',NULL,'Not in Financial PlanG FY 26-27 tables');
INSERT INTO "citation" VALUES(123,'funding_line','ttd-nvstate','prior_year_amount','state','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(124,'funding_line','ttd-nvstate','restrictions','state','Nevada State');
INSERT INTO "citation" VALUES(125,'funding_line','ttd-localapp','amount',NULL,'Not in Financial PlanG FY 26-27 tables');
INSERT INTO "citation" VALUES(126,'funding_line','ttd-localapp','prior_year_amount','loc1','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(127,'funding_line','ttd-localapp','restrictions','loc1','Local Appropriation');
INSERT INTO "citation" VALUES(128,'funding_line','ttd-tdva','allocation','plan','Revenue %s row 19');
INSERT INTO "citation" VALUES(129,'funding_line','ttd-tdva','amount','plan','Per Route Model D28');
INSERT INTO "citation" VALUES(130,'funding_line','ttd-tdva','amount','plan','T2-4 Table A1 G77');
INSERT INTO "citation" VALUES(131,'funding_line','ttd-tdva','prior_year_amount','loc1','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(132,'funding_line','ttd-tdva','match','plan','Revenue %s row 19');
INSERT INTO "citation" VALUES(133,'funding_line','ttd-tdva','restrictions','loc1','Tahoe Douglas Visitor Authority');
INSERT INTO "citation" VALUES(134,'funding_line','ttd-tdva','projection','plan','T2-4 Table A1 note 4');
INSERT INTO "citation" VALUES(135,'funding_line','ttd-interest','allocation','plan','Revenue %s row 20 (same basis as LCTOP)');
INSERT INTO "citation" VALUES(136,'funding_line','ttd-interest','amount','plan','Per Route Model D29');
INSERT INTO "citation" VALUES(137,'funding_line','ttd-interest','amount','plan','T2-4 Table A1 G78');
INSERT INTO "citation" VALUES(138,'funding_line','ttd-interest','match','plan','Revenue %s row 20');
INSERT INTO "citation" VALUES(139,'funding_line','ttd-interest','projection','plan','T2-4 Table A1 note 4');
INSERT INTO "citation" VALUES(140,'funding_line','ttd-ktb','allocation','plan','Revenue %s row 21');
INSERT INTO "citation" VALUES(141,'funding_line','ttd-ktb','amount','plan','Per Route Model D30');
INSERT INTO "citation" VALUES(142,'funding_line','ttd-ktb','amount','plan','T2-4 Table A1 G79:H79');
INSERT INTO "citation" VALUES(143,'funding_line','ttd-ktb','match','plan','Revenue %s row 21');
INSERT INTO "citation" VALUES(144,'funding_line','ttd-crp','allocation','plan','Revenue %s row 22');
INSERT INTO "citation" VALUES(145,'funding_line','ttd-crp','amount','plan','Per Route Model D31');
INSERT INTO "citation" VALUES(146,'funding_line','ttd-crp','amount','plan','T2-4 Table A1 G80:H80');
INSERT INTO "citation" VALUES(147,'funding_line','ttd-crp','match','plan','Revenue %s row 22 C22');
INSERT INTO "citation" VALUES(148,'funding_line','ttd-eldebs','allocation','plan','Revenue %s row 23');
INSERT INTO "citation" VALUES(149,'funding_line','ttd-eldebs','amount','plan','Per Route Model D32');
INSERT INTO "citation" VALUES(150,'funding_line','ttd-eldebs','amount','plan','T2-4 Table A1 G81:H81');
INSERT INTO "citation" VALUES(151,'funding_line','ttd-eldebs','match','plan','Revenue %s row 23 B23');
INSERT INTO "citation" VALUES(152,'funding_line','ttd-plaebs','allocation','plan','Revenue %s row 24');
INSERT INTO "citation" VALUES(153,'funding_line','ttd-plaebs','amount','plan','Per Route Model D33');
INSERT INTO "citation" VALUES(154,'funding_line','ttd-plaebs','amount','plan','T2-4 Table A1 G82:H82');
INSERT INTO "citation" VALUES(155,'funding_line','ttd-plaebs','match','plan','Revenue %s row 24');
INSERT INTO "citation" VALUES(156,'funding_line','ttd-fares30','allocation',NULL,'Fares belong to the route that collects them');
INSERT INTO "citation" VALUES(157,'funding_line','ttd-fares30','amount','plan','T2-4 Table A1 G72');
INSERT INTO "citation" VALUES(158,'funding_line','ttd-fares30','projection','plan','T2-4 Table A1 G135: 2% base ridership growth');
INSERT INTO "citation" VALUES(159,'funding_line','ttd-5339','prior_year_amount','fed','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(160,'funding_line','ttd-5339','amount','plan','FTA Allocation Split (26-27) I34');
INSERT INTO "citation" VALUES(161,'funding_line','ll-sb125','allocation',NULL,'Not split across Lake Link zones on Revenue %s; applied to Lake Link');
INSERT INTO "citation" VALUES(162,'funding_line','ll-sb125','amount','plan','Per Route Model F26');
INSERT INTO "citation" VALUES(163,'funding_line','ll-sb125','amount','plan','T2-4 Table A1 G85');
INSERT INTO "citation" VALUES(164,'funding_line','ll-sb125','prior_year_amount','plan','T2-4 Table A1 F85');
INSERT INTO "citation" VALUES(165,'funding_line','ll-sb125','restrictions','state','SB 125 Operating');
INSERT INTO "citation" VALUES(166,'funding_line','ll-douglas','allocation','plan','Revenue %s row 34');
INSERT INTO "citation" VALUES(167,'funding_line','ll-douglas','amount','plan','Per Route Model F43');
INSERT INTO "citation" VALUES(168,'funding_line','ll-douglas','amount','plan','T2-4 Table A1 G86:K86');
INSERT INTO "citation" VALUES(169,'funding_line','ll-douglas','prior_year_amount','plan','T2-4 Table A1 F86');
INSERT INTO "citation" VALUES(170,'funding_line','ll-douglas','match','plan','Revenue %s row 34');
INSERT INTO "citation" VALUES(171,'funding_line','ll-douglas','restrictions','loc2','Douglas County');
INSERT INTO "citation" VALUES(172,'funding_line','ll-cslt','allocation','plan','Revenue %s row 35');
INSERT INTO "citation" VALUES(173,'funding_line','ll-cslt','amount','plan','Per Route Model F44');
INSERT INTO "citation" VALUES(174,'funding_line','ll-cslt','amount','plan','T2-4 Table A1 G87:K87');
INSERT INTO "citation" VALUES(175,'funding_line','ll-cslt','prior_year_amount','plan','T2-4 Table A1 F87');
INSERT INTO "citation" VALUES(176,'funding_line','ll-cslt','match','plan','Revenue %s row 35');
INSERT INTO "citation" VALUES(177,'funding_line','ll-cslt','restrictions','loc2','City of South Lake Tahoe');
INSERT INTO "citation" VALUES(178,'funding_line','ll-tahoeblue','allocation','plan','Revenue %s row 36');
INSERT INTO "citation" VALUES(179,'funding_line','ll-tahoeblue','amount','plan','Per Route Model F45');
INSERT INTO "citation" VALUES(180,'funding_line','ll-tahoeblue','amount','plan','T2-4 Table A1 G88');
INSERT INTO "citation" VALUES(181,'funding_line','ll-tahoeblue','prior_year_amount','plan','T2-4 Table A1 F88');
INSERT INTO "citation" VALUES(182,'funding_line','ll-tahoeblue','restrictions','loc2','Tahoe Blue Events Center Mitigation Fee');
INSERT INTO "citation" VALUES(183,'funding_line','ll-tahoeblue','projection','plan','T2-4 Table A1 H88: 6% per year, capped at $750,000');
INSERT INTO "citation" VALUES(184,'funding_line','ll-slttid','allocation','plan','Revenue %s row 37–43');
INSERT INTO "citation" VALUES(185,'funding_line','ll-slttid','amount','plan','T2-4 Table A1 G89 (FY 26-27 = $0)');
INSERT INTO "citation" VALUES(186,'funding_line','ll-slttid','prior_year_amount','plan','T2-4 Table A1 F89');
INSERT INTO "citation" VALUES(187,'funding_line','ll-slttid','prior_year_amount','loc2','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(188,'funding_line','ll-slttid','restrictions','loc2','South Lake Tahoe Tourism Improvement District');
INSERT INTO "citation" VALUES(189,'funding_line','ll-heavenly','allocation','plan','Revenue %s row 37–43');
INSERT INTO "citation" VALUES(190,'funding_line','ll-heavenly','amount','plan','T2-4 Table A1 G90 (FY 26-27 = $0)');
INSERT INTO "citation" VALUES(191,'funding_line','ll-heavenly','prior_year_amount','plan','T2-4 Table A1 F90');
INSERT INTO "citation" VALUES(192,'funding_line','ll-heavenly','prior_year_amount','loc2','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(193,'funding_line','ll-heavenly','restrictions','loc2','Heavenly');
INSERT INTO "citation" VALUES(194,'funding_line','ll-caesars','allocation','plan','Revenue %s row 37–43');
INSERT INTO "citation" VALUES(195,'funding_line','ll-caesars','amount','plan','T2-4 Table A1 G91 (FY 26-27 = $0)');
INSERT INTO "citation" VALUES(196,'funding_line','ll-caesars','prior_year_amount','plan','T2-4 Table A1 F91');
INSERT INTO "citation" VALUES(197,'funding_line','ll-caesars','prior_year_amount','loc2','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(198,'funding_line','ll-caesars','restrictions','loc2','Caesars Entertainment');
INSERT INTO "citation" VALUES(199,'funding_line','ll-roundhill','allocation','plan','Revenue %s row 37–43');
INSERT INTO "citation" VALUES(200,'funding_line','ll-roundhill','amount','plan','T2-4 Table A1 G92 (FY 26-27 = $0)');
INSERT INTO "citation" VALUES(201,'funding_line','ll-roundhill','prior_year_amount','plan','T2-4 Table A1 F92');
INSERT INTO "citation" VALUES(202,'funding_line','ll-roundhill','prior_year_amount','loc2','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(203,'funding_line','ll-roundhill','restrictions','loc2','Round Hill Pines Resort');
INSERT INTO "citation" VALUES(204,'funding_line','ll-advlearn','allocation','plan','Revenue %s row 37–43');
INSERT INTO "citation" VALUES(205,'funding_line','ll-advlearn','amount','plan','T2-4 Table A1 G93 (FY 26-27 = $0)');
INSERT INTO "citation" VALUES(206,'funding_line','ll-advlearn','prior_year_amount','plan','T2-4 Table A1 F93');
INSERT INTO "citation" VALUES(207,'funding_line','ll-advlearn','prior_year_amount','loc2','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(208,'funding_line','ll-advlearn','restrictions','loc2','Advance Learning');
INSERT INTO "citation" VALUES(209,'funding_line','ll-ltva','allocation','plan','Revenue %s row 37–43');
INSERT INTO "citation" VALUES(210,'funding_line','ll-ltva','amount','plan','T2-4 Table A1 G94 (FY 26-27 = $0)');
INSERT INTO "citation" VALUES(211,'funding_line','ll-ltva','prior_year_amount','plan','T2-4 Table A1 F94');
INSERT INTO "citation" VALUES(212,'funding_line','ll-ltva','prior_year_amount','loc2','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(213,'funding_line','ll-ltva','restrictions','loc2','Lake Tahoe Visitors Authority');
INSERT INTO "citation" VALUES(214,'funding_line','ll-ltcc','allocation','plan','Revenue %s row 37–43');
INSERT INTO "citation" VALUES(215,'funding_line','ll-ltcc','amount','plan','T2-4 Table A1 G95 (FY 26-27 = $0)');
INSERT INTO "citation" VALUES(216,'funding_line','ll-ltcc','prior_year_amount','plan','T2-4 Table A1 F95');
INSERT INTO "citation" VALUES(217,'funding_line','ll-ltcc','prior_year_amount','loc2','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(218,'funding_line','ll-ltcc','restrictions','loc2','Lake Tahoe Community College');
INSERT INTO "citation" VALUES(219,'funding_line','tart-5307','allocation','plan','Revenue %s row 3: share of TART service hours; the PlanG total double-counts Main Line so draft shares sum to 72%, corrected as in Funding Model V1G');
INSERT INTO "citation" VALUES(220,'funding_line','tart-5307','amount','plan','Per Route Model E12 = FTA Allocation Split (26-27) G35');
INSERT INTO "citation" VALUES(221,'funding_line','tart-5307','amount','plan','T5-7 Table A2 G59 shows $2,660,000');
INSERT INTO "citation" VALUES(222,'funding_line','tart-5307','prior_year_amount','fed','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(223,'funding_line','tart-5307','match','plan','Revenue %s row 3');
INSERT INTO "citation" VALUES(224,'funding_line','tart-5307','restrictions','fed','FTA 5307');
INSERT INTO "citation" VALUES(225,'funding_line','tart-5307','projection','plan','T5-7 Table A2 O59: 1% increase yearly');
INSERT INTO "citation" VALUES(226,'funding_line','tart-5310','allocation','plan','Revenue %s row 8');
INSERT INTO "citation" VALUES(227,'funding_line','tart-5310','amount','plan','Per Route Model E17 = FTA Allocation Split (26-27) J35');
INSERT INTO "citation" VALUES(228,'funding_line','tart-5310','prior_year_amount','fed','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(229,'funding_line','tart-5310','match','plan','Revenue %s row 8');
INSERT INTO "citation" VALUES(230,'funding_line','tart-5310','restrictions','fed','FTA 5310');
INSERT INTO "citation" VALUES(231,'funding_line','tart-5311ca','allocation',NULL,'Not allocated on Revenue %s; placeholder split by service hours among eligible TART routes');
INSERT INTO "citation" VALUES(232,'funding_line','tart-5311ca','amount','plan','Per Route Model E16');
INSERT INTO "citation" VALUES(233,'funding_line','tart-5311ca','amount','plan','T5-7 Table A2 G60');
INSERT INTO "citation" VALUES(234,'funding_line','tart-5311ca','prior_year_amount','fed','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(235,'funding_line','tart-5311ca','match','plan','Revenue %s row 7 B7, C7');
INSERT INTO "citation" VALUES(236,'funding_line','tart-5311ca','restrictions','fed','FTA 5311 (Cal Trans)');
INSERT INTO "citation" VALUES(237,'funding_line','tart-5311ca','projection','plan','T5-7 Table A2 1% increase yearly');
INSERT INTO "citation" VALUES(238,'funding_line','tart-ltf-trpa','allocation','plan','Not allocated on Revenue %s; placeholder split by service hours on TART routes in California');
INSERT INTO "citation" VALUES(239,'funding_line','tart-ltf-trpa','amount','plan','Per Route Model E19');
INSERT INTO "citation" VALUES(240,'funding_line','tart-ltf-trpa','amount','plan','T5-7 Table A2 G61');
INSERT INTO "citation" VALUES(241,'funding_line','tart-ltf-trpa','prior_year_amount','state','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(242,'funding_line','tart-ltf-trpa','match','plan','Revenue %s row 11');
INSERT INTO "citation" VALUES(243,'funding_line','tart-ltf-trpa','projection','plan','T5-7 Table A2 note 2: population change');
INSERT INTO "citation" VALUES(244,'funding_line','tart-ltf-pctpa','allocation','plan','Not allocated on Revenue %s; placeholder split by service hours on TART routes in California');
INSERT INTO "citation" VALUES(245,'funding_line','tart-ltf-pctpa','amount','plan','Per Route Model E20');
INSERT INTO "citation" VALUES(246,'funding_line','tart-ltf-pctpa','amount','plan','T5-7 Table A2 G61');
INSERT INTO "citation" VALUES(247,'funding_line','tart-ltf-pctpa','prior_year_amount','state','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(248,'funding_line','tart-ltf-pctpa','match','plan','Revenue %s row 11');
INSERT INTO "citation" VALUES(249,'funding_line','tart-ltf-pctpa','projection','plan','T5-7 Table A2 note 2: population change');
INSERT INTO "citation" VALUES(250,'funding_line','tart-sta-trpa','allocation','plan','Not allocated on Revenue %s; placeholder split by service hours on TART routes in California');
INSERT INTO "citation" VALUES(251,'funding_line','tart-sta-trpa','amount','plan','Per Route Model E21');
INSERT INTO "citation" VALUES(252,'funding_line','tart-sta-trpa','amount','plan','T5-7 Table A2 G62');
INSERT INTO "citation" VALUES(253,'funding_line','tart-sta-trpa','prior_year_amount','state','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(254,'funding_line','tart-sta-trpa','match','plan','Revenue %s row 13');
INSERT INTO "citation" VALUES(255,'funding_line','tart-sta-trpa','projection','plan','T5-7 Table A2 note 2: population change');
INSERT INTO "citation" VALUES(256,'funding_line','tart-sta-pctpa','allocation','plan','Not allocated on Revenue %s; placeholder split by service hours on TART routes in California');
INSERT INTO "citation" VALUES(257,'funding_line','tart-sta-pctpa','amount','plan','Per Route Model E22');
INSERT INTO "citation" VALUES(258,'funding_line','tart-sta-pctpa','amount','plan','T5-7 Table A2 G62');
INSERT INTO "citation" VALUES(259,'funding_line','tart-sta-pctpa','prior_year_amount','state','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(260,'funding_line','tart-sta-pctpa','match','plan','Revenue %s row 13');
INSERT INTO "citation" VALUES(261,'funding_line','tart-sta-pctpa','projection','plan','T5-7 Table A2 note 2: population change');
INSERT INTO "citation" VALUES(262,'funding_line','tart-sgr','allocation',NULL,'Not allocated on Revenue %s; placeholder split by service hours on TART routes in California');
INSERT INTO "citation" VALUES(263,'funding_line','tart-sgr','amount','plan','Per Route Model E23');
INSERT INTO "citation" VALUES(264,'funding_line','tart-sgr','amount','plan','T5-7 Table A2 G63');
INSERT INTO "citation" VALUES(265,'funding_line','tart-sgr','prior_year_amount','state','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(266,'funding_line','tart-sgr','match','plan','Revenue %s row 14');
INSERT INTO "citation" VALUES(267,'funding_line','tart-sgr','restrictions','state','State of Good Repair (SGR)');
INSERT INTO "citation" VALUES(268,'funding_line','tart-tot-tc','allocation','plan','Actual Revenues row 28');
INSERT INTO "citation" VALUES(269,'funding_line','tart-tot-tc','amount','plan','Actual Revenues U28:X28 ($2.9 million across TART Connect zones); T5-7 G155');
INSERT INTO "citation" VALUES(270,'funding_line','tart-tot-tc','match','plan','Revenue %s row 28');
INSERT INTO "citation" VALUES(271,'funding_line','tart-tot-tc','restrictions','loc1','Placer County (Transient Occupancy Tax)');
INSERT INTO "citation" VALUES(272,'funding_line','tart-tot-tc','projection','plan','T5-7 Table A2 O68: 4% annually with inflation');
INSERT INTO "citation" VALUES(273,'funding_line','tart-tot-fr','allocation',NULL,'Not allocated on Revenue %s; placeholder split by service hours on Placer County routes');
INSERT INTO "citation" VALUES(274,'funding_line','tart-tot-fr','amount','plan','T5-7 Table A2 G68');
INSERT INTO "citation" VALUES(275,'funding_line','tart-tot-fr','prior_year_amount','loc1','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(276,'funding_line','tart-tot-fr','match','plan','Revenue %s row 28');
INSERT INTO "citation" VALUES(277,'funding_line','tart-tot-fr','restrictions','loc1','Placer County (Transient Occupancy Tax)');
INSERT INTO "citation" VALUES(278,'funding_line','tart-tot-fr','projection','plan','T5-7 Table A2 O68: 4% annually');
INSERT INTO "citation" VALUES(279,'funding_line','tart-washoe','allocation','plan','Revenue %s row 25');
INSERT INTO "citation" VALUES(280,'funding_line','tart-washoe','amount','plan','Per Route Model E34');
INSERT INTO "citation" VALUES(281,'funding_line','tart-washoe','amount','plan','T5-7 Table A2 G69');
INSERT INTO "citation" VALUES(282,'funding_line','tart-washoe','prior_year_amount','loc1','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(283,'funding_line','tart-washoe','match','plan','Revenue %s row 25 B25');
INSERT INTO "citation" VALUES(284,'funding_line','tart-washoe','restrictions','loc1','Washoe RTC');
INSERT INTO "citation" VALUES(285,'funding_line','tart-washoe','projection','plan','T5-7 Table A2 O69: 2% annual increase');
INSERT INTO "citation" VALUES(286,'funding_line','tart-truckee','amount','plan','Per Route Model E38');
INSERT INTO "citation" VALUES(287,'funding_line','tart-truckee','amount','plan','T5-7 Table A2 G70');
INSERT INTO "citation" VALUES(288,'funding_line','tart-truckee','prior_year_amount','loc1','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(289,'funding_line','tart-truckee','match','plan','Revenue %s row 29');
INSERT INTO "citation" VALUES(290,'funding_line','tart-truckee','restrictions','loc1','Town of Truckee');
INSERT INTO "citation" VALUES(291,'funding_line','tart-truckee','projection','plan','T5-7 Table A2 O70: no change');
INSERT INTO "citation" VALUES(292,'funding_line','tart-nsrp','allocation',NULL,'Not allocated on Revenue %s; placeholder split by service hours on TART fixed routes');
INSERT INTO "citation" VALUES(293,'funding_line','tart-nsrp','amount','plan','Per Route Model E40');
INSERT INTO "citation" VALUES(294,'funding_line','tart-nsrp','amount','plan','T5-7 Table A2 G71');
INSERT INTO "citation" VALUES(295,'funding_line','tart-nsrp','prior_year_amount','loc1','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(296,'funding_line','tart-nsrp','match','plan','Revenue %s row 31');
INSERT INTO "citation" VALUES(297,'funding_line','tart-nsrp','restrictions','loc1','North Shore Resort Partners');
INSERT INTO "citation" VALUES(298,'funding_line','tart-nsrp','projection','plan','T5-7 Table A2 O71: no change');
INSERT INTO "citation" VALUES(299,'funding_line','tart-nslp','allocation',NULL,'Not allocated on Revenue %s; placeholder split by service hours on TART fixed routes');
INSERT INTO "citation" VALUES(300,'funding_line','tart-nslp','amount','plan','Per Route Model E41');
INSERT INTO "citation" VALUES(301,'funding_line','tart-nslp','amount','plan','T5-7 Table A2 G72');
INSERT INTO "citation" VALUES(302,'funding_line','tart-nslp','prior_year_amount','loc1','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(303,'funding_line','tart-nslp','match','plan','Revenue %s row 32');
INSERT INTO "citation" VALUES(304,'funding_line','tart-nslp','restrictions','loc1','North Shore Resort Partners (Free Fares)');
INSERT INTO "citation" VALUES(305,'funding_line','tart-nslp','projection','plan','T5-7 Table A2 O72: no change');
INSERT INTO "citation" VALUES(306,'funding_line','tart-martis','allocation',NULL,'Restricted to Hwy 267');
INSERT INTO "citation" VALUES(307,'funding_line','tart-martis','amount','plan','Per Route Model E42');
INSERT INTO "citation" VALUES(308,'funding_line','tart-martis','amount','plan','T5-7 Table A2 G73');
INSERT INTO "citation" VALUES(309,'funding_line','tart-martis','prior_year_amount','loc1','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(310,'funding_line','tart-martis','restrictions','loc1','Martis Zones of Benefit');
INSERT INTO "citation" VALUES(311,'funding_line','tart-5339','prior_year_amount','fed','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(312,'funding_line','tart-5339','amount','plan','FTA Allocation Split (26-27) I35');
INSERT INTO "citation" VALUES(313,'funding_line','tnt-tot-nlte','allocation',NULL,'NLTE budget line');
INSERT INTO "citation" VALUES(314,'funding_line','tnt-tot-nlte','amount','plan','TNTTMA $ F9 (FY 26-27 budget)');
INSERT INTO "citation" VALUES(315,'funding_line','tnt-tot-nlte','match','plan','Revenue %s row 28');
INSERT INTO "citation" VALUES(316,'funding_line','tnt-tot-nlte','projection','plan','T5-7 Table A2 4% annually');
INSERT INTO "citation" VALUES(317,'funding_line','tnt-tot-pr','amount','plan','TNTTMA $ F29 (FY 26-27 budget)');
INSERT INTO "citation" VALUES(318,'funding_line','tnt-tot-pr','prior_year_amount','plan','TNTTMA $ E29 (FY 25-26)');
INSERT INTO "citation" VALUES(319,'funding_line','tnt-tot-pr','projection','plan','T5-7 Table A2 4% annually');
INSERT INTO "citation" VALUES(320,'funding_line','tnt-tot-van','allocation',NULL,'Vanpool budget line');
INSERT INTO "citation" VALUES(321,'funding_line','tnt-tot-van','amount','plan','TNTTMA $ K29 (FY 26-27 budget)');
INSERT INTO "citation" VALUES(322,'funding_line','tnt-tot-van','prior_year_amount','plan','TNTTMA $ J29 (FY 25-26)');
INSERT INTO "citation" VALUES(323,'funding_line','tnt-tot-van','projection','plan','T5-7 Table A2 4% annually');
INSERT INTO "citation" VALUES(324,'funding_line','tnt-tntn','allocation','plan','Revenue %s row 26');
INSERT INTO "citation" VALUES(325,'funding_line','tnt-tntn','amount','plan','TNTTMA $ F10 (FY 26-27 budget)');
INSERT INTO "citation" VALUES(326,'funding_line','tnt-tntn','prior_year_amount','plan','TNTTMA $ E10 (FY 25-26)');
INSERT INTO "citation" VALUES(327,'funding_line','tnt-tntn','match','plan','Revenue %s row 26');
INSERT INTO "citation" VALUES(328,'funding_line','tnt-tntn','restrictions','loc1','Travel North Tahoe Nevada');
INSERT INTO "citation" VALUES(329,'funding_line','tnt-washoe','allocation',NULL,'NLTE budget line');
INSERT INTO "citation" VALUES(330,'funding_line','tnt-washoe','amount','plan','TNTTMA $ F11 (FY 26-27 budget)');
INSERT INTO "citation" VALUES(331,'funding_line','tnt-washoe','prior_year_amount','plan','TNTTMA $ E11 (FY 25-26)');
INSERT INTO "citation" VALUES(332,'funding_line','tnt-rtaa','allocation','plan','Revenue %s row 27');
INSERT INTO "citation" VALUES(333,'funding_line','tnt-rtaa','amount','plan','TNTTMA $ F12 (FY 26-27 budget)');
INSERT INTO "citation" VALUES(334,'funding_line','tnt-rtaa','prior_year_amount','loc1','FY 25-26 budgeted for operations');
INSERT INTO "citation" VALUES(335,'funding_line','tnt-rtaa','match','plan','Revenue %s row 27');
INSERT INTO "citation" VALUES(336,'funding_line','tnt-rtaa','restrictions','loc1','Reno-Tahoe Airport Authority');
INSERT INTO "citation" VALUES(337,'funding_line','tnt-truckee','allocation',NULL,'NLTE budget line');
INSERT INTO "citation" VALUES(338,'funding_line','tnt-truckee','amount','plan','TNTTMA $ F13 (FY 26-27 budget)');
INSERT INTO "citation" VALUES(339,'funding_line','tnt-truckee','prior_year_amount','plan','TNTTMA $ E13 (FY 25-26)');
INSERT INTO "citation" VALUES(340,'funding_line','tnt-truckee','restrictions','loc1','Town of Truckee');
INSERT INTO "citation" VALUES(341,'funding_line','tnt-truckee2','allocation','plan','Revenue %s row 30');
INSERT INTO "citation" VALUES(342,'funding_line','tnt-truckee2','amount','plan','TNTTMA $ F14 (FY 26-27 budget)');
INSERT INTO "citation" VALUES(343,'funding_line','tnt-nevco','amount','plan','TNTTMA $ F31 (FY 26-27 budget)');
INSERT INTO "citation" VALUES(344,'funding_line','tnt-northstar','amount','plan','TNTTMA $ F32 (FY 26-27 budget)');
INSERT INTO "citation" VALUES(345,'funding_line','tnt-northstar','prior_year_amount','plan','TNTTMA $ E32 (FY 25-26)');
INSERT INTO "citation" VALUES(346,'funding_line','tnt-palisades','amount','plan','TNTTMA $ F33 (FY 26-27 budget)');
INSERT INTO "citation" VALUES(347,'funding_line','tnt-palisades','prior_year_amount','plan','TNTTMA $ E33 (FY 25-26)');
INSERT INTO "citation" VALUES(348,'funding_line','tnt-ntca','amount','plan','TNTTMA $ V10 (FY 26-27 = $0)');
INSERT INTO "citation" VALUES(349,'funding_line','tnt-ntca','prior_year_amount','plan','TNTTMA $ E30 (FY 25-26)');
INSERT INTO "citation" VALUES(350,'funding_line','tnt-fares','allocation',NULL,'Fares belong to the route that collects them');
INSERT INTO "citation" VALUES(351,'funding_line','tnt-fares','amount','plan','TNTTMA $ F15 (FY 26-27 budget)');
INSERT INTO "citation" VALUES(352,'funding_line','tnt-fares','prior_year_amount','plan','TNTTMA $ E15 (FY 25-26)');
INSERT INTO "citation" VALUES(353,'funding_line','tnt-fares','projection','plan','T5-7 Table A2 G87: flat');
INSERT INTO "citation" VALUES(354,'funding_line','tnt-reserve','allocation',NULL,'NLTE budget line');
INSERT INTO "citation" VALUES(355,'funding_line','tnt-reserve','amount','plan','TNTTMA $ F16 (FY 26-27 budget)');
INSERT INTO "citation" VALUES(356,'fta','fta_suballocation','apportionment','plan','FTA Allocation Split (26-27) K23:M23 (FY 25-26 apportionment plus 1%, marked EXAMPLE); G33 (75% operating)');
INSERT INTO "citation" VALUES(357,'fta','fta_earned_share_factor','factors','plan','FTA Allocation Split (26-27) F17:G20 (urban revenue miles), F22:F23 (2020 Census population), L17:L18 (FY 22-23 ridership)');
INSERT INTO "citation" VALUES(358,'agreement','AG-01','description','plan','Per Route Model D88; T2-4 note 6');
INSERT INTO "citation" VALUES(359,'agreement','AG-02','description','scen','VRH Rates L9');
INSERT INTO "citation" VALUES(360,'agreement','AG-02','description','plan','T2-4 note 2');
INSERT INTO "citation" VALUES(361,'agreement','AG-03','description','plan','T2-4 rows 79–82');
INSERT INTO "citation" VALUES(362,'agreement','AG-04','description','scen','VRH Rates L15');
INSERT INTO "citation" VALUES(363,'agreement','AG-05','description','scen','VRH Rates rows 18–21');
INSERT INTO "citation" VALUES(364,'agreement','AG-05','description','plan','Revenue %s M81');
INSERT INTO "citation" VALUES(365,'agreement','AG-06','description','plan','FTA Allocation Split (26-27); Revenue %s AD59');
INSERT INTO "citation" VALUES(366,'agreement','AG-07','description','plan','T2-4 note 2; Revenue %s AE10');
INSERT INTO "citation" VALUES(367,'agreement','AG-08','description','plan','Revenue %s D67');
INSERT INTO "citation" VALUES(368,'agreement','AG-09','description','plan','Revenue %s F64');
INSERT INTO "citation" VALUES(369,'agreement','AG-10','description','plan','T2-4 note 7');
INSERT INTO "citation" VALUES(370,'agreement','AG-11','description','plan','Revenue %s E61:E63, C65');
INSERT INTO "citation" VALUES(371,'agreement','AG-12','description','plan','T2-4 note 8');
INSERT INTO "citation" VALUES(372,'data_issue','DI-01','description','scen','costs K25, K13:K16');
INSERT INTO "citation" VALUES(373,'data_issue','DI-02','description','scen','costs J7; VRH Rates J10');
INSERT INTO "citation" VALUES(374,'data_issue','DI-02','description','plan','T2-4 G20');
INSERT INTO "citation" VALUES(375,'data_issue','DI-03','description','scen','costs rows 22–24');
INSERT INTO "citation" VALUES(376,'data_issue','DI-03','description','plan','TNTTMA $ F22, F43');
INSERT INTO "citation" VALUES(377,'data_issue','DI-04','description','plan','Per Route Model E12; T5-7 G59');
INSERT INTO "citation" VALUES(378,'data_issue','DI-05','description','plan','Operating Stats F45; Revenue %s row 3');
INSERT INTO "citation" VALUES(379,'data_issue','DI-05','description','v1g','Operating Stats F45');
INSERT INTO "citation" VALUES(380,'data_issue','DI-06','description','plan','Per Route Model D19, D21; T2-4 G66:G67');
INSERT INTO "citation" VALUES(381,'data_issue','DI-07','description','plan','T2-4 rows 21, 29');
INSERT INTO "citation" VALUES(382,'data_issue','DI-08','description','plan','Revenue %s row 25; TNTTMA $ F11');
INSERT INTO "citation" VALUES(383,'data_issue','DI-09','description','plan','Per Route Model O28');
INSERT INTO "citation" VALUES(384,'data_issue','DI-10','description','plan','Revenue %s rows 15, 20');
INSERT INTO "citation" VALUES(385,'data_issue','DI-10','description','v1g','Operating Stats F48');
INSERT INTO "citation" VALUES(386,'data_issue','DI-11','description','plan','Revenue %s row 53, column AD');
INSERT INTO "citation" VALUES(387,'data_issue','DI-12','description','plan','T2-4 H72, H20');
INSERT INTO "citation" VALUES(388,'data_issue','DI-13','description','plan','Per Route Model E17; FTA Allocation Split J35');
INSERT INTO "citation" VALUES(389,'data_issue','DI-14','description','state','Nevada State');
INSERT INTO "citation" VALUES(390,'data_issue','DI-14','description','loc1','Local Appropriation; Martis Zones of Benefit');
INSERT INTO "citation" VALUES(391,'data_issue','DI-15','description','loc1','Tahoe Douglas Visitor Authority; Travel North Tahoe Nevada');
INSERT INTO "citation" VALUES(392,'data_issue','DI-16','description','plan','Per Route Model row 1; Revenue %s H83; Actual Revenues G83');
INSERT INTO "citation" VALUES(393,'data_issue','DI-17','description','plan','Revenue %s C6, F64');
INSERT INTO "citation" VALUES(394,'data_issue','DI-18','description','plan','Revenue %s B16:C16');
INSERT INTO "citation" VALUES(395,'data_issue','DI-18','description','state','Electrification Credits');
INSERT INTO "citation" VALUES(396,'data_issue','DI-19','description','scen','costs U12');
CREATE TABLE data_issue (
  issue_id     TEXT PRIMARY KEY,
  title        TEXT NOT NULL,
  description  TEXT NOT NULL
);
INSERT INTO "data_issue" VALUES('DI-01','Costs tab total double-counts TART Main Line','The costs tab total ($23,078,713, K25) sums the Main Line subtotal (row 16) and its three segments (rows 13–15), counting $2,497,613 twice. The model counts the segments once.');
INSERT INTO "data_issue" VALUES('DI-02','Route 30 cost rate','The costs tab prices Route 30 at the Lake Link Via rate ($68.70/VSH, $240,450). VRH Rates lists $147.80/VSH for Route 30 (TTD–Via), and the FY 26-27 Emerald Bay Shuttle budget is $517,288.');
INSERT INTO "data_issue" VALUES('DI-03','TNT/TMA service costs','The costs tab estimates NLTE at $241,181 (1,200 VSH) and Park & Ride at $602,952 (3,000 VSH). The TNT/TMA FY 26-27 budget shows NLTE $694,260 and Park & Ride $894,233.');
INSERT INTO "data_issue" VALUES('DI-04','TART FTA 5307 amount','The per-route model uses $1,653,136 (75 percent of Placer''s earned share); TART''s plan (Table A2) budgets $2,660,000.');
INSERT INTO "data_issue" VALUES('DI-05','TART service-hour total double-counts Main Line','Operating Stats F45 sums F19:F26, so TART 5307 shares on Revenue %s row 3 sum to 72 percent. Funding Model V1G corrects it.');
INSERT INTO "data_issue" VALUES('DI-06','TDA rows mislabeled and unused','Per Route Model D19 and D21 are labeled LTF and STA but hold TTD''s rural third ($615,042) and urban two-thirds ($1,230,085) of LTF plus STA; no route formulas use them.');
INSERT INTO "data_issue" VALUES('DI-07','US 50 service added without removing 19X','The service plan adds $476,500 for the US 50 replacement while Route 19X''s cost is still counted.');
INSERT INTO "data_issue" VALUES('DI-08','Washoe support may be counted twice','Revenue %s gives 4.2 percent of Washoe RTC''s $296,055 to NLTE, but TNT/TMA budgets Washoe County NLTE support separately ($12,500).');
INSERT INTO "data_issue" VALUES('DI-09','TDVA formula error','Per Route Model row 28 multiplies the Nevada State Parks amount (D27, $85,000) instead of the TDVA amount (D28, $120,000).');
INSERT INTO "data_issue" VALUES('DI-10','LCTOP and interest shares leave out Route 30','Revenue %s rows 15 and 20 divide by TTD hours including Route 30 but give it 0 percent, so shares sum to 90 percent. Funding Model V1G uses F48.');
INSERT INTO "data_issue" VALUES('DI-11','Revenue %s check totals','G53 onward sum only rows 37–51; AD10 sums F:K and skips the ADA column, so it shows 88 percent though the shares total 100 percent.');
INSERT INTO "data_issue" VALUES('DI-12','Route 30 fares end a year early','Table A1 shows $0 fares in FY 27-28 though the pilot runs (cost $523,384 in H20). The model carries $54,570.');
INSERT INTO "data_issue" VALUES('DI-13','TART 5310 missing from TART plan','$75,225 to Placer in FY 26-27 (FTA split J35) is not in T5-7 Table A2.');
INSERT INTO "data_issue" VALUES('DI-14','Fact sheet items missing from the FY 26-27 plan','Nevada State allocation $346,500, local appropriation $232,235, and Martis Zones of Benefit $50,000 (all FY 25-26). Listed at $0.');
INSERT INTO "data_issue" VALUES('DI-15','Fact sheet and plan disagree','TDVA $65,000 (FY 25-26) vs $120,000 (FY 26-27 plan). The Travel North Tahoe Nevada card shows "TTD budgeted $8,000" though it funds NLTE.');
INSERT INTO "data_issue" VALUES('DI-16','Copied and broken cells','Per Route Model row 1 cost cells for Lake Link, Main Line, Hwy 89, Hwy 267, and TART Connect repeat TTD route values; Revenue %s H83 and Actual Revenues G83 show #REF!.');
INSERT INTO "data_issue" VALUES('DI-17','Match rate for NDOT 5311','Revenue %s lists 50 percent non-federal match for 5311; partner notes say NDOT match is 20 percent for administration, 40 percent for operating, and 5 percent for capital.');
INSERT INTO "data_issue" VALUES('DI-18','Electrification credits','Revenue %s notes call electrification credits "not real money, only used as match." The fact sheet lists $8,000 budgeted for TTD operations.');
INSERT INTO "data_issue" VALUES('DI-19','Lake Link hours','Lake Link VSH are contract hours, not actuals.');
CREATE TABLE eligibility_rule (
  rule_row_id INTEGER PRIMARY KEY,
  line_id     TEXT NOT NULL REFERENCES funding_line (line_id),
  rule_type   TEXT NOT NULL CHECK (rule_type IN ('service', 'agency', 'area_class', 'service_type', 'state', 'jurisdiction_share')),
  strength    TEXT NOT NULL CHECK (strength IN ('required', 'preferred')),
  value       TEXT NOT NULL,
  UNIQUE (line_id, rule_type, strength, value)
);
INSERT INTO "eligibility_rule" VALUES(1,'ttd-5307','area_class','required','urban');
INSERT INTO "eligibility_rule" VALUES(2,'ttd-5307','area_class','required','mixed');
INSERT INTO "eligibility_rule" VALUES(3,'ttd-5307cmaq','area_class','required','urban');
INSERT INTO "eligibility_rule" VALUES(4,'ttd-5307cmaq','area_class','required','mixed');
INSERT INTO "eligibility_rule" VALUES(5,'ttd-5307co','area_class','required','urban');
INSERT INTO "eligibility_rule" VALUES(6,'ttd-5307co','area_class','required','mixed');
INSERT INTO "eligibility_rule" VALUES(7,'ttd-5311nv','state','required','NV');
INSERT INTO "eligibility_rule" VALUES(8,'ttd-5311nv','area_class','required','rural');
INSERT INTO "eligibility_rule" VALUES(9,'ttd-5311nv','area_class','required','mixed');
INSERT INTO "eligibility_rule" VALUES(10,'ttd-5310','service_type','required','paratransit');
INSERT INTO "eligibility_rule" VALUES(11,'ttd-5310co','service_type','required','paratransit');
INSERT INTO "eligibility_rule" VALUES(12,'ttd-ltf','state','preferred','CA');
INSERT INTO "eligibility_rule" VALUES(13,'ttd-sta','state','preferred','CA');
INSERT INTO "eligibility_rule" VALUES(14,'ttd-lctop','state','required','CA');
INSERT INTO "eligibility_rule" VALUES(15,'ttd-sb125','state','preferred','CA');
INSERT INTO "eligibility_rule" VALUES(16,'ttd-nvparks','service','required','28');
INSERT INTO "eligibility_rule" VALUES(17,'ttd-nvstate','state','required','NV');
INSERT INTO "eligibility_rule" VALUES(18,'ttd-tdva','state','preferred','NV');
INSERT INTO "eligibility_rule" VALUES(19,'ttd-tdva','service','preferred','51');
INSERT INTO "eligibility_rule" VALUES(20,'ttd-ktb','service','required','30');
INSERT INTO "eligibility_rule" VALUES(21,'ttd-crp','service','required','30');
INSERT INTO "eligibility_rule" VALUES(22,'ttd-eldebs','service','required','30');
INSERT INTO "eligibility_rule" VALUES(23,'ttd-eldebs','state','preferred','CA');
INSERT INTO "eligibility_rule" VALUES(24,'ttd-plaebs','service','required','30');
INSERT INTO "eligibility_rule" VALUES(25,'ttd-plaebs','state','preferred','CA');
INSERT INTO "eligibility_rule" VALUES(26,'ttd-fares30','service','required','30');
INSERT INTO "eligibility_rule" VALUES(27,'ll-sb125','service','required','LL');
INSERT INTO "eligibility_rule" VALUES(28,'ll-sb125','state','preferred','CA');
INSERT INTO "eligibility_rule" VALUES(29,'ll-douglas','service','required','LL');
INSERT INTO "eligibility_rule" VALUES(30,'ll-douglas','jurisdiction_share','required','DOU');
INSERT INTO "eligibility_rule" VALUES(31,'ll-cslt','service','required','LL');
INSERT INTO "eligibility_rule" VALUES(32,'ll-cslt','jurisdiction_share','required','CSLT');
INSERT INTO "eligibility_rule" VALUES(33,'ll-tahoeblue','service','required','LL');
INSERT INTO "eligibility_rule" VALUES(34,'ll-slttid','service','required','LL');
INSERT INTO "eligibility_rule" VALUES(35,'ll-heavenly','service','required','LL');
INSERT INTO "eligibility_rule" VALUES(36,'ll-caesars','service','required','LL');
INSERT INTO "eligibility_rule" VALUES(37,'ll-roundhill','service','required','LL');
INSERT INTO "eligibility_rule" VALUES(38,'ll-advlearn','service','required','LL');
INSERT INTO "eligibility_rule" VALUES(39,'ll-ltva','service','required','LL');
INSERT INTO "eligibility_rule" VALUES(40,'ll-ltcc','service','required','LL');
INSERT INTO "eligibility_rule" VALUES(41,'tart-5307','area_class','required','urban');
INSERT INTO "eligibility_rule" VALUES(42,'tart-5307','area_class','required','mixed');
INSERT INTO "eligibility_rule" VALUES(43,'tart-5310','service_type','required','paratransit');
INSERT INTO "eligibility_rule" VALUES(44,'tart-5311ca','state','required','CA');
INSERT INTO "eligibility_rule" VALUES(45,'tart-5311ca','area_class','required','rural');
INSERT INTO "eligibility_rule" VALUES(46,'tart-5311ca','area_class','required','mixed');
INSERT INTO "eligibility_rule" VALUES(47,'tart-ltf-trpa','state','preferred','CA');
INSERT INTO "eligibility_rule" VALUES(48,'tart-ltf-pctpa','state','preferred','CA');
INSERT INTO "eligibility_rule" VALUES(49,'tart-sta-trpa','state','preferred','CA');
INSERT INTO "eligibility_rule" VALUES(50,'tart-sta-pctpa','state','preferred','CA');
INSERT INTO "eligibility_rule" VALUES(51,'tart-sgr','state','preferred','CA');
INSERT INTO "eligibility_rule" VALUES(52,'tart-tot-tc','service','required','TC');
INSERT INTO "eligibility_rule" VALUES(53,'tart-tot-tc','jurisdiction_share','preferred','PLA');
INSERT INTO "eligibility_rule" VALUES(54,'tart-tot-fr','jurisdiction_share','preferred','PLA');
INSERT INTO "eligibility_rule" VALUES(55,'tart-washoe','service','required','TART-NV');
INSERT INTO "eligibility_rule" VALUES(56,'tart-truckee','service','required','89');
INSERT INTO "eligibility_rule" VALUES(57,'tart-truckee','service','required','267');
INSERT INTO "eligibility_rule" VALUES(58,'tart-truckee','service','required','NLTE');
INSERT INTO "eligibility_rule" VALUES(59,'tart-nsrp','agency','required','TART');
INSERT INTO "eligibility_rule" VALUES(60,'tart-nslp','agency','required','TART');
INSERT INTO "eligibility_rule" VALUES(61,'tart-martis','service','required','267');
INSERT INTO "eligibility_rule" VALUES(62,'tnt-tot-nlte','service','required','NLTE');
INSERT INTO "eligibility_rule" VALUES(63,'tnt-tot-nlte','jurisdiction_share','preferred','PLA');
INSERT INTO "eligibility_rule" VALUES(64,'tnt-tot-pr','service','required','PR-W');
INSERT INTO "eligibility_rule" VALUES(65,'tnt-tot-pr','service','required','PR-S');
INSERT INTO "eligibility_rule" VALUES(66,'tnt-tot-pr','jurisdiction_share','preferred','PLA');
INSERT INTO "eligibility_rule" VALUES(67,'tnt-tot-van','service','required','VAN');
INSERT INTO "eligibility_rule" VALUES(68,'tnt-tntn','service','required','NLTE');
INSERT INTO "eligibility_rule" VALUES(69,'tnt-tntn','state','preferred','NV');
INSERT INTO "eligibility_rule" VALUES(70,'tnt-washoe','service','required','NLTE');
INSERT INTO "eligibility_rule" VALUES(71,'tnt-rtaa','service','required','NLTE');
INSERT INTO "eligibility_rule" VALUES(72,'tnt-truckee','service','required','89');
INSERT INTO "eligibility_rule" VALUES(73,'tnt-truckee','service','required','267');
INSERT INTO "eligibility_rule" VALUES(74,'tnt-truckee','service','required','NLTE');
INSERT INTO "eligibility_rule" VALUES(75,'tnt-truckee2','service','required','NLTE');
INSERT INTO "eligibility_rule" VALUES(76,'tnt-nevco','service','required','PR-W');
INSERT INTO "eligibility_rule" VALUES(77,'tnt-nevco','service','required','PR-S');
INSERT INTO "eligibility_rule" VALUES(78,'tnt-northstar','service','required','PR-W');
INSERT INTO "eligibility_rule" VALUES(79,'tnt-northstar','service','required','PR-S');
INSERT INTO "eligibility_rule" VALUES(80,'tnt-palisades','service','required','PR-W');
INSERT INTO "eligibility_rule" VALUES(81,'tnt-palisades','service','required','PR-S');
INSERT INTO "eligibility_rule" VALUES(82,'tnt-ntca','service','required','PR-W');
INSERT INTO "eligibility_rule" VALUES(83,'tnt-ntca','service','required','PR-S');
INSERT INTO "eligibility_rule" VALUES(84,'tnt-fares','service','required','NLTE');
INSERT INTO "eligibility_rule" VALUES(85,'tnt-reserve','service','required','NLTE');
CREATE TABLE fiscal_year (
  fy_index      INTEGER PRIMARY KEY,             -- 0 = base year (FY 26-27)
  label         TEXT NOT NULL UNIQUE
);
INSERT INTO "fiscal_year" VALUES(0,'FY 26-27');
INSERT INTO "fiscal_year" VALUES(1,'FY 27-28');
INSERT INTO "fiscal_year" VALUES(2,'FY 28-29');
INSERT INTO "fiscal_year" VALUES(3,'FY 29-30');
INSERT INTO "fiscal_year" VALUES(4,'FY 30-31');
CREATE TABLE fta_earned_share_factor (
  agency_id            TEXT PRIMARY KEY REFERENCES agency (agency_id),
  urban_revenue_miles  REAL NOT NULL,
  population           REAL NOT NULL,
  ridership            REAL NOT NULL
);
INSERT INTO "fta_earned_share_factor" VALUES('TTD',803084.0,31420.0,489907.0);
INSERT INTO "fta_earned_share_factor" VALUES('TART',1408116.0,16643.0,613042.0);
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
INSERT INTO "fta_suballocation" VALUES(0,4296912.69,405232.2,75224.8,0.75,1.0,1.0,1.0);
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
INSERT INTO "funding_line" VALUES('ttd-5307','fta-5307-urbanized-area-formula','TTD','FTA 5307 formula (TTD)','Federal Transit Administration',1569548.05,'fta_5307_formula',2400000.0,0.01,NULL,NULL,'budgeted','formula','Annual FTA apportionment to the Lake Tahoe UZA, split between TTD and Placer County by the earned-share worksheet.',NULL,0.5,0.8,1,0,1,'Urbanized area operating, capital, and transportation-related planning.','50% non-federal','Can be used to cover 50% of operating costs (urban routes), 80% ADA.','Lake Tahoe UZA and Nevada',NULL);
INSERT INTO "funding_line" VALUES('ttd-5307cmaq','fta-5307-flexed-cmaq','TTD','FTA 5307, formerly CMAQ (TTD)','Federal Transit Administration',596121.0,'fixed',NULL,0.01,NULL,NULL,'budgeted','formula','Programmed annually; partner notes say more CMAQ grants are coming (Revenue %s D55).',NULL,0.5,0.8,1,0,1,'CMAQ funds transferred to FTA 5307 for operations.','50% non-federal',NULL,'Lake Tahoe UZA and Nevada',NULL);
INSERT INTO "funding_line" VALUES('ttd-5307co','fta-5307-carryover','TTD','FTA 5307 carryover (TTD)','Federal Transit Administration',946281.95,'fixed',NULL,0.0,0,NULL,'budgeted','onetime','One-time. The summary table notes the drop in 5307 funds once carryover ends in FY 27-28.',NULL,0.5,0.8,1,0,1,'Prior-year 5307 balance applied to operations.','50% non-federal',NULL,'Lake Tahoe UZA and Nevada',NULL);
INSERT INTO "funding_line" VALUES('ttd-5311nv','fta-5311-rural-area-formula','TTD','FTA 5311 rural (NDOT)','FTA through Nevada DOT',1798577.0,'fixed',1669792.0,0.01,NULL,NULL,'budgeted','formula','NDOT subrecipient award. Partner notes: NDOT match is 20% for admin, 40% for operating, 5% for capital (Revenue %s F64). Nevada receives $9.8 million in total FTA 5311 (Table A1 O65).',NULL,0.5,NULL,1,0,1,'Rural operating, capital, and planning assistance.','50% non-federal','Can only be applied to rural routes (19X and 22)','Nevada only; rural component',NULL);
INSERT INTO "funding_line" VALUES('ttd-5310','fta-5310-enhanced-mobility','TTD','FTA 5310 seniors and disabilities (TTD)','Federal Transit Administration',0.0,'fixed',27000.0,0.0,NULL,NULL,'budgeted','formula','Alternates with Placer County: the FY 26-27 apportionment goes to Placer (FTA Allocation Split J35); TTD in FY 27-28 and FY 29-30.',NULL,0.5,NULL,1,0,1,'Urbanized area funding to meet the needs of older adults and people with disabilities.','50% non-federal','Can only be applied to ADA routes','ADA services and capital only',NULL);
INSERT INTO "funding_line" VALUES('ttd-5310co','fta-5310-carryover','TTD','FTA 5310 carryover (TTD)','Federal Transit Administration',30277.0,'fixed',NULL,0.0,0,NULL,'budgeted','onetime',NULL,NULL,0.5,NULL,1,0,1,NULL,'50% non-federal','Can only be applied to ADA routes','ADA services and capital only',NULL);
INSERT INTO "funding_line" VALUES('ttd-ltf','tda-local-transportation-fund-ltf','TTD','TDA Local Transportation Fund (TTD)','State of California (sales tax), apportioned by TRPA',1263326.0,'fixed',1200000.0,0.00025,NULL,NULL,'budgeted','formula','TRPA apportionment; no change assumed in the TRPA TDA split (Table A1 note 2). TTD applies one-third to rural and two-thirds to urban routes (Revenue %s AE10).',NULL,NULL,NULL,1,0,1,'Operating, capital, and planning funds from a quarter-cent of the general sales tax collected in California.','No match requirement','California funding ideally used in CA, but can be used as federal match','CA and NV (operations only)',NULL);
INSERT INTO "funding_line" VALUES('ttd-sta','tda-state-transit-assistance-sta','TTD','TDA State Transit Assistance (TTD)','State of California (fuel sales tax), apportioned by TRPA',581801.0,'fixed',400000.0,0.00025,NULL,NULL,'budgeted','formula',NULL,NULL,NULL,NULL,1,0,1,'Transit purposes only.','No match requirement','California funding ideally used in CA, but can be used as federal match','CA and NV (operations only)',NULL);
INSERT INTO "funding_line" VALUES('ttd-lctop','lctop','TTD','Low Carbon Transit Operations Program (TTD)','State of California (5% of cap-and-trade proceeds)',265506.0,'fixed',0.0,0.0,NULL,NULL,'budgeted','formula','TTD receives LCTOP every other year; it alternates with TART based on ridership (Revenue %s D67).',NULL,NULL,NULL,1,0,1,'Operating and capital assistance to reduce greenhouse gas emissions and improve mobility.','No match requirement','California funding ideally used in CA, but can be used as federal match','CA only',NULL);
INSERT INTO "funding_line" VALUES('ttd-elec','electrification-credits','TTD','Electrification credits (TTD)','State of California',8000.0,'fixed',8000.0,0.0,NULL,NULL,'budgeted','earned',NULL,NULL,NULL,NULL,1,1,1,'Reimbursement for electrification credits earned through use of the electric fleet.','Not real money; only used as match for other sources','Not real money','–','Counted toward local match only, not toward funding the cost, per the Revenue %s notes. The State Funds fact sheet lists $8,000 budgeted for TTD operations.');
INSERT INTO "funding_line" VALUES('ttd-sb125','sb-125','TTD','SB 125 operating (TTD)','State of California',825000.0,'fixed',1000000.0,0.0,0,NULL,'budgeted','onetime','Table A1 assumes no SB 125 after FY 26-27.',NULL,NULL,NULL,1,0,1,'Operating, capital, and planning.','No match requirement','California funding ideally used in CA, but can be used as federal match','Existing STA recipients only',NULL);
INSERT INTO "funding_line" VALUES('ttd-nvparks','nevada-state-parks','TTD','Nevada State Parks (Route 28)','State of Nevada',85000.0,'fixed',85000.0,0.0,NULL,NULL,'budgeted','budget',NULL,NULL,NULL,NULL,1,0,1,'Operating, capital, and administrative support for the East Shore Express.','No match requirement','Only applied to Route 28','East Shore Express',NULL);
INSERT INTO "funding_line" VALUES('ttd-nvstate','nevada-state-allocation','TTD','Nevada State allocation to TTD general fund','FTA, State of Nevada',0.0,'fixed',346500.0,0.0,NULL,NULL,'factsheet','budget',NULL,NULL,NULL,NULL,1,0,1,'Budget allocation to TTD general fund.','No match requirement',NULL,'NV','On the State Funds fact sheet for FY 25-26 but not in the FY 26-27 financial plan. Enter an amount if it is still expected.');
INSERT INTO "funding_line" VALUES('ttd-localapp','local-appropriation','TTD','Local appropriation (Douglas, Washoe, Placer, Carson City)','Douglas, Washoe, Placer, Carson City',0.0,'fixed',232235.0,0.0,NULL,NULL,'factsheet','budget',NULL,NULL,NULL,NULL,1,0,1,'TTD general fund planning and administration.','No match requirement',NULL,'Planning and administrative support','Supports TTD planning and administration rather than route operations; not in the FY 26-27 operating plan.');
INSERT INTO "funding_line" VALUES('ttd-tdva','visitor-authority-contribution','TTD','Tahoe Douglas Visitor Authority','Tahoe Douglas Visitor Authority',120000.0,'fixed',65000.0,0.0,NULL,NULL,'budgeted','budget',NULL,NULL,NULL,NULL,1,0,1,'Budget contribution for expanded operations (Route 51).','No match requirement','Ideally applied only to NV routes','TTD expanded operations (Route 51)','Per Route Model row 28 multiplies the Nevada State Parks amount ($85,000) instead of the TDVA amount ($120,000).');
INSERT INTO "funding_line" VALUES('ttd-interest','interest','TTD','Interest revenue (TTD)','TTD',18000.0,'fixed',NULL,0.0,NULL,NULL,'budgeted','earned',NULL,NULL,NULL,NULL,1,0,1,NULL,'No match requirement',NULL,NULL,NULL);
INSERT INTO "funding_line" VALUES('ttd-ktb','private-contribution','TTD','Keep Tahoe Blue (Emerald Bay Shuttle)','League to Save Lake Tahoe (Keep Tahoe Blue)',8322.0,'fixed',NULL,0.0,1,NULL,'budgeted','onetime','Total allocated through FY 27-28: $38,000.',NULL,NULL,NULL,1,0,1,NULL,'No match requirement',NULL,NULL,NULL);
INSERT INTO "funding_line" VALUES('ttd-crp','fhwa-carbon-reduction-program','TTD','Carbon Reduction Program (Emerald Bay Shuttle)','Federal Highway Administration',271910.0,'fixed',NULL,0.0,1,NULL,'budgeted','onetime','Total allocated through FY 27-28: $809,000.',NULL,0.8853,NULL,1,0,1,NULL,'11.47% non-federal',NULL,NULL,NULL);
INSERT INTO "funding_line" VALUES('ttd-eldebs','county-contribution','TTD','El Dorado County (Emerald Bay Shuttle)','El Dorado County (AQMD, VMT Reduction Fund)',331240.0,'fixed',NULL,0.0,1,NULL,'budgeted','onetime','Total allocated through FY 27-28: $431,395.','ELD',NULL,NULL,1,0,1,NULL,'No match requirement','Ideally used only in CA',NULL,NULL);
INSERT INTO "funding_line" VALUES('ttd-plaebs','county-contribution','TTD','Placer County (Emerald Bay Shuttle)','Placer County',8324.0,'fixed',NULL,0.0,1,NULL,'budgeted','onetime','Total allocated through FY 27-28: $38,000.','PLA',NULL,NULL,1,0,1,NULL,'No match requirement','Ideally used only in CA',NULL,NULL);
INSERT INTO "funding_line" VALUES('ttd-fares30','passenger-fares','TTD','Fares – Emerald Bay Shuttle','Riders ($5 one-way)',53500.0,'fixed',NULL,0.02,1,NULL,'budgeted','earned',NULL,NULL,NULL,NULL,0,0,1,NULL,NULL,NULL,NULL,'Route 30 is TTD''s only fare route ($5 one-way; Fare Rates tab). Table A1 carries fares in FY 26-27 only; this model continues them with 2% ridership growth through the FY 27-28 pilot season.');
INSERT INTO "funding_line" VALUES('ttd-5339','fta-5339-bus-and-bus-facilities','TTD','FTA 5339 bus and facilities (TTD)','FTA; Nevada DOT',0.0,'fixed',0.0,0.0,NULL,NULL,'capital','formula',NULL,NULL,0.8,NULL,1,0,1,'Capital funds to replace, rehabilitate, and purchase buses and equipment, and to build bus facilities.','Yes (capital)',NULL,'Lake Tahoe UZA and Nevada; Nevada facilities, bi-state fleet OK','Capital program, outside the operating model. FY 26-27 example UZA split: TTD $197,361 (FTA Allocation Split I34).');
INSERT INTO "funding_line" VALUES('ll-sb125','sb-125','SSTMA','SB 125 operating (Lake Link)','State of California',750000.0,'fixed',750000.0,0.0,0,NULL,'budgeted','onetime','Assumes an SB 125 allocation in FY 26-27 only (Table A1 O85).',NULL,NULL,NULL,1,0,1,NULL,'No match requirement',NULL,'Existing STA recipients only',NULL);
INSERT INTO "funding_line" VALUES('ll-douglas','lake-link-funding-agreement','SSTMA','Douglas County (Lake Link)','Douglas County (TLRT)',750000.0,'fixed',650000.0,0.0,NULL,NULL,'budgeted','agreement','Written agreement; one of only two written Lake Link contracts (Per Route Model D88). Table A1 note 6 assumes support at existing levels beyond the end of current agreements.','DOU',NULL,NULL,1,0,1,'Contribution for Lake Link operations in Douglas County.','No match requirement','Ideally used only in Douglas County','Lake Link in Douglas County',NULL);
INSERT INTO "funding_line" VALUES('ll-cslt','lake-link-funding-agreement','SSTMA','City of South Lake Tahoe (Lake Link)','City of South Lake Tahoe',1100000.0,'fixed',850000.0,0.0,NULL,NULL,'budgeted','agreement','Written agreement (Per Route Model D88). Table A1 note 6 assumes support at existing levels beyond current agreements.','CSLT',NULL,NULL,1,0,1,'Contribution for Lake Link operations.','No match requirement','Ideally used only in the City of South Lake Tahoe','Lake Link in City of SLT',NULL);
INSERT INTO "funding_line" VALUES('ll-tahoeblue','transportation-mitigation-fee','SSTMA','Tahoe Blue Events Center mitigation fee','Ticket surcharge, Tahoe Blue Events Center',687724.0,'fixed',613053.0,0.06,NULL,750000.0,'budgeted','agreement','Assumes the $3 surcharge goes to transit and no increase in the annual attendee cap (Table A1 note 7).',NULL,NULL,NULL,1,0,1,'Contribution for Lake Link operations in Stateline and South Lake Tahoe from a transportation mitigation fee on event tickets.','No match requirement',NULL,'Lake Link Service',NULL);
INSERT INTO "funding_line" VALUES('ll-slttid','lake-link-partner-contribution','SSTMA','South Lake Tahoe Tourism Improvement District','South Lake Tahoe Tourism Improvement District',0.0,'fixed',25000.0,0.0,NULL,NULL,'none','none','Contributed to Lake Link in FY 25-26; no FY 26-27 commitment secured (Table A1 note 8).',NULL,NULL,NULL,1,0,1,'Contribution for Lake Link operations.','No match requirement',NULL,'Lake Link Service',NULL);
INSERT INTO "funding_line" VALUES('ll-heavenly','lake-link-partner-contribution','SSTMA','Heavenly','Heavenly',0.0,'fixed',15000.0,0.0,NULL,NULL,'none','none','Contributed to Lake Link in FY 25-26; no FY 26-27 commitment secured (Table A1 note 8).',NULL,NULL,NULL,1,0,1,'Contribution for Lake Link operations.','No match requirement',NULL,'Lake Link Service',NULL);
INSERT INTO "funding_line" VALUES('ll-caesars','lake-link-partner-contribution','SSTMA','Caesars Entertainment','Caesars Entertainment',0.0,'fixed',65000.0,0.0,NULL,NULL,'none','none','Contributed to Lake Link in FY 25-26; no FY 26-27 commitment secured (Table A1 note 8).',NULL,NULL,NULL,1,0,1,'Contribution for Lake Link operations.','No match requirement',NULL,'Lake Link Service',NULL);
INSERT INTO "funding_line" VALUES('ll-roundhill','lake-link-partner-contribution','SSTMA','Round Hill Pines Resort','Round Hill Pines Resort',0.0,'fixed',85000.0,0.0,NULL,NULL,'none','none','Contributed to Lake Link in FY 25-26; no FY 26-27 commitment secured (Table A1 note 8).',NULL,NULL,NULL,1,0,1,'Contribution for Lake Link operations.','No match requirement',NULL,'Lake Link Service',NULL);
INSERT INTO "funding_line" VALUES('ll-advlearn','lake-link-partner-contribution','SSTMA','Advance Learning','Advance Learning',0.0,'fixed',25000.0,0.0,NULL,NULL,'none','none','Contributed to Lake Link in FY 25-26; no FY 26-27 commitment secured (Table A1 note 8).',NULL,NULL,NULL,1,0,1,'Contribution for Lake Link operations.','No match requirement',NULL,'Lake Link Service',NULL);
INSERT INTO "funding_line" VALUES('ll-ltva','lake-link-partner-contribution','SSTMA','Lake Tahoe Visitors Authority','Lake Tahoe Visitors Authority',0.0,'fixed',62100.0,0.0,NULL,NULL,'none','none','Contributed to Lake Link in FY 25-26; no FY 26-27 commitment secured (Table A1 note 8).',NULL,NULL,NULL,1,0,1,'Contribution for Lake Link operations.','No match requirement',NULL,'Lake Link Service',NULL);
INSERT INTO "funding_line" VALUES('ll-ltcc','lake-link-partner-contribution','SSTMA','Lake Tahoe Community College','Lake Tahoe Community College',0.0,'fixed',25000.0,0.0,NULL,NULL,'none','none','Contributed to Lake Link in FY 25-26; no FY 26-27 commitment secured (Table A1 note 8).',NULL,NULL,NULL,1,0,1,'Contribution for Lake Link operations.','No match requirement',NULL,'Lake Link Service',NULL);
INSERT INTO "funding_line" VALUES('tart-5307','fta-5307-urbanized-area-formula','TART','FTA 5307 formula (TART)','Federal Transit Administration',1653136.47,'fta_5307_formula',2500000.0,0.01,NULL,NULL,'budgeted','formula',NULL,NULL,0.5,0.8,1,0,1,'Urbanized area operating, capital, and transportation-related planning.','50% non-federal',NULL,'Lake Tahoe UZA and Nevada','TART financial plan Table A2 budgets $2,660,000 of 5307 for FY 26-27; the per-route model uses the earned-share result ($1,653,136).');
INSERT INTO "funding_line" VALUES('tart-5310','fta-5310-enhanced-mobility','TART','FTA 5310 seniors and disabilities (TART)','Federal Transit Administration',75224.8,'fixed',0.0,0.0,0,NULL,'budgeted','formula',NULL,NULL,0.5,NULL,1,0,1,NULL,'50% non-federal',NULL,'ADA services and capital only','The FTA split worksheet assigns the FY 26-27 5310 apportionment to Placer (J35). It does not appear in TART Table A2. Alternates with TTD; later Placer years are not projected.');
INSERT INTO "funding_line" VALUES('tart-5311ca','fta-5311-rural-area-formula','TART','FTA 5311 rural (Caltrans)','FTA through Caltrans',290000.0,'fixed',450000.0,0.01,NULL,NULL,'budgeted','formula',NULL,NULL,0.5,NULL,1,0,1,'Rural operating, capital, and planning assistance.','50% non-federal','Can only be applied to rural routes','California only; rural component',NULL);
INSERT INTO "funding_line" VALUES('tart-ltf-trpa','tda-local-transportation-fund-ltf','TART','TDA LTF, TRPA apportionment (TART)','State of California, apportioned by TRPA',913053.0,'fixed',NULL,0.00025,NULL,NULL,'budgeted','formula',NULL,NULL,NULL,NULL,1,0,1,NULL,'No match requirement','California funding ideally used in CA, but can be used as federal match','CA and NV (operations only)','Fact sheet FY 25-26 TART totals: LTF $2,023,819 and STA $1,110,118 (TRPA and PCTPA combined).');
INSERT INTO "funding_line" VALUES('tart-ltf-pctpa','tda-local-transportation-fund-ltf','TART','TDA LTF, PCTPA apportionment (TART)','State of California, apportioned by PCTPA',1675000.0,'fixed',NULL,0.00025,NULL,NULL,'budgeted','formula',NULL,NULL,NULL,NULL,1,0,1,NULL,'No match requirement','California funding ideally used in CA, but can be used as federal match','CA and NV (operations only)','Fact sheet FY 25-26 TART totals: LTF $2,023,819 and STA $1,110,118 (TRPA and PCTPA combined).');
INSERT INTO "funding_line" VALUES('tart-sta-trpa','tda-state-transit-assistance-sta','TART','TDA STA, TRPA apportionment (TART)','State of California, apportioned by TRPA',510729.0,'fixed',NULL,0.00025,NULL,NULL,'budgeted','formula',NULL,NULL,NULL,NULL,1,0,1,NULL,'No match requirement','California funding ideally used in CA, but can be used as federal match','CA and NV (operations only)','Fact sheet FY 25-26 TART totals: LTF $2,023,819 and STA $1,110,118 (TRPA and PCTPA combined).');
INSERT INTO "funding_line" VALUES('tart-sta-pctpa','tda-state-transit-assistance-sta','TART','TDA STA, PCTPA apportionment (TART)','State of California, apportioned by PCTPA',308898.0,'fixed',NULL,0.00025,NULL,NULL,'budgeted','formula',NULL,NULL,NULL,NULL,1,0,1,NULL,'No match requirement','California funding ideally used in CA, but can be used as federal match','CA and NV (operations only)','Fact sheet FY 25-26 TART totals: LTF $2,023,819 and STA $1,110,118 (TRPA and PCTPA combined).');
INSERT INTO "funding_line" VALUES('tart-sgr','state-of-good-repair-sgr','TART','State of Good Repair (TART)','State of California (gas tax and vehicle fees)',100084.0,'fixed',102929.0,0.00025,NULL,NULL,'budgeted','formula',NULL,NULL,NULL,NULL,1,0,1,'Transit infrastructure repair and service improvements.','No match requirement',NULL,'Eligible transit maintenance and match for capital projects',NULL);
INSERT INTO "funding_line" VALUES('tart-tot-tc','placer-county-transient-occupancy-tax','TART','Placer County TOT – TART Connect','Placer County',2900000.0,'fixed',NULL,0.04,NULL,NULL,'budgeted','budget',NULL,'PLA',NULL,NULL,1,0,1,'Budget contribution for TART Connect.','No match requirement','Ideally used only in Placer County','Various usage restrictions based on funding subcategory',NULL);
INSERT INTO "funding_line" VALUES('tart-tot-fr','placer-county-transient-occupancy-tax','TART','Placer County TOT – TART fixed route and paratransit','Placer County',2447400.0,'fixed',2563510.0,0.04,NULL,NULL,'budgeted','budget',NULL,'PLA',NULL,NULL,1,0,1,NULL,'No match requirement','Ideally used only in Placer County','Various usage restrictions based on funding subcategory','FY 26-27 TART TOT totals $5,347,400: $2,900,000 for TART Connect plus four subcategories ($150,000; $1,874,954; $277,500; $144,946). Prior year is the FY 25-26 fact sheet total ($5,463,510) less $2.9 million.');
INSERT INTO "funding_line" VALUES('tart-washoe','rtc-washoe-contribution','TART','Washoe RTC (TART Nevada service)','Regional Transportation Commission of Washoe County',296055.0,'fixed',288746.0,0.02,NULL,NULL,'budgeted','budget',NULL,'WAS',NULL,NULL,1,0,1,'Operations in Nevada.','No match requirement','Only applied to TART NV route','Fixed route service in Nevada; airport shuttle service in Tahoe in Washoe County','Revenue %s assigns 95.8% to Main Line and 4.2% to NLTE; NLTE Washoe County support is budgeted separately by TNT/TMA ($12,500).');
INSERT INTO "funding_line" VALUES('tart-truckee','town-of-truckee-contribution','TART','Town of Truckee (TART)','Town of Truckee (LTF)',230478.0,'fixed',256402.0,0.0,NULL,NULL,'budgeted','budget',NULL,'TRK',NULL,NULL,1,0,1,'TART Hwy 89 and Hwy 267 service; NLTE operations.','No match requirement',NULL,'TART Hwy 89 and Hwy 267 fixed route service, and NLTE services in Truckee',NULL);
INSERT INTO "funding_line" VALUES('tart-nsrp','resort-contribution','TART','North Shore Resort Partners','Private resorts',47900.0,'fixed',60000.0,0.0,NULL,NULL,'budgeted','budget',NULL,NULL,NULL,NULL,1,0,1,'Operating support for TART service and winter Park and Ride.','No match requirement',NULL,'TART operating only; operation contribution earmarked for winter service',NULL);
INSERT INTO "funding_line" VALUES('tart-nslp','free-fare-partnership','TART','North Shore Local Partners (free fares)','Tahoe Truckee Airport District, resorts, Town of Truckee',139000.0,'fixed',148500.0,0.0,NULL,NULL,'budgeted','budget',NULL,NULL,NULL,NULL,1,0,1,'Contribution to TART for operating free fares and winter Park and Ride shuttles.','No match requirement',NULL,'TART operations; free fares',NULL);
INSERT INTO "funding_line" VALUES('tart-martis','zone-of-benefit','TART','Martis Zones of Benefit','Martis Zone of Benefit',0.0,'fixed',50000.0,0.0,NULL,NULL,'none','none','FY 25-26 $50,000; $0 in the FY 26-27 plan.',NULL,NULL,NULL,1,0,1,'Budget contribution for Hwy 267 operations.','No match requirement',NULL,'Hwy 267 TART service only',NULL);
INSERT INTO "funding_line" VALUES('tart-5339','fta-5339-bus-and-bus-facilities','TART','FTA 5339 bus and facilities (TART)','Federal Transit Administration',0.0,'fixed',0.0,0.0,NULL,NULL,'capital','formula',NULL,NULL,0.8,NULL,1,0,1,'Capital funds for buses, equipment, and bus facilities.','Yes (capital)',NULL,'Lake Tahoe UZA and Nevada','Capital program, outside the operating model. FY 26-27 example UZA split: Placer $207,871 (FTA Allocation Split I35).');
INSERT INTO "funding_line" VALUES('tnt-tot-nlte','placer-county-transient-occupancy-tax','TNTTMA','Placer County TOT – NLTE','Placer County',162595.0,'fixed',NULL,0.04,NULL,NULL,'budgeted','budget',NULL,'PLA',NULL,NULL,1,0,1,NULL,'No match requirement',NULL,NULL,NULL);
INSERT INTO "funding_line" VALUES('tnt-tot-pr','placer-county-transient-occupancy-tax','TNTTMA','Placer County TOT – Park & Ride','Placer County',749956.0,'fixed',128580.0,0.04,NULL,NULL,'budgeted','budget',NULL,'PLA',NULL,NULL,1,0,1,NULL,'No match requirement',NULL,NULL,NULL);
INSERT INTO "funding_line" VALUES('tnt-tot-van','placer-county-transient-occupancy-tax','TNTTMA','Placer County TOT – Vanpools','Placer County',195800.0,'fixed',220818.0,0.04,NULL,NULL,'budgeted','budget',NULL,'PLA',NULL,NULL,1,0,1,NULL,'No match requirement',NULL,NULL,NULL);
INSERT INTO "funding_line" VALUES('tnt-tntn','visitor-bureau-contribution','TNTTMA','Travel North Tahoe Nevada (NLTE)','Travel North Tahoe Nevada',26421.0,'fixed',30390.0,0.0,NULL,NULL,'budgeted','budget',NULL,NULL,NULL,NULL,1,0,1,'Contribution for NLTE operations.','No match requirement','Ideally used only in NV','Airport shuttle service in CA/NV','The Local Funds fact sheet card shows "TTD budgeted $8,000," although the funded system is NLTE.');
INSERT INTO "funding_line" VALUES('tnt-washoe','county-contribution','TNTTMA','Washoe County (NLTE)','Washoe County',12500.0,'fixed',25000.0,0.0,NULL,NULL,'budgeted','budget',NULL,'WAS',NULL,NULL,1,0,1,NULL,'No match requirement',NULL,NULL,NULL);
INSERT INTO "funding_line" VALUES('tnt-rtaa','airport-authority-contribution','TNTTMA','Reno-Tahoe Airport Authority (NLTE)','Reno-Tahoe Airport Authority',12500.0,'fixed',0.0,0.0,NULL,NULL,'budgeted','budget',NULL,NULL,NULL,NULL,1,0,1,'Contribution for NLTE operations.','No match requirement',NULL,'Airport shuttle service in CA/NV',NULL);
INSERT INTO "funding_line" VALUES('tnt-truckee','town-of-truckee-contribution','TNTTMA','Town of Truckee (NLTE)','Town of Truckee',15500.0,'fixed',15500.0,0.0,NULL,NULL,'budgeted','budget',NULL,'TRK',NULL,NULL,1,0,1,NULL,'No match requirement',NULL,NULL,NULL);
INSERT INTO "funding_line" VALUES('tnt-truckee2','town-of-truckee-contribution','TNTTMA','Additional Truckee contribution (NLTE)','Truckee (not specified)',2927.0,'fixed',NULL,0.0,NULL,NULL,'budgeted','budget',NULL,NULL,NULL,NULL,1,0,1,NULL,'No match requirement',NULL,NULL,'The FY 25-26 per-route model lists Visit Truckee Tahoe ($2,932) for NLTE; confirm whether this is the same contribution.');
INSERT INTO "funding_line" VALUES('tnt-nevco','county-contribution','TNTTMA','Nevada County (Park & Ride)','Nevada County',16339.0,'fixed',NULL,0.0,NULL,NULL,'budgeted','budget',NULL,'NEV',NULL,NULL,1,0,1,NULL,'No match requirement',NULL,NULL,NULL);
INSERT INTO "funding_line" VALUES('tnt-northstar','resort-contribution','TNTTMA','Northstar (Park & Ride)','Northstar',3862.0,'fixed',21413.0,0.0,NULL,NULL,'budgeted','budget',NULL,NULL,NULL,NULL,1,0,1,NULL,'No match requirement',NULL,NULL,NULL);
INSERT INTO "funding_line" VALUES('tnt-palisades','resort-contribution','TNTTMA','Palisades Tahoe (Park & Ride)','Palisades Tahoe',124076.0,'fixed',119304.0,0.0,NULL,NULL,'budgeted','budget',NULL,NULL,NULL,NULL,1,0,1,NULL,'No match requirement',NULL,NULL,NULL);
INSERT INTO "funding_line" VALUES('tnt-ntca','nonprofit-contribution','TNTTMA','North Tahoe Community Alliance (Park & Ride)','North Tahoe Community Alliance',0.0,'fixed',487173.0,0.0,NULL,NULL,'none','none','FY 25-26 $487,173; $0 in the FY 26-27 budget, which relies on Placer County TOT instead.',NULL,NULL,NULL,1,0,1,NULL,'No match requirement',NULL,NULL,NULL);
INSERT INTO "funding_line" VALUES('tnt-fares','passenger-fares','TNTTMA','Fares – North Lake Tahoe Express','Riders',377656.0,'fixed',445263.0,0.0,NULL,NULL,'budgeted','earned',NULL,NULL,NULL,NULL,0,0,1,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "funding_line" VALUES('tnt-reserve','reserve-draw','TNTTMA','NLTE reserve','TNT/TMA',240000.0,'fixed',NULL,0.0,0,NULL,'budgeted','onetime','Included so the NLTE FY 26-27 budget balances (Table 7 note).',NULL,NULL,NULL,1,0,1,NULL,'No match requirement',NULL,NULL,NULL);
CREATE TABLE funding_line_year (
  line_id   TEXT NOT NULL REFERENCES funding_line (line_id),
  fy_index  INTEGER NOT NULL REFERENCES fiscal_year (fy_index) CHECK (fy_index > 0),
  amount    REAL NOT NULL CHECK (amount >= 0),
  PRIMARY KEY (line_id, fy_index)
);
INSERT INTO "funding_line_year" VALUES('ttd-5310',1,76000.0);
INSERT INTO "funding_line_year" VALUES('ttd-5310',2,0.0);
INSERT INTO "funding_line_year" VALUES('ttd-5310',3,78300.0);
INSERT INTO "funding_line_year" VALUES('ttd-5310',4,0.0);
INSERT INTO "funding_line_year" VALUES('ttd-lctop',1,0.0);
INSERT INTO "funding_line_year" VALUES('ttd-lctop',2,265500.0);
INSERT INTO "funding_line_year" VALUES('ttd-lctop',3,0.0);
INSERT INTO "funding_line_year" VALUES('ttd-lctop',4,265500.0);
INSERT INTO "funding_line_year" VALUES('ttd-ktb',1,29678.0);
INSERT INTO "funding_line_year" VALUES('ttd-crp',1,537090.0);
INSERT INTO "funding_line_year" VALUES('ttd-eldebs',1,100155.0);
INSERT INTO "funding_line_year" VALUES('ttd-plaebs',1,29676.0);
INSERT INTO "funding_line_year" VALUES('ll-douglas',1,850000.0);
CREATE TABLE funding_program (
  program_id    TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  level         TEXT NOT NULL CHECK (level IN ('federal', 'state', 'local', 'private', 'fare', 'other')),
  grantor       TEXT
);
INSERT INTO "funding_program" VALUES('fta-5307-urbanized-area-formula','FTA 5307 Urbanized Area Formula','federal',NULL);
INSERT INTO "funding_program" VALUES('fta-5307-flexed-cmaq','FTA 5307 (flexed CMAQ)','federal',NULL);
INSERT INTO "funding_program" VALUES('fta-5307-carryover','FTA 5307 carryover','federal',NULL);
INSERT INTO "funding_program" VALUES('fta-5311-rural-area-formula','FTA 5311 Rural Area Formula','federal',NULL);
INSERT INTO "funding_program" VALUES('fta-5310-enhanced-mobility','FTA 5310 Enhanced Mobility','federal',NULL);
INSERT INTO "funding_program" VALUES('fta-5310-carryover','FTA 5310 carryover','federal',NULL);
INSERT INTO "funding_program" VALUES('tda-local-transportation-fund-ltf','TDA Local Transportation Fund (LTF)','state',NULL);
INSERT INTO "funding_program" VALUES('tda-state-transit-assistance-sta','TDA State Transit Assistance (STA)','state',NULL);
INSERT INTO "funding_program" VALUES('lctop','LCTOP','state',NULL);
INSERT INTO "funding_program" VALUES('electrification-credits','Electrification credits','state',NULL);
INSERT INTO "funding_program" VALUES('sb-125','SB 125','state',NULL);
INSERT INTO "funding_program" VALUES('nevada-state-parks','Nevada State Parks','state',NULL);
INSERT INTO "funding_program" VALUES('nevada-state-allocation','Nevada State allocation','state',NULL);
INSERT INTO "funding_program" VALUES('local-appropriation','Local appropriation','local',NULL);
INSERT INTO "funding_program" VALUES('visitor-authority-contribution','Visitor authority contribution','local',NULL);
INSERT INTO "funding_program" VALUES('interest','Interest','other',NULL);
INSERT INTO "funding_program" VALUES('private-contribution','Private contribution','private',NULL);
INSERT INTO "funding_program" VALUES('fhwa-carbon-reduction-program','FHWA Carbon Reduction Program','federal',NULL);
INSERT INTO "funding_program" VALUES('county-contribution','County contribution','local',NULL);
INSERT INTO "funding_program" VALUES('passenger-fares','Passenger fares','fare',NULL);
INSERT INTO "funding_program" VALUES('fta-5339-bus-and-bus-facilities','FTA 5339 Bus and Bus Facilities','federal',NULL);
INSERT INTO "funding_program" VALUES('lake-link-funding-agreement','Lake Link funding agreement','local',NULL);
INSERT INTO "funding_program" VALUES('transportation-mitigation-fee','Transportation mitigation fee','private',NULL);
INSERT INTO "funding_program" VALUES('lake-link-partner-contribution','Lake Link partner contribution','private',NULL);
INSERT INTO "funding_program" VALUES('state-of-good-repair-sgr','State of Good Repair (SGR)','state',NULL);
INSERT INTO "funding_program" VALUES('placer-county-transient-occupancy-tax','Placer County transient occupancy tax','local',NULL);
INSERT INTO "funding_program" VALUES('rtc-washoe-contribution','RTC Washoe contribution','local',NULL);
INSERT INTO "funding_program" VALUES('town-of-truckee-contribution','Town of Truckee contribution','local',NULL);
INSERT INTO "funding_program" VALUES('resort-contribution','Resort contribution','private',NULL);
INSERT INTO "funding_program" VALUES('free-fare-partnership','Free-fare partnership','local',NULL);
INSERT INTO "funding_program" VALUES('zone-of-benefit','Zone of benefit','local',NULL);
INSERT INTO "funding_program" VALUES('visitor-bureau-contribution','Visitor bureau contribution','private',NULL);
INSERT INTO "funding_program" VALUES('airport-authority-contribution','Airport authority contribution','local',NULL);
INSERT INTO "funding_program" VALUES('nonprofit-contribution','Nonprofit contribution','private',NULL);
INSERT INTO "funding_program" VALUES('reserve-draw','Reserve draw','other',NULL);
CREATE TABLE jurisdiction (
  jurisdiction_id TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  short_name    TEXT NOT NULL,
  state         TEXT NOT NULL CHECK (state IN ('CA', 'NV'))
);
INSERT INTO "jurisdiction" VALUES('CSLT','City of South Lake Tahoe','CSLT','CA');
INSERT INTO "jurisdiction" VALUES('ELD','El Dorado County','El Dorado','CA');
INSERT INTO "jurisdiction" VALUES('PLA','Placer County','Placer','CA');
INSERT INTO "jurisdiction" VALUES('NEV','Nevada County','Nevada Co.','CA');
INSERT INTO "jurisdiction" VALUES('TRK','Town of Truckee','Truckee','CA');
INSERT INTO "jurisdiction" VALUES('DOU','Douglas County','Douglas','NV');
INSERT INTO "jurisdiction" VALUES('WAS','Washoe County','Washoe','NV');
INSERT INTO "jurisdiction" VALUES('CC','Carson City','Carson City','NV');
CREATE TABLE operator (
  operator_id      TEXT PRIMARY KEY,
  name             TEXT NOT NULL,
  cost_per_vsh     REAL NOT NULL CHECK (cost_per_vsh >= 0),   -- fully allocated operating cost per vehicle service hour
  annual_escalator REAL NOT NULL,                              -- cost growth per year
  basis            TEXT
);
INSERT INTO "operator" VALUES('TTD','TTD (directly operated)',214.66,0.04,'Total operating cost per VSH from FY 24-25 actuals plus 4% per year inflation');
INSERT INTO "operator" VALUES('Via','Via (SSTMA Lake Link contract)',68.7,0.04,'SSTMA Lake Link contract costs for 2027 plus fixed admin costs');
INSERT INTO "operator" VALUES('TART','TART (Placer County)',185.83,0.04,'FY 24-25 actuals cost model, Existing Conditions report, plus 4% per year');
INSERT INTO "operator" VALUES('Placer Via','Placer Via / Downtowner (TART Connect)',107.23,0.05,'FY 24-25 actuals plus 5% per year, the contract escalation rate');
INSERT INTO "operator" VALUES('Truckee','Truckee (TART paratransit)',1.345293265175516809e+02,0.04,'FY 24-25 actuals cost model plus 4% per year');
INSERT INTO "operator" VALUES('MRTW','My Ride to Work (TNT/TMA contract)',200.9839,0.03,'Park and Ride bus contract cost FY 25-26 plus 3%; the costs tab uses the bus rate for all MRTW service');
INSERT INTO "operator" VALUES('BUDGET','Budget amount (no hourly rate)',0.0,0.04,'Annual cost entered directly; escalated at the financial plan general inflation rate');
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
INSERT INTO "service" VALUES('19X','Route 19X','19X','TTD','TTD','TTD','rural','fixed',1,0,1,10747.0,2250.4,61381.0,'24-25',NULL,NULL,613805.0,NULL,'Nevada Route','Carson City, Douglas County',NULL);
INSERT INTO "service" VALUES('22','Route 22','22','TTD','TTD','TTD','rural','fixed',1,0,1,18457.0,4409.6,121654.0,'24-25',NULL,NULL,1210300.0,NULL,'Nevada Route','Douglas County',NULL);
INSERT INTO "service" VALUES('28','Route 28 (East Shore Express)','28','TTD','TTD','TTD','urban','seasonal',1,0,1,24699.0,1192.7,22330.0,'24-25',NULL,NULL,269366.0,NULL,'Nevada Seasonal Route','Washoe County',NULL);
INSERT INTO "service" VALUES('30','Route 30 (Emerald Bay Shuttle)','30','TTD','Via','TTD','urban','seasonal',1,0,1,10700.0,3500.0,9850.0,'26-27 estimate',NULL,NULL,517288.0,NULL,'California Seasonal Route','El Dorado County','Pilot funded through FY 27-28. The costs tab looks up operator "Via" ($68.70/VSH, the Lake Link rate). VRH Rates lists $147.80/VSH for Route 30 (TTD–Via), and the FY 26-27 Emerald Bay Shuttle budget is $517,288.');
INSERT INTO "service" VALUES('50','Route 50','50','TTD','TTD','TTD','urban','fixed',1,0,1,170332.0,9418.6,134562.0,'24-25',NULL,NULL,1898048.0,NULL,'California Route (portion in NV)','CSLT, El Dorado County, Douglas County',NULL);
INSERT INTO "service" VALUES('51','Route 51','51','TTD','TTD','TTD','urban','fixed',1,0,1,115.0,167.0,1700.0,'24-25',NULL,NULL,29892.0,NULL,'California Route (portion in NV)','CSLT, El Dorado County, Douglas County','TTD expanded operations supported by the Tahoe Douglas Visitor Authority (Local Funds fact sheet).');
INSERT INTO "service" VALUES('55','Route 55','55','TTD','TTD','TTD','urban','fixed',1,0,1,55609.0,9312.2,111689.0,'24-25',NULL,NULL,1759504.0,NULL,'California Route','CSLT, El Dorado County',NULL);
INSERT INTO "service" VALUES('ADA-TTD','TTD ADA paratransit','ADA (TTD)','TTD','TTD','TTD','urban','paratransit',1,0,1,14556.0,5429.0,71677.0,'24-25',NULL,NULL,1061778.0,NULL,'CA/NV','(none listed)','Costs tab lists CA/NV with no local conditions. Jurisdiction shares are a placeholder that follows Route 50.');
INSERT INTO "service" VALUES('LL','Lake Link microtransit','Lake Link','SSTMA','Via','Lake Link','urban','microtransit',1,0,1,223047.0,47002.0,366322.0,'25-26',NULL,NULL,3228840.0,NULL,'CA/NV','Zone 1 (Douglas County), Zone 2 (CSLT), Zone 3 (CSLT)','VSH are from the contract, not actuals (costs tab U12). Zone split follows the even example split in Operating Stats rows 16–18.');
INSERT INTO "service" VALUES('TART-WS','Main Line – West Shore','West Shore','TART','TART','Main Line','urban','fixed',1,0,1,21205.0,4237.5,82391.1,'25-26',NULL,NULL,NULL,NULL,'California route','Placer County','Main Line segment. The costs tab Main Line subtotal (row 16) is not counted again.');
INSERT INTO "service" VALUES('TART-NS','Main Line – North Shore','North Shore','TART','TART','Main Line','urban','fixed',1,0,1,92011.0,4983.5,113132.1,'25-26',NULL,NULL,NULL,NULL,'California route','Placer County','Main Line segment.');
INSERT INTO "service" VALUES('TART-NV','Main Line – Nevada','Nevada','TART','TART','Main Line','urban','fixed',1,0,1,34977.0,4219.3125,63697.0,'25-26',NULL,NULL,NULL,NULL,'Nevada route','Washoe County','Main Line segment in Washoe County; supported by Washoe RTC.');
INSERT INTO "service" VALUES('89','Hwy 89 (Tahoe City–Truckee)','Hwy 89','TART','TART','TART','mixed','fixed',1,0,1,71136.0,8331.75,167948.7,'25-26',NULL,NULL,NULL,NULL,'California route','Placer County, Nevada County','Urban and rural class is a placeholder: the Truckee end lies outside the Lake Tahoe UZA.');
INSERT INTO "service" VALUES('267','Hwy 267 (Kings Beach–Truckee)','Hwy 267','TART','TART','TART','mixed','fixed',1,0,1,73556.0,8420.233333,176999.3,'25-26',NULL,NULL,NULL,NULL,'California route','Placer County, Nevada County','Urban and rural class is a placeholder.');
INSERT INTO "service" VALUES('NIGHT','Night service','Night','TART','TART','TART','urban','fixed',1,0,1,4725.0,2985.0,57781.2,'25-26',NULL,NULL,NULL,NULL,'California route','Placer County',NULL);
INSERT INTO "service" VALUES('ADA-PLA','TART ADA paratransit','ADA (TART)','TART','Truckee','TART','urban','paratransit',1,0,1,3573.0,1951.65,34749.0,'25-26',NULL,NULL,NULL,NULL,'California route','(none listed)','No local conditions listed; Placer County is a placeholder.');
INSERT INTO "service" VALUES('TC','TART Connect microtransit','TART Connect','TART','Placer Via','TART','urban','microtransit',1,0,1,157369.0,27342.51,544888.71,'25-26',NULL,NULL,2997578.0,NULL,'California route','Placer County',NULL);
INSERT INTO "service" VALUES('PR-W','Park & Ride shuttle (winter)','P&R winter','TNTTMA','MRTW','TNT/TMA','mixed','seasonal',1,0,1,NULL,2500.0,NULL,'estimate',NULL,NULL,894233.0,NULL,'California route','Placer County, Nevada County','Costs tab estimate (2,500 VSH). TNT/TMA FY 26-27 Park & Ride budget is $894,233 for both seasons.');
INSERT INTO "service" VALUES('PR-S','Park & Ride shuttle (summer)','P&R summer','TNTTMA','MRTW','TNT/TMA','mixed','seasonal',1,0,1,NULL,500.0,NULL,'estimate',NULL,NULL,NULL,NULL,'California route','Placer County, Nevada County','Costs tab estimate (500 VSH).');
INSERT INTO "service" VALUES('NLTE','North Lake Tahoe Express (airport)','NLTE','TNTTMA','MRTW','TNT/TMA','mixed','airport',1,0,1,NULL,1200.0,NULL,'estimate',NULL,NULL,694260.0,NULL,'CA/NV','Placer County, Nevada County, Washoe County','Costs tab estimate based on FY 25-26 budget (1,200 VSH × $200.98). TNT/TMA FY 26-27 NLTE budget is $694,260.');
INSERT INTO "service" VALUES('VAN','Vanpools (TNT/TMA)','Vanpools','TNTTMA','BUDGET','TNT/TMA','mixed','vanpool',1,0,1,NULL,NULL,NULL,'26-27 budget',NULL,195800.0,195800.0,NULL,'CA/NV','Placer County, Washoe County','Not in the costs tab. Included because Revenue %s has a Vanpools column; cost is the TNT/TMA FY 26-27 vanpool budget.');
INSERT INTO "service" VALUES('SP-US50','Replace 19X with US 50 service (4 round trips)','US 50 service','TTD','BUDGET',NULL,'rural','fixed',1,1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'The financial plan adds this cost without removing Route 19X. Exclude Route 19X to model the replacement.');
INSERT INTO "service" VALUES('SP-28','Seasonal Route 28 extension to Spooner Mobility Hub','28 to Spooner','TTD','BUDGET',NULL,'urban','seasonal',1,1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'Jurisdiction split is a placeholder.');
INSERT INTO "service" VALUES('SP-EBS','Continue Emerald Bay Shuttle (Route 30) beyond the pilot','30 after pilot','TTD','BUDGET',NULL,'urban','seasonal',1,1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "service" VALUES('SP-MEY','Pilot co-mingled paratransit and microtransit to Meyers','Meyers pilot','SSTMA','BUDGET',NULL,'urban','microtransit',1,1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'Assumes a third-party contractor at Lake Link costs (Table 2 note 4).');
INSERT INTO "service" VALUES('SP-LTCC','Discontinue Route 50 summer deviation to LTCC','50 LTCC change','TTD','BUDGET',NULL,'urban','fixed',1,1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'50',NULL,NULL,'Cost reduction applied to Route 50.');
INSERT INTO "service" VALUES('SP-INC','Reinstate TART Connect in Incline Village','Incline Connect','TART','BUDGET',NULL,'urban','microtransit',1,1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO "service" VALUES('SP-VAN','Add vanpools between Reno and Truckee/North Lake Tahoe','More vanpools','TNTTMA','BUDGET',NULL,'mixed','vanpool',1,1,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'Two vans per year at $12,000 per van (TNTTMA $ J45:J46).');
CREATE TABLE service_jurisdiction (
  service_id      TEXT NOT NULL REFERENCES service (service_id),
  jurisdiction_id TEXT NOT NULL REFERENCES jurisdiction (jurisdiction_id),
  share           REAL NOT NULL CHECK (share > 0),
  is_placeholder  INTEGER NOT NULL DEFAULT 1 CHECK (is_placeholder IN (0, 1)),
  PRIMARY KEY (service_id, jurisdiction_id)
);
INSERT INTO "service_jurisdiction" VALUES('19X','CC',0.5,1);
INSERT INTO "service_jurisdiction" VALUES('19X','DOU',0.5,1);
INSERT INTO "service_jurisdiction" VALUES('22','DOU',1.0,0);
INSERT INTO "service_jurisdiction" VALUES('28','WAS',1.0,0);
INSERT INTO "service_jurisdiction" VALUES('30','ELD',1.0,0);
INSERT INTO "service_jurisdiction" VALUES('50','CSLT',3.333333333333333148e-01,1);
INSERT INTO "service_jurisdiction" VALUES('50','ELD',3.333333333333333148e-01,1);
INSERT INTO "service_jurisdiction" VALUES('50','DOU',3.333333333333333148e-01,1);
INSERT INTO "service_jurisdiction" VALUES('51','CSLT',3.333333333333333148e-01,1);
INSERT INTO "service_jurisdiction" VALUES('51','ELD',3.333333333333333148e-01,1);
INSERT INTO "service_jurisdiction" VALUES('51','DOU',3.333333333333333148e-01,1);
INSERT INTO "service_jurisdiction" VALUES('55','CSLT',0.5,1);
INSERT INTO "service_jurisdiction" VALUES('55','ELD',0.5,1);
INSERT INTO "service_jurisdiction" VALUES('ADA-TTD','CSLT',3.333333333333333148e-01,1);
INSERT INTO "service_jurisdiction" VALUES('ADA-TTD','ELD',3.333333333333333148e-01,1);
INSERT INTO "service_jurisdiction" VALUES('ADA-TTD','DOU',3.333333333333333148e-01,1);
INSERT INTO "service_jurisdiction" VALUES('LL','DOU',3.333333333333333148e-01,1);
INSERT INTO "service_jurisdiction" VALUES('LL','CSLT',6.666666666666666296e-01,1);
INSERT INTO "service_jurisdiction" VALUES('TART-WS','PLA',1.0,0);
INSERT INTO "service_jurisdiction" VALUES('TART-NS','PLA',1.0,0);
INSERT INTO "service_jurisdiction" VALUES('TART-NV','WAS',1.0,0);
INSERT INTO "service_jurisdiction" VALUES('89','PLA',0.5,1);
INSERT INTO "service_jurisdiction" VALUES('89','NEV',0.5,1);
INSERT INTO "service_jurisdiction" VALUES('267','PLA',0.5,1);
INSERT INTO "service_jurisdiction" VALUES('267','NEV',0.5,1);
INSERT INTO "service_jurisdiction" VALUES('NIGHT','PLA',1.0,0);
INSERT INTO "service_jurisdiction" VALUES('ADA-PLA','PLA',1.0,1);
INSERT INTO "service_jurisdiction" VALUES('TC','PLA',1.0,0);
INSERT INTO "service_jurisdiction" VALUES('PR-W','PLA',0.5,1);
INSERT INTO "service_jurisdiction" VALUES('PR-W','NEV',0.5,1);
INSERT INTO "service_jurisdiction" VALUES('PR-S','PLA',0.5,1);
INSERT INTO "service_jurisdiction" VALUES('PR-S','NEV',0.5,1);
INSERT INTO "service_jurisdiction" VALUES('NLTE','PLA',3.333333333333333148e-01,1);
INSERT INTO "service_jurisdiction" VALUES('NLTE','NEV',3.333333333333333148e-01,1);
INSERT INTO "service_jurisdiction" VALUES('NLTE','WAS',3.333333333333333148e-01,1);
INSERT INTO "service_jurisdiction" VALUES('VAN','PLA',0.5,1);
INSERT INTO "service_jurisdiction" VALUES('VAN','WAS',0.5,1);
INSERT INTO "service_jurisdiction" VALUES('SP-US50','CC',0.5,1);
INSERT INTO "service_jurisdiction" VALUES('SP-US50','DOU',0.5,1);
INSERT INTO "service_jurisdiction" VALUES('SP-28','WAS',0.5,1);
INSERT INTO "service_jurisdiction" VALUES('SP-28','DOU',0.5,1);
INSERT INTO "service_jurisdiction" VALUES('SP-EBS','ELD',1.0,1);
INSERT INTO "service_jurisdiction" VALUES('SP-MEY','ELD',1.0,1);
INSERT INTO "service_jurisdiction" VALUES('SP-LTCC','CSLT',3.333333333333333148e-01,1);
INSERT INTO "service_jurisdiction" VALUES('SP-LTCC','ELD',3.333333333333333148e-01,1);
INSERT INTO "service_jurisdiction" VALUES('SP-LTCC','DOU',3.333333333333333148e-01,1);
INSERT INTO "service_jurisdiction" VALUES('SP-INC','WAS',1.0,1);
INSERT INTO "service_jurisdiction" VALUES('SP-VAN','WAS',0.5,1);
INSERT INTO "service_jurisdiction" VALUES('SP-VAN','NEV',0.5,1);
CREATE TABLE service_year (
  service_id      TEXT NOT NULL REFERENCES service (service_id),
  fy_index        INTEGER NOT NULL REFERENCES fiscal_year (fy_index),
  active          INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
  scheduled_cost  REAL,
  PRIMARY KEY (service_id, fy_index)
);
INSERT INTO "service_year" VALUES('30',0,1,NULL);
INSERT INTO "service_year" VALUES('30',1,1,NULL);
INSERT INTO "service_year" VALUES('30',2,0,NULL);
INSERT INTO "service_year" VALUES('30',3,0,NULL);
INSERT INTO "service_year" VALUES('30',4,0,NULL);
INSERT INTO "service_year" VALUES('SP-US50',0,1,476500.0);
INSERT INTO "service_year" VALUES('SP-US50',1,1,495600.0);
INSERT INTO "service_year" VALUES('SP-US50',2,1,514600.0);
INSERT INTO "service_year" VALUES('SP-US50',3,1,533700.0);
INSERT INTO "service_year" VALUES('SP-US50',4,1,552700.0);
INSERT INTO "service_year" VALUES('SP-28',0,1,0.0);
INSERT INTO "service_year" VALUES('SP-28',1,1,137200.0);
INSERT INTO "service_year" VALUES('SP-28',2,1,142400.0);
INSERT INTO "service_year" VALUES('SP-28',3,1,147700.0);
INSERT INTO "service_year" VALUES('SP-28',4,1,153000.0);
INSERT INTO "service_year" VALUES('SP-EBS',0,1,0.0);
INSERT INTO "service_year" VALUES('SP-EBS',1,1,0.0);
INSERT INTO "service_year" VALUES('SP-EBS',2,1,558700.0);
INSERT INTO "service_year" VALUES('SP-EBS',3,1,579400.0);
INSERT INTO "service_year" VALUES('SP-EBS',4,1,600100.0);
INSERT INTO "service_year" VALUES('SP-MEY',0,1,0.0);
INSERT INTO "service_year" VALUES('SP-MEY',1,1,357300.0);
INSERT INTO "service_year" VALUES('SP-MEY',2,1,371000.0);
INSERT INTO "service_year" VALUES('SP-MEY',3,1,384800.0);
INSERT INTO "service_year" VALUES('SP-MEY',4,1,398500.0);
INSERT INTO "service_year" VALUES('SP-LTCC',0,1,-10600.0);
INSERT INTO "service_year" VALUES('SP-LTCC',1,1,-11000.0);
INSERT INTO "service_year" VALUES('SP-LTCC',2,1,-11400.0);
INSERT INTO "service_year" VALUES('SP-LTCC',3,1,-11800.0);
INSERT INTO "service_year" VALUES('SP-LTCC',4,1,-12300.0);
INSERT INTO "service_year" VALUES('SP-INC',0,1,0.0);
INSERT INTO "service_year" VALUES('SP-INC',1,1,1044400.0);
INSERT INTO "service_year" VALUES('SP-INC',2,1,1086200.0);
INSERT INTO "service_year" VALUES('SP-INC',3,1,1129600.0);
INSERT INTO "service_year" VALUES('SP-INC',4,1,1402800.0);
INSERT INTO "service_year" VALUES('SP-VAN',0,1,25000.0);
INSERT INTO "service_year" VALUES('SP-VAN',1,1,26000.0);
INSERT INTO "service_year" VALUES('SP-VAN',2,1,0.0);
INSERT INTO "service_year" VALUES('SP-VAN',3,1,0.0);
INSERT INTO "service_year" VALUES('SP-VAN',4,1,0.0);
CREATE TABLE source_document (
  document_id   TEXT PRIMARY KEY,                -- short key used by citations, e.g. 'plan'
  file_name     TEXT NOT NULL,
  description   TEXT
);
INSERT INTO "source_document" VALUES('scen','Example Transit Financial Scenario Workbook.xlsx','Current operator costs per route (costs tab), route conditions, and operator rates (VRH Rates).');
INSERT INTO "source_document" VALUES('plan','Financial PlanG.xlsx','Revenue %s, Actual Revenues, Per Route Model, Operating Stats, FTA split, five-year plan tables, TNT/TMA budget.');
INSERT INTO "source_document" VALUES('v1g','Funding Model V1G.xlsx','Earlier funding model; source of the corrected service-hour bases.');
INSERT INTO "source_document" VALUES('sstma','SSTMA - multijursidiction transit services - financial working morking model.xlsb.xlsx','Multi-jurisdiction cost-share method and Lake Link zones.');
INSERT INTO "source_document" VALUES('fed','Federal Funds - FINAL.pdf','Federal funding fact sheet (FY 25-26 budgeted amounts, purpose, match, restrictions).');
INSERT INTO "source_document" VALUES('state','State Funds - FINAL.pdf','State funding fact sheet.');
INSERT INTO "source_document" VALUES('loc1','Local Funds 1 of 2 - FINAL.pdf','Local funding fact sheet, part 1.');
INSERT INTO "source_document" VALUES('loc2','Local Funds 2 of 2 - FINAL.pdf','Local funding fact sheet, part 2 (Lake Link partners).');
CREATE INDEX ix_citation_entity ON citation (entity_type, entity_id);
CREATE INDEX ix_rule_line ON eligibility_rule (line_id);
CREATE INDEX ix_service_agency ON service (agency_id);
CREATE INDEX ix_line_recipient ON funding_line (recipient_agency_id);
COMMIT;
