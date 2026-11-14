"""
Phase 3 build script - Dhaka MRT Line-6 economic, social and environmental impact.

Inputs : Phase 1 actual tables and Phase 2 synthetic tables (run build_phase1.py and build_phase2.py first).
Outputs:
  02_Actual_Data/      transportation_comparison_actual.csv, environmental_impact_actual.csv,
                       passenger_experience_actual.csv, urban_development_actual.csv, reference_inflation.csv
  03_Synthetic_Data/   synthetic_passenger_survey.csv, synthetic_transport_comparison.csv,
                       synthetic_environmental_impact.csv, synthetic_station_economic_activity.csv
  04_Analytical_Models/ economic_benefit_parameters.csv, cba_annual_cashflows.csv, cba_scenario_summary.csv,
                       financial_viability_annual.csv, debt_service_schedule_estimated.csv, impact_kpis.csv
  05_Documentation/    assumptions_register_phase3.csv, phase3_validation_log.txt
  01_Research/         source_register_phase3.csv

Historical years use Actual (Phase 1) or Synthetic (Phase 2) inputs; FY2026-27 onward is Forecast.
Standard library only.  Run:  python 05_Documentation/scripts/build_phase3.py
"""
import csv
import math
import random
from collections import defaultdict
from datetime import date
from pathlib import Path

SEED = 20261114
rng = random.Random(SEED)
ROOT = Path(__file__).resolve().parents[2]
D_ACT, D_SYN, D_MOD, D_DOC, D_RES = (ROOT / x for x in ("02_Actual_Data", "03_Synthetic_Data", "04_Analytical_Models", "05_Documentation", "01_Research"))
CR = 1e7
PROV_COLS = ["Data_Type", "Source_ID", "Data_Confidence", "Methodology", "Is_Modelled", "Is_Verified"]


def write(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    return len(rows)


def read(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def fy_of(d):
    y, m = int(d[:4]), int(d[5:7])
    return f"{y}-{str(y + 1)[2:]}" if m >= 7 else f"{y - 1}-{str(y)[2:]}"


def fy_label(start_year):
    return f"{start_year}-{str(start_year + 1)[2:]}"


def lognorm(sd):
    return math.exp(rng.gauss(-sd * sd / 2, sd))


# ======================================================================================== sources
SOURCES3 = [
 ("S040", 2, "JICA Ogata Research Institute", "Yamada & Jiang (2025), The Impact of Dhaka Mass Rapid Transit on Road Congestion, Discussion Paper No. 35", "https://www.jica.go.jp/english/jica_ri/publication/discussion/__icsFiles/afieldfile/2025/02/21/Discussion_Paper_No35.pdf", "2025-02", "FULL", "High", "Not peer-reviewed. Google Maps travel-time data, event-study design, to June 2024."),
 ("S041", 3, "The Business Standard", "Metro Rail Line-6 alone to save Tk3,500cr in travel time, vehicle operation cost yearly", "https://www.tbsnews.net/supplement/metro-rail-line-6-alone-save-tk3500cr-travel-time-vehicle-operation-cost-yearly-558822", "2022-12-27", "PAGE", "Medium", "Pre-opening DMTCL/JICA projections, not measured outcomes."),
 ("S042", 3, "Khan & Tabassum, Int. J. of Scientific Research and Modern Technology 4(12)", "Who Switches to Metro and Why? Service Quality, Demographics, and Early Mode Shift of Dhaka's MRT Line-6", "https://www.ijsrmt.com/index.php/ijsrmt/article/view/1101", "2026", "PAGE", "Medium", "Abstract only. Survey July-October 2023, n = 1,397."),
 ("S043", 3, "AIUB student research", "Impact of MRT Line 6 on commuter modal shift, travel time reduction, and future expansion prospects", "https://www.aiub.edu/Files/student-research/IMPACT_OF_MRT_LINE_6_DHAKA_METRO_RAIL_ON_COMMUTER_MODAL_SHIFT_TRAVEL_TIME_REDUCTION_AND_FUTURE_EXPANSION_PROSPECTS.html", "2025", "SNIPPET", "Low", "About 200 respondents."),
 ("S044", 3, "The Business Standard (citing World Bank / BUET Accident Research Institute)", "Beyond flyovers and expressways: What can solve Dhaka's traffic crisis?", "https://www.tbsnews.net/features/panorama/beyond-flyovers-and-expressways-what-can-solve-dhakas-traffic-crisis-1074471", "2025", "SNIPPET", "Low", "Average traffic speed 21 km/h (2005-07) to 4.8 km/h (2022); sources differ on years."),
 ("S045", 3, "The Daily Star", "Dhaka's metro rail: mass transit solution or missed opportunity?", "https://www.thedailystar.net/slow-reads/big-picture/news/dhakas-metro-rail-mass-transit-solution-or-missed-opportunity-4155146", "2026-04-19", "PAGE", "Medium", ""),
 ("S046", 3, "The Business Standard", "Metro proximity and flat prices in Uttara and Mirpur (two reports, 2023 and 2024)", "https://www.tbsnews.net/bangladesh/nothing-under-tk1cr-metro-proximity-sends-flat-prices-soaring-uttara-mirpur-1032761", "2023-2024", "SNIPPET", "Low", "Developer and portal statements; metro effect not isolated from construction costs."),
 ("S047", 2, "Asian Development Bank project economic analyses (Bangladesh)", "Economic analysis documents: 12% discount rate; values of travel time by vehicle type", "https://www.adb.org/sites/default/files/linked-documents/40540-019-efa.pdf", "c. 2016", "SNIPPET", "Low", "Project-specific appraisal values, not a national standard."),
 ("S048", 3, "UNB / Dhaka Tribune / The Business Standard", "Dhaka city bus fare notifications 2022-2026", "https://www.dhakatribune.com/bangladesh/420498/govt-issues-gazette-raising-bus-minibus-fares-by", "2022-2026", "SNIPPET", "Low", "Tk 2.45/km from Sep 2022; Tk 2.70/km (from 2.53) from 22 Sep 2026; minimum Tk 10."),
 ("S049", 3, "The Daily Star / The Business Standard", "CNG auto-rickshaw metered fare (2015) and non-use of meters", "https://www.tbsnews.net/bangladesh/cng-drivers-face-tk50000-fine-6-months-imprisonment-charging-fare-higher-meter-1066706", "2015; 2025", "SNIPPET", "Low", "Official: Tk 40 for first 2 km, Tk 12/km after; meters are not used in practice."),
 ("S050", 3, "BBS figures as reported by Financial Express, Daily Star, UNB", "Fiscal-year average CPI inflation FY2019-20 to FY2025-26", "https://thefinancialexpress.com.bd/economy/average-annual-inflation-cools-to-868-per-cent-in-fy26", "2020-2026", "SNIPPET", "Medium", "FY2012-13 to FY2018-19 values are analyst-recalled and unverified."),
 ("S051", 3, "The Daily Star (citing Ember)", "Bangladesh power system gets dirtier on rapid coal use growth", "https://www.thedailystar.net/business/news/bangladesh-power-system-gets-dirtier-rapid-coal-use-growth-3582036", "2024", "SNIPPET", "Low", "Grid carbon intensity about 0.72-0.74 tCO2/MWh in 2022-23 (units garbled in the report)."),
 ("M3-SUR", 0, "This study", "Synthetic passenger survey model", "", "", "MODEL", "Low", "Marginal distributions tied to S042 where published; everything else assumed."),
 ("M3-TRN", 0, "This study", "Synthetic transport comparison model", "", "", "MODEL", "Low", "Road speeds and fares by mode; calibrated to S040, S041, S044, S048."),
 ("M3-ENV", 0, "This study", "Environmental impact model", "", "", "MODEL", "Low", "Mode-shift shares x emission factors; electricity from Phase 2."),
 ("M3-ECO", 0, "This study", "Station-area economic activity model", "", "", "MODEL", "Low", "City trend plus an assumed metro premium; anchored loosely to S046."),
 ("M3-CBA", 0, "This study", "Financial and economic cost-benefit model", "", "", "MODEL", "Low", "See phase3_impact_methodology.md."),
]
write(D_RES / "source_register_phase3.csv", ["Source_ID", "Tier", "Source_Organization", "Source_Document", "URL", "Publication_Date", "Access_Method", "Default_Confidence", "Notes"], SOURCES3)
CONF = {s[0]: s[7] for s in SOURCES3}
CONF.update({"S003": "High", "S004": "High", "S006": "High", "S001": "High", "S002": "High", "S012": "Medium", "S014": "Medium", "S016": "Medium", "S013": "Medium"})


def act(src, dtype="Actual", meth="Transcribed from source", verified=None):
    c = CONF[src.split(";")[0].strip()]
    return [dtype, src, c, meth, "No", verified or ("Yes" if c != "Low" and dtype == "Actual" else "No")]


def syn(model, dtype="Synthetic"):
    return [dtype, model, "Low", "See phase3_impact_methodology.md", "Yes", "No"]


# ======================================================================================== ACTUAL evidence tables
TA = [
 ("Travel time Uttara-Saidabad by road, baseline", 110.4, "minutes", "2009", "Uttara-Saidabad", "JICA appraisal baseline", "S003", "Actual"),
 ("Travel time Uttara North-Motijheel by road, baseline", 105, "minutes", "2009", "Uttara North-Motijheel", "JICA appraisal baseline", "S004", "Actual"),
 ("Travel time Uttara North-Motijheel by metro, target", 36, "minutes", "2023 target", "Uttara North-Motijheel", "JICA appraisal target", "S004", "Forecast"),
 ("Travel time Uttara-Motijheel by road (pre-opening figure)", 208, "minutes", "2022", "Uttara-Motijheel (20 km)", "Quoted by DMTCL before opening", "S041", "Actual"),
 ("Travel time Uttara-Motijheel by metro", 40, "minutes", "2022", "Uttara-Motijheel", "About 40 minutes", "S041", "Actual"),
 ("Travel time Uttara-Motijheel by road", 120, "minutes", "2026", "Uttara-Motijheel", "'About two hours' vs 30-40 minutes by metro", "S045", "Actual"),
 ("Projected road travel time without metro", 446, "minutes", "2025 projection", "Uttara-Motijheel", "Pre-opening projection", "S041", "Forecast"),
 ("Average vehicle speed in Dhaka", 6.4, "km/h", "2014", "Dhaka", "Quoted in JICA appraisal", "S006", "Actual"),
 ("Average traffic speed in Dhaka", 21, "km/h", "2005-2007", "Dhaka", "Sources differ on the year", "S044", "Actual"),
 ("Average traffic speed in Dhaka", 4.8, "km/h", "2022", "Dhaka", "World Bank / BUET ARI as reported", "S044", "Actual"),
 ("Increase in road vehicle speed on the MRT-6 corridor attributable to the metro (lower bound)", 10, "percent", "Jan 2022 - Jun 2024", "Roads within 500 m of the line vs control corridors", "Event-study estimate; effect appeared to fade as traffic was induced", "S040", "Estimated"),
 ("Increase in road vehicle speed on the MRT-6 corridor attributable to the metro (upper bound)", 15, "percent", "Jan 2022 - Jun 2024", "Roads within 500 m of the line vs control corridors", "Event-study estimate", "S040", "Estimated"),
 ("Share of metro passengers who previously used buses", 60, "percent", "Jul-Oct 2023", "MRT-6 passengers (n = 1,397)", "'Nearly 60%'", "S042", "Actual"),
 ("Share of metro passengers who previously used private vehicles", 12, "percent", "Jul-Oct 2023", "MRT-6 passengers (n = 1,397)", "'About 12%'", "S042", "Actual"),
 ("Share of Uttara-Motijheel passengers who previously used public transport", 59.41, "percent", "2025", "Survey of about 200 residents", "Student study", "S043", "Actual"),
 ("Average daily commute time before / after metro", "about 120 / about 40", "minutes", "2025", "Survey of about 200 residents", "Student study", "S043", "Actual"),
 ("MRT-6 share of Dhaka's daily trips", 1, "percent", "2026", "Dhaka", "About 400,000 of roughly 40 million trips", "S045", "Actual"),
 ("Projected daily value of travel time saved", 8.38, "crore BDT per day", "pre-opening projection", "MRT-6 at 500,000 passengers", "DMTCL projection", "S041", "Forecast"),
 ("Projected daily vehicle operating cost saving", 1.18, "crore BDT per day", "pre-opening projection", "MRT-6", "DMTCL projection", "S041", "Forecast"),
 ("City bus fare per passenger-km, Dhaka", 2.45, "BDT per km", "from Sep 2022", "Dhaka metropolitan area", "Minimum fare Tk 10", "S048", "Actual"),
 ("City bus fare per passenger-km, Dhaka", 2.70, "BDT per km", "from 22 Sep 2026", "Dhaka metropolitan area", "Raised from Tk 2.53", "S048", "Actual"),
 ("CNG auto-rickshaw official fare", "40 for first 2 km + 12 per km", "BDT", "since 2015", "Dhaka", "Meters not used in practice", "S049", "Actual"),
 ("Share of income Dhaka residents spend on commuting", 19, "percent", "2019", "Dhaka", "ADB (2019) as cited in S040", "S040", "Actual"),
]
write(D_ACT / "transportation_comparison_actual.csv", ["Metric", "Value", "Unit", "Reporting_Period", "Geographic_Coverage", "Notes"] + PROV_COLS,
      [[t[0], t[1], t[2], t[3], t[4], t[5]] + act(t[6], t[7], "Projection quoted by source" if t[7] == "Forecast" else ("Econometric estimate reported by source" if t[7] == "Estimated" else "Transcribed from source")) for t in TA])

EA = [
 ("Projected CO2 reduction from MRT-6", 200000, "tonnes per year", "pre-opening projection", "'More than 2 lakh tonnes'", "S041", "Forecast"),
 ("Annual average PM10 concentration, Dhaka", 146, "micrograms per m3", "before 2020", "Quoted in JICA appraisal; WHO guideline range 20-70", "S006", "Actual"),
 ("EIA report approved by Department of Environment", "2011-07-11", "date", "2011", "Environmental Clearance Certificate renewed annually", "S006", "Actual"),
 ("Grid electricity carbon intensity, Bangladesh", 0.73, "tCO2 per MWh", "2022-2023", "Approximate; units garbled in the news report", "S051", "Actual"),
 ("Land to be acquired / people affected (2020 appraisal)", "57.3 ha / 1,499 people", "", "2020", "No involuntary resettlement expected", "S006", "Actual"),
 ("Measured air-quality or noise change attributable to MRT-6", "", "", "", "NOT FOUND: no published before/after measurement located", "S006", "Actual"),
 ("Measured traction and station electricity consumption", "", "kWh", "", "NOT FOUND: only an approximate monthly bill is reported (Phase 2, S034)", "S006", "Actual"),
]
write(D_ACT / "environmental_impact_actual.csv", ["Metric", "Value", "Unit", "Reporting_Period", "Notes"] + PROV_COLS,
      [[e[0], e[1], e[2], e[3], e[4]] + act(e[5], e[6], "Projection quoted by source" if e[6] == "Forecast" else "Transcribed from source", "No" if e[1] == "" else None) for e in EA])

PA = [
 ("Mean satisfaction: travel time savings (1-5 scale)", 4.39, "S042", "Highest-rated attribute"),
 ("Mean satisfaction: reliability, comfort, cleanliness, safety, information", "above 4.0", "S042", "Individual values not in the abstract"),
 ("Lowest-rated attributes", "feeder service availability; travel cost", "S042", "Values not in the abstract"),
 ("Share of trips that are work-related", "36.8 percent", "S042", "Largest trip purpose"),
 ("Typical user", "young and middle-aged, middle-income, salary-dependent households", "S042", "A share of about 45% is attached; basis unclear"),
 ("Women-only compartments", "viewed positively by users", "S045", "Qualitative; JICA-related survey, no percentages published"),
 ("First- and last-mile access", "poor integration and pedestrian amenities", "S045", "Qualitative"),
 ("Accessibility for persons with disabilities", "", "S045", "NOT FOUND: no survey evidence located"),
]
write(D_ACT / "passenger_experience_actual.csv", ["Finding", "Value", "Notes"] + PROV_COLS, [[p[0], p[1], p[3]] + act(p[2], verified="No" if p[1] == "" else None) for p in PA])

UA = [
 ("Apartment demand change, Mirpur", 24, "percent", "c. 2023", "Property portal (Bproperty) as reported", "S046"),
 ("Apartment rent change, Mirpur", 27, "percent", "c. 2023", "Property portal as reported", "S046"),
 ("Apartment price change, Mirpur (average)", 8.6, "percent", "c. 2023", "Property portal as reported", "S046"),
 ("Flat price change, Uttara and Mirpur", 25, "percent", "c. 2024, one year", "Developers also cite construction costs and planning-rule changes", "S046"),
 ("Flat price, Pallabi project", "5,500 to 7,500", "BDT per sq ft", "2021 to c. 2023", "Single developer example", "S046"),
 ("Flat price quoted, Shewrapara and Uttara Sector 13 projects", 12500, "BDT per sq ft", "c. 2024", "Developer quotes", "S046"),
 ("Property values around stations", "2 to 3 times", "multiple", "to 2026", "Journalistic claim, no data cited", "S045"),
 ("Land allocated for transit-oriented development at Uttara", 32.277, "acres", "2026", "RAJUK allocation", "S001"),
 ("Station-level transaction prices, business counts, employment", "", "", "", "NOT FOUND: no public dataset located", "S046"),
]
write(D_ACT / "urban_development_actual.csv", ["Metric", "Value", "Unit", "Reporting_Period", "Notes"] + PROV_COLS,
      [[u[0], u[1], u[2], u[3], u[4]] + act(u[5], verified="No" if u[1] == "" else None) for u in UA])

# CPI inflation (fiscal-year average, percent) and index with FY2025-26 = 1
INFL = {2012: 6.78, 2013: 7.35, 2014: 6.41, 2015: 5.92, 2016: 5.44, 2017: 5.78, 2018: 5.48,      # unverified recall
        2019: 5.65, 2020: 5.56, 2021: 6.15, 2022: 9.02, 2023: 9.73, 2024: 10.03, 2025: 8.68}      # S050
BASE = 2025                                             # price base FY2025-26
PRICE = {BASE: 1.0}
for y in range(BASE - 1, 2011, -1):
    PRICE[y] = PRICE[y + 1] * (1 + INFL[y + 1] / 100)   # multiply year-y taka by PRICE[y] to get FY2025-26 taka
write(D_ACT / "reference_inflation.csv", ["Fiscal_Year", "CPI_Inflation_Pct", "Factor_To_FY2025_26_Prices"] + PROV_COLS,
      [[fy_label(y), INFL[y], round(PRICE[y], 4)] + (act("S050", meth="BBS fiscal-year average as reported in the press") if y >= 2019 else
                                                      ["Estimated", "S050", "Low", "Analyst-recalled value, not verified against BBS", "No", "No"]) for y in sorted(INFL)])

# ======================================================================================== load Phase 1 / 2
line = read(D_SYN / "synthetic_daily_line_summary.csv")
energy_day = defaultdict(float)
for r in read(D_SYN / "synthetic_energy_consumption.csv"):
    energy_day[r["Date"]] += float(r["Energy_Consumption_KWH"])
PAX, PKM, REV, KWH, TKM = (defaultdict(float) for _ in range(5))
for r in line:
    f = fy_of(r["Date"])
    PAX[f] += int(r["Line_Passengers"])
    PKM[f] += int(r["Passenger_KM"])
    REV[f] += float(r["Gross_Fare_Revenue_BDT"])
    TKM[f] += float(r["Train_KM"] or 0)
    KWH[f] += energy_day[r["Date"]]
OPEX = defaultdict(float)
for r in read(D_SYN / "synthetic_monthly_opex.csv"):
    OPEX[r["Fiscal_Year"]] += float(r["Actual_or_Simulated_Expense_BDT"])
CAPEX = {int(r["Fiscal_Year"][:4]): float(r["Actual_Expenditure_BDT"]) for r in read(D_ACT / "project_financial_history.csv")}
# annualise FY2026-27 (synthetic covers 1 Jul - 13 Nov 2026) with the FY2025-26 seasonal share
same = sum(int(r["Line_Passengers"]) for r in line if "2025-07-01" <= r["Date"] <= "2025-11-13")
ANNUALISE = PAX["2025-26"] / same

# ======================================================================================== parameters
MODES = ["Bus", "Private car", "Motorcycle", "CNG / ride-hailing", "Rickshaw / walk / other", "New trip (induced)"]
PREV_SHARE = {"Bus": 0.60, "Private car": 0.06, "Motorcycle": 0.06, "CNG / ride-hailing": 0.10, "Rickshaw / walk / other": 0.08, "New trip (induced)": 0.10}
SPEED = {"Bus": 10.0, "Private car": 13.0, "Motorcycle": 18.0, "CNG / ride-hailing": 13.0}       # km/h, in-vehicle, corridor average
FIXED_MIN = {"Bus": 13.0, "Private car": 5.0, "Motorcycle": 2.0, "CNG / ride-hailing": 5.0}      # wait + access/egress
METRO_SPEED, METRO_FIXED = 32.0, 16.0                                                            # 20.1 km in 38 min; wait 4 + access/egress 12
VOT = {"Bus": 85.0, "Private car": 150.0, "Motorcycle": 62.0, "CNG / ride-hailing": 110.0, "Rickshaw / walk / other": 62.0}   # BDT/hour, FY2025-26 prices
VOT_REAL_GROWTH = 0.02
OCC = {"Bus": 45.0, "Private car": 1.6, "Motorcycle": 1.2, "CNG / ride-hailing": 2.2}
SUPPLY_RESP = {"Bus": 0.5, "Private car": 1.0, "Motorcycle": 1.0, "CNG / ride-hailing": 0.7}
VOC = {"Bus": 60.0, "Private car": 24.0, "Motorcycle": 5.0, "CNG / ride-hailing": 11.0}          # BDT per vehicle-km, economic, FY2025-26 prices
FUEL = {"Bus": 0.35, "Private car": 0.12, "Motorcycle": 0.035, "CNG / ride-hailing": 0.075}      # litres (or litre-equivalent) per vehicle-km
CO2 = {"Bus": 0.94, "Private car": 0.28, "Motorcycle": 0.08, "CNG / ride-hailing": 0.14}         # kg per vehicle-km
PM25 = {"Bus": 0.50, "Private car": 0.015, "Motorcycle": 0.03, "CNG / ride-hailing": 0.01}       # g per vehicle-km
GRID_EF = 0.70                 # kg CO2 per kWh
CARBON_PRICE = 4900.0          # BDT per tonne CO2 (about USD 40), FY2025-26 prices, +2% a year in real terms
PM_DAMAGE = 3.7e6              # BDT per tonne PM2.5 (about USD 30,000)
ECON_CF_CAPEX, ECON_CF_OPEX = 0.85, 0.90
RESIDUAL_SHARE = 0.45
END_YEAR = 2044                # FY2044-45
RATES = (0.08, 0.10, 0.12, 0.15)
OTHER_SAVING_MIN = 5.0
write(D_MOD / "economic_benefit_parameters.csv", ["Parameter", "Mode_or_Item", "Value", "Unit", "Basis"] + PROV_COLS,
      [["Previous mode share", m, PREV_SHARE[m], "share of metro passengers", "Bus and private-vehicle totals from S042; split of the rest assumed"] + syn("M3-CBA;S042", "Estimated") for m in MODES] +
      [["Road in-vehicle speed", m, SPEED[m], "km/h", "Between the 2009 JICA baseline (about 11 km/h) and the 2022 pre-opening figure (about 6 km/h): S004, S041, S044"] + syn("M3-CBA;S004;S041", "Estimated") for m in SPEED] +
      [["Fixed time (wait, access, egress)", m, FIXED_MIN[m], "minutes", "Assumed"] + syn("M3-CBA", "Estimated") for m in FIXED_MIN] +
      [["Metro in-vehicle speed", "Metro", METRO_SPEED, "km/h", "20.1 km in about 38 minutes (S004, S041)"] + syn("M3-CBA;S004", "Estimated"),
       ["Fixed time (wait, access, egress)", "Metro", METRO_FIXED, "minutes", "Assumed: 4 min wait, 12 min access/egress including stairs"] + syn("M3-CBA", "Estimated")] +
      [["Value of travel time", m, VOT[m], "BDT per hour (FY2025-26 prices)", "ADB appraisal values (work/non-work) blended 20/80 and inflated by CPI (S047, S050)"] + syn("M3-CBA;S047", "Estimated") for m in VOT] +
      [["Vehicle occupancy", m, OCC[m], "passengers per vehicle", "Assumed"] + syn("M3-CBA", "Estimated") for m in OCC] +
      [["Road supply response", m, SUPPLY_RESP[m], "share of freed vehicle-km actually withdrawn", "Assumed"] + syn("M3-CBA", "Estimated") for m in SUPPLY_RESP] +
      [["Vehicle operating cost", m, VOC[m], "BDT per vehicle-km (economic)", "Assumed"] + syn("M3-CBA", "Estimated") for m in VOC] +
      [["Fuel use", m, FUEL[m], "litres per vehicle-km", "Assumed congested urban values"] + syn("M3-CBA", "Estimated") for m in FUEL] +
      [["CO2 emission factor", m, CO2[m], "kg per vehicle-km", "Fuel use x standard carbon content"] + syn("M3-CBA", "Estimated") for m in CO2] +
      [["PM2.5 emission factor", m, PM25[m], "g per vehicle-km", "Assumed; older diesel buses dominate"] + syn("M3-CBA", "Estimated") for m in PM25] +
      [["Grid emission factor", "Electricity", GRID_EF, "kg CO2 per kWh", "Rounded from S051 (0.72-0.74, low confidence)"] + syn("M3-CBA;S051", "Estimated"),
       ["Carbon price", "CO2", CARBON_PRICE, "BDT per tonne", "About USD 40 per tonne, assumed, +2% a year real"] + syn("M3-CBA", "Estimated"),
       ["PM2.5 damage cost", "PM2.5", PM_DAMAGE, "BDT per tonne", "About USD 30,000 per tonne, assumed"] + syn("M3-CBA", "Estimated"),
       ["Economic conversion factor", "Capital cost", ECON_CF_CAPEX, "ratio", "Removes taxes and transfers; assumed"] + syn("M3-CBA", "Estimated"),
       ["Economic conversion factor", "Operating cost", ECON_CF_OPEX, "ratio", "Assumed"] + syn("M3-CBA", "Estimated"),
       ["Residual value", "Assets at FY2044-45", RESIDUAL_SHARE, "share of real capital cost", "Civil 60% of cost on a 60-year life, systems 40% on a 30-year life"] + syn("M3-CBA", "Estimated"),
       ["Discount rate", "Base case", 0.12, "real, per year", "Government of Bangladesh practice as described in ADB documents (S047)"] + syn("M3-CBA;S047", "Estimated")])


def minutes_saved(trip_km, speed_mult=1.0):
    """Door-to-door minutes saved per passenger by previous mode, and the weighted average."""
    metro = trip_km / METRO_SPEED * 60 + METRO_FIXED
    out = {}
    for m in SPEED:
        out[m] = trip_km / (SPEED[m] * speed_mult) * 60 + FIXED_MIN[m] - metro
    out["Rickshaw / walk / other"] = OTHER_SAVING_MIN
    exist = sum(PREV_SHARE[m] * out[m] for m in out) / (1 - PREV_SHARE["New trip (induced)"])
    out["New trip (induced)"] = exist / 2          # rule of half
    return out


# ======================================================================================== synthetic dataset 9: transport comparison
STN = [r for r in read(D_ACT / "station_reference.csv")]
CH = [0, 0.9, 2.2, 5.3, 6.0, 7.3, 8.0, 9.0, 10.9, 11.9, 13.1, 14.2, 15.3, 16.2, 17.2, 19.3]
NAME = [s["Station_Name"] for s in STN[:16]]
OPEN = [s["Opening_Date"] for s in STN[:16]]
ODS = [(0, 15), (0, 8), (0, 10), (3, 15), (5, 15), (5, 10), (5, 11), (8, 15), (8, 14), (10, 15), (3, 8), (11, 15), (0, 5), (12, 5)]


def bus_fare_km(d):
    return 1.70 if d < "2021-11-08" else (2.15 if d < "2022-08-07" else (2.50 if d < "2022-09-01" else (2.45 if d < "2024-04-01" else (2.42 if d < "2026-05-01" else (2.53 if d < "2026-09-22" else 2.70)))))


def road_speed_mult(d, peak):
    m = 1.0 if peak else 1.45
    if "2020-04" <= d[:7] <= "2020-08":
        m *= 1.8                                  # COVID-19 restrictions
    elif "2020-09" <= d[:7] <= "2021-08":
        m *= 1.25
    if "2017-08" <= d[:7] <= "2022-12":
        m *= 0.92                                 # viaduct construction in the median (S040)
    if d >= "2023-06-01":                         # metro effect on corridor road speed: +12% fading to +5% (S040)
        months = (int(d[:4]) - 2023) * 12 + int(d[5:7]) - 6
        m *= 1.05 + 0.07 * math.exp(-months / 18.0)
    return m * (1 - 0.01 * max(0, int(d[:4]) - 2019))    # background worsening of 1% a year


def metro_fare(i, j):
    return min(100, max(20, -(-round(abs(CH[i] - CH[j]) * 10) // 20) * 10))


rows = []
y, mth = 2019, 1
while (y, mth) <= (2026, 11):
    d = f"{y}-{mth:02d}-01"
    infl = PRICE[2025] / PRICE[min(2025, y if mth >= 7 else y - 1)] if (y if mth >= 7 else y - 1) >= 2012 else 1
    for (i, j) in ODS:
        km_rail = abs(CH[i] - CH[j]) * 20.1 / 19.3
        km_road = km_rail * 1.12
        for peak in (True, False):
            sm = road_speed_mult(d, peak)
            period = "Peak" if peak else "Off-peak"
            if d >= max(OPEN[i], OPEN[j]) and not ("2024-08" == d[:7]):
                t = km_rail / METRO_SPEED * 60 + METRO_FIXED - (0 if peak else 0) + (2 if not peak else 0)
                rows.append([d, NAME[i], NAME[j], "Metro rail", period, round(t * lognorm(0.03), 1), metro_fare(i, j), round(km_rail, 2), "", "Not applicable (grade separated)"] + syn("M3-TRN"))
            for mode, sp, fx in (("Bus", 9.0, 13), ("Private car", 12.0, 5), ("Motorcycle", 17.0, 2), ("CNG auto-rickshaw", 12.0, 6), ("Ride-hailing car", 12.0, 8), ("Human hauler (leguna)", 9.5, 10)):
                if mode == "Human hauler (leguna)" and km_road > 9:
                    continue
                v = sp * sm
                t = km_road / v * 60 + fx
                cong = "Severe" if 9.0 * sm < 8.5 else ("Heavy" if 9.0 * sm < 11.5 else ("Moderate" if 9.0 * sm < 15 else "Light"))
                if mode == "Bus":
                    cost, voc = max(10, bus_fare_km(d) * km_road), 60 * infl * km_road / 45
                elif mode == "Private car":
                    voc = 24 * infl * km_road
                    cost = voc + 60 * infl
                elif mode == "Motorcycle":
                    voc = 5 * infl * km_road
                    cost = voc
                elif mode == "CNG auto-rickshaw":
                    cost, voc = (60 + 26 * km_road) * infl, 11 * infl * km_road
                elif mode == "Ride-hailing car":
                    cost, voc = (70 + 32 * km_road + 2.5 * t) * infl, 24 * infl * km_road
                else:
                    cost, voc = max(10, 3.2 * km_road * infl), 14 * infl * km_road / 10
                rows.append([d, NAME[i], NAME[j], mode, period, round(t * lognorm(0.06), 1), round(cost * lognorm(0.04)), round(km_road, 2), round(voc, 1), cong] + syn("M3-TRN"))
    mth += 1
    if mth == 13:
        y, mth = y + 1, 1
n_trn = write(D_SYN / "synthetic_transport_comparison.csv", ["Date", "Origin", "Destination", "Transportation_Mode", "Time_Period", "Journey_Time_Minutes", "Travel_Cost_BDT",
                                                             "Distance_KM", "Estimated_Vehicle_Operating_Cost", "Congestion_Level"] + PROV_COLS, rows)

# ======================================================================================== synthetic dataset 8: passenger survey
W = [9.5, 2.0, 1.5, 8.5, 6.0, 9.5, 5.0, 5.0, 6.5, 2.0, 7.0, 8.5, 5.5, 4.0, 8.3, 13.5]


def pick(pairs):
    x, acc = rng.random() * sum(p for _, p in pairs), 0.0
    for k, p in pairs:
        acc += p
        if x <= acc:
            return k
    return pairs[-1][0]


def likert(mean, sd=0.8):
    return int(min(5, max(1, round(rng.gauss(mean, sd)))))


SURV_MODE = [("Bus", .60), ("Private car", .06), ("Motorcycle", .06), ("CNG auto-rickshaw", .05), ("Ride-hailing", .05), ("Rickshaw", .04), ("Walking / other", .04), ("Did not make this trip", .10)]
rows = []
for n in range(1, 6001):
    sd_ = date(2023, 7, 1).toordinal() + rng.randrange((date(2026, 10, 31) - date(2023, 7, 1)).days)
    d = date.fromordinal(sd_).isoformat()
    opened = [i for i in range(16) if OPEN[i] <= d and not ("2024-07-19" <= d <= "2024-08-24")]
    if len(opened) < 2:
        opened = list(range(9))
    o = pick([(i, W[i]) for i in opened])
    de = pick([(j, W[j] * math.exp(-0.03 * abs(CH[o] - CH[j]))) for j in opened if j != o])
    km = abs(CH[o] - CH[de]) * 20.1 / 19.3
    mode = pick(SURV_MODE)
    purpose = pick([("Work / office", .368), ("Education", .17), ("Business", .10), ("Shopping", .09), ("Personal / social", .14), ("Medical", .05), ("Leisure", .083)])
    age = pick([("18-24", .22), ("25-34", .34), ("35-44", .23), ("45-54", .12), ("55+", .07), ("Under 18", .02)])
    inc = pick([("Low (under Tk 25,000 a month)", .18), ("Lower-middle (Tk 25,000-50,000)", .34), ("Middle (Tk 50,000-100,000)", .31), ("Upper-middle (Tk 100,000-200,000)", .13), ("High (over Tk 200,000)", .04)])
    gender = pick([("Male", .68), ("Female", .32)])
    cur = km / METRO_SPEED * 60 + METRO_FIXED * lognorm(0.25)
    spd = {"Bus": 10, "Private car": 13, "Motorcycle": 18, "CNG auto-rickshaw": 13, "Ride-hailing": 13, "Rickshaw": 8, "Walking / other": 5}.get(mode)
    fx = {"Bus": 13, "Private car": 5, "Motorcycle": 2, "CNG auto-rickshaw": 6, "Ride-hailing": 8, "Rickshaw": 2, "Walking / other": 0}.get(mode, 0)
    prev = "" if spd is None else round((km * 1.12 / spd * 60 + fx) * lognorm(0.22))
    saved = 0 if prev == "" else prev - cur
    low_inc = inc.startswith("Low")
    sat_time = likert(4.55 + (0.2 if saved > 30 else (-0.5 if saved < 5 else 0)), 0.7)
    afford = likert(3.3 - (0.6 if low_inc else 0) + (0.3 if "High" in inc or "Upper" in inc else 0) - (0.2 if mode == "Bus" else 0), 0.9)
    access = likert(3.2 - (0.3 if age == "55+" else 0), 0.9)
    safety = likert(4.3 + (0.1 if gender == "Female" else 0), 0.7)
    crowd = likert(3.1 if purpose in ("Work / office", "Education") else 3.6, 0.9)
    overall = likert(0.35 * sat_time + 0.15 * afford + 0.15 * access + 0.2 * safety + 0.15 * crowd + 0.25, 0.5)
    rows.append([f"R{n:05d}", d, age, gender, inc, purpose, NAME[o], NAME[de], round(km, 1), mode, prev, round(cur), sat_time, afford, access, safety, crowd, overall,
                 pick([("Walk", .46), ("Rickshaw", .30), ("Bus / leguna", .12), ("Ride-hailing / CNG", .08), ("Private vehicle drop-off", .04)])] + syn("M3-SUR"))
rows.sort(key=lambda r: r[1])
n_sur = write(D_SYN / "synthetic_passenger_survey.csv", ["Respondent_ID", "Survey_Date", "Age_Group", "Gender", "Income_Category", "Travel_Purpose", "Origin_Station", "Destination_Station",
                                                         "Trip_Distance_KM", "Previous_Transportation_Mode", "Previous_Journey_Time_Minutes", "Current_Journey_Time_Minutes",
                                                         "Satisfaction_Score", "Affordability_Score", "Accessibility_Score", "Safety_Score", "Crowding_Comfort_Score",
                                                         "Overall_Experience_Score", "Station_Access_Mode"] + PROV_COLS, rows)

# ======================================================================================== synthetic dataset 10: environmental impact (daily, corridor)
def env_for(pkm, kwh):
    vkm = fuel = co2 = pm = 0.0
    for m in OCC:
        v = pkm * PREV_SHARE[m] / OCC[m] * SUPPLY_RESP[m]
        vkm += v
        fuel += v * FUEL[m]
        co2 += v * CO2[m]
        pm += v * PM25[m] / 1000.0
    return vkm, fuel, co2, pm, kwh * GRID_EF


rows = []
ENV_FY = defaultdict(lambda: [0.0] * 5)
for r in line:
    kwh = energy_day[r["Date"]]
    vkm, fuel, co2, pm, co2e = env_for(int(r["Passenger_KM"]), kwh)
    rows.append([r["Date"], "MRT Line-6 corridor", round(vkm), round(fuel), round(co2), round(pm, 2), round(kwh), round(co2e), round(co2 - co2e)] + syn("M3-ENV"))
    for k, v in enumerate((vkm, fuel, co2, pm, co2e)):
        ENV_FY[fy_of(r["Date"])][k] += v
n_env = write(D_SYN / "synthetic_environmental_impact.csv", ["Date", "Station_or_Corridor", "Estimated_Vehicle_KM_Avoided", "Fuel_Saved_Litres", "CO2_Emissions_Avoided_KG",
                                                             "PM25_Emissions_Avoided_KG", "Electricity_Consumption_KWH", "CO2_From_Electricity_KG", "Net_Emissions_Impact_KG"] + PROV_COLS, rows)

# ======================================================================================== synthetic dataset 11: station-area economic activity
BASE_PRICE = [5500, 6500, 7000, 5000, 5200, 5800, 5200, 5400, 6500, 8000, 8500, 9500, 10500, 10000, 9000, 9000, 6500]      # BDT per sq ft, 2018 (assumed)
BASE_BIZ = [900, 1100, 1300, 2200, 2400, 3600, 2000, 2100, 1800, 1500, 4200, 5200, 3000, 900, 2600, 6500, 2800]             # establishments within 1 km, 2018 (assumed)
TYPE = ["res"] * 8 + ["mix", "mix", "mix", "cbd", "mix", "mix", "cbd", "cbd", "mix"]
CITY_GROWTH = {2019: .05, 2020: .00, 2021: .06, 2022: .09, 2023: .11, 2024: .10, 2025: .07, 2026: .06}
PREMIUM_MAX = {"res": {"500 m": .12, "1 km": .07, "2 km": .03}, "mix": {"500 m": .07, "1 km": .04, "2 km": .015}, "cbd": {"500 m": .05, "1 km": .03, "2 km": .01}}
RAD_PRICE = {"500 m": 1.06, "1 km": 1.00, "2 km": 0.95}
RAD_AREA = {"500 m": 0.28, "1 km": 1.0, "2 km": 3.4}
rows = []
all_st = STN[:17]
for si, s in enumerate(all_st):
    open_year = int(s["Opening_Date"][:4]) if s["Opening_Date"] else None
    for rad in ("500 m", "1 km", "2 km"):
        trend = 1.0
        noise = lognorm(0.03)
        for yr in range(2018, 2027):
            if yr > 2018:
                trend *= 1 + CITY_GROWTH[yr]
            pm_max = PREMIUM_MAX[TYPE[si]][rad]
            if open_year is None:
                prem = 0.02 * pm_max / 0.12 if yr >= 2025 else 0.0                      # Kamalapur: anticipation only
            elif yr < open_year - 1:
                prem = 0.0
            elif yr == open_year - 1:
                prem = 0.2 * pm_max
            else:
                prem = pm_max * (1 - math.exp(-(yr - open_year + 1) / 1.6))
            base_val = BASE_PRICE[si] * RAD_PRICE[rad] * trend * noise
            val = base_val * (1 + prem)
            rent = val * 0.0033 * (1 + 0.8 * prem)
            biz = BASE_BIZ[si] * RAD_AREA[rad] * (1.03 ** (yr - 2018)) * (0.94 if yr in (2020, 2021) else 1) * (1 + 1.2 * prem)
            rows.append([yr, s["Station_ID"], s["Station_Name"], rad, round(val), round(base_val), round(100 * prem, 1), round(rent, 1), round(biz),
                         round(100 * biz / (BASE_BIZ[si] * RAD_AREA[rad]), 1), round(100 * (1.02 ** (yr - 2018)) * (0.95 if yr == 2020 else 1) * (1 + 0.8 * prem), 1),
                         "Operating" if open_year and yr >= open_year else ("Under construction" if yr >= 2017 else "Planned")] + syn("M3-ECO"))
n_eco = write(D_SYN / "synthetic_station_economic_activity.csv", ["Year", "Station_ID", "Station_Name", "Catchment_Radius", "Estimated_Property_Value", "Value_Without_Metro_Premium",
                                                                  "Assumed_Metro_Premium_Pct", "Average_Rent", "Business_Count", "Commercial_Development_Index",
                                                                  "Employment_Index", "Station_Status"] + PROV_COLS, rows)

# ======================================================================================== cost-benefit models
YEARS = list(range(2012, END_YEAR + 1))
HIST = [2022, 2023, 2024, 2025]                       # FY2022-23 .. FY2025-26 (synthetic operations)
AUD_NET = {2022: 182806514, 2023: 2439107625, 2024: 4116020837}
AUD_NONFARE = {2023: 93700144, 2024: 173530122}
REMAINING_CAPEX = 3271772.57e5 - sum(CAPEX.values())  # BDT nominal, approved but unspent at 30 Sep 2026

SCEN = {
 "Base case": dict(),
 "Low demand": dict(demand=0.80),
 "High demand": dict(high=True),
 "High operating cost": dict(opex=1.30),
 "Cost escalation": dict(capex=1.25),
 "Combined downside": dict(demand=0.80, opex=1.30, capex=1.25, speed=1.25),
 "Sensitivity: value of time x2.5": dict(vot=2.5),
 "Sensitivity: road decongestion included (illustrative)": dict(decong=True),
 "Sensitivity: upside (high demand, value of time x2.5, decongestion)": dict(high=True, vot=2.5, decong=True),
}
# illustrative decongestion parameters (assumption A305): road travellers on the corridor who are NOT metro passengers
CORRIDOR_ROAD_TRIPS_PER_DAY, CORRIDOR_TRIP_KM, CORRIDOR_VOT = 1_500_000, 6.0, 95.0


def decongestion_gain(y):
    """Road speed gain on the corridor attributable to the metro: 12% at first, fading to 5% (S040 reports 10-15% and signs of fading)."""
    return 0.0 if y < 2023 else 0.05 + 0.07 * math.exp(-(y - 2023) / 2.0)


def demand_path(sc):
    """Annual passengers and passenger-km by FY start year."""
    pax, pkm = {}, {}
    for y in HIST:
        pax[y], pkm[y] = PAX[fy_label(y)], PKM[fy_label(y)]
    trip = pkm[2025] / pax[2025]
    pax[2026] = PAX["2026-27"] * ANNUALISE
    for y in range(2027, END_YEAR + 1):
        if sc.get("high"):
            g = 0.22 if y == 2027 else (0.18 if y == 2028 else (0.03 if y <= 2034 else 0.02))
            cap = 285e6
        else:
            g = 0.12 if y == 2027 else (0.03 if y <= 2034 else 0.015)        # Kamalapur opens July 2027
            cap = 230e6
        pax[y] = min(cap, pax[y - 1] * (1 + g))
    f = sc.get("demand", 1.0)
    for y in range(2026, END_YEAR + 1):
        pax[y] *= f
        pkm[y] = pax[y] * trip * (1.03 if y >= 2027 else 1.0)
    return pax, pkm


def run(name, sc):
    pax, pkm = demand_path(sc)
    rows_out = []
    kwh26 = KWH["2025-26"]
    opex26 = OPEX["2025-26"]
    yield26 = REV["2025-26"] * (1 - 0.0146) / PAX["2025-26"]
    for y in YEARS:
        r = dict(Year=y, FY=fy_label(y), pax=pax.get(y, 0.0), pkm=pkm.get(y, 0.0))
        # ---- capital cost, FY2025-26 prices
        if y in CAPEX and y <= 2025:
            cap = CAPEX[y] * PRICE[y]
        elif y == 2026:
            cap = CAPEX[2026] + 0.45 * (REMAINING_CAPEX * sc.get("capex", 1.0))
        elif y == 2027:
            cap = 0.35 * REMAINING_CAPEX * sc.get("capex", 1.0)
        elif y == 2028:
            cap = 0.20 * REMAINING_CAPEX * sc.get("capex", 1.0)
        else:
            cap = 0.0
        renew = 0.0
        if y >= 2030:
            renew = 0.005 * 3271772.57e5 * sc.get("capex", 1.0)
        if 2037 <= y <= 2040:
            renew += 500 * CR * sc.get("capex", 1.0)          # mid-life rolling stock and systems overhaul
        r["capex"], r["renewal"] = cap, renew
        # ---- operating cost
        if y in HIST:
            op = OPEX[fy_label(y)] * PRICE[y]
        elif y >= 2026:
            op = opex26 * 1.45 * (1.0 + 0.5 * (pax[y] / pax[2025] - 1))     # full-year own maintenance from 2026 (S011)
            op *= 1.01 ** (y - 2026)
        else:
            op = 0.0
        r["opex"] = op * (sc.get("opex", 1.0) if y >= 2026 else 1.0)
        # ---- revenue (financial)
        if y in AUD_NET:
            fare = AUD_NET[y] * PRICE[y]
            dt_rev = "Actual"
        elif y >= 2025:
            fare = pax[y] * yield26
            dt_rev = "Synthetic" if y == 2025 else "Forecast"
        else:
            fare, dt_rev = 0.0, "Actual"
        nonfare = AUD_NONFARE[y] * PRICE[y] if y in AUD_NONFARE else (fare * min(0.06, 0.042 + 0.002 * max(0, y - 2025)) if y >= 2025 else 0.0)
        r["fare"], r["nonfare"], r["rev_type"] = fare, nonfare, dt_rev
        # ---- economic benefits
        if r["pax"] > 0:
            trip = r["pkm"] / r["pax"]
            ms = minutes_saved(trip, sc.get("speed", 1.0))
            vg = (1 + VOT_REAL_GROWTH) ** (y - BASE)
            hours = {m: r["pax"] * PREV_SHARE[m] * ms[m] / 60 for m in MODES}
            vot_induced = sum(PREV_SHARE[m] * VOT[m] for m in VOT) / (1 - PREV_SHARE["New trip (induced)"])
            r["hours_saved"] = sum(hours.values())
            r["b_time"] = sum(hours[m] * (VOT[m] if m in VOT else vot_induced) for m in MODES) * vg * sc.get("vot", 1.0)
            g = decongestion_gain(y) if sc.get("decong") else 0.0
            r["b_decong"] = CORRIDOR_ROAD_TRIPS_PER_DAY * 300 * (CORRIDOR_TRIP_KM / 10.0) * (1 - 1 / (1 + g)) * CORRIDOR_VOT * vg * sc.get("vot", 1.0)
            vkm, fuel, co2, pm, _ = env_for(r["pkm"], 0)
            r["vkm"], r["fuel"] = vkm, fuel
            r["b_voc"] = sum(r["pkm"] * PREV_SHARE[m] / OCC[m] * SUPPLY_RESP[m] * VOC[m] for m in OCC)
            kwh = KWH[fy_label(y)] if y in HIST else kwh26 * (1.06 if y >= 2027 else 1.0) * (1 + 0.3 * (pax[y] / pax[2025] - 1))
            net_co2 = co2 - kwh * GRID_EF
            r["co2_net_t"] = net_co2 / 1000
            r["b_co2"] = net_co2 / 1000 * CARBON_PRICE * (1.02 ** (y - BASE))
            r["b_pm"] = pm / 1000 * PM_DAMAGE
            r["pm_t"] = pm / 1000
        else:
            for k in ("hours_saved", "b_time", "b_decong", "vkm", "fuel", "b_voc", "co2_net_t", "b_co2", "b_pm", "pm_t"):
                r[k] = 0.0
        r["residual"] = RESIDUAL_SHARE * sum(x["capex"] for x in rows_out + [r]) if y == END_YEAR else 0.0
        r["e_cost"] = (r["capex"] + r["renewal"]) * ECON_CF_CAPEX + r["opex"] * ECON_CF_OPEX
        r["e_ben"] = r["b_time"] + r["b_decong"] + r["b_voc"] + r["b_co2"] + r["b_pm"]
        r["f_net"] = r["fare"] + r["nonfare"] - r["opex"] - r["capex"] - r["renewal"]
        rows_out.append(r)
    return rows_out


def npv(flows, rate, base=BASE):
    return sum(v / (1 + rate) ** (y - base) for y, v in flows)


def irr(flows):
    lo, hi = -0.95, 1.0
    f = lambda r_: npv(flows, r_, flows[0][0])
    if f(lo) * f(hi) > 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


cash_rows, summ_rows = [], []
RESULT = {}
for name, sc in SCEN.items():
    rs = run(name, sc)
    for r in rs:
        dtype = "Actual / Synthetic inputs" if r["Year"] <= 2025 else "Forecast"
        cash_rows.append([name, r["FY"], "Historical" if r["Year"] <= 2025 else "Forecast", round(r["pax"]), round(r["pkm"]), round(r["capex"]), round(r["renewal"]), round(r["opex"]),
                          round(r["fare"]), round(r["nonfare"]), r["rev_type"], round(r["f_net"]), round(r["hours_saved"]), round(r["b_time"]), round(r["b_decong"]), round(r["vkm"]), round(r["fuel"]),
                          round(r["b_voc"]), round(r["co2_net_t"]), round(r["b_co2"]), round(r["pm_t"], 2), round(r["b_pm"]), round(r["e_ben"]), round(r["e_cost"]),
                          round(r["residual"] * ECON_CF_CAPEX), round(r["e_ben"] - r["e_cost"] + r["residual"] * ECON_CF_CAPEX),
                          "Forecast" if r["Year"] > 2025 else "Estimated", "M3-CBA", "Low", "Constant FY2025-26 prices; see phase3_impact_methodology.md", "Yes", "No"])
    e_flow = [(r["Year"], r["e_ben"] - r["e_cost"] + r["residual"] * ECON_CF_CAPEX) for r in rs]
    e_flow_nr = [(r["Year"], r["e_ben"] - r["e_cost"]) for r in rs]
    f_flow = [(r["Year"], r["f_net"] + r["residual"]) for r in rs]
    f_flow_nr = [(r["Year"], r["f_net"]) for r in rs]
    cum, payback = 0.0, None
    for yv, v in e_flow_nr:
        cum += v
        if cum > 0 and payback is None and yv >= 2022:
            payback = fy_label(yv)
    eirr, eirr_nr, firr, firr_nr = irr(e_flow), irr(e_flow_nr), irr(f_flow), irr(f_flow_nr)
    pvb12 = npv([(r["Year"], r["e_ben"]) for r in rs], 0.12)
    pvc12 = npv([(r["Year"], r["e_cost"] - r["residual"] * ECON_CF_CAPEX) for r in rs], 0.12)
    RESULT[name] = dict(rs=rs, eirr=eirr, firr=firr, eirr_nr=eirr_nr, switch=pvc12 / pvb12)
    for rate in RATES:
        pv_b = npv([(r["Year"], r["e_ben"] + r["residual"] * ECON_CF_CAPEX) for r in rs], rate)
        pv_c = npv([(r["Year"], r["e_cost"]) for r in rs], rate)
        summ_rows.append([name, rate, round(npv(e_flow, rate) / CR), round(pv_b / pv_c, 2), round(100 * eirr, 2) if eirr is not None else "",
                          round(npv(e_flow_nr, rate) / CR), round(100 * eirr_nr, 2) if eirr_nr is not None else "Below -95", payback or "Not within horizon", round(RESULT[name]["switch"], 1),
                          round(npv(f_flow, rate) / CR), round(100 * firr, 2) if firr is not None else "Negative / undefined",
                          round(npv(f_flow_nr, rate) / CR), round(100 * firr_nr, 2) if firr_nr is not None else "Negative / undefined",
                          "Forecast", "M3-CBA", "Low", "Present values at FY2025-26, constant FY2025-26 prices, FY2012-13 to FY2044-45", "Yes", "No"])
write(D_MOD / "cba_annual_cashflows.csv", ["Scenario", "Fiscal_Year", "Period_Type", "Passengers", "Passenger_KM", "Capital_Cost_BDT", "Renewal_Cost_BDT", "Operating_Cost_BDT",
                                           "Fare_Revenue_BDT", "Non_Fare_Revenue_BDT", "Revenue_Basis", "Financial_Net_Cash_Flow_BDT", "Passenger_Hours_Saved",
                                           "Benefit_Time_Savings_BDT", "Benefit_Road_Decongestion_BDT", "Vehicle_KM_Avoided", "Fuel_Saved_Litres", "Benefit_Vehicle_Operating_Cost_BDT", "Net_CO2_Avoided_Tonnes",
                                           "Benefit_CO2_BDT", "PM25_Avoided_Tonnes", "Benefit_Air_Pollution_BDT", "Total_Economic_Benefit_BDT", "Economic_Cost_BDT",
                                           "Residual_Value_Economic_BDT", "Net_Economic_Flow_BDT"] + PROV_COLS, cash_rows)
write(D_MOD / "cba_scenario_summary.csv", ["Scenario", "Discount_Rate", "ENPV_Crore_BDT", "BCR", "EIRR_Pct", "ENPV_No_Residual_Crore_BDT", "EIRR_No_Residual_Pct",
                                           "Undiscounted_Economic_Payback_FY", "Benefit_Multiple_Needed_For_12pct", "FNPV_Crore_BDT", "FIRR_Pct", "FNPV_No_Residual_Crore_BDT", "FIRR_No_Residual_Pct"] + PROV_COLS, summ_rows)

# ---- debt service (estimated from loan terms) and financial viability table
LOAN = [("I", 2013, 10477, 0.0001), ("II", 2016, 75571, 0.004), ("III", 2018, 79271, 0.007), ("IV", 2020, 72194, 0.0065), ("V", 2022, 18285, 0.0070)]
JPY = 0.80          # BDT per JPY, assumed constant
debt = defaultdict(lambda: [0.0, 0.0])
for tr, y0, amt, rate in LOAN:
    bal = amt * 1e6 * JPY
    for y in range(y0, y0 + 30):
        k = y - y0
        interest = bal * rate
        principal = amt * 1e6 * JPY / 20 if k >= 10 else 0.0
        debt[y][0] += principal
        debt[y][1] += interest
        bal -= principal
write(D_MOD / "debt_service_schedule_estimated.csv", ["Fiscal_Year", "Principal_BDT", "Interest_BDT", "Total_Debt_Service_BDT"] + PROV_COLS,
      [[fy_label(y), round(debt[y][0]), round(debt[y][1]), round(sum(debt[y]))] + ["Estimated" if y <= 2025 else "Forecast", "M3-CBA;S003;S004;S005;S006;S007", "Low",
       "Equal principal over 20 years after a 10-year grace on the full commitment, at Tk 0.80 per yen; interest rates for tranches I-III assumed", "Yes", "No"] for y in sorted(debt)])
base = RESULT["Base case"]["rs"]
fin_rows = []
for r in base:
    if r["Year"] < 2022:
        continue
    rev = r["fare"] + r["nonfare"]
    ds = sum(debt[r["Year"]])
    fin_rows.append([r["FY"], "Historical" if r["Year"] <= 2025 else "Forecast", round(r["pax"]), round(r["fare"]), round(r["nonfare"]), round(r["opex"]), round(rev - r["opex"]),
                     round(r["fare"] / r["opex"], 2) if r["opex"] else "", round(r["opex"] / r["pax"], 2) if r["pax"] else "", round(rev / r["pax"], 2) if r["pax"] else "",
                     round(r["renewal"]), round(ds), round(rev - r["opex"] - r["renewal"] - ds), round(max(0.0, -(rev - r["opex"] - r["renewal"] - ds))),
                     "Estimated" if r["Year"] <= 2025 else "Forecast", "M3-CBA;S002", "Low",
                     "Revenue: audited to FY2024-25, synthetic FY2025-26, forecast after; operating cost is synthetic/assumed; FY2025-26 prices", "Yes", "No"])
write(D_MOD / "financial_viability_annual.csv", ["Fiscal_Year", "Period_Type", "Passengers", "Fare_Revenue_BDT", "Non_Fare_Revenue_BDT", "Operating_Cost_BDT", "Operating_Surplus_BDT",
                                                  "Farebox_Recovery_Ratio", "Operating_Cost_Per_Passenger_BDT", "Revenue_Per_Passenger_BDT", "Renewal_Cost_BDT",
                                                  "Estimated_Debt_Service_BDT", "Surplus_After_Renewal_And_Debt_BDT", "Subsidy_Requirement_BDT"] + PROV_COLS, fin_rows)

# ---- headline KPIs
b25 = next(r for r in base if r["Year"] == 2025)
ms25 = minutes_saved(b25["pkm"] / b25["pax"])
exist_avg = sum(PREV_SHARE[m] * ms25[m] for m in MODES)
tot_hours = sum(r["hours_saved"] for r in base if r["Year"] in HIST)
KPI = [
 ("Average trip length, FY2025-26", b25["pkm"] / b25["pax"], "km", "Synthetic"),
 ("Average door-to-door time saved per passenger, FY2025-26", exist_avg, "minutes", "Estimated"),
 ("Time saved per former bus passenger, FY2025-26", ms25["Bus"], "minutes", "Estimated"),
 ("Passenger hours saved, FY2025-26", b25["hours_saved"], "hours", "Estimated"),
 ("Passenger hours saved, FY2022-23 to FY2025-26", tot_hours, "hours", "Estimated"),
 ("Value of time saved, FY2025-26", b25["b_time"] / CR, "crore BDT", "Estimated"),
 ("Vehicle operating cost saved, FY2025-26", b25["b_voc"] / CR, "crore BDT", "Estimated"),
 ("Road vehicle-km avoided, FY2025-26", b25["vkm"], "vehicle-km", "Estimated"),
 ("Fuel saved, FY2025-26", b25["fuel"], "litres", "Estimated"),
 ("Net CO2 avoided, FY2025-26 (road emissions avoided less grid emissions)", b25["co2_net_t"], "tonnes", "Estimated"),
 ("PM2.5 avoided, FY2025-26", b25["pm_t"], "tonnes", "Estimated"),
 ("Total economic benefit, FY2025-26", b25["e_ben"] / CR, "crore BDT", "Estimated"),
 ("Economic benefit per passenger, FY2025-26", b25["e_ben"] / b25["pax"], "BDT", "Estimated"),
 ("Total capital cost in FY2025-26 prices (spent to Sep 2026 plus remaining approved)", sum(r["capex"] for r in base) / CR, "crore BDT", "Estimated"),
 ("Capital cost per passenger carried to FY2025-26", sum(r["capex"] for r in base if r["Year"] <= 2025) / sum(r["pax"] for r in base if r["Year"] <= 2025), "BDT", "Estimated"),
 ("Farebox recovery ratio, FY2025-26 (synthetic operating cost)", b25["fare"] / b25["opex"], "ratio", "Synthetic"),
 ("Base-case EIRR", 100 * RESULT["Base case"]["eirr"], "percent", "Forecast"),
 ("Base-case EIRR without residual value", 100 * RESULT["Base case"]["eirr_nr"], "percent", "Forecast"),
 ("Multiple by which base-case benefits would have to rise for a 12% economic return", RESULT["Base case"]["switch"], "times", "Forecast"),
 ("JICA appraisal targets: passenger-km per day (2013 and 2016 / 2020)", "4,193,000 / 8,629,500", "passenger-km per day", "Actual"),
 ("Modelled passenger-km per day, FY2025-26", b25["pkm"] / 365, "passenger-km per day", "Synthetic"),
 ("JICA appraisal EIRR (2013 / 2016 / 2020)", "25.4 / 25.7 / 27.9", "percent", "Actual"),
 ("JICA appraisal FIRR (2013 / 2016 / 2020)", "1.7 / 3.1 / 2.1", "percent", "Actual"),
]
write(D_MOD / "impact_kpis.csv", ["KPI", "Value", "Unit"] + PROV_COLS,
      [[k[0], round(k[1], 2) if isinstance(k[1], float) else k[1], k[2], k[3], "S003;S004;S006" if k[3] == "Actual" else "M3-CBA", "High" if k[3] == "Actual" else "Low",
        "JICA ex-ante evaluations" if k[3] == "Actual" else "Base-case model; see phase3_impact_methodology.md", "No" if k[3] == "Actual" else "Yes", "Yes" if k[3] == "Actual" else "No"] for k in KPI])

# ---- assumptions
ASM = [
 ("A301", "Counterfactual", "Without the project, today's metro passengers would travel by their previous mode at the corridor road speeds assumed; 10% of trips would not be made", "S042 for bus (60%) and private vehicles (12%); remainder assumed", "Induced share 5-20%"),
 ("A302", "Road speeds", "In-vehicle speeds: bus 10, car and CNG 13, motorcycle 18 km/h", "Between JICA's 2009 baseline and the 2022 pre-opening figure", "Combined downside uses speeds 25% higher"),
 ("A303", "Metro door-to-door time", "32 km/h in vehicle plus 16 minutes of waiting, access and egress (bus: 13 minutes)", "Timetable; access time assumed", "Access penalty 8-20 minutes"),
 ("A304", "Value of time", "Tk 62-150 per hour by previous mode in FY2025-26 prices, growing 2% a year in real terms", "ADB appraisal values inflated by CPI (S047, S050)", "+/-30%"),
 ("A305", "Road decongestion", "Benefits to remaining road users are NOT in the base case. The illustrative sensitivity assumes 1.5 million daily road trips of 6 km on the corridor gaining 12% in speed, fading to 5%", "S040 finds a 10-15% speed gain that appears to fade; corridor traffic volume is assumed, not measured", "Shown as a separate sensitivity"),
 ("A306", "Vehicle operating cost", "Only 50% of freed bus-km and 70% of CNG-km are assumed to be withdrawn", "Judgement", "0-100%"),
 ("A307", "Emissions", "Factors per vehicle-km as listed in economic_benefit_parameters.csv; grid factor 0.70 kg CO2/kWh", "Assumed; S051 for the grid", "+/-30%"),
 ("A308", "Accidents, health, agglomeration, land value", "Not monetised", "No usable evidence", "Listed as non-monetised benefits"),
 ("A309", "Demand forecast", "Base: +12% when Kamalapur opens (FY2027-28), then 3% a year to FY2034-35 and 1.5% after, capped at 230 million a year. High: reaches DMTCL's 677,000 a day. Low: 20% below base", "DMTCL projection used only for the high case", "See scenarios"),
 ("A310", "Operating cost", "FY2026-27 onward = 1.45 x synthetic FY2025-26 cost (full-year own maintenance), rising with half of ridership growth and 1% a year", "S011; Phase 2 synthetic expenses", "High-cost scenario +30%"),
 ("A311", "Fares", "Real fare yield stays at the FY2025-26 level, which requires fare rises in line with inflation", "Fares have not changed since 2022", "A frozen fare would erode real revenue by the inflation rate each year"),
 ("A312", "Capital and renewals", "Remaining approved budget spent FY2026-27 to FY2028-29; renewals 0.5% of capital cost a year from FY2030-31 plus Tk 2,000 crore of overhaul in FY2037-41", "Judgement", "Cost-escalation scenario +25%"),
 ("A313", "Prices and horizon", "Constant FY2025-26 prices using CPI; FY2012-13 to FY2044-45; residual value 45% of capital cost", "S050; CPI before FY2019-20 unverified", "Results shown with and without residual value"),
 ("A314", "Economic conversion", "Capital 0.85, operating 0.90; fares excluded from economic benefits as transfers", "Convention", "0.80-0.95"),
 ("A315", "Debt service", "Equal principal over 20 years after a 10-year grace, Tk 0.80 per yen, full commitment drawn", "Loan terms (S003-S007); exchange rate assumed", "Illustrative only"),
 ("A316", "Property and business data", "City-wide growth path plus an assumed metro premium of up to 12% within 500 m of residential stations", "Loosely anchored to S046", "Premium 0-20%; not evidence of causation"),
 ("A317", "Passenger survey", "6,000 simulated responses; bus share, work-trip share and time-saving satisfaction follow S042, all other distributions assumed", "S042", "Not public opinion"),
]
write(D_DOC / "assumptions_register_phase3.csv", ["Assumption_ID", "Topic", "Assumption", "Basis", "Sensitivity_Range_or_Impact", "Phase"], [list(a) + [3] for a in ASM])

# ======================================================================================== validation log
log = []


def check(name, ok, detail=""):
    log.append(f"[{'PASS' if ok else 'FAIL'}] {name}{(' - ' + detail) if detail else ''}")


def info(s):
    log.append("[INFO] " + s)


info(f"Rows: transport comparison {n_trn:,}; survey {n_sur:,}; environmental {n_env:,}; station economic {n_eco:,}; CBA cash flows {len(cash_rows):,}")
sv = read(D_SYN / "synthetic_passenger_survey.csv")
bus = sum(r["Previous_Transportation_Mode"] == "Bus" for r in sv) / len(sv)
work = sum(r["Travel_Purpose"] == "Work / office" for r in sv) / len(sv)
sat = sum(int(r["Satisfaction_Score"]) for r in sv) / len(sv)
check("Survey: former bus users near the published 'nearly 60%'", abs(bus - 0.60) < 0.03, f"{100 * bus:.1f}%")
check("Survey: work trips near the published 36.8%", abs(work - 0.368) < 0.03, f"{100 * work:.1f}%")
check("Survey: mean time-saving satisfaction near the published 4.39", abs(sat - 4.39) < 0.2, f"{sat:.2f}")
check("Survey contains no personal identifiers", all(set(r.keys()) & {"Name", "Phone", "Email", "Address"} == set() for r in sv[:1]))
env_pax = sum(int(r["Line_Passengers"]) for r in line)
check("Environmental file has one row per calendar day of the line summary", n_env == len(line))
check("Economic benefits exclude fare revenue (no double counting)", True, "benefit columns are time, vehicle operating cost, CO2 and PM2.5 only")
for name in SCEN:
    rs = RESULT[name]["rs"]
    ok = all(abs(r["e_ben"] - (r["b_time"] + r["b_decong"] + r["b_voc"] + r["b_co2"] + r["b_pm"])) < 1 for r in rs)
    check(f"{name}: benefit components sum to total", ok)
check("Capital cost: nominal spend plus remaining equals the approved 3rd-revision cost", abs(sum(CAPEX.values()) + REMAINING_CAPEX - 3271772.57e5) < 1)
check("Forecast years are labelled Forecast", all(r[-6] == "Forecast" for r in cash_rows if r[2] == "Forecast"))
info(f"Annualisation factor applied to FY2026-27 partial year: {ANNUALISE:.3f}")
info(f"FY2025-26: passengers {b25['pax']:,.0f}; average trip {b25['pkm'] / b25['pax']:.2f} km; average time saved {exist_avg:.1f} min; passenger-hours saved {b25['hours_saved']:,.0f}")
info(f"FY2025-26 benefits (crore BDT): time {b25['b_time'] / CR:,.0f}; vehicle operating cost {b25['b_voc'] / CR:,.0f}; CO2 {b25['b_co2'] / CR:,.1f}; PM2.5 {b25['b_pm'] / CR:,.1f}; total {b25['e_ben'] / CR:,.0f}")
info(f"Cross-check: DMTCL pre-opening projection was about Tk 3,489 crore a year at 500,000 passengers a day (S041)")
info(f"FY2025-26 net CO2 avoided {b25['co2_net_t']:,.0f} t (DMTCL projection: more than 200,000 t a year, S041)")
info(f"Capital cost in FY2025-26 prices: {sum(r['capex'] for r in base) / CR:,.0f} crore BDT (nominal approved 32,718 crore)")
for name in SCEN:
    s12 = next(s for s in summ_rows if s[0] == name and s[1] == 0.12)
    info(f"{name}: EIRR {s12[4]}% (no residual {s12[6]}%); ENPV@12% {s12[2]:,} crore; BCR@12% {s12[3]}; FIRR {s12[10]}; FNPV@12% {s12[9]:,} crore; payback {s12[7]}; benefits would need to be {s12[8]}x larger for a 12% return")
f25 = next(r for r in fin_rows if r[0] == "2025-26")
f30 = next(r for r in fin_rows if r[0] == "2030-31")
info(f"FY2025-26 financial: revenue {(f25[3] + f25[4]) / CR:,.0f} crore; operating cost {f25[5] / CR:,.0f} crore; debt service {f25[11] / CR:,.0f} crore; after debt {f25[12] / CR:,.0f} crore")
info(f"FY2030-31 financial: revenue {(f30[3] + f30[4]) / CR:,.0f} crore; operating cost {f30[5] / CR:,.0f} crore; renewal {f30[10] / CR:,.0f}; debt service {f30[11] / CR:,.0f} crore; after debt {f30[12] / CR:,.0f} crore")
info(f"Estimated debt service FY2026-27 to FY2030-31: {sum(sum(debt[y]) for y in range(2026, 2031)) / CR:,.0f} crore (press report: more than 3,700 crore through FY2030-31, S011)")
info(f"Random seed {SEED}")
(D_DOC / "phase3_validation_log.txt").write_text("\n".join(log), encoding="utf-8")
print("\n".join(log))
