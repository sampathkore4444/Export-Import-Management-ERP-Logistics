import base64
import os
import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.database import get_db
from database.security import get_current_user, require_roles
from models.models import ExportJob, ExportActivityLog, ExportDocument
from schemas.schemas import (
    ExportJobCreate, ExportJobUpdate, ExportJobResponse,
    ExportTruckAssignment, ExportDeparture, ExportClearance, ExportGateIn,
    ExportActivityLogResponse,
    ExportDocumentCreate, ExportDocumentResponse,
)

router = APIRouter(prefix="/api", tags=["exports"])

MANAGER_ROLES = ["admin", "manager"]
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", "exports")

def generate_export_job_number():
    return f"EXP-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

def log_export_activity(db, job_id, action, description, old_value=None, new_value=None, performed_by=None):
    activity = ExportActivityLog(
        job_id=job_id,
        action=action,
        description=description,
        old_value=old_value,
        new_value=new_value,
        performed_by=performed_by
    )
    db.add(activity)
    db.commit()

def get_export_or_404(db, job_id):
    job = db.query(ExportJob).filter(ExportJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")
    return job

# ---- Activity logs ----
@router.get("/exports/activities", response_model=List[ExportActivityLogResponse])
def list_export_activities(job_id: uuid.UUID = None, skip: int = 0, limit: int = 50, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    query = db.query(ExportActivityLog)
    if job_id:
        query = query.filter(ExportActivityLog.job_id == job_id)
    return query.order_by(ExportActivityLog.created_at.desc()).offset(skip).limit(limit).all()

# ---- Export jobs ----
@router.post("/exports", response_model=ExportJobResponse, status_code=status.HTTP_201_CREATED)
def create_export_job(job: ExportJobCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_job = ExportJob(
        job_number=generate_export_job_number(),
        created_by=uuid.UUID(user.get("user_id")) if user.get("user_id") else None,
        **job.model_dump()
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    log_export_activity(db, db_job.id, "CREATE", "Export job created", None, "PENDING_APPROVAL", user.get("username"))
    return db_job

@router.get("/exports", response_model=List[ExportJobResponse])
def list_exports(skip: int = 0, limit: int = 100, status_filter: str = None, search: str = None, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    query = db.query(ExportJob)
    if status_filter:
        query = query.filter(ExportJob.status == status_filter)
    if search:
        like = f"%{search.lower()}%"
        query = query.filter(
            ExportJob.job_number.ilike(like)
            | ExportJob.container_number.ilike(like)
            | ExportJob.vessel_name.ilike(like)
            | ExportJob.shipper.ilike(like)
            | ExportJob.consignee.ilike(like)
            | ExportJob.bl_number.ilike(like)
        )
    return query.order_by(ExportJob.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/exports/{job_id}", response_model=ExportJobResponse)
def get_export_job(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return get_export_or_404(db, job_id)

@router.put("/exports/{job_id}", response_model=ExportJobResponse)
def update_export_job(job_id: uuid.UUID, job_update: ExportJobUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    job = get_export_or_404(db, job_id)
    for key, value in job_update.model_dump(exclude_unset=True).items():
        setattr(job, key, value)
    db.commit()
    db.refresh(job)
    return job

@router.put("/exports/{job_id}/approve", response_model=ExportJobResponse)
def approve_export_job(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    job = get_export_or_404(db, job_id)
    if job.status != "PENDING_APPROVAL":
        raise HTTPException(status_code=400, detail="Export job is not pending approval")
    old_status = job.status
    job.status = "APPROVED"
    db.commit()
    db.refresh(job)
    log_export_activity(db, job_id, "APPROVE", "Export job approved", old_status, "APPROVED", user.get("username"))
    return job

@router.put("/exports/{job_id}/reject", response_model=ExportJobResponse)
def reject_export_job(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    job = get_export_or_404(db, job_id)
    old_status = job.status
    job.status = "REJECTED"
    db.commit()
    db.refresh(job)
    log_export_activity(db, job_id, "REJECT", "Export job rejected", old_status, "REJECTED", user.get("username"))
    return job

@router.put("/exports/{job_id}/assign-team", response_model=ExportJobResponse)
def assign_export_team(job_id: uuid.UUID, team: dict, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    job = get_export_or_404(db, job_id)
    old_status = job.status
    old_team = job.assigned_team
    job.assigned_team = team.get("team")
    job.status = "TEAM_ASSIGNED"
    db.commit()
    db.refresh(job)
    log_export_activity(db, job_id, "ASSIGN_TEAM", f"Team assigned: {team.get('team')}", old_team, team.get("team"), user.get("username"))
    return job

@router.put("/exports/{job_id}/apply-license", response_model=ExportJobResponse)
def apply_export_license(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    job = get_export_or_404(db, job_id)
    job.license_approved = True
    db.commit()
    db.refresh(job)
    log_export_activity(db, job_id, "LICENSE", "Export license applied", None, "APPROVED", user.get("username"))
    return job

@router.put("/exports/{job_id}/customs-permit", response_model=ExportJobResponse)
def submit_export_customs_permit(job_id: uuid.UUID, permit: dict, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    job = get_export_or_404(db, job_id)
    old_status = job.status
    job.customs_permit_status = permit.get("status", "SUBMITTED")
    job.status = "PERMIT_SUBMITTED"
    db.commit()
    db.refresh(job)
    log_export_activity(db, job_id, "CUSTOMS_PERMIT", f"Export customs permit submitted: {permit.get('status')}", old_status, "PERMIT_SUBMITTED", user.get("username"))
    return job

@router.put("/exports/{job_id}/truck", response_model=ExportJobResponse)
def assign_export_truck(job_id: uuid.UUID, assignment: ExportTruckAssignment, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    job = get_export_or_404(db, job_id)
    old_status = job.status
    job.truck_id = assignment.truck_id
    job.trailer_id = assignment.trailer_id
    job.driver_id = assignment.driver_id
    job.is_outsourced = assignment.is_outsourced
    job.vendor_id = assignment.vendor_id
    job.status = "TRUCK_ASSIGNED"
    db.commit()
    db.refresh(job)
    log_export_activity(db, job_id, "TRUCK_ASSIGN", f"Truck assigned (outsourced: {assignment.is_outsourced})", old_status, "TRUCK_ASSIGNED", user.get("username"))
    return job

@router.put("/exports/{job_id}/empty-pickup", response_model=ExportJobResponse)
def record_empty_pickup(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    job = get_export_or_404(db, job_id)
    old_status = job.status
    job.empty_pickup_date = datetime.utcnow()
    job.status = "EMPTY_PICKED_UP"
    db.commit()
    db.refresh(job)
    log_export_activity(db, job_id, "EMPTY_PICKUP", "Empty container picked up for stuffing", old_status, "EMPTY_PICKED_UP", user.get("username"))
    return job

@router.put("/exports/{job_id}/stuff", response_model=ExportJobResponse)
def confirm_stuffing(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    job = get_export_or_404(db, job_id)
    old_status = job.status
    job.status = "STUFFED"
    db.commit()
    db.refresh(job)
    log_export_activity(db, job_id, "STUFFING", "Container stuffed at shipper", old_status, "STUFFED", user.get("username"))
    return job

@router.put("/exports/{job_id}/gate-in", response_model=ExportJobResponse)
def record_gate_in(job_id: uuid.UUID, gate: ExportGateIn, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    job = get_export_or_404(db, job_id)
    old_status = job.status
    job.gate_in_date = datetime.utcnow()
    job.eir_number = gate.eir_number or f"EIR-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    job.status = "GATE_IN"
    db.commit()
    db.refresh(job)
    log_export_activity(db, job_id, "GATE_IN", f"Container gated into port (EIR: {job.eir_number})", old_status, "GATE_IN", user.get("username"))
    return job

@router.put("/exports/{job_id}/departure", response_model=ExportJobResponse)
def record_departure(job_id: uuid.UUID, departure: ExportDeparture, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    job = get_export_or_404(db, job_id)
    old_status = job.status
    job.atd = departure.atd
    job.status = "VESSEL_DEPARTED"
    db.commit()
    db.refresh(job)
    log_export_activity(db, job_id, "VESSEL_DEPARTED", f"Vessel departed: {departure.atd}", old_status, "VESSEL_DEPARTED", user.get("username"))
    return job

@router.put("/exports/{job_id}/clearance", response_model=ExportJobResponse)
def process_export_clearance(job_id: uuid.UUID, clearance: ExportClearance, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    job = get_export_or_404(db, job_id)
    old_status = job.status
    job.customs_permit_status = clearance.customs_permit_status
    job.status = "EXPORT_CLEARED"
    db.commit()
    db.refresh(job)
    log_export_activity(db, job_id, "EXPORT_CLEARANCE", f"Export customs cleared: {clearance.customs_permit_status}", old_status, "EXPORT_CLEARED", user.get("username"))
    return job

@router.put("/exports/{job_id}/close", response_model=ExportJobResponse)
def close_export_job(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    job = get_export_or_404(db, job_id)
    old_status = job.status
    job.status = "CLOSED"
    db.commit()
    db.refresh(job)
    log_export_activity(db, job_id, "CLOSE", "Export job closed", old_status, "CLOSED", user.get("username"))
    return job

@router.delete("/exports/{job_id}")
def delete_export_job(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles("admin"))):
    job = get_export_or_404(db, job_id)
    db.delete(job)
    db.commit()
    return {"message": "Export job deleted"}

# ---- Export documents ----
@router.get("/exports/{job_id}/documents", response_model=List[ExportDocumentResponse])
def list_export_documents(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    get_export_or_404(db, job_id)
    return db.query(ExportDocument).filter(ExportDocument.job_id == job_id).order_by(ExportDocument.created_at.desc()).all()

@router.post("/exports/{job_id}/documents", response_model=ExportDocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_export_document(job_id: uuid.UUID, doc: ExportDocumentCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    get_export_or_404(db, job_id)
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
    db_doc = ExportDocument(
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
    log_export_activity(db, job_id, "DOCUMENT_UPLOAD", f"Document uploaded: {safe_name}", None, safe_name, user.get("username"))
    return db_doc

@router.delete("/export-documents/{document_id}")
def delete_export_document(document_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    doc = db.query(ExportDocument).filter(ExportDocument.id == document_id).first()
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
