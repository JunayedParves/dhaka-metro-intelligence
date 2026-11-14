# Phase 2 — synthetic operational data: methodology and validation

**These datasets are simulations, not observations.** DMTCL publishes no daily, hourly, station-level, train-level, energy or maintenance records. Every row is labelled `Data_Type = Synthetic` (four documented real incidents are labelled `Actual`; the fare matrix is `Estimated`). Published figures were used only as calibration targets.

Rebuild: `python 05_Documentation/scripts/build_phase2.py` then `python 05_Documentation/scripts/validate_phase2.py` (standard library, seed 20261113, about 40 seconds). `convert_to_parquet.py` is optional and needs pyarrow.

## Datasets (`03_Synthetic_Data/`)

| File | Grain | Rows |
|---|---|---|
| synthetic_daily_ridership.csv | Date × Station | 18,103 |
| synthetic_hourly_ridership.csv | Date × Hour × Station × Direction | 503,221 |
| synthetic_ticket_revenue.csv | Date × Station × Fare product | 54,309 |
| synthetic_train_operations.csv | One train run | 246,302 |
| synthetic_energy_consumption.csv | Date × Component | 3,990 |
| synthetic_maintenance_incidents.csv | One incident or work order | 3,316 |
| synthetic_monthly_opex.csv | Month × Expense category | 480 |
| synthetic_daily_line_summary.csv | Date (line totals, service pattern, punctuality) | 1,416 |
| estimated_fare_matrix.csv | Origin × Destination | 240 |

`04_Analytical_Models/synthetic_monthly_operating_summary.csv` rolls these up by month. Parquet copies are in the `parquet` sub-folders.

Column notes: `Passenger_Entry` summed over stations is the number of passengers carried; `Total_Passengers` is entries plus exits at a station (throughput), so it must not be summed across stations to get ridership. `Direction` in the hourly file is the direction of the train boarded or alighted from. `Peak_Passengers` counts entries in the hours starting 08, 09, 17, 18 and 19.

## How the data are generated

1. **Service calendar.** Opening dates of each station, operating hours, Tuesday then Friday closures, Friday afternoon service from 20 September 2024, the 19 July–24 August 2024 shutdown, the later reopening of Kazipara and Mirpur 10, and the October 2025 hour extension are taken from Phase 1. Headways by period were chosen to reproduce published trips per day.
2. **Line ridership.** A working-day trend passes through 36 anchor levels set from published averages. It is multiplied by day-of-week, holiday, Eid, Ramadan and weather factors and 2.5% random noise. Nine published single-day totals are inserted exactly. No other day may exceed the record standing on that date. A single scale factor (0.9956) then makes the cumulative total to 31 August 2026 equal the published 313,546,306.
3. **Stations.** Daily entries are split by land-use weights (residential, mixed, business district), with different weekend mixes and a February uplift at Shahbagh and Dhaka University.
4. **Hours and destinations.** Each station's entries follow a morning-peaked, evening-peaked or mixed hourly profile (Ramadan moves the evening peak earlier). Destinations come from a gravity model with distance deterrence, balanced so that each station's exits match its entries over a day. This gives directional flows, exits and the load on every section of the line.
5. **Fares and revenue.** A modelled fare matrix (Tk 5 per km on fitted fare-distances, rounded up to Tk 10, minimum 20, maximum 100) reproduces all 21 published station-pair fares. Revenue is the origin–destination flow times the fare, with a 10% discount on card products. Product shares are assumed.
6. **Trains.** A timetable is generated from the service pattern. Each run gets a delay (random, incident-driven, and crowding-related) and may be cancelled during incidents longer than 30 minutes. Hourly directional boardings are shared among the trains running in that hour.
7. **Incidents and maintenance.** Service-affecting incidents and routine work orders arrive at random with log-normal durations and costs. Long incidents reduce that day's ridership.
8. **Energy.** Traction energy is proportional to train-km; stations and the depot have base loads that vary with service hours and season. Cost uses an assumed tariff.
9. **Operating expenses.** Electricity and maintenance are derived from the datasets above. Staff and administration follow DMTCL's audited FY2023-24 and FY2024-25 levels. Maintenance and equipment costs step up from January 2026, when DMTCL was due to take them over. Other categories are assumed.

All parameters and their sensitivity ranges are in `assumptions_register_phase2.csv`.

## Calibration results

| Benchmark (published) | Published | Synthetic |
|---|---|---|
| Cumulative passengers to 31 Aug 2026 | 313,546,306 | 313,546,306 (forced) |
| Nine single-day totals | as published | identical (forced) |
| January 2023 passengers | about 350,000 | 334,452 |
| January–March 2023 passengers | 1,077,000 | 1,055,970 |
| 1–18 September 2024 passengers | more than 4,900,000 | 5,027,096 |
| 1–18 September 2024 ticket revenue | more than Tk 20.67 crore | Tk 21.46 crore |
| Motijheel daily entries / exits, September 2026 | 51,542 / 51,036 | 49,607 / 53,085 |
| Trips per day: weekday early 2025 / Friday / September 2025 / 2026 | 198 / 60 / 238 / about 297 | 198 / 60 / 234 / 304 |
| Gross ticket sales FY2024-25 | Tk 417.69 crore | Tk 403.44 crore (ratio 0.966) |
| Gross ticket sales FY2023-24 | Tk 246.28 crore | Tk 207.00 crore (ratio 0.841) |
| Net ticket revenue FY2022-23 | Tk 18.28 crore | Tk 11.41 crore (ratio 0.624) |
| Monthly electricity bill, early 2025 | about Tk 6 crore | Tk 5.57 crore (February 2025) |

Only the first two rows were forced. The distance-deterrence parameter was tuned on FY2024-25 revenue alone.

**Revenue for FY2022-23 and FY2023-24 was deliberately not forced to match.** The model produces less revenue than the audited accounts in those years. To close the gap, the average fare paid would have to exceed what the fare table allows for the ridership the published figures support. Likely explanations are card top-ups and deposits counted as sales when paid, or under-estimated early ridership; neither can be verified. Treat synthetic revenue before July 2024 as understated by roughly 15–40%.

## Internal consistency checks (all pass)

- Hourly rows sum to the daily station figures; line entries equal line exits every day.
- Ticket passenger counts equal station entries; gross = passengers × average fare; net = gross − refunds; average fares stay within Tk 18–100.
- Train passenger loads sum to the day's line ridership on every day.
- No un-pinned day exceeds the standing record; September 2026 working days are all above 450,000.

## Known limitations

- **Capacity.** 4,154 of 246,032 operated trains (1.7%) reach the 2,300-passenger cap on their busiest section, almost all southbound between 08:00 and 10:00, peaking at 8% of trains in March 2025 before the modelled headway cut. On these trains the section load is capped, so the model implies passengers left behind that it does not track.
- **Punctuality (94.8% on time, 0.71 minutes average delay), incident rates, maintenance costs, product shares and most expense categories are assumptions with no published benchmark.** They produce plausible patterns, not estimates of DMTCL's performance.
- **Farebox recovery in the monthly summary is not a finding.** It divides synthetic revenue by largely assumed costs and excludes depreciation and debt service.
- Weather is drawn from monthly climate probabilities, not observed weather. 2026 Ramadan and Eid dates depend on moon sighting.
- Passengers are assumed to exit in the clock hour they enter; travel time is not modelled.
- Service hours for 2023 and exact last-train times are partly unverified (assumption A205).
- Sources S034 (electricity bill) and S035 (trips per day) were seen only as search-result summaries.
