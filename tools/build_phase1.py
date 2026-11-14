"""
Phase 1 build script - Dhaka MRT Line-6 historical project intelligence (ACTUAL data only).

Re-creates every CSV in 01_Research/, 02_Actual_Data/ and 04_Analytical_Models/ from the
values transcribed below, then runs validation checks and writes a validation log.

Standard library only.  Run:  python 05_Documentation/scripts/build_phase1.py

Rules enforced here
  * Every record carries Source_ID, Data_Type, Data_Confidence, Methodology, Is_Modelled, Is_Verified.
  * Nothing in this script is synthetic.  Data_Type is Actual, Estimated (derived by arithmetic
    from actual values, or an unverified reference value) or Forecast (a projection quoted by a source).
  * Original units are preserved in *_Original columns where a conversion was made
    (1 lakh = 100,000 BDT; 1 crore = 10,000,000 BDT).
"""
import csv
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D_RES = ROOT / "01_Research"
D_ACT = ROOT / "02_Actual_Data"
D_MOD = ROOT / "04_Analytical_Models"
D_DOC = ROOT / "05_Documentation"
for d in (D_RES, D_ACT, D_MOD, D_DOC, ROOT / "03_Synthetic_Data"):
    d.mkdir(parents=True, exist_ok=True)

PROJECT_ID = "MRT6"
ACCESS_DATE = "2026-11-13"
LAKH = 100_000
CRORE = 10_000_000

# --------------------------------------------------------------------------------------
# 1. SOURCE REGISTER
#    Access_Method: FULL = document text/pages read directly; PAGE = web page fetched and read;
#    SNIPPET = only a search-result summary was seen (page not opened) -> low confidence.
# --------------------------------------------------------------------------------------
SOURCES = [
 # id, tier, organisation, document, url, pub_date, method, notes
 ("S001", 1, "Road Transport and Highways Division (RTHD)", "Project fact sheet: Dhaka Mass Rapid Transit Development Project (Line-6), 'Up to September 2026'", "https://eservices.rthd.gov.bd/admin/docs/news/rthd_13.pdf", "2026-10 (undated; status as of 30 Sep 2026)", "FULL", "Primary source for cost revisions, year-wise DPP provision / allocation / expenditure, land, package progress. 5 pages."),
 ("S002", 1, "Dhaka Mass Transit Company Limited (DMTCL)", "Auditor's Report & Audited Financial Statements for the year ended 30 June 2025 (MABS & J Partners, signed 27 Dec 2025)", "https://objectstorage.ap-dcc-gazipur-1.oraclecloud15.com/n/axvjbnqprylg/b/V2Ministry/o/office-dmtcl/2026/1/044ae68d-62b0-4056-9f06-8be7b0be6ed2.pdf", "2025-12-27", "FULL", "Scanned PDF, 26 pages; figures transcribed by eye from pages 1-2, 14-15, 17, 19 of the statements. Unmodified opinion with emphasis-of-matter paragraphs."),
 ("S003", 2, "JICA", "Ex-Ante Evaluation: Dhaka Urban Transport Development Project (I) (L/A 20 Feb 2013)", "https://www.jica.go.jp/english/our_work/evaluation/oda_loan/economic_cooperation/c8h0vm000001rdjt-att/bangladesh_130220_02.pdf", "2013-06", "FULL", "Tranche I."),
 ("S004", 2, "JICA", "Ex-Ante Evaluation: Dhaka Mass Rapid Transit Development Project (II) (L/A 29 Jun 2016)", "https://www2.jica.go.jp/en/evaluation/pdf/2016_BD-P87_1_f.pdf", "2016", "FULL", "Tranche II."),
 ("S005", 2, "JICA", "Press release: Signing of Japanese ODA Loan Agreements with Bangladesh (14 June 2018)", "https://www2.jica.go.jp/yen_loan/pdf/en/6969/20180614_01.pdf", "2018-06-14", "FULL", "Tranche III. Terms table was garbled in text extraction; only amount and dates used."),
 ("S006", 2, "JICA", "Ex-Ante Evaluation: Dhaka Mass Rapid Transit Development Project (IV) (L/A 12 Aug 2020)", "https://www.jica.go.jp/Resource/english/news/press/2020/c8h0vm0000fahwk1-att/3DhakaMassRapidTransitDevelopmentProjectIV.pdf", "2020-11", "FULL", "Tranche IV. Interest terms taken from JICA press table as returned in search summary."),
 ("S007", 2, "JICA", "Press release: loan agreement for Dhaka Mass Rapid Transit Development Project (V) (signed 29 Mar 2022)", "https://www.jica.go.jp/english/information/press/2021/20220330_30.html", "2022-03-30", "PAGE", "Tranche V."),
 ("S008", 3, "The Business Standard", "MRT-6 cost trimmed by Tk754cr, deadline pushed to 2028", "https://www.tbsnews.net/bangladesh/mrt-6-cost-trimmed-tk754cr-deadline-pushed-2028-1277486", "2025-11-05", "PAGE", "Component changes in 3rd revision; items listed do not sum to the net change."),
 ("S009", 3, "The Daily Star", "Metro Rail Line-6: Revision proposes cost cut by Tk 755cr", "https://www.thedailystar.net/news/bangladesh/transport/news/metro-rail-line-6-revision-proposes-cost-cut-tk-755cr-4046001", "2025-11-28", "PAGE", "Physical progress as of June 2025."),
 ("S010", 3, "The Business Standard", "Metro Rail project cost rise by Tk11,486cr gets Ecnec nod", "https://www.tbsnews.net/economy/metro-rail-mrt-line-6-project-cost-goes-tk11486cr-gets-ecnec-nod-461158", "2022-07-19", "PAGE", ""),
 ("S011", 3, "Prothom Alo (English)", "MRT Line-6: Metrorail revenue inadequate to repay loans", "https://en.prothomalo.com/bangladesh/50uf5yx57u", "2025-08-06", "PAGE", "Loan repayment schedule in BDT."),
 ("S012", 3, "Prothom Alo", "Metro Rail: Nearly 500,000 passengers a day, how much revenue is generated? (English + Bangla versions)", "https://en.prothomalo.com/bangladesh/city/146wfh47ir", "2026-09-19", "PAGE", "Bangla version: https://www.prothomalo.com/bangladesh/muxrdtf8ij . Quotes DMTCL data."),
 ("S013", 3, "Prothom Alo (English)", "Metro rail extension to Kamalapur 85pc complete, service set to begin in July", "https://en.prothomalo.com/bangladesh/city/mgs7bkipic", "2026-10-26", "PAGE", ""),
 ("S014", 3, "Wikipedia", "MRT Line 6 (Dhaka Metro Rail)", "https://en.wikipedia.org/wiki/MRT_Line_6", "accessed 2026-11-13", "PAGE", "Tertiary source used for timeline, station opening dates and early ridership; each item should be re-verified against the news reference it cites."),
 ("S015", 3, "Bonik Barta (English)", "Report on DMTCL FY2023-24 audit report", "https://en.bonikbarta.com/bangladesh/U67TupknuSSiYFoU", "2025-01-03", "PAGE", ""),
 ("S016", 3, "Prothom Alo (English)", "Metro rail: Number of trips increasing", "https://en.prothomalo.com/bangladesh/city/3gv2j4ztn5", "2025-09-08", "PAGE", "Fleet utilisation and capacity."),
 ("S017", 3, "The Business Standard", "Metro rail commuters to get 10% discount by paying fares on smart cards", "https://www.tbsnews.net/bangladesh/transport/metro-rail-commuters-get-10-discount-paying-fares-smart-cards-492718", "2022-09-08", "PAGE", ""),
 ("S018", 3, "Dhaka Tribune", "All you need to know about metro rail", "https://www.dhakatribune.com/bangladesh/dhaka/330036/all-you-need-to-know-about-metro-rail", "2023-11-04", "PAGE", "Fare pairs for Agargaon-Motijheel section."),
 ("S019", 3, "The Business Standard", "MRT Line-1 slashed 91%, Line-5 down 60% in Revised ADP", "https://www.tbsnews.net/economy/mrt-line-1-slashed-91-line-5-down-60-revised-adp-1306926", "2025-12-11", "PAGE", ""),
 ("S020", 3, "The Financial Express", "Nine megaprojects eat up over 12pc of FY27 ADP", "https://today.thefinancialexpress.com.bd/last-page/nine-megaprojects-eat-up-over-12pc-of-fy27-adp-1781027825", "2026-06-10", "PAGE", ""),
 ("S021", 3, "The Business Standard", "Slow progress triggers over 54% fund cuts for 4 metro projects", "https://www.tbsnews.net/bangladesh/infrastructure/slow-progress-triggers-over-54-fund-cuts-4-metro-projects-790226", "2024-02-10", "PAGE", ""),
 ("S022", 3, "The Business Standard", "Fund cut as Dhaka's fast-track transit projects on slow spending lane", "https://www.tbsnews.net/bangladesh/infrastructure/fund-cut-dhakas-fast-track-transit-projects-slow-spending-lane-575970", "2023-01-29", "PAGE", ""),
 ("S023", 3, "Prothom Alo (English)", "Metro rail fare: Minimum Tk 20, maximum Tk 100", "https://en.prothomalo.com/bangladesh/city/vqsoalw74g", "2022-12 (not confirmed)", "SNIPPET", "Uttara North fares to Pallabi ... Agargaon seen only in a search summary."),
 ("S024", 3, "The Financial Express / BSS", "VAT exemption on metro rail extended till June 2026", "https://thefinancialexpress.com.bd/national/vat-exemption-on-metro-rail-extended-till-june-2026", "2025-12", "SNIPPET", "NBR gazette of 23 Dec 2025. FY27 budget speech (11 Jun 2026) proposed extension to 30 Jun 2028 - enactment not confirmed."),
 ("S025", 3, "The Daily Star", "What is the fare for a metro rail trip?", "https://www.thedailystar.net/node/3206586", "2022-12-27", "PAGE", "Full chart is an image on the page; only min/max were readable."),
 ("S026", 3, "BSS", "Metro rail's Motijheel to Kamalapur expected to open in July next year", "https://www.bssnews.net/news/435899", "2026-10-17", "SNIPPET", ""),
 ("S027", 3, "The Business Standard", "Metro rail extension to Kamalapur 79% complete, trial run planned early next year", "https://www.tbsnews.net/bangladesh/transport/metro-rail-extension-kamalapur-79-complete-trial-run-planned-early-next-year", "2026-09", "SNIPPET", ""),
 ("S028", 3, "Daily Observer / Daily Ittefaq", "Reports on metro operating-hour extensions (Oct 2025, Jun-Jul 2026)", "https://en.ittefaq.com.bd/8124/dhaka-metro-rail-operations-to-continue-past-9-pm", "2025-10 to 2026-07", "SNIPPET", "Reports disagree on last-train times; treat as indicative only."),
 ("S029", 3, "Khobor Sangjog", "DMTCL MD: metro passengers down 10% (press conference, Dec 2025)", "https://www.khoborsangjog.com/capital/99662/", "2025-12", "SNIPPET", "URL truncated to article id."),
 ("S030", 3, "The Business Standard", "Comparing Metro Rail's current and initial earnings not logical: DMTCL", "https://www.tbsnews.net/node/947906", "2024-09 (year inferred)", "SNIPPET", "1-18 September passenger and revenue figures; year inferred as 2024 from ridership level and article id."),
 ("S031", 3, "The Business Standard / Prothom Alo", "Metro rail sets record carrying 403,164 passengers in a day", "https://www.tbsnews.net/bangladesh/transport/metro-rail-sets-record-carrying-403164-passengers-day-1068961", "2025-02-14", "SNIPPET", ""),
 ("S032", 3, "Analyst reference values", "Fiscal-year average BDT/USD exchange rates (Bangladesh Bank period averages as recalled)", "", "", "NONE", "NOT VERIFIED against a source document in this phase. Placeholder for USD conversion only; replace with Bangladesh Bank / Bangladesh Economic Review table before publication."),
 ("S033", 3, "The Financial Express", "Govt may approve third revision of MRT-6 project tomorrow / ECNEC approval reports of 1 Dec 2025", "https://today.thefinancialexpress.com.bd/print/govt-may-approve-third-revision-of-mrt-6-project-tomorrow-1764437064", "2025-11-30", "SNIPPET", "ECNEC approval date itself is confirmed by S001."),
 ("DRV", 0, "This study", "Derived by arithmetic from actual values in this package", "", ACCESS_DATE, "DERIVED", "See Methodology column on each row."),
]
SRC = {s[0]: s for s in SOURCES}
CONF_BY_METHOD = {"FULL": "High", "PAGE": "Medium", "SNIPPET": "Low", "NONE": "Low", "DERIVED": "Medium"}


def prov(source_id, data_type="Actual", methodology="Transcribed from source", confidence=None, modelled="No", verified=None):
    """Provenance fields appended to every record."""
    primary = source_id.split(";")[0].strip()
    method = SRC[primary][6]
    if confidence is None:
        confidence = CONF_BY_METHOD[method]
    if verified is None:
        verified = "Yes" if method in ("FULL", "PAGE") and data_type == "Actual" else "No"
    return {"Source_ID": source_id, "Data_Type": data_type, "Data_Confidence": confidence,
            "Methodology": methodology, "Is_Modelled": modelled, "Is_Verified": verified}


def write_csv(path, rows):
    cols = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    return len(rows)


OUT = {}

# source register
OUT[D_RES / "source_register.csv"] = [
    {"Source_ID": s[0], "Tier": s[1], "Source_Organization": s[2], "Source_Document": s[3], "URL": s[4],
     "Publication_Date": s[5], "Access_Date": ACCESS_DATE, "Access_Method": s[6],
     "Default_Confidence": CONF_BY_METHOD[s[6]], "Notes": s[7]} for s in SOURCES]

# --------------------------------------------------------------------------------------
# 2. PROJECT COST REVISIONS  (S001, Lakh Taka)
# --------------------------------------------------------------------------------------
REV = [
 # revision, approval date, approving body, total, GoB, PA, period start, period end, length km, stations, note, source
 ("Original DPP", "2012-12-18", "ECNEC", 2198507.21, 539048.00, 1659459.21, "2012-07-01", "2024-06-30", 20.10, 16, "Uttara North-Motijheel", "S001; S008"),
 ("1st Revision", "2017-06", "Not confirmed", 2198507.21, 539048.00, 1659459.21, "2012-07-01", "2024-06-30", 20.10, 16, "No cost change reported (S008). Not listed in S001; approving body and exact date not verified.", "S008"),
 ("2nd Revision", "2022-07-19", "ECNEC", 3347199.01, 1375352.23, 1971846.78, "2012-07-01", "2025-12-31", 21.26, 17, "Adds 1.16 km Motijheel-Kamalapur extension, extra land, station plazas", "S001; S010"),
 ("3rd Revision", "2025-12-01", "ECNEC", 3271772.57, 1252196.53, 2019576.04, "2012-07-01", "2028-12-31", 21.26, 17, "Land need cut by 3.56 ha, four station plazas dropped; PA up on taka depreciation", "S001; S008; S009"),
]
rows = []
for r in REV:
    rows.append({"Project_ID": PROJECT_ID, "Project_Revision": r[0], "Approval_Date": r[1], "Approving_Body": r[2],
                 "Total_Cost_Lakh_BDT_Original": r[3], "GoB_Lakh_BDT_Original": r[4], "PA_JICA_Lakh_BDT_Original": r[5],
                 "Total_Cost_BDT": round(r[3] * LAKH), "GoB_BDT": round(r[4] * LAKH), "PA_JICA_BDT": round(r[5] * LAKH),
                 "GoB_Share_Pct": round(100 * r[4] / r[3], 2), "PA_Share_Pct": round(100 * r[5] / r[3], 2),
                 "Implementation_Start": r[6], "Implementation_End": r[7], "Route_Length_KM": r[8], "Stations": r[9],
                 "Notes": r[10],
                 **prov(r[11], confidence="High" if r[11].startswith("S001") else "Medium",
                        verified="Yes" if r[11].startswith("S001") else "No")})
OUT[D_ACT / "project_cost_revisions.csv"] = rows

# 3rd-revision component changes (S008) - deltas only; full component-wise DPP table NOT obtained
COMP = [
 ("Land acquisition", -1211.72, "3.56 ha no longer needed for station entry/exit structures"),
 ("Station plazas (Uttara North, Uttara Center, Agargaon, Motijheel)", -164.00, "Dropped"),
 ("Main line civil and station works", -116.00, ""),
 ("E&M railway management system", -90.45, ""),
 ("Rehabilitation consultancy", -2.98, ""),
 ("Salaries, allowances, office rent", 167.00, ""),
 ("General consultancy and institutional development", 222.25, ""),
 ("Foreign loan repayment (principal + construction-period interest)", 270.00, ""),
 ("Rolling stock and equipment", 561.17, ""),
]
rows = [{"Project_ID": PROJECT_ID, "From_Revision": "2nd Revision", "To_Revision": "3rd Revision", "Cost_Component": c[0],
         "Change_Crore_BDT_Original": c[1], "Change_BDT": round(c[1] * CRORE), "Notes": c[2], **prov("S008")} for c in COMP]
rows.append({"Project_ID": PROJECT_ID, "From_Revision": "2nd Revision", "To_Revision": "3rd Revision",
             "Cost_Component": "NET CHANGE (official totals)", "Change_Crore_BDT_Original": round((3271772.57 - 3347199.01) / 100, 2),
             "Change_BDT": round((3271772.57 - 3347199.01) * LAKH),
             "Notes": "Listed items sum to -364.73 crore; remaining -389.53 crore not itemised in the source",
             **prov("S001", "Estimated", "Difference of official 3rd and 2nd revision totals", "High", verified="Yes")})
OUT[D_ACT / "project_cost_component_changes.csv"] = rows

# known contract values (partial)
OUT[D_ACT / "project_contract_values.csv"] = [
 {"Project_ID": PROJECT_ID, "Contract_Package": "CP-08", "Scope": "Rolling stock: 24 six-car trains (144 cars) and depot equipment", "Contractor": "Kawasaki Heavy Industries (consortium details not verified)", "Contract_Value_Crore_BDT_Original": 4257.34, "Contract_Value_BDT": round(4257.34 * CRORE), "Contract_Year": 2017, "Notes": "Value 'about' per source", **prov("S014", confidence="Low", verified="No")},
 {"Project_ID": PROJECT_ID, "Contract_Package": "CP-07 (extension)", "Scope": "Electro-mechanical systems, Motijheel-Kamalapur", "Contractor": "Larsen & Toubro", "Contract_Value_Crore_BDT_Original": 465.00, "Contract_Value_BDT": round(465 * CRORE), "Contract_Year": "", "Notes": "Earlier bid 651 crore, negotiated down by 186 crore", **prov("S013")},
]

# --------------------------------------------------------------------------------------
# 3. YEAR-WISE FINANCIAL HISTORY  (S001, Lakh Taka)
# --------------------------------------------------------------------------------------
# FY, DPP provision, basis, allocation as published, expenditure, revision in force, original ADP (news, crore), ADP source, note
FIN = [
 ("2012-13", 35124.87, "Original DPP", 76.50, 76.50, "Original DPP", None, "", ""),
 ("2013-14", 108543.89, "Original DPP", 17300.00, 13092.00, "Original DPP", None, "", ""),
 ("2014-15", 95311.68, "Original DPP", 38000.00, 37978.00, "Original DPP", None, "", ""),
 ("2015-16", 74834.50, "Original DPP", 36595.00, 36348.98, "Original DPP", None, "", ""),
 ("2016-17", 59024.93, "Original DPP", 118242.00, 117717.40, "Original DPP", None, "", ""),
 ("2017-18", 390564.49, "Revised DPP", 309595.00, 298322.49, "1st Revision", None, "", ""),
 ("2018-19", 470390.67, "Revised DPP", 248118.00, 253962.72, "1st Revision", None, "", "Expenditure exceeds published allocation"),
 ("2019-20", 398571.95, "Revised DPP", 432673.00, 379392.33, "1st Revision", None, "", "COVID-19 disruption from March 2020"),
 ("2020-21", 329382.37, "Revised DPP", 554283.00, 428530.70, "1st Revision", None, "", "COVID-19 period"),
 ("2021-22", 198294.41, "Revised DPP", 400770.00, 400904.87, "1st Revision", None, "", ""),
 ("2022-23", 99616.13, "Revised DPP", 304900.00, 304670.47, "2nd Revision", 4963.00, "S022", "Published allocation equals original ADP less ~1,914 crore surrendered, i.e. it is the RADP figure"),
 ("2023-24", 402752.25, "Revised DPP", 342500.00, 197612.21, "2nd Revision", 3425.00, "S021", "Published allocation equals the ORIGINAL ADP; RADP proposal was 1,993 crore (S021)"),
 ("2024-25", 198834.43, "Revised DPP", 153250.00, 136375.09, "2nd Revision", None, "", ""),
 ("2025-26", 82856.75, "Revised DPP", 134744.00, 94370.04, "2nd Revision until 1 Dec 2025, then 3rd Revision", 1347.44, "S019", "Published allocation equals the ORIGINAL ADP; RADP about 1,023 crore (S019, S020)"),
 ("2026-27", 231979.13, "Revised DPP", 189949.00, 3586.04, "3rd Revision", 1899.49, "S020", "PARTIAL YEAR: expenditure July-September 2026 only"),
]
# UNVERIFIED reference exchange rates (S032) - BDT per USD, fiscal-year average
FX = {"2012-13": 79.93, "2013-14": 77.72, "2014-15": 77.67, "2015-16": 78.27, "2016-17": 79.12, "2017-18": 82.10,
      "2018-19": 84.03, "2019-20": 84.78, "2020-21": 84.81, "2021-22": 86.30, "2022-23": 99.46, "2023-24": 111.00,
      "2024-25": 120.90, "2025-26": 122.20}
rows, cum = [], 0.0
for fy, dpp, basis, alloc, exp, rev, oadp, oadp_src, note in FIN:
    cum += exp
    fx = FX.get(fy)
    rows.append({
        "Project_ID": PROJECT_ID, "Fiscal_Year": fy, "Fiscal_Year_Start": f"{fy[:4]}-07-01",
        "Fiscal_Year_End": f"{int(fy[:4]) + 1}-06-30", "Project_Revision": rev, "Cost_Component": "Total project (all components)",
        "DPP_Provision_Lakh_Original": dpp, "DPP_Basis": basis,
        "ADP_RADP_Allocation_Lakh_Original": alloc, "Actual_Expenditure_Lakh_Original": exp,
        "Approved_Budget_BDT": round(dpp * LAKH), "ADP_Allocation_BDT": round(alloc * LAKH),
        "Actual_Expenditure_BDT": round(exp * LAKH),
        "Original_ADP_Allocation_BDT_News": round(oadp * CRORE) if oadp else "", "Original_ADP_Source_ID": oadp_src,
        "Budget_Utilization_Pct": round(100 * exp / alloc, 2),
        "Expenditure_Variance_BDT": round((exp - alloc) * LAKH),
        "Expenditure_vs_DPP_Provision_Pct": round(100 * exp / dpp, 2),
        "Cumulative_Expenditure_BDT": round(cum * LAKH),
        "Cumulative_Pct_of_3rd_Revision_Cost": round(100 * cum / 3271772.57, 2),
        "Funding_Source": "GoB + JICA (year-wise GoB/PA split not published in source)",
        "Foreign_Loan_BDT": "",
        "Exchange_Rate_BDT_per_USD_UNVERIFIED": fx if fx else "",
        "Actual_Expenditure_USD_ESTIMATED": round(exp * LAKH / fx) if fx else "",
        "Is_Partial_Year": "Yes" if fy == "2026-27" else "No", "Notes": note,
        **prov("S001", methodology="Transcribed from S001 year-wise table (Lakh Taka x 100,000). Utilization, variance and cumulative columns are derived. USD column uses unverified S032 rates.")})
OUT[D_ACT / "project_financial_history.csv"] = rows
CUM_EXP_LAKH = cum

OUT[D_ACT / "reference_exchange_rates_unverified.csv"] = [
    {"Fiscal_Year": fy, "BDT_per_USD_FY_Average": v,
     **prov("S032", "Estimated", "Analyst-recalled Bangladesh Bank fiscal-year period average; NOT checked against a source document", "Low", verified="No")}
    for fy, v in FX.items()]

# --------------------------------------------------------------------------------------
# 4. JICA LOAN AGREEMENTS AND DEBT SERVICE
# --------------------------------------------------------------------------------------
LOANS = [
 ("I", "2013-02-20", 10477, "", "", "", "", 244470, "Planned full opening Dec 2021; project period Feb 2013-Aug 2022", "S003"),
 ("II", "2016-06-29", 75571, "", "", "", "", 279902, "Total planned loan 187,707 mn yen; planned full opening Jul 2021", "S004"),
 ("III", "2018-06-14", 79271, "", "", 30, 10, "", "Planned completion June 2022", "S005"),
 ("IV", "2020-08-12", 72194, 0.65, 0.01, 30, 10, 371941, "Planned opening of all sections Dec 2022; period to Dec 2024", "S006"),
 ("V", "2022-03-29", 18285, 0.70, "", 30, 10, "", "Planned completion Dec 2025", "S007"),
]
rows = [{"Project_ID": PROJECT_ID, "Tranche": l[0], "Loan_Agreement_Date": l[1], "Loan_Amount_Million_JPY": l[2],
         "Interest_Rate_Project_Pct": l[3], "Interest_Rate_Consulting_Pct": l[4], "Repayment_Period_Years": l[5],
         "Grace_Period_Years": l[6], "JICA_Total_Project_Cost_Estimate_Million_JPY": l[7], "Lender": "JICA",
         "Borrower": "Government of Bangladesh", "Executing_Agency": "DMTCL", "Notes": l[8], **prov(l[9])} for l in LOANS]
OUT[D_ACT / "jica_loan_agreements.csv"] = rows

DEBT = [
 ("Total JICA borrowing for MRT-6 (five agreements)", 19718, "crore BDT", "as reported Aug 2025", "S011", "Compare PA of 20,195.76 crore in 3rd revision (S001)"),
 ("Loan repaid since June 2023", 75, "crore BDT", "Jun 2023 - Aug 2025", "S011", "Approximate"),
 ("Repayment due in 2025", 10, "crore BDT", "calendar 2025", "S011", "Approximate"),
 ("Repayment in the year from May 2026", 465, "crore BDT", "May 2026 - Apr 2027", "S011", "Larger instalments start May 2026"),
 ("Total instalments 2026-2031", 3700, "crore BDT", "to FY2030-31", "S011; S012", "'More than'; about 740 crore a year on average"),
 ("Average annual principal repayment over 30 years", 657, "crore BDT", "to FY2061-62", "S015", "Excluding interest"),
 ("GoB long-term loan to DMTCL outstanding", 153.75, "crore BDT", "30 Jun 2025", "S002", "1% p.a., 20 years, 5-year grace, first payment 26 Dec 2027 (Note 12)"),
]
OUT[D_ACT / "debt_service_statistics.csv"] = [
    {"Project_ID": PROJECT_ID, "Metric": d[0], "Value": d[1], "Unit": d[2], "Reporting_Period": d[3], "Notes": d[5],
     **prov(d[4], "Forecast" if "2026" in d[3] or "2061" in d[3] else "Actual",
            "Quoted from source" + ("; scheduled future payment" if "2026" in d[3] or "2061" in d[3] else ""))} for d in DEBT]

# --------------------------------------------------------------------------------------
# 5. MILESTONES
# --------------------------------------------------------------------------------------
MS = [
 # date, category, component, milestone, planned date (if any), source
 ("2005", "Planning", "Network", "Strategic Transport Plan for Dhaka (Louis Berger) recommends MRT lines", "", "S014"),
 ("2010/2011", "Feasibility", "MRT6", "JICA feasibility study", "", "S014"),
 ("2011-07-11", "Environment", "MRT6", "EIA report approved by Department of Environment", "", "S003"),
 ("2012-07-01", "Approval", "MRT6", "Project implementation period begins", "", "S001"),
 ("2012-12-18", "Approval", "MRT6", "Original DPP approved by ECNEC (Tk 21,985.07 crore; completion June 2024)", "", "S001; S008"),
 ("2013-02-20", "Financing", "MRT6", "JICA loan agreement (I) signed - 10,477 mn yen", "", "S003"),
 ("2016-03-27", "Contract award", "CP-01 Depot land development", "Depot development agreement signed (Tokyu Construction)", "", "S014"),
 ("2016-06-26", "Construction", "MRT6", "Construction inaugurated", "", "S014"),
 ("2016-06-29", "Financing", "MRT6", "JICA loan agreement (II) signed - 75,571 mn yen", "", "S004"),
 ("2016-09-08", "Construction", "CP-01 Depot land development", "Physical work commenced", "", "S001"),
 ("2017-06", "Approval", "MRT6", "1st revision (no cost change)", "", "S008"),
 ("2017-08-01", "Construction", "CP-03/CP-04 Viaduct and 9 stations Uttara North-Agargaon", "Implementation commenced", "", "S001"),
 ("2017-09-13", "Construction", "CP-02 Depot civil and building works", "Physical work commenced", "", "S001"),
 ("2017-09-13", "Procurement", "CP-08 Rolling stock and depot equipment", "Implementation commenced", "", "S001"),
 ("2018-01-31", "Completion", "CP-01 Depot land development", "Completed, 9 months ahead of schedule", "2018-10 (approx.)", "S001"),
 ("2018-06-14", "Financing", "MRT6", "JICA loan agreement (III) signed - 79,271 mn yen", "", "S005"),
 ("2018-07-11", "Construction", "CP-07 Electrical and mechanical systems", "Works commenced", "", "S001"),
 ("2018-08-01", "Construction", "CP-05 Viaduct and 3 stations Agargaon-Karwan Bazar", "Physical work commenced", "", "S001"),
 ("2018-08-01", "Construction", "CP-06 Viaduct and 4 stations Karwan Bazar-Motijheel", "Physical work commenced", "", "S001"),
 ("2019-04-16", "Procurement", "CP-08 Rolling stock", "Train production started", "", "S014"),
 ("2020-08-12", "Financing", "MRT6", "JICA loan agreement (IV) signed - 72,194 mn yen", "", "S006"),
 ("2021-04", "Procurement", "CP-08 Rolling stock", "First train set arrived in Dhaka", "", "S014"),
 ("2021-08-29", "Testing", "Uttara North-Agargaon", "First trial run (Diabari to Mirpur 11)", "", "S014"),
 ("2022-01-27", "Construction", "Uttara North-Motijheel", "All viaduct spans installed", "", "S014"),
 ("2022-03-29", "Financing", "MRT6", "JICA loan agreement (V) signed - 18,285 mn yen", "", "S007"),
 ("2022-06-20", "Completion", "CP-02 Depot civil and building works", "Completed", "", "S001"),
 ("2022-07-19", "Approval", "MRT6", "2nd revision approved by ECNEC (Tk 33,471.99 crore; to Dec 2025; adds Kamalapur extension)", "", "S001; S010"),
 ("2022-12-28", "Opening", "Uttara North-Agargaon", "Inauguration of Uttara North-Agargaon section (11.73 km)", "2021-12 (JICA appraisal, full line)", "S014; S011"),
 ("2022-12-29", "Opening", "Uttara North-Agargaon", "Commercial service begins (Uttara North and Agargaon stations only)", "", "S014"),
 ("2023-01", "Construction", "Motijheel-Kamalapur extension", "Extension work began", "", "S014"),
 ("2023-03", "Procurement", "CP-08 Rolling stock", "Final train set delivered (24 sets)", "", "S014"),
 ("2023-03-31", "Opening", "Uttara North-Agargaon", "All nine stations of first section open", "", "S014"),
 ("2023-11-04", "Opening", "Agargaon-Motijheel", "Inauguration of Agargaon-Motijheel section", "", "S011; S018"),
 ("2023-11-05", "Opening", "Agargaon-Motijheel", "Commercial service to Motijheel (Farmgate, Secretariat, Motijheel stations)", "", "S014; S018"),
 ("2023-12-31", "Opening", "Uttara North-Motijheel", "All 16 stations in passenger service", "2024-06 (original DPP)", "S012; S014"),
 ("2024-06-30", "Completion", "CP-05 and CP-06", "Civil packages completed", "", "S001"),
 ("2024-07-18", "Disruption", "Operations", "Service suspended amid unrest; Mirpur-10 and Kazipara stations vandalised on 19 July", "", "S014"),
 ("2024-08-25", "Disruption", "Operations", "Service resumed excluding Mirpur-10 and Kazipara", "", "S014"),
 ("2024-09-20", "Disruption", "Operations", "Kazipara station reopened", "", "S014"),
 ("2024-10-15", "Disruption", "Operations", "Mirpur-10 station reopened", "", "S014"),
 ("2025-10-26", "Disruption", "Operations", "Bearing pad fell at Farmgate section killing a pedestrian; service briefly suspended", "", "S014"),
 ("2025-11-04", "Approval", "MRT6", "Planning Commission PEC clears 3rd revision", "", "S008"),
 ("2025-12-01", "Approval", "MRT6", "3rd revision approved by ECNEC (Tk 32,717.73 crore; to Dec 2028)", "", "S001"),
 ("2026-12-31", "Construction", "Motijheel-Kamalapur extension", "TARGET: Kamalapur station MEP and architectural works complete", "2026-12-31", "S001"),
 ("2027-07", "Opening", "Motijheel-Kamalapur extension", "TARGET: commercial opening (earlier targets: June 2025, then 1 Jan 2027)", "2025-06 (first plan)", "S013; S026"),
 ("2028-12-31", "Approval", "MRT6", "TARGET: approved project end date (3rd revision)", "2024-06-30 (original DPP)", "S001"),
]
OUT[D_ACT / "project_milestones.csv"] = [
    {"Project_ID": PROJECT_ID, "Milestone_Date": m[0], "Category": m[1], "Project_Component": m[2], "Milestone": m[3],
     "Originally_Planned_Date": m[4], "Asset_Status": "Target / under construction" if m[3].startswith("TARGET") else "Occurred",
     **prov(m[5], "Forecast" if m[3].startswith("TARGET") else "Actual",
            "Official target date quoted by source" if m[3].startswith("TARGET") else "Transcribed from source")} for m in MS]

# --------------------------------------------------------------------------------------
# 6. CONSTRUCTION PROGRESS (package snapshot + time series)
# --------------------------------------------------------------------------------------
PKG = [
 ("2026-08-31", "Depot", "CP-01", "Depot land development", "2016-09-08", "2018-01-31", 100.00, "Completed (operational asset)"),
 ("2026-08-31", "Depot", "CP-02", "Civil and building works in depot", "2017-09-13", "2022-06-20", 100.00, "Completed (operational asset)"),
 ("2026-08-31", "Uttara North-Agargaon", "CP-03 & CP-04", "11.739 km viaduct and 9 stations", "2017-08-01", "", 100.00, "Completed (operational asset)"),
 ("2026-08-31", "Agargaon-Karwan Bazar", "CP-05", "3.195 km viaduct and 3 stations", "2018-08-01", "2024-06-30", 100.00, "Completed (operational asset)"),
 ("2026-08-31", "Karwan Bazar-Motijheel", "CP-06", "4.922 km viaduct and 4 stations", "2018-08-01", "2024-06-30", 100.00, "Completed (operational asset)"),
 ("2026-08-31", "Uttara North-Motijheel", "CP-07", "Electrical and mechanical systems (Uttara-Motijheel)", "2018-07-11", "", 99.98, "Operational"),
 ("2026-08-31", "Motijheel-Kamalapur extension", "CP-07", "Electrical and mechanical systems (extension)", "", "", 58.00, "Under construction"),
 ("2026-08-31", "Rolling stock and depot equipment", "CP-08", "24 train sets and depot equipment", "2017-09-13", "", 98.45, "Trains operational; depot equipment installation ongoing"),
 ("2026-09-30", "Motijheel-Kamalapur extension", "Civil (under CP-03/04 scope per S001)", "1.16 km viaduct and Kamalapur station - civil works", "2023-01", "", 82.85, "Under construction"),
 ("2026-09-30", "Uttara North-Motijheel", "All", "Overall average physical progress", "", "", 99.67, "Operational"),
]
rows = [{"Date": p[0], "Project_ID": PROJECT_ID, "Project_Component": p[1], "Contract_Package": p[2], "Scope": p[3],
         "Progress_Type": "Physical", "Planned_Progress_Pct": "", "Actual_Progress_Pct": p[6],
         "Commencement_Date": p[4], "Planned_Completion_Date": "", "Actual_Completion_Date": p[5], "Delay_Days": "",
         "Status": p[7], **prov("S001")} for p in PKG]
SERIES = [
 ("2025-06-30", "Uttara North-Motijheel", "Physical", 99.40, "Operational", "S009"),
 ("2025-06-30", "Motijheel-Kamalapur extension", "Physical", 63.15, "Under construction", "S009"),
 ("2025-12-11", "Motijheel-Kamalapur extension", "Physical", 72.00, "Under construction", "S019"),
 ("2026-09-15", "Motijheel-Kamalapur extension", "Physical", 79.00, "Under construction", "S027"),
 ("2026-10-26", "Motijheel-Kamalapur extension", "Physical (overall infrastructure)", 85.00, "Under construction", "S013"),
 ("2026-10-26", "Motijheel-Kamalapur extension", "Physical (track laying)", 30.00, "Under construction", "S013"),
 ("2026-09-30", "MRT6 whole project", "Financial (cumulative expenditure / 3rd revision cost)", 82.66, "Mixed", "S001"),
]
for s in SERIES:
    rows.append({"Date": s[0], "Project_ID": PROJECT_ID, "Project_Component": s[1], "Contract_Package": "All", "Scope": "",
                 "Progress_Type": s[2], "Planned_Progress_Pct": "", "Actual_Progress_Pct": s[3], "Commencement_Date": "",
                 "Planned_Completion_Date": "", "Actual_Completion_Date": "", "Delay_Days": "", "Status": s[4],
                 **prov(s[5], methodology="Transcribed from source" + ("; report date approximate (September 2026)" if s[5] == "S027" else ""))})
OUT[D_ACT / "project_construction_progress.csv"] = rows

# land
LAND = [
 ("Land provided for in original DPP", 66.69, "acres", "27 ha"),
 ("Land provided for in 2nd revision (acquisition, requisition, purchase)", 111.998, "acres", "45.33 ha"),
 ("Land acquired/purchased to date", 94.44913, "acres", "As of Sep 2026"),
 ("Land under acquisition/purchase", 11.97592, "acres", "As of Sep 2026"),
 ("Land allocated by RAJUK for depot", 58.90, "acres", ""),
 ("Land allocated by RAJUK for Transit Oriented Development", 32.277, "acres", ""),
 ("Land acquired for Motijheel-Kamalapur extension", 1.8759, "acres", "Motijheel and Uttar Brahmanchiran mouza"),
]
OUT[D_ACT / "land_acquisition_statistics.csv"] = [
    {"Project_ID": PROJECT_ID, "Metric": l[0], "Value": l[1], "Unit": l[2], "As_Of": "2026-09-30", "Notes": l[3], **prov("S001")} for l in LAND]

# --------------------------------------------------------------------------------------
# 7. STATIONS (reference)
# --------------------------------------------------------------------------------------
STN = [
 (1, "Uttara North", "2022-12-29", "Operational"), (2, "Uttara Center", "2023-02-18", "Operational"),
 (3, "Uttara South", "2023-03-31", "Operational"), (4, "Pallabi", "2023-01-25", "Operational"),
 (5, "Mirpur 11", "2023-03-15", "Operational"), (6, "Mirpur 10", "2023-03-01", "Operational"),
 (7, "Kazipara", "2023-03-15", "Operational"), (8, "Shewrapara", "2023-03-31", "Operational"),
 (9, "Agargaon", "2022-12-29", "Operational"), (10, "Bijoy Sarani", "2023-12-13", "Operational"),
 (11, "Farmgate", "2023-11-05", "Operational"), (12, "Karwan Bazar", "2023-12-31", "Operational"),
 (13, "Shahbagh", "2023-12-31", "Operational"), (14, "Dhaka University", "2023-12-13", "Operational"),
 (15, "Bangladesh Secretariat", "2023-11-05", "Operational"), (16, "Motijheel", "2023-11-05", "Operational"),
 (17, "Kamalapur", "", "Under construction (target July 2027)"),
]
OUT[D_ACT / "station_reference.csv"] = [
    {"Station_ID": f"MRT6-{s[0]:02d}", "Station_Sequence": s[0], "Station_Name": s[1], "Opening_Date": s[2], "Status": s[3],
     "Section": "Uttara North-Agargaon" if s[0] <= 9 else ("Agargaon-Motijheel" if s[0] <= 16 else "Motijheel-Kamalapur"),
     "Notes": "Opening date not stated in source table; set to the date all 16 stations were in service (S012) - verify" if s[1] == "Shahbagh"
              else ("Date read from an ambiguous table layout - verify" if s[1] == "Mirpur 10" else ""),
     **prov("S014", confidence="Low" if s[1] in ("Shahbagh", "Mirpur 10") else "Medium",
            verified="No" if s[1] in ("Shahbagh", "Mirpur 10", "Kamalapur") else "Yes")} for s in STN]

# --------------------------------------------------------------------------------------
# 8. RIDERSHIP (original reporting grain preserved - NOT converted to daily series)
# --------------------------------------------------------------------------------------
RID = [
 # period start, period end, grain, metric, value, unit, scope, note, source, dtype
 ("2022-12-29", "2022-12-29", "Single day", "Passengers carried", 3857, "passengers", "Line (2 stations open)", "First day of commercial service", "S014", "Actual"),
 ("2022-12-29", "2023-01-07", "10-day period", "Passengers carried", 90000, "passengers", "Line", "Approximate", "S014", "Actual"),
 ("2023-01-01", "2023-01-31", "Month", "Passengers carried", 350000, "passengers", "Line", "Approximate ('about')", "S014", "Actual"),
 ("2023-01-01", "2023-03-31", "Quarter", "Passengers carried", 1077000, "passengers", "Line", "", "S014", "Actual"),
 ("2023-07-01", "2023-07-31", "Month (average day)", "Average daily passengers", 70000, "passengers/day", "Line (Uttara-Agargaon)", "Approximate", "S014", "Actual"),
 ("2023-11-01", "2023-11-30", "Month (average day)", "Average daily passengers", 100000, "passengers/day", "Line", "'At least'", "S014", "Actual"),
 ("2024-03-01", "2024-03-31", "Month (average day)", "Average daily passengers", 275000, "passengers/day", "Line", "Rising to 290,000 by month end", "S014", "Actual"),
 ("2024-07-01", "2024-07-17", "Period (average day)", "Average daily passengers", 360000, "passengers/day", "Line", "During quota-reform road blockades", "S014", "Actual"),
 ("2024-09-01", "2024-09-18", "18-day period", "Passengers carried", 4900000, "passengers", "Line (2 stations closed)", "'More than 49 lakh'; year inferred as 2024", "S030", "Actual"),
 ("2025-02-03", "2025-02-03", "Single day", "Passengers carried (record)", 382088, "passengers", "Line", "Record at the time", "S031", "Actual"),
 ("2025-02-13", "2025-02-13", "Single day", "Passengers carried (record)", 403164, "passengers", "Line", "Record at the time", "S031", "Actual"),
 ("2025-08-06", "2025-08-06", "Single day", "Passengers carried (record)", 456746, "passengers", "Line", "Record at the time", "S016", "Actual"),
 ("2025-08-01", "2025-08-31", "Month (average day)", "Average daily passengers", 400000, "passengers/day", "Line", "'About/over 400,000'", "S011; S016", "Actual"),
 ("2025-10-01", "2025-10-25", "Period (average day)", "Average daily passengers", 460000, "passengers/day", "Line", "Average before the 26 Oct 2025 bearing-pad incident, per DMTCL MD", "S029", "Actual"),
 ("2025-10-27", "2025-12-15", "Period (average day)", "Change in average daily passengers after incident", -10, "percent", "Line", "'About 10%' fall; end date of period approximate", "S029", "Actual"),
 ("2026-05-21", "2026-05-21", "Single day", "Passengers carried", 474635, "passengers", "Line", "Year inferred from article context", "S012", "Actual"),
 ("2026-08-20", "2026-08-20", "Single day", "Passengers carried", 478280, "passengers", "Line", "Year inferred from article context", "S012", "Actual"),
 ("2026-09-10", "2026-09-10", "Single day", "Passengers carried (record)", 499756, "passengers", "Line", "Highest single day to date", "S012", "Actual"),
 ("2026-09-13", "2026-09-13", "Single day", "Passengers carried", 480620, "passengers", "Line", "", "S012", "Actual"),
 ("2026-09-14", "2026-09-14", "Single day", "Passengers carried", 476815, "passengers", "Line", "", "S012", "Actual"),
 ("2026-09-01", "2026-09-19", "Period (floor)", "Minimum typical daily passengers", 450000, "passengers/day", "Line", "'Always remains above 450,000'", "S012", "Actual"),
 ("2022-12-29", "2026-08-31", "Cumulative since launch", "Passengers carried", 313546306, "passengers", "Line", "As of end of August 2026 per S013", "S012; S013", "Actual"),
 ("2026-09-01", "2026-09-19", "Average day", "Average daily entries", 51542, "passengers/day", "Motijheel station", "Busiest station; averaging period not stated", "S012", "Actual"),
 ("2026-09-01", "2026-09-19", "Average day", "Average daily exits", 51036, "passengers/day", "Motijheel station", "Averaging period not stated", "S012", "Actual"),
 ("", "", "Design projection", "Projected daily passengers, Uttara-Motijheel", 500000, "passengers/day", "Line", "Project estimate", "S012", "Forecast"),
 ("", "", "Projection", "Projected daily passengers (2024 DMTCL study)", 483000, "passengers/day", "Line", "", "S014", "Forecast"),
 ("", "", "Projection", "Projected daily passengers after Kamalapur extension", 677000, "passengers/day", "Line incl. Kamalapur", "DMTCL estimate", "S012; S013", "Forecast"),
]
OUT[D_ACT / "actual_ridership_statistics.csv"] = [
    {"Project_ID": PROJECT_ID, "Period_Start": r[0], "Period_End": r[1], "Reporting_Grain": r[2], "Metric": r[3], "Value": r[4],
     "Unit": r[5], "Geographic_Coverage": r[6], "Notes": r[7],
     **prov(r[8], r[9], "Published figure preserved at original grain" if r[9] == "Actual" else "Projection quoted by source",
            verified="No" if r[9] == "Forecast" else None)} for r in RID]

# --------------------------------------------------------------------------------------
# 9. FARE STRUCTURE
# --------------------------------------------------------------------------------------
FARE_RULES = [
 ("2022-12-29", "", "Rule", "Fare basis", "Tk 5 per km, set by DTCA under the Metro Rail Act 2015", "", "S017; S025"),
 ("2022-12-29", "", "Rule", "Minimum fare (BDT)", 20, "Single Journey Ticket", "S025"),
 ("2022-12-29", "", "Rule", "Maximum fare, Uttara North-Motijheel (BDT)", 100, "Single Journey Ticket", "S025"),
 ("2022-12-29", "", "Rule", "Smart-card discount (percent)", 10, "MRT Pass / Rapid Pass", "S017"),
 ("2022-12-29", "2026-06-30", "Tax", "VAT on metro tickets", "Exempt (15% VAT on AC rail waived); extended by NBR gazette 23 Dec 2025 to 30 Jun 2026", "All", "S024"),
 ("2026-07-01", "2028-06-30", "Tax", "VAT on metro tickets", "Extension to 30 Jun 2028 PROPOSED in FY27 budget speech; enactment not confirmed", "All", "S024"),
 ("2022-12-29", "", "Rule", "Fare revision since launch", "None identified in sources reviewed (not positively confirmed)", "All", "S012"),
]
rows = [{"Record_Type": f[2], "Effective_From": f[0], "Effective_To": f[1], "Item": f[3], "Value": f[4], "Fare_Product": f[5],
         "Origin_Station": "", "Destination_Station": "", "Fare_BDT": "", "Notes": "",
         **prov(f[6], verified="No" if "S024" in f[6] or "revision" in f[3] else None)} for f in FARE_RULES]
PAIRS = [
 ("Uttara North", "Pallabi", 30, "S023"), ("Uttara North", "Mirpur 11", 30, "S023"), ("Uttara North", "Mirpur 10", 40, "S023"),
 ("Uttara North", "Kazipara", 40, "S023"), ("Uttara North", "Shewrapara", 50, "S023"), ("Uttara North", "Agargaon", 60, "S023"),
 ("Uttara North", "Bijoy Sarani", 60, "S023"), ("Uttara North", "Farmgate", 70, "S018"),
 ("Uttara North", "Bangladesh Secretariat", 90, "S018"), ("Uttara North", "Motijheel", 100, "S018"),
 ("Uttara Center", "Farmgate", 70, "S018"), ("Uttara Center", "Bangladesh Secretariat", 90, "S018"), ("Uttara Center", "Motijheel", 100, "S018"),
 ("Mirpur 10", "Farmgate", 30, "S018"), ("Mirpur 10", "Karwan Bazar", 40, "S023"), ("Mirpur 10", "Bangladesh Secretariat", 50, "S018"),
 ("Mirpur 10", "Motijheel", 60, "S018"), ("Agargaon", "Farmgate", 20, "S018"), ("Agargaon", "Bangladesh Secretariat", 40, "S018"),
 ("Agargaon", "Motijheel", 50, "S018"), ("Farmgate", "Motijheel", 40, "S023"),
]
for o, d, fare, src in PAIRS:
    rows.append({"Record_Type": "Station pair", "Effective_From": "2022-12-29", "Effective_To": "", "Item": "Single journey fare",
                 "Value": "", "Fare_Product": "Single Journey Ticket", "Origin_Station": o, "Destination_Station": d, "Fare_BDT": fare,
                 "Notes": "S013 (Oct 2026) quotes Tk 28 for this pair - unexplained discrepancy" if (o, d) == ("Farmgate", "Motijheel") else "",
                 **prov(src)})
OUT[D_ACT / "fare_structure_history.csv"] = rows

# --------------------------------------------------------------------------------------
# 10. REVENUE AND DMTCL FINANCIAL STATEMENTS  (S002, BDT)
# --------------------------------------------------------------------------------------
REVN = [
 # start, end, category, product, value, note, source, dtype
 ("2022-07-01", "2023-06-30", "Fare", "Net ticket revenue (transferred to deferred revenue)", 182806514, "Opening balance of deferred revenue at 1 Jul 2023 (Note 13.1). News reports 'over Tk 22 crore' for the same year (S012) - the gap may be DTCA commission/other adjustments; not reconciled", "S002", "Actual"),
 ("2023-07-01", "2024-06-30", "Fare", "MRT ticket sale (gross)", 2462821403, "Note 19", "S002", "Actual"),
 ("2023-07-01", "2024-06-30", "Fare", "Commission to DTCA (deduction)", 23713778, "Note 19; clearing-house services", "S002", "Actual"),
 ("2023-07-01", "2024-06-30", "Fare", "Net ticket revenue (transferred to deferred revenue)", 2439107625, "Note 19", "S002", "Actual"),
 ("2024-07-01", "2025-06-30", "Fare", "MRT ticket sale (gross)", 4176915397, "Note 19", "S002", "Actual"),
 ("2024-07-01", "2025-06-30", "Fare", "Commission to DTCA (deduction)", 60894560, "Note 19", "S002", "Actual"),
 ("2024-07-01", "2025-06-30", "Fare", "Net ticket revenue (transferred to deferred revenue)", 4116020837, "Note 19", "S002", "Actual"),
 ("2023-07-01", "2024-06-30", "Non-fare", "Advertisement income", 81358071, "Note 23.06", "S002", "Actual"),
 ("2023-07-01", "2024-06-30", "Non-fare", "Space rent income", 10468584, "Note 23.06", "S002", "Actual"),
 ("2023-07-01", "2024-06-30", "Non-fare", "Shooting income", 1873489, "Note 23.06", "S002", "Actual"),
 ("2023-07-01", "2024-06-30", "Non-fare", "Total non-fare income", 93700144, "Note 23.06", "S002", "Actual"),
 ("2024-07-01", "2025-06-30", "Non-fare", "Advertisement income", 170508856, "Note 23.06", "S002", "Actual"),
 ("2024-07-01", "2025-06-30", "Non-fare", "Space rent income", 2455841, "Note 23.06.01; net of 8,375,724 prior-year unearned-revenue adjustment", "S002", "Actual"),
 ("2024-07-01", "2025-06-30", "Non-fare", "Shooting income", 565425, "Note 23.06", "S002", "Actual"),
 ("2024-07-01", "2025-06-30", "Non-fare", "Total non-fare income", 173530122, "Note 23.06", "S002", "Actual"),
 ("2022-12-29", "2023-03-29", "Fare", "Ticket revenue, first three months (news)", 62000000, "'About Tk 6.2 crore' per reference headline dated 30 Mar 2023", "S014", "Actual"),
 ("2024-09-01", "2024-09-18", "Fare", "Ticket revenue, 18-day period (news)", 206700000, "'More than Tk 20.67 crore'; year inferred as 2024", "S030", "Actual"),
 ("2025-07-01", "2026-06-30", "Fare", "FY2025-26 ticket revenue", "", "NOT YET PUBLISHED / not found. Do not fill with an estimate in this table.", "S012", "Actual"),
]
OUT[D_ACT / "actual_revenue_statistics.csv"] = [
    {"Project_ID": PROJECT_ID, "Period_Start": r[0], "Period_End": r[1], "Revenue_Category": r[2], "Item": r[3], "Amount_BDT": r[4],
     "Station_ID": "All", "Notes": r[5], **prov(r[6], r[7], verified="No" if r[4] == "" else None)} for r in REVN]

FS = [
 # statement, line, FY2024-25, FY2023-24, note
 ("Profit or loss", "Net sales revenue recognised", 0, 0, "Ticket revenue is deferred, not recognised, because Line-6 assets are not yet transferred to DMTCL"),
 ("Profit or loss", "Administrative expenses", 1030921723, 522863451, "Note 21 (FY2023-24 restated)"),
 ("Profit or loss", "  of which salary and allowances", 614591874, 399102794, "Note 21.01"),
 ("Profit or loss", "  of which office/administrative expenses", 199167664, 105084423, "Note 21.02"),
 ("Profit or loss", "  of which fees, charges and commissions", 179679521, 1248461, "Note 21.03"),
 ("Profit or loss", "  of which repairs and maintenance", 2259751, 384311, "Note 21.10"),
 ("Profit or loss", "  of which depreciation", 11333209, 11333209, "Note 21.12 (DMTCL's own small asset base only)"),
 ("Profit or loss", "Marketing / advertisement expenses", 785261, 198720, "Note 22"),
 ("Profit or loss", "Total operating expenses", 1031706984, 523062171, ""),
 ("Profit or loss", "Non-operating income", 781904900, 291143463, "Note 23; mostly interest on bank deposits, T-bonds and T-bills"),
 ("Profit or loss", "  of which non-fare income", 173530122, 93700144, "Note 23.06"),
 ("Profit or loss", "Financial expenses", 15660612, 15025520, "Note 24"),
 ("Profit or loss", "Net loss before tax", -265462695, -246944228, ""),
 ("Profit or loss", "Income tax expense", 58133204, 47687654, "Note 25"),
 ("Profit or loss", "Net loss for the year", -323595899, -294631882, ""),
 ("Financial position", "Total assets", 7981302291, 4068428544, ""),
 ("Financial position", "Investments", 6241088348, 2633559365, "Note 6"),
 ("Financial position", "Cash and bank balances", 1322632782, 1158824780, "Note 9"),
 ("Financial position", "Share capital (paid up)", 400000000, 400000000, "Tk 40 crore paid of Tk 500 crore stipulated (emphasis of matter)"),
 ("Financial position", "Retained earnings", -1034634164, -711038265, "Note 11"),
 ("Financial position", "Total equity", -634634164, -311038265, "Negative equity"),
 ("Financial position", "Borrowing from GoB", 1537500000, 1522500000, "Note 12"),
 ("Financial position", "Deferred revenue (cumulative net ticket sales)", 6737934976, 2621914139, "Note 13"),
 ("Financial position", "Total liabilities", 8615936455, 4379466809, ""),
]
rows = []
for st, line, a, b, note in FS:
    for fy, v, end in (("2024-25", a, "2025-06-30"), ("2023-24", b, "2024-06-30")):
        rows.append({"Entity": "DMTCL (company accounts, not MRT-6 project accounts)", "Fiscal_Year": fy, "Period_End": end,
                     "Statement": st, "Line_Item": line.strip(), "Is_Sub_Item": "Yes" if line.startswith("  ") else "No",
                     "Amount_BDT": v, "Notes": note, **prov("S002")})
OUT[D_ACT / "dmtcl_financial_statements.csv"] = rows

# --------------------------------------------------------------------------------------
# 11. OPERATIONAL FACTS AND SERVICE CHANGES (no daily operating records are published)
# --------------------------------------------------------------------------------------
OPS = [
 ("2017", "Fleet", "Train sets ordered", 24, "sets", "Six cars each (144 cars), Kawasaki", "S006; S014"),
 ("2025-09-08", "Fleet", "Train sets in constant operation", 13, "sets", "3 more on standby, 7 unused, 1 test train each morning", "S016"),
 ("2025-10-19", "Fleet", "Train sets expected in continuous use after hour extension", 19, "sets", "", "S028"),
 ("2025-09-08", "Capacity", "Maximum passengers per six-car train", 2300, "passengers", "Typically about 2,000", "S016"),
 ("2025-09-08", "Capacity", "Cars per train", 6, "cars", "2 trailer + 4 motor cars; platforms allow 8 cars", "S016"),
 ("2022-12-28", "Infrastructure", "Operating route length", 11.73, "km", "Uttara North-Agargaon", "S001; S014"),
 ("2023-11-05", "Infrastructure", "Operating route length", 20.10, "km", "Uttara North-Motijheel", "S001"),
 ("2022-12-28", "Infrastructure", "Electrification", 1500, "V DC overhead", "", "S014"),
 ("2022-12-28", "Infrastructure", "Maximum operating speed", 100, "km/h", "", "S014"),
 ("2023-01-01", "Service hours", "Operating window", "08:30-12:30, closed Tuesdays", "", "Initial limited service", "S014"),
 ("2023-05-31", "Service hours", "Operating days", "Daily except Friday", "", "", "S014"),
 ("2023-07-08", "Service hours", "Service extended to", "20:30", "", "", "S014"),
 ("2023-11-05", "Service hours", "Operating window", "07:30-20:30", "", "Uttara North-Motijheel only 07:30-11:30 initially", "S018"),
 ("2024-01-20", "Service hours", "Operating window", "07:00-20:40", "", "", "S014"),
 ("2024-01-20", "Headway", "Peak headway", 10, "minutes", "Off-peak 12 minutes", "S014"),
 ("2024-02-17", "Headway", "Peak headway", 8, "minutes", "Peak headway cut by 2 minutes", "S014"),
 ("2024-03-27", "Service hours", "Operating hours extended by", 1, "hour", "", "S014"),
 ("2024-09-20", "Service hours", "Friday service introduced", "from 15:00, 12-minute headway", "", "", "S014"),
 ("2025-08-06", "Headway", "Design minimum headway", 3.5, "minutes", "Not sustained because of staff shortages", "S011; S012"),
 ("2025-08-06", "Headway", "Actual headway range", "8-12", "minutes", "", "S011"),
 ("2025-10-19", "Service hours", "Operating hours extended by", 1, "hour", "Excluding Fridays; Friday start moved to 14:30", "S014; S028"),
 ("2026-07", "Service hours", "Last trains", "about 21:20 from Uttara North, 21:40 from Motijheel", "", "Sources disagree (another report: 21:50 / 22:30)", "S028"),
 ("2024-07-18", "Disruption", "Full line closure", 38, "days", "18 Jul-24 Aug 2024; damage estimated at Tk 50 crore", "S014"),
 ("2024-07-18", "Disruption", "Kazipara station closure", 64, "days", "Reopened 20 Sep 2024", "S014"),
 ("2024-07-18", "Disruption", "Mirpur 10 station closure", 89, "days", "Reopened 15 Oct 2024", "S014"),
 ("2024-09-18", "Disruption", "Section stoppage - displaced viaduct bearing pad", 11, "hours", "", "S014"),
 ("2025-10-26", "Disruption", "Bearing pad fall at Farmgate section", 1, "fatality", "Pedestrian killed; service suspended for a limited period", "S014"),
 ("2016", "Staffing", "Planned O&M employees before start of operation", 1616, "employees", "JICA appraisal estimate", "S004"),
]
OUT[D_ACT / "operational_performance_actual.csv"] = [
    {"Project_ID": PROJECT_ID, "Effective_Date": o[0], "Category": o[1], "Metric": o[2], "Value": o[3], "Unit": o[4], "Notes": o[5],
     **prov(o[6], "Estimated" if o[2] in ("Full line closure", "Kazipara station closure", "Mirpur 10 station closure") else "Actual",
            "Day count derived from closure and reopening dates" if "closure" in o[2] else "Transcribed from source")} for o in OPS]

# --------------------------------------------------------------------------------------
# 12. DERIVED INVESTMENT KPIs  (04_Analytical_Models)
# --------------------------------------------------------------------------------------
orig, rev2, rev3 = 2198507.21, 3347199.01, 3271772.57


def months(a, b):
    return (b.year - a.year) * 12 + (b.month - a.month)


plan_m = months(date(2012, 7, 1), date(2024, 7, 1))       # 144
rev3_m = months(date(2012, 7, 1), date(2029, 1, 1))       # 198
KPI = [
 ("Original approved cost", orig * LAKH, "BDT", "S001", "Actual", ""),
 ("2nd revision cost", rev2 * LAKH, "BDT", "S001", "Actual", ""),
 ("3rd (latest) revision cost", rev3 * LAKH, "BDT", "S001", "Actual", ""),
 ("Absolute cost escalation, original to 2nd revision", (rev2 - orig) * LAKH, "BDT", "DRV", "Estimated", "rev2 - original"),
 ("Cost escalation, original to 2nd revision", 100 * (rev2 - orig) / orig, "percent", "DRV", "Estimated", "(rev2 - original) / original"),
 ("Absolute cost escalation, original to 3rd revision", (rev3 - orig) * LAKH, "BDT", "DRV", "Estimated", "rev3 - original"),
 ("Cost escalation, original to 3rd revision", 100 * (rev3 - orig) / orig, "percent", "DRV", "Estimated", "(rev3 - original) / original; note scope grew by 1.16 km and one station"),
 ("Cost change, 2nd to 3rd revision", 100 * (rev3 - rev2) / rev2, "percent", "DRV", "Estimated", "(rev3 - rev2) / rev2"),
 ("GoB financing share, original", 100 * 539048.00 / orig, "percent", "DRV", "Estimated", "GoB / total"),
 ("GoB financing share, 3rd revision", 100 * 1252196.53 / rev3, "percent", "DRV", "Estimated", "GoB / total"),
 ("Foreign (JICA) financing share, original", 100 * 1659459.21 / orig, "percent", "DRV", "Estimated", "PA / total"),
 ("Foreign (JICA) financing share, 3rd revision", 100 * 2019576.04 / rev3, "percent", "DRV", "Estimated", "PA / total"),
 ("Increase in GoB contribution, original to 3rd revision", 100 * (1252196.53 - 539048.00) / 539048.00, "percent", "DRV", "Estimated", ""),
 ("Increase in JICA-financed portion, original to 3rd revision", 100 * (2019576.04 - 1659459.21) / 1659459.21, "percent", "DRV", "Estimated", "In BDT terms; reflects taka depreciation as well as scope"),
 ("Cost per km, original (20.10 km)", orig * LAKH / 20.10, "BDT per km", "DRV", "Estimated", "original cost / 20.10 km"),
 ("Cost per km, 3rd revision (21.26 km)", rev3 * LAKH / 21.26, "BDT per km", "DRV", "Estimated", "rev3 cost / 21.26 km; includes depot, rolling stock, land, loan repayment items"),
 ("Cost per station, original (16 stations)", orig * LAKH / 16, "BDT per station", "DRV", "Estimated", "whole-project cost / stations (not station construction cost)"),
 ("Cost per station, 3rd revision (17 stations)", rev3 * LAKH / 17, "BDT per station", "DRV", "Estimated", "whole-project cost / stations (not station construction cost)"),
 ("Cumulative expenditure to 30 Sep 2026 (sum of year-wise table)", CUM_EXP_LAKH * LAKH, "BDT", "DRV", "Estimated", "Sum of S001 annual expenditure; S001 states 82.66% financial progress, implying ~2,704,447 lakh"),
 ("Financial progress against 3rd revision (sum of year-wise table)", 100 * CUM_EXP_LAKH / rev3, "percent", "DRV", "Estimated", "cumulative expenditure / rev3 cost"),
 ("Remaining approved budget after 30 Sep 2026", (rev3 - CUM_EXP_LAKH) * LAKH, "BDT", "DRV", "Estimated", "rev3 cost - cumulative expenditure"),
 ("Lifetime budget utilization FY2012-13 to FY2025-26", 100 * sum(f[4] for f in FIN[:-1]) / sum(f[3] for f in FIN[:-1]), "percent", "DRV", "Estimated", "sum expenditure / sum published allocation, full years only"),
 ("Original planned implementation period", plan_m, "months", "DRV", "Estimated", "Jul 2012 - Jun 2024"),
 ("Current approved implementation period", rev3_m, "months", "DRV", "Estimated", "Jul 2012 - Dec 2028"),
 ("Project end-date slippage", rev3_m - plan_m, "months", "DRV", "Estimated", "Dec 2028 vs Jun 2024"),
 ("Project end-date slippage", 100 * (rev3_m - plan_m) / plan_m, "percent of original duration", "DRV", "Estimated", ""),
 ("Full Uttara-Motijheel opening vs JICA 2013 appraisal target (Dec 2021)", months(date(2021, 12, 1), date(2023, 12, 1)), "months late", "DRV", "Estimated", "All 16 stations in service 31 Dec 2023 (S012) vs Dec 2021 (S003)"),
 ("Full Uttara-Motijheel opening vs original DPP end date (Jun 2024)", months(date(2024, 6, 1), date(2023, 12, 1)), "months (negative = early)", "DRV", "Estimated", "Original 20.1 km scope was in service before the original DPP end date"),
 ("Kamalapur extension opening slippage (June 2025 plan vs July 2027 target)", months(date(2025, 6, 1), date(2027, 7, 1)), "months", "DRV", "Forecast", "Depends on July 2027 target being met (S013, S026)"),
 ("JICA loan commitments, five tranches", sum(l[2] for l in LOANS), "million JPY", "DRV", "Estimated", "Sum of S003-S007 tranche amounts"),
 ("Net ticket revenue FY2023-24 to FY2024-25 growth", 100 * (4116020837 - 2439107625) / 2439107625, "percent", "DRV", "Estimated", "From S002; FY2023-24 had the full line for only ~8 months"),
 ("Non-fare income as share of net ticket revenue, FY2024-25", 100 * 173530122 / 4116020837, "percent", "DRV", "Estimated", "From S002"),
 ("DTCA commission as share of gross ticket sales, FY2024-25", 100 * 60894560 / 4176915397, "percent", "DRV", "Estimated", "From S002"),
 ("Average revenue per passenger, 1-18 Sep 2024", 206700000 / 4900000, "BDT per passenger", "DRV", "Estimated", "From S030 snippet values; both are lower bounds ('more than') - low confidence"),
 ("Cumulative net ticket revenue to 30 Jun 2025", 6737934976, "BDT", "S002", "Actual", "Deferred revenue balance, Note 13"),
 ("Cumulative net ticket revenue as share of 3rd revision project cost", 100 * 6737934976 / (rev3 * LAKH), "percent", "DRV", "Estimated", "Illustrative only; not a cost-recovery measure"),
]
OUT[D_MOD / "project_cost_analysis_kpis.csv"] = [
    {"Project_ID": PROJECT_ID, "KPI": k[0], "Value": round(k[1], 2), "Unit": k[2], "Formula_or_Note": k[5],
     **prov(k[3], k[4], "Arithmetic on actual values" if k[3] == "DRV" else "Transcribed from source",
            "High" if k[3] != "DRV" else ("Low" if "S030" in k[5] else "Medium"), verified="Yes" if k[3] != "DRV" else "No")} for k in KPI]

# --------------------------------------------------------------------------------------
# 13. ASSUMPTIONS REGISTER (Phase 1 only)
# --------------------------------------------------------------------------------------
ASM = [
 ("A001", "Unit conversion", "1 lakh = 100,000 BDT; 1 crore = 10,000,000 BDT; fiscal year runs 1 July - 30 June", "Standard", "None"),
 ("A002", "Allocation column", "S001 'ADP/Revised RADP Allocation' is used as published. Cross-checks show it is the RADP in FY2022-23 but the original ADP in FY2023-24 and FY2025-26, so utilization rates are not on a uniform basis", "Evidence from S019-S022", "Utilization for FY2023-24 would be ~99% on the 1,993 crore RADP proposal instead of 57.7%"),
 ("A003", "Revision in force", "Each fiscal year is tagged with the revision in force for most of that year; the 1st revision is dated June 2017 from a news source only", "S008", "Labelling only"),
 ("A004", "Exchange rates", "USD conversions use unverified analyst-recalled fiscal-year average rates (S032)", "Not verified", "Replace with Bangladesh Bank table; USD totals may move by a few percent"),
 ("A005", "Inferred years", "Single-day ridership figures of 21 May, 20 Aug, 13 Sep, 14 Sep are assigned to 2026 and the 1-18 September period to 2024 by context", "Article dates", "If wrong, affects calibration benchmarks only"),
 ("A006", "Station opening dates", "Shahbagh opening date set to 31 Dec 2023 (date all 16 stations were in service); Mirpur 10 date read from an ambiguous table", "S012, S014", "Affects station-level synthetic series start dates in Phase 2"),
 ("A007", "Cost per km / station", "Whole-project cost (including depot, trains, land, consultancy, loan repayment items) divided by route length or station count", "Convention", "Not comparable with civil-works-only benchmarks"),
 ("A008", "Constant-price cost", "NOT computed in Phase 1: needs a verified BBS CPI or GDP-deflator series", "Gap", "Deferred to Phase 3"),
 ("A009", "Company vs project accounts", "DMTCL company accounts (S002) exclude most MRT-6 operating costs (electricity, maintenance, loan service), which are still paid from the project budget (S002 Note 3.13); they therefore understate true operating cost", "S002", "Farebox recovery cannot be computed from actual data yet"),
]
OUT[D_DOC / "assumptions_register.csv"] = [
    {"Assumption_ID": a[0], "Topic": a[1], "Assumption": a[2], "Basis": a[3], "Sensitivity_or_Impact": a[4], "Phase": 1} for a in ASM]

# --------------------------------------------------------------------------------------
# WRITE + VALIDATE
# --------------------------------------------------------------------------------------
log = []
REQ = ["Source_ID", "Data_Type", "Data_Confidence", "Methodology", "Is_Modelled", "Is_Verified"]
EXEMPT = {"source_register.csv", "assumptions_register.csv"}


def check(name, ok, detail=""):
    log.append(f"[{'PASS' if ok else 'FAIL'}] {name}{(' - ' + detail) if detail else ''}")
    return ok


all_ok = True
for path, rows in OUT.items():
    n = write_csv(path, rows)
    log.append(f"wrote {path.relative_to(ROOT)}  ({n} rows)")
    if path.name in EXEMPT:
        continue
    for r in rows:
        missing = [c for c in REQ if r.get(c, "") == ""]
        if missing:
            all_ok &= check(f"{path.name} provenance fields", False, f"missing {missing} in {r}")
            break
        for sid in r["Source_ID"].split(";"):
            if sid.strip() not in SRC:
                all_ok &= check(f"{path.name} source id", False, sid)
        if r["Data_Type"] not in ("Actual", "Estimated", "Forecast"):
            all_ok &= check(f"{path.name} data type", False, r["Data_Type"])
    # duplicates
    seen = set()
    dup = 0
    for r in rows:
        key = tuple(str(v) for k, v in r.items() if k not in REQ and k != "Notes")
        dup += key in seen
        seen.add(key)
    all_ok &= check(f"{path.name}: no duplicate records, provenance complete, source ids resolve", dup == 0, f"{dup} duplicates" if dup else "")

for r in REV:
    all_ok &= check(f"GoB + PA = total ({r[0]})", abs(r[4] + r[5] - r[3]) < 0.011, f"{r[4] + r[5]:.2f} vs {r[3]:.2f}")
all_ok &= check("Deferred revenue roll-forward FY2023-24", 182806514 + 2439107625 == 2621914139)
all_ok &= check("Deferred revenue roll-forward FY2024-25", 2621914139 + 4116020837 == 6737934976)
all_ok &= check("Gross ticket sale - DTCA commission = net (FY2023-24)", 2462821403 - 23713778 == 2439107625)
all_ok &= check("Gross ticket sale - DTCA commission = net (FY2024-25)", 4176915397 - 60894560 == 4116020837)
all_ok &= check("Non-fare components sum (FY2024-25)", 170508856 + 2455841 + 565425 == 173530122)
all_ok &= check("Non-fare components sum (FY2023-24)", 81358071 + 10468584 + 1873489 == 93700144)
all_ok &= check("Operating expenses = admin + marketing (FY2024-25)", 1030921723 + 785261 == 1031706984)
all_ok &= check("Loss before tax (FY2024-25), within Tk 1 rounding", abs(-1031706984 + 781904900 - 15660612 - -265462695) <= 1,
                "components give -265,462,696; statement prints -265,462,695 (Tk 1 rounding difference in the source)")
all_ok &= check("Loss before tax (FY2023-24)", -523062171 + 291143463 - 15025520 == -246944228)
all_ok &= check("Net loss (FY2024-25)", -265462695 - 58133204 == -323595899)
all_ok &= check("Equity + liabilities = assets (30 Jun 2025)", -634634164 + 8615936455 == 7981302291)
all_ok &= check("JICA tranches I-IV = 237,513 mn yen (matches Daily Observer report)", sum(l[2] for l in LOANS[:4]) == 237513)
implied = 0.8266 * rev3
check("Cumulative expenditure vs stated 82.66% financial progress",
      abs(CUM_EXP_LAKH - implied) / implied < 0.002,
      f"sum of years {CUM_EXP_LAKH:,.2f} lakh = {100 * CUM_EXP_LAKH / rev3:.2f}%; stated 82.66% = {implied:,.0f} lakh (difference {implied - CUM_EXP_LAKH:,.0f} lakh, unexplained)")
fys = [f[0] for f in FIN]
all_ok &= check("Fiscal years consecutive and unique", fys == [f"{y}-{str(y + 1)[2:]}" for y in range(2012, 2027)])
ms_dates = [m[0] for m in MS if len(m[0]) == 10]
all_ok &= check("Milestones in chronological order", ms_dates == sorted(ms_dates))
syn = sum(1 for rows in OUT.values() for r in rows if r.get("Data_Type") == "Synthetic")
all_ok &= check("No synthetic records in Phase 1 outputs", syn == 0)
fc_in_actual = [r for r in OUT[D_ACT / "actual_ridership_statistics.csv"] if r["Data_Type"] == "Forecast" and r["Period_Start"]]
all_ok &= check("Forecast ridership rows carry no observation dates", not fc_in_actual)

log.append("")
log.append("OVERALL: " + ("ALL HARD CHECKS PASSED" if all_ok else "SOME CHECKS FAILED"))
(D_DOC / "phase1_validation_log.txt").write_text("\n".join(log), encoding="utf-8")
print("\n".join(log))
