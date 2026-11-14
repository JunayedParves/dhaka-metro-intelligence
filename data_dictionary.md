# Data dictionary — dashboard inputs

The dashboard reads one packaged file, `sample_data/dashboard_data.js`, and can also import the eleven CSV datasets below. A file is accepted only if it has the required fields. `Data_Type` (Actual, Synthetic, Estimated or Forecast) is read from every file when present and shown in the dataset table; rows without it are reported as *Unclassified*.

## CSV datasets accepted by the import control

| File | Required fields | Optional fields used | What it updates |
|---|---|---|---|
| `synthetic_daily_ridership.csv` | `Date`, `Station_ID`, `Passenger_Entry`, `Passenger_Exit` | `Data_Type` | Station entries and exits, line ridership, the date range |
| `synthetic_hourly_ridership.csv` | `Date`, `Hour`, `Station_ID`, `Passenger_Entry`, `Passenger_Exit` | `Direction`, `Data_Type` | Hourly line demand and station hour profiles |
| `synthetic_ticket_revenue.csv` | `Date`, `Station_ID`, `Gross_Revenue` | `Fare_Product`, `Data_Type` | Revenue by station and day |
| `synthetic_train_operations.csv` | `Date`, `Trip_Status`, `Delay_Minutes`, `Capacity_Utilization`, `Scheduled_Departure`, `Train_ID` | `Data_Type` | Scheduled and operated trips, on-time share, delay, utilization, trains in service |
| `synthetic_environmental_impact.csv` | `Date`, `Estimated_Vehicle_KM_Avoided`, `Fuel_Saved_Litres`, `CO2_Emissions_Avoided_KG`, `Electricity_Consumption_KWH` | `CO2_From_Electricity_KG` | Daily environmental counters |
| `synthetic_monthly_opex.csv` | `Month`, `Actual_or_Simulated_Expense_BDT` | `Expense_Category` | Monthly operating expense |
| `synthetic_station_economic_activity.csv` | `Year`, `Station_ID`, `Catchment_Radius`, `Estimated_Property_Value`, `Business_Count` | `Assumed_Metro_Premium_Pct`, `Average_Rent` | Station-area table (latest year in the file) |
| `project_financial_history.csv` | `Fiscal_Year`, `ADP_Allocation_BDT`, `Actual_Expenditure_BDT` | `Is_Partial_Year` | Annual expenditure chart and cumulative spend |
| `actual_ridership_statistics.csv` | `Period_Start`, `Metric`, `Value`, `Data_Type` | `Period_End`, `Reporting_Grain`, `Unit` | Published markers on the monthly trend |
| `operational_performance_actual.csv` | `Effective_Date`, `Metric`, `Value` | — | Stored for reference |
| `fare_structure_history.csv` | `Record_Type`, `Item` | — | Stored for reference |

Field formats: `Date` is `YYYY-MM-DD`; `Month` is `YYYY-MM`; `Hour` is 0–23 (06–22 are charted); `Station_ID` is `MRT6-01` to `MRT6-16`; money is in BDT; `Capacity_Utilization` is a fraction (0–1); `Trip_Status` is `Operated` or `Cancelled`.

Rows with an unknown station or a date outside the loaded range are skipped and counted in the import note. Importing `synthetic_daily_ridership.csv` resets the date range to the dates in that file; import it first.

## Packaged data file (`window.MRT_DATA`)

| Key | Classification | Contents |
|---|---|---|
| `meta` | — | Title, research cut-off, train capacity, geometry note, disclaimers |
| `stations[]` | Actual (position, opening date) | `id`, `seq`, `name`, `lat`, `lng`, `routeIndex`, `chainageM`, `opening`, `status`, descriptive text (`area`, `character`, `summary`, `commercial`, `education`, `health`, `transport`), `photo{file, author, license, page}` |
| `route[]`, `routeCum[]` | Actual | Track polyline `[lat, lng]` from OpenStreetMap and cumulative distance in metres |
| `dates[]`, `hours[]` | — | Calendar days covered and the charted hours (6–22) |
| `daily.entries / exits / revenue` | Synthetic | Flat arrays indexed `dateIndex × 16 + stationIndex` |
| `hourlyLine.values` | Synthetic | Line boardings, indexed `dateIndex × 17 + hourIndex` |
| `stationHourShape.{wk,sat,fri}.{entry,exit}` | Synthetic | For each station, the share of its daily total in each hour |
| `line.*` | Synthetic | One value per date: `status`, `pax`, `rev`, `pkm`, `sched`, `actual`, `cancelled`, `sets`, `otp`, `delay`, `interrupt`, `maxUtil`, `avgUtil`, `peakUtil`, `start`, `end` (minutes after midnight), `pkHw`, `offHw`, `openStations`, `weather`, `holiday`, `ramadan`, `pinned`, `trainKm`, `vkm`, `fuel`, `co2Road`, `pm25`, `kwh`, `co2Grid` |
| `monthly.rows[]` | Synthetic | `month`, `pax`, `rev`, `trips`, `trainKm`, `kwh`, `energyCost`, `opex` |
| `links.byMonth[month]` | Synthetic | `south[15]`, `north[15]`: average working-day load on each link |
| `finance.revisions` | Actual | Cost by revision and financing source |
| `finance.yearly` | Actual | Allocation, expenditure and cumulative spend by fiscal year |
| `finance.audited` | Actual | DMTCL audited ticket and non-fare revenue |
| `finance.componentChanges` | Actual | Cost changes by component in the third revision |
| `finance.viability` | Estimated | Revenue, operating cost, farebox ratio and estimated debt service by fiscal year |
| `published.rows[]` | Actual / Forecast | Published ridership figures at their original grain |
| `milestones[]` | Actual / Forecast | Dated project milestones; official targets are Forecast |
| `impact` | Estimated | Previous-mode shares, travel-time comparisons, annual modelled savings |
| `catchment.byStation[]` | Synthetic | Property value, assumed metro premium, rent and business count for 500 m, 1 km and 2 km |

`pinned = 1` marks the nine days whose line total equals a published single-day figure.
