"""Independent checks of the funding model, written separately from the JavaScript engine.

1. Data fidelity: re-reads the workbooks and compares every seeded hour count, cost, and budget amount
   with the cell it was taken from.
2. Optimizer cross-check: rebuilds the rules-based allocation as a linear program from data/seed.json
   with its own code and solves it with its own simplex, then prints funded service for the scenarios
   the browser tests report, so the two implementations can be compared.

Usage:  python -P tools/verify.py "<folder with the source workbooks>"
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SEED = json.load(open(os.path.join(ROOT, 'data', 'seed.json'), encoding='utf-8'))['tables']


def rows(t):
    return SEED[t]


# ── 1. Data fidelity ────────────────────────────────────────────────────────
def data_checks(folder):
    import openpyxl
    scen = openpyxl.load_workbook(os.path.join(folder, 'Example Transit Financial Scenario Workbook.xlsx'), data_only=True)
    plan = openpyxl.load_workbook(os.path.join(folder, 'Financial PlanG.xlsx'), data_only=True)
    costs, prm, a1, a2, tnt, fta = scen['costs'], plan['Per Route Model'], plan['T2-4 A1 TTD LL Costs'], plan['T5-7 TART TNTTMA FinancialPlan'], plan['TNTTMA $'], plan['FTA Allocation Split (26-27)']
    svc = {s['service_id']: s for s in rows('service')}
    op = {o['operator_id']: o for o in rows('operator')}
    line = {l['line_id']: l for l in rows('funding_line')}
    bad, n = [], 0

    def cmp(label, model, source, tol=0.51):
        nonlocal n
        n += 1
        if source is None or model is None or abs(float(model) - float(source)) > tol:
            bad.append(f'{label}: model {model} vs source {source}')

    row_of = {'19X': 4, '22': 5, '28': 6, '30': 7, '50': 8, '51': 9, '55': 10, 'ADA-TTD': 11, 'LL': 12, 'TART-WS': 13, 'TART-NS': 14, 'TART-NV': 15,
              '89': 17, '267': 18, 'NIGHT': 19, 'ADA-PLA': 20, 'TC': 21, 'PR-W': 22, 'PR-S': 23, 'NLTE': 24}
    for sid, r in row_of.items():
        s = svc[sid]
        cmp(f'{sid} VSH (costs H{r})', s['vsh'], costs[f'H{r}'].value, 0.001)
        if costs[f'G{r}'].value is not None:
            cmp(f'{sid} trips (costs G{r})', s['passenger_trips'], costs[f'G{r}'].value, 0.001)
        rate = s['cost_per_vsh_override'] if s['cost_per_vsh_override'] is not None else op[s['operator_id']]['cost_per_vsh']
        cmp(f'{sid} cost (costs K{r})', s['vsh'] * rate, costs[f'K{r}'].value, 0.01)
    cmp('Costs tab total less Main Line (K25 - K16)', sum(svc[k]['vsh'] * op[svc[k]['operator_id']]['cost_per_vsh'] for k in row_of), costs['K25'].value - costs['K16'].value, 0.05)

    cells = {
        'ttd-5307': (prm, 'D12'), 'ttd-5307cmaq': (prm, 'D13'), 'ttd-5307co': (prm, 'D14'), 'ttd-5311nv': (prm, 'D15'), 'ttd-5310co': (prm, 'D18'),
        'ttd-ltf': (a1, 'G66'), 'ttd-sta': (a1, 'G67'), 'ttd-lctop': (prm, 'D24'), 'ttd-elec': (prm, 'D25'), 'ttd-sb125': (prm, 'D26'), 'ttd-nvparks': (prm, 'D27'),
        'ttd-tdva': (prm, 'D28'), 'ttd-interest': (prm, 'D29'), 'ttd-ktb': (prm, 'D30'), 'ttd-crp': (prm, 'D31'), 'ttd-eldebs': (prm, 'D32'), 'ttd-plaebs': (prm, 'D33'),
        'ttd-fares30': (a1, 'G72'), 'll-sb125': (prm, 'F26'), 'll-douglas': (prm, 'F43'), 'll-cslt': (prm, 'F44'), 'll-tahoeblue': (prm, 'F45'),
        'tart-5307': (prm, 'E12'), 'tart-5310': (prm, 'E17'), 'tart-5311ca': (prm, 'E16'), 'tart-ltf-trpa': (prm, 'E19'), 'tart-ltf-pctpa': (prm, 'E20'),
        'tart-sta-trpa': (prm, 'E21'), 'tart-sta-pctpa': (prm, 'E22'), 'tart-sgr': (prm, 'E23'), 'tart-washoe': (prm, 'E34'), 'tart-truckee': (prm, 'E38'),
        'tart-nsrp': (prm, 'E40'), 'tart-nslp': (prm, 'E41'), 'tart-martis': (prm, 'E42'),
        'tnt-tot-nlte': (tnt, 'F9'), 'tnt-tntn': (tnt, 'F10'), 'tnt-washoe': (tnt, 'F11'), 'tnt-rtaa': (tnt, 'F12'), 'tnt-truckee': (tnt, 'F13'),
        'tnt-truckee2': (tnt, 'F14'), 'tnt-fares': (tnt, 'F15'), 'tnt-reserve': (tnt, 'F16'), 'tnt-tot-pr': (tnt, 'F29'), 'tnt-nevco': (tnt, 'F31'),
        'tnt-northstar': (tnt, 'F32'), 'tnt-palisades': (tnt, 'F33'), 'tnt-tot-van': (tnt, 'K29'),
    }
    for lid, (ws, c) in cells.items():
        cmp(f'{lid} amount ({ws.title} {c})', line[lid]['base_amount'], ws[c].value or 0, 0.51)
    cmp('Placer TOT for TART (T5-7 G68) = TART Connect + fixed route', line['tart-tot-tc']['base_amount'] + line['tart-tot-fr']['base_amount'], a2['G68'].value)
    for y, col in zip(range(1, 5), 'HIJK'):
        cmp(f'Douglas County year {y} (T2-4 {col}86)', next((r['amount'] for r in rows('funding_line_year') if r['line_id'] == 'll-douglas' and r['fy_index'] == y), line['ll-douglas']['base_amount'] if y > 1 else None) if y == 1 else 850000, a1[f'{col}86'].value)
    f = rows('fta_suballocation')[0]
    cmp('5307 apportionment (FTA split K23)', f['apportionment_5307'], fta['K23'].value, 0.01)
    fac = {r['agency_id']: r for r in rows('fta_earned_share_factor')}
    cmp('TTD revenue miles (F28)', fac['TTD']['urban_revenue_miles'], fta['F28'].value, 0)
    cmp('Placer revenue miles (F29)', fac['TART']['urban_revenue_miles'], fta['F29'].value, 0)
    cmp('TTD ridership (J28)', fac['TTD']['ridership'], fta['J28'].value, 0)
    cmp('TTD population (H28)', fac['TTD']['population'], fta['H28'].value, 0)
    for o, cell in (('TTD', 'J7'), ('Via', 'J9'), ('TART', 'J14'), ('Placer Via', 'J15'), ('Truckee', 'J16'), ('MRTW', 'J20')):
        cmp(f'{o} rate (VRH Rates {cell})', op[o]['cost_per_vsh'], scen['VRH Rates'][cell].value, 0.0001)
    return n, bad


# ── 2. Independent LP ───────────────────────────────────────────────────────
JUR_STATE = {j['jurisdiction_id']: j['state'] for j in rows('jurisdiction')}


def model_inputs(year, drop=(), cost_scale=1.0):
    ops = {o['operator_id']: o for o in rows('operator')}
    sy = {}
    for r in rows('service_year'):
        sy[(r['service_id'], r['fy_index'])] = r
    shares = {}
    for r in rows('service_jurisdiction'):
        shares.setdefault(r['service_id'], {})[r['jurisdiction_id']] = r['share']
    services = []
    for s in rows('service'):
        if s['adjusts_service_id'] or not s['included']:
            continue
        r = sy.get((s['service_id'], year))
        if r and not r['active']:
            continue
        if r and r['scheduled_cost'] is not None:
            c = r['scheduled_cost']
        else:
            rate = s['cost_per_vsh_override'] if s['cost_per_vsh_override'] is not None else ops[s['operator_id']]['cost_per_vsh']
            base = s['annual_cost_override'] if s['annual_cost_override'] is not None else (s['vsh'] or 0) * rate
            c = base * (1 + ops[s['operator_id']]['annual_escalator']) ** year
        if c > 0:
            services.append(dict(s, cost=c * cost_scale, juris=shares.get(s['service_id'], {})))
    prog = {p['program_id']: p for p in rows('funding_program')}
    yov = {(r['line_id'], r['fy_index']): r['amount'] for r in rows('funding_line_year')}
    fac = {r['agency_id']: r for r in rows('fta_earned_share_factor')}
    fta = rows('fta_suballocation')[0]

    def fta_amount(agency):
        a, b = fac['TTD'], fac['TART']
        parts = [a[k] / (a[k] + b[k]) for k in ('urban_revenue_miles', 'population', 'ridership')]
        w = [fta['weight_revenue_miles'], fta['weight_population'], fta['weight_ridership']]
        ttd = sum(p * q for p, q in zip(parts, w)) / sum(w)
        return fta['apportionment_5307'] * (ttd if agency == 'TTD' else 1 - ttd) * fta['operations_share']

    rules = {}
    for r in rows('eligibility_rule'):
        rules.setdefault(r['line_id'], {}).setdefault(r['strength'], {}).setdefault(r['rule_type'], []).append(r['value'])
    lines = []
    for l in rows('funding_line'):
        if not l['enabled'] or l['status'] == 'capital' or l['line_id'] in drop:
            continue
        if l['last_fy_index'] is not None and year > l['last_fy_index']:
            continue
        a = fta_amount(l['recipient_agency_id']) if l['amount_method'] == 'fta_5307_formula' else l['base_amount']
        cap = l['annual_cap'] if l['annual_cap'] is not None else float('inf')
        a = min(a, cap)
        for y in range(1, year + 1):
            a = min(yov[(l['line_id'], y)] if (l['line_id'], y) in yov else a * (1 + l['growth_rate']), cap)
        lines.append(dict(l, amount=a, level=prog[l['program_id']]['level'], rules=rules.get(l['line_id'], {})))
    return services, lines


def eligible(l, s, transfers, strict):
    """Returns the eligible portion of cost (0 = not eligible), following the written rules."""
    req, pref = l['rules'].get('required', {}), l['rules'].get('preferred', {})
    if 'service' in req and s['service_id'] not in req['service']:
        return 0
    if 'agency' in req and s['agency_id'] not in req['agency']:
        return 0
    if 'area_class' in req and s['area_class'] not in req['area_class']:
        return 0
    if 'service_type' in req and s['service_type'] not in req['service_type']:
        return 0
    if l['level'] == 'federal' and not s['federalized']:
        return 0
    tot = sum(s['juris'].values()) or 1
    portion = 1.0
    if 'state' in req:
        portion = min(portion, sum(v for k, v in s['juris'].items() if JUR_STATE[k] in req['state']) / tot)
    if 'jurisdiction_share' in req:
        portion = min(portion, sum(s['juris'].get(j, 0) for j in req['jurisdiction_share']) / tot)
    if portion <= 1e-9:
        return 0
    if l['recipient_agency_id'] != 'REGION' and s['agency_id'] != l['recipient_agency_id'] and not transfers:
        return 0
    if strict:
        if 'service' in pref and s['service_id'] not in pref['service']:
            return 0
        if 'state' in pref and sum(v for k, v in s['juris'].items() if JUR_STATE[k] in pref['state']) <= 1e-9:
            return 0
        if 'jurisdiction_share' in pref and sum(s['juris'].get(j, 0) for j in pref['jurisdiction_share']) <= 1e-9:
            return 0
    return portion


def solve_max_funded(year, drop=(), transfers=False, strict=False):
    services, lines = model_inputs(year, drop)
    pairs = [(l, s, p) for l in lines for s in services for p in [eligible(l, s, transfers, strict)] if p > 0]
    n = len(pairs)
    A, b = [], []
    for l in lines:
        r = np.zeros(n)
        for j, (pl, ps, _) in enumerate(pairs):
            if pl is l:
                r[j] = 1
        if r.any():
            A.append(r); b.append(l['amount'] / 1e6)
    for s in services:
        r, mrow = np.zeros(n), np.zeros(n)
        for j, (pl, ps, p) in enumerate(pairs):
            if ps is not s:
                continue
            if not pl['match_only']:
                r[j] = 1
            if pl['level'] == 'federal':
                k = pl['federal_share_cap_ada'] if (s['service_type'] == 'paratransit' and pl['federal_share_cap_ada'] is not None) else pl['federal_share_cap']
                if k is not None:
                    mrow[j] = (1 - k) / k
            elif pl['level'] != 'fare' and (pl['counts_as_match'] or pl['match_only']):
                mrow[j] = -1
        A.append(r); b.append(s['cost'] / 1e6)
        if (mrow > 0).any():
            A.append(mrow); b.append(0.0)
    for j, (pl, ps, p) in enumerate(pairs):
        if p < 1 - 1e-9:
            r = np.zeros(n); r[j] = 1; A.append(r); b.append(p * ps['cost'] / 1e6)
    c = np.array([0.0 if pl['match_only'] else 1.0 for pl, _, _ in pairs])
    return simplex_bland(np.array(A), np.array(b), c) * 1e6


def simplex_bland(A, b, c):
    """Maximize c x subject to A x <= b, x >= 0, b >= 0, with Bland's rule throughout (no cycling)."""
    m, n = A.shape
    T = np.zeros((m + 1, n + m + 1))
    T[:m, :n] = A
    T[:m, n:n + m] = np.eye(m)
    T[:m, -1] = b
    T[m, :n] = -c
    basis = list(range(n, n + m))
    for _ in range(100000):
        cand = np.where(T[m, :-1] < -1e-11)[0]
        if not len(cand):
            break
        e = cand[0]
        col = T[:m, e]
        ok = np.where(col > 1e-11)[0]
        ratios = T[ok, -1] / col[ok]
        best = ratios.min()
        r = min((i for i, q in zip(ok, ratios) if q <= best + 1e-13), key=lambda i: basis[i])
        T[r] /= T[r, e]
        for i in range(m + 1):
            if i != r and T[i, e] != 0:
                T[i] -= T[i, e] * T[r]
        basis[r] = e
    return T[m, -1]


def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(ROOT)
    n, bad = data_checks(folder)
    print(f'Data fidelity: {n - len(bad)} of {n} values match their source cells')
    for x in bad:
        print('  MISMATCH', x)
    print('Independent optimizer (funded service, dollars):')
    for label, kw in [('FY 26-27 base', dict(year=0)), ('FY 26-27 without SB 125', dict(year=0, drop=('ttd-sb125', 'll-sb125'))),
                      ('FY 26-27 strict preferences', dict(year=0, strict=True)), ('FY 30-31 base', dict(year=4)), ('FY 30-31 with transfers', dict(year=4, transfers=True))]:
        print(f'  {label:32s} {solve_max_funded(**kw):,.0f}')


if __name__ == '__main__':
    main()
