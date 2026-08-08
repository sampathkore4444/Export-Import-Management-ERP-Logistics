# ERP System - Import Management Module Specification

## 1. Project Overview

### Project Name
ERP Import Management System

### Project Type
Web-based Enterprise Resource Planning (ERP) Module

### Core Functionality
A comprehensive import management system that handles the complete lifecycle of import operations, from booking receipt to job closure, including truck/driver management, vendor/customer management, and location tracking.

### Target Users
- Operations Staff
- Warehouse Managers
- Finance/Accounting
- Management/Approvers

---

## 2. Architecture

### Microservices Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway (FastAPI)                    │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │   Auth      │ │   Import    │ │   Fleet     │ │   Master  │ │
│  │   Service   │ │   Service   │ │   Service   │ │   Data    │ │
│  │             │ │             │ │             │ │   Service │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                      PostgreSQL Database                         │
│                    (Each service has its own schema)            │
└─────────────────────────────────────────────────────────────────┘
```

### Tech Stack
- **Frontend**: ReactJS with TypeScript
- **Backend**: Python FastAPI
- **Database**: PostgreSQL
- **Authentication**: JWT-based

### Service Boundaries

| Service | Responsibility |
|---------|----------------|
| Auth Service | User authentication, roles, permissions |
| Import Service | Import job workflow, customs, delivery |
| Fleet Service | Trucks, trailers, drivers management |
| Master Data Service | Customers, vendors, locations, items |

---

## 3. Functional Requirements

### 3.1 Import Process Workflow

#### Phase 1: Job Creation
- **3.1.1** Receive and verify booking receipt (container number, vessel name, ETA, BL)
- **3.1.2** Enter booking details into system
- **3.1.3** Create job and submit for approval

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

### 3.2 Master Data Management

#### 3.2.1 Truck Setup
| Field | Type | Required |
|-------|------|----------|
| Plate Number | String | Yes |
| Driver Name | String | Yes |
| Brand | String | Yes |
| Model | String | Yes |
| Year of Manufacture | Integer | Yes |
| Status | Enum (Active, Maintenance, Retired) | Yes |

#### 3.2.2 Trailer Setup
| Field | Type | Required |
|-------|------|----------|
| Trailer Number | String | Yes |
| Trailer Size | String | Yes |
| Status | Enum (Active, Maintenance, Retired) | Yes |

#### 3.2.3 Driver Setup
| Field | Type | Required |
|-------|------|----------|
| Identification Card Number | String | Yes |
| IC Issued Date | Date | Yes |
| IC Expired Date | Date | Yes |
| Company IC Number | String | Yes |
| Company IC Issued Date | Date | Yes |
| Company IC Expired Date | Date | Yes |
| Driving License Number | String | Yes |
| Driving License Type | String | Yes |
| License Issued Date | Date | Yes |
| License Expired Date | Date | Yes |

#### 3.2.4 Location Setup
| Field | Type | Required |
|-------|------|----------|
| Location Name | String | Yes |
| Google Map X Coordinate | Float | Yes |
| Google Map Y Coordinate | Float | Yes |

#### 3.2.5 Vendor Setup
| Field | Type | Required |
|-------|------|----------|
| Name (Khmer) | String | Yes |
| Name (English) | String | Yes |
| Address 1 | String | Yes |
| Contact Person for Order | String | Yes |
| Address 2 | String | No |
| Contact Person for Complaint | String | No |
| Tax Identification Number | String | Yes |
| Credit Term | Integer | Yes |
| Credit Limit | Decimal | Yes |
| Bank Name | String | No |
| Account Name | String | No |
| Account Number | String | No |

#### 3.2.6 Customer Setup
| Field | Type | Required |
|-------|------|----------|
| Name (Khmer) | String | Yes |
| Name (English) | String | Yes |
| Address 1 | String | Yes |
| Contact Person for Order | String | Yes |
| Address 2 | String | No |
| Contact Person for Payment | String | No |
| Tax Identification Number (TIN) | String | Yes |
| Credit Term | Integer | Yes |
| Credit Limit | Decimal | Yes |
| Sales Person | String | Yes |
| Bank Name | String | No |
| Account Name | String | No |
| Account Number | String | No |

#### 3.2.7 Item/Service Setup
| Field | Type | Required |
|-------|------|----------|
| Name | String | Yes |
| Type | Enum (Service, Goods) | Yes |
| Min Qty (for Goods) | Decimal | Conditional |
| Delivery Lead Time (for Goods) | Integer | Conditional |
| Purchase COA | String | Yes |
| Sale COA | String | Yes |

---

## 4. API Specification

### 4.1 Auth Service

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/login | User login |
| POST | /api/auth/refresh | Refresh token |
| GET | /api/auth/me | Get current user |

### 4.2 Import Service

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/jobs | Create import job |
| GET | /api/jobs | List all jobs |
| GET | /api/jobs/{id} | Get job details |
| PUT | /api/jobs/{id} | Update job |
| PUT | /api/jobs/{id}/approve | Approve job |
| PUT | /api/jobs/{id}/reject | Reject job |
| PUT | /api/jobs/{id}/assign-team | Assign team |
| PUT | /api/jobs/{id}/apply-license | Apply import license |
| PUT | /api/jobs/{id}/customs-permit | Submit customs permit |
| PUT | /api/jobs/{id}/truck | Assign truck |
| PUT | /api/jobs/{id}/outsource | Outsource transport |
| PUT | /api/jobs/{id}/arrival | Record vessel arrival |
| PUT | /api/jobs/{id}/clearance | Process customs clearance |
| PUT | /api/jobs/{id}/pickup | Container pick up |
| PUT | /api/jobs/{id}/deliver | Deliver to customer |
| PUT | /api/jobs/{id}/unload | Confirm unloading |
| PUT | /api/jobs/{id}/return-container | Return empty container |
| PUT | /api/jobs/{id}/close | Close job |

### 4.3 Fleet Service

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/trucks | Create truck |
| GET | /api/trucks | List trucks |
| GET | /api/trucks/{id} | Get truck |
| PUT | /api/trucks/{id} | Update truck |
| DELETE | /api/trucks/{id} | Delete truck |
| POST | /api/trailers | Create trailer |
| GET | /api/trailers | List trailers |
| PUT | /api/trailers/{id} | Update trailer |
| POST | /api/drivers | Create driver |
| GET | /api/drivers | List drivers |
| PUT | /api/drivers/{id} | Update driver |

### 4.4 Master Data Service

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/locations | Create location |
| GET | /api/locations | List locations |
| POST | /api/vendors | Create vendor |
| GET | /api/vendors | List vendors |
| PUT | /api/vendors/{id} | Update vendor |
| POST | /api/customers | Create customer |
| GET | /api/customers | List customers |
| PUT | /api/customers/{id} | Update customer |
| POST | /api/items | Create item/service |
| GET | /api/items | List items |

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
    eta DATE,
    ata DATE,
    bl_number VARCHAR(100),
    consignee VARCHAR(255),
    cargo_description TEXT,
    quantity DECIMAL,
    status VARCHAR(50) DEFAULT 'PENDING_APPROVAL',
    license_required BOOLEAN DEFAULT FALSE,
    license_approved BOOLEAN DEFAULT FALSE,
    customs_permit_status VARCHAR(50),
    truck_id UUID,
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
```

---

## 6. UI/UX Requirements

### 6.1 Pages

1. **Login Page** - Authentication
2. **Dashboard** - Overview of import jobs, status summary
3. **Job List** - View/filter all import jobs
4. **Job Detail** - View and update job status
5. **Create Job** - Form to create new import job
6. **Truck Management** - CRUD for trucks
7. **Trailer Management** - CRUD for trailers
8. **Driver Management** - CRUD for drivers
9. **Location Management** - CRUD for locations
10. **Vendor Management** - CRUD for vendors
11. **Customer Management** - CRUD for customers
12. **Item/Service Management** - CRUD for items

### 6.2 Job Status Flow

```
PENDING_APPROVAL → APPROVED → LICENSE_APPLIED → PERMIT_SUBMITTED → 
TRUCK_ASSIGNED → VESSEL_ARRIVED → CUSTOMS_CLEARED → PICKED_UP → 
DELIVERED → UNLOADED → CONTAINER_RETURNED → CLOSED
```

---

## 7. Acceptance Criteria

### 7.1 Job Management
- [ ] User can create new import job with all required fields
- [ ] User can view list of all import jobs with filtering
- [ ] User can approve/reject jobs
- [ ] System tracks job status through all phases
- [ ] User can assign trucks (internal or outsourced)
- [ ] User can record vessel arrival, customs clearance, delivery

### 7.2 Fleet Management
- [ ] User can add/edit/delete trucks
- [ ] User can add/edit/delete trailers
- [ ] User can add/edit/delete drivers with all document dates

### 7.3 Master Data
- [ ] User can manage locations with coordinates
- [ ] User can manage vendors with credit terms
- [ ] User can manage customers with credit terms
- [ ] User can manage items/services with COA codes

### 7.4 Authentication
- [ ] JWT-based authentication
- [ ] Role-based access control

---

## 8. Project Structure

```
erp-system/
├── api-gateway/
│   ├── main.py
│   └── requirements.txt
├── auth-service/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   └── requirements.txt
├── import-service/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   └── requirements.txt
├── fleet-service/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   └── requirements.txt
├── master-data-service/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── database.py
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── components/
    │   ├── pages/
    │   ├── services/
    │   └── App.tsx
    ├── package.json
    └── vite.config.ts
```
