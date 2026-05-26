# DECISIONS.md - Product and Engineering Decisions

This document lists the main ambiguities I resolved, what I chose, why, and what I would ask the PM if I could.

## 1. Source Ingestion: CSV First

Decision: support CSV uploads for SAP, utility, and travel sources.

Why: CSV is easy to demo, inspect, and test. It also matches a realistic first version where analysts export reports from enterprise systems before full API integration exists.

What I ignored:

- direct SAP API integration
- Green Button XML ingestion
- SAP Concur OAuth/API ingestion
- scheduled jobs
- SFTP/email ingestion

PM question: are users expected to upload files manually, or is the production expectation API/scheduled ingestion from day one?

## 2. Synchronous Processing

Decision: process uploads synchronously inside the upload request.

Why: the assignment-sized data is small, and synchronous processing keeps the app simple and reviewable.

What I ignored:

- Celery/RQ worker queue
- background progress polling
- resumable ingestion
- large-file chunking

PM question: what is the expected file size and row count for a normal customer upload?

## 3. One Tenant Root: Organization

Decision: use `Organization` as the multi-tenant root and scope users, uploads, and activity records through it.

Why: it is simple, safe, and easy to enforce in DRF querysets.

What I ignored:

- users belonging to multiple organizations
- organization groups or parent companies
- facility-level permission boundaries
- row-level sharing across tenants

PM question: can consultants or auditors access multiple customer organizations from one account?

## 4. Scope Classification in Normalizers

Decision: normalizers assign Scope 1/2/3 and category during ingestion.

Why: classification depends heavily on source semantics. Fuel rows, utility rows, and travel rows need different logic.

Chosen mapping:

- SAP fuel/procurement -> Scope 1
- Utility electricity -> Scope 2
- Travel and expenses -> Scope 3

What I ignored:

- market-based vs location-based Scope 2
- purchased goods/services Scope 3 procurement categories beyond travel
- leased assets, waste, commuting, and upstream/downstream transportation

PM question: which GHG Protocol categories are in scope for the first evaluated release?

## 5. SAP Subset

Decision: handle a simplified SAP fuel/procurement export with these fields:

- `WERKS`: plant code
- `MATNR`: material code
- `MENGE`: quantity
- `MEINS`: unit
- `BUDAT`: posting date
- `LIFNR`: vendor
- `BELNR`: document number

Why: this is enough to show plant-aware fuel/procurement normalization, unit conversion, and Scope 1 classification.

What I ignored:

- company code
- movement type
- reversal indicators
- valuation/currency fields
- batch/lot fields
- purchase order references
- multiple SAP modules and custom extract layouts

PM question: should we key classification off material code, GL account, movement type, cost center, or an explicit activity mapping table?

## 6. Utility Subset

Decision: handle a flattened utility billing CSV with:

- meter ID
- facility/location
- billing start and end dates
- kWh or MWh usage
- cost
- tariff type

Why: monthly electricity bills are a common analyst input and map cleanly to Scope 2.

What I ignored:

- Green Button XML parsing
- interval meter reads
- demand charges
- renewable energy certificates
- market-based factors
- time-zone and meter multiplier handling
- estimated vs actual meter reads

PM question: do customers provide utility bills as CSV/PDF exports, or should the app ingest Green Button/ESPI data?

## 7. Travel Subset

Decision: handle a Concur/Navan-like travel expense CSV with:

- employee
- travel type
- origin
- destination
- date
- cost
- currency
- purpose

Why: it demonstrates Scope 3 business travel normalization with flight distance estimation.

What I ignored:

- multi-leg trips
- cabin class
- radiative forcing uplift
- actual ticket itinerary data
- hotel nights from check-in/check-out dates
- expense allocations across departments/projects
- currency conversion to a reporting currency

PM question: should travel emissions be calculated from actual booking itinerary data or from reimbursed expense rows?

## 8. Emission Factors

Decision: seed a small emission factor table with approximate factors for fuels, electricity, and travel.

Why: emission factors should not be hardcoded into normalizers, and auditors need a factor source field.

What I ignored:

- complete DEFRA/EPA/IEA factor catalogs
- country/year/fuel-grade specificity
- factor approval/version workflow
- market-based Scope 2 residual mix factors

PM question: which official factor library must be used for scoring and audit acceptance?

## 9. Audit Lock

Decision: approved records can be locked for audit, and locked records cannot be edited through the normal endpoint.

Why: an audit-ready record needs protection from accidental changes.

What I ignored:

- unlock approval flow
- reason-required edits after lock
- digital signatures
- immutable database-level append-only enforcement

PM question: who is allowed to lock and unlock records in production?

## 10. Deployment Target

Decision: prepare the project for Render deployment using `render.yaml`.

Why: Render can host a Django backend and a Vite static frontend from the same GitHub repository with simple build/start commands.

What I ignored:

- Docker-based deployment
- separate object storage for uploads
- CDN tuning
- multi-region deployment
- background worker services

PM question: should the evaluator expect one URL for the frontend only, or separate frontend and API URLs?
