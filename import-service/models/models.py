import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Numeric, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database.database import Base

class ImportJob(Base):
    __tablename__ = "import_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_number = Column(String(50), unique=True, nullable=False, index=True)
    container_number = Column(String(50))
    container_id = Column(UUID(as_uuid=True), nullable=True)
    vessel_name = Column(String(255))
    eta = Column(DateTime)
    ata = Column(DateTime)
    bl_number = Column(String(100))
    consignee = Column(String(255))
    cargo_description = Column(Text)
    quantity = Column(Numeric(12, 2))
    status = Column(String(50), default="PENDING_APPROVAL")
    license_required = Column(Boolean, default=False)
    license_approved = Column(Boolean, default=False)
    customs_permit_status = Column(String(50))
    truck_id = Column(UUID(as_uuid=True), nullable=True)
    trailer_id = Column(UUID(as_uuid=True), nullable=True)
    driver_id = Column(UUID(as_uuid=True), nullable=True)
    vendor_id = Column(UUID(as_uuid=True), nullable=True)
    is_outsourced = Column(Boolean, default=False)
    pickup_schedule = Column(DateTime)
    delivery_location_id = Column(UUID(as_uuid=True), nullable=True)
    eir_number = Column(String(100))
    created_by = Column(UUID(as_uuid=True))
    assigned_team = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    invoices = relationship("Invoice", back_populates="job", cascade="all, delete-orphan")

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("import_jobs.id"), nullable=False)
    action = Column(String(100), nullable=False)
    description = Column(Text)
    old_value = Column(Text)
    new_value = Column(Text)
    performed_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

class JobDocument(Base):
    __tablename__ = "job_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("import_jobs.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(100))
    file_size = Column(Integer)
    file_path = Column(String(500))
    description = Column(String(255))
    uploaded_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

class JobTemplate(Base):
    __tablename__ = "job_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    container_number = Column(String(50))
    vessel_name = Column(String(255))
    cargo_description = Column(Text)
    quantity = Column(Numeric(12, 2))
    license_required = Column(Boolean, default=False)
    created_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("import_jobs.id"), nullable=False)
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    customer_name = Column(String(255))
    issue_date = Column(DateTime)
    due_date = Column(DateTime)
    status = Column(String(50), default="DRAFT")
    subtotal = Column(Numeric(12, 2), default=0)
    tax_rate = Column(Numeric(5, 2), default=0)
    tax = Column(Numeric(12, 2), default=0)
    total = Column(Numeric(12, 2), default=0)
    notes = Column(Text)
    created_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    job = relationship("ImportJob", back_populates="invoices")
    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")

class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False)
    description = Column(String(255), nullable=False)
    quantity = Column(Numeric(12, 2), default=1)
    unit_price = Column(Numeric(12, 2), default=0)
    amount = Column(Numeric(12, 2), default=0)
    coa = Column(String(50))

    invoice = relationship("Invoice", back_populates="lines")

class ExportJob(Base):
    __tablename__ = "export_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_number = Column(String(50), unique=True, nullable=False, index=True)
    container_number = Column(String(50))
    container_id = Column(UUID(as_uuid=True), nullable=True)
    vessel_name = Column(String(255))
    etd = Column(DateTime)
    atd = Column(DateTime)
    bl_number = Column(String(100))
    shipper = Column(String(255))
    consignee = Column(String(255))
    cargo_description = Column(Text)
    quantity = Column(Numeric(12, 2))
    status = Column(String(50), default="PENDING_APPROVAL")
    license_required = Column(Boolean, default=False)
    license_approved = Column(Boolean, default=False)
    customs_permit_status = Column(String(50))
    truck_id = Column(UUID(as_uuid=True), nullable=True)
    trailer_id = Column(UUID(as_uuid=True), nullable=True)
    driver_id = Column(UUID(as_uuid=True), nullable=True)
    vendor_id = Column(UUID(as_uuid=True), nullable=True)
    is_outsourced = Column(Boolean, default=False)
    empty_pickup_date = Column(DateTime)
    stuffing_location_id = Column(UUID(as_uuid=True), nullable=True)
    gate_in_date = Column(DateTime)
    eir_number = Column(String(100))
    created_by = Column(UUID(as_uuid=True))
    assigned_team = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ExportActivityLog(Base):
    __tablename__ = "export_activity_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("export_jobs.id"), nullable=False)
    action = Column(String(100), nullable=False)
    description = Column(Text)
    old_value = Column(Text)
    new_value = Column(Text)
    performed_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

class ExportDocument(Base):
    __tablename__ = "export_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("export_jobs.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(100))
    file_size = Column(Integer)
    file_path = Column(String(500))
    description = Column(String(255))
    uploaded_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

class Quotation(Base):
    __tablename__ = "quotations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quote_number = Column(String(50), unique=True, nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), nullable=True)
    job_type = Column(String(20), default="import")
    customer_name = Column(String(255))
    issue_date = Column(DateTime)
    valid_until = Column(DateTime)
    status = Column(String(50), default="DRAFT")
    subtotal = Column(Numeric(12, 2), default=0)
    tax_rate = Column(Numeric(5, 2), default=0)
    tax = Column(Numeric(12, 2), default=0)
    total = Column(Numeric(12, 2), default=0)
    notes = Column(Text)
    created_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    lines = relationship("QuotationLine", back_populates="quotation", cascade="all, delete-orphan")

class QuotationLine(Base):
    __tablename__ = "quotation_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quotation_id = Column(UUID(as_uuid=True), ForeignKey("quotations.id"), nullable=False)
    description = Column(String(255), nullable=False)
    quantity = Column(Numeric(12, 2), default=1)
    unit_price = Column(Numeric(12, 2), default=0)
    amount = Column(Numeric(12, 2), default=0)
    coa = Column(String(50))

    quotation = relationship("Quotation", back_populates="lines")

class VendorBill(Base):
    __tablename__ = "vendor_bills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_number = Column(String(50), unique=True, nullable=False, index=True)
    job_id = Column(UUID(as_uuid=True), nullable=True)
    job_type = Column(String(20), default="import")
    vendor_id = Column(UUID(as_uuid=True), nullable=True)
    vendor_name = Column(String(255))
    bill_date = Column(DateTime)
    due_date = Column(DateTime)
    status = Column(String(50), default="UNPAID")
    subtotal = Column(Numeric(12, 2), default=0)
    tax_rate = Column(Numeric(5, 2), default=0)
    tax = Column(Numeric(12, 2), default=0)
    total = Column(Numeric(12, 2), default=0)
    notes = Column(Text)
    created_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    lines = relationship("BillLine", back_populates="bill", cascade="all, delete-orphan")

class BillLine(Base):
    __tablename__ = "bill_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bill_id = Column(UUID(as_uuid=True), ForeignKey("vendor_bills.id"), nullable=False)
    description = Column(String(255), nullable=False)
    quantity = Column(Numeric(12, 2), default=1)
    unit_price = Column(Numeric(12, 2), default=0)
    amount = Column(Numeric(12, 2), default=0)
    coa = Column(String(50))

    bill = relationship("VendorBill", back_populates="lines")

class JobCost(Base):
    __tablename__ = "job_costs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    job_type = Column(String(20), default="import")
    cost_type = Column(String(50), default="other")
    description = Column(String(255))
    amount = Column(Numeric(12, 2), default=0)
    vendor_id = Column(UUID(as_uuid=True), nullable=True)
    bill_id = Column(UUID(as_uuid=True), nullable=True)
    created_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    amount = Column(Numeric(12, 2), default=0)
    payment_date = Column(DateTime)
    method = Column(String(50))
    reference = Column(String(100))
    created_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

class Container(Base):
    __tablename__ = "containers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    container_number = Column(String(50), unique=True, nullable=False, index=True)
    size = Column(String(10))
    type = Column(String(20), default="DRY")
    status = Column(String(50), default="EMPTY")
    current_location_id = Column(UUID(as_uuid=True), nullable=True)
    last_event_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    events = relationship("ContainerEvent", back_populates="container", cascade="all, delete-orphan")

class ContainerEvent(Base):
    __tablename__ = "container_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    container_id = Column(UUID(as_uuid=True), ForeignKey("containers.id"), nullable=False)
    event_type = Column(String(50), nullable=False)
    event_date = Column(DateTime)
    job_id = Column(UUID(as_uuid=True), nullable=True)
    job_type = Column(String(20))
    description = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    container = relationship("Container", back_populates="events")

class AirJob(Base):
    __tablename__ = "air_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_number = Column(String(50), unique=True, nullable=False, index=True)
    awb_number = Column(String(100), index=True)
    hawb_number = Column(String(100))
    carrier = Column(String(255))
    flight_number = Column(String(50))
    origin = Column(String(255))
    destination = Column(String(255))
    etd = Column(DateTime)
    atd = Column(DateTime)
    eta = Column(DateTime)
    ata = Column(DateTime)
    shipper = Column(String(255))
    consignee = Column(String(255))
    cargo_description = Column(Text)
    total_weight_kg = Column(Numeric(12, 2))
    pieces = Column(Integer)
    status = Column(String(50), default="PENDING_APPROVAL")
    license_required = Column(Boolean, default=False)
    license_approved = Column(Boolean, default=False)
    customs_permit_status = Column(String(50))
    created_by = Column(UUID(as_uuid=True))
    assigned_team = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AirActivityLog(Base):
    __tablename__ = "air_activity_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("air_jobs.id"), nullable=False)
    action = Column(String(100), nullable=False)
    description = Column(Text)
    old_value = Column(Text)
    new_value = Column(Text)
    performed_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

class AirDocument(Base):
    __tablename__ = "air_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("air_jobs.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(100))
    file_size = Column(Integer)
    file_path = Column(String(500))
    description = Column(String(255))
    uploaded_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

class ExportCommercialInvoice(Base):
    __tablename__ = "export_commercial_invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    export_job_id = Column(UUID(as_uuid=True), ForeignKey("export_jobs.id"), nullable=False)
    invoice_no = Column(String(50), nullable=False)
    date = Column(DateTime)
    terms = Column(String(255))
    shipper = Column(String(255))
    consignee = Column(String(255))
    subtotal = Column(Numeric(12, 2), default=0)
    tax = Column(Numeric(12, 2), default=0)
    total = Column(Numeric(12, 2), default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    lines = relationship("ExportCommercialInvoiceLine", back_populates="ci", cascade="all, delete-orphan")

class ExportCommercialInvoiceLine(Base):
    __tablename__ = "export_commercial_invoice_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ci_id = Column(UUID(as_uuid=True), ForeignKey("export_commercial_invoices.id"), nullable=False)
    description = Column(String(255), nullable=False)
    quantity = Column(Numeric(12, 2), default=1)
    unit_price = Column(Numeric(12, 2), default=0)
    amount = Column(Numeric(12, 2), default=0)
    hs_code = Column(String(50))

    ci = relationship("ExportCommercialInvoice", back_populates="lines")

class ExportPackingList(Base):
    __tablename__ = "export_packing_lists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    export_job_id = Column(UUID(as_uuid=True), ForeignKey("export_jobs.id"), nullable=False)
    pl_no = Column(String(50), nullable=False)
    date = Column(DateTime)
    shipper = Column(String(255))
    consignee = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    lines = relationship("ExportPackingListLine", back_populates="pl", cascade="all, delete-orphan")

class ExportPackingListLine(Base):
    __tablename__ = "export_packing_list_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pl_id = Column(UUID(as_uuid=True), ForeignKey("export_packing_lists.id"), nullable=False)
    description = Column(String(255), nullable=False)
    quantity = Column(Numeric(12, 2), default=1)
    units = Column(String(50))
    gross_weight = Column(Numeric(12, 2), default=0)
    net_weight = Column(Numeric(12, 2), default=0)
    dimensions = Column(String(100))
    marks = Column(String(255))

    pl = relationship("ExportPackingList", back_populates="lines")
