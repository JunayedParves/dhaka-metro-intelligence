# Data quality report — MRT Line-6 analytical database

Covers the whole package as of 14 November 2026. Phase-specific detail is in `phase1_data_quality_and_gaps.md`, `phase2_synthetic_methodology.md` and `phase3_impact_methodology.md`. Validation logs: `phase1_…`, `phase2_…`, `phase3_…` and `phase4_validation_log.txt`.

## What the database contains

29 tables (11 dimensions, 18 facts), 867,296 rows, 59 registered sources, 41 documented assumptions.

| Classification | Fact rows | Meaning |
|---|---|---|
| Actual | 78 | Published figures at their original grain |
| Synthetic | 854,672 | Simulated records |
| Estimated | 126 | Calculated from actual or synthetic inputs |
| Forecast | 210 | Future periods and quoted projections |

**More than 99.9% of the rows are simulated.** The real evidence is the 78 actual fact rows plus the reference tables in `02_Actual_Data/`. Any dashboard built on this database must show the classification.

## Validation checklist

| # | Check | Result |
|---|---|---|
| 1 | Missing values | Required keys are never blank. Blank measures are intentional: closed days, cancelled trips, non-traction energy rows, unpublished figures |
| 2 | Duplicate records | None; every table's primary key is unique |
| 3 | Primary and foreign keys | 29 primary keys and 81 foreign-key relationships validated; 0 unmatched |
| 4 | Passenger counts against capacity | No train exceeds 2,300 on any section; 1.7% of trains are at the cap |
| 5 | Ticket revenue against fare structure | Revenue = passengers × average fare on every row; fares stay within Tk 18–100; all 21 published station-pair fares reproduced |
| 6 | Financial totals against source documents | Cost revisions sum (government + loan = total); audited statement sub-totals reconcile, with one Tk 1 rounding difference inside the source; cumulative expenditure Tk 27,029.40 crore |
| 7 | Annual and monthly aggregates | Hourly = daily = line totals; cumulative ridership equals the published 313,546,306; FY2024-25 synthetic revenue is 96.6% of audited |
| 8 | Chronological consistency | Fiscal years consecutive; milestones in order; date dimension continuous from 1 July 2012 to 30 June 2045 |
| 9 | Currency conversions | Lakh and crore conversions checked. **USD figures use unverified exchange rates** |
| 10 | Synthetic never classified as actual | 0 model-generated rows carry the Actual classification |
| 11 | Forecasts not mixed with history | All cost-benefit rows after FY2025-26 are classified Forecast; none before |
| 12 | Cost-benefit arithmetic | Benefit components sum to totals in all nine scenarios; fares excluded from economic benefits |

Not tested: the SQL scripts were generated and inspected but **not executed against a SQL Server instance**. Column types are inferred from the data.

## Quality by dimension

| Dimension | Assessment |
|---|---|
| Completeness | Project cost, revisions, yearly spending, loans and audited revenue are complete. Operating data is absent from public sources and is simulated |
| Accuracy and source confidence | High for the RTHD fact sheet, DMTCL audited accounts and JICA evaluations, all read in full. Medium for press articles read in full. Low for 16 sources seen only as search-result summaries, and for all model outputs |
| Consistency | Internally consistent across all tables. Two unexplained differences against sources remain (below) |
| Timeliness | Project data to 30 September 2026; ridership to September 2026; audited accounts to 30 June 2025; FY2025-26 revenue not yet published |

## Unreconciled differences

- The RTHD fact sheet states 82.66% financial progress; its own yearly figures sum to 82.61% (Tk 15 crore difference).
- Synthetic revenue is 16% below audited sales in FY2023-24 and 38% below in FY2022-23. It was not forced to match.
- News reports give FY2022-23 revenue as "over Tk 22 crore"; the audited net figure is Tk 18.28 crore.
- The itemised changes in the third revision sum to −Tk 365 crore against an official net change of −Tk 754 crore.
- The published allocation column mixes original and revised ADP figures across years.

## Unverified assumptions with the largest effect

1. Value of travel time (Tk 62–150 per hour).
2. Road speeds without the metro (bus 10 km/h).
3. Average trip length (7.7 km), inferred from revenue per passenger.
4. Operating cost of the line, of which only staff and administration are anchored to audited figures.
5. Electricity use, anchored to one approximate monthly bill.
6. Exchange rates and CPI before FY2019-20, recalled and not checked.
7. Station entry shares, fare-product shares, punctuality and incident rates.

## Missing datasets

Component-wise cost tables; yearly split of spending between government and loan; loan disbursements; contract values for most packages; official monthly, annual, station and hourly ridership; the full official fare matrix; FY2025-26 revenue; true operating cost; operating statistics (trips, train-km, punctuality, energy); IMED monitoring reports; measured air quality, noise and traffic counts; station-area property, business and employment data.

## Known limitations

- Public sources only. DMTCL's website could not be opened from the research environment.
- Wikipedia was used for parts of the timeline and should be re-verified before citation.
- The cost-benefit model is a conservative test on direct passenger benefits, not a replacement for a full appraisal.
- Simulated data reproduces plausible patterns. It cannot reveal anything about real operations that was not put into it.
