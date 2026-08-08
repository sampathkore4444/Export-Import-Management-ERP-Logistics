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
