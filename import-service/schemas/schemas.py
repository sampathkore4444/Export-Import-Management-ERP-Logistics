from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal

class ImportJobBase(BaseModel):
    container_number: Optional[str] = None
    container_id: Optional[UUID] = None
    vessel_name: Optional[str] = None
    eta: Optional[datetime] = None
    bl_number: Optional[str] = None
    consignee: Optional[str] = None
    cargo_description: Optional[str] = None
    quantity: Optional[Decimal] = None
    license_required: bool = False

class ImportJobCreate(ImportJobBase):
    pass

class ImportJobUpdate(BaseModel):
    container_number: Optional[str] = None
    container_id: Optional[UUID] = None
    vessel_name: Optional[str] = None
    eta: Optional[datetime] = None
    ata: Optional[datetime] = None
    bl_number: Optional[str] = None
    consignee: Optional[str] = None
    cargo_description: Optional[str] = None
    quantity: Optional[Decimal] = None
    license_required: Optional[bool] = None
    license_approved: Optional[bool] = None
    customs_permit_status: Optional[str] = None
    truck_id: Optional[UUID] = None
    trailer_id: Optional[UUID] = None
    driver_id: Optional[UUID] = None
    vendor_id: Optional[UUID] = None
    is_outsourced: Optional[bool] = None
    pickup_schedule: Optional[datetime] = None
    delivery_location_id: Optional[UUID] = None
    eir_number: Optional[str] = None
    assigned_team: Optional[str] = None

class ImportJobResponse(ImportJobBase):
    id: UUID
    job_number: str
    ata: Optional[datetime]
    status: str
    license_approved: bool
    customs_permit_status: Optional[str]
    truck_id: Optional[UUID]
    trailer_id: Optional[UUID]
    driver_id: Optional[UUID]
    vendor_id: Optional[UUID]
    is_outsourced: bool
    pickup_schedule: Optional[datetime]
    delivery_location_id: Optional[UUID]
    eir_number: Optional[str]
    created_by: Optional[UUID]
    assigned_team: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class JobStatusUpdate(BaseModel):
    status: str

class TruckAssignment(BaseModel):
    truck_id: UUID
    trailer_id: Optional[UUID] = None
    driver_id: Optional[UUID] = None
    is_outsourced: bool = False
    vendor_id: Optional[UUID] = None

class VesselArrival(BaseModel):
    ata: datetime

class CustomsClearance(BaseModel):
    customs_permit_status: str
    eir_number: Optional[str] = None

class DeliveryUpdate(BaseModel):
    delivery_location_id: UUID
    eir_number: Optional[str] = None

class ActivityLogResponse(BaseModel):
    id: UUID
    job_id: UUID
    action: str
    description: Optional[str]
    old_value: Optional[str]
    new_value: Optional[str]
    performed_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class JobDocumentCreate(BaseModel):
    filename: str
    data_base64: str
    file_type: Optional[str] = None
    description: Optional[str] = None

class JobDocumentResponse(BaseModel):
    id: UUID
    job_id: UUID
    filename: str
    file_type: Optional[str]
    file_size: Optional[int]
    description: Optional[str]
    uploaded_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class JobTemplateBase(BaseModel):
    name: str
    container_number: Optional[str] = None
    vessel_name: Optional[str] = None
    cargo_description: Optional[str] = None
    quantity: Optional[Decimal] = None
    license_required: bool = False

class JobTemplateCreate(JobTemplateBase):
    pass

class JobTemplateUpdate(BaseModel):
    name: Optional[str] = None
    container_number: Optional[str] = None
    vessel_name: Optional[str] = None
    cargo_description: Optional[str] = None
    quantity: Optional[Decimal] = None
    license_required: Optional[bool] = None

class JobTemplateResponse(JobTemplateBase):
    id: UUID
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class InvoiceLineCreate(BaseModel):
    description: str
    quantity: Decimal = Decimal("1")
    unit_price: Decimal = Decimal("0")
    coa: Optional[str] = None

class InvoiceLineResponse(BaseModel):
    id: UUID
    invoice_id: UUID
    description: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal
    coa: Optional[str]

    class Config:
        from_attributes = True

class InvoiceCreate(BaseModel):
    customer_name: Optional[str] = None
    issue_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    status: str = "DRAFT"
    tax_rate: Decimal = Decimal("0")
    notes: Optional[str] = None
    lines: List[InvoiceLineCreate] = []

class InvoiceUpdate(BaseModel):
    customer_name: Optional[str] = None
    issue_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = None
    tax_rate: Optional[Decimal] = None
    notes: Optional[str] = None

class InvoiceResponse(BaseModel):
    id: UUID
    job_id: UUID
    invoice_number: str
    customer_name: Optional[str]
    issue_date: Optional[datetime]
    due_date: Optional[datetime]
    status: str
    subtotal: Decimal
    tax_rate: Decimal
    tax: Decimal
    total: Decimal
    notes: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    lines: List[InvoiceLineResponse] = []

    class Config:
        from_attributes = True

class ExportJobBase(BaseModel):
    container_number: Optional[str] = None
    container_id: Optional[UUID] = None
    vessel_name: Optional[str] = None
    etd: Optional[datetime] = None
    bl_number: Optional[str] = None
    shipper: Optional[str] = None
    consignee: Optional[str] = None
    cargo_description: Optional[str] = None
    quantity: Optional[Decimal] = None
    license_required: bool = False

class ExportJobCreate(ExportJobBase):
    pass

class ExportJobUpdate(BaseModel):
    container_number: Optional[str] = None
    container_id: Optional[UUID] = None
    vessel_name: Optional[str] = None
    etd: Optional[datetime] = None
    atd: Optional[datetime] = None
    bl_number: Optional[str] = None
    shipper: Optional[str] = None
    consignee: Optional[str] = None
    cargo_description: Optional[str] = None
    quantity: Optional[Decimal] = None
    license_required: Optional[bool] = None
    license_approved: Optional[bool] = None
    customs_permit_status: Optional[str] = None
    truck_id: Optional[UUID] = None
    trailer_id: Optional[UUID] = None
    driver_id: Optional[UUID] = None
    vendor_id: Optional[UUID] = None
    is_outsourced: Optional[bool] = None
    empty_pickup_date: Optional[datetime] = None
    stuffing_location_id: Optional[UUID] = None
    gate_in_date: Optional[datetime] = None
    eir_number: Optional[str] = None
    assigned_team: Optional[str] = None

class ExportJobResponse(ExportJobBase):
    id: UUID
    job_number: str
    atd: Optional[datetime]
    status: str
    license_approved: bool
    customs_permit_status: Optional[str]
    truck_id: Optional[UUID]
    trailer_id: Optional[UUID]
    driver_id: Optional[UUID]
    vendor_id: Optional[UUID]
    is_outsourced: bool
    empty_pickup_date: Optional[datetime]
    stuffing_location_id: Optional[UUID]
    gate_in_date: Optional[datetime]
    eir_number: Optional[str]
    created_by: Optional[UUID]
    assigned_team: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ExportTruckAssignment(BaseModel):
    truck_id: UUID
    trailer_id: Optional[UUID] = None
    driver_id: Optional[UUID] = None
    is_outsourced: bool = False
    vendor_id: Optional[UUID] = None

class ExportDeparture(BaseModel):
    atd: datetime

class ExportClearance(BaseModel):
    customs_permit_status: str

class ExportGateIn(BaseModel):
    eir_number: Optional[str] = None

class ExportActivityLogResponse(BaseModel):
    id: UUID
    job_id: UUID
    action: str
    description: Optional[str]
    old_value: Optional[str]
    new_value: Optional[str]
    performed_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class ExportDocumentCreate(BaseModel):
    filename: str
    data_base64: str
    file_type: Optional[str] = None
    description: Optional[str] = None

class ExportDocumentResponse(BaseModel):
    id: UUID
    job_id: UUID
    filename: str
    file_type: Optional[str]
    file_size: Optional[int]
    description: Optional[str]
    uploaded_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ---- Finance: Quotations ----
class QuotationLineCreate(BaseModel):
    description: str
    quantity: Decimal = Decimal("1")
    unit_price: Decimal = Decimal("0")
    coa: Optional[str] = None

class QuotationLineResponse(BaseModel):
    id: UUID
    quotation_id: UUID
    description: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal
    coa: Optional[str]

    class Config:
        from_attributes = True

class QuotationCreate(BaseModel):
    job_id: Optional[UUID] = None
    job_type: str = "import"
    customer_name: Optional[str] = None
    issue_date: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    status: str = "DRAFT"
    tax_rate: Decimal = Decimal("0")
    notes: Optional[str] = None
    lines: List[QuotationLineCreate] = []

class QuotationUpdate(BaseModel):
    customer_name: Optional[str] = None
    issue_date: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    status: Optional[str] = None
    tax_rate: Optional[Decimal] = None
    notes: Optional[str] = None

class QuotationResponse(BaseModel):
    id: UUID
    quote_number: str
    job_id: Optional[UUID]
    job_type: str
    customer_name: Optional[str]
    issue_date: Optional[datetime]
    valid_until: Optional[datetime]
    status: str
    subtotal: Decimal
    tax_rate: Decimal
    tax: Decimal
    total: Decimal
    notes: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    lines: List[QuotationLineResponse] = []

    class Config:
        from_attributes = True

# ---- Finance: Vendor Bills ----
class BillLineCreate(BaseModel):
    description: str
    quantity: Decimal = Decimal("1")
    unit_price: Decimal = Decimal("0")
    coa: Optional[str] = None

class BillLineResponse(BaseModel):
    id: UUID
    bill_id: UUID
    description: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal
    coa: Optional[str]

    class Config:
        from_attributes = True

class BillCreate(BaseModel):
    job_id: Optional[UUID] = None
    job_type: str = "import"
    vendor_id: Optional[UUID] = None
    vendor_name: Optional[str] = None
    bill_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    status: str = "UNPAID"
    tax_rate: Decimal = Decimal("0")
    notes: Optional[str] = None
    lines: List[BillLineCreate] = []

class BillUpdate(BaseModel):
    vendor_name: Optional[str] = None
    bill_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = None
    tax_rate: Optional[Decimal] = None
    notes: Optional[str] = None

class BillResponse(BaseModel):
    id: UUID
    bill_number: str
    job_id: Optional[UUID]
    job_type: str
    vendor_id: Optional[UUID]
    vendor_name: Optional[str]
    bill_date: Optional[datetime]
    due_date: Optional[datetime]
    status: str
    subtotal: Decimal
    tax_rate: Decimal
    tax: Decimal
    total: Decimal
    notes: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    lines: List[BillLineResponse] = []

    class Config:
        from_attributes = True

# ---- Finance: Job Costs ----
class JobCostCreate(BaseModel):
    cost_type: str = "other"
    description: Optional[str] = None
    amount: Decimal = Decimal("0")
    vendor_id: Optional[UUID] = None
    bill_id: Optional[UUID] = None

class JobCostUpdate(BaseModel):
    cost_type: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    vendor_id: Optional[UUID] = None
    bill_id: Optional[UUID] = None

class JobCostResponse(BaseModel):
    id: UUID
    job_id: UUID
    job_type: str
    cost_type: str
    description: Optional[str]
    amount: Decimal
    vendor_id: Optional[UUID]
    bill_id: Optional[UUID]
    created_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ---- Finance: Payments ----
class PaymentCreate(BaseModel):
    invoice_id: UUID
    amount: Decimal
    payment_date: Optional[datetime] = None
    method: Optional[str] = None
    reference: Optional[str] = None

class PaymentResponse(BaseModel):
    id: UUID
    invoice_id: UUID
    amount: Decimal
    payment_date: Optional[datetime]
    method: Optional[str]
    reference: Optional[str]
    created_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class ProfitabilityResponse(BaseModel):
    job_id: UUID
    job_type: str
    revenue: Decimal
    costs: Decimal
    profit: Decimal
    margin: float

class FinanceAnalyticsResponse(BaseModel):
    revenue_30d: Decimal
    expenses_30d: Decimal
    profit_30d: Decimal
    outstanding_invoices: Decimal
    unpaid_bills: Decimal
    invoices_issued: int
    bills_received: int
    top_customers: List[dict] = []

# ---- Containers ----
class ContainerCreate(BaseModel):
    container_number: str
    size: Optional[str] = None
    type: Optional[str] = "DRY"
    status: Optional[str] = "EMPTY"
    current_location_id: Optional[UUID] = None

class ContainerUpdate(BaseModel):
    size: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None
    current_location_id: Optional[UUID] = None

class ContainerResponse(BaseModel):
    id: UUID
    container_number: str
    size: Optional[str]
    type: Optional[str]
    status: str
    current_location_id: Optional[UUID]
    last_event_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ContainerEventCreate(BaseModel):
    event_type: str
    event_date: Optional[datetime] = None
    job_id: Optional[UUID] = None
    job_type: Optional[str] = None
    description: Optional[str] = None

class ContainerEventResponse(BaseModel):
    id: UUID
    container_id: UUID
    event_type: str
    event_date: Optional[datetime]
    job_id: Optional[UUID]
    job_type: Optional[str]
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ---- Air freight ----
class AirJobBase(BaseModel):
    awb_number: Optional[str] = None
    hawb_number: Optional[str] = None
    carrier: Optional[str] = None
    flight_number: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    etd: Optional[datetime] = None
    eta: Optional[datetime] = None
    shipper: Optional[str] = None
    consignee: Optional[str] = None
    cargo_description: Optional[str] = None
    total_weight_kg: Optional[Decimal] = None
    pieces: Optional[int] = None
    license_required: bool = False

class AirJobCreate(AirJobBase):
    pass

class AirJobUpdate(BaseModel):
    awb_number: Optional[str] = None
    hawb_number: Optional[str] = None
    carrier: Optional[str] = None
    flight_number: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    etd: Optional[datetime] = None
    atd: Optional[datetime] = None
    eta: Optional[datetime] = None
    ata: Optional[datetime] = None
    shipper: Optional[str] = None
    consignee: Optional[str] = None
    cargo_description: Optional[str] = None
    total_weight_kg: Optional[Decimal] = None
    pieces: Optional[int] = None
    license_required: Optional[bool] = None
    license_approved: Optional[bool] = None
    customs_permit_status: Optional[str] = None
    assigned_team: Optional[str] = None

class AirJobResponse(AirJobBase):
    id: UUID
    job_number: str
    atd: Optional[datetime]
    ata: Optional[datetime]
    status: str
    license_approved: bool
    customs_permit_status: Optional[str]
    created_by: Optional[UUID]
    assigned_team: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AirDeparture(BaseModel):
    atd: datetime

class AirArrival(BaseModel):
    ata: datetime

class AirActivityLogResponse(BaseModel):
    id: UUID
    job_id: UUID
    action: str
    description: Optional[str]
    old_value: Optional[str]
    new_value: Optional[str]
    performed_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class AirDocumentCreate(BaseModel):
    filename: str
    data_base64: str
    file_type: Optional[str] = None
    description: Optional[str] = None

class AirDocumentResponse(BaseModel):
    id: UUID
    job_id: UUID
    filename: str
    file_type: Optional[str]
    file_size: Optional[int]
    description: Optional[str]
    uploaded_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ---- Export structured docs ----
class CommercialInvoiceLineCreate(BaseModel):
    description: str
    quantity: Decimal = Decimal("1")
    unit_price: Decimal = Decimal("0")
    hs_code: Optional[str] = None

class CommercialInvoiceLineResponse(BaseModel):
    id: UUID
    ci_id: UUID
    description: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal
    hs_code: Optional[str]

    class Config:
        from_attributes = True

class CommercialInvoiceCreate(BaseModel):
    invoice_no: Optional[str] = None
    date: Optional[datetime] = None
    terms: Optional[str] = None
    shipper: Optional[str] = None
    consignee: Optional[str] = None
    lines: List[CommercialInvoiceLineCreate] = []

class CommercialInvoiceUpdate(BaseModel):
    invoice_no: Optional[str] = None
    date: Optional[datetime] = None
    terms: Optional[str] = None
    shipper: Optional[str] = None
    consignee: Optional[str] = None

class CommercialInvoiceResponse(BaseModel):
    id: UUID
    export_job_id: UUID
    invoice_no: str
    date: Optional[datetime]
    terms: Optional[str]
    shipper: Optional[str]
    consignee: Optional[str]
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    created_at: datetime
    updated_at: datetime
    lines: List[CommercialInvoiceLineResponse] = []

    class Config:
        from_attributes = True

class PackingListLineCreate(BaseModel):
    description: str
    quantity: Decimal = Decimal("1")
    units: Optional[str] = None
    gross_weight: Decimal = Decimal("0")
    net_weight: Decimal = Decimal("0")
    dimensions: Optional[str] = None
    marks: Optional[str] = None

class PackingListLineResponse(BaseModel):
    id: UUID
    pl_id: UUID
    description: str
    quantity: Decimal
    units: Optional[str]
    gross_weight: Decimal
    net_weight: Decimal
    dimensions: Optional[str]
    marks: Optional[str]

    class Config:
        from_attributes = True

class PackingListCreate(BaseModel):
    pl_no: Optional[str] = None
    date: Optional[datetime] = None
    shipper: Optional[str] = None
    consignee: Optional[str] = None
    lines: List[PackingListLineCreate] = []

class PackingListUpdate(BaseModel):
    pl_no: Optional[str] = None
    date: Optional[datetime] = None
    shipper: Optional[str] = None
    consignee: Optional[str] = None

class PackingListResponse(BaseModel):
    id: UUID
    export_job_id: UUID
    pl_no: str
    date: Optional[datetime]
    shipper: Optional[str]
    consignee: Optional[str]
    created_at: datetime
    updated_at: datetime
    lines: List[PackingListLineResponse] = []

    class Config:
        from_attributes = True
