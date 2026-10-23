"""Source data for the Lake Tahoe Region transit funding model.

Every value here was read from the workbooks and fact sheets in the project folder. Citations are
(document key, locator) pairs; build.py turns them into citation rows. Edit values here, then run
tools/build.py to regenerate data/seed.json, data/seed.js, and data/funding_model.sqlite.
"""

YEARS = ['FY 26-27', 'FY 27-28', 'FY 28-29', 'FY 29-30', 'FY 30-31']

DOCUMENTS = {
    'scen': ('Example Transit Financial Scenario Workbook.xlsx', 'Current operator costs per route (costs tab), route conditions, and operator rates (VRH Rates).'),
    'plan': ('Financial PlanG.xlsx', 'Revenue %s, Actual Revenues, Per Route Model, Operating Stats, FTA split, five-year plan tables, TNT/TMA budget.'),
    'v1g': ('Funding Model V1G.xlsx', 'Earlier funding model; source of the corrected service-hour bases.'),
    'sstma': ('SSTMA - multijursidiction transit services - financial working morking model.xlsb.xlsx', 'Multi-jurisdiction cost-share method and Lake Link zones.'),
    'fed': ('Federal Funds - FINAL.pdf', 'Federal funding fact sheet (FY 25-26 budgeted amounts, purpose, match, restrictions).'),
    'state': ('State Funds - FINAL.pdf', 'State funding fact sheet.'),
    'loc1': ('Local Funds 1 of 2 - FINAL.pdf', 'Local funding fact sheet, part 1.'),
    'loc2': ('Local Funds 2 of 2 - FINAL.pdf', 'Local funding fact sheet, part 2 (Lake Link partners).'),
}

AGENCIES = [
    ('TTD', 'Tahoe Transportation District', 'TTD'),
    ('SSTMA', 'South Shore TMA (Lake Link)', 'Lake Link'),
    ('TART', 'Placer County TART', 'TART'),
    ('TNTTMA', 'Truckee North Tahoe TMA', 'TNT/TMA'),
    ('REGION', 'Regional or new (not yet assigned)', 'Regional'),
]

JURISDICTIONS = [
    ('CSLT', 'City of South Lake Tahoe', 'CSLT', 'CA'),
    ('ELD', 'El Dorado County', 'El Dorado', 'CA'),
    ('PLA', 'Placer County', 'Placer', 'CA'),
    ('NEV', 'Nevada County', 'Nevada Co.', 'CA'),
    ('TRK', 'Town of Truckee', 'Truckee', 'CA'),
    ('DOU', 'Douglas County', 'Douglas', 'NV'),
    ('WAS', 'Washoe County', 'Washoe', 'NV'),
    ('CC', 'Carson City', 'Carson City', 'NV'),
]

# id, name, cost per VSH, escalator, basis, citation
OPERATORS = [
    ('TTD', 'TTD (directly operated)', 214.66, 0.04, 'Total operating cost per VSH from FY 24-25 actuals plus 4% per year inflation', [('scen', 'VRH Rates J7, L7')]),
    ('Via', 'Via (SSTMA Lake Link contract)', 68.70, 0.04, 'SSTMA Lake Link contract costs for 2027 plus fixed admin costs', [('scen', 'VRH Rates J9, L9')]),
    ('TART', 'TART (Placer County)', 185.83, 0.04, 'FY 24-25 actuals cost model, Existing Conditions report, plus 4% per year', [('scen', 'VRH Rates J14, L14')]),
    ('Placer Via', 'Placer Via / Downtowner (TART Connect)', 107.23, 0.05, 'FY 24-25 actuals plus 5% per year, the contract escalation rate', [('scen', 'VRH Rates J15, L15')]),
    ('Truckee', 'Truckee (TART paratransit)', 134.52932651755168, 0.04, 'FY 24-25 actuals cost model plus 4% per year', [('scen', 'VRH Rates J16, L16')]),
    ('MRTW', 'My Ride to Work (TNT/TMA contract)', 200.9839, 0.03, 'Park and Ride bus contract cost FY 25-26 plus 3%; the costs tab uses the bus rate for all MRTW service', [('scen', 'VRH Rates J20, L20; costs X35')]),
    ('BUDGET', 'Budget amount (no hourly rate)', 0.0, 0.04, 'Annual cost entered directly; escalated at the financial plan general inflation rate', [('plan', 'T2-4 O1 (4% general escalator)')]),
]

THIRD = 1 / 3


def svc(id, name, short, agency, operator, **o):
    d = dict(id=id, name=name, short=short, agency=agency, operator=operator, group='', state_cond='', local_cond='', area='urban',
             type='fixed', federalized=True, trips=None, vsh=None, vsm=None, data_year='', rate_override=None, cost_override=None,
             schedule=None, active_years=None, included=True, plan=False, juris={}, juris_placeholder=True, ref_cost=None,
             ref_cite=None, note='', cite=None, adjusts=None)
    d.update(o)
    return d


def ct(row):
    return [('scen', f'costs row {row}')]


def t24(row):
    return [('plan', f'T2-4 A1 TTD LL Costs G{row} (route cost incl. allocated fixed cost)')]


SERVICES = [
    svc('19X', 'Route 19X', '19X', 'TTD', 'TTD', group='TTD', state_cond='Nevada Route', local_cond='Carson City, Douglas County', area='rural', trips=10747, vsh=2250.4, vsm=61381, data_year='24-25', juris={'CC': 0.5, 'DOU': 0.5}, ref_cost=613805, ref_cite=t24(142), cite=ct(4)),
    svc('22', 'Route 22', '22', 'TTD', 'TTD', group='TTD', state_cond='Nevada Route', local_cond='Douglas County', area='rural', trips=18457, vsh=4409.6, vsm=121654, data_year='24-25', juris={'DOU': 1}, juris_placeholder=False, ref_cost=1210300, ref_cite=t24(151), cite=ct(5)),
    svc('28', 'Route 28 (East Shore Express)', '28', 'TTD', 'TTD', group='TTD', state_cond='Nevada Seasonal Route', local_cond='Washoe County', type='seasonal', trips=24699, vsh=1192.7, vsm=22330, data_year='24-25', juris={'WAS': 1}, juris_placeholder=False, ref_cost=269366, ref_cite=t24(160), cite=ct(6)),
    svc('30', 'Route 30 (Emerald Bay Shuttle)', '30', 'TTD', 'Via', group='TTD', state_cond='California Seasonal Route', local_cond='El Dorado County', type='seasonal', trips=10700, vsh=3500, vsm=9850, data_year='26-27 estimate', juris={'ELD': 1}, juris_placeholder=False, active_years=[True, True, False, False, False], ref_cost=517288, ref_cite=t24(169) + [('plan', 'T2-4 Table 2 row 20')],
        note='Pilot funded through FY 27-28. The costs tab looks up operator "Via" ($68.70/VSH, the Lake Link rate). VRH Rates lists $147.80/VSH for Route 30 (TTD–Via), and the FY 26-27 Emerald Bay Shuttle budget is $517,288.', cite=ct(7)),
    svc('50', 'Route 50', '50', 'TTD', 'TTD', group='TTD', state_cond='California Route (portion in NV)', local_cond='CSLT, El Dorado County, Douglas County', trips=170332, vsh=9418.6, vsm=134562, data_year='24-25', juris={'CSLT': THIRD, 'ELD': THIRD, 'DOU': THIRD}, ref_cost=1898048, ref_cite=t24(175), cite=ct(8)),
    svc('51', 'Route 51', '51', 'TTD', 'TTD', group='TTD', state_cond='California Route (portion in NV)', local_cond='CSLT, El Dorado County, Douglas County', trips=115, vsh=167, vsm=1700, data_year='24-25', juris={'CSLT': THIRD, 'ELD': THIRD, 'DOU': THIRD}, ref_cost=29892, ref_cite=t24(186), note='TTD expanded operations supported by the Tahoe Douglas Visitor Authority (Local Funds fact sheet).', cite=ct(9)),
    svc('55', 'Route 55', '55', 'TTD', 'TTD', group='TTD', state_cond='California Route', local_cond='CSLT, El Dorado County', trips=55609, vsh=9312.2, vsm=111689, data_year='24-25', juris={'CSLT': 0.5, 'ELD': 0.5}, ref_cost=1759504, ref_cite=t24(196), cite=ct(10)),
    svc('ADA-TTD', 'TTD ADA paratransit', 'ADA (TTD)', 'TTD', 'TTD', group='TTD', state_cond='CA/NV', local_cond='(none listed)', type='paratransit', trips=14556, vsh=5429, vsm=71677, data_year='24-25', juris={'CSLT': THIRD, 'ELD': THIRD, 'DOU': THIRD}, ref_cost=1061778, ref_cite=t24(206),
        note='Costs tab lists CA/NV with no local conditions. Jurisdiction shares are a placeholder that follows Route 50.', cite=ct(11)),
    svc('LL', 'Lake Link microtransit', 'Lake Link', 'SSTMA', 'Via', group='Lake Link', state_cond='CA/NV', local_cond='Zone 1 (Douglas County), Zone 2 (CSLT), Zone 3 (CSLT)', type='microtransit', trips=223047, vsh=47002, vsm=366322, data_year='25-26', juris={'DOU': THIRD, 'CSLT': 2 * THIRD}, ref_cost=3228840, ref_cite=[('plan', 'T2-4 G26 (contract plus fixed costs)')],
        note='VSH are from the contract, not actuals (costs tab U12). Zone split follows the even example split in Operating Stats rows 16–18.', cite=ct(12)),
    svc('TART-WS', 'Main Line – West Shore', 'West Shore', 'TART', 'TART', group='Main Line', state_cond='California route', local_cond='Placer County', trips=21205, vsh=4237.5, vsm=82391.1, data_year='25-26', juris={'PLA': 1}, juris_placeholder=False, note='Main Line segment. The costs tab Main Line subtotal (row 16) is not counted again.', cite=ct(13)),
    svc('TART-NS', 'Main Line – North Shore', 'North Shore', 'TART', 'TART', group='Main Line', state_cond='California route', local_cond='Placer County', trips=92011, vsh=4983.5, vsm=113132.1, data_year='25-26', juris={'PLA': 1}, juris_placeholder=False, note='Main Line segment.', cite=ct(14)),
    svc('TART-NV', 'Main Line – Nevada', 'Nevada', 'TART', 'TART', group='Main Line', state_cond='Nevada route', local_cond='Washoe County', trips=34977, vsh=4219.3125, vsm=63697, data_year='25-26', juris={'WAS': 1}, juris_placeholder=False, note='Main Line segment in Washoe County; supported by Washoe RTC.', cite=ct(15)),
    svc('89', 'Hwy 89 (Tahoe City–Truckee)', 'Hwy 89', 'TART', 'TART', group='TART', state_cond='California route', local_cond='Placer County, Nevada County', area='mixed', trips=71136, vsh=8331.75, vsm=167948.7, data_year='25-26', juris={'PLA': 0.5, 'NEV': 0.5}, note='Urban and rural class is a placeholder: the Truckee end lies outside the Lake Tahoe UZA.', cite=ct(17)),
    svc('267', 'Hwy 267 (Kings Beach–Truckee)', 'Hwy 267', 'TART', 'TART', group='TART', state_cond='California route', local_cond='Placer County, Nevada County', area='mixed', trips=73556, vsh=8420.233333, vsm=176999.3, data_year='25-26', juris={'PLA': 0.5, 'NEV': 0.5}, note='Urban and rural class is a placeholder.', cite=ct(18)),
    svc('NIGHT', 'Night service', 'Night', 'TART', 'TART', group='TART', state_cond='California route', local_cond='Placer County', trips=4725, vsh=2985, vsm=57781.2, data_year='25-26', juris={'PLA': 1}, juris_placeholder=False, cite=ct(19)),
    svc('ADA-PLA', 'TART ADA paratransit', 'ADA (TART)', 'TART', 'Truckee', group='TART', state_cond='California route', local_cond='(none listed)', type='paratransit', trips=3573, vsh=1951.65, vsm=34749, data_year='25-26', juris={'PLA': 1}, note='No local conditions listed; Placer County is a placeholder.', cite=ct(20)),
    svc('TC', 'TART Connect microtransit', 'TART Connect', 'TART', 'Placer Via', group='TART', state_cond='California route', local_cond='Placer County', type='microtransit', trips=157369, vsh=27342.51, vsm=544888.71, data_year='25-26', juris={'PLA': 1}, juris_placeholder=False, ref_cost=2997578, ref_cite=[('plan', 'T5-7 G26')], cite=ct(21)),
    svc('PR-W', 'Park & Ride shuttle (winter)', 'P&R winter', 'TNTTMA', 'MRTW', group='TNT/TMA', state_cond='California route', local_cond='Placer County, Nevada County', type='seasonal', area='mixed', vsh=2500, data_year='estimate', juris={'PLA': 0.5, 'NEV': 0.5}, ref_cost=894233, ref_cite=[('plan', 'TNTTMA $ F43 (winter and summer combined)')],
        note='Costs tab estimate (2,500 VSH). TNT/TMA FY 26-27 Park & Ride budget is $894,233 for both seasons.', cite=ct(22)),
    svc('PR-S', 'Park & Ride shuttle (summer)', 'P&R summer', 'TNTTMA', 'MRTW', group='TNT/TMA', state_cond='California route', local_cond='Placer County, Nevada County', type='seasonal', area='mixed', vsh=500, data_year='estimate', juris={'PLA': 0.5, 'NEV': 0.5}, note='Costs tab estimate (500 VSH).', cite=ct(23)),
    svc('NLTE', 'North Lake Tahoe Express (airport)', 'NLTE', 'TNTTMA', 'MRTW', group='TNT/TMA', state_cond='CA/NV', local_cond='Placer County, Nevada County, Washoe County', type='airport', area='mixed', vsh=1200, data_year='estimate', juris={'PLA': THIRD, 'NEV': THIRD, 'WAS': THIRD}, ref_cost=694260, ref_cite=[('plan', 'TNTTMA $ F22')],
        note='Costs tab estimate based on FY 25-26 budget (1,200 VSH × $200.98). TNT/TMA FY 26-27 NLTE budget is $694,260.', cite=ct(24)),
    svc('VAN', 'Vanpools (TNT/TMA)', 'Vanpools', 'TNTTMA', 'BUDGET', group='TNT/TMA', state_cond='CA/NV', local_cond='Placer County, Washoe County', type='vanpool', area='mixed', cost_override=195800, data_year='26-27 budget', juris={'PLA': 0.5, 'WAS': 0.5}, ref_cost=195800, ref_cite=[('plan', 'TNTTMA $ K43')],
        note='Not in the costs tab. Included because Revenue %s has a Vanpools column; cost is the TNT/TMA FY 26-27 vanpool budget.', cite=[('plan', 'TNTTMA $ K36:K43')]),
    # Service plan elements: marginal costs from the financial plan, off by default
    svc('SP-US50', 'Replace 19X with US 50 service (4 round trips)', 'US 50 service', 'TTD', 'BUDGET', plan=True, included=False, area='rural', schedule=[476500, 495600, 514600, 533700, 552700], juris={'CC': 0.5, 'DOU': 0.5},
        note='The financial plan adds this cost without removing Route 19X. Exclude Route 19X to model the replacement.', cite=[('plan', 'T2-4 row 29')]),
    svc('SP-28', 'Seasonal Route 28 extension to Spooner Mobility Hub', '28 to Spooner', 'TTD', 'BUDGET', plan=True, included=False, type='seasonal', schedule=[0, 137200, 142400, 147700, 153000], juris={'WAS': 0.5, 'DOU': 0.5}, note='Jurisdiction split is a placeholder.', cite=[('plan', 'T2-4 row 30')]),
    svc('SP-EBS', 'Continue Emerald Bay Shuttle (Route 30) beyond the pilot', '30 after pilot', 'TTD', 'BUDGET', plan=True, included=False, type='seasonal', schedule=[0, 0, 558700, 579400, 600100], juris={'ELD': 1}, cite=[('plan', 'T2-4 row 31')]),
    svc('SP-MEY', 'Pilot co-mingled paratransit and microtransit to Meyers', 'Meyers pilot', 'SSTMA', 'BUDGET', plan=True, included=False, type='microtransit', schedule=[0, 357300, 371000, 384800, 398500], juris={'ELD': 1}, note='Assumes a third-party contractor at Lake Link costs (Table 2 note 4).', cite=[('plan', 'T2-4 row 32')]),
    svc('SP-LTCC', 'Discontinue Route 50 summer deviation to LTCC', '50 LTCC change', 'TTD', 'BUDGET', plan=True, included=False, schedule=[-10600, -11000, -11400, -11800, -12300], adjusts='50', juris={'CSLT': THIRD, 'ELD': THIRD, 'DOU': THIRD}, note='Cost reduction applied to Route 50.', cite=[('plan', 'T2-4 row 33')]),
    svc('SP-INC', 'Reinstate TART Connect in Incline Village', 'Incline Connect', 'TART', 'BUDGET', plan=True, included=False, type='microtransit', schedule=[0, 1044400, 1086200, 1129600, 1402800], juris={'WAS': 1}, cite=[('plan', 'T5-7 row 36')]),
    svc('SP-VAN', 'Add vanpools between Reno and Truckee/North Lake Tahoe', 'More vanpools', 'TNTTMA', 'BUDGET', plan=True, included=False, type='vanpool', area='mixed', schedule=[25000, 26000, 0, 0, 0], juris={'WAS': 0.5, 'NEV': 0.5}, note='Two vans per year at $12,000 per van (TNTTMA $ J45:J46).', cite=[('plan', 'T5-7 row 37')]),
]

# ── Funding lines ────────────────────────────────────────────────────────────


def ln(**o):
    d = dict(enabled=True, status='budgeted', amount_method='fixed', amount=0.0, prior=None, growth=0.0, last_year=None, cap=None,
             overrides={}, fed_share=None, fed_share_ada=None, counts_as_match=True, match_only=False, required={}, preferred={},
             alloc=None, commitment='budget', commit_note='', contributor=None, match_text='', condition_text='', restriction_text='',
             purpose='', administered_by='', notes='', cites={})
    d.update(o)
    return d


def rp(r):
    return ('plan', f'Revenue %s row {r}')


def prm(c):
    return ('plan', f'Per Route Model {c}')


def a1(c):
    return ('plan', f'T2-4 Table A1 {c}')


def a2(c):
    return ('plan', f'T5-7 Table A2 {c}')


def tnt(c):
    return ('plan', f'TNTTMA $ {c} (FY 26-27 budget)')


FS_FED = ('fed', 'FY 25-26 budgeted for operations')
FS_STATE = ('state', 'FY 25-26 budgeted for operations')
FS_L1 = ('loc1', 'FY 25-26 budgeted for operations')
FS_L2 = ('loc2', 'FY 25-26 budgeted for operations')
FTA_RULE = 'Lake Tahoe UZA and Nevada'

TDA_PCT = {'19X': 0.11604604993756787, '22': 0.2260494520132804, '28': 0.000379024230270383, '50': 0.35421128969792537, '55': 0.1692836788071976, '51': 0.011628129524001163, 'ADA-TTD': 0.12240237578975716}
VSH_TTD = {'19X': 0.06993272114234218, '22': 0.13703133982815147, '28': 0.03706396929722339, '50': 0.29268944514364736, '55': 0.2893829922776923, '51': 0.005189639366677543, 'ADA-TTD': 0.16870989294426575}
CMAQ_PCT = {'50': 0.368122, '55': 0.295802, 'ADA-TTD': 0.336076}
TART_ALL = ['TART-WS', 'TART-NS', 'TART-NV', '89', '267', 'NIGHT', 'ADA-PLA']
TART_PLACER = ['TART-WS', 'TART-NS', '89', '267', 'NIGHT', 'ADA-PLA']
TART_FIXED = ['TART-WS', 'TART-NS', 'TART-NV', '89', '267', 'NIGHT']


def shares(p, cite):
    return dict(method='shares', shares=dict(p), cite=cite)


def auto(basis='vsh', targets=None, cite=None):
    return dict(method='auto', basis=basis, targets=list(targets) if targets else None, cite=cite)


def ll_partner(id, name, prior, cell):
    return ln(id=id, name=name, program=('Lake Link partner contribution', 'private'), recipient='SSTMA', administered_by=name, amount=0, prior=prior,
              status='none', commitment='none', purpose='Contribution for Lake Link operations.', restriction_text='Lake Link Service', match_text='No match requirement',
              required={'service': ['LL']}, alloc=shares({'LL': 1}, [rp('37–43')]),
              commit_note='Contributed to Lake Link in FY 25-26; no FY 26-27 commitment secured (Table A1 note 8).',
              cites={'amount': [a1(f'{cell} (FY 26-27 = $0)')], 'prior_year_amount': [a1(cell.replace('G', 'F')), FS_L2], 'restrictions': [('loc2', name)]})


def tart_tda(id, name, amt, cell):
    ltf = 'ltf' in id
    return ln(id=id, name=name, program=('TDA Local Transportation Fund (LTF)' if ltf else 'TDA State Transit Assistance (STA)', 'state'), recipient='TART',
              administered_by='State of California, apportioned by PCTPA' if 'pctpa' in id else 'State of California, apportioned by TRPA',
              amount=amt, growth=0.00025, commitment='formula', restriction_text='CA and NV (operations only)', match_text='No match requirement',
              condition_text='California funding ideally used in CA, but can be used as federal match', preferred={'state': ['CA']},
              alloc=auto('vsh', TART_PLACER, [('plan', 'Not allocated on Revenue %s; placeholder split by service hours on TART routes in California')]),
              notes='Fact sheet FY 25-26 TART totals: LTF $2,023,819 and STA $1,110,118 (TRPA and PCTPA combined).',
              cites={'amount': [prm(cell), a2('G61' if ltf else 'G62')], 'prior_year_amount': [FS_STATE], 'match': [rp(11 if ltf else 13)], 'projection': [a2('note 2: population change')]})


LINES = [
    # ───────── TTD ─────────
    ln(id='ttd-5307', name='FTA 5307 formula (TTD)', program=('FTA 5307 Urbanized Area Formula', 'federal'), recipient='TTD', administered_by='Federal Transit Administration',
       amount=1569548.05, amount_method='fta_5307_formula', prior=2400000, growth=0.01, fed_share=0.5, fed_share_ada=0.8, commitment='formula',
       purpose='Urbanized area operating, capital, and transportation-related planning.', restriction_text=FTA_RULE, match_text='50% non-federal',
       condition_text='Can be used to cover 50% of operating costs (urban routes), 80% ADA.', required={'area_class': ['urban', 'mixed']},
       commit_note='Annual FTA apportionment to the Lake Tahoe UZA, split between TTD and Placer County by the earned-share worksheet.',
       alloc=shares({'28': 0.042293835679174434, '50': 0.5150124315394018, '55': 0.20248122143183558, '51': 0.0061511257128486225, 'ADA-TTD': 0.23406138563673973},
                    [rp('3 (TTD FY 24-25 route allocations, Actual Revenues row 3)')]),
       cites={'amount': [prm('D12 = FTA Allocation Split (26-27) G34 (75% of TTD earned share)')], 'prior_year_amount': [FS_FED], 'match': [rp('3 C3, AE3')], 'restrictions': [('fed', 'FTA 5307')], 'projection': [a1('O60: 1% increase annually')]}),
    ln(id='ttd-5307cmaq', name='FTA 5307, formerly CMAQ (TTD)', program=('FTA 5307 (flexed CMAQ)', 'federal'), recipient='TTD', administered_by='Federal Transit Administration',
       amount=596121, growth=0.01, fed_share=0.5, fed_share_ada=0.8, commitment='formula', restriction_text=FTA_RULE, match_text='50% non-federal',
       purpose='CMAQ funds transferred to FTA 5307 for operations.', required={'area_class': ['urban', 'mixed']},
       alloc=shares(CMAQ_PCT, [rp('4 (TTD FY 24-25 CMAQ route allocations, Actual Revenues row 4)')]),
       commit_note='Programmed annually; partner notes say more CMAQ grants are coming (Revenue %s D55).',
       cites={'amount': [prm('D13'), a1('G61')], 'match': [rp('4 C4')], 'projection': [a1('O61: 1% increase annually')]}),
    ln(id='ttd-5307co', name='FTA 5307 carryover (TTD)', program=('FTA 5307 carryover', 'federal'), recipient='TTD', administered_by='Federal Transit Administration',
       amount=946281.95, last_year=0, fed_share=0.5, fed_share_ada=0.8, commitment='onetime', restriction_text=FTA_RULE, match_text='50% non-federal',
       purpose='Prior-year 5307 balance applied to operations.', required={'area_class': ['urban', 'mixed']}, alloc=shares(CMAQ_PCT, [rp(5)]),
       commit_note='One-time. The summary table notes the drop in 5307 funds once carryover ends in FY 27-28.',
       cites={'amount': [prm('D14'), a1('G62')], 'match': [rp('5 C5')], 'projection': [('plan', 'T1 Summary Table M32')]}),
    ln(id='ttd-5311nv', name='FTA 5311 rural (NDOT)', program=('FTA 5311 Rural Area Formula', 'federal'), recipient='TTD', administered_by='FTA through Nevada DOT',
       amount=1798577, prior=1669792, growth=0.01, fed_share=0.5, commitment='formula', restriction_text='Nevada only; rural component', match_text='50% non-federal',
       condition_text='Can only be applied to rural routes (19X and 22)', purpose='Rural operating, capital, and planning assistance.',
       required={'state': ['NV'], 'area_class': ['rural', 'mixed']}, alloc=shares({'19X': 0.3392119810002851, '22': 0.6607880189997148}, [rp(6)]),
       commit_note='NDOT subrecipient award. Partner notes: NDOT match is 20% for admin, 40% for operating, 5% for capital (Revenue %s F64). Nevada receives $9.8 million in total FTA 5311 (Table A1 O65).',
       cites={'amount': [prm('D15'), a1('G65')], 'prior_year_amount': [FS_FED], 'match': [rp('6 B6, C6')], 'restrictions': [('fed', 'FTA 5311 (NV DOT)')], 'projection': [a1('O65: 1% increase yearly')]}),
    ln(id='ttd-5310', name='FTA 5310 seniors and disabilities (TTD)', program=('FTA 5310 Enhanced Mobility', 'federal'), recipient='TTD', administered_by='Federal Transit Administration',
       amount=0, prior=27000, overrides={1: 76000, 2: 0, 3: 78300, 4: 0}, fed_share=0.5, commitment='formula', restriction_text='ADA services and capital only',
       match_text='50% non-federal', condition_text='Can only be applied to ADA routes', purpose='Urbanized area funding to meet the needs of older adults and people with disabilities.',
       required={'service_type': ['paratransit']}, alloc=shares({'ADA-TTD': 1}, [rp(8)]),
       commit_note='Alternates with Placer County: the FY 26-27 apportionment goes to Placer (FTA Allocation Split J35); TTD in FY 27-28 and FY 29-30.',
       cites={'amount': [a1('G63:K63'), prm('D17')], 'prior_year_amount': [FS_FED], 'match': [rp('8 B8, C8')], 'restrictions': [('fed', 'FTA 5310')], 'projection': [a1('H63, J63')]}),
    ln(id='ttd-5310co', name='FTA 5310 carryover (TTD)', program=('FTA 5310 carryover', 'federal'), recipient='TTD', administered_by='Federal Transit Administration',
       amount=30277, last_year=0, fed_share=0.5, commitment='onetime', restriction_text='ADA services and capital only', match_text='50% non-federal',
       condition_text='Can only be applied to ADA routes', required={'service_type': ['paratransit']}, alloc=shares({'ADA-TTD': 1}, [rp(9)]),
       cites={'amount': [prm('D18'), a1('G64')], 'match': [rp(9)]}),
    ln(id='ttd-ltf', name='TDA Local Transportation Fund (TTD)', program=('TDA Local Transportation Fund (LTF)', 'state'), recipient='TTD', administered_by='State of California (sales tax), apportioned by TRPA',
       amount=1263326, prior=1200000, growth=0.00025, commitment='formula', restriction_text='CA and NV (operations only)', match_text='No match requirement',
       condition_text='California funding ideally used in CA, but can be used as federal match', purpose='Operating, capital, and planning funds from a quarter-cent of the general sales tax collected in California.',
       preferred={'state': ['CA']}, alloc=shares(TDA_PCT, [rp('10 (TTD FY 24-25 TDA route allocations, Actual Revenues row 10)')]),
       commit_note='TRPA apportionment; no change assumed in the TRPA TDA split (Table A1 note 2). TTD applies one-third to rural and two-thirds to urban routes (Revenue %s AE10).',
       cites={'amount': [a1('G66 (Per Route Model D19 holds the rural one-third of LTF plus STA, $615,042, under this label)')], 'prior_year_amount': [FS_STATE], 'match': [rp('10 B10, C10')], 'restrictions': [('state', 'Local Transportation Funds (LTF)')], 'projection': [a1('note 2: RTP projected population change, 0.025% per year')]}),
    ln(id='ttd-sta', name='TDA State Transit Assistance (TTD)', program=('TDA State Transit Assistance (STA)', 'state'), recipient='TTD', administered_by='State of California (fuel sales tax), apportioned by TRPA',
       amount=581801, prior=400000, growth=0.00025, commitment='formula', restriction_text='CA and NV (operations only)', match_text='No match requirement',
       condition_text='California funding ideally used in CA, but can be used as federal match', purpose='Transit purposes only.', preferred={'state': ['CA']}, alloc=shares(TDA_PCT, [rp(12)]),
       cites={'amount': [a1('G67 (Per Route Model D21 holds the urban two-thirds of LTF plus STA, $1,230,085, under this label)')], 'prior_year_amount': [FS_STATE], 'match': [rp(12)], 'restrictions': [('state', 'State Transportation Assistance (STA)')], 'projection': [a1('note 2')]}),
    ln(id='ttd-lctop', name='Low Carbon Transit Operations Program (TTD)', program=('LCTOP', 'state'), recipient='TTD', administered_by='State of California (5% of cap-and-trade proceeds)',
       amount=265506, prior=0, overrides={1: 0, 2: 265500, 3: 0, 4: 265500}, commitment='formula', restriction_text='CA only', match_text='No match requirement',
       condition_text='California funding ideally used in CA, but can be used as federal match', purpose='Operating and capital assistance to reduce greenhouse gas emissions and improve mobility.',
       required={'state': ['CA']}, alloc=shares(VSH_TTD, [rp('15: share of TTD service hours on the V1G basis that leaves out Route 30 so shares sum to 100%; the draft assigns shares to Nevada routes 19X, 22, and 28')]),
       commit_note='TTD receives LCTOP every other year; it alternates with TART based on ridership (Revenue %s D67).',
       cites={'amount': [prm('D24'), a1('G73:K73')], 'prior_year_amount': [('state', 'LCTOP (used for capital, FY 25-26)')], 'match': [rp(15)], 'restrictions': [('state', 'LCTOP: "CA only"')], 'projection': [a1('O73: TTD gets every other year')]}),
    ln(id='ttd-elec', name='Electrification credits (TTD)', program=('Electrification credits', 'state'), recipient='TTD', administered_by='State of California',
       amount=8000, prior=8000, match_only=True, commitment='earned', restriction_text='–', match_text='Not real money; only used as match for other sources', condition_text='Not real money',
       purpose='Reimbursement for electrification credits earned through use of the electric fleet.',
       alloc=shares({'19X': 0.11417091717203645, '22': 0.22505933646761356, '28': 0.03076817731070858, '50': 0.3069142915275666, '55': 0.17025173537720015, '51': 0.021536572704106832, 'ADA-TTD': 0.13129896944076805}, [rp(16)]),
       notes='Counted toward local match only, not toward funding the cost, per the Revenue %s notes. The State Funds fact sheet lists $8,000 budgeted for TTD operations.',
       cites={'amount': [prm('D25'), a1('G74')], 'prior_year_amount': [FS_STATE], 'match': [rp('16 B16, C16')]}),
    ln(id='ttd-sb125', name='SB 125 operating (TTD)', program=('SB 125', 'state'), recipient='TTD', administered_by='State of California',
       amount=825000, prior=1000000, last_year=0, commitment='onetime', restriction_text='Existing STA recipients only', match_text='No match requirement',
       condition_text='California funding ideally used in CA, but can be used as federal match', purpose='Operating, capital, and planning.', preferred={'state': ['CA']},
       alloc=shares({'50': 0.5258405599999999, '55': 0.4249148200000001, '51': 0.04924462000000002}, [rp(17)]), commit_note='Table A1 assumes no SB 125 after FY 26-27.',
       cites={'amount': [prm('D26'), a1('G75')], 'prior_year_amount': [FS_STATE], 'match': [rp(17)], 'restrictions': [('state', 'SB 125 Operating')], 'projection': [a1('H75:K75 = 0')]}),
    ln(id='ttd-nvparks', name='Nevada State Parks (Route 28)', program=('Nevada State Parks', 'state'), recipient='TTD', administered_by='State of Nevada',
       amount=85000, prior=85000, restriction_text='East Shore Express', match_text='No match requirement', condition_text='Only applied to Route 28',
       purpose='Operating, capital, and administrative support for the East Shore Express.', required={'service': ['28']}, alloc=shares({'28': 1}, [rp(18)]),
       cites={'amount': [prm('D27'), a1('G76')], 'prior_year_amount': [FS_L1], 'match': [rp(18)], 'restrictions': [('loc1', 'Nevada State Parks')], 'projection': [a1('note 4: no annual change')]}),
    ln(id='ttd-nvstate', name='Nevada State allocation to TTD general fund', program=('Nevada State allocation', 'state'), recipient='TTD', administered_by='FTA, State of Nevada',
       amount=0, prior=346500, status='factsheet', restriction_text='NV', match_text='No match requirement', purpose='Budget allocation to TTD general fund.',
       required={'state': ['NV']}, alloc=auto('vsh'), notes='On the State Funds fact sheet for FY 25-26 but not in the FY 26-27 financial plan. Enter an amount if it is still expected.',
       cites={'amount': [(None, 'Not in Financial PlanG FY 26-27 tables')], 'prior_year_amount': [FS_STATE], 'restrictions': [('state', 'Nevada State')]}),
    ln(id='ttd-localapp', name='Local appropriation (Douglas, Washoe, Placer, Carson City)', program=('Local appropriation', 'local'), recipient='TTD', administered_by='Douglas, Washoe, Placer, Carson City',
       amount=0, prior=232235, status='factsheet', restriction_text='Planning and administrative support', match_text='No match requirement', purpose='TTD general fund planning and administration.',
       alloc=auto('vsh'), notes='Supports TTD planning and administration rather than route operations; not in the FY 26-27 operating plan.',
       cites={'amount': [(None, 'Not in Financial PlanG FY 26-27 tables')], 'prior_year_amount': [FS_L1], 'restrictions': [('loc1', 'Local Appropriation')]}),
    ln(id='ttd-tdva', name='Tahoe Douglas Visitor Authority', program=('Visitor authority contribution', 'local'), recipient='TTD', administered_by='Tahoe Douglas Visitor Authority',
       amount=120000, prior=65000, restriction_text='TTD expanded operations (Route 51)', match_text='No match requirement', condition_text='Ideally applied only to NV routes',
       purpose='Budget contribution for expanded operations (Route 51).', preferred={'state': ['NV'], 'service': ['51']}, alloc=shares({'51': 1}, [rp(19)]),
       notes='Per Route Model row 28 multiplies the Nevada State Parks amount ($85,000) instead of the TDVA amount ($120,000).',
       cites={'amount': [prm('D28'), a1('G77')], 'prior_year_amount': [FS_L1], 'match': [rp(19)], 'restrictions': [('loc1', 'Tahoe Douglas Visitor Authority')], 'projection': [a1('note 4')]}),
    ln(id='ttd-interest', name='Interest revenue (TTD)', program=('Interest', 'other'), recipient='TTD', administered_by='TTD', amount=18000, commitment='earned', match_text='No match requirement',
       alloc=shares(VSH_TTD, [rp('20 (same basis as LCTOP)')]), cites={'amount': [prm('D29'), a1('G78')], 'match': [rp(20)], 'projection': [a1('note 4')]}),
    ln(id='ttd-ktb', name='Keep Tahoe Blue (Emerald Bay Shuttle)', program=('Private contribution', 'private'), recipient='TTD', administered_by='League to Save Lake Tahoe (Keep Tahoe Blue)',
       amount=8322, overrides={1: 29678}, last_year=1, commitment='onetime', match_text='No match requirement', required={'service': ['30']}, alloc=shares({'30': 1}, [rp(21)]),
       commit_note='Total allocated through FY 27-28: $38,000.', cites={'amount': [prm('D30'), a1('G79:H79')], 'match': [rp(21)]}),
    ln(id='ttd-crp', name='Carbon Reduction Program (Emerald Bay Shuttle)', program=('FHWA Carbon Reduction Program', 'federal'), recipient='TTD', administered_by='Federal Highway Administration',
       amount=271910, overrides={1: 537090}, last_year=1, fed_share=0.8853, commitment='onetime', match_text='11.47% non-federal', required={'service': ['30']}, alloc=shares({'30': 1}, [rp(22)]),
       commit_note='Total allocated through FY 27-28: $809,000.', cites={'amount': [prm('D31'), a1('G80:H80')], 'match': [rp('22 C22')]}),
    ln(id='ttd-eldebs', name='El Dorado County (Emerald Bay Shuttle)', program=('County contribution', 'local'), recipient='TTD', administered_by='El Dorado County (AQMD, VMT Reduction Fund)',
       amount=331240, overrides={1: 100155}, last_year=1, commitment='onetime', contributor='ELD', match_text='No match requirement', condition_text='Ideally used only in CA',
       required={'service': ['30']}, preferred={'state': ['CA']}, alloc=shares({'30': 1}, [rp(23)]), commit_note='Total allocated through FY 27-28: $431,395.',
       cites={'amount': [prm('D32'), a1('G81:H81')], 'match': [rp('23 B23')]}),
    ln(id='ttd-plaebs', name='Placer County (Emerald Bay Shuttle)', program=('County contribution', 'local'), recipient='TTD', administered_by='Placer County',
       amount=8324, overrides={1: 29676}, last_year=1, commitment='onetime', contributor='PLA', match_text='No match requirement', condition_text='Ideally used only in CA',
       required={'service': ['30']}, preferred={'state': ['CA']}, alloc=shares({'30': 1}, [rp(24)]), commit_note='Total allocated through FY 27-28: $38,000.',
       cites={'amount': [prm('D33'), a1('G82:H82')], 'match': [rp(24)]}),
    ln(id='ttd-fares30', name='Fares – Emerald Bay Shuttle', program=('Passenger fares', 'fare'), recipient='TTD', administered_by='Riders ($5 one-way)',
       amount=53500, growth=0.02, last_year=1, counts_as_match=False, commitment='earned', required={'service': ['30']}, alloc=shares({'30': 1}, [(None, 'Fares belong to the route that collects them')]),
       notes="Route 30 is TTD's only fare route ($5 one-way; Fare Rates tab). Table A1 carries fares in FY 26-27 only; this model continues them with 2% ridership growth through the FY 27-28 pilot season.",
       cites={'amount': [a1('G72')], 'projection': [a1('G135: 2% base ridership growth')]}),
    ln(id='ttd-5339', name='FTA 5339 bus and facilities (TTD)', program=('FTA 5339 Bus and Bus Facilities', 'federal'), recipient='TTD', administered_by='FTA; Nevada DOT', amount=0, prior=0,
       status='capital', commitment='formula', fed_share=0.8, restriction_text='Lake Tahoe UZA and Nevada; Nevada facilities, bi-state fleet OK', match_text='Yes (capital)',
       purpose='Capital funds to replace, rehabilitate, and purchase buses and equipment, and to build bus facilities.',
       notes='Capital program, outside the operating model. FY 26-27 example UZA split: TTD $197,361 (FTA Allocation Split I34).',
       cites={'prior_year_amount': [FS_FED], 'amount': [('plan', 'FTA Allocation Split (26-27) I34')]}),

    # ───────── Lake Link (SSTMA) ─────────
    ln(id='ll-sb125', name='SB 125 operating (Lake Link)', program=('SB 125', 'state'), recipient='SSTMA', administered_by='State of California',
       amount=750000, prior=750000, last_year=0, commitment='onetime', restriction_text='Existing STA recipients only', match_text='No match requirement',
       required={'service': ['LL']}, preferred={'state': ['CA']}, alloc=shares({'LL': 1}, [(None, 'Not split across Lake Link zones on Revenue %s; applied to Lake Link')]),
       commit_note='Assumes an SB 125 allocation in FY 26-27 only (Table A1 O85).',
       cites={'amount': [prm('F26'), a1('G85')], 'prior_year_amount': [a1('F85')], 'restrictions': [('state', 'SB 125 Operating')]}),
    ln(id='ll-douglas', name='Douglas County (Lake Link)', program=('Lake Link funding agreement', 'local'), recipient='SSTMA', administered_by='Douglas County (TLRT)',
       amount=750000, prior=650000, overrides={1: 850000}, commitment='agreement', contributor='DOU', restriction_text='Lake Link in Douglas County', match_text='No match requirement',
       condition_text='Ideally used only in Douglas County', purpose='Contribution for Lake Link operations in Douglas County.',
       required={'service': ['LL'], 'jurisdiction_share': ['DOU']}, alloc=shares({'LL': 1}, [rp(34)]),
       commit_note='Written agreement; one of only two written Lake Link contracts (Per Route Model D88). Table A1 note 6 assumes support at existing levels beyond the end of current agreements.',
       cites={'amount': [prm('F43'), a1('G86:K86')], 'prior_year_amount': [a1('F86')], 'match': [rp(34)], 'restrictions': [('loc2', 'Douglas County')]}),
    ln(id='ll-cslt', name='City of South Lake Tahoe (Lake Link)', program=('Lake Link funding agreement', 'local'), recipient='SSTMA', administered_by='City of South Lake Tahoe',
       amount=1100000, prior=850000, commitment='agreement', contributor='CSLT', restriction_text='Lake Link in City of SLT', match_text='No match requirement',
       condition_text='Ideally used only in the City of South Lake Tahoe', purpose='Contribution for Lake Link operations.',
       required={'service': ['LL'], 'jurisdiction_share': ['CSLT']}, alloc=shares({'LL': 1}, [rp(35)]),
       commit_note='Written agreement (Per Route Model D88). Table A1 note 6 assumes support at existing levels beyond current agreements.',
       cites={'amount': [prm('F44'), a1('G87:K87')], 'prior_year_amount': [a1('F87')], 'match': [rp(35)], 'restrictions': [('loc2', 'City of South Lake Tahoe')]}),
    ln(id='ll-tahoeblue', name='Tahoe Blue Events Center mitigation fee', program=('Transportation mitigation fee', 'private'), recipient='SSTMA', administered_by='Ticket surcharge, Tahoe Blue Events Center',
       amount=687724, prior=613053, growth=0.06, cap=750000, commitment='agreement', restriction_text='Lake Link Service', match_text='No match requirement',
       purpose='Contribution for Lake Link operations in Stateline and South Lake Tahoe from a transportation mitigation fee on event tickets.',
       required={'service': ['LL']}, alloc=shares({'LL': 1}, [rp(36)]),
       commit_note='Assumes the $3 surcharge goes to transit and no increase in the annual attendee cap (Table A1 note 7).',
       cites={'amount': [prm('F45'), a1('G88')], 'prior_year_amount': [a1('F88')], 'restrictions': [('loc2', 'Tahoe Blue Events Center Mitigation Fee')], 'projection': [a1('H88: 6% per year, capped at $750,000')]}),
    ll_partner('ll-slttid', 'South Lake Tahoe Tourism Improvement District', 25000, 'G89'),
    ll_partner('ll-heavenly', 'Heavenly', 15000, 'G90'),
    ll_partner('ll-caesars', 'Caesars Entertainment', 65000, 'G91'),
    ll_partner('ll-roundhill', 'Round Hill Pines Resort', 85000, 'G92'),
    ll_partner('ll-advlearn', 'Advance Learning', 25000, 'G93'),
    ll_partner('ll-ltva', 'Lake Tahoe Visitors Authority', 62100, 'G94'),
    ll_partner('ll-ltcc', 'Lake Tahoe Community College', 25000, 'G95'),

    # ───────── TART (Placer County) ─────────
    ln(id='tart-5307', name='FTA 5307 formula (TART)', program=('FTA 5307 Urbanized Area Formula', 'federal'), recipient='TART', administered_by='Federal Transit Administration',
       amount=1653136.47, amount_method='fta_5307_formula', prior=2500000, growth=0.01, fed_share=0.5, fed_share_ada=0.8, commitment='formula', restriction_text=FTA_RULE, match_text='50% non-federal',
       purpose='Urbanized area operating, capital, and transportation-related planning.', required={'area_class': ['urban', 'mixed']},
       alloc=auto('vsh', TART_ALL, [rp('3: share of TART service hours; the PlanG total double-counts Main Line so draft shares sum to 72%, corrected as in Funding Model V1G')]),
       notes='TART financial plan Table A2 budgets $2,660,000 of 5307 for FY 26-27; the per-route model uses the earned-share result ($1,653,136).',
       cites={'amount': [prm('E12 = FTA Allocation Split (26-27) G35'), a2('G59 shows $2,660,000')], 'prior_year_amount': [FS_FED], 'match': [rp(3)], 'restrictions': [('fed', 'FTA 5307')], 'projection': [a2('O59: 1% increase yearly')]}),
    ln(id='tart-5310', name='FTA 5310 seniors and disabilities (TART)', program=('FTA 5310 Enhanced Mobility', 'federal'), recipient='TART', administered_by='Federal Transit Administration',
       amount=75224.8, prior=0, last_year=0, fed_share=0.5, commitment='formula', restriction_text='ADA services and capital only', match_text='50% non-federal',
       required={'service_type': ['paratransit']}, alloc=shares({'ADA-PLA': 1}, [rp(8)]),
       notes='The FTA split worksheet assigns the FY 26-27 5310 apportionment to Placer (J35). It does not appear in TART Table A2. Alternates with TTD; later Placer years are not projected.',
       cites={'amount': [prm('E17 = FTA Allocation Split (26-27) J35')], 'prior_year_amount': [FS_FED], 'match': [rp(8)], 'restrictions': [('fed', 'FTA 5310')]}),
    ln(id='tart-5311ca', name='FTA 5311 rural (Caltrans)', program=('FTA 5311 Rural Area Formula', 'federal'), recipient='TART', administered_by='FTA through Caltrans',
       amount=290000, prior=450000, growth=0.01, fed_share=0.5, commitment='formula', restriction_text='California only; rural component', match_text='50% non-federal',
       condition_text='Can only be applied to rural routes', purpose='Rural operating, capital, and planning assistance.', required={'state': ['CA'], 'area_class': ['rural', 'mixed']},
       alloc=auto('vsh', None, [(None, 'Not allocated on Revenue %s; placeholder split by service hours among eligible TART routes')]),
       cites={'amount': [prm('E16'), a2('G60')], 'prior_year_amount': [FS_FED], 'match': [rp('7 B7, C7')], 'restrictions': [('fed', 'FTA 5311 (Cal Trans)')], 'projection': [a2('1% increase yearly')]}),
    tart_tda('tart-ltf-trpa', 'TDA LTF, TRPA apportionment (TART)', 913053, 'E19'),
    tart_tda('tart-ltf-pctpa', 'TDA LTF, PCTPA apportionment (TART)', 1675000, 'E20'),
    tart_tda('tart-sta-trpa', 'TDA STA, TRPA apportionment (TART)', 510729, 'E21'),
    tart_tda('tart-sta-pctpa', 'TDA STA, PCTPA apportionment (TART)', 308898, 'E22'),
    ln(id='tart-sgr', name='State of Good Repair (TART)', program=('State of Good Repair (SGR)', 'state'), recipient='TART', administered_by='State of California (gas tax and vehicle fees)',
       amount=100084, prior=102929, growth=0.00025, commitment='formula', restriction_text='Eligible transit maintenance and match for capital projects', match_text='No match requirement',
       purpose='Transit infrastructure repair and service improvements.', preferred={'state': ['CA']},
       alloc=auto('vsh', TART_PLACER, [(None, 'Not allocated on Revenue %s; placeholder split by service hours on TART routes in California')]),
       cites={'amount': [prm('E23'), a2('G63')], 'prior_year_amount': [FS_STATE], 'match': [rp(14)], 'restrictions': [('state', 'State of Good Repair (SGR)')]}),
    ln(id='tart-tot-tc', name='Placer County TOT – TART Connect', program=('Placer County transient occupancy tax', 'local'), recipient='TART', administered_by='Placer County',
       amount=2900000, growth=0.04, contributor='PLA', restriction_text='Various usage restrictions based on funding subcategory', match_text='No match requirement',
       condition_text='Ideally used only in Placer County', purpose='Budget contribution for TART Connect.', required={'service': ['TC']}, preferred={'jurisdiction_share': ['PLA']},
       alloc=shares({'TC': 1}, [('plan', 'Actual Revenues row 28')]),
       cites={'amount': [('plan', 'Actual Revenues U28:X28 ($2.9 million across TART Connect zones); T5-7 G155')], 'match': [rp(28)], 'restrictions': [('loc1', 'Placer County (Transient Occupancy Tax)')], 'projection': [a2('O68: 4% annually with inflation')]}),
    ln(id='tart-tot-fr', name='Placer County TOT – TART fixed route and paratransit', program=('Placer County transient occupancy tax', 'local'), recipient='TART', administered_by='Placer County',
       amount=2447400, prior=2563510, growth=0.04, contributor='PLA', restriction_text='Various usage restrictions based on funding subcategory', match_text='No match requirement',
       condition_text='Ideally used only in Placer County', preferred={'jurisdiction_share': ['PLA']},
       alloc=auto('vsh', TART_PLACER, [(None, 'Not allocated on Revenue %s; placeholder split by service hours on Placer County routes')]),
       notes='FY 26-27 TART TOT totals $5,347,400: $2,900,000 for TART Connect plus four subcategories ($150,000; $1,874,954; $277,500; $144,946). Prior year is the FY 25-26 fact sheet total ($5,463,510) less $2.9 million.',
       cites={'amount': [a2('G68')], 'prior_year_amount': [FS_L1], 'match': [rp(28)], 'restrictions': [('loc1', 'Placer County (Transient Occupancy Tax)')], 'projection': [a2('O68: 4% annually')]}),
    ln(id='tart-washoe', name='Washoe RTC (TART Nevada service)', program=('RTC Washoe contribution', 'local'), recipient='TART', administered_by='Regional Transportation Commission of Washoe County',
       amount=296055, prior=288746, growth=0.02, contributor='WAS', restriction_text='Fixed route service in Nevada; airport shuttle service in Tahoe in Washoe County', match_text='No match requirement',
       condition_text='Only applied to TART NV route', purpose='Operations in Nevada.', required={'service': ['TART-NV']}, alloc=shares({'TART-NV': 1}, [rp(25)]),
       notes='Revenue %s assigns 95.8% to Main Line and 4.2% to NLTE; NLTE Washoe County support is budgeted separately by TNT/TMA ($12,500).',
       cites={'amount': [prm('E34'), a2('G69')], 'prior_year_amount': [FS_L1], 'match': [rp('25 B25')], 'restrictions': [('loc1', 'Washoe RTC')], 'projection': [a2('O69: 2% annual increase')]}),
    ln(id='tart-truckee', name='Town of Truckee (TART)', program=('Town of Truckee contribution', 'local'), recipient='TART', administered_by='Town of Truckee (LTF)',
       amount=230478, prior=256402, contributor='TRK', restriction_text='TART Hwy 89 and Hwy 267 fixed route service, and NLTE services in Truckee', match_text='No match requirement',
       purpose='TART Hwy 89 and Hwy 267 service; NLTE operations.', required={'service': ['89', '267', 'NLTE']}, alloc=auto('vsh', ['89', '267']),
       cites={'amount': [prm('E38'), a2('G70')], 'prior_year_amount': [FS_L1], 'match': [rp(29)], 'restrictions': [('loc1', 'Town of Truckee')], 'projection': [a2('O70: no change')]}),
    ln(id='tart-nsrp', name='North Shore Resort Partners', program=('Resort contribution', 'private'), recipient='TART', administered_by='Private resorts',
       amount=47900, prior=60000, restriction_text='TART operating only; operation contribution earmarked for winter service', match_text='No match requirement',
       purpose='Operating support for TART service and winter Park and Ride.', required={'agency': ['TART']},
       alloc=auto('vsh', TART_FIXED, [(None, 'Not allocated on Revenue %s; placeholder split by service hours on TART fixed routes')]),
       cites={'amount': [prm('E40'), a2('G71')], 'prior_year_amount': [FS_L1], 'match': [rp(31)], 'restrictions': [('loc1', 'North Shore Resort Partners')], 'projection': [a2('O71: no change')]}),
    ln(id='tart-nslp', name='North Shore Local Partners (free fares)', program=('Free-fare partnership', 'local'), recipient='TART', administered_by='Tahoe Truckee Airport District, resorts, Town of Truckee',
       amount=139000, prior=148500, restriction_text='TART operations; free fares', match_text='No match requirement',
       purpose='Contribution to TART for operating free fares and winter Park and Ride shuttles.', required={'agency': ['TART']},
       alloc=auto('vsh', TART_FIXED, [(None, 'Not allocated on Revenue %s; placeholder split by service hours on TART fixed routes')]),
       cites={'amount': [prm('E41'), a2('G72')], 'prior_year_amount': [FS_L1], 'match': [rp(32)], 'restrictions': [('loc1', 'North Shore Resort Partners (Free Fares)')], 'projection': [a2('O72: no change')]}),
    ln(id='tart-martis', name='Martis Zones of Benefit', program=('Zone of benefit', 'local'), recipient='TART', administered_by='Martis Zone of Benefit',
       amount=0, prior=50000, status='none', commitment='none', restriction_text='Hwy 267 TART service only', match_text='No match requirement',
       purpose='Budget contribution for Hwy 267 operations.', required={'service': ['267']}, alloc=shares({'267': 1}, [(None, 'Restricted to Hwy 267')]),
       commit_note='FY 25-26 $50,000; $0 in the FY 26-27 plan.', cites={'amount': [prm('E42'), a2('G73')], 'prior_year_amount': [FS_L1], 'restrictions': [('loc1', 'Martis Zones of Benefit')]}),
    ln(id='tart-5339', name='FTA 5339 bus and facilities (TART)', program=('FTA 5339 Bus and Bus Facilities', 'federal'), recipient='TART', administered_by='Federal Transit Administration', amount=0, prior=0,
       status='capital', commitment='formula', fed_share=0.8, restriction_text='Lake Tahoe UZA and Nevada', match_text='Yes (capital)', purpose='Capital funds for buses, equipment, and bus facilities.',
       notes='Capital program, outside the operating model. FY 26-27 example UZA split: Placer $207,871 (FTA Allocation Split I35).',
       cites={'prior_year_amount': [FS_FED], 'amount': [('plan', 'FTA Allocation Split (26-27) I35')]}),

    # ───────── TNT/TMA ─────────
    ln(id='tnt-tot-nlte', name='Placer County TOT – NLTE', program=('Placer County transient occupancy tax', 'local'), recipient='TNTTMA', administered_by='Placer County', amount=162595, growth=0.04, contributor='PLA',
       match_text='No match requirement', required={'service': ['NLTE']}, preferred={'jurisdiction_share': ['PLA']}, alloc=shares({'NLTE': 1}, [(None, 'NLTE budget line')]),
       cites={'amount': [tnt('F9')], 'match': [rp(28)], 'projection': [a2('4% annually')]}),
    ln(id='tnt-tot-pr', name='Placer County TOT – Park & Ride', program=('Placer County transient occupancy tax', 'local'), recipient='TNTTMA', administered_by='Placer County', amount=749956, prior=128580, growth=0.04, contributor='PLA',
       match_text='No match requirement', required={'service': ['PR-W', 'PR-S']}, preferred={'jurisdiction_share': ['PLA']}, alloc=auto('vsh', ['PR-W', 'PR-S']),
       cites={'amount': [tnt('F29')], 'prior_year_amount': [('plan', 'TNTTMA $ E29 (FY 25-26)')], 'projection': [a2('4% annually')]}),
    ln(id='tnt-tot-van', name='Placer County TOT – Vanpools', program=('Placer County transient occupancy tax', 'local'), recipient='TNTTMA', administered_by='Placer County', amount=195800, prior=220818, growth=0.04, contributor='PLA',
       match_text='No match requirement', required={'service': ['VAN']}, alloc=shares({'VAN': 1}, [(None, 'Vanpool budget line')]),
       cites={'amount': [tnt('K29')], 'prior_year_amount': [('plan', 'TNTTMA $ J29 (FY 25-26)')], 'projection': [a2('4% annually')]}),
    ln(id='tnt-tntn', name='Travel North Tahoe Nevada (NLTE)', program=('Visitor bureau contribution', 'private'), recipient='TNTTMA', administered_by='Travel North Tahoe Nevada', amount=26421, prior=30390,
       restriction_text='Airport shuttle service in CA/NV', match_text='No match requirement', condition_text='Ideally used only in NV', purpose='Contribution for NLTE operations.',
       required={'service': ['NLTE']}, preferred={'state': ['NV']}, alloc=shares({'NLTE': 1}, [rp(26)]),
       notes='The Local Funds fact sheet card shows "TTD budgeted $8,000," although the funded system is NLTE.',
       cites={'amount': [tnt('F10')], 'prior_year_amount': [('plan', 'TNTTMA $ E10 (FY 25-26)')], 'match': [rp(26)], 'restrictions': [('loc1', 'Travel North Tahoe Nevada')]}),
    ln(id='tnt-washoe', name='Washoe County (NLTE)', program=('County contribution', 'local'), recipient='TNTTMA', administered_by='Washoe County', amount=12500, prior=25000, contributor='WAS',
       match_text='No match requirement', required={'service': ['NLTE']}, alloc=shares({'NLTE': 1}, [(None, 'NLTE budget line')]),
       cites={'amount': [tnt('F11')], 'prior_year_amount': [('plan', 'TNTTMA $ E11 (FY 25-26)')]}),
    ln(id='tnt-rtaa', name='Reno-Tahoe Airport Authority (NLTE)', program=('Airport authority contribution', 'local'), recipient='TNTTMA', administered_by='Reno-Tahoe Airport Authority', amount=12500, prior=0,
       restriction_text='Airport shuttle service in CA/NV', match_text='No match requirement', purpose='Contribution for NLTE operations.', required={'service': ['NLTE']}, alloc=shares({'NLTE': 1}, [rp(27)]),
       cites={'amount': [tnt('F12')], 'prior_year_amount': [FS_L1], 'match': [rp(27)], 'restrictions': [('loc1', 'Reno-Tahoe Airport Authority')]}),
    ln(id='tnt-truckee', name='Town of Truckee (NLTE)', program=('Town of Truckee contribution', 'local'), recipient='TNTTMA', administered_by='Town of Truckee', amount=15500, prior=15500, contributor='TRK',
       match_text='No match requirement', required={'service': ['89', '267', 'NLTE']}, alloc=shares({'NLTE': 1}, [(None, 'NLTE budget line')]),
       cites={'amount': [tnt('F13')], 'prior_year_amount': [('plan', 'TNTTMA $ E13 (FY 25-26)')], 'restrictions': [('loc1', 'Town of Truckee')]}),
    ln(id='tnt-truckee2', name='Additional Truckee contribution (NLTE)', program=('Town of Truckee contribution', 'local'), recipient='TNTTMA', administered_by='Truckee (not specified)', amount=2927,
       match_text='No match requirement', required={'service': ['NLTE']}, alloc=shares({'NLTE': 1}, [rp(30)]),
       notes='The FY 25-26 per-route model lists Visit Truckee Tahoe ($2,932) for NLTE; confirm whether this is the same contribution.', cites={'amount': [tnt('F14')]}),
    ln(id='tnt-nevco', name='Nevada County (Park & Ride)', program=('County contribution', 'local'), recipient='TNTTMA', administered_by='Nevada County', amount=16339, contributor='NEV',
       match_text='No match requirement', required={'service': ['PR-W', 'PR-S']}, alloc=auto('vsh', ['PR-W', 'PR-S']), cites={'amount': [tnt('F31')]}),
    ln(id='tnt-northstar', name='Northstar (Park & Ride)', program=('Resort contribution', 'private'), recipient='TNTTMA', administered_by='Northstar', amount=3862, prior=21413,
       match_text='No match requirement', required={'service': ['PR-W', 'PR-S']}, alloc=auto('vsh', ['PR-W', 'PR-S']),
       cites={'amount': [tnt('F32')], 'prior_year_amount': [('plan', 'TNTTMA $ E32 (FY 25-26)')]}),
    ln(id='tnt-palisades', name='Palisades Tahoe (Park & Ride)', program=('Resort contribution', 'private'), recipient='TNTTMA', administered_by='Palisades Tahoe', amount=124076, prior=119304,
       match_text='No match requirement', required={'service': ['PR-W', 'PR-S']}, alloc=auto('vsh', ['PR-W', 'PR-S']),
       cites={'amount': [tnt('F33')], 'prior_year_amount': [('plan', 'TNTTMA $ E33 (FY 25-26)')]}),
    ln(id='tnt-ntca', name='North Tahoe Community Alliance (Park & Ride)', program=('Nonprofit contribution', 'private'), recipient='TNTTMA', administered_by='North Tahoe Community Alliance', amount=0, prior=487173,
       status='none', commitment='none', match_text='No match requirement', required={'service': ['PR-W', 'PR-S']}, alloc=auto('vsh', ['PR-W', 'PR-S']),
       commit_note='FY 25-26 $487,173; $0 in the FY 26-27 budget, which relies on Placer County TOT instead.',
       cites={'amount': [('plan', 'TNTTMA $ V10 (FY 26-27 = $0)')], 'prior_year_amount': [('plan', 'TNTTMA $ E30 (FY 25-26)')]}),
    ln(id='tnt-fares', name='Fares – North Lake Tahoe Express', program=('Passenger fares', 'fare'), recipient='TNTTMA', administered_by='Riders', amount=377656, prior=445263, counts_as_match=False, commitment='earned',
       required={'service': ['NLTE']}, alloc=shares({'NLTE': 1}, [(None, 'Fares belong to the route that collects them')]),
       cites={'amount': [tnt('F15')], 'prior_year_amount': [('plan', 'TNTTMA $ E15 (FY 25-26)')], 'projection': [a2('G87: flat')]}),
    ln(id='tnt-reserve', name='NLTE reserve', program=('Reserve draw', 'other'), recipient='TNTTMA', administered_by='TNT/TMA', amount=240000, last_year=0, commitment='onetime', match_text='No match requirement',
       required={'service': ['NLTE']}, alloc=shares({'NLTE': 1}, [(None, 'NLTE budget line')]), commit_note='Included so the NLTE FY 26-27 budget balances (Table 7 note).', cites={'amount': [tnt('F16')]}),
]

FTA = dict(apportionment_5307=4296912.69, apportionment_5339=405232.2, apportionment_5310=75224.8, operations_share=0.75, weight_revenue_miles=1, weight_population=1, weight_ridership=1,
           cites=[('plan', 'FTA Allocation Split (26-27) K23:M23 (FY 25-26 apportionment plus 1%, marked EXAMPLE); G33 (75% operating)')])
FTA_FACTORS = {
    'TTD': dict(urban_revenue_miles=803084, population=31420, ridership=489907),
    'TART': dict(urban_revenue_miles=1408116, population=16643, ridership=613042),
}
FTA_FACTOR_CITE = [('plan', 'FTA Allocation Split (26-27) F17:G20 (urban revenue miles), F22:F23 (2020 Census population), L17:L18 (FY 22-23 ridership)')]

# (id, title, description, citations)
DATA_ISSUES = [
    ('DI-01', 'Costs tab total double-counts TART Main Line', 'The costs tab total ($23,078,713, K25) sums the Main Line subtotal (row 16) and its three segments (rows 13–15), counting $2,497,613 twice. The model counts the segments once.', [('scen', 'costs K25, K13:K16')]),
    ('DI-02', 'Route 30 cost rate', 'The costs tab prices Route 30 at the Lake Link Via rate ($68.70/VSH, $240,450). VRH Rates lists $147.80/VSH for Route 30 (TTD–Via), and the FY 26-27 Emerald Bay Shuttle budget is $517,288.', [('scen', 'costs J7; VRH Rates J10'), ('plan', 'T2-4 G20')]),
    ('DI-03', 'TNT/TMA service costs', 'The costs tab estimates NLTE at $241,181 (1,200 VSH) and Park & Ride at $602,952 (3,000 VSH). The TNT/TMA FY 26-27 budget shows NLTE $694,260 and Park & Ride $894,233.', [('scen', 'costs rows 22–24'), ('plan', 'TNTTMA $ F22, F43')]),
    ('DI-04', 'TART FTA 5307 amount', 'The per-route model uses $1,653,136 (75 percent of Placer\'s earned share); TART\'s plan (Table A2) budgets $2,660,000.', [('plan', 'Per Route Model E12; T5-7 G59')]),
    ('DI-05', 'TART service-hour total double-counts Main Line', 'Operating Stats F45 sums F19:F26, so TART 5307 shares on Revenue %s row 3 sum to 72 percent. Funding Model V1G corrects it.', [('plan', 'Operating Stats F45; Revenue %s row 3'), ('v1g', 'Operating Stats F45')]),
    ('DI-06', 'TDA rows mislabeled and unused', 'Per Route Model D19 and D21 are labeled LTF and STA but hold TTD\'s rural third ($615,042) and urban two-thirds ($1,230,085) of LTF plus STA; no route formulas use them.', [('plan', 'Per Route Model D19, D21; T2-4 G66:G67')]),
    ('DI-07', 'US 50 service added without removing 19X', 'The service plan adds $476,500 for the US 50 replacement while Route 19X\'s cost is still counted.', [('plan', 'T2-4 rows 21, 29')]),
    ('DI-08', 'Washoe support may be counted twice', 'Revenue %s gives 4.2 percent of Washoe RTC\'s $296,055 to NLTE, but TNT/TMA budgets Washoe County NLTE support separately ($12,500).', [('plan', 'Revenue %s row 25; TNTTMA $ F11')]),
    ('DI-09', 'TDVA formula error', 'Per Route Model row 28 multiplies the Nevada State Parks amount (D27, $85,000) instead of the TDVA amount (D28, $120,000).', [('plan', 'Per Route Model O28')]),
    ('DI-10', 'LCTOP and interest shares leave out Route 30', 'Revenue %s rows 15 and 20 divide by TTD hours including Route 30 but give it 0 percent, so shares sum to 90 percent. Funding Model V1G uses F48.', [('plan', 'Revenue %s rows 15, 20'), ('v1g', 'Operating Stats F48')]),
    ('DI-11', 'Revenue %s check totals', 'G53 onward sum only rows 37–51; AD10 sums F:K and skips the ADA column, so it shows 88 percent though the shares total 100 percent.', [('plan', 'Revenue %s row 53, column AD')]),
    ('DI-12', 'Route 30 fares end a year early', 'Table A1 shows $0 fares in FY 27-28 though the pilot runs (cost $523,384 in H20). The model carries $54,570.', [('plan', 'T2-4 H72, H20')]),
    ('DI-13', 'TART 5310 missing from TART plan', '$75,225 to Placer in FY 26-27 (FTA split J35) is not in T5-7 Table A2.', [('plan', 'Per Route Model E17; FTA Allocation Split J35')]),
    ('DI-14', 'Fact sheet items missing from the FY 26-27 plan', 'Nevada State allocation $346,500, local appropriation $232,235, and Martis Zones of Benefit $50,000 (all FY 25-26). Listed at $0.', [('state', 'Nevada State'), ('loc1', 'Local Appropriation; Martis Zones of Benefit')]),
    ('DI-15', 'Fact sheet and plan disagree', 'TDVA $65,000 (FY 25-26) vs $120,000 (FY 26-27 plan). The Travel North Tahoe Nevada card shows "TTD budgeted $8,000" though it funds NLTE.', [('loc1', 'Tahoe Douglas Visitor Authority; Travel North Tahoe Nevada')]),
    ('DI-16', 'Copied and broken cells', 'Per Route Model row 1 cost cells for Lake Link, Main Line, Hwy 89, Hwy 267, and TART Connect repeat TTD route values; Revenue %s H83 and Actual Revenues G83 show #REF!.', [('plan', 'Per Route Model row 1; Revenue %s H83; Actual Revenues G83')]),
    ('DI-17', 'Match rate for NDOT 5311', 'Revenue %s lists 50 percent non-federal match for 5311; partner notes say NDOT match is 20 percent for administration, 40 percent for operating, and 5 percent for capital.', [('plan', 'Revenue %s C6, F64')]),
    ('DI-18', 'Electrification credits', 'Revenue %s notes call electrification credits "not real money, only used as match." The fact sheet lists $8,000 budgeted for TTD operations.', [('plan', 'Revenue %s B16:C16'), ('state', 'Electrification Credits')]),
    ('DI-19', 'Lake Link hours', 'Lake Link VSH are contract hours, not actuals.', [('scen', 'costs U12')]),
]

AGREEMENTS = [
    ('AG-01', 'Lake Link funding agreements with Douglas County and the City of South Lake Tahoe', 'The only two written Lake Link contracts. The plan assumes support continues at existing levels after the current terms end.', [('plan', 'Per Route Model D88; T2-4 note 6')]),
    ('AG-02', 'SSTMA operating contract for Lake Link (Downtowner/Via)', 'Sets the Lake Link hourly cost and the 2027 contract service hours.', [('scen', 'VRH Rates L9'), ('plan', 'T2-4 note 2')]),
    ('AG-03', 'Emerald Bay Shuttle (Route 30) pilot: TTD–Via contract and pilot funding', 'Keep Tahoe Blue, Carbon Reduction Program, El Dorado County, and Placer County funds committed through FY 27-28.', [('plan', 'T2-4 rows 79–82')]),
    ('AG-04', 'Placer County TART Connect contract', 'Contract-specified escalation of 5 percent per year.', [('scen', 'VRH Rates L15')]),
    ('AG-05', 'My Ride to Work contracts with TART and TNT/TMA', 'Bus and van rates for Park & Ride shuttles and NLTE; the MRTW contract is listed at $488,320.', [('scen', 'VRH Rates rows 18–21'), ('plan', 'Revenue %s M81')]),
    ('AG-06', 'FTA 5307, 5339, and 5310 sub-allocation between TTD and Placer County', 'Earned-share worksheet based on revenue miles, population, and ridership. FTA expects the MPO and designated recipients to set the split through a "fair and rational" process.', [('plan', 'FTA Allocation Split (26-27); Revenue %s AD59')]),
    ('AG-07', 'TRPA TDA apportionment (LTF and STA) to TTD and TART', 'The plan assumes no change in the TRPA TDA split; TTD applies one-third to rural and two-thirds to urban routes.', [('plan', 'T2-4 note 2; Revenue %s AE10')]),
    ('AG-08', 'LCTOP rotation between TTD and TART', 'LCTOP alternates every other year based on ridership.', [('plan', 'Revenue %s D67')]),
    ('AG-09', 'NDOT 5311 subrecipient agreement with TTD', 'Partner notes record NDOT match at 20 percent for administration, 40 percent for operating, and 5 percent for capital.', [('plan', 'Revenue %s F64')]),
    ('AG-10', 'Tahoe Blue Events Center transportation mitigation fee', 'A $3 ticket surcharge allocated to transit, with an annual attendee cap.', [('plan', 'T2-4 note 7')]),
    ('AG-11', 'Partner cost-sharing practices on TTD routes', "Costs are allocated by route by percent of miles per month, utility costs are pooled systemwide by partner agreement, and whoever receives a route's benefit gets its urban or rural benefit.", [('plan', 'Revenue %s E61:E63, C65')]),
    ('AG-12', 'Lake Link private partners', 'SLTTID, Heavenly, Caesars, Round Hill Pines, Advance Learning, LTVA, and LTCC contributed in FY 25-26 with no FY 26-27 commitment.', [('plan', 'T2-4 note 8')]),
]
