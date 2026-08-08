from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal

class ImportJobBase(BaseModel):
    container_number: Optional[str] = None
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
