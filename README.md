# CarbonTrack - ESG Carbon Accounting Platform

CarbonTrack is a full-stack ESG carbon accounting application for uploading operational data, normalizing it into auditable activity records, calculating CO2e emissions, and moving records through a review and audit workflow.

The project is built around a simple idea: every calculated emission value must be traceable back to the original uploaded row, the emission factor used, the person who reviewed it, and the audit trail of changes made afterward.

## Table of Contents

- [Project Overview](#project-overview)
- [Technology Stack](#technology-stack)
- [High-Level Architecture](#high-level-architecture)
- [Project Structure](#project-structure)
- [Evaluation Documents](#evaluation-documents)
- [Application Flow](#application-flow)
- [Detailed Flow Chart](#detailed-flow-chart)
- [Data Ingestion Pipeline](#data-ingestion-pipeline)
- [Review and Audit Workflow](#review-and-audit-workflow)
- [Database Model Diagram](#database-model-diagram)
- [Frontend Flow](#frontend-flow)
- [Backend API Flow](#backend-api-flow)
- [Environment and Database](#environment-and-database)
- [Setup Instructions](#setup-instructions)
- [Running the Project](#running-the-project)
- [Deployment](#deployment)
- [Seed Data](#seed-data)
- [Main API Endpoints](#main-api-endpoints)
- [Supported CSV Sources](#supported-csv-sources)
- [Important Design Decisions](#important-design-decisions)
- [Troubleshooting](#troubleshooting)

## Project Overview

CarbonTrack helps an ESG analyst manage carbon activity data from different business systems:

1. The user logs in or registers an organization.
2. The user uploads CSV files from SAP, utility billing systems, or travel expense systems.
3. The backend stores every source row as an immutable raw record.
4. Each raw row is normalized into a standard activity record.
5. Validation rules flag suspicious records.
6. Emission factors are applied to calculate CO2e.
7. Analysts review, edit, approve, reject, or lock records.
8. Every meaningful record change is written into an audit log.
9. The dashboard summarizes emissions by scope and review status.

## Technology Stack

| Layer | Technology |
| --- | --- |
| Frontend | React, TypeScript, Vite |
| UI/Data | Tailwind-style CSS, lucide-react icons, Recharts, TanStack Query, Zustand |
| Backend | Django, Django REST Framework |
| Auth | JWT using `djangorestframework-simplejwt` |
| Database | PostgreSQL, configured for Neon |
| Data Processing | pandas |
| API Client | axios |

## High-Level Architecture

```mermaid
flowchart LR
    User["User / ESG Analyst"] --> Browser["React Frontend<br/>Vite + TypeScript"]
    Browser --> API["Django REST API<br/>JWT protected endpoints"]
    API --> Auth["Auth Module<br/>Users + Organizations"]
    API --> Ingestion["Ingestion Module<br/>CSV upload + processing"]
    API --> Activities["Activities Module<br/>Normalized records + review"]
    API --> Audits["Audit Module<br/>Immutable change history"]
    API --> DB[("Neon PostgreSQL")]

    Ingestion --> Normalizers["Source Normalizers<br/>SAP / Utility / Travel"]
    Ingestion --> Validation["Validation Engine<br/>quality checks + flags"]
    Activities --> Factors["Emission Factors<br/>kg CO2e per unit"]

    Auth --> DB
    Ingestion --> DB
    Activities --> DB
    Audits --> DB
    Factors --> DB
```

### Architecture Explanation

The frontend never connects directly to the database. It sends requests to the Django API under `/api`. The backend authenticates the request using JWT, checks the user's organization, and only returns data that belongs to that organization.

The backend is split into focused Django apps:

- `users` handles login, registration, JWT generation, and current-user profile.
- `organizations` stores tenant organizations, plants, and airport lookup data.
- `ingestion` handles uploaded files, raw rows, and upload history.
- `activities` stores normalized emission activity records and review actions.
- `audits` stores immutable audit logs for traceability.
- `validation` contains rules for suspicious or invalid records.
- `normalizers` converts source-specific CSV rows into a standard internal shape.

## Project Structure

```text
.
+-- backend/
|   +-- manage.py
|   +-- requirements.txt
|   +-- config/
|   |   +-- settings.py
|   |   +-- urls.py
|   |   +-- asgi.py
|   |   +-- wsgi.py
|   +-- apps/
|   |   +-- users/
|   |   +-- organizations/
|   |   +-- ingestion/
|   |   +-- activities/
|   |   +-- audits/
|   |   +-- validation/
|   +-- normalizers/
|   |   +-- sap_normalizer.py
|   |   +-- utility_normalizer.py
|   |   +-- travel_normalizer.py
|   +-- sample_data/
|       +-- sap_fuel_procurement.csv
|       +-- utility_electricity.csv
|       +-- travel_expenses.csv
|
+-- frontend/
    +-- package.json
    +-- vite.config.ts
    +-- index.html
    +-- src/
        +-- App.tsx
        +-- main.tsx
        +-- lib/api.ts
        +-- stores/auth.ts
        +-- components/
        +-- pages/
            +-- LoginPage.tsx
            +-- DashboardPage.tsx
            +-- UploadsPage.tsx
            +-- ReviewPage.tsx
            +-- ActivityDetailPage.tsx
            +-- AuditLogPage.tsx
```

## Evaluation Documents

The assignment-specific design documents are included at the repository root:

| Document | Purpose |
| --- | --- |
| `MODEL.md` | Data model, tenancy strategy, source tracking, unit normalization, and audit trail rationale. |
| `DECISIONS.md` | Ambiguities resolved, source subsets chosen, ignored areas, and PM questions. |
| `TRADEOFFS.md` | Three deliberate omissions and why they were not built. |
| `SOURCES.md` | Source-format research, sample data rationale, and real-deployment failure modes. |

## Application Flow

The user-facing flow is:

```mermaid
flowchart TD
    A["Open App"] --> B{"Authenticated?"}
    B -- "No" --> C["Login / Register"]
    C --> D["JWT tokens saved in localStorage"]
    B -- "Yes" --> E["Dashboard"]
    D --> E

    E --> F["Upload CSV"]
    F --> G["Backend parses and processes file"]
    G --> H["Activity records created"]
    H --> I["Review Queue"]
    I --> J["Open Activity Detail"]
    J --> K{"Record valid?"}
    K -- "Needs correction" --> L["Edit normalized record"]
    L --> M["Audit log: updated"]
    K -- "Accept" --> N["Approve"]
    K -- "Reject" --> O["Reject"]
    N --> P["Audit log: approved"]
    O --> Q["Audit log: rejected"]
    P --> R["Lock for Audit"]
    R --> S["Audit log: locked"]
    S --> T["Dashboard and Audit Log updated"]
```

## Detailed Flow Chart

This diagram shows the full data journey from upload to locked audit record.

```mermaid
flowchart TB
    subgraph Frontend["Frontend - React"]
        Login["Login/Register Page"]
        Dashboard["Dashboard Page"]
        Uploads["Uploads Page"]
        Review["Review Queue Page"]
        Detail["Activity Detail Page"]
        AuditPage["Audit Log Page"]
    end

    subgraph API["Backend - Django REST API"]
        AuthAPI["/api/auth/*"]
        UploadAPI["/api/ingestion/upload/"]
        SourcesAPI["/api/ingestion/sources/"]
        ActivityAPI["/api/activities/*"]
        AuditAPI["/api/audits/*"]
    end

    subgraph Processing["Processing Layer"]
        CSVParse["pandas CSV parser"]
        RawStore["Create RawRecord rows"]
        NormalizerSelect{"source_type"}
        SAP["SAP normalizer"]
        Utility["Utility normalizer"]
        Travel["Travel normalizer"]
        Rules["Validation engine"]
        EF["Emission factor lookup"]
        CO2["CO2e calculation"]
    end

    subgraph Database["PostgreSQL / Neon"]
        OrgDB[("organizations")]
        UserDB[("users")]
        SourceDB[("data_sources")]
        RawDB[("raw_records")]
        ActivityDB[("activity_records")]
        FactorDB[("emission_factors")]
        AuditDB[("audit_logs")]
    end

    Login --> AuthAPI
    AuthAPI --> UserDB
    AuthAPI --> OrgDB
    AuthAPI --> Dashboard

    Dashboard --> ActivityAPI
    Dashboard --> SourcesAPI
    Uploads --> UploadAPI
    UploadAPI --> CSVParse
    CSVParse --> SourceDB
    CSVParse --> RawStore
    RawStore --> RawDB
    RawStore --> NormalizerSelect
    NormalizerSelect -- "sap" --> SAP
    NormalizerSelect -- "utility" --> Utility
    NormalizerSelect -- "travel" --> Travel
    SAP --> Rules
    Utility --> Rules
    Travel --> Rules
    Rules --> EF
    EF --> FactorDB
    EF --> CO2
    CO2 --> ActivityDB
    CO2 --> AuditDB

    Review --> ActivityAPI
    Detail --> ActivityAPI
    Detail --> AuditAPI
    ActivityAPI --> ActivityDB
    ActivityAPI --> AuditDB
    AuditPage --> AuditAPI
    AuditAPI --> AuditDB
```

## Data Ingestion Pipeline

The ingestion pipeline lives mainly in:

- `backend/apps/ingestion/views.py`
- `backend/apps/ingestion/services.py`
- `backend/normalizers/sap_normalizer.py`
- `backend/normalizers/utility_normalizer.py`
- `backend/normalizers/travel_normalizer.py`
- `backend/apps/validation/engine.py`

### Pipeline Steps

```mermaid
flowchart TD
    A["CSV Upload Request"] --> B["Validate file type and size"]
    B --> C["Create DataSource<br/>status = uploading"]
    C --> D["Read CSV bytes"]
    D --> E["Parse with pandas"]
    E --> F{"CSV empty?"}
    F -- "Yes" --> G["Mark DataSource failed"]
    F -- "No" --> H["Create RawRecord for every row"]
    H --> I{"Source Type"}

    I -- "SAP" --> J["Map SAP columns<br/>WERKS, MATNR, MENGE, MEINS, BUDAT"]
    I -- "Utility" --> K["Map utility columns<br/>meter, facility, kWh/MWh"]
    I -- "Travel" --> L["Map travel columns<br/>flight/train/hotel/taxi"]

    J --> M["Normalize quantity and unit"]
    K --> M
    L --> M

    M --> N["Classify activity<br/>scope + category"]
    N --> O["Run validation rules"]
    O --> P["Find emission factor"]
    P --> Q["Calculate CO2e"]
    Q --> R["Create ActivityRecord"]
    R --> S["Update RawRecord status"]
    S --> T["Create AuditLog action = created"]
    T --> U{"Any row failures?"}
    U -- "No" --> V["DataSource status = completed"]
    U -- "Some" --> W["DataSource status = partial"]
    U -- "All failed" --> X["DataSource status = failed"]
```

### What Is Stored During Upload

| Object | Purpose |
| --- | --- |
| `DataSource` | Represents the uploaded file and processing summary. |
| `RawRecord` | Stores the exact row payload from the CSV. This is the immutable source of truth. |
| `ActivityRecord` | Stores normalized, reviewable activity data. |
| `AuditLog` | Records that an activity record was created from ingestion. |

## Review and Audit Workflow

Every activity record has a status and may be locked. Once locked, it cannot be edited by the normal update flow.

```mermaid
stateDiagram-v2
    [*] --> validated: clean upload row
    [*] --> flagged: validation warning/error
    [*] --> pending: manually created or awaiting review

    validated --> approved: analyst approves
    flagged --> approved: analyst approves after review
    pending --> approved: analyst approves

    validated --> rejected: analyst rejects
    flagged --> rejected: analyst rejects
    pending --> rejected: analyst rejects

    validated --> flagged: suspicious rule detected
    flagged --> flagged: edited but still suspicious

    approved --> locked: lock for audit
    locked --> [*]

    note right of locked
        Locked records are treated
        as audit-ready and cannot
        be edited through the
        standard update endpoint.
    end note
```

### Review Actions

| Action | Endpoint | Result |
| --- | --- | --- |
| Edit activity | `PATCH /api/activities/{id}/` | Updates selected normalized fields and creates an `updated` audit log. |
| Approve | `POST /api/activities/{id}/approve/` | Sets status to `approved`, clears suspicious flag, stores reviewer and comment. |
| Reject | `POST /api/activities/{id}/reject/` | Sets status to `rejected`, stores reviewer and comment. |
| Lock | `POST /api/activities/{id}/lock/` | Sets status to `locked` and prevents future edits. |
| Bulk approve | `POST /api/activities/bulk_approve/` | Approves multiple unlocked records. |
| Bulk lock | `POST /api/activities/bulk_lock/` | Locks multiple approved records. |

## Database Model Diagram

```mermaid
erDiagram
    ORGANIZATION ||--o{ USER : has
    ORGANIZATION ||--o{ PLANT : has
    ORGANIZATION ||--o{ DATASOURCE : owns
    ORGANIZATION ||--o{ ACTIVITY_RECORD : owns

    USER ||--o{ DATASOURCE : uploads
    USER ||--o{ ACTIVITY_RECORD : reviews
    USER ||--o{ ACTIVITY_RECORD : locks
    USER ||--o{ AUDIT_LOG : changes

    DATASOURCE ||--o{ RAW_RECORD : contains
    DATASOURCE ||--o{ ACTIVITY_RECORD : creates
    RAW_RECORD ||--|| ACTIVITY_RECORD : normalizes_to

    EMISSION_FACTOR ||--o{ ACTIVITY_RECORD : used_by
    ACTIVITY_RECORD ||--o{ AUDIT_LOG : has

    AIRPORT_LOOKUP {
        string iata_code PK
        string name
        string city
        string country
        float latitude
        float longitude
    }

    ORGANIZATION {
        int id PK
        string name
        string industry
        string country
        datetime created_at
        datetime updated_at
    }

    USER {
        int id PK
        string username
        string email
        string role
        int organization_id FK
    }

    PLANT {
        int id PK
        int organization_id FK
        string code
        string name
        string location
        string country
    }

    DATASOURCE {
        int id PK
        int organization_id FK
        string source_type
        string ingestion_method
        string file_name
        string status
        int total_rows
        int processed_rows
        int failed_rows
    }

    RAW_RECORD {
        int id PK
        int datasource_id FK
        int row_number
        json raw_payload
        string ingestion_status
        string error_message
    }

    ACTIVITY_RECORD {
        int id PK
        int organization_id FK
        int raw_record_id FK
        int datasource_id FK
        string activity_type
        int scope
        string category
        float quantity
        string original_unit
        float normalized_quantity
        string normalized_unit
        float co2e_kg
        string status
        boolean suspicious
        boolean locked
    }

    EMISSION_FACTOR {
        int id PK
        string activity_type
        string fuel_type
        string unit
        float factor_value
        string factor_unit
        string source
    }

    AUDIT_LOG {
        int id PK
        int record_id FK
        string action
        int changed_by_id FK
        json old_values
        json new_values
        string comment
        datetime timestamp
    }
```

## Frontend Flow

The frontend starts at `frontend/src/App.tsx`.

```mermaid
flowchart TD
    A["main.tsx"] --> B["App.tsx"]
    B --> C["QueryClientProvider"]
    C --> D["BrowserRouter"]
    D --> E{"Route"}

    E -- "/login" --> F["LoginPage"]
    E -- "Protected routes" --> G{"access_token exists?"}
    G -- "No" --> F
    G -- "Yes" --> H["Layout"]

    H --> I["/dashboard<br/>DashboardPage"]
    H --> J["/uploads<br/>UploadsPage"]
    H --> K["/review<br/>ReviewPage"]
    H --> L["/activity/:id<br/>ActivityDetailPage"]
    H --> M["/audit-log<br/>AuditLogPage"]

    F --> N["authAPI.login/register"]
    N --> O["Save access_token + refresh_token"]
    O --> I
```

### Frontend Pages

| Page | Path | Purpose |
| --- | --- | --- |
| Login/Register | `/login` | Authenticates users and creates organizations during registration. |
| Dashboard | `/dashboard` | Shows total records, review counts, CO2e totals, scope breakdown, and recent uploads. |
| Uploads | `/uploads` | Uploads CSVs and shows upload history. |
| Review Queue | `/review` | Lists activity records with filters, selections, bulk approve, and bulk lock. |
| Activity Detail | `/activity/:id` | Shows normalized data, raw source payload, validation flags, review actions, and audit trail. |
| Audit Log | `/audit-log` | Shows all audit events for the current organization. |

## Backend API Flow

All main API routes are mounted in `backend/config/urls.py`.

```mermaid
flowchart LR
    API["/api"] --> Auth["/auth"]
    API --> Org["/organizations"]
    API --> Ingestion["/ingestion"]
    API --> Activities["/activities"]
    API --> Audits["/audits"]

    Auth --> Register["POST /register/"]
    Auth --> Login["POST /login/"]
    Auth --> Me["GET /me/"]
    Auth --> Refresh["POST /token/refresh/"]

    Ingestion --> Upload["POST /upload/"]
    Ingestion --> Sources["GET /sources/"]
    Ingestion --> SourceDetail["GET /sources/{id}/"]
    Ingestion --> RawRows["GET /sources/{id}/raw_records/"]

    Activities --> Stats["GET /stats/"]
    Activities --> List["GET /"]
    Activities --> Detail["GET /{id}/"]
    Activities --> Update["PATCH /{id}/"]
    Activities --> Approve["POST /{id}/approve/"]
    Activities --> Reject["POST /{id}/reject/"]
    Activities --> Lock["POST /{id}/lock/"]
    Activities --> BulkApprove["POST /bulk_approve/"]
    Activities --> BulkLock["POST /bulk_lock/"]

    Audits --> AuditList["GET /"]
    Audits --> RecordTrail["GET /record/{record_id}/"]
```

## Environment and Database

The backend database config is in:

```text
backend/config/settings.py
```

The code reads configuration from environment variables using `python-decouple`.
It looks for a local env file at:

```text
backend/.env
```

`backend/.env` is intentionally ignored by Git so real passwords are not pushed to GitHub. The repository includes this safe template instead:

```text
backend/.env.example
```

The database URL is read like this:

```python
DATABASE_URL = config("DATABASE_URL", default="")
```

If `DATABASE_URL` is missing, Django falls back to a local SQLite database at `backend/db.sqlite3`. For Neon/PostgreSQL, set `DATABASE_URL` in `backend/.env` or in the shell environment.

Example PowerShell session:

```powershell
$env:DATABASE_URL="postgresql://USER:PASSWORD@HOST/neondb?sslmode=require&channel_binding=require"
python manage.py runserver
```

Example `.env` content:

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST/neondb?sslmode=require&channel_binding=require
DJANGO_SECRET_KEY=replace-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=*
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

Important: do not commit real database passwords or production secrets.

## Setup Instructions

### 1. Backend Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run migrations:

```powershell
python manage.py migrate
```

Optional seed data:

```powershell
python manage.py seed_data
```

### 2. Frontend Setup

```powershell
cd frontend
npm install
```

## Running the Project

### Start Backend

From the `backend` directory:

```powershell
python manage.py runserver
```

Backend default URL:

```text
http://127.0.0.1:8000
```

### Start Frontend

From the `frontend` directory:

```powershell
npm run dev
```

Frontend default URL:

```text
http://localhost:5173
```

The frontend uses `/api` as its API base path. In development, `frontend/vite.config.ts` proxies `/api` requests to the Django backend at `http://localhost:8000`.

## Deployment

This repository includes a Render Blueprint:

```text
render.yaml
```

It defines two services:

| Service | Purpose |
| --- | --- |
| `carbon-tracker-api` | Django REST API served by Gunicorn. |
| `carbon-tracker` | Vite static frontend. |

The backend service runs:

```text
pip install -r requirements.txt && python manage.py collectstatic --noinput
python manage.py migrate && python manage.py seed_data && gunicorn config.wsgi:application
```

The frontend service runs:

```text
npm ci && npm run build
```

Required Render environment variable for the backend:

```text
DATABASE_URL=postgresql://USER:PASSWORD@HOST/neondb?sslmode=require&channel_binding=require
```

The frontend uses:

```text
VITE_API_BASE=https://carbon-tracker-api.onrender.com/api
```

If Render assigns different service URLs, update:

- backend `DJANGO_ALLOWED_HOSTS`
- backend `CORS_ALLOWED_ORIGINS`
- backend `CSRF_TRUSTED_ORIGINS`
- frontend `VITE_API_BASE`

The local `.env` file is intentionally ignored by Git. Use `backend/.env.example` and `frontend/.env.example` as templates.

## Seed Data

The seed command creates:

- Demo organization: `Acme Manufacturing Corp`
- Demo users:
  - `admin / admin123`
  - `analyst / analyst123`
- Plant lookup data
- Airport lookup data
- Emission factors for fuels, electricity, flights, train, taxi, and hotel stays

Seed command:

```powershell
cd backend
python manage.py seed_data
```

## Main API Endpoints

### Authentication

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/auth/register/` | Register a new user and organization. |
| `POST` | `/api/auth/login/` | Login and receive JWT tokens. |
| `GET` | `/api/auth/me/` | Get current authenticated user. |
| `POST` | `/api/auth/token/refresh/` | Refresh JWT access token. |

### Ingestion

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/ingestion/upload/` | Upload CSV file with `file` and `source_type`. |
| `GET` | `/api/ingestion/sources/` | List upload history for the current organization. |
| `GET` | `/api/ingestion/sources/{id}/` | Get upload details. |
| `GET` | `/api/ingestion/sources/{id}/raw_records/` | Get raw rows for a data source. |

### Activities

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/activities/stats/` | Dashboard metrics. |
| `GET` | `/api/activities/` | List activity records. |
| `GET` | `/api/activities/{id}/` | Activity detail with raw record and emission factor. |
| `PATCH` | `/api/activities/{id}/` | Edit normalized activity fields. |
| `POST` | `/api/activities/{id}/approve/` | Approve record. |
| `POST` | `/api/activities/{id}/reject/` | Reject record. |
| `POST` | `/api/activities/{id}/lock/` | Lock approved record for audit. |
| `POST` | `/api/activities/bulk_approve/` | Approve multiple records. |
| `POST` | `/api/activities/bulk_lock/` | Lock multiple approved records. |

### Audits

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/audits/` | List audit logs. |
| `GET` | `/api/audits/record/{record_id}/` | Get audit trail for one activity record. |

## Supported CSV Sources

### 1. SAP Fuel and Procurement

Source type:

```text
sap
```

Expected or supported columns include:

| Source Column | Meaning |
| --- | --- |
| `WERKS` | Plant code |
| `MATNR` | Material number |
| `MENGE` | Quantity |
| `MEINS` | Unit |
| `BUDAT` | Posting date |
| `LIFNR` | Vendor |
| `BELNR` | Document number |

The SAP normalizer maps material codes like `DSL-FUEL`, `PET-FUEL`, `COAL-01`, `NAT-GAS`, and `LPG-01` into activity types and Scope 1 categories.

### 2. Utility Electricity

Source type:

```text
utility
```

Supported columns include:

| Source Column | Meaning |
| --- | --- |
| `meter_id` | Meter identifier |
| `facility` | Facility name |
| `start_date` | Billing start date |
| `end_date` | Billing end date |
| `usage_kwh` | Electricity use in kWh |
| `usage_mwh` | Electricity use in MWh |
| `tariff_type` | Tariff |

Utility records become Scope 2 purchased electricity records.

### 3. Travel and Expenses

Source type:

```text
travel
```

Supported columns include:

| Source Column | Meaning |
| --- | --- |
| `employee_id` | Employee identifier |
| `employee_name` | Employee name |
| `travel_type` | flight, train, hotel, taxi, etc. |
| `origin` | Origin city or airport |
| `destination` | Destination city or airport |
| `date` | Travel date |
| `cost` | Expense amount |
| `currency` | Currency |
| `purpose` | Travel purpose |

Travel records become Scope 3 business travel records. Flights use airport lookup data and Haversine distance calculation when possible.

## Validation Rules

The validation engine checks normalized rows before creating final activity records.

| Rule | Severity | Purpose |
| --- | --- | --- |
| `non_finite_quantity` | error | Detects NaN or infinite values. |
| `negative_quantity` | error | Detects negative quantities. |
| `zero_quantity` | warning | Warns about zero quantities. |
| `missing_unit` | error | Detects missing or unknown normalized units. |
| `future_date` | warning | Warns when activity date is in the future. |
| `suspicious_spike` | warning | Flags quantities over 5x category average. |
| `extreme_value` | warning | Flags very high values by unit type. |

If any warning or error exists, the record is marked suspicious. Records with suspicious data are created with status `flagged`; clean records are created with status `validated`.

## Important Design Decisions

### 1. Tenant Isolation

Most queries filter by:

```python
organization=request.user.organization
```

This keeps each organization's data separate.

### 2. Raw Data Is Immutable

`RawRecord` stores the original CSV row payload. The system edits normalized `ActivityRecord` values, not the raw source data. This keeps the audit trail reliable.

### 3. Emission Factor Snapshot

Each activity stores:

- `emission_factor`
- `emission_factor_value`
- `co2e_kg`

The factor relationship points to the source factor, while the numeric snapshot helps preserve what was used at calculation time.

### 4. Locked Records Cannot Be Edited

Once a record is locked, the API blocks standard edits. This protects audit-ready data from accidental changes.

### 5. Audit Logs Are Created Automatically

Audit logs are created when records are:

- created by ingestion
- edited
- approved
- rejected
- locked
- bulk approved
- bulk locked

## Troubleshooting

### `psql` Is Not Recognized

This means the PostgreSQL CLI is not installed or not on the system PATH. The Django app can still connect to Neon through `psycopg2` if dependencies are installed.

Check Django database connectivity:

```powershell
cd backend
python manage.py shell -c "from django.db import connection; c = connection.cursor(); c.execute('select current_database(), current_user, now()'); print(c.fetchone())"
```

### Neon Connection Permission Error

If you see a permission or network error when connecting to Neon, check:

- Internet/network access is allowed.
- Port `5432` is not blocked.
- The Neon connection string is correct.
- `sslmode=require` is included.

### Migrations Not Applied

Run:

```powershell
cd backend
python manage.py migrate
```

Check migration state:

```powershell
python manage.py migrate --check
```

### Frontend Cannot Reach Backend

Check:

- Django is running on `http://127.0.0.1:8000`.
- Vite dev server is running on `http://localhost:5173`.
- `frontend/vite.config.ts` proxies `/api` to Django.
- The browser has a valid JWT access token after login.

## Summary

CarbonTrack is organized around a traceable emissions workflow:

```mermaid
flowchart LR
    CSV["CSV source data"] --> Raw["Immutable raw records"]
    Raw --> Normalized["Normalized activity records"]
    Normalized --> Validation["Validation flags"]
    Validation --> CO2e["CO2e calculation"]
    CO2e --> Review["Analyst review"]
    Review --> Approved["Approved records"]
    Approved --> Locked["Locked audit records"]
    Review --> Logs["Audit logs"]
    Locked --> Logs
```

That flow gives ESG analysts a practical system for turning messy operational files into reviewable, traceable, audit-ready carbon accounting data.
