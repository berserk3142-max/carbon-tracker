# SOURCES.md - Source Research and Sample Data Choices

This project handles three source families:

1. SAP fuel/procurement exports
2. Utility electricity usage exports
3. Travel and expense exports

The implementation intentionally uses simplified CSV subsets. The goal is to show source-specific normalization, traceability, and audit workflow without pretending that the demo parser covers every enterprise export.

## 1. SAP Fuel and Procurement

### Real-World Format Researched

I modeled the SAP source after material document / goods movement extracts from SAP MM/S/4HANA. The code uses common SAP-style fields:

- `WERKS`: plant
- `MATNR`: material
- `MENGE`: quantity
- `MEINS`: unit of measure
- `BUDAT`: posting date
- `LIFNR`: vendor
- `BELNR`: document number

Research references:

- SAP Business Accelerator Hub, Goods Movement Document extraction fields: https://api.sap.com/cdsviews/I_GOODSMOVEMENTDOCUMENTDEX/fields
- SAP Business Accelerator Hub / SAP APIs in general: https://api.sap.com/

### What I Learned

SAP exports are usually not carbon-ready. They are operational accounting/logistics records. To become emissions records, the system must infer:

- which material codes represent fuels or relevant procurement items
- which plant/facility consumed them
- how units should be normalized
- which posting date should become the activity date
- whether a row is a normal posting, reversal, return, or adjustment

### Sample Data Shape

The sample file is:

```text
backend/sample_data/sap_fuel_procurement.csv
```

It contains SAP-like rows with German headers:

```text
WERKS,MATNR,MENGE,MEINS,BUDAT,LIFNR,BELNR
1102,DSL-FUEL,1200,L,2025-01-15,V001,500001
```

Why: this is enough to demonstrate material-code classification, plant tracking, date parsing, unit normalization, emission-factor lookup, and Scope 1 calculation.

### What This Project Handles

- common fuel material codes such as diesel, petrol, coal, natural gas, LPG
- unit conversions for liters, gallons, kilograms, tons, and cubic meters
- multiple date formats
- unknown material flags
- unknown unit flags

### What Was Ignored

- movement type logic
- reversal and cancellation indicators
- purchase order references
- batch/lot tracking
- valuation amount and currency
- plant-to-facility lookup enrichment in the normalized record
- customer-specific SAP Z-fields

### What Would Break in a Real Deployment

- custom material codes not mapped in `MATERIAL_TO_ACTIVITY`
- localized decimals such as `1.234,56`
- mixed unit semantics, such as `EA` for drums or cylinders
- negative quantities that represent valid reversals
- fuels reported indirectly through GL account or purchase category rather than `MATNR`
- SAP exports from a different module or custom report layout

## 2. Utility Electricity

### Real-World Format Researched

I modeled the utility source after common utility portal CSV exports and Green Button / ESPI concepts.

Research references:

- U.S. Department of Energy, Green Button overview: https://www.energy.gov/node/369883
- Green Button Alliance, usage data and interval metering concepts: https://www.greenbuttonalliance.org/usage-data
- Green Button Alliance, interval metering certification concepts: https://www.greenbuttonalliance.org/fb04

### What I Learned

Real utility usage data may be monthly billing data or interval meter data. Green Button/ESPI data is commonly XML/Atom based and can represent:

- usage points
- meter readings
- reading types
- interval blocks
- interval readings
- reading quality flags

For this project, I flattened the problem into monthly-style billing rows because that is what analysts often receive as CSV exports from utility portals.

### Sample Data Shape

The sample file is:

```text
backend/sample_data/utility_electricity.csv
```

Example shape:

```text
meter_id,facility,start_date,end_date,usage_kwh,cost,tariff_type
MTR-001,Mumbai Production Facility,2025-01-01,2025-01-31,84200,9240,industrial
```

Why: the app can show Scope 2 calculation clearly without XML parsing overhead.

### What This Project Handles

- meter and facility fields
- billing start/end dates
- kWh and MWh usage
- conversion from MWh to kWh
- tariff text carried into description
- missing usage validation
- invalid date validation

### What Was Ignored

- Green Button XML parsing
- interval data aggregation
- meter multipliers
- estimated vs actual reads
- demand charges
- utility account hierarchy
- renewable tariffs and certificates
- market-based vs location-based Scope 2

### What Would Break in a Real Deployment

- Green Button XML files would not parse because the current parser expects CSV
- interval reads would need aggregation by period
- meter multiplier or scale fields could make raw usage wrong
- time-zone boundaries could affect reporting periods
- net metering or exported solar could create negative/offset rows
- tariffs and renewable attributes may require market-based emissions logic

## 3. Travel and Expenses

### Real-World Format Researched

I modeled the travel source after SAP Concur / Navan-like expense exports and expense-entry schemas.

Research references:

- SAP Concur API tutorial overview: https://developers.sap.com/tutorials/data-to-value-conn-concur-part01..html
- SAP Concur expense schema examples on SAP Help Portal: https://help.sap.com/docs/SAP_CONCUR/27041ab78c844e679db485fff6f4033f/8d12726bd34f43238e04269939cfc59c.html
- SAP Concur expense configuration API reference: https://preview.developer.concur.com/api-reference/expense/expense-config/v4.expense.config.html

### What I Learned

Travel expense data is usually spend-oriented, not emissions-oriented. An expense entry may contain amount, currency, date, expense type, report, user, and purpose, but it often does not contain enough travel detail to calculate emissions precisely.

Flight emissions are especially difficult because accurate calculation needs:

- origin/destination airports
- each flight segment
- cabin class
- passenger count
- distance method
- radiative forcing assumptions

Expense exports often only include cost and a text description.

### Sample Data Shape

The sample file is:

```text
backend/sample_data/travel_expenses.csv
```

Example shape:

```text
employee_id,employee_name,travel_type,origin,destination,date,cost,currency,purpose
E001,Priya Sharma,flight,DEL,BLR,2025-01-22,18000,INR,Client workshop
```

Why: this supports a useful Scope 3 demo with route-based flight distance calculation when IATA codes are present.

### What This Project Handles

- travel types: flight, train, hotel, taxi/cab, car, bus
- IATA airport lookup for flight distance
- fallback airport data plus seeded airport table
- Haversine distance calculation
- simple train route lookup
- estimated taxi distance
- hotel room-night assumption
- cost fallback when route distance is unknown

### What Was Ignored

- multi-leg itineraries
- cabin class
- hotel check-in/check-out duration
- actual booking-system segments
- receipt OCR
- corporate card matching
- expense allocations across cost centers
- currency conversion
- personal vs reimbursable expense flags

### What Would Break in a Real Deployment

- free-text locations instead of IATA codes
- missing origin/destination
- multi-city trips
- expenses without travel distance
- hotel expenses without number of nights
- unknown travel types or localized expense names
- currency-only calculations without emission-specific units
- corporate card reversals or refunded expenses

## Summary of Source Coverage

| Source | Implemented | Ignored |
| --- | --- | --- |
| SAP | Fuel/procurement CSV, material mapping, units, dates | movement types, reversals, GL logic, custom SAP layouts |
| Utility | Monthly-style electricity CSV, kWh/MWh conversion | Green Button XML, interval reads, demand charges, RECs |
| Travel | Expense CSV, simple travel types, airport distance | full itinerary data, cabin class, currency conversion, allocations |

The app is intentionally built so each source-specific decision lives in a normalizer. Adding real-world coverage should mean adding richer normalizers and lookup tables without rewriting the core activity/audit model.
