import base64
import os
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.database import get_db
from database.security import get_current_user, get_optional_user, require_roles
from models.models import (
    ImportJob, ActivityLog, JobDocument, JobTemplate, Invoice, InvoiceLine
)
from schemas.schemas import (
    ImportJobCreate, ImportJobUpdate, ImportJobResponse,
    TruckAssignment, VesselArrival, CustomsClearance, DeliveryUpdate,
    ActivityLogResponse,
    JobDocumentCreate, JobDocumentResponse,
    JobTemplateCreate, JobTemplateUpdate, JobTemplateResponse,
    InvoiceCreate, InvoiceUpdate, InvoiceResponse, InvoiceLineCreate,
)

router = APIRouter(prefix="/api", tags=["import"])

MANAGER_ROLES = ["admin", "manager"]
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")

def generate_job_number():
    return f"IMP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

def generate_invoice_number():
    return f"INV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

def log_activity(db, job_id, action, description, old_value=None, new_value=None, performed_by=None):
    activity = ActivityLog(
        job_id=job_id,
        action=action,
        description=description,
        old_value=old_value,
        new_value=new_value,
        performed_by=performed_by
    )
    db.add(activity)
    db.commit()

def get_job_or_404(db, job_id):
    job = db.query(ImportJob).filter(ImportJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

def recalculate_invoice(db, invoice):
    subtotal = sum(
        (line.quantity or Decimal("0")) * (line.unit_price or Decimal("0"))
        for line in invoice.lines
    )
    invoice.subtotal = subtotal
    invoice.tax = (subtotal * invoice.tax_rate) / Decimal("100")
    invoice.total = invoice.subtotal + invoice.tax
    db.commit()
    db.refresh(invoice)
    return invoice

# ---- Activity logs ----
@router.get("/jobs/activities", response_model=List[ActivityLogResponse])
def list_activities(job_id: uuid.UUID = None, skip: int = 0, limit: int = 50, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    query = db.query(ActivityLog)
    if job_id:
        query = query.filter(ActivityLog.job_id == job_id)
    return query.order_by(ActivityLog.created_at.desc()).offset(skip).limit(limit).all()

# ---- Jobs ----
@router.post("/jobs", response_model=ImportJobResponse, status_code=status.HTTP_201_CREATED)
def create_job(job: ImportJobCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_job = ImportJob(
        job_number=generate_job_number(),
        created_by=uuid.UUID(user.get("user_id")) if user.get("user_id") else None,
        **job.model_dump()
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    log_activity(db, db_job.id, "CREATE", "Job created", None, "PENDING_APPROVAL", user.get("username"))
    return db_job

@router.get("/jobs", response_model=List[ImportJobResponse])
def list_jobs(skip: int = 0, limit: int = 100, status_filter: str = None, search: str = None, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    query = db.query(ImportJob)
    if status_filter:
        query = query.filter(ImportJob.status == status_filter)
    if search:
        like = f"%{search.lower()}%"
        query = query.filter(
            ImportJob.job_number.ilike(like)
            | ImportJob.container_number.ilike(like)
            | ImportJob.vessel_name.ilike(like)
            | ImportJob.consignee.ilike(like)
            | ImportJob.bl_number.ilike(like)
        )
    return query.order_by(ImportJob.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/jobs/{job_id}", response_model=ImportJobResponse)
def get_job(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return get_job_or_404(db, job_id)

@router.put("/jobs/{job_id}", response_model=ImportJobResponse)
def update_job(job_id: uuid.UUID, job_update: ImportJobUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    job = get_job_or_404(db, job_id)
    for key, value in job_update.model_dump(exclude_unset=True).items():
        setattr(job, key, value)
    db.commit()
    db.refresh(job)
    return job

@router.put("/jobs/{job_id}/approve", response_model=ImportJobResponse)
def approve_job(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    job = get_job_or_404(db, job_id)
    if job.status != "PENDING_APPROVAL":
        raise HTTPException(status_code=400, detail="Job is not pending approval")
    old_status = job.status
    job.status = "APPROVED"
    db.commit()
    db.refresh(job)
    log_activity(db, job_id, "APPROVE", "Job approved", old_status, "APPROVED", user.get("username"))
    return job

@router.put("/jobs/{job_id}/reject", response_model=ImportJobResponse)
def reject_job(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    job = get_job_or_404(db, job_id)
    old_status = job.status
    job.status = "REJECTED"
    db.commit()
    db.refresh(job)
    log_activity(db, job_id, "REJECT", "Job rejected", old_status, "REJECTED", user.get("username"))
    return job

@router.put("/jobs/{job_id}/assign-team", response_model=ImportJobResponse)
def assign_team(job_id: uuid.UUID, team: dict, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    job = get_job_or_404(db, job_id)
    old_status = job.status
    old_team = job.assigned_team
    job.assigned_team = team.get("team")
    job.status = "TEAM_ASSIGNED"
    db.commit()
    db.refresh(job)
    log_activity(db, job_id, "ASSIGN_TEAM", f"Team assigned: {team.get('team')}", old_team, team.get("team"), user.get("username"))
    return job

@router.put("/jobs/{job_id}/apply-license", response_model=ImportJobResponse)
def apply_license(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    job = get_job_or_404(db, job_id)
    old_status = job.status
    job.license_approved = True
    job.status = "LICENSE_APPROVED"
    db.commit()
    db.refresh(job)
    log_activity(db, job_id, "LICENSE", "License applied", old_status, "LICENSE_APPROVED", user.get("username"))
    return job

@router.put("/jobs/{job_id}/customs-permit", response_model=ImportJobResponse)
def submit_customs_permit(job_id: uuid.UUID, permit: dict, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    job = get_job_or_404(db, job_id)
    old_status = job.status
    job.customs_permit_status = permit.get("status", "SUBMITTED")
    job.status = "PERMIT_SUBMITTED"
    db.commit()
    db.refresh(job)
    log_activity(db, job_id, "CUSTOMS_PERMIT", f"Customs permit submitted: {permit.get('status')}", old_status, "PERMIT_SUBMITTED", user.get("username"))
    return job

@router.put("/jobs/{job_id}/truck", response_model=ImportJobResponse)
def assign_truck(job_id: uuid.UUID, assignment: TruckAssignment, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    job = get_job_or_404(db, job_id)
    old_status = job.status
    job.truck_id = assignment.truck_id
    job.trailer_id = assignment.trailer_id
    job.driver_id = assignment.driver_id
    job.is_outsourced = assignment.is_outsourced
    job.vendor_id = assignment.vendor_id
    job.status = "TRUCK_ASSIGNED"
    db.commit()
    db.refresh(job)
    log_activity(db, job_id, "TRUCK_ASSIGN", f"Truck assigned (outsourced: {assignment.is_outsourced})", old_status, "TRUCK_ASSIGNED", user.get("username"))
    return job

@router.put("/jobs/{job_id}/arrival", response_model=ImportJobResponse)
def record_arrival(job_id: uuid.UUID, arrival: VesselArrival, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    job = get_job_or_404(db, job_id)
    old_status = job.status
    job.ata = arrival.ata
    job.status = "VESSEL_ARRIVED"
    db.commit()
    db.refresh(job)
    log_activity(db, job_id, "VESSEL_ARRIVED", f"Vessel arrived: {arrival.ata}", old_status, "VESSEL_ARRIVED", user.get("username"))
    return job

@router.put("/jobs/{job_id}/clearance", response_model=ImportJobResponse)
def process_clearance(job_id: uuid.UUID, clearance: CustomsClearance, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    job = get_job_or_404(db, job_id)
    old_status = job.status
    job.customs_permit_status = clearance.customs_permit_status
    job.eir_number = clearance.eir_number
    job.status = "CUSTOMS_CLEARED"
    db.commit()
    db.refresh(job)
    log_activity(db, job_id, "CUSTOMS_CLEARANCE", f"Customs cleared: {clearance.customs_permit_status}", old_status, "CUSTOMS_CLEARED", user.get("username"))
    return job

@router.put("/jobs/{job_id}/pickup", response_model=ImportJobResponse)
def container_pickup(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    job = get_job_or_404(db, job_id)
    old_status = job.status
    job.status = "PICKED_UP"
    db.commit()
    db.refresh(job)
    log_activity(db, job_id, "PICKUP", "Container picked up", old_status, "PICKED_UP", user.get("username"))
    return job

@router.put("/jobs/{job_id}/deliver", response_model=ImportJobResponse)
def deliver(job_id: uuid.UUID, delivery: DeliveryUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    job = get_job_or_404(db, job_id)
    old_status = job.status
    job.delivery_location_id = delivery.delivery_location_id
    job.eir_number = delivery.eir_number
    job.status = "DELIVERED"
    db.commit()
    db.refresh(job)
    log_activity(db, job_id, "DELIVER", "Container delivered to customer", old_status, "DELIVERED", user.get("username"))
    return job

@router.put("/jobs/{job_id}/unload", response_model=ImportJobResponse)
def confirm_unload(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    job = get_job_or_404(db, job_id)
    old_status = job.status
    job.status = "UNLOADED"
    db.commit()
    db.refresh(job)
    log_activity(db, job_id, "UNLOAD", "Container unloaded", old_status, "UNLOADED", user.get("username"))
    return job

@router.put("/jobs/{job_id}/return-container", response_model=ImportJobResponse)
def return_container(job_id: uuid.UUID, eir: dict, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    job = get_job_or_404(db, job_id)
    old_status = job.status
    job.eir_number = eir.get("eir_number")
    job.status = "CONTAINER_RETURNED"
    db.commit()
    db.refresh(job)
    log_activity(db, job_id, "RETURN_CONTAINER", f"Container returned: {eir.get('eir_number')}", old_status, "CONTAINER_RETURNED", user.get("username"))
    return job

@router.put("/jobs/{job_id}/close", response_model=ImportJobResponse)
def close_job(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    job = get_job_or_404(db, job_id)
    old_status = job.status
    job.status = "CLOSED"
    db.commit()
    db.refresh(job)
    log_activity(db, job_id, "CLOSE", "Job closed", old_status, "CLOSED", user.get("username"))
    return job

@router.delete("/jobs/{job_id}")
def delete_job(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles("admin"))):
    job = get_job_or_404(db, job_id)
    db.delete(job)
    db.commit()
    return {"message": "Job deleted"}

# ---- Documents ----
@router.get("/jobs/{job_id}/documents", response_model=List[JobDocumentResponse])
def list_documents(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    get_job_or_404(db, job_id)
    return db.query(JobDocument).filter(JobDocument.job_id == job_id).order_by(JobDocument.created_at.desc()).all()

@router.post("/jobs/{job_id}/documents", response_model=JobDocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document(job_id: uuid.UUID, doc: JobDocumentCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    get_job_or_404(db, job_id)
    job_dir = os.path.join(UPLOAD_DIR, str(job_id))
    os.makedirs(job_dir, exist_ok=True)
    safe_name = os.path.basename(doc.filename)
    file_path = os.path.join(job_dir, safe_name)
    try:
        raw = base64.b64decode(doc.data_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 data")
    with open(file_path, "wb") as f:
        f.write(raw)
    db_doc = JobDocument(
        job_id=job_id,
        filename=safe_name,
        file_type=doc.file_type,
        file_size=len(raw),
        file_path=file_path,
        description=doc.description,
        uploaded_by=user.get("username"),
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    log_activity(db, job_id, "DOCUMENT_UPLOAD", f"Document uploaded: {safe_name}", None, safe_name, user.get("username"))
    return db_doc

@router.delete("/documents/{document_id}")
def delete_document(document_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    doc = db.query(JobDocument).filter(JobDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except OSError:
            pass
    db.delete(doc)
    db.commit()
    return {"message": "Document deleted"}

# ---- Job templates ----
@router.get("/templates", response_model=List[JobTemplateResponse])
def list_templates(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return db.query(JobTemplate).order_by(JobTemplate.created_at.desc()).offset(skip).limit(limit).all()

@router.post("/templates", response_model=JobTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(template: JobTemplateCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_template = JobTemplate(**template.model_dump(), created_by=user.get("username"))
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@router.put("/templates/{template_id}", response_model=JobTemplateResponse)
def update_template(template_id: uuid.UUID, template_update: JobTemplateUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    template = db.query(JobTemplate).filter(JobTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    for key, value in template_update.model_dump(exclude_unset=True).items():
        setattr(template, key, value)
    db.commit()
    db.refresh(template)
    return template

@router.delete("/templates/{template_id}")
def delete_template(template_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    template = db.query(JobTemplate).filter(JobTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(template)
    db.commit()
    return {"message": "Template deleted"}

# ---- Invoices ----
@router.get("/jobs/{job_id}/invoices", response_model=List[InvoiceResponse])
def list_job_invoices(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    get_job_or_404(db, job_id)
    return db.query(Invoice).filter(Invoice.job_id == job_id).order_by(Invoice.created_at.desc()).all()

@router.post("/jobs/{job_id}/invoices", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(job_id: uuid.UUID, invoice: InvoiceCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    job = get_job_or_404(db, job_id)
    db_invoice = Invoice(
        job_id=job_id,
        invoice_number=generate_invoice_number(),
        customer_name=invoice.customer_name or job.consignee,
        issue_date=invoice.issue_date or datetime.utcnow(),
        due_date=invoice.due_date,
        status=invoice.status,
        tax_rate=invoice.tax_rate,
        notes=invoice.notes,
        created_by=user.get("username"),
    )
    db.add(db_invoice)
    db.flush()
    for line in invoice.lines:
        amount = (line.quantity or Decimal("1")) * (line.unit_price or Decimal("0"))
        db.add(InvoiceLine(
            invoice_id=db_invoice.id,
            description=line.description,
            quantity=line.quantity,
            unit_price=line.unit_price,
            amount=amount,
            coa=line.coa,
        ))
    db.commit()
    recalculate_invoice(db, db_invoice)
    log_activity(db, job_id, "INVOICE_CREATE", f"Invoice {db_invoice.invoice_number} created", None, db_invoice.invoice_number, user.get("username"))
    return db_invoice

@router.get("/invoices", response_model=List[InvoiceResponse])
def list_invoices(skip: int = 0, limit: int = 100, status_filter: str = None, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    query = db.query(Invoice)
    if status_filter:
        query = query.filter(Invoice.status == status_filter)
    return query.order_by(Invoice.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(invoice_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@router.put("/invoices/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(invoice_id: uuid.UUID, invoice_update: InvoiceUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    for key, value in invoice_update.model_dump(exclude_unset=True).items():
        setattr(invoice, key, value)
    db.commit()
    recalculate_invoice(db, invoice)
    return invoice

@router.put("/invoices/{invoice_id}/status", response_model=InvoiceResponse)
def update_invoice_status(invoice_id: uuid.UUID, body: dict, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    new_status = body.get("status")
    if new_status not in ["DRAFT", "ISSUED", "PAID", "VOID"]:
        raise HTTPException(status_code=400, detail="Invalid invoice status")
    invoice.status = new_status
    db.commit()
    db.refresh(invoice)
    return invoice

@router.post("/invoices/{invoice_id}/lines", response_model=InvoiceResponse)
def add_invoice_line(invoice_id: uuid.UUID, line: InvoiceLineCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    amount = (line.quantity or Decimal("1")) * (line.unit_price or Decimal("0"))
    db.add(InvoiceLine(
        invoice_id=invoice_id,
        description=line.description,
        quantity=line.quantity,
        unit_price=line.unit_price,
        amount=amount,
        coa=line.coa,
    ))
    db.commit()
    recalculate_invoice(db, invoice)
    return invoice

@router.delete("/invoices/{invoice_id}/lines/{line_id}", response_model=InvoiceResponse)
def delete_invoice_line(invoice_id: uuid.UUID, line_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    line = db.query(InvoiceLine).filter(InvoiceLine.id == line_id, InvoiceLine.invoice_id == invoice_id).first()
    if not line:
        raise HTTPException(status_code=404, detail="Line not found")
    db.delete(line)
    db.commit()
    recalculate_invoice(db, invoice)
    return invoice

@router.delete("/invoices/{invoice_id}")
def delete_invoice(invoice_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    db.delete(invoice)
    db.commit()
    return {"message": "Invoice deleted"}
