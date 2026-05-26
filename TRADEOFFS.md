# TRADEOFFS.md - Deliberately Not Built

## 1. Background Ingestion Workers

I did not build Celery/RQ workers, a job table, or real-time progress polling.

Why: the current sample files are small, and synchronous ingestion made the data pipeline easier to review within the assignment scope.

Impact: large production files could time out or block the API request. A production version should move parsing, normalization, validation, and audit-log creation into an async worker.

Future version:

- create an `IngestionJob` table
- enqueue processing in Celery/RQ
- show progress per data source
- support retries and partial reprocessing

## 2. Full Emission Factor Library and Version Governance

I did not build a complete factor library with region, year, source, approval status, or market/location-based variants.

Why: full factor governance is a large product area. For this version, a compact `EmissionFactor` table demonstrates that factors are data-driven and auditable.

Impact: real customers need country-specific electricity factors, year-specific fuel factors, and defensible source/version selection. The current seeded factors are demo-quality and not enough for formal reporting.

Future version:

- factor version table
- jurisdiction and reporting-year filters
- market-based Scope 2 factors
- effective-date factor selection
- admin workflow for approving factor changes

## 3. Production-Grade Integrations, Storage, and Identity

I did not build direct SAP, utility, or Concur integrations; object storage; SSO; or role-policy management beyond basic user roles.

Why: CSV ingestion and JWT auth are enough to demonstrate the workflow from raw source data to audit-ready records.

Impact: real deployments would need stronger operational plumbing:

- SAP/Concur OAuth or service-account integrations
- Green Button Connect My Data or utility API connections
- S3-compatible storage for uploaded files
- SSO/SAML/OIDC
- fine-grained permissions for analysts, admins, auditors, and external reviewers

Future version:

- replace manual CSV upload with connector jobs
- store original files in object storage
- add organization-level integration credentials
- implement permissions around approve, reject, edit, lock, and export actions
