"""
Build the data file consumed by 06_Dashboard/index.html.

Reads the Phase 1-4 CSV outputs plus the OpenStreetMap route relation and the photo credits, and writes
  06_Dashboard/sample_data/dashboard_data.js     (window.MRT_DATA = {...}; loaded by a <script> tag so the page works from file://)
  06_Dashboard/sample_data/dashboard_data.json   (same content as JSON)
  06_Dashboard/sample_data/csv/                  (small CSV extracts for testing the upload control)

Every block carries its classification (Actual / Synthetic / Estimated / Forecast).
Standard library only.  Run:  python 05_Documentation/scripts/build_dashboard_data.py
"""
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D_ACT, D_SYN, D_MOD = ROOT / "02_Actual_Data", ROOT / "03_Synthetic_Data", ROOT / "04_Analytical_Models"
DASH = ROOT / "06_Dashboard"
OUT = DASH / "sample_data"
(OUT / "csv").mkdir(parents=True, exist_ok=True)


def read(p):
    with open(p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def hav(a, b):
    r = 6371000.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dl = math.radians(b[1] - a[1])
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


# ------------------------------------------------------------------ geography (OpenStreetMap relation 15060935)
NAMES = ["Uttara North", "Uttara Center", "Uttara South", "Pallabi", "Mirpur 11", "Mirpur 10", "Kazipara", "Shewrapara", "Agargaon", "Bijoy Sarani", "Farmgate",
         "Karwan Bazar", "Shahbagh", "Dhaka University", "Bangladesh Secretariat", "Motijheel"]
rel = json.load(open(OUT / "osm_relation_15060935_mrt_line6.json", encoding="utf-8"))
nodes = {e["id"]: e for e in rel["elements"] if e["type"] == "node"}
ways = {e["id"]: e["nodes"] for e in rel["elements"] if e["type"] == "way"}
stops = {}
for n in nodes.values():
    t = n.get("tags", {})
    nm = (t.get("name:en") or t.get("name") or "").replace("Bijoy Shoroni", "Bijoy Sarani")
    if nm in NAMES and (t.get("railway") or t.get("public_transport")):
        stops[nm] = n
assert len(stops) == 16, sorted(set(NAMES) - set(stops))
# chain the ways into one ordered node list
remaining = dict(ways)
wid, chain = next(iter(remaining.items()))
del remaining[wid]
chain = list(chain)
changed = True
while remaining and changed:
    changed = False
    for wid, nd in list(remaining.items()):
        if nd[0] == chain[-1]:
            chain += nd[1:]
        elif nd[-1] == chain[-1]:
            chain += nd[-2::-1]
        elif nd[-1] == chain[0]:
            chain = nd[:-1] + chain
        elif nd[0] == chain[0]:
            chain = nd[:0:-1] + chain
        else:
            continue
        del remaining[wid]
        changed = True
pts = [(nodes[i]["lat"], nodes[i]["lon"]) for i in chain]


def nearest(p):
    return min(range(len(pts)), key=lambda k: hav(pts[k], p))


i_un, i_mo = nearest((stops["Uttara North"]["lat"], stops["Uttara North"]["lon"])), nearest((stops["Motijheel"]["lat"], stops["Motijheel"]["lon"]))
route = pts[i_un:i_mo + 1] if i_un < i_mo else pts[i_mo:i_un + 1][::-1]
cum = [0.0]
for a, b in zip(route, route[1:]):
    cum.append(cum[-1] + hav(a, b))
GEO_NOTE = f"Track geometry and station stop positions from OpenStreetMap relation 15060935 (Dhaka Metro Rail Line 6), {len(route)} vertices, {cum[-1] / 1000:.2f} km between Uttara North and Motijheel stop positions. (c) OpenStreetMap contributors, ODbL."
if remaining:
    GEO_NOTE += f" {len(remaining)} way(s) of the relation not on the main chain were ignored."

CONTEXT = {  # descriptive context written for this dashboard from general knowledge of the areas - not a dataset
 "Uttara North": ("Diabari, Uttara Sector 18", "Residential (developing)", "Northern terminus beside the Diabari depot; RAJUK Uttara third-phase housing still filling in.", "Uttara Sector 18 apartment project; Diabari lakeside", "Private universities' permanent campuses in Uttara third phase", "Local clinics in Uttara sectors", "Local buses and human haulers to Uttara and Mirpur; rickshaws"),
 "Uttara Center": ("Uttara third phase, Sector 15/16", "Residential (developing)", "Planned as the centre of the Uttara third-phase township; RAJUK land earmarked for transit-oriented development nearby.", "Planned commercial centre (largely undeveloped)", "None close by", "None close by", "Rickshaws; limited bus service"),
 "Uttara South": ("Uttara third phase, Sector 15", "Residential (developing)", "Lowest-demand station on the line; surrounded by partly built residential plots.", "Neighbourhood shops", "None close by", "None close by", "Rickshaws; limited bus service"),
 "Pallabi": ("Pallabi, Mirpur 12", "Residential", "Dense residential Mirpur; serves Mirpur 12, Mirpur DOHS and the cantonment edge.", "Mirpur 12 bus stand markets", "Bangladesh University of Professionals (Mirpur Cantonment)", "Local hospitals and clinics", "City buses on Begum Rokeya Avenue; human haulers; rickshaws"),
 "Mirpur 11": ("Mirpur Section 11", "Residential", "Mixed residential and neighbourhood retail along Begum Rokeya Avenue.", "Mirpur 11 kitchen market; Purobi area shops", "Local schools and colleges", "Local clinics", "City buses; rickshaws"),
 "Mirpur 10": ("Mirpur 10 roundabout", "Residential / commercial hub", "Mirpur's main junction and one of the busiest stations; damaged in July 2024 and reopened 15 October 2024.", "Mirpur 10 shopping centres; Benarasi Palli", "Mirpur schools and colleges", "Private hospitals around the roundabout", "Major bus interchange (Mirpur 1, 2, 13, 14); Sher-e-Bangla National Cricket Stadium nearby"),
 "Kazipara": ("Kazipara, Mirpur", "Residential", "Residential corridor station; closed after the July 2024 unrest and reopened 20 September 2024.", "Furniture and household shops on Begum Rokeya Avenue", "Local schools", "Local clinics", "City buses; rickshaws"),
 "Shewrapara": ("Shewrapara, Mirpur", "Residential", "Dense middle-income residential area.", "Neighbourhood markets", "Local schools", "Local clinics", "City buses; rickshaws"),
 "Agargaon": ("Agargaon, Sher-e-Bangla Nagar", "Government / institutional", "Government office district; terminus of the first section opened in December 2022.", "IDB Bhaban computer market; office district", "Sher-e-Bangla Agricultural University", "National Institute of Neurosciences; Shaheed Suhrawardy Medical College Hospital; other national institutes", "Buses on Mirpur Road and Rokeya Avenue; passport and election commission offices nearby"),
 "Bijoy Sarani": ("Bijoy Sarani, Tejgaon", "Institutional", "Between the parliament complex and the old Tejgaon airport; one of the quieter stations.", "Limited", "None close by", "None close by", "Buses on Bijoy Sarani; Novo Theatre and military museum nearby"),
 "Farmgate": ("Farmgate, Tejgaon", "Commercial / transport hub", "One of Dhaka's busiest road interchanges, with coaching centres, colleges and offices.", "Farmgate markets; Green Road and Indira Road commerce", "Tejgaon College; Government Science College; Holy Cross College", "Hospitals and clinics on Green Road", "Major bus interchange; Dhaka Elevated Expressway ramp; Khamarbari"),
 "Karwan Bazar": ("Karwan Bazar", "Business district", "Wholesale market and corporate office district with media houses and hotels.", "Karwan Bazar wholesale market; corporate towers; Bashundhara City mall at Panthapath", "None close by", "Private hospitals at Panthapath", "Buses on Kazi Nazrul Islam Avenue; Tejgaon railway station about 1 km"),
 "Shahbagh": ("Shahbagh", "Institutional / mixed", "Hospital and cultural district at the edge of the university area.", "Aziz Super Market; flower market", "Dhaka University (north side); Faculty of Fine Arts", "Bangladesh Medical University (formerly BSMMU); BIRDEM General Hospital", "Buses at Shahbagh intersection; National Museum and Public Library nearby"),
 "Dhaka University": ("TSC, Dhaka University campus", "Educational", "Serves the main university campus; demand follows the academic calendar and the February book fair.", "Limited (campus)", "University of Dhaka; BUET within about 1 km", "Dhaka Medical College Hospital about 1 km", "Rickshaws; campus buses; Suhrawardy Udyan and Bangla Academy adjacent"),
 "Bangladesh Secretariat": ("Topkhana Road / Paltan", "Government / business district", "Government headquarters and press district.", "Paltan and Baitul Mukarram markets", "None close by", "Local clinics", "Buses at Paltan and Press Club; Supreme Court nearby"),
 "Motijheel": ("Motijheel commercial area", "Central business district", "Dhaka's traditional financial centre and the busiest station; southern terminus until the Kamalapur extension opens.", "Bank and corporate headquarters; Bangladesh Bank", "Notre Dame College", "Local clinics", "City buses; Kamalapur railway station about 1 km (extension under construction)"),
}
credits = json.load(open(DASH / "assets" / "stations" / "photo_credits.json", encoding="utf-8"))
CRED = {c["station"]: c for c in credits}
sref = read(D_ACT / "station_reference.csv")
stations = []
for k, nm in enumerate(NAMES):
    s = stops[nm]
    vi = min(range(len(route)), key=lambda q: hav(route[q], (s["lat"], s["lon"])))
    c = CONTEXT[nm]
    ph = CRED[nm]
    stations.append(dict(id=sref[k]["Station_ID"], seq=k + 1, name=nm, lat=round(s["lat"], 6), lng=round(s["lon"], 6), routeIndex=vi, chainageM=round(cum[vi]),
                         opening=sref[k]["Opening_Date"], status="Operational", area=c[0], character=c[1], summary=c[2], commercial=c[3], education=c[4], health=c[5], transport=c[6],
                         photo=dict(file="assets/stations/" + ph["file"], authentic=True, title=ph["title"], author=ph["author"], license=ph["license"], page=ph["page"])))

# ------------------------------------------------------------------ operations (synthetic)
line = read(D_SYN / "synthetic_daily_line_summary.csv")
dates = [r["Date"] for r in line]
DI = {d: k for k, d in enumerate(dates)}
ND = len(dates)
E, X, R = [0] * (ND * 16), [0] * (ND * 16), [0] * (ND * 16)
SI = {s["id"]: k for k, s in enumerate(stations)}
for r in read(D_SYN / "synthetic_daily_ridership.csv"):
    q = DI[r["Date"]] * 16 + SI[r["Station_ID"]]
    E[q], X[q] = int(r["Passenger_Entry"]), int(r["Passenger_Exit"])
for r in read(D_SYN / "synthetic_ticket_revenue.csv"):
    R[DI[r["Date"]] * 16 + SI[r["Station_ID"]]] += int(r["Gross_Revenue"])

HOURS = list(range(6, 23))
H = [0] * (ND * len(HOURS))                    # line entries by date x hour
shape_e = defaultdict(lambda: [0] * len(HOURS))  # (daytype, station) -> entries by hour over the last 365 days
shape_x = defaultdict(lambda: [0] * len(HOURS))
flow = defaultdict(lambda: [0.0] * 4)            # (month, station) -> entS, entN, exS, exN on working days
wdays = defaultdict(set)
import datetime as _dt
last = _dt.date.fromisoformat(dates[-1])


def daytype(d):
    w = _dt.date.fromisoformat(d).weekday()
    return "fri" if w == 4 else ("sat" if w == 5 else "wk")


with open(D_SYN / "synthetic_hourly_ridership.csv", encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        d, h, s = r["Date"], int(r["Hour"]), SI[r["Station_ID"]]
        e, x = int(r["Passenger_Entry"]), int(r["Passenger_Exit"])
        if 6 <= h <= 22:
            H[DI[d] * len(HOURS) + h - 6] += e
        dt = daytype(d)
        if (last - _dt.date.fromisoformat(d)).days < 365 and 6 <= h <= 22:
            shape_e[(dt, s)][h - 6] += e
            shape_x[(dt, s)][h - 6] += x
        if dt == "wk":
            m = d[:7]
            wdays[m].add(d)
            fl = flow[(m, s)]
            k0 = 0 if r["Direction"] == "Southbound" else 1
            fl[k0] += e
            fl[2 + k0] += x


def norm(v):
    t = sum(v)
    return [round(a / t, 4) if t else 0 for a in v]


shape = {dt: dict(entry=[norm(shape_e[(dt, s)]) for s in range(16)], exit=[norm(shape_x[(dt, s)]) for s in range(16)]) for dt in ("wk", "sat", "fri")}
months = sorted(wdays)
links = {}
for m in months:
    n = len(wdays[m])
    ls, ln = [], []
    load = 0.0
    for s in range(15):                          # southbound load on the link after station s
        load += flow[(m, s)][0] - flow[(m, s)][2]
        ls.append(round(max(0.0, load) / n))
    load = 0.0
    rev = []
    for s in range(15, 0, -1):                   # northbound load on the link before station s
        load += flow[(m, s)][1] - flow[(m, s)][3]
        rev.append(round(max(0.0, load) / n))
    links[m] = dict(south=ls, north=rev[::-1])

util_sum, util_n, pk_sum, pk_n = defaultdict(float), defaultdict(int), defaultdict(float), defaultdict(int)
with open(D_SYN / "synthetic_train_operations.csv", encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        if r["Trip_Status"] != "Operated":
            continue
        u = float(r["Capacity_Utilization"])
        util_sum[r["Date"]] += u
        util_n[r["Date"]] += 1
        if int(r["Scheduled_Departure"][:2]) in (8, 9, 17, 18):
            pk_sum[r["Date"]] += u
            pk_n[r["Date"]] += 1
env = {r["Date"]: r for r in read(D_SYN / "synthetic_environmental_impact.csv")}


def hm(t):
    return int(t[:2]) * 60 + int(t[3:]) if t else None


def col(fn):
    return [fn(r) for r in line]


def fnum(v, nd=None):
    if v in ("", None):
        return None
    x = float(v)
    return int(x) if nd is None else round(x, nd)


L = dict(
    status=col(lambda r: r["Service_Status"]), pax=col(lambda r: int(r["Line_Passengers"])), rev=col(lambda r: fnum(r["Gross_Fare_Revenue_BDT"])), pkm=col(lambda r: int(r["Passenger_KM"])),
    sched=col(lambda r: int(r["Scheduled_Trips"])), actual=col(lambda r: int(r["Actual_Trips"])), cancelled=col(lambda r: int(r["Cancelled_Trips"])), sets=col(lambda r: int(r["Train_Sets_In_Service"])),
    otp=col(lambda r: fnum(r["On_Time_Percentage"], 2)), delay=col(lambda r: fnum(r["Average_Delay_Minutes"], 2)), interrupt=col(lambda r: fnum(r["Service_Interruption_Minutes"])),
    maxUtil=col(lambda r: fnum(r["Max_Capacity_Utilization"], 3)), avgUtil=col(lambda r: round(util_sum[r["Date"]] / util_n[r["Date"]], 3) if util_n[r["Date"]] else None),
    peakUtil=col(lambda r: round(pk_sum[r["Date"]] / pk_n[r["Date"]], 3) if pk_n[r["Date"]] else None),
    start=col(lambda r: hm(r["First_Departure"])), end=col(lambda r: hm(r["Last_Departure"])), pkHw=col(lambda r: fnum(r["Peak_Headway_Min"])), offHw=col(lambda r: fnum(r["Off_Peak_Headway_Min"])),
    openStations=col(lambda r: int(r["Open_Stations"])), weather=col(lambda r: r["Weather_Category"]), holiday=col(lambda r: int(r["Holiday_Flag"] or 0)), ramadan=col(lambda r: int(r["Ramadan_Flag"] or 0)),
    pinned=col(lambda r: 1 if r["Line_Total_Calibration"].startswith("Pinned") else 0), trainKm=col(lambda r: fnum(r["Train_KM"])),
    vkm=col(lambda r: int(env[r["Date"]]["Estimated_Vehicle_KM_Avoided"])), fuel=col(lambda r: int(env[r["Date"]]["Fuel_Saved_Litres"])), co2Road=col(lambda r: int(env[r["Date"]]["CO2_Emissions_Avoided_KG"])),
    pm25=col(lambda r: float(env[r["Date"]]["PM25_Emissions_Avoided_KG"])), kwh=col(lambda r: int(env[r["Date"]]["Electricity_Consumption_KWH"])), co2Grid=col(lambda r: int(env[r["Date"]]["CO2_From_Electricity_KG"])),
)

monthly = [dict(month=r["Month"], pax=int(r["Line_Passengers"]), rev=int(r["Gross_Fare_Revenue_BDT"]), trips=int(r["Operated_Trips"]), trainKm=int(r["Train_KM"]), kwh=int(r["Energy_KWH"]),
                energyCost=int(r["Energy_Cost_BDT"]), opex=int(r["Operating_Expense_BDT"])) for r in read(D_MOD / "synthetic_monthly_operating_summary.csv")]

# ------------------------------------------------------------------ published / financial (actual)
revisions = [dict(revision=r["Project_Revision"], approved=r["Approval_Date"], total=int(r["Total_Cost_BDT"]), gob=int(r["GoB_BDT"]), pa=int(r["PA_JICA_BDT"]), end=r["Implementation_End"],
                  km=float(r["Route_Length_KM"])) for r in read(D_ACT / "project_cost_revisions.csv")]
yearly = [dict(fy=r["Fiscal_Year"], alloc=int(r["ADP_Allocation_BDT"]), exp=int(r["Actual_Expenditure_BDT"]), cum=int(r["Cumulative_Expenditure_BDT"]), partial=r["Is_Partial_Year"] == "Yes")
          for r in read(D_ACT / "project_financial_history.csv")]
components = [dict(component=r["Cost_Component"], change=int(r["Change_BDT"])) for r in read(D_ACT / "project_cost_component_changes.csv") if not r["Cost_Component"].startswith("NET")]
audited = [dict(fy="2022-23", gross=None, net=182806514, nonFare=None), dict(fy="2023-24", gross=2462821403, net=2439107625, nonFare=93700144), dict(fy="2024-25", gross=4176915397, net=4116020837, nonFare=173530122)]
published = [dict(start=r["Period_Start"], end=r["Period_End"], grain=r["Reporting_Grain"], metric=r["Metric"], value=float(r["Value"]), unit=r["Unit"], coverage=r["Geographic_Coverage"],
                  notes=r["Notes"], type=r["Data_Type"], source=r["Source_ID"]) for r in read(D_ACT / "actual_ridership_statistics.csv")]
milestones = [dict(date=r["Milestone_Date"], category=r["Category"], text=r["Milestone"], type=r["Data_Type"]) for r in read(D_ACT / "project_milestones.csv")
              if r["Category"] in ("Approval", "Opening", "Financing", "Disruption") or "TARGET" in r["Milestone"]]
fy_opex = defaultdict(float)
for r in read(D_SYN / "synthetic_monthly_opex.csv"):
    fy_opex[r["Fiscal_Year"]] += float(r["Actual_or_Simulated_Expense_BDT"])
fin = [dict(fy=r["Fiscal_Year"], period=r["Period_Type"], pax=int(r["Passengers"]), fare=int(r["Fare_Revenue_BDT"]), nonFare=int(r["Non_Fare_Revenue_BDT"]), opex=int(r["Operating_Cost_BDT"]),
            farebox=fnum(r["Farebox_Recovery_Ratio"], 2), debt=int(r["Estimated_Debt_Service_BDT"])) for r in read(D_MOD / "financial_viability_annual.csv")]
cba = [dict(fy=r["Fiscal_Year"], period=r["Period_Type"], hours=int(r["Passenger_Hours_Saved"]), vkm=int(r["Vehicle_KM_Avoided"]), fuel=int(r["Fuel_Saved_Litres"]), co2=int(r["Net_CO2_Avoided_Tonnes"]),
            timeBenefit=int(r["Benefit_Time_Savings_BDT"]), vocBenefit=int(r["Benefit_Vehicle_Operating_Cost_BDT"]))
       for r in read(D_MOD / "cba_annual_cashflows.csv") if r["Scenario"] == "Base case" and int(r["Fiscal_Year"][:4]) >= 2022]
params = read(D_MOD / "economic_benefit_parameters.csv")
modes = [dict(mode=r["Mode_or_Item"], share=float(r["Value"])) for r in params if r["Parameter"] == "Previous mode share"]
eco = defaultdict(dict)
for r in read(D_SYN / "synthetic_station_economic_activity.csv"):
    if r["Year"] == "2026" and r["Station_ID"] in SI:
        eco[SI[r["Station_ID"]]][r["Catchment_Radius"]] = dict(value=int(r["Estimated_Property_Value"]), premium=float(r["Assumed_Metro_Premium_Pct"]), rent=float(r["Average_Rent"]), business=int(r["Business_Count"]))
kp = {r["KPI"]: r["Value"] for r in read(D_MOD / "impact_kpis.csv")}

data = dict(
    meta=dict(title="DHAKA METRO INTELLIGENCE", project="Dhaka Mass Rapid Transit Development Project - MRT Line-6", researchCutoff="2026-11-13", built=_dt.date.today().isoformat(),
              dataset="Packaged dataset (MRT Line-6 analytical package, Phases 1-4)", geoNote=GEO_NOTE, trainCapacity=2300,
              disclaimer="Operational figures are SYNTHETIC simulations calibrated to published totals. They are not a DMTCL feed.",
              contextNote="Station descriptions and nearby places are descriptive context written for this dashboard, not a dataset. Catchment population is not available from public sources."),
    stations=stations, route=[[round(a, 6), round(b, 6)] for a, b in route], routeCum=[round(c) for c in cum],
    dates=dates, hours=HOURS,
    daily=dict(type="Synthetic", entries=E, exits=X, revenue=R), hourlyLine=dict(type="Synthetic", values=H), stationHourShape=dict(type="Synthetic", note="Average share of a station's daily entries/exits by hour over the last 365 days, by day type", **shape),
    line=dict(type="Synthetic", **L), monthly=dict(type="Synthetic", rows=monthly), links=dict(type="Synthetic", note="Average working-day passenger load on each link between adjacent stations, by month", months=months, byMonth=links),
    finance=dict(revisions=dict(type="Actual", source="S001 RTHD project fact sheet", rows=revisions), yearly=dict(type="Actual", source="S001 RTHD project fact sheet", rows=yearly),
                 audited=dict(type="Actual", source="S002 DMTCL audited financial statements FY2024-25", rows=audited),
                 componentChanges=dict(type="Actual", source="S008 press report of the 3rd revision", note="A full component-wise cost breakdown has not been published; only the changes made in the 3rd revision are available", rows=components),
                 viability=dict(type="Estimated", note="Revenue audited to FY2024-25, synthetic FY2025-26, forecast after; operating cost synthetic/assumed; FY2025-26 prices", rows=fin)),
    published=dict(type="Actual", rows=published), milestones=milestones,
    impact=dict(type="Estimated", note="Modelled from mode-shift shares and assumed emission factors, speeds and values of time (see phase3_impact_methodology.md)", annual=cba, modes=modes,
                travelTime=[dict(label="Uttara North - Motijheel, road (2009 baseline, JICA)", minutes=105, type="Actual"), dict(label="Uttara North - Motijheel, road (press, 2026)", minutes=120, type="Actual"),
                            dict(label="Uttara North - Motijheel, metro", minutes=38, type="Actual"), dict(label="Average 7.7 km trip, former bus rider (modelled)", minutes=59, type="Estimated"),
                            dict(label="Average 7.7 km trip, metro door to door (modelled)", minutes=30, type="Estimated")],
                avgMinutesSaved=float(kp["Average door-to-door time saved per passenger, FY2025-26"]), busMinutesSaved=float(kp["Time saved per former bus passenger, FY2025-26"])),
    catchment=dict(type="Synthetic", note="Simulated station-area indicators for 2026; the metro premium is an assumption, not a measured effect", byStation=[eco[k] for k in range(16)]),
)
js = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
(OUT / "dashboard_data.json").write_text(js, encoding="utf-8")
(OUT / "dashboard_data.js").write_text("// Generated by 05_Documentation/scripts/build_dashboard_data.py - do not edit by hand.\nwindow.MRT_DATA = " + js + ";\n", encoding="utf-8")

# ------------------------------------------------------------------ small CSV extracts for testing the upload control
cut = dates[-31]


def extract(src, name, keep=lambda r: True):
    with open(src, encoding="utf-8-sig") as f, open(OUT / "csv" / name, "w", newline="", encoding="utf-8") as g:
        rd = csv.DictReader(f)
        w = csv.DictWriter(g, fieldnames=rd.fieldnames)
        w.writeheader()
        n = 0
        for r in rd:
            if keep(r):
                w.writerow(r)
                n += 1
    return n


recent = lambda r: r["Date"] >= cut
counts = {
    "synthetic_daily_ridership.csv": extract(D_SYN / "synthetic_daily_ridership.csv", "synthetic_daily_ridership.csv", recent),
    "synthetic_hourly_ridership.csv": extract(D_SYN / "synthetic_hourly_ridership.csv", "synthetic_hourly_ridership.csv", recent),
    "synthetic_ticket_revenue.csv": extract(D_SYN / "synthetic_ticket_revenue.csv", "synthetic_ticket_revenue.csv", recent),
    "synthetic_train_operations.csv": extract(D_SYN / "synthetic_train_operations.csv", "synthetic_train_operations.csv", recent),
    "synthetic_environmental_impact.csv": extract(D_SYN / "synthetic_environmental_impact.csv", "synthetic_environmental_impact.csv", recent),
    "synthetic_monthly_opex.csv": extract(D_SYN / "synthetic_monthly_opex.csv", "synthetic_monthly_opex.csv"),
    "synthetic_station_economic_activity.csv": extract(D_SYN / "synthetic_station_economic_activity.csv", "synthetic_station_economic_activity.csv"),
    "actual_ridership_statistics.csv": extract(D_ACT / "actual_ridership_statistics.csv", "actual_ridership_statistics.csv"),
    "operational_performance_actual.csv": extract(D_ACT / "operational_performance_actual.csv", "operational_performance_actual.csv"),
    "fare_structure_history.csv": extract(D_ACT / "fare_structure_history.csv", "fare_structure_history.csv"),
    "project_financial_history.csv": extract(D_ACT / "project_financial_history.csv", "project_financial_history.csv"),
}
print(GEO_NOTE)
print("stations:", [(s["name"], s["lat"], s["lng"], s["chainageM"]) for s in stations][:3], "...")
print("dates", ND, dates[0], dates[-1], "| data.js size", round(len(js) / 1e6, 2), "MB | csv extracts (last 31 days for the large files):", counts)
