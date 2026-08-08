# ERP System - Import/Export Management System Specification

## 1. Project Overview

### Project Name
CargoFlow ERP — Import/Export Management System

### Project Type
Web-based Enterprise Resource Planning (ERP) Module

### Core Functionality
A comprehensive import/export management system that handles the complete lifecycle of both **import operations** (booking receipt → job closure) and **export operations** (outbound shipment booking → vessel departure → clearance), including truck/trailer/driver management, vendor/customer management, location tracking, invoicing, job templates, document management, activity logging, and **AI-powered assistants** (chat, document OCR extraction, delay/ETA prediction, weekly reports, and smart job suggestions).

### Target Users
- Operations Staff
- Warehouse Managers
- Finance/Accounting
- Management/Approvers
- Administrators

---

## 2. Architecture

### Microservices Pattern

```
┌──────────────────────────────────────────────────────────────────────┐
│                         API Gateway (FastAPI)                        │
├──────────────────────────────────────────────────────────────────────┤
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐        │
│  │   Auth     │ │   Import   │ │   Fleet    │ │   Master   │        │
│  │   Service  │ │   Service  │ │   Service  │ │   Data     │        │
│  │            │ │            │ │            │ │   Service  │        │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘        │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    AI Service (Ollama)                       │   │
│  │   Chat · OCR extraction · ETA prediction · Reports · Assist  │   │
│  └──────────────────────────────────────────────────────────────┘   │
├──────────────────────────────────────────────────────────────────────┤
│                        PostgreSQL Database                           │
│                    (Each service has its own schema)                 │
└──────────────────────────────────────────────────────────────────────┘
```

### Tech Stack
- **Frontend**: ReactJS with TypeScript (Vite)
- **Backend**: Python FastAPI (microservices)
- **Database**: PostgreSQL
- **Authentication**: JWT-based (shared secret across services, token relay)
- **AI**: Ollama (local, self-hosted small models)

### Service Boundaries

| Service | Port | Responsibility |
|---------|------|----------------|
| API Gateway | 8000 | Routing, proxy, CORS |
| Auth Service | 8001 | User authentication, roles, permissions, user management |
| Import Service | 8002 | Import job workflow, export job workflow, invoices, templates, documents, activity logs |
| Fleet Service | 8003 | Trucks, trailers, drivers management |
| Master Data Service | 8004 | Customers, vendors, locations, items, company settings |
| AI Service | 8005 | AI chat, document OCR extraction, delay/ETA prediction, weekly reports, smart job assist |

---

## 3. Functional Requirements

### 3.1 Import Process Workflow

#### Phase 1: Job Creation
- **3.1.1** Receive and verify booking receipt (container number, vessel name, ETA, BL)
- **3.1.2** Enter booking details into system
- **3.1.3** Create job and submit for approval (status `PENDING_APPROVAL`)

#### Phase 2: Approval & Preparation
- **3.1.4** Approve/Reject job
- **3.1.5** Assign operational team

#### Phase 3: License & Permits
- **3.1.6** Check if OT (Import) License required
- **3.1.7** Apply for license if required
- **3.1.8** Submit customs permit application with documents (Invoice, Packing List, BL, License)

#### Phase 4: Transportation
- **3.1.9** Check truck availability
- **3.1.10** Assign internal truck or outsource to vendor
- **3.1.11** Confirm pickup schedule based on vessel ETA

#### Phase 5: Execution
- **3.1.12** Record vessel Actual Time of Arrival (ATA)
- **3.1.13** Process customs clearance (inspection, duties, release)
- **3.1.14** Container pick up from port

#### Phase 6: Delivery
- **3.1.15** Deliver container to customer warehouse
- **3.1.16** Confirm unloading and cargo condition

#### Phase 7: Completion
- **3.1.17** Return empty container to depot (capture EIR)
- **3.1.18** Close job, update status, complete billing

### 3.2 Export Process Workflow (NEW)

#### Phase 1: Job Creation
- **3.2.1** Receive outbound booking (container number, vessel, ETD, BL, shipper/consignee)
- **3.2.2** Create export job and submit for approval (`PENDING_APPROVAL`)

#### Phase 2: Approval & Preparation
- **3.2.3** Approve/Reject export job
- **3.2.4** Assign operational team

#### Phase 3: License & Permits
- **3.2.5** Check if export license required; apply if needed (`apply-license`)
- **3.2.6** Submit export customs permit application (`customs-permit`)

#### Phase 4: Transportation
- **3.2.7** Assign truck/trailer/driver (internal or outsourced to vendor)

#### Phase 5: Execution
- **3.2.8** Pick up empty container from depot (`empty-pickup`)
- **3.2.9** Confirm stuffing at shipper location (`stuff`)
- **3.2.10** Record port gate-in and generate/enter EIR number (`gate-in`)
- **3.2.11** Record vessel Actual Time of Departure (ATD) (`departure`)

#### Phase 6: Clearance & Completion
- **3.2.12** Process export customs clearance (`clearance`)
- **3.2.13** Close job (`close`)

### 3.3 AI Features (NEW)

All AI endpoints live in the **AI Service** and call **Ollama** locally. If Ollama is unavailable, every feature degrades gracefully to an offline rule-based mode.

#### 3.3.1 AI Chat Assistant
- Natural-language assistant over live ERP data
- Auto-detects intent (jobs, exports, fleet, invoices, customers, vendors, items) and pulls relevant context
- Answers via `qwen2.5:1.5b` (configurable); falls back to live summary stats when offline
- Accessible from every page via a floating chat widget

#### 3.3.2 Document OCR / Data Extraction
- Upload PDF or image (PNG/JPG/BMP/WebP)
- PDFs rasterized via PyMuPDF (up to 3 pages)
- Vision model (`llava:7b`, configurable) extracts structured JSON: BL number, container number, vessel, shipper, consignee, cargo, ETD/ATD, quantity
- Extracted fields can be applied directly to an import or export job

#### 3.3.3 Delay / ETA Prediction
- Heuristic model over historical shipments (average delay vs ETA/ETD, per-status timings)
- Returns predicted arrival/departure date, delay risk (low/medium/high) and confidence
- Fully offline, no external ML dependencies

#### 3.3.4 Weekly AI Reports
- Aggregates 7-day stats: new import/export jobs, revenue (invoices), active jobs, delayed shipments, status distribution
- Generates a natural-language narrative with bottleneck highlights and recommendations
- Rendered on the dedicated AI Reports page

#### 3.3.5 Smart Job Assist
- Rule-based suggestions per job: next recommended workflow step, missing required fields, license/permit flags, stuck-in-status and aged-job anomaly detection, past ETA/ETD warnings
- Optional LLM tip for each job
- Embedded in both Import Job Detail and Export Job Detail pages

### 3.4 Supporting Features

#### 3.4.1 Invoicing
- Create invoices per job with line items (description, qty, unit price, COA)
- Subtotal, tax rate, tax, total auto-calculation
- Invoice status workflow (DRAFT → ISSUED → PAID etc.)

#### 3.4.2 Job Templates
- Reusable job templates for common shipments (name, container, vessel, cargo, quantity, license flag)

#### 3.4.3 Document Management
- Upload/attach documents (base64) to import and export jobs; view and delete
- Files stored on disk under the service uploads directory; metadata in DB

#### 3.4.4 Activity Logging
- Every workflow action recorded with action, description, old/new value and actor
- Viewable per job (import `job_id` or export `job_id`)

#### 3.4.5 User Management
- Admin-managed users: create, list, update roles, delete

#### 3.4.6 Company Settings
- Editable company profile used across the platform

#### 3.4.7 Dashboard Alerts & Search
- Real-time notifications: driver ID/license expiry (30-day window), past ETA (import) and past ETD (export) alerts
- Global search across jobs, trucks, customers and vendors

### 3.5 Plan-Based Feature Gating (NEW)

Selling tiers (Starter / Business / Enterprise) control which modules and features a tenant can use. Enforcement is server-side; the UI only reflects the backend rule.

**Plans & limits**

| Plan | Included features | Max users |
|------|-------------------|-----------|
| `starter` | import, export, fleet, master-data | 5 |
| `business` | + invoicing, documents, templates, ai | 25 |
| `enterprise` | everything | unlimited |

**Enforcement points**

1. **Plan storage** — `plan` column on `users` in the auth-service (default `starter`); embedded in the JWT claims at login/refresh (`plan`, plus existing `role`/`user_id`).
2. **API Gateway** — the single enforcement choke point for all `/api/*` traffic:
   - Decodes the bearer JWT using the shared `SECRET_KEY`/`ALGORITHM`.
   - Maps the request path to a feature via `ROUTE_FEATURES` (e.g. `/api/ai` → `ai`, `/api/invoices` → `invoicing`, `/api/templates` → `templates`, `/api/documents*` → `documents`).
   - Returns `403` when the user's plan does not include the requested feature.
   - Injects `X-User-Plan`, `X-User-Role`, `X-User-Id` headers downstream for services that need them.
3. **User count limits** — enforced in the auth-service `register` and user-update endpoints (`PLAN_MAX_USERS`): rejecting creation/assignment when the target plan's user cap is reached.
4. **Frontend** — plan-aware: hides sidebar links (Templates, AI Reports, Invoices) and the AI chat widget when the plan lacks the feature, renders a locked/upgrade panel in `AIAssistPanel`, and gates routes via `PlanGate`. The upgrade prompt links to `sales@cargoflow.app`.

**Plan switching** — admins change a user's plan from User Management (PUT `/api/auth/users/{id}`). The new plan takes effect on that user's next login or token refresh.

---

## 4. API Specification

### 4.1 Auth Service

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/register | Register user |
| POST | /api/auth/login | User login |
| POST | /api/auth/refresh | Refresh token |
| GET | /api/auth/me | Get current user |
| GET | /api/auth/users | List users (admin) |
| PUT | /api/auth/users/{id} | Update user |
| DELETE | /api/auth/users/{id} | Delete user (admin) |

### 4.2 Import Service — Import Jobs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/jobs | Create import job |
| GET | /api/jobs | List all jobs (search/filter) |
| GET | /api/jobs/{id} | Get job details |
| PUT | /api/jobs/{id} | Update job |
| PUT | /api/jobs/{id}/approve | Approve job (admin/manager) |
| PUT | /api/jobs/{id}/reject | Reject job (admin/manager) |
| PUT | /api/jobs/{id}/assign-team | Assign team (admin/manager) |
| PUT | /api/jobs/{id}/apply-license | Apply import license |
| PUT | /api/jobs/{id}/customs-permit | Submit customs permit |
| PUT | /api/jobs/{id}/truck | Assign truck/trailer/driver (or outsource) |
| PUT | /api/jobs/{id}/arrival | Record vessel arrival |
| PUT | /api/jobs/{id}/clearance | Process customs clearance |
| PUT | /api/jobs/{id}/pickup | Container pick up |
| PUT | /api/jobs/{id}/deliver | Deliver to customer |
| PUT | /api/jobs/{id}/unload | Confirm unloading |
| PUT | /api/jobs/{id}/return-container | Return empty container |
| PUT | /api/jobs/{id}/close | Close job (admin/manager) |
| DELETE | /api/jobs/{id} | Delete job (admin) |
| GET | /api/jobs/activities | Activity log (optional job_id) |
| GET | /api/jobs/{id}/documents | List job documents |
| POST | /api/jobs/{id}/documents | Upload job document |
| DELETE | /api/documents/{id} | Delete document |
| GET | /api/jobs/{id}/invoices | List job invoices |
| POST | /api/jobs/{id}/invoices | Create invoice for job |

### 4.3 Import Service — Export Jobs (NEW)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/exports | Create export job |
| GET | /api/exports | List export jobs (search/filter) |
| GET | /api/exports/{id} | Get export job details |
| PUT | /api/exports/{id} | Update export job |
| PUT | /api/exports/{id}/approve | Approve export job (admin/manager) |
| PUT | /api/exports/{id}/reject | Reject export job (admin/manager) |
| PUT | /api/exports/{id}/assign-team | Assign team (admin/manager) |
| PUT | /api/exports/{id}/apply-license | Apply export license |
| PUT | /api/exports/{id}/customs-permit | Submit export customs permit |
| PUT | /api/exports/{id}/truck | Assign truck/trailer/driver (or outsource) |
| PUT | /api/exports/{id}/empty-pickup | Record empty container pickup |
| PUT | /api/exports/{id}/stuff | Confirm stuffing |
| PUT | /api/exports/{id}/gate-in | Record port gate-in (EIR) |
| PUT | /api/exports/{id}/departure | Record vessel departure (ATD) |
| PUT | /api/exports/{id}/clearance | Process export clearance |
| PUT | /api/exports/{id}/close | Close export job (admin/manager) |
| DELETE | /api/exports/{id} | Delete export job (admin) |
| GET | /api/exports/activities | Export activity log (optional job_id) |
| GET | /api/exports/{id}/documents | List export documents |
| POST | /api/exports/{id}/documents | Upload export document |
| DELETE | /api/export-documents/{id} | Delete export document |

### 4.4 Import Service — Invoices & Templates

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/invoices | List invoices |
| GET | /api/invoices/{id} | Get invoice |
| PUT | /api/invoices/{id} | Update invoice |
| PUT | /api/invoices/{id}/status | Update invoice status |
| POST | /api/invoices/{id}/lines | Add invoice line |
| DELETE | /api/invoices/{id}/lines/{line_id} | Remove invoice line |
| DELETE | /api/invoices/{id} | Delete invoice |
| GET | /api/templates | List job templates |
| POST | /api/templates | Create template |
| PUT | /api/templates/{id} | Update template |
| DELETE | /api/templates/{id} | Delete template |

### 4.5 Fleet Service

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/trucks | Create truck |
| GET | /api/trucks | List trucks |
| GET | /api/trucks/{id} | Get truck |
| PUT | /api/trucks/{id} | Update truck |
| DELETE | /api/trucks/{id} | Delete truck |
| POST | /api/trailers | Create trailer |
| GET | /api/trailers | List trailers |
| GET | /api/trailers/{id} | Get trailer |
| PUT | /api/trailers/{id} | Update trailer |
| DELETE | /api/trailers/{id} | Delete trailer |
| POST | /api/drivers | Create driver |
| GET | /api/drivers | List drivers |
| GET | /api/drivers/{id} | Get driver |
| PUT | /api/drivers/{id} | Update driver |
| DELETE | /api/drivers/{id} | Delete driver |

### 4.6 Master Data Service

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/locations | Create location |
| GET | /api/locations | List locations |
| GET | /api/locations/{id} | Get location |
| PUT | /api/locations/{id} | Update location |
| DELETE | /api/locations/{id} | Delete location |
| POST | /api/vendors | Create vendor |
| GET | /api/vendors | List vendors |
| GET | /api/vendors/{id} | Get vendor |
| PUT | /api/vendors/{id} | Update vendor |
| DELETE | /api/vendors/{id} | Delete vendor |
| POST | /api/customers | Create customer |
| GET | /api/customers | List customers |
| GET | /api/customers/{id} | Get customer |
| PUT | /api/customers/{id} | Update customer |
| DELETE | /api/customers/{id} | Delete customer |
| POST | /api/items | Create item/service |
| GET | /api/items | List items |
| GET | /api/items/{id} | Get item |
| PUT | /api/items/{id} | Update item |
| DELETE | /api/items/{id} | Delete item |
| GET | /api/settings | Get company settings |
| PUT | /api/settings | Update company settings |

### 4.7 AI Service (NEW)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/ai/status | Ollama availability + installed models |
| POST | /api/ai/chat | Natural-language chat over live ERP data |
| POST | /api/ai/extract-document | OCR document data extraction (multipart upload) |
| POST | /api/ai/predict-eta | Delay/ETA prediction for a job |
| GET | /api/ai/reports/weekly | Weekly operations report (stats + narrative) |
| POST | /api/ai/assist/job | Smart suggestions + AI tip for a job |

> **Auth note**: All endpoints require a Bearer JWT. The AI Service validates the token itself and relays it to the gateway when fetching ERP context, preserving per-service RBAC.

---

## 5. Database Schema

### 5.1 Auth Service Schema

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 5.2 Import Service Schema

```sql
CREATE TABLE import_jobs (
    id UUID PRIMARY KEY,
    job_number VARCHAR(50) UNIQUE NOT NULL,
    container_number VARCHAR(50),
    vessel_name VARCHAR(255),
    eta TIMESTAMP,
    ata TIMESTAMP,
    bl_number VARCHAR(100),
    consignee VARCHAR(255),
    cargo_description TEXT,
    quantity DECIMAL,
    status VARCHAR(50) DEFAULT 'PENDING_APPROVAL',
    license_required BOOLEAN DEFAULT FALSE,
    license_approved BOOLEAN DEFAULT FALSE,
    customs_permit_status VARCHAR(50),
    truck_id UUID,
    trailer_id UUID,
    driver_id UUID,
    vendor_id UUID,
    is_outsourced BOOLEAN DEFAULT FALSE,
    pickup_schedule TIMESTAMP,
    delivery_location_id UUID,
    eir_number VARCHAR(100),
    created_by UUID,
    assigned_team TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE activity_logs (
    id UUID PRIMARY KEY,
    job_id UUID NOT NULL REFERENCES import_jobs(id),
    action VARCHAR(100) NOT NULL,
    description TEXT,
    old_value TEXT,
    new_value TEXT,
    performed_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE job_documents (
    id UUID PRIMARY KEY,
    job_id UUID NOT NULL REFERENCES import_jobs(id),
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(100),
    file_size INTEGER,
    file_path VARCHAR(500),
    description VARCHAR(255),
    uploaded_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE job_templates (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    container_number VARCHAR(50),
    vessel_name VARCHAR(255),
    cargo_description TEXT,
    quantity DECIMAL,
    license_required BOOLEAN DEFAULT FALSE,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE invoices (
    id UUID PRIMARY KEY,
    job_id UUID NOT NULL REFERENCES import_jobs(id),
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    customer_name VARCHAR(255),
    issue_date TIMESTAMP,
    due_date TIMESTAMP,
    status VARCHAR(50) DEFAULT 'DRAFT',
    subtotal DECIMAL DEFAULT 0,
    tax_rate DECIMAL DEFAULT 0,
    tax DECIMAL DEFAULT 0,
    total DECIMAL DEFAULT 0,
    notes TEXT,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE invoice_lines (
    id UUID PRIMARY KEY,
    invoice_id UUID NOT NULL REFERENCES invoices(id),
    description VARCHAR(255) NOT NULL,
    quantity DECIMAL DEFAULT 1,
    unit_price DECIMAL DEFAULT 0,
    amount DECIMAL DEFAULT 0,
    coa VARCHAR(50)
);

CREATE TABLE export_jobs (
    id UUID PRIMARY KEY,
    job_number VARCHAR(50) UNIQUE NOT NULL,
    container_number VARCHAR(50),
    vessel_name VARCHAR(255),
    etd TIMESTAMP,
    atd TIMESTAMP,
    bl_number VARCHAR(100),
    shipper VARCHAR(255),
    consignee VARCHAR(255),
    cargo_description TEXT,
    quantity DECIMAL,
    status VARCHAR(50) DEFAULT 'PENDING_APPROVAL',
    license_required BOOLEAN DEFAULT FALSE,
    license_approved BOOLEAN DEFAULT FALSE,
    customs_permit_status VARCHAR(50),
    truck_id UUID,
    trailer_id UUID,
    driver_id UUID,
    vendor_id UUID,
    is_outsourced BOOLEAN DEFAULT FALSE,
    empty_pickup_date TIMESTAMP,
    stuffing_location_id UUID,
    gate_in_date TIMESTAMP,
    eir_number VARCHAR(100),
    created_by UUID,
    assigned_team TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE export_activity_logs (
    id UUID PRIMARY KEY,
    job_id UUID NOT NULL REFERENCES export_jobs(id),
    action VARCHAR(100) NOT NULL,
    description TEXT,
    old_value TEXT,
    new_value TEXT,
    performed_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE export_documents (
    id UUID PRIMARY KEY,
    job_id UUID NOT NULL REFERENCES export_jobs(id),
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(100),
    file_size INTEGER,
    file_path VARCHAR(500),
    description VARCHAR(255),
    uploaded_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 5.3 Fleet Service Schema

```sql
CREATE TABLE trucks (
    id UUID PRIMARY KEY,
    plate_number VARCHAR(50) UNIQUE NOT NULL,
    driver_name VARCHAR(255),
    brand VARCHAR(100),
    model VARCHAR(100),
    year_of_manufacture INTEGER,
    status VARCHAR(50) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE trailers (
    id UUID PRIMARY KEY,
    trailer_number VARCHAR(50) UNIQUE NOT NULL,
    trailer_size VARCHAR(50),
    status VARCHAR(50) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE drivers (
    id UUID PRIMARY KEY,
    identification_card_number VARCHAR(50) UNIQUE NOT NULL,
    ic_issued_date DATE,
    ic_expired_date DATE,
    company_ic_number VARCHAR(50),
    company_ic_issued_date DATE,
    company_ic_expired_date DATE,
    driving_license_number VARCHAR(50) UNIQUE NOT NULL,
    license_type VARCHAR(50),
    license_issued_date DATE,
    license_expired_date DATE,
    status VARCHAR(50) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 5.4 Master Data Service Schema

```sql
CREATE TABLE locations (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    coordinate_x FLOAT,
    coordinate_y FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE vendors (
    id UUID PRIMARY KEY,
    name_kh VARCHAR(255) NOT NULL,
    name_eng VARCHAR(255) NOT NULL,
    address_1 VARCHAR(255),
    contact_person_order VARCHAR(255),
    address_2 VARCHAR(255),
    contact_person_complaint VARCHAR(255),
    tin VARCHAR(50),
    credit_term INTEGER,
    credit_limit DECIMAL,
    bank_name VARCHAR(255),
    account_name VARCHAR(255),
    account_number VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE customers (
    id UUID PRIMARY KEY,
    name_kh VARCHAR(255) NOT NULL,
    name_eng VARCHAR(255) NOT NULL,
    address_1 VARCHAR(255),
    contact_person_order VARCHAR(255),
    address_2 VARCHAR(255),
    contact_person_payment VARCHAR(255),
    tin VARCHAR(50),
    credit_term INTEGER,
    credit_limit DECIMAL,
    sales_person VARCHAR(255),
    bank_name VARCHAR(255),
    account_name VARCHAR(255),
    account_number VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE items (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    min_qty DECIMAL,
    delivery_lead_time INTEGER,
    purchase_coa VARCHAR(50),
    sale_coa VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE company_settings (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    logo TEXT,
    address VARCHAR(500),
    phone VARCHAR(100),
    email VARCHAR(255),
    website VARCHAR(255),
    tin VARCHAR(50),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 5.5 AI Service

The AI Service has **no database** — it reads live data by relaying the caller's JWT through the API Gateway to the relevant services, and calls Ollama (`http://localhost:11434`) for inference.

| Model | Purpose | Default |
|-------|---------|---------|
| `OLLAMA_TEXT_MODEL` | Chat, reports, tips | `qwen2.5:1.5b` |
| `OLLAMA_VISION_MODEL` | Document OCR extraction | `llava:7b` |

---

## 6. UI/UX Requirements

### 6.1 Pages

1. **Login Page** — Authentication
2. **Dashboard** — Overview of jobs, status summary, KPI stat cards
3. **Reports** — Operational reports
4. **Calendar** — Job schedule view
5. **Templates** — Manage reusable job templates
6. **AI Reports** — AI-generated weekly operations report
7. **Import Job List** — View/search/filter/approve/reject import jobs
8. **Import Job Detail** — View/update import job status, documents, activity log, AI assist
9. **Create Import Job** — Form to create new import job
10. **Export Job List** — View/search/filter/approve/reject export jobs
11. **Export Job Detail** — View/update export job status, documents, activity log, AI assist
12. **Create Export Job** — Form to create new export job
13. **Invoices** — View/manage invoices with line items
14. **Truck Management** — CRUD for trucks
15. **Trailer Management** — CRUD for trailers
16. **Driver Management** — CRUD for drivers
17. **Location Management** — CRUD for locations
18. **Vendor Management** — CRUD for vendors
19. **Customer Management** — CRUD for customers
20. **Item/Service Management** — CRUD for items
21. **User Management** — Admin-only user CRUD
22. **Settings** — Company settings

### 6.2 Global Components
- **AI Chat Assistant** — floating chat widget available on all pages; shows online/offline status; quick-question chips; offline fallback mode badge
- **AI Assist Panel** — embedded in both job detail pages: predicted arrival/departure, delay risk, confidence, actionable next-step suggestions, OCR document extract with one-click apply
- **Global Search** — jobs, trucks, customers, vendors
- **Notifications** — driver ID/license expiry, past ETA/ETD alerts
- **Print Cards** — printable import and export job cards
- **Dark Mode** — full theme toggle

### 6.3 Import Job Status Flow

```
PENDING_APPROVAL → APPROVED → (LICENSE_APPROVED) → PERMIT_SUBMITTED →
TRUCK_ASSIGNED → VESSEL_ARRIVED → CUSTOMS_CLEARED → PICKED_UP →
DELIVERED → UNLOADED → CONTAINER_RETURNED → CLOSED

Branches: REJECTED (from PENDING_APPROVAL), TEAM_ASSIGNED (from APPROVED)
```

### 6.4 Export Job Status Flow

```
PENDING_APPROVAL → APPROVED → TEAM_ASSIGNED → (LICENSE_APPROVED) →
PERMIT_SUBMITTED → TRUCK_ASSIGNED → EMPTY_PICKED_UP → STUFFED →
GATE_IN → VESSEL_DEPARTED → EXPORT_CLEARED → CLOSED

Branches: REJECTED (from PENDING_APPROVAL)
```

---

## 7. Acceptance Criteria

### 7.1 Import Job Management
- [ ] User can create new import job with all required fields
- [ ] User can view list of all import jobs with filtering/search
- [ ] User can approve/reject jobs
- [ ] System tracks job status through all phases
- [ ] User can assign trucks (internal or outsourced)
- [ ] User can record vessel arrival, customs clearance, delivery
- [ ] User can attach/delete documents and view activity history

### 7.2 Export Job Management (NEW)
- [ ] User can create new export job with all required fields
- [ ] User can view list of all export jobs with filtering/search
- [ ] User can approve/reject export jobs
- [ ] System tracks export job status through all phases
- [ ] User can assign trucks (internal or outsourced)
- [ ] User can record empty pickup, stuffing, gate-in (EIR), vessel departure, clearance
- [ ] User can attach/delete export documents and view activity history

### 7.3 Fleet Management
- [ ] User can add/edit/delete trucks
- [ ] User can add/edit/delete trailers
- [ ] User can add/edit/delete drivers with all document dates

### 7.4 Master Data
- [ ] User can manage locations with coordinates
- [ ] User can manage vendors with credit terms
- [ ] User can manage customers with credit terms
- [ ] User can manage items/services with COA codes
- [ ] User can manage company settings

### 7.5 Invoicing & Templates (NEW)
- [ ] User can create invoices per job with line items and auto totals
- [ ] User can manage invoice status
- [ ] User can create/use job templates

### 7.6 AI Features (NEW)
- [ ] Chat assistant answers questions from live ERP data (Ollama online) and degrades to offline summaries when Ollama is down
- [ ] Document upload extracts BL/container/vessel/date fields via vision OCR
- [ ] Extracted OCR fields can be applied to a job
- [ ] Delay/ETA prediction returns predicted date, risk and confidence
- [ ] Weekly AI report shows 7-day stats and narrative
- [ ] Job assist surfaces next step, missing fields and anomaly warnings

### 7.7 Authentication & Authorization
- [ ] JWT-based authentication
- [ ] Role-based access control (admin/manager/staff), admin-only destructive actions

---

## 8. Project Structure

```
erp-system/
├── api-gateway/
│   ├── main.py              # routing/proxy to all services (incl. /api/ai)
│   └── requirements.txt
├── auth-service/
│   ├── main.py
│   ├── database/
│   │   ├── database.py
│   │   └── security.py
│   ├── models/
│   ├── routers/
│   ├── schemas/
│   └── requirements.txt
├── import-service/
│   ├── main.py              # import + export + invoices + templates + documents
│   ├── database/
│   │   ├── database.py
│   │   └── security.py
│   ├── models/models.py     # ImportJob, ExportJob, ActivityLog, ExportActivityLog,
│   │                        # JobDocument, ExportDocument, JobTemplate, Invoice, InvoiceLine
│   ├── routers/
│   │   ├── jobs.py
│   │   └── exports.py
│   ├── schemas/schemas.py
│   └── requirements.txt
├── fleet-service/
│   ├── main.py
│   ├── database/
│   ├── models/
│   ├── routers/
│   ├── schemas/
│   └── requirements.txt
├── master-data-service/
│   ├── main.py
│   ├── database/
│   ├── models/
│   ├── routers/
│   ├── schemas/
│   └── requirements.txt
├── ai-service/
│   ├── main.py              # AI endpoints, CORS
│   ├── database/security.py # JWT validation (token relay)
│   ├── ollama_client.py     # Ollama chat/generate + vision helpers
│   ├── erp_client.py        # Live ERP context via gateway (token relay)
│   ├── routers/ai.py        # status, chat, extract-document, predict-eta,
│   │                        # reports/weekly, assist/job
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.tsx          # all pages, components, routes, auth, AI widget
    │   └── index.css
    ├── package.json
    └── vite.config.ts
```

---

## 9. Setup & Running

### Backend
Run `start-backend.bat` (Windows) or start each service with uvicorn:

| Service | Command |
|---------|---------|
| Auth | `uvicorn main:app --port 8001` |
| Import | `uvicorn main:app --port 8002` |
| Fleet | `uvicorn main:app --port 8003` |
| Master Data | `uvicorn main:app --port 8004` |
| AI | `uvicorn main:app --port 8005` |
| Gateway | `uvicorn main:app --port 8000` |

### Frontend
```
cd frontend
npm install
npm run dev
```

### AI (Ollama)
1. Install [Ollama](https://ollama.com)
2. Pull models:
   ```
   ollama pull qwen2.5:1.5b
   ollama pull llava:7b
   ```
3. Optional overrides (env vars on the AI Service):
   - `OLLAMA_TEXT_MODEL` (default `qwen2.5:1.5b`)
   - `OLLAMA_VISION_MODEL` (default `llava:7b`)

All AI features degrade to offline rule-based mode if Ollama is not running.
