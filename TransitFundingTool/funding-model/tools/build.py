"""Build the model's data files from tools/seed_source.py.

Writes:
  data/seed.json           normalized tables matching schema.sql (the canonical data)
  data/seed.js             the same tables for the browser apps (window.FUNDING_SEED)
  data/funding_model.sqlite  schema.sql loaded with every row, keys and checks enforced
  data/seed.sql            SQL dump of that database

Run from anywhere:  python -P tools/build.py
"""
import json, os, re, sqlite3, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import seed_source as S  # noqa: E402


def slug(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def build_tables():
    T = {k: [] for k in ['source_document', 'fiscal_year', 'agency', 'jurisdiction', 'operator', 'service', 'service_year', 'service_jurisdiction',
                         'funding_program', 'funding_line', 'funding_line_year', 'eligibility_rule', 'fta_suballocation', 'fta_earned_share_factor',
                         'allocation_scenario', 'allocation_rule', 'allocation_share', 'allocation_target', 'citation', 'agreement', 'data_issue', 'scenario_change']}
    cites = T['citation']

    def cite(entity_type, entity_id, field, refs):
        for doc, loc in (refs or []):
            cites.append(dict(citation_id=len(cites) + 1, entity_type=entity_type, entity_id=entity_id, field=field, document_id=doc, locator=loc))

    for k, (fn, desc) in S.DOCUMENTS.items():
        T['source_document'].append(dict(document_id=k, file_name=fn, description=desc))
    for i, label in enumerate(S.YEARS):
        T['fiscal_year'].append(dict(fy_index=i, label=label))
    for a, n, sh in S.AGENCIES:
        T['agency'].append(dict(agency_id=a, name=n, short_name=sh))
    for j, n, sh, st in S.JURISDICTIONS:
        T['jurisdiction'].append(dict(jurisdiction_id=j, name=n, short_name=sh, state=st))
    for o, n, rate, esc, basis, c in S.OPERATORS:
        T['operator'].append(dict(operator_id=o, name=n, cost_per_vsh=rate, annual_escalator=esc, basis=basis))
        cite('operator', o, 'rate', c)

    for s in S.SERVICES:
        T['service'].append(dict(service_id=s['id'], name=s['name'], short_name=s['short'], agency_id=s['agency'], operator_id=s['operator'],
                                 service_group=s['group'] or None, area_class=s['area'], service_type=s['type'], federalized=int(s['federalized']),
                                 is_plan_element=int(s['plan']), included=int(s['included']), passenger_trips=s['trips'], vsh=s['vsh'], vsm=s['vsm'],
                                 data_year=s['data_year'] or None, cost_per_vsh_override=s['rate_override'], annual_cost_override=s['cost_override'],
                                 reference_cost=s['ref_cost'], adjusts_service_id=s['adjusts'], state_conditions=s['state_cond'] or None, local_conditions=s['local_cond'] or None,
                                 notes=s['note'] or None))
        if s['schedule'] is not None or s['active_years'] is not None:
            for y in range(len(S.YEARS)):
                active = True if s['active_years'] is None else bool(s['active_years'][y])
                sched = None if s['schedule'] is None else s['schedule'][y]
                T['service_year'].append(dict(service_id=s['id'], fy_index=y, active=int(active), scheduled_cost=sched))
        for j, share in s['juris'].items():
            T['service_jurisdiction'].append(dict(service_id=s['id'], jurisdiction_id=j, share=share, is_placeholder=int(s['juris_placeholder'])))
        cite('service', s['id'], 'cost', s['cite'])
        cite('service', s['id'], 'reference_cost', s['ref_cite'])

    programs = {}
    for l in S.LINES:
        name, level = l['program']
        pid = slug(name)
        if pid in programs and programs[pid]['level'] != level:
            raise SystemExit(f'Program {name} used with two levels')
        programs.setdefault(pid, dict(program_id=pid, name=name, level=level, grantor=None))
    T['funding_program'] = list(programs.values())

    T['allocation_scenario'].append(dict(scenario_id='draft', name='Consultant draft shares', method='fixed_shares',
                                         description='Shares from Financial PlanG Revenue %s; sources the draft left unallocated are split by service hours as placeholders.'))
    T['allocation_scenario'].append(dict(scenario_id='optimized', name='Rules-based optimized allocation', method='optimized',
                                         description='The engine allocates every source to maximize funded service subject to all required rules, federal share caps, and match.'))

    for l in S.LINES:
        lid = l['id']
        T['funding_line'].append(dict(line_id=lid, program_id=slug(l['program'][0]), recipient_agency_id=l['recipient'], name=l['name'], administered_by=l['administered_by'] or None,
                                      base_amount=float(l['amount']), amount_method=l['amount_method'], prior_year_amount=l['prior'], growth_rate=float(l['growth']),
                                      last_fy_index=l['last_year'], annual_cap=l['cap'], status=l['status'], commitment_basis=l['commitment'],
                                      commitment_note=l['commit_note'] or None, contributor_jurisdiction_id=l['contributor'], federal_share_cap=l['fed_share'],
                                      federal_share_cap_ada=l['fed_share_ada'], counts_as_match=int(l['counts_as_match']), match_only=int(l['match_only']),
                                      enabled=int(l['enabled']), purpose=l['purpose'] or None, match_text=l['match_text'] or None, condition_text=l['condition_text'] or None,
                                      restriction_text=l['restriction_text'] or None, notes=l['notes'] or None))
        for y, amt in sorted(l['overrides'].items()):
            T['funding_line_year'].append(dict(line_id=lid, fy_index=int(y), amount=float(amt)))
        for strength, rules in (('required', l['required']), ('preferred', l['preferred'])):
            for rtype, values in rules.items():
                for v in values:
                    T['eligibility_rule'].append(dict(rule_row_id=len(T['eligibility_rule']) + 1, line_id=lid, rule_type=rtype, strength=strength, value=v))
        a = l['alloc']
        if a:
            T['allocation_rule'].append(dict(scenario_id='draft', line_id=lid, method=a['method'], auto_basis=a.get('basis') if a['method'] == 'auto' else None))
            if a['method'] == 'shares':
                for sid, sh in a['shares'].items():
                    T['allocation_share'].append(dict(scenario_id='draft', line_id=lid, service_id=sid, share=sh))
            for sid in (a.get('targets') or []):
                T['allocation_target'].append(dict(scenario_id='draft', line_id=lid, service_id=sid))
            cite('funding_line', lid, 'allocation', a.get('cite'))
        for field, refs in l['cites'].items():
            cite('funding_line', lid, field, refs)

    f = S.FTA
    T['fta_suballocation'].append(dict(fy_index=0, apportionment_5307=f['apportionment_5307'], apportionment_5339=f['apportionment_5339'], apportionment_5310=f['apportionment_5310'],
                                       operations_share=f['operations_share'], weight_revenue_miles=f['weight_revenue_miles'], weight_population=f['weight_population'],
                                       weight_ridership=f['weight_ridership']))
    cite('fta', 'fta_suballocation', 'apportionment', f['cites'])
    for a, v in S.FTA_FACTORS.items():
        T['fta_earned_share_factor'].append(dict(agency_id=a, **v))
    cite('fta', 'fta_earned_share_factor', 'factors', S.FTA_FACTOR_CITE)

    for i, t, d, c in S.AGREEMENTS:
        T['agreement'].append(dict(agreement_id=i, title=t, description=d))
        cite('agreement', i, 'description', c)
    for i, t, d, c in S.DATA_ISSUES:
        T['data_issue'].append(dict(issue_id=i, title=t, description=d))
        cite('data_issue', i, 'description', c)
    return T


def check(T):
    """Consistency checks the database constraints cannot express."""
    errs = []
    svc_ids = {s['service_id'] for s in T['service']}
    for s in T['service']:
        shares = [r['share'] for r in T['service_jurisdiction'] if r['service_id'] == s['service_id']]
        if not shares:
            errs.append(f"service {s['service_id']} has no jurisdiction shares")
        elif abs(sum(shares) - 1) > 1e-9:
            errs.append(f"service {s['service_id']} jurisdiction shares sum to {sum(shares)}")
        if s['is_plan_element'] and not any(r['service_id'] == s['service_id'] and r['scheduled_cost'] is not None for r in T['service_year']):
            errs.append(f"plan element {s['service_id']} has no scheduled costs")
    for l in T['funding_line']:
        sh = [r['share'] for r in T['allocation_share'] if r['line_id'] == l['line_id']]
        if sum(sh) > 1 + 1e-9:
            errs.append(f"line {l['line_id']} draft shares sum to {sum(sh)}")
    for r in T['eligibility_rule']:
        if r['rule_type'] == 'service' and r['value'] not in svc_ids:
            errs.append(f"rule on {r['line_id']} names unknown service {r['value']}")
    return errs


def load_sqlite(T, path):
    if os.path.exists(path):
        os.remove(path)
    con = sqlite3.connect(path)
    con.execute('PRAGMA foreign_keys = ON')
    with open(os.path.join(ROOT, 'schema.sql'), encoding='utf-8') as fh:
        con.executescript(fh.read())
    order = ['source_document', 'fiscal_year', 'agency', 'jurisdiction', 'operator', 'service', 'service_year', 'service_jurisdiction', 'funding_program',
             'funding_line', 'funding_line_year', 'eligibility_rule', 'fta_suballocation', 'fta_earned_share_factor', 'allocation_scenario', 'allocation_rule',
             'allocation_share', 'allocation_target', 'citation', 'agreement', 'data_issue', 'scenario_change']
    for t in order:
        for row in T[t]:
            cols = list(row.keys())
            con.execute(f'INSERT INTO {t} ({",".join(cols)}) VALUES ({",".join("?" * len(cols))})', [row[c] for c in cols])
    con.commit()
    bad = con.execute('PRAGMA foreign_key_check').fetchall()
    if bad:
        raise SystemExit(f'Foreign key violations: {bad[:5]}')
    ok = con.execute('PRAGMA integrity_check').fetchone()[0]
    counts = {t: con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0] for t in order}
    with open(os.path.join(ROOT, 'data', 'seed.sql'), 'w', encoding='utf-8') as fh:
        for line in con.iterdump():
            fh.write(line + '\n')
    con.close()
    return ok, counts


def main():
    T = build_tables()
    errs = check(T)
    if errs:
        print('Data check failed:')
        for e in errs:
            print(' -', e)
        raise SystemExit(1)
    os.makedirs(os.path.join(ROOT, 'data'), exist_ok=True)
    meta = dict(model='Lake Tahoe Region transit funding model', schema_version='1.0', base_year='FY 26-27',
                note='Generated by tools/build.py from tools/seed_source.py. Do not edit by hand.')
    seed = dict(meta=meta, tables=T)
    with open(os.path.join(ROOT, 'data', 'seed.json'), 'w', encoding='utf-8') as fh:
        json.dump(seed, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(ROOT, 'data', 'seed.js'), 'w', encoding='utf-8') as fh:
        fh.write('/* Generated by tools/build.py from tools/seed_source.py. Do not edit by hand. */\n')
        fh.write('window.FUNDING_SEED = ' + json.dumps(seed, ensure_ascii=False, separators=(',', ':')) + ';\n')
    ok, counts = load_sqlite(T, os.path.join(ROOT, 'data', 'funding_model.sqlite'))
    print('SQLite integrity:', ok)
    for t, n in counts.items():
        print(f'  {t:26s} {n}')


if __name__ == '__main__':
    main()
