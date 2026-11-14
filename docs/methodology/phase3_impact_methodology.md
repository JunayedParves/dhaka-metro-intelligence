# Phase 3 — economic, social and environmental impact: methodology and results

Rebuild: `python 05_Documentation/scripts/build_phase3.py` (needs the Phase 1 and Phase 2 outputs; standard library; seed 20261114).

**Status of the numbers.** The evidence tables in `02_Actual_Data/` are transcribed from sources. Everything else is modelled: the four datasets in `03_Synthetic_Data/` are simulations, historical benefit estimates are `Estimated`, and FY2026-27 onward is `Forecast`. The cost-benefit results depend on assumptions that could not be checked against DMTCL or JICA working papers and should be read as an order-of-magnitude test, not a definitive appraisal.

## 1. Evidence collected (Actual)

| Topic | Finding | Source |
|---|---|---|
| Road travel time, Uttara–Motijheel | 105 minutes (2009 baseline), 208 minutes (2022 pre-opening figure), about 120 minutes (2026 press); metro 36–40 minutes | S004, S041, S045 |
| Effect on road traffic | Vehicle speeds on roads within 500 m of the line rose 10–15% relative to control corridors up to June 2024; the gain appeared to fade as traffic was induced | S040 (JICA Ogata Research Institute, not peer-reviewed) |
| Who uses the metro | Nearly 60% came from buses, about 12% from private vehicles; 36.8% of trips are work-related (survey July–October 2023, n = 1,397) | S042 |
| Satisfaction | Travel-time saving rated 4.39 out of 5; reliability, comfort, cleanliness and safety above 4.0; feeder services and cost rated lowest | S042 |
| Share of city travel | About 1% of Dhaka's daily trips | S045 |
| Property | Reports of Mirpur rents up 27% and prices up 8.6% (c. 2023), and flat prices in Uttara and Mirpur up about 25% in a year (c. 2024); developers also cite construction costs and planning rules | S046 (low confidence) |
| JICA appraisal | EIRR 25.4% / 25.7% / 27.9% and FIRR 1.7% / 3.1% / 2.1% (2013 / 2016 / 2020); target 4.19 million passenger-km a day, raised to 8.63 million in 2020 | S003, S004, S006 |
| DMTCL pre-opening projection | Tk 3,489 crore a year in time and vehicle-cost savings; more than 200,000 tonnes of CO2 a year | S041 |

Not found: measured air-quality, noise or electricity data; station-level property transactions, business counts or employment; any survey on access for people with disabilities.

## 2. Synthetic datasets

| File | Grain | Rows | Basis |
|---|---|---|---|
| synthetic_passenger_survey.csv | One simulated respondent | 6,000 | Bus share, work-trip share and time-saving satisfaction follow S042; all other distributions assumed. No personal identifiers. |
| synthetic_transport_comparison.csv | Month × origin–destination × mode × peak/off-peak, January 2019 – November 2026 | 15,664 | 14 station pairs, metro plus six road modes. Includes the COVID-19 period, construction disruption, and a post-opening road-speed gain that fades (S040). |
| synthetic_environmental_impact.csv | Day × corridor | 1,416 | Passenger-km and electricity from Phase 2; mode shares and emission factors as listed in the parameters file. |
| synthetic_station_economic_activity.csv | Year × station × catchment (500 m, 1 km, 2 km), 2018–2026 | 459 | A city-wide growth path plus an assumed metro premium. The file carries the value without the premium and the premium itself in separate columns. |

The station-area file is an assumption about what a metro premium might look like. It is not evidence that the metro caused any price change.

## 3. Cost-benefit model

- **Prices and period.** Constant FY2025-26 prices (CPI), FY2012-13 to FY2044-45, residual value 45% of capital cost. Present values are stated at FY2025-26, so past spending is compounded forward; ratios and rates of return do not depend on this choice.
- **Costs.** Actual spending to September 2026 from Phase 1, the remaining approved budget to FY2028-29, renewals, and operating cost. Economic costs remove taxes and transfers (capital × 0.85, operating × 0.90).
- **No-project counterfactual.** Metro passengers would travel by their previous mode at assumed corridor road speeds (bus 10 km/h); 10% of trips would not be made and are valued at half.
- **Benefits counted.** Passenger time savings, vehicle operating cost savings, net CO2 and PM2.5. Fares are excluded as transfers, so nothing is counted twice.
- **Not counted in the base case.** Time savings to remaining road users, accidents, health, reliability, comfort, agglomeration and land value. Road decongestion is shown as a separate illustrative sensitivity because corridor traffic volumes are not available.
- **Financial model.** Audited revenue to FY2024-25, synthetic FY2025-26, forecast afterwards; operating cost from Phase 2 (largely assumed); debt service estimated from loan terms.

All parameters are in `04_Analytical_Models/economic_benefit_parameters.csv`; assumptions and ranges in `assumptions_register_phase3.csv`.

## 4. Results

### FY2025-26 (estimated)

| Measure | Value |
|---|---|
| Passengers | 133.8 million |
| Average trip length | 7.7 km |
| Door-to-door time saved per passenger | 20 minutes on average; 29 minutes for a former bus passenger |
| Passenger-hours saved | 45.1 million (96.4 million since opening) |
| Value of time saved | Tk 398 crore |
| Vehicle operating cost saved | Tk 196 crore |
| Fuel saved | 11.3 million litres |
| Net CO2 | **34,300 tonnes more emitted than avoided** |
| PM2.5 avoided | 5.9 tonnes |
| Total economic benefit | Tk 579 crore, or Tk 43 per passenger |

### Economic returns

| Scenario | EIRR | EIRR without residual value | Benefit-cost ratio at 12% | Benefits needed for a 12% return |
|---|---|---|---|---|
| Base case | −2.3% | −10.9% | 0.13 | 9.3× |
| Low demand (−20%) | −2.8% | −14.1% | 0.11 | 11.1× |
| High demand (DMTCL's 677,000 a day) | −1.8% | −8.4% | 0.15 | 7.8× |
| High operating cost (+30%) | −2.8% | −14.2% | 0.13 | 9.4× |
| Cost escalation (+25% on remaining and renewal costs) | −2.5% | −12.2% | 0.13 | 9.4× |
| Combined downside | −4.3% | undefined | 0.09 | 15.6× |
| Value of time × 2.5 | 0.9% | −2.1% | 0.24 | 4.5× |
| Road decongestion included (illustrative) | −1.8% | −8.8% | 0.16 | 7.5× |
| Upside: high demand, value of time × 2.5, decongestion | 2.9% | 1.1% | 0.34 | 3.1× |

Net present values at 8%, 10%, 12% and 15% are in `cba_scenario_summary.csv`; all are negative.

### Financial position (base case, FY2025-26 prices)

| Year | Revenue | Operating cost | Operating surplus | Estimated debt service | After renewals and debt |
|---|---|---|---|---|---|
| FY2025-26 | Tk 551 crore | Tk 300 crore | Tk 251 crore | Tk 158 crore | Tk 92 crore |
| FY2026-27 | Tk 593 crore | Tk 451 crore | Tk 141 crore | Tk 461 crore | −Tk 319 crore |
| FY2030-31 | Tk 731 crore | Tk 524 crore | Tk 207 crore | Tk 1,057 crore | −Tk 1,014 crore |
| FY2044-45 | Tk 961 crore | Tk 707 crore | Tk 254 crore | Tk 1,008 crore | −Tk 917 crore |

The financial rate of return on the whole project is about −3.4% (JICA expected 1.7–3.1%). Estimated debt service for FY2026-27 to FY2030-31 totals Tk 3,524 crore, close to the press figure of more than Tk 3,700 crore.

## 5. How to read these results

1. **Fares appear to cover day-to-day operating cost but not debt.** This rests on assumed operating costs. It also assumes fares rise with inflation; they have not changed since 2022.
2. **The economic return is far below JICA's appraisal, and the gap has identifiable causes.**
   - Passenger-km: about 2.8 million a day now, against appraisal targets of 4.2 million and later 8.6 million. Trips are shorter than expected (7.7 km on a 20 km line), which the audited revenue per passenger of about Tk 42 supports.
   - Capital cost rose 49% in nominal terms.
   - This model values only direct benefits to passengers at conservative values of time. JICA's workings were not available, but its appraisal assumed road conditions without the metro would deteriorate much further (446 minutes for Uttara–Motijheel by 2025) and counted benefits to road users.
3. **The CO2 result contradicts the pre-opening claim.** Most passengers came from full buses, which emit little per passenger, while the metro draws power from a carbon-intensive grid. The result depends on modelled electricity use (calibrated only to an approximate monthly bill) and on how many buses were actually withdrawn. A cleaner grid would reverse it.
4. **What would change the conclusion.** A measured value of time well above Tk 85–150 per hour, proof of lasting road-speed gains with traffic counts, longer average trips once connecting lines open, and network effects from Lines 1 and 5. None of these can be established with public data today.

## 6. Limitations

- Trip length, previous-mode split beyond two published figures, road speeds, values of time, vehicle costs, emission factors and operating costs are assumptions.
- CPI before FY2019-20, the grid emission factor, bus-fare dates between 2024 and 2026, and several sources (S043–S051) were not verified against primary documents.
- The horizon ends in FY2044-45 with a residual value; JICA used a 36–40 year life.
- No accident, health, land-value or wider economic benefits are included.
- The debt schedule assumes full drawdown and a fixed yen rate.
