# Phase 1 data quality report and gap register

Build: `python 05_Documentation/scripts/build_phase1.py` (standard library only). It regenerates every CSV and writes `phase1_validation_log.txt`. All hard checks pass.

## Classification rules applied

Every record carries `Source_ID`, `Data_Type`, `Data_Confidence`, `Methodology`, `Is_Modelled`, `Is_Verified`.

| Data_Type | Meaning in Phase 1 |
|---|---|
| Actual | Transcribed from a source at its original reporting grain |
| Estimated | Arithmetic on actual values (ratios, sums, day counts), or an unverified reference value |
| Forecast | A projection or target date quoted by a source |
| Synthetic | None in Phase 1 |

Confidence follows how the source was accessed: **High** = document read in full (S001–S006), **Medium** = web page fetched and read, **Low** = only a search-result summary was seen, or the value is unverified.

## Validation performed

| Check | Result |
|---|---|
| Provenance fields present on every record; every Source_ID resolves | Pass |
| No duplicate records in any table | Pass |
| GoB + project aid = total for each cost revision | Pass |
| Fiscal years consecutive; milestones chronological | Pass |
| Deferred-revenue roll-forward; gross − DTCA commission = net; non-fare and expense sub-totals; balance sheet balances | Pass (one Tk 1 rounding difference inside the audited statements) |
| JICA tranches I–IV sum to the 237,513 mn yen reported independently | Pass |
| Sum of annual expenditure vs the stated 82.66% financial progress | 82.61% computed; Tk 15.07 crore difference unexplained |
| No synthetic rows; forecast rows carry no observation dates | Pass |

## Quality by dataset

| Dataset | Completeness | Confidence | Main limitation |
|---|---|---|---|
| project_cost_revisions | Complete for original, 2nd, 3rd | High | 1st revision (June 2017) rests on one news report |
| project_financial_history | 15 fiscal years, total only | High | No component or GoB/loan split by year; allocation column mixes ADP and RADP; FY2026-27 is three months |
| project_cost_component_changes | Partial | Medium | Only 3rd-revision deltas; items do not sum to the official net change |
| jica_loan_agreements | 5 of 5 tranches | High | Interest rates missing for I–III; no disbursement data |
| debt_service_statistics | Partial | Medium | News-reported, rounded |
| project_milestones | 46 events | Medium | Many from Wikipedia; re-verify before citing |
| project_construction_progress | Package snapshot + 7 time points | High / Medium | No planned-progress curve, so schedule variance by package cannot be computed |
| actual_ridership_statistics | 27 published points | Medium / Low | No monthly, annual, station or hourly series; some years inferred |
| fare_structure_history | Rules + 21 station pairs | Medium / Low | Full DTCA matrix not retrieved; one conflicting quote (Farmgate–Motijheel Tk 28 vs 40) |
| actual_revenue_statistics | FY2022-23 to FY2024-25 | High | FY2025-26 not published; no monthly or station revenue |
| dmtcl_financial_statements | FY2023-24, FY2024-25 | High | Company accounts exclude most Line-6 operating costs; transcribed by eye from a scan |
| operational_performance_actual | 28 facts and service changes | Medium / Low | No daily trips, punctuality, train-km or energy records exist publicly; last-train times conflict between sources |
| station_reference | 17 stations | Medium | Shahbagh and Mirpur 10 opening dates uncertain; no coordinates yet |

## Missing datasets (not found — reported, not filled)

1. Component-wise DPP cost tables for each revision (land, civil, E&M, rolling stock, consultancy, contingency, tax).
2. Year-wise split of expenditure between GoB and JICA; loan disbursement by year; yen exposure.
3. Contract values and variation orders for CP-01 to CP-07.
4. Official monthly and annual ridership; station-wise entries and exits; hourly profiles; Ramadan, Eid and holiday patterns.
5. Full station-to-station fare matrix; share of trips by Single Journey Ticket, MRT Pass and Rapid Pass; refunds.
6. FY2025-26 ticket and non-fare revenue; monthly revenue.
7. True operating expenditure of the line: traction and station electricity, maintenance, security, cleaning. Only DMTCL's administrative expenses are published.
8. Operating statistics: scheduled and actual trips, train-km, punctuality, headway adherence, incidents, lift/escalator/platform-door availability.
9. IMED monitoring or evaluation reports for MRT-6; DMTCL annual reports as a series.
10. Verified fiscal-year exchange rates and a CPI/deflator series (needed for USD and constant-price cost).

Items 4–8 are the inputs Phase 2 will have to model; the published points in `actual_ridership_statistics.csv` and `actual_revenue_statistics.csv` are the calibration benchmarks.

## Unverified items to confirm before publication

- Exchange rates in `reference_exchange_rates_unverified.csv` (and the USD column derived from them) are analyst-recalled values, not checked against Bangladesh Bank.
- The VAT exemption after 30 June 2026 (budget proposal only).
- All rows with `Data_Confidence = Low` (search-summary sources S023, S024, S026–S031, S033).
- Rolling-stock contract value (Tk 4,257.34 crore) from Wikipedia.
- The DMTCL website (dmtcl.gov.bd) could not be opened from this environment (TLS certificate error), so its fare chart, FAQ and timetable pages were not consulted directly.

## Known limitations

- Research used public web sources only; no data request was made to DMTCL, DTCA, IMED or the Planning Commission.
- Wikipedia (S014) is a tertiary source used for the timeline and early ridership.
- The operational table uses a long format (date, metric, value) instead of the suggested daily schema, because no daily operating record is published; forcing the daily schema would have meant inventing rows.
