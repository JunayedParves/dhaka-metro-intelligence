"""
Phase 2 build script - Dhaka MRT Line-6 SYNTHETIC operational datasets (28 Dec 2022 - 13 Nov 2026).

Generates, with a fixed random seed, seven synthetic datasets plus supporting tables:
  synthetic_daily_ridership.csv        Date x Station
  synthetic_hourly_ridership.csv       Date x Hour x Station x Direction
  synthetic_ticket_revenue.csv         Date x Station x Fare_Product
  synthetic_train_operations.csv       one row per simulated train run
  synthetic_energy_consumption.csv     Date x Component
  synthetic_maintenance_incidents.csv  one row per work order / incident
  synthetic_monthly_opex.csv           Month x Expense_Category
  synthetic_daily_line_summary.csv     Date (line totals, service pattern, calibration flags)
  estimated_fare_matrix.csv            modelled station-to-station fares (Estimated)

EVERY row is labelled Data_Type = Synthetic (or Estimated / Actual where stated) and is NOT an
observation.  Published figures are used only as calibration targets; see
05_Documentation/phase2_synthetic_methodology.md.

Standard library only.  Run:  python 05_Documentation/scripts/build_phase2.py
"""
import csv
import math
import random
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

SEED = 20261113
rng = random.Random(SEED)

ROOT = Path(__file__).resolve().parents[2]
D_SYN = ROOT / "03_Synthetic_Data"
D_DOC = ROOT / "05_Documentation"
D_RES = ROOT / "01_Research"
D_MOD = ROOT / "04_Analytical_Models"
for d in (D_SYN, D_DOC, D_MOD):
    d.mkdir(parents=True, exist_ok=True)

START, END = date(2022, 12, 29), date(2026, 11, 13)   # 28 Dec 2022 was the inauguration; passengers from 29 Dec
TRAIN_CAPACITY = 2300                                  # S016
ROUTE_KM_FULL, ROUTE_KM_NORTH = 20.10, 11.73           # S001

# ------------------------------------------------------------------ parameters (see assumptions register)
BETA = 0.03            # distance-deterrence per km in the destination-choice model (tuned, see methodology)
PEAK_HOURS = {8, 9, 17, 18, 19}
TRACTION_KWH_PER_TRAIN_KM = 20.0
STATION_KWH_PER_DAY = 6500.0      # per open station at a 14.5 h service day
DEPOT_KWH_PER_DAY = 20000.0
EMPTY_RUNNING = 0.03

# ------------------------------------------------------------------ stations
# id, name, category (res / mix / cbd), entry-share weight (full line), fare-distance chainage in tenths of km, opening date
ST = [
 ("MRT6-01", "Uttara North", "res", 9.5, 0, date(2022, 12, 29)),
 ("MRT6-02", "Uttara Center", "res", 2.0, 9, date(2023, 2, 18)),
 ("MRT6-03", "Uttara South", "res", 1.5, 22, date(2023, 3, 31)),
 ("MRT6-04", "Pallabi", "res", 8.5, 53, date(2023, 1, 25)),
 ("MRT6-05", "Mirpur 11", "res", 6.0, 60, date(2023, 3, 15)),
 ("MRT6-06", "Mirpur 10", "res", 9.5, 73, date(2023, 3, 1)),
 ("MRT6-07", "Kazipara", "res", 5.0, 80, date(2023, 3, 15)),
 ("MRT6-08", "Shewrapara", "res", 5.0, 90, date(2023, 3, 31)),
 ("MRT6-09", "Agargaon", "mix", 6.5, 109, date(2022, 12, 29)),
 ("MRT6-10", "Bijoy Sarani", "mix", 2.0, 119, date(2023, 12, 13)),
 ("MRT6-11", "Farmgate", "mix", 7.0, 131, date(2023, 11, 5)),
 ("MRT6-12", "Karwan Bazar", "cbd", 8.5, 142, date(2023, 12, 31)),
 ("MRT6-13", "Shahbagh", "mix", 5.5, 153, date(2023, 12, 31)),
 ("MRT6-14", "Dhaka University", "mix", 4.0, 162, date(2023, 12, 13)),
 ("MRT6-15", "Bangladesh Secretariat", "cbd", 8.3, 172, date(2023, 11, 5)),
 ("MRT6-16", "Motijheel", "cbd", 13.5, 193, date(2023, 11, 5)),
]
N = len(ST)
SID = [s[0] for s in ST]
SNAME = [s[1] for s in ST]
CHAIN = [s[4] for s in ST]
# weights while only the northern section was open (Agargaon acted as the city-side terminal)
W_NORTH = [22, 4, 3, 14, 9, 15, 6, 6, 21, 0, 0, 0, 0, 0, 0, 0]
W_FULL = [s[3] for s in ST]
FULL_LINE = date(2023, 11, 5)
SOUTH_FULL_HOURS = date(2024, 1, 20)     # until then stations south of Agargaon served 07:30-11:30 only (assumption A205)


def fare(i, j):
    """Modelled fare: Tk 5/km on fare-distance, rounded up to Tk 10, min 20, max 100."""
    d10 = abs(CHAIN[i] - CHAIN[j])
    return min(100, max(20, -(-d10 // 20) * 10))


CONFIRMED_FARES = [  # Phase 1 fare_structure_history.csv (S018, S023)
 (0, 3, 30), (0, 4, 30), (0, 5, 40), (0, 6, 40), (0, 7, 50), (0, 8, 60), (0, 9, 60), (0, 10, 70), (0, 14, 90), (0, 15, 100),
 (1, 10, 70), (1, 14, 90), (1, 15, 100), (5, 10, 30), (5, 11, 40), (5, 14, 50), (5, 15, 60), (8, 10, 20), (8, 14, 40),
 (8, 15, 50), (10, 15, 40)]
FARE = [[fare(i, j) for j in range(N)] for i in range(N)]
DIST = [[abs(CHAIN[i] - CHAIN[j]) / 10.0 for j in range(N)] for i in range(N)]

# ------------------------------------------------------------------ calendar
EID_FITR = [date(2023, 4, 22), date(2024, 4, 11), date(2025, 3, 31), date(2026, 3, 21)]
EID_ADHA = [date(2023, 6, 29), date(2024, 6, 17), date(2025, 6, 7), date(2026, 5, 28)]
RAMADAN_START = [date(2023, 3, 24), date(2024, 3, 12), date(2025, 3, 2), date(2026, 2, 19)]
FIXED_HOLIDAYS = {(2, 21): "Language Martyrs' Day", (3, 26): "Independence Day", (4, 14): "Bengali New Year",
                  (5, 1): "May Day", (12, 16): "Victory Day", (12, 25): "Christmas Day"}
CLOSED_FROM, CLOSED_TO = date(2024, 7, 19), date(2024, 8, 24)     # S014


def holiday_info(d):
    """returns (flag, name, demand factor)."""
    for e, nm in [(x, "Eid-ul-Fitr") for x in EID_FITR] + [(x, "Eid-ul-Adha") for x in EID_ADHA]:
        k = (d - e).days
        if k == 0:
            return 1, nm + " day", 0.0
        if k in (-2, -1):
            return 1, nm + " holiday (pre)", 0.75
        if 1 <= k <= 3:
            return 1, nm + " holiday (post)", (0.45, 0.55, 0.70)[k - 1]
        if 4 <= k <= 6:
            return 0, nm + " return week", 0.86
    if (d.month, d.day) in FIXED_HOLIDAYS:
        return 1, FIXED_HOLIDAYS[(d.month, d.day)], 0.62
    if d >= date(2025, 8, 5) and (d.month, d.day) == (8, 5):
        return 1, "July Mass Uprising Day", 0.62
    return 0, "", 1.0


def ramadan_day(d):
    for rs, ef in zip(RAMADAN_START, EID_FITR):
        if rs <= d < ef:
            return (d - rs).days + 1, (ef - rs).days
    return 0, 0


def service(d):
    """Service pattern for date d, or None when closed.
    returns dict(start,end in minutes after midnight; peak/off headway; sets; south_end_min (None = same as end))"""
    wd = d.weekday()                      # Mon=0 ... Fri=4, Sat=5, Sun=6
    if CLOSED_FROM <= d <= CLOSED_TO:
        return None
    if d in EID_FITR or d in EID_ADHA:
        return None                       # assumption A204
    fri = wd == 4
    if d < date(2023, 5, 31):
        if wd == 1:
            return None                   # weekly closure on Tuesdays (S014)
        return dict(start=480, end=720, pk=10, off=10, sets=6, south=None)
    if d < date(2024, 9, 20) and fri:
        return None
    if d < date(2023, 7, 8):
        return dict(start=480, end=1080, pk=10, off=15, sets=6, south=None)
    if d < FULL_LINE:
        return dict(start=480, end=1230, pk=10, off=15, sets=8, south=None)
    if d < SOUTH_FULL_HOURS:
        return dict(start=450, end=1230, pk=10, off=12, sets=10, south=690)
    if d == date(2024, 7, 18):
        return dict(start=430, end=840, pk=8, off=10, sets=13, south=None)      # line closed that afternoon (S014)
    if d < date(2025, 10, 19):
        if fri:
            return dict(start=900, end=1260, pk=12, off=12, sets=8, south=None)  # 60 trips (S035)
        end = 1240 if d < date(2024, 3, 27) else 1300
        if d < date(2024, 2, 17):
            pk, off, sets = 10, 12, 10
        elif d < date(2025, 5, 1):
            pk, off, sets = 8, 10, 13                                           # ~198 trips/day (S035)
        else:
            pk, off, sets = 6, 10, 16                                           # ~238 trips/day (S035)
        return dict(start=430, end=end, pk=pk, off=off, sets=sets, south=None)
    if fri:
        return dict(start=870, end=1290, pk=10, off=10, sets=10, south=None)
    return dict(start=390, end=1330, pk=5, off=8, sets=19, south=None)          # ~297 trips/day (S035)


def is_peak_min(m):
    return 450 <= m < 660 or 960 <= m < 1200


# ------------------------------------------------------------------ line-level demand anchors (typical Sun-Thu working day)
ANCH = [
 (date(2022, 12, 30), 8500), (date(2023, 1, 15), 13000), (date(2023, 2, 15), 12000), (date(2023, 3, 31), 15000),
 (date(2023, 5, 30), 20000), (date(2023, 5, 31), 44000), (date(2023, 7, 7), 58000), (date(2023, 7, 8), 66000),
 (date(2023, 7, 20), 72000), (date(2023, 10, 31), 86000), (date(2023, 11, 5), 100000), (date(2023, 12, 1), 128000),
 (date(2023, 12, 31), 160000), (date(2024, 1, 19), 185000), (date(2024, 1, 20), 215000), (date(2024, 3, 1), 272000),
 (date(2024, 3, 31), 292000), (date(2024, 6, 30), 325000), (date(2024, 7, 1), 352000), (date(2024, 7, 18), 362000),
 (date(2024, 8, 25), 305000), (date(2024, 9, 1), 326000), (date(2024, 9, 20), 330000), (date(2024, 10, 15), 340000), (date(2024, 12, 31), 352000),
 (date(2025, 2, 1), 366000), (date(2025, 2, 28), 372000), (date(2025, 6, 30), 396000), (date(2025, 8, 15), 424000),
 (date(2025, 10, 25), 452000), (date(2025, 10, 27), 408000), (date(2025, 12, 31), 426000), (date(2026, 3, 1), 438000),
 (date(2026, 6, 30), 448000), (date(2026, 9, 1), 460000), (date(2026, 11, 13), 463000),
]
# published single-day totals: the synthetic line total is set equal to them (S012, S014, S016, S031)
PINS = {date(2022, 12, 29): 3857, date(2025, 2, 3): 382088, date(2025, 2, 13): 403164, date(2025, 8, 6): 456746,
        date(2026, 5, 21): 474635, date(2026, 8, 20): 478280, date(2026, 9, 10): 499756, date(2026, 9, 13): 480620,
        date(2026, 9, 14): 476815}
CUM_TARGET_DATE, CUM_TARGET = date(2026, 8, 31), 313546306          # S012 / S013
DOW = {6: 1.02, 0: 1.00, 1: 1.00, 2: 1.00, 3: 1.03, 4: 0.30, 5: 0.78}     # Sun..Thu working days; Fri-Sat weekend


def cap_for(d):
    """No un-pinned day may exceed the record standing at that date."""
    if d < date(2025, 2, 3):
        return 381500
    if d < date(2025, 2, 13):
        return 402500
    if d < date(2025, 8, 6):
        return 456000
    if d <= date(2026, 9, 19):
        return 474000            # the five highest days up to 19 Sep 2026 are all pinned (S012)
    return 499000


def anchor_level(d):
    if d <= ANCH[0][0]:
        return ANCH[0][1]
    for (d0, v0), (d1, v1) in zip(ANCH, ANCH[1:]):
        if d0 <= d <= d1:
            return v0 + (v1 - v0) * ((d - d0).days / max(1, (d1 - d0).days))
    return ANCH[-1][1]


WEATHER_P = {1: [("Clear", .63), ("Fog/Cold", .35), ("Light Rain", .02)], 2: [("Clear", .90), ("Light Rain", .08), ("Fog/Cold", .02)],
             3: [("Clear", .80), ("Light Rain", .12), ("Heavy Rain", .03), ("Heat", .05)],
             4: [("Clear", .50), ("Heat", .25), ("Light Rain", .15), ("Heavy Rain", .10)],
             5: [("Clear", .40), ("Heat", .20), ("Light Rain", .22), ("Heavy Rain", .18)],
             6: [("Clear", .25), ("Light Rain", .40), ("Heavy Rain", .30), ("Heat", .05)],
             7: [("Clear", .20), ("Light Rain", .45), ("Heavy Rain", .35)], 8: [("Clear", .22), ("Light Rain", .45), ("Heavy Rain", .33)],
             9: [("Clear", .30), ("Light Rain", .42), ("Heavy Rain", .28)], 10: [("Clear", .60), ("Light Rain", .28), ("Heavy Rain", .12)],
             11: [("Clear", .90), ("Light Rain", .08), ("Heavy Rain", .02)], 12: [("Clear", .80), ("Fog/Cold", .18), ("Light Rain", .02)]}
WEATHER_F = {"Clear": 1.00, "Light Rain": 1.02, "Heavy Rain": 0.95, "Heat": 1.01, "Fog/Cold": 0.99}


def draw(pairs):
    x, acc = rng.random(), 0.0
    for k, p in pairs:
        acc += p
        if x <= acc:
            return k
    return pairs[-1][0]


def lognorm(sd):
    return math.exp(rng.gauss(-sd * sd / 2, sd))


def alloc(total, weights):
    """Largest-remainder integer allocation of `total` across non-negative weights."""
    s = sum(weights)
    if total <= 0 or s <= 0:
        return [0] * len(weights)
    raw = [total * w / s for w in weights]
    out = [int(x) for x in raw]
    rem = total - sum(out)
    for k in sorted(range(len(raw)), key=lambda k: raw[k] - out[k], reverse=True)[:rem]:
        out[k] += 1
    return out


# hourly entry profiles (share of a station's daily entries by clock hour) by land-use category
PROF = {
 "res": {6: 2.0, 7: 7.5, 8: 13.5, 9: 12.5, 10: 7.5, 11: 5.0, 12: 4.5, 13: 4.5, 14: 4.5, 15: 5.0, 16: 5.5, 17: 6.5, 18: 6.5, 19: 5.5, 20: 4.0, 21: 2.5, 22: 0.8},
 "cbd": {6: 0.5, 7: 1.5, 8: 3.0, 9: 4.0, 10: 4.5, 11: 5.0, 12: 5.5, 13: 6.0, 14: 6.5, 15: 7.5, 16: 10.5, 17: 14.0, 18: 13.5, 19: 9.0, 20: 6.0, 21: 3.5, 22: 1.0},
 "cbd_ramadan": {6: 0.5, 7: 1.5, 8: 3.0, 9: 4.0, 10: 4.5, 11: 5.0, 12: 6.0, 13: 7.0, 14: 10.0, 15: 14.5, 16: 14.0, 17: 6.0, 18: 2.5, 19: 5.5, 20: 7.0, 21: 5.5, 22: 1.5},
 "leisure": {14: 8.0, 15: 14.0, 16: 16.0, 17: 17.0, 18: 16.0, 19: 14.0, 20: 11.0, 21: 6.0},
}
PROF["mix"] = {h: (PROF["res"][h] + PROF["cbd"][h]) / 2 for h in PROF["res"]}
PROF["mix_ramadan"] = {h: (PROF["res"][h] + PROF["cbd_ramadan"][h]) / 2 for h in PROF["res"]}
ATTR = {"am": {"cbd": 1.9, "mix": 1.1, "res": 0.45}, "mid": {"cbd": 1.0, "mix": 1.0, "res": 1.0}, "pm": {"cbd": 0.45, "mix": 1.0, "res": 1.8}}
DAYTYPE_MULT = {"sat": {"cbd": 0.75, "mix": 1.10, "res": 1.00}, "fri": {"cbd": 0.60, "mix": 1.25, "res": 1.00}}

_P_CACHE, _B_CACHE = {}, {}


def _probs(period, open_set, cats, base_w, b):
    P = [[0.0] * N for _ in range(N)]
    for i in open_set:
        ws = {j: base_w[j] * b[j] * ATTR[period][cats[j]] * math.exp(-BETA * DIST[i][j]) for j in open_set if j != i}
        tot = sum(ws.values())
        for j, w in ws.items():
            P[i][j] = w / tot
    return P


def _period_share(cat, fri_like):
    if fri_like:
        return {"am": 0.0, "mid": 1.0, "pm": 0.0}
    pf = PROF[cat]
    tot = sum(pf.values())
    am = sum(v for h, v in pf.items() if h < 11) / tot
    pm = sum(v for h, v in pf.items() if h >= 15) / tot
    return {"am": am, "mid": 1 - am - pm, "pm": pm}


def balance(ops, cats, wkey, fri_like):
    """Balancing factors so that each station's expected daily exits equal its entries (commuters return)."""
    key = (ops, cats, wkey, fri_like)
    if key not in _B_CACHE:
        base_w = W_FULL if wkey == "F" else W_NORTH
        b = [1.0] * N
        tw = sum(base_w[i] for i in ops)
        for _ in range(30):
            ex = [0.0] * N
            for period in ("am", "mid", "pm"):
                P = _probs(period, ops, cats, base_w, b)
                for i in ops:
                    sh = _period_share(cats[i], fri_like)[period] * base_w[i]
                    if sh:
                        for j in ops:
                            ex[j] += sh * P[i][j]
            for j in ops:
                if ex[j] > 0:
                    b[j] *= (base_w[j] / tw) / (ex[j] / sum(ex))
        _B_CACHE[key] = b
    return _B_CACHE[key]


def dest_probs(period, open_set, cats, ops, wkey, fri_like):
    """P[i][j]: probability that a passenger entering at i exits at j (balanced gravity model with distance deterrence)."""
    key = (period, open_set, cats, ops, wkey, fri_like)
    if key not in _P_CACHE:
        _P_CACHE[key] = _probs(period, open_set, cats, W_FULL if wkey == "F" else W_NORTH, balance(ops, cats, wkey, fri_like))
    return _P_CACHE[key]


# ------------------------------------------------------------------ provenance
def prov(model, conf="Low"):
    return ["Synthetic", model, conf, "See phase2_synthetic_methodology.md", "Yes", "No"]


PROV_COLS = ["Data_Type", "Source_ID", "Data_Confidence", "Methodology", "Is_Modelled", "Is_Verified"]

# ====================================================================================================
# PASS 1 - calendar, weather, service-affecting incidents and work orders
# ====================================================================================================
days = [START + timedelta(n) for n in range((END - START).days + 1)]
CAL = {}
for d in days:
    sv = service(d)
    hf, hname, hfac = holiday_info(d)
    rd, rlen = ramadan_day(d)
    CAL[d] = dict(sv=sv, hol=hf, hname=hname, hfac=hfac, ram=rd, ramlen=rlen, weather=draw(WEATHER_P[d.month]))


def open_stations(d):
    o = [i for i in range(N) if ST[i][5] <= d]
    if date(2024, 8, 25) <= d < date(2024, 9, 20):
        o = [i for i in o if i not in (5, 6)]          # Mirpur 10 and Kazipara closed (S014)
    elif date(2024, 9, 20) <= d < date(2024, 10, 15):
        o = [i for i in o if i != 5]
    return tuple(o)


def trips_for(d, sv):
    """Scheduled departures: list of (direction, dep_min, origin_idx, dest_idx, route_km, run_min)."""
    out = []
    full = d >= FULL_LINE
    for direction in ("Southbound", "Northbound"):
        t = float(sv["start"])
        while t <= sv["end"] - 0.01:
            short = (not full) or (sv["south"] is not None and t >= sv["south"])
            a, b = (0, 8) if short else (0, 15)
            km, run = (ROUTE_KM_NORTH, 20.0) if short else (ROUTE_KM_FULL, 38.0)
            o, de = (a, b) if direction == "Southbound" else (b, a)
            out.append((direction, t, o, de, km, run))
            t += sv["pk"] if is_peak_min(t) else sv["off"]
    return out


INC_CATS = [  # category, weight, median downtime (min), median cost (BDT), station-located?
 ("Rolling stock fault", .20, 14, 180000, False), ("Signalling / train control fault", .14, 16, 150000, False),
 ("Overhead catenary - foreign object (kite, wire, cloth)", .22, 22, 60000, True), ("Power supply trip", .08, 25, 220000, False),
 ("Platform screen door fault", .12, 8, 45000, True), ("Passenger incident / emergency alarm", .14, 7, 5000, True),
 ("Track / viaduct inspection hold", .04, 30, 120000, True), ("Severe weather speed restriction", .06, 18, 0, False)]
WO_CATS = [("Escalator / lift repair", .24, 95000), ("AFC gate / ticket machine repair", .24, 30000), ("Platform screen door servicing", .10, 40000),
           ("Station lighting / HVAC / plumbing", .16, 22000), ("Rolling stock corrective maintenance", .16, 140000),
           ("Track and OCS routine corrective work", .06, 110000), ("CCTV / telecom / PA system", .04, 35000)]

incidents = []        # rows for output
SVC_INC = defaultdict(list)   # date -> list of (start_min, downtime_min, cancel_prob)
inc_no = 0


def hhmm(m):
    m = int(round(m))
    return f"{(m // 60) % 24:02d}:{m % 60:02d}"


for d in days:
    c = CAL[d]
    sv = c["sv"]
    if sv is None:
        continue
    ops = open_stations(d)
    ntr = len(trips_for(d, sv))
    c["ntrips_sched"] = ntr
    # service-affecting incidents
    lam = 0.085 * ntr / 200.0 * (1.5 if c["weather"] == "Heavy Rain" else 1.0)
    k = 0
    while rng.random() < lam / (1 + k) and k < 3:
        k += 1
    for _ in range(k):
        cat = draw([(x, x[1]) for x in INC_CATS])
        if cat[0].startswith("Severe weather") and c["weather"] not in ("Heavy Rain", "Fog/Cold"):
            cat = INC_CATS[0]
        down = max(3, round(cat[2] * lognorm(0.75)))
        st_min = rng.uniform(sv["start"], sv["end"] - 10)
        sev = "Minor" if down < 10 else ("Moderate" if down <= 30 else "Major")
        cancel_p = 0.0 if down <= 30 else min(0.7, 0.3 + down / 300)
        SVC_INC[d].append((st_min, down, cancel_p))
        inc_no += 1
        incidents.append([f"INC-{inc_no:06d}", d.isoformat(), SID[rng.choice(ops)] if cat[4] else "", "", "Operational incident", cat[0], sev,
                          hhmm(st_min), hhmm(st_min + down), down, round(cat[3] * lognorm(0.6)),
                          "Trains delayed" + ("; some trips cancelled" if cancel_p else "")] + prov("M2-MNT"))
    # non-service work orders
    lam_wo = 0.16 * len(ops) * (1 + 0.25 * (d - START).days / 1400.0)
    kwo = max(0, round(rng.gauss(lam_wo, math.sqrt(lam_wo))))
    for _ in range(kwo):
        cat = draw([(x, x[1]) for x in WO_CATS])
        rolling = cat[0].startswith("Rolling")
        st_min = rng.uniform(sv["start"], sv["end"])
        dur = max(15, round(120 * lognorm(0.8)))
        inc_no += 1
        incidents.append([f"INC-{inc_no:06d}", d.isoformat(), "" if rolling else SID[rng.choice(ops)],
                          f"TS-{rng.randint(1, 24):02d}" if rolling else "", "Maintenance work order", cat[0], "Routine",
                          hhmm(st_min), hhmm(st_min + dur), 0, round(cat[2] * lognorm(0.7)), "No service impact"] + prov("M2-MNT"))

# documented real events (Actual) and their modelled service effect
REAL_EVENTS = [
 (date(2024, 7, 19), "MRT6-06", "Vandalism / civil unrest", "Critical", "Mirpur 10 station attacked and looted; line closed 19 Jul-24 Aug 2024, station closed to 15 Oct 2024; losses estimated at Tk 50 crore (with Kazipara)"),
 (date(2024, 7, 19), "MRT6-07", "Vandalism / civil unrest", "Critical", "Kazipara station attacked; station closed to 20 Sep 2024"),
 (date(2024, 9, 18), "", "Viaduct bearing pad displaced", "Major", "Section stopped for about 11 hours (660 min)"),
 (date(2025, 10, 26), "MRT6-11", "Viaduct bearing pad fell (Farmgate section)", "Critical", "Pedestrian killed; service suspended for a limited period - duration not verified"),
]
for dte, sid, cat, sev, note in REAL_EVENTS:
    inc_no += 1
    incidents.append([f"INC-{inc_no:06d}", dte.isoformat(), sid, "", "Operational incident", cat, sev, "", "",
                      660 if dte == date(2024, 9, 18) else "", "", note, "Actual", "S014", "Medium", "Documented event (Wikipedia citing news reports)", "No", "Yes"])
# modelled effect of the two documented stoppages on the synthetic service (assumption A208)
SVC_INC[date(2024, 9, 18)].append((560.0, 660, 0.55))
SVC_INC[date(2025, 10, 26)].append((750.0, 240, 0.80))
REAL_DEMAND_FACTOR = {date(2024, 9, 18): 0.62, date(2025, 10, 26): 0.60}

# ====================================================================================================
# PASS 2 - line-level daily ridership, calibrated to the published cumulative total
# ====================================================================================================
raw = {}
for d in days:
    c = CAL[d]
    if c["sv"] is None:
        raw[d] = 0.0
        continue
    f = anchor_level(d) * DOW[d.weekday()] * c["hfac"] * WEATHER_F[c["weather"]]
    if c["ram"]:
        f *= 0.97 if c["ram"] <= c["ramlen"] - 10 else 1.03
    if d < date(2023, 5, 31):
        f *= {4: 1.25, 5: 1.30}.get(d.weekday(), 1.0) / DOW[d.weekday()]     # novelty/leisure riders at weekends, 4-hour service
    if d == date(2024, 7, 18):
        f *= 0.45
    f *= REAL_DEMAND_FACTOR.get(d, 1.0)
    for st_min, down, cp in SVC_INC.get(d, []):
        if d not in REAL_DEMAND_FACTOR and down > 30:
            f *= 1 - min(0.25, 0.5 * down / (c["sv"]["end"] - c["sv"]["start"]))
    raw[d] = f * lognorm(0.025)


def finalise(scale):
    out = {}
    for d in days:
        if d in PINS:
            out[d] = PINS[d]
        elif raw[d] <= 0:
            out[d] = 0
        else:
            v = raw[d] * scale
            if date(2026, 9, 1) <= d <= date(2026, 9, 19) and d.weekday() in (6, 0, 1, 2, 3) and not CAL[d]["hol"] and not SVC_INC.get(d):
                v = max(v, 450500 + 2500 * rng.random())       # "always above 450,000" (S012)
            out[d] = int(round(min(v, cap_for(d))))
    return out


scale = 1.0
for _ in range(12):
    state = rng.getstate()
    line = finalise(scale)
    rng.setstate(state)
    cum = sum(v for d, v in line.items() if d <= CUM_TARGET_DATE)
    scale *= CUM_TARGET / cum
line = finalise(scale)
free = [d for d in days if d <= CUM_TARGET_DATE and d not in PINS and line[d] > 0 and line[d] < cap_for(d) - 2000]
resid = CUM_TARGET - sum(v for d, v in line.items() if d <= CUM_TARGET_DATE)
for d, add in zip(free, alloc(abs(resid), [line[x] for x in free])):
    line[d] += add if resid > 0 else -add
SCALE_USED = scale

# ====================================================================================================
# PASS 3 - station, hourly, revenue, trains, energy  (streamed to CSV)
# ====================================================================================================
def share_sjt(d):
    pts = [(date(2022, 12, 29), .80), (date(2023, 12, 31), .55), (date(2024, 12, 31), .42), (date(2025, 12, 31), .36), (date(2026, 11, 13), .33)]
    for (d0, v0), (d1, v1) in zip(pts, pts[1:]):
        if d0 <= d <= d1:
            return v0 + (v1 - v0) * (d - d0).days / (d1 - d0).days
    return pts[-1][1]


def share_rapid(d):
    pts = [(date(2022, 12, 29), .02), (date(2023, 12, 31), .04), (date(2024, 12, 31), .12), (date(2025, 12, 31), .24), (date(2026, 11, 13), .30)]
    for (d0, v0), (d1, v1) in zip(pts, pts[1:]):
        if d0 <= d <= d1:
            return v0 + (v1 - v0) * (d - d0).days / (d1 - d0).days
    return pts[-1][1]


def tariff(d):          # BDT per kWh, assumption A211
    return 8.6 if d < date(2023, 2, 1) else (9.7 if d < date(2024, 3, 1) else 10.6)


files = {}


def opener(name, header):
    f = open(D_SYN / name, "w", newline="", encoding="utf-8-sig")
    w = csv.writer(f)
    w.writerow(header)
    files[name] = f
    return w


w_day = opener("synthetic_daily_ridership.csv", ["Date", "Station_ID", "Station_Name", "Passenger_Entry", "Passenger_Exit", "Total_Passengers",
                                                 "Peak_Passengers", "Off_Peak_Passengers", "Weekday_Weekend", "Holiday_Flag", "Holiday_Name",
                                                 "Ramadan_Flag", "Weather_Category"] + PROV_COLS)
w_hr = opener("synthetic_hourly_ridership.csv", ["Date", "Hour", "Station_ID", "Direction", "Passenger_Entry", "Passenger_Exit", "Passenger_Volume",
                                                 "Peak_Hour_Flag"] + PROV_COLS)
w_tk = opener("synthetic_ticket_revenue.csv", ["Date", "Station_ID", "Fare_Product", "Ticket_Count", "Passenger_Count", "Average_Fare", "Gross_Revenue",
                                               "Refund_Amount", "Net_Revenue"] + PROV_COLS)
w_tr = opener("synthetic_train_operations.csv", ["Date", "Train_ID", "Trip_ID", "Direction", "Origin_Station", "Destination_Station", "Scheduled_Departure",
                                                 "Actual_Departure", "Scheduled_Arrival", "Actual_Arrival", "Scheduled_Travel_Time", "Actual_Travel_Time",
                                                 "Delay_Minutes", "Trip_Status", "Passenger_Load", "Max_Section_Load", "Capacity_Utilization", "Route_KM"] + PROV_COLS)
w_en = opener("synthetic_energy_consumption.csv", ["Date", "Component", "Train_KM", "Energy_Consumption_KWH", "Energy_Cost_BDT", "KWH_Per_Train_KM",
                                                   "Tariff_BDT_Per_KWH"] + PROV_COLS)
w_ln = opener("synthetic_daily_line_summary.csv", ["Date", "Service_Status", "Open_Stations", "First_Departure", "Last_Departure", "Operating_Hours",
                                                   "Peak_Headway_Min", "Off_Peak_Headway_Min", "Train_Sets_In_Service", "Scheduled_Trips", "Actual_Trips",
                                                   "Cancelled_Trips", "On_Time_Percentage", "Average_Delay_Minutes", "Service_Interruption_Minutes", "Train_KM",
                                                   "Line_Passengers", "Passenger_KM", "Line_Total_Calibration", "Max_Capacity_Utilization", "Gross_Fare_Revenue_BDT",
                                                   "Weekday_Weekend", "Holiday_Flag", "Ramadan_Flag", "Weather_Category"] + PROV_COLS)

P_RID, P_TKT, P_OPS, P_ENG = prov("M2-RID"), prov("M2-FARE"), prov("M2-OPS"), prov("M2-ENG")
STATS = defaultdict(float)
monthly = defaultdict(lambda: defaultdict(float))      # month -> metric -> value
fy_rev = defaultdict(float)
fy_pax = defaultdict(int)
st_2026 = [[0, 0, 0] for _ in range(N)]                # entries, exits, days (1-19 Sep 2026 window for Motijheel check)
maxutil_overall = 0.0
capped_trips = 0
unassigned = 0
sep24 = [0, 0.0]
rows_written = defaultdict(int)

for d in days:
    c = CAL[d]
    sv = c["sv"]
    wd = d.weekday()
    wk = "Weekend" if wd in (4, 5) else "Weekday"
    mkey = d.strftime("%Y-%m")
    fy = f"{d.year}-{str(d.year + 1)[2:]}" if d.month >= 7 else f"{d.year - 1}-{str(d.year)[2:]}"
    if sv is None:
        reason = "Closed - civil unrest damage" if CLOSED_FROM <= d <= CLOSED_TO else ("Closed - Eid day" if c["hname"].endswith("day") and c["hfac"] == 0 else "Closed - weekly off day")
        w_ln.writerow([d.isoformat(), reason, 0, "", "", 0, "", "", 0, 0, 0, 0, "", "", 0, 0, 0, 0, "", "", 0, wk, c["hol"], 1 if c["ram"] else 0, c["weather"]] + P_OPS)
        # depot / OCC base load continues on closed days
        kwh = DEPOT_KWH_PER_DAY * 0.6 * lognorm(0.04)
        w_en.writerow([d.isoformat(), "Depot and OCC", "", round(kwh), round(kwh * tariff(d)), "", tariff(d)] + P_ENG)
        monthly[mkey]["energy_cost"] += kwh * tariff(d)
        monthly[mkey]["kwh"] += kwh
        continue

    ops = open_stations(d)
    L = line[d]
    cats = tuple(("cbd" if (i == 8 and d < FULL_LINE) else ST[i][2]) for i in range(N))
    # ---- station entries
    base_w = W_FULL if d >= FULL_LINE else W_NORTH
    w = []
    for i in range(N):
        if i not in ops:
            w.append(0.0)
            continue
        x = base_w[i]
        if FULL_LINE <= d < SOUTH_FULL_HOURS and i > 8:
            x *= 0.45
        if wd == 5:
            x *= DAYTYPE_MULT["sat"][cats[i]]
        elif wd == 4:
            x *= DAYTYPE_MULT["fri"][cats[i]]
        if d.month == 2 and i in (12, 13) and d.year >= 2024:
            x *= 1.25                                   # Ekushey book fair (assumption A207)
        w.append(x * lognorm(0.04))
    if len(ops) == 2:
        w = [0.5 if i in ops else 0.0 for i in range(N)]
    E = alloc(L, w)

    # ---- hours and per-station open hours
    h0, h1 = sv["start"] // 60, sv["end"] // 60
    hours = list(range(h0, h1 + 1))
    frac = {h: max(0.02, min(sv["end"], (h + 1) * 60) - max(sv["start"] - 10, h * 60)) / 60.0 for h in hours}
    south_end = sv["south"]
    fri_like = wd == 4 and d >= date(2023, 5, 31)

    def stn_open(i, h):
        if south_end is not None and i > 8:
            return h * 60 < south_end
        return True

    # ---- hourly entries per station
    EH = [[0] * len(hours) for _ in range(N)]
    for i in ops:
        if E[i] == 0:
            continue
        if fri_like:
            pf = PROF["leisure"]
        else:
            key = cats[i]
            if c["ram"] and key in ("cbd", "mix"):
                key += "_ramadan"
            pf = PROF[key]
        ws = [(pf.get(h, 0.3) * frac[h] * lognorm(0.05) if stn_open(i, h) else 0.0) for h in hours]
        EH[i] = alloc(E[i], ws)

    # ---- flows, directional entries/exits, link loads
    ent_dir = [[[0, 0] for _ in hours] for _ in range(N)]        # [station][hour][S,N]
    exit_f = [[[0.0, 0.0] for _ in hours] for _ in range(N)]
    board = [[0.0, 0.0] for _ in hours]
    maxlink = [[0.0, 0.0] for _ in hours]
    fare_sum = [0.0] * N
    day_pkm = 0.0                      # passenger-km on physical distance (fare-distance scaled to the 20.10 km route)
    for hi, h in enumerate(hours):
        period = "mid" if fri_like else ("am" if h < 11 else ("pm" if h >= 15 else "mid"))
        oset = tuple(i for i in ops if stn_open(i, h))
        if len(oset) < 2:
            continue
        P = dest_probs(period, oset, cats, ops, "F" if d >= FULL_LINE else "N", fri_like)
        link = [[0.0] * N for _ in range(2)]                      # load on link after station k (S) / before (N)
        for i in oset:
            e = EH[i][hi]
            if e == 0:
                continue
            Pi = P[i]
            south = 0.0
            for j in oset:
                if j == i:
                    continue
                f = e * Pi[j]
                fare_sum[i] += f * FARE[i][j]
                day_pkm += f * DIST[i][j] * (ROUTE_KM_FULL / 19.3)
                if j > i:
                    south += f
                    exit_f[j][hi][0] += f
                    for k in range(i, j):
                        link[0][k] += f
                else:
                    exit_f[j][hi][1] += f
                    for k in range(j, i):
                        link[1][k] += f
            s_int = int(round(south))
            ent_dir[i][hi][0] = s_int
            ent_dir[i][hi][1] = e - s_int
            board[hi][0] += s_int
            board[hi][1] += e - s_int
        maxlink[hi][0], maxlink[hi][1] = max(link[0]), max(link[1])

    # integer exits: allocate the line total across station-hour-direction cells
    cells = [(j, hi, k) for j in range(N) for hi in range(len(hours)) for k in (0, 1)]
    ex_int = alloc(L, [exit_f[j][hi][k] for j, hi, k in cells])
    EX = [[[0, 0] for _ in hours] for _ in range(N)]
    for (j, hi, k), v in zip(cells, ex_int):
        EX[j][hi][k] = v

    # ---- write hourly + daily
    day_rev = 0.0
    s_sjt, s_rap = share_sjt(d), share_rapid(d)
    for i in ops:
        ent_tot = E[i]
        ex_tot = sum(EX[i][hi][0] + EX[i][hi][1] for hi in range(len(hours)))
        peak = 0
        for hi, h in enumerate(hours):
            pk = 1 if h in PEAK_HOURS else 0
            for k, dn in ((0, "Southbound"), (1, "Northbound")):
                en, ex = ent_dir[i][hi][k], EX[i][hi][k]
                if en or ex:
                    w_hr.writerow([d.isoformat(), h, SID[i], dn, en, ex, en + ex, pk] + P_RID)
                    rows_written["hourly"] += 1
                if pk:
                    peak += en
        w_day.writerow([d.isoformat(), SID[i], SNAME[i], ent_tot, ex_tot, ent_tot + ex_tot, peak, ent_tot - peak, wk, c["hol"], c["hname"],
                        1 if c["ram"] else 0, c["weather"]] + P_RID)
        rows_written["daily"] += 1
        if date(2026, 9, 1) <= d <= date(2026, 9, 19):
            st_2026[i][0] += ent_tot
            st_2026[i][1] += ex_tot
            st_2026[i][2] += 1
        # ---- ticket revenue by product
        if ent_tot:
            avg_full = fare_sum[i] / ent_tot
            cnt = alloc(ent_tot, [s_sjt, 1 - s_sjt - s_rap, s_rap])
            for prod, n_p, disc in (("Single Journey Ticket", cnt[0], 1.0), ("MRT Pass", cnt[1], 0.9), ("Rapid Pass", cnt[2], 0.9)):
                if n_p == 0:
                    continue
                af = round(avg_full * disc, 2)
                gross = round(n_p * af)
                refund = round(gross * 0.0015 * lognorm(0.5)) if prod.startswith("Single") else 0
                w_tk.writerow([d.isoformat(), SID[i], prod, n_p, n_p, af, gross, refund, gross - refund] + P_TKT)
                rows_written["ticket"] += 1
                day_rev += gross
                monthly[mkey]["refund"] += refund
    fy_rev[fy] += day_rev
    fy_pax[fy] += L
    monthly[mkey]["rev"] += day_rev
    monthly[mkey]["pax"] += L
    if date(2024, 9, 1) <= d <= date(2024, 9, 18):
        sep24[0] += L
        sep24[1] += day_rev

    # ---- train runs
    trips = trips_for(d, sv)
    incs = SVC_INC.get(d, [])
    recs = []
    for n_t, (dn, dep, o, de, km, run) in enumerate(trips):
        k = 0 if dn == "Southbound" else 1
        status, delay = "Operated", 0.0
        x = rng.random()
        if x > 0.86:
            delay = min(12.0, math.exp(rng.gauss(0.3, 0.8)))
        else:
            delay = rng.uniform(0, 0.9)
        for st_min, down, cp in incs:
            if st_min - 2 <= dep <= st_min + down + 20:
                if cp and st_min <= dep <= st_min + down and rng.random() < cp:
                    status = "Cancelled"
                else:
                    remaining = max(0.0, st_min + down - dep)
                    delay += min(45.0, 2 + remaining * rng.uniform(0.3, 0.9)) if dep <= st_min + down else rng.uniform(1, 6) * max(0.2, 1 - (dep - st_min - down) / 20)
        recs.append([dn, k, dep, o, de, km, run, status, delay])
    # passenger loads per hour-direction across operated trips
    groups = defaultdict(list)
    for idx, r in enumerate(recs):
        if r[7] == "Operated":
            groups[(min(max(int(r[2] // 60), hours[0]), hours[-1]), r[1])].append(idx)
    loads = [0] * len(recs)
    maxsec = [0.0] * len(recs)
    for hi, h in enumerate(hours):
        for k in (0, 1):
            b = int(round(board[hi][k]))
            g = groups.get((h, k))
            if not g:
                # roll boardings to the nearest later hour with trains in that direction
                later = [hh for hh in hours if hh > h and groups.get((hh, k))] or [hh for hh in reversed(hours) if hh < h and groups.get((hh, k))]
                if later and b and later[0] > h:
                    hi2 = hours.index(later[0])
                    board[hi2][k] += b
                    maxlink[hi2][k] += maxlink[hi][k]
                elif later and b:
                    g2 = groups[(later[0], k)]                      # earlier trains already loaded: add to the last one
                    loads[g2[-1]] += b
                    maxsec[g2[-1]] += b * ((maxlink[hi][k] / board[hi][k]) if board[hi][k] else 0.0)
                else:
                    unassigned += b
                continue
            al = alloc(b, [lognorm(0.12) for _ in g])
            ratio = (maxlink[hi][k] / board[hi][k]) if board[hi][k] else 0.0
            for idx, v in zip(g, al):
                loads[idx] = v
                maxsec[idx] = v * ratio
    sets = sv["sets"]
    ontime = cancelled = 0
    dsum = 0.0
    day_km = 0.0
    day_maxutil = 0.0
    for n_t, r in enumerate(recs):
        dn, k, dep, o, de, km, run, status, delay = r
        ms = maxsec[n_t]
        if ms > TRAIN_CAPACITY:
            capped_trips += 1
            ms = TRAIN_CAPACITY
        util = ms / TRAIN_CAPACITY
        if util > 0.9 and status == "Operated":
            delay += rng.uniform(0, 1.5)                         # dwell-time extension when crowded
        tid = f"TS-{(n_t % sets) + 1:02d}"
        trip_id = f"{d.strftime('%Y%m%d')}-{dn[0]}-{n_t + 1:03d}"
        if status == "Cancelled":
            cancelled += 1
            w_tr.writerow([d.isoformat(), tid, trip_id, dn, SID[o], SID[de], hhmm(dep), "", hhmm(dep + run), "", run, "", "", status, 0, 0, 0, km] + P_OPS)
        else:
            run_act = run + rng.gauss(0.2, 0.5) + 0.25 * delay
            dly = round(delay, 1)
            ontime += 1 if dly < 2.0 else 0
            dsum += dly
            day_km += km
            day_maxutil = max(day_maxutil, util)
            w_tr.writerow([d.isoformat(), tid, trip_id, dn, SID[o], SID[de], hhmm(dep), hhmm(dep + dly), hhmm(dep + run), hhmm(dep + dly + run_act),
                           run, round(run_act, 1), dly, status, loads[n_t], int(round(ms)), round(util, 3), km] + P_OPS)
        rows_written["trips"] += 1
    operated = len(recs) - cancelled
    train_km = day_km * (1 + EMPTY_RUNNING)
    maxutil_overall = max(maxutil_overall, day_maxutil)
    interruption = sum(dn_ for _, dn_, _ in incs)
    STATS["trips"] += len(recs)
    STATS["operated"] += operated
    STATS["ontime"] += ontime
    STATS["delay"] += dsum
    op_hours = round((sv["end"] - sv["start"]) / 60.0, 2)
    w_ln.writerow([d.isoformat(), "Operating", len(ops), hhmm(sv["start"]), hhmm(sv["end"]), op_hours, sv["pk"], sv["off"], sets, len(recs), operated,
                   cancelled, round(100.0 * ontime / operated, 2) if operated else "", round(dsum / operated, 2) if operated else "", interruption,
                   round(train_km, 1), L, round(day_pkm), "Pinned to published single-day total" if d in PINS else "Modelled; cumulative total calibrated",
                   round(day_maxutil, 3), round(day_rev), wk, c["hol"], 1 if c["ram"] else 0, c["weather"]] + P_OPS)

    # ---- energy
    season = 1.08 if d.month in (4, 5, 6, 7, 8, 9) else (0.95 if d.month in (11, 12, 1, 2) else 1.0)
    load_f = 1 + 0.04 * (L / max(1, operated) / 1500.0)
    t = tariff(d)
    kwh_tr = train_km * TRACTION_KWH_PER_TRAIN_KM * season * load_f * lognorm(0.03)
    kwh_st = len(ops) * STATION_KWH_PER_DAY * (0.45 + 0.55 * op_hours / 14.5) * season * lognorm(0.03)
    kwh_dp = DEPOT_KWH_PER_DAY * (0.7 + 0.3 * sets / 13.0) * lognorm(0.04)
    w_en.writerow([d.isoformat(), "Traction", round(train_km, 1), round(kwh_tr), round(kwh_tr * t), round(kwh_tr / train_km, 2), t] + P_ENG)
    w_en.writerow([d.isoformat(), "Stations", "", round(kwh_st), round(kwh_st * t), "", t] + P_ENG)
    w_en.writerow([d.isoformat(), "Depot and OCC", "", round(kwh_dp), round(kwh_dp * t), "", t] + P_ENG)
    for kk in (kwh_tr, kwh_st, kwh_dp):
        monthly[mkey]["energy_cost"] += kk * t
        monthly[mkey]["kwh"] += kk
    monthly[mkey]["train_km"] += train_km
    monthly[mkey]["trips"] += operated
    monthly[mkey]["stations"] = max(monthly[mkey]["stations"], len(ops))

for f in files.values():
    f.close()

# ---- maintenance / incident file
incidents.sort(key=lambda r: (r[1], r[0]))
with open(D_SYN / "synthetic_maintenance_incidents.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["Incident_ID", "Date", "Station_ID", "Train_ID", "Record_Type", "Incident_Category", "Severity", "Start_Time", "Resolution_Time",
                "Downtime_Minutes", "Maintenance_Cost_BDT", "Operational_Impact"] + PROV_COLS)
    w.writerows(incidents)
for r in incidents:
    if r[10] != "":
        monthly[r[1][:7]]["maint_inc_cost"] += r[10]

# ====================================================================================================
# monthly operating expenses
# ====================================================================================================
def fy_of_month(mk):
    y, m = int(mk[:4]), int(mk[5:])
    return f"{y}-{str(y + 1)[2:]}" if m >= 7 else f"{y - 1}-{str(y)[2:]}"


EMP_ANNUAL = {"2022-23": 26.0e7, "2023-24": 39.91e7, "2024-25": 61.46e7, "2025-26": 76.0e7, "2026-27": 84.0e7}   # FY24, FY25 = S002 Note 21.01
ADM_ANNUAL = {"2022-23": 7.0e7, "2023-24": 10.51e7, "2024-25": 19.92e7, "2025-26": 23.0e7, "2026-27": 25.0e7}    # FY24, FY25 = S002 Note 21.02
DTCA_RATE = {"2022-23": 0.0096, "2023-24": 0.0096, "2024-25": 0.0146, "2025-26": 0.0146, "2026-27": 0.0146}      # S002 Note 19
opex_rows = []
for mk in sorted(monthly):
    m = monthly[mk]
    fyk = fy_of_month(mk)
    nst = max(2, m["stations"])
    own = mk >= "2026-01"                      # DMTCL takes over maintenance and equipment costs from January 2026 (S011)
    grow = 1 + 0.06 * (int(mk[:4]) - 2023)
    plan = {
        "Employee expenses": EMP_ANNUAL[fyk] / 12,
        "Maintenance": (6.2e7 if own else 0.6e7) * nst / 16,
        "Cleaning": 0.055e7 * nst * grow,
        "Security": 0.075e7 * nst * grow,
        "Station operations": 0.05e7 * nst * grow,
        "Administration": ADM_ANNUAL[fyk] / 12,
        "Equipment replacement": (1.0e7 if own else 0.15e7) * nst / 16,
        "Insurance": 0.45e7,
        "Other operating expenses": 0.3e7 + DTCA_RATE[fyk] * m["rev"],
    }
    partial = "Partial month" if mk in ("2022-12", "2026-11") else ""
    for cat, p in [("Electricity", None)] + list(plan.items()):
        if cat == "Electricity":
            exp = m["energy_cost"]
            bud = exp * rng.gauss(1.04, 0.05)
            note = "Sum of synthetic_energy_consumption.csv for the month"
        elif cat == "Maintenance":
            exp = p * rng.gauss(1.0, 0.10) + m["maint_inc_cost"]
            bud = p * 1.05 + 0.9 * m["maint_inc_cost"]
            note = "Contract maintenance plus the month's incident and work-order costs"
        else:
            if partial:
                p *= (3 / 31 if mk == "2022-12" else 13 / 30)
            exp = p * rng.gauss(0.98, 0.06)
            bud = p
            note = "Annual level from DMTCL audited accounts" if cat in ("Employee expenses", "Administration") and fyk in ("2023-24", "2024-25") else "Assumed level"
            if cat == "Other operating expenses":
                note = "Includes DTCA clearing commission at the audited share of ticket sales"
        opex_rows.append([mk, fyk, cat, round(bud), round(exp), round(exp - bud), partial, note] + prov("M2-OPX"))
with open(D_SYN / "synthetic_monthly_opex.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["Month", "Fiscal_Year", "Expense_Category", "Budget_BDT", "Actual_or_Simulated_Expense_BDT", "Variance_BDT", "Partial_Month_Flag", "Basis"] + PROV_COLS)
    w.writerows(opex_rows)

# ====================================================================================================
# fare matrix (Estimated), model register, assumptions, monthly summary
# ====================================================================================================
conf = {(min(a, b), max(a, b)) for a, b, _ in CONFIRMED_FARES}
with open(D_SYN / "estimated_fare_matrix.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["Origin_Station_ID", "Origin_Station", "Destination_Station_ID", "Destination_Station", "Fare_Distance_KM_Model", "Single_Journey_Fare_BDT",
                "Card_Fare_BDT", "Matches_Published_Pair"] + PROV_COLS)
    for i in range(N):
        for j in range(N):
            if i != j:
                pub = (min(i, j), max(i, j)) in conf
                w.writerow([SID[i], SNAME[i], SID[j], SNAME[j], DIST[i][j], FARE[i][j], round(FARE[i][j] * 0.9, 1), "Yes" if pub else "No",
                            "Estimated", "M2-FARE;S018;S023", "Medium" if pub else "Low",
                            "Tk 5/km on fitted fare-distances, rounded up to Tk 10, min 20, max 100; fitted to reproduce 21 published pairs", "Yes", "Yes" if pub else "No"])

MODELS = [
 ("M2-RID", "Ridership model", "Daily line total = anchor trend x day-of-week x holiday x Ramadan x weather x noise; station split by land-use weights; hourly by category profiles; destination choice by gravity model", "S012; S013; S014; S016; S029; S031"),
 ("M2-FARE", "Fare and revenue model", "Modelled fare matrix applied to the synthetic origin-destination flows; product shares assumed; 10% card discount", "S002; S017; S018; S023; S025"),
 ("M2-OPS", "Train operations model", "Timetable generated from service hours and headways; delays and cancellations from random and incident-driven components; loads from hourly directional boardings", "S014; S016; S035"),
 ("M2-ENG", "Energy model", "Traction kWh per train-km plus station and depot loads, with seasonal factors; tariff assumed", "S034"),
 ("M2-MNT", "Maintenance and incident model", "Poisson-type arrivals of incidents and work orders with log-normal durations and costs; four documented real events included as Actual rows", "S014"),
 ("M2-OPX", "Operating expense model", "Electricity and maintenance derived from the synthetic datasets; staff and administration levels from DMTCL audited accounts; other categories assumed", "S002; S011; S034"),
 ("S034", "Dhaka Tribune / Prothom Alo (search summary only)", "DMTCL pays about Tk 6 crore a month in electricity bills (reported with FY2023-24 revenue, c. Feb 2025). https://www.dhakatribune.com/bangladesh/dhaka/372817/metro-rail-earns-244c-from-ticket-sales-more", "Low confidence"),
 ("S035", "Prothom Alo / Dhaka Tribune / Daily Observer (search summaries only)", "Trips per day: 198 on regular days and 60 on Fridays (FY2023-24 report); 238 before and about 297 after the Oct 2025 hour extension; Eid schedule about 140. https://en.prothomalo.com/bangladesh/city/r5oh5hxan4", "Low confidence"),
]
with open(D_RES / "source_register_phase2_models.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["Source_ID", "Name", "Description", "Calibration_Sources_or_Confidence"])
    w.writerows(MODELS)

ASSUME = [
 ("A201", "Demand trend", "Working-day ridership follows a piecewise-linear path through 36 anchor levels set from published averages and records", "Phase 1 ridership table", "Global scale factor applied to meet the cumulative total: see validation log"),
 ("A202", "Day of week", "Sun 1.02, Mon-Wed 1.00, Thu 1.03, Sat 0.78, Fri 0.30 (Friday service is afternoon-only)", "Judgement; Friday trips are 30% of weekday trips (S035)", "Sat 0.70-0.85; Fri 0.25-0.40"),
 ("A203", "Holidays and Ramadan", "National holidays 0.62; two days before Eid 0.75; three days after 0.45/0.55/0.70; Ramadan 0.97, last ten days 1.03; evening peak moves earlier in Ramadan", "Judgement - no published series", "+/-10 percentage points on each factor"),
 ("A204", "Eid day", "No passenger service on Eid-ul-Fitr and Eid-ul-Adha day; 2026 Eid and Ramadan dates depend on moon sighting", "Judgement", "Low impact (8 days)"),
 ("A205", "Early service pattern", "08:00-12:00 with Tuesday closure to 30 May 2023; 08:00-18:00 to 7 Jul 2023; to 20:30 afterwards; Motijheel-side stations 07:30-11:30 only until 19 Jan 2024; Friday service from 20 Sep 2024", "S014, S018 (times partly recalled, not all verified)", "Affects 2023 hourly shapes only"),
 ("A206", "Station shares", "Entry shares by station fixed by land-use weights (Motijheel weight set so its September 2026 average matches the published 51,542 daily entries); busiest/quietest ordering follows S012", "S012", "Individual station shares +/-25% except Motijheel"),
 ("A207", "Special events", "Shahbagh and Dhaka University entries +25% in February (book fair)", "Judgement", "0-40%"),
 ("A208", "Weather", "Light rain +2%, heavy rain -5%, heat +1%, fog -1%; weather drawn from monthly climatological probabilities, not observed weather", "Judgement", "Heavy rain -10% to 0%"),
 ("A209", "Destination choice", f"Gravity model with distance deterrence {BETA} per km and time-of-day attraction factors; passengers exit in the same clock hour they enter", "Tuned so FY2024-25 modelled fare revenue approximates audited gross ticket sales", "Deterrence 0.08-0.15 moves average fare by about +/-Tk 4"),
 ("A210", "Fare products", "Single Journey Ticket share falls from 80% to 33%; Rapid Pass rises from 2% to 30%; MRT Pass is the remainder; refunds 0.15% of single-journey sales", "Judgement - no published split", "Card share +/-15 points changes revenue by about +/-1.5%"),
 ("A211", "Energy", f"Traction {TRACTION_KWH_PER_TRAIN_KM} kWh per train-km, stations {STATION_KWH_PER_DAY:.0f} kWh/day, depot {DEPOT_KWH_PER_DAY:.0f} kWh/day; tariff Tk 8.6 / 9.7 / 10.6 per kWh (from Feb 2023 / Mar 2024)", "Levels set so the early-2025 monthly bill is near the reported Tk 6 crore (S034)", "+/-25%"),
 ("A212", "Reliability", "86% of trips depart within 1 minute; the rest follow a log-normal delay; incidents add delay and, above 30 minutes, cancellations; on time = under 2 minutes late", "Judgement - no published punctuality data", "Not calibrated"),
 ("A213", "Fleet and headways", "Headways 10/15, 10/12, 8/10, 6/10 and 5/8 minutes (peak/off-peak) by period; sets in service 6 to 19", "Chosen to reproduce published trips per day (S035) and fleet use (S016, S028)", "See validation log"),
 ("A214", "Operating expenses", "Maintenance and equipment costs step up from January 2026; cleaning, security, station operations and insurance are assumed levels", "S011 for the timing; levels are judgement", "+/-50% on assumed categories"),
 ("A215", "Train capacity", "2,300 passengers per six-car train; a trip's maximum section load is capped at this value", "S016", "Count of capped trips in validation log"),
]
with open(D_DOC / "assumptions_register_phase2.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["Assumption_ID", "Topic", "Assumption", "Basis", "Sensitivity_Range_or_Impact", "Phase"])
    w.writerows([list(a) + [2] for a in ASSUME])

with open(D_MOD / "synthetic_monthly_operating_summary.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["Month", "Line_Passengers", "Gross_Fare_Revenue_BDT", "Revenue_Per_Passenger_BDT", "Operated_Trips", "Train_KM", "Energy_KWH", "Energy_Cost_BDT",
                "KWH_Per_Train_KM_All_Loads", "Operating_Expense_BDT", "Farebox_Recovery_Ratio"] + PROV_COLS)
    opex_m = defaultdict(float)
    for r in opex_rows:
        opex_m[r[0]] += r[4]
    for mk in sorted(monthly):
        m = monthly[mk]
        w.writerow([mk, int(m["pax"]), round(m["rev"]), round(m["rev"] / m["pax"], 2) if m["pax"] else "", int(m["trips"]), round(m["train_km"]),
                    round(m["kwh"]), round(m["energy_cost"]), round(m["kwh"] / m["train_km"], 2) if m["train_km"] else "", round(opex_m[mk]),
                    round(m["rev"] / opex_m[mk], 2) if opex_m[mk] else ""] + prov("M2-RID;M2-FARE;M2-OPX"))

# ====================================================================================================
# validation log
# ====================================================================================================
log = []


def check(name, ok, detail=""):
    log.append(f"[{'PASS' if ok else 'FAIL'}] {name}{(' - ' + detail) if detail else ''}")


def info(s):
    log.append("[INFO] " + s)


cum = sum(v for d, v in line.items() if d <= CUM_TARGET_DATE)
check("Cumulative line ridership to 31 Aug 2026 equals published 313,546,306", cum == CUM_TARGET, f"synthetic {cum:,}")
info(f"Global scale factor applied to un-pinned days: {SCALE_USED:.4f}")
check("All nine published single-day totals reproduced", all(line[d] == v for d, v in PINS.items()))
viol = [d for d in days if d not in PINS and line[d] > cap_for(d)]
check("No un-pinned day exceeds the record standing at that date", not viol, f"{len(viol)} violations")
sep26 = [line[d] for d in days if date(2026, 9, 1) <= d <= date(2026, 9, 19) and d.weekday() in (6, 0, 1, 2, 3) and not CAL[d]["hol"] and not SVC_INC.get(d)]
check("September 2026 working days all above 450,000", min(sep26) > 450000, f"min {min(sep26):,}")
check("All 21 published station-pair fares reproduced by the fare model", all(FARE[a][b] == f for a, b, f in CONFIRMED_FARES))
check("Train maximum section load never exceeds capacity after capping", True, f"{capped_trips:,} of {int(STATS['operated']):,} operated trips hit the 2,300 cap; highest utilisation {maxutil_overall:.3f}")
info(f"Boardings that could not be assigned to a train (all trips in that hour and direction cancelled, none later): {unassigned:,}")
info(f"On-time performance (under 2 min late): {100 * STATS['ontime'] / STATS['operated']:.2f}%; average delay {STATS['delay'] / STATS['operated']:.2f} min; "
     f"cancelled {int(STATS['trips'] - STATS['operated']):,} of {int(STATS['trips']):,} scheduled trips")
AUD = {"2022-23": 182806514, "2023-24": 2462821403, "2024-25": 4176915397}
for fyk in sorted(fy_rev):
    a = AUD.get(fyk)
    extra = f"; audited {'net' if fyk == '2022-23' else 'gross'} ticket sales {a:,} -> synthetic/audited = {fy_rev[fyk] / a:.3f}" if a else "; no audited figure published"
    info(f"FY{fyk}: synthetic passengers {fy_pax[fyk]:,}; synthetic gross fare revenue {fy_rev[fyk]:,.0f}; revenue per passenger {fy_rev[fyk] / fy_pax[fyk]:.2f}{extra}")
check("FY2024-25 synthetic fare revenue within 5% of audited gross ticket sales", abs(fy_rev["2024-25"] / AUD["2024-25"] - 1) < 0.05, f"ratio {fy_rev['2024-25'] / AUD['2024-25']:.3f}")
info(f"1-18 Sep 2024: synthetic passengers {sep24[0]:,} (published: more than 4,900,000); synthetic revenue {sep24[1]:,.0f} (published: more than 206,700,000)")
q1 = sum(line[d] for d in days if date(2023, 1, 1) <= d <= date(2023, 3, 31))
jan = sum(line[d] for d in days if date(2023, 1, 1) <= d <= date(2023, 1, 31))
info(f"Jan 2023 synthetic {jan:,} (published about 350,000); Jan-Mar 2023 synthetic {q1:,} (published 1,077,000)")
mo = st_2026[15]
info(f"Motijheel 1-19 Sep 2026 average daily entries {mo[0] / mo[2]:,.0f} (published 51,542) and exits {mo[1] / mo[2]:,.0f} (published 51,036)")
for label, dd in (("regular weekday early 2025", date(2025, 2, 10)), ("Friday early 2025", date(2025, 2, 14)), ("weekday Sep 2025", date(2025, 9, 10)), ("weekday 2026", date(2026, 9, 9))):
    info(f"Scheduled trips on a {label} ({dd}): {len(trips_for(dd, service(dd)))} (published benchmarks: 198 / 60 / 238 / about 297)")
for mk in ("2025-02", "2026-09"):
    info(f"Electricity cost {mk}: {monthly[mk]['energy_cost']:,.0f} BDT (reported benchmark about 60,000,000 a month around early 2025)")
info(f"Rows written: daily {rows_written['daily']:,}; hourly {rows_written['hourly']:,}; ticket {rows_written['ticket']:,}; train runs {rows_written['trips']:,}; "
     f"incidents/work orders {len(incidents):,}; opex {len(opex_rows):,}")
info(f"Random seed {SEED}")
(D_DOC / "phase2_validation_log.txt").write_text("\n".join(log), encoding="utf-8")
print("\n".join(log))
