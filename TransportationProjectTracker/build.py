"""Build index.html, the Transportation Plan Projects tool.

Reads the three plan lists in data/, links projects that appear in more than one plan,
and writes one self-contained page from src/template.html. Needs Python 3 only.

    python build.py
"""
import base64, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.dont_write_bytecode = True   # keep data/ free of __pycache__
sys.path.insert(0, str(ROOT / "data"))
from rtp_project_list import RTP, RTP_TOTALS
from vision_zero_locations import VZ
from atp_project_tables import TABLES, NOT_ON_MAP, COMPLETE

SNAPSHOT = "Oct. 21, 2026"   # date the ATP map layer was pulled; shown on the page

CSLT, EDC, PC, DC, WC, CC, REG = ("City of South Lake Tahoe", "El Dorado County", "Placer County",
                                  "Douglas County", "Washoe County", "Carson City", "Regional")
COUNTY = {"El Dorado": EDC, "Placer": PC, "Douglas": DC, "Washoe": WC, "Carson": CC, "Carson City": CC,
          "Regional": REG, "Various": REG}

def counties(txt):
    out = []
    for t in re.split(r"[/;]|\s(?=Carson)", txt):
        t = t.strip()
        if t and COUNTY[t] not in out:
            out.append(COUNTY[t])
    return out

# RTP rows inside the City of South Lake Tahoe that the county column lists as El Dorado.
# Value is the jurisdiction list to use. Location taken from each row's own description.
RTP_JUR = {
    "03.02.02.0109": [CSLT], "03.01.02.0030": [CSLT], "03.02.02.0106": [CSLT], "03.02.02.0122": [DC],
    "4589": [CSLT], "03.02.01.0062": [CSLT], "TBD|Spruce Class 1 Connector Bridge": [CSLT],
    "TBD|B Street Pedestrian Crossing": [CSLT],
    "03.02.02.0085": [EDC, CSLT], "03.02.02.0117": [EDC, CSLT], "03.02.02.0123": [EDC, CSLT],
    "03.02.02.0065": [EDC], "03.02.02.0119": [EDC], "2716": [CSLT],
    "03.02.01.0047": [EDC, CSLT], "04.02.02.0011": [CSLT],
}

recs = []
# ---------- RTP
for i, (lst, cat, no, title, desc, lead, county, c1, c2, c3) in enumerate(RTP):
    sig = title.rstrip().endswith("*")
    title = title.rstrip().rstrip("*").strip()
    jur = counties(county)
    key = no if no != "TBD" else f"TBD|{title}"
    if key in RTP_JUR:
        jur = RTP_JUR[key]
    elif lead == CSLT:
        jur = [CSLT if j == EDC else j for j in jur]
    costs = [c1, c2, c3]
    total = None if c1 is None else c1 + c2 + c3
    periods = [p for p, c in zip(["2025-2030", "2031-2040", "2041-2050"], costs) if c]
    nos = [n.strip() for n in no.split(",")]
    link = None
    if re.match(r"^\d\d\.\d\d\.\d\d\.\d{4}$", nos[0]):
        link = f"https://eip.laketahoeinfo.org/Project/FactSheet/{nos[0]}"
    recs.append(dict(
        id=f"R{i}", plan="RTP", no=no, nos=nos, title=title, desc=desc, lead=lead, jur=jur,
        type=cat, status=f"{lst} (financially {'constrained' if lst=='Constrained' else 'unconstrained'})" if False else lst,
        when=", ".join(periods) if periods else "Not listed", cost=total,
        c2030=c1, c2040=c2, c2050=c3, sig=sig, link=link, county=county,
    ))

# ---------- Vision Zero
for i, (loc, lead, tf, conn, pri, jur) in enumerate(VZ):
    recs.append(dict(
        id=f"V{i}", plan="VZ", no="", nos=[], title=loc, desc="",
        lead=lead, jur=jur, type="Safety location", status="Priority project" if pri else "Candidate location",
        when=tf, cost=None, conn=conn, link=None,
    ))

# ---------- 2024 ATP: Chapter 4 corridor tables, cross-referenced to the proposed-facilities map
CLASS = {0: "Sidewalk", 1: "Class 1 shared use path", 2: "Class 2 bike lane", 3: "Class 3 bike route", 5: "Complete streets"}
ATPJ = {"El Dorado": EDC, "Placer": PC, "Douglas": DC, "Washoe": WC, "Carson City": CC, "City of South Lake Tahoe": CSLT}
norm = lambda t: re.sub(r"[^a-z0-9]", "", t.lower().replace("–", "-").replace("5th", "5th"))
maprows = {}
for i, r in enumerate(json.load(open(ROOT / "data" / "atp_map_snapshot.json", encoding="utf-8"))["rows"]):
    maprows.setdefault(norm(r[2]), []).append((i, r))
used = set()
money = lambda v: "$" + format(v, ",")
ai = 0
for tab, corridor, pages, rows in TABLES:
    for tier, eip, pname, pimpl, pmiles, pcost, pphase, pyear, maplabel in rows:
        cand = maprows.get(norm(maplabel or pname), [])
        hit = None
        for i, r in cand:
            if i not in used and (len(cand) == 1 or r[1] == eip or eip == "NOT LISTED"):
                hit = (i, r); break
        rec = dict(id=f"A{ai}", plan="ATP", no="" if eip == "NOT LISTED" else eip, nos=[] if eip == "NOT LISTED" else [eip],
                   title=pname, lead=pimpl, status="Priority " + tier if tier[0].isdigit() else tier, tier="Priority " + tier if tier[0].isdigit() else tier,
                   when="Completion year TBD" if pyear == "TBD" else f"Complete by {pyear}", cost=pcost, miles=pmiles, phase=pphase,
                   corridor=f"{corridor} ({tab}, page {pages})", onmap=bool(hit), diffs=[])
        ai += 1
        if eip != "NOT LISTED":
            rec["link"] = f"https://eip.laketahoeinfo.org/Project/FactSheet/{eip}"
        if hit:
            i, (name, meip, label, impl, sy, cy, desc, cost, phase, miles, cls, url, fin, fund, jur) = hit
            used.add(i)
            if impl == "City of South Lake tahoe": impl = CSLT
            d = desc.strip()
            if len(d) >= 495: d += "…"
            jl = sorted([ATPJ[j] for j in jur.split(";") if j], key=lambda j: [CSLT, EDC, PC, DC, WC, CC].index(j))
            mcost = int(cost.replace("$", "").replace(",", "")) if cost else None
            rec.update(mapName=name, label=label if norm(label) != norm(pname) else "", desc=d, jur=jl, type=CLASS[cls], funding=fin)
            if url and "link" not in rec: rec["link"] = url
            dif = rec["diffs"]
            if meip != eip: dif.append(f"EIP number on map: {meip.title() if meip == 'NOT LISTED' else meip}")
            if mcost != pcost: dif.append(f"Cost on map: {money(mcost) if mcost else 'none'}")
            if abs((miles or 0) - pmiles) > 0.005: dif.append(f"Miles on map: {miles}")
            if cy != pyear: dif.append(f"Completion year on map: {cy}")
            if phase != pphase: dif.append(f"Phase on map: {phase}")
            if impl != pimpl: dif.append(f"Implementer on map: {impl}")
            if label and norm(label) != norm(pname): dif.append(f"Name on map: {label}")
        else:
            t, jl = NOT_ON_MAP[pname]
            rec.update(mapName="", label="", desc="", jur=jl, type=t, funding="", status="Complete" if pname in COMPLETE else rec["status"])
        recs.append(rec)
unmatched = [r for k, v in maprows.items() for i, r in v if i not in used]
print("ATP plan rows", ai, "| on map", len(used), "| map facilities not in tables", [r[2] for r in unmatched])
# Jurisdiction decisions (Oct. 23 review) applied to the ATP entry of the same project
for r in recs:
    if r["plan"] == "ATP" and r["title"] in ("Sawmill to City Bike Path", "Lake Tahoe Blvd bike lanes"):
        r["jur"] = [EDC]
by = {r["id"]: r for r in recs}

# ---------- Matching
parent = {r["id"]: r["id"] for r in recs}
def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]; x = parent[x]
    return x
links = []
def link(a, b, why):
    if a == b: return
    links.append((a, b, why))
    parent[find(a)] = find(b)

def rtp(no=None, title=None):
    out = [r["id"] for r in recs if r["plan"] == "RTP" and ((no and no in r["nos"]) or (title and r["title"] == title))]
    assert out, (no, title)
    return out
def atp(name=None, label=None):
    out = [r["id"] for r in recs if r["plan"] == "ATP" and ((name and r.get("mapName") == name) or (label and r.get("label") == label))]
    assert out, (name, label)
    return out
def vz(loc):
    out = [r["id"] for r in recs if r["plan"] == "VZ" and r["title"] == loc]
    assert out, loc
    return out[0]

SAME_NO, SAME_NAME, CONN, LOC = ("Same EIP project number", "Same project, matched by name and limits",
    "Vision Zero lists this project under connections to existing plans", "Same location and limits")

# 1. Same EIP number between RTP and ATP
for a in [r for r in recs if r["plan"] == "ATP" and r["nos"]]:
    for b in [r for r in recs if r["plan"] == "RTP" and set(r["nos"]) & set(a["nos"])]:
        link(a["id"], b["id"], SAME_NO)
# 2. Segments that share one project name within the ATP layer
seen = {}
for r in recs:
    if r["plan"] == "ATP" and r["mapName"] and r["mapName"] != "North Tahoe Regional Bike Trail":
        if r["mapName"] in seen: link(r["id"], seen[r["mapName"]], "Segments of the same project on the ATP map")
        else: seen[r["mapName"]] = r["id"]
# 3. RTP and ATP rows with no shared number, matched by name and limits
M = [
 ("03.02.02.0109", dict(name="Link Road to Sussex Ave")),
 ("03.02.02.0106", dict(name="South Tahoe Greenway Shared Use Trail Planning and Future Phases")),
 ("03.02.02.0114", dict(name="Lake Pkwy South Sidewalks")),
 ("03.02.02.0118", dict(name="South Tahoe Greenway Phase 4a - Pioneer to Elks Club")),
 ("03.02.02.0117", dict(name="South Tahoe Greenway Phase 4b - Elks Club to Nottaway")),
 ("03.02.02.0117", dict(name="South Tahoe Greenway Phase 4c: Nottaway to Golden Bear")),
 ("03.02.02.0117", dict(name="South Tahoe Greenway Phase 4d: Golden Bear to Johnson Meadow Path")),
 ("03.02.02.0127", dict(name="Northwood Blvd Class 1")),
 ("03.02.02.0123", dict(name="US hwy 50 bike lane Meyers to City")),
 ("03.02.02.0129", dict(name="Tahoe Keys Blvd Complete Streets")),
 ("03.02.02.0128", dict(name="Complete streets from Pioneer Trail to Heavenly")),
 ("03.02.02.0112", dict(name="Johnson Blvd to Lester Ave bike path connector")),
 ("03.02.02.0130", dict(name="Herbert Ave Complete Streets")),
 ("03.02.02.0119", dict(name="Viking Rd to Sawmill Rd bike lanes")),
 ("03.02.02.0120", dict(name="SR28 Class 1 Country Club to Sweetwater")),
 ("T:Mt. Rose Highway Bike Lanes", dict(name="Mt. Rose Hwy Bike Lanes")),
 ("T:Fox & Speckled Complete Streets", dict(name="Fox & Speckled Complete Streets")),
 ("T:Dolly Varden/Deer St. Sidewalks", dict(name="Dolly Varden/Deer St Sidewalks")),
 ("T:Kings Beach Shared Use Path-Remaining Segments", dict(name="Kings Beach Shared Use Path: SR267 - Stateline")),
 ("T:Spruce Class 1 Connector Bridge", dict(name="Spruce Class 1 Connector Bridge")),
 ("T:B Street Pedestrian Crossing", dict(name="B Street Overpass")),
]
for k, a in M:
    rs = rtp(title=k[2:]) if k.startswith("T:") else rtp(no=k)
    for x in atp(**a):
        for y in rs: link(x, y, SAME_NAME)
# West Shore Tahoe Trail (RTP) = Cascade to Meeks Trail segments (ATP)
for seg in ("1 - Meeks", "2- Rubicon", "3 - Paradise", "4 - DL Bliss North"):
    for x in [r["id"] for r in recs if r["plan"] == "ATP" and r["mapName"].startswith("Cascade to Meeks Trail " + seg)]:
        link(x, rtp(no="03.02.02.0115")[0], SAME_NAME)
for seg in ("5 - ", "6 - ", "7 - ", "8 - ", "9 - ", "10 - "):
    for x in [r["id"] for r in recs if r["plan"] == "ATP" and r["mapName"].startswith("Cascade to Meeks Trail " + seg)]:
        for y in rtp(no="03.02.02.0116"): link(x, y, SAME_NAME)
# 4. Vision Zero locations
VZM = [
 ("Pioneer Trail from Ski Run Blvd to Price Rd", rtp(no="03.02.02.0113"), LOC),
 ("US 50 at F St to SR 89 at 10th St", rtp(no="4589"), LOC),
 ("US 50 from Old Meyers Grade Rd to Echo Summit Rd", rtp(no="4593"), LOC),
 ("US 50 from Lakeview Drive to Church St", rtp(no="4620"), LOC),
 ("SR 28 from Southwood/Northwood Blvd East to Southwood/Northwood Blvd West", rtp(no="4621"), LOC),
 ("SR 28 from Thunderbird Cove to Secret Harbor", rtp(no="03.02.01.0017"), LOC),
 ("SR 28/N Lake Blvd, Beach St to Secline St including SR 28 & SR 267 intersection & SR 267 to Dolly Varden Ave", rtp(no="01.01.01.0168"), CONN),
 ("US 50 from Lake Parkway to SR 207 intersection", rtp(no="03.02.01.0007"), CONN),
 ("US 50 from Stateline Ave to Lake Parkway, including Lake Parkway intersection", rtp(no="03.02.01.0007"), CONN),
 ("SR 89 from Cascade Lake Rd to Upper Emerald Bay FS Rd", rtp(no="03.01.02.0044"), CONN),
]
for loc, targets, why in VZM:
    for t in targets: link(vz(loc), t, why)

# ---------- Groups
groups = {}
for r in recs:
    groups.setdefault(find(r["id"]), []).append(r["id"])
gi = 0
for root, ids in groups.items():
    plans = sorted({by[i]["plan"] for i in ids}, key=["RTP", "ATP", "VZ"].index)
    gid = f"G{gi}" if len(ids) > 1 else None; gi += 1
    for i in ids:
        by[i]["group"] = gid
        by[i]["plans"] = plans
reasons = {}
for a, b, why in links:
    reasons.setdefault(a, {})[b] = why
    reasons.setdefault(b, {})[a] = why
for r in recs:
    r["why"] = reasons.get(r["id"], {})

import sys
VERBOSE = "-v" in sys.argv
multi = {r["group"] for r in recs if len(r["plans"]) > 1}
print("records", len(recs), "| groups spanning 2+ plans", len(multi),
      "| records in them", sum(1 for r in recs if len(r["plans"]) > 1))
for g in sorted(multi, key=lambda g: int(g[1:])):
    if VERBOSE: print(" ", g, " | ".join(f'{r["plan"]}:{r["title"][:40]}' for r in recs if r["group"] == g))

# ---------- Page
tok = (ROOT / 'assets' / 'trpa-tokens.css').read_text(encoding='utf-8')
root = tok[tok.index(':root {'):]
depth = 0
for i, ch in enumerate(root):
    if ch == '{': depth += 1
    elif ch == '}':
        depth -= 1
        if depth == 0: root = root[:i+1]; break
root = re.sub(r'/\*.*?\*/', '', root, flags=re.S)
root = '\n'.join(l.rstrip() for l in root.splitlines() if l.strip())
def block(sel):
    s = tok[tok.index(sel):]
    d = 0
    for i, ch in enumerate(s):
        if ch == '{': d += 1
        elif ch == '}':
            d -= 1
            if d == 0: return s[:i+1]
ct = re.sub(r'/\*.*?\*/', '', block('[data-brand="connecting-tahoe"] {'), flags=re.S)
root = root + "\n" + '\n'.join(l.rstrip() for l in ct.splitlines() if l.strip())
data = json.dumps(recs, separators=(',', ':'), ensure_ascii=False).replace('</', '<\\/')
html = (ROOT / 'src' / 'template.html').read_text(encoding='utf-8')
b64 = lambda f: base64.b64encode((ROOT / 'assets' / f).read_bytes()).decode()
for k, v in {'__TOKENS__': root, '__LOGO__': b64('trpa-logo.png'), '__FAVICON__': b64('favicon.ico'),
             '__BUILT__': SNAPSHOT, '__DATA__': data}.items():
    html = html.replace(k, v)
assert not re.search(r'__(TOKENS|LOGO|FAVICON|BUILT|DATA)__', html)
(ROOT / 'index.html').write_text(html, encoding='utf-8')
print(f'Wrote index.html ({len(html):,} characters)')
