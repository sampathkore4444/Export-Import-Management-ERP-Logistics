import base64
import os
import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.database import get_db
from database.security import get_current_user, require_roles
from models.models import AirJob, AirActivityLog, AirDocument
from schemas.schemas import (
    AirJobCreate, AirJobUpdate, AirJobResponse,
    AirDeparture, AirArrival,
    AirActivityLogResponse,
    AirDocumentCreate, AirDocumentResponse,
)

router = APIRouter(prefix="/api", tags=["air"])

MANAGER_ROLES = ["admin", "manager"]
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", "air")

def generate_air_job_number():
    return f"AIR-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

def log_air_activity(db, job_id, action, description, old_value=None, new_value=None, performed_by=None):
    activity = AirActivityLog(
        job_id=job_id,
        action=action,
        description=description,
        old_value=old_value,
        new_value=new_value,
        performed_by=performed_by,
    )
    db.add(activity)
    db.commit()

def get_air_or_404(db, job_id):
    job = db.query(AirJob).filter(AirJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Air job not found")
    return job

# ---- Air jobs ----
@router.post("/air", response_model=AirJobResponse, status_code=status.HTTP_201_CREATED)
def create_air_job(job: AirJobCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_job = AirJob(
        job_number=generate_air_job_number(),
        created_by=uuid.UUID(user.get("user_id")) if user.get("user_id") else None,
        **job.model_dump()
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    log_air_activity(db, db_job.id, "CREATE", "Air job created", None, "PENDING_APPROVAL", user.get("username"))
    return db_job

@router.get("/air", response_model=List[AirJobResponse])
def list_air_jobs(skip: int = 0, limit: int = 100, status_filter: str = None, search: str = None, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    query = db.query(AirJob)
    if status_filter:
        query = query.filter(AirJob.status == status_filter)
    if search:
        like = f"%{search.lower()}%"
        query = query.filter(
            AirJob.job_number.ilike(like)
            | AirJob.awb_number.ilike(like)
            | AirJob.hawb_number.ilike(like)
            | AirJob.carrier.ilike(like)
            | AirJob.origin.ilike(like)
            | AirJob.destination.ilike(like)
            | AirJob.shipper.ilike(like)
            | AirJob.consignee.ilike(like)
        )
    return query.order_by(AirJob.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/air/activities", response_model=List[AirActivityLogResponse])
def list_air_activities(job_id: uuid.UUID = None, skip: int = 0, limit: int = 50, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    query = db.query(AirActivityLog)
    if job_id:
        query = query.filter(AirActivityLog.job_id == job_id)
    return query.order_by(AirActivityLog.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/air/{job_id}", response_model=AirJobResponse)
def get_air_job(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return get_air_or_404(db, job_id)

@router.put("/air/{job_id}", response_model=AirJobResponse)
def update_air_job(job_id: uuid.UUID, job_update: AirJobUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    job = get_air_or_404(db, job_id)
    for key, value in job_update.model_dump(exclude_unset=True).items():
        setattr(job, key, value)
    db.commit()
    db.refresh(job)
    return job

@router.put("/air/{job_id}/approve", response_model=AirJobResponse)
def approve_air_job(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    job = get_air_or_404(db, job_id)
    if job.status != "PENDING_APPROVAL":
        raise HTTPException(status_code=400, detail="Air job is not pending approval")
    old_status = job.status
    job.status = "APPROVED"
    db.commit()
    db.refresh(job)
    log_air_activity(db, job_id, "APPROVE", "Air job approved", old_status, "APPROVED", user.get("username"))
    return job

@router.put("/air/{job_id}/reject", response_model=AirJobResponse)
def reject_air_job(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    job = get_air_or_404(db, job_id)
    old_status = job.status
    job.status = "REJECTED"
    db.commit()
    db.refresh(job)
    log_air_activity(db, job_id, "REJECT", "Air job rejected", old_status, "REJECTED", user.get("username"))
    return job

@router.put("/air/{job_id}/assign-team", response_model=AirJobResponse)
def assign_air_team(job_id: uuid.UUID, team: dict, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    job = get_air_or_404(db, job_id)
    old_status = job.status
    old_team = job.assigned_team
    job.assigned_team = team.get("team")
    job.status = "TEAM_ASSIGNED"
    db.commit()
    db.refresh(job)
    log_air_activity(db, job_id, "ASSIGN_TEAM", f"Team assigned: {team.get('team')}", old_team, team.get("team"), user.get("username"))
    return job

@router.put("/air/{job_id}/apply-license", response_model=AirJobResponse)
def apply_air_license(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    job = get_air_or_404(db, job_id)
    job.license_approved = True
    db.commit()
    db.refresh(job)
    log_air_activity(db, job_id, "LICENSE", "Air export license applied", None, "APPROVED", user.get("username"))
    return job

@router.put("/air/{job_id}/customs-permit", response_model=AirJobResponse)
def submit_air_customs_permit(job_id: uuid.UUID, permit: dict, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    job = get_air_or_404(db, job_id)
    old_status = job.status
    job.customs_permit_status = permit.get("status", "SUBMITTED")
    job.status = "PERMIT_SUBMITTED"
    db.commit()
    db.refresh(job)
    log_air_activity(db, job_id, "CUSTOMS_PERMIT", f"Air customs permit submitted: {permit.get('status')}", old_status, "PERMIT_SUBMITTED", user.get("username"))
    return job

@router.put("/air/{job_id}/departure", response_model=AirJobResponse)
def record_air_departure(job_id: uuid.UUID, departure: AirDeparture, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    job = get_air_or_404(db, job_id)
    old_status = job.status
    job.atd = departure.atd
    job.status = "FLIGHT_DEPARTED"
    db.commit()
    db.refresh(job)
    log_air_activity(db, job_id, "FLIGHT_DEPARTED", f"Flight departed: {departure.atd}", old_status, "FLIGHT_DEPARTED", user.get("username"))
    return job

@router.put("/air/{job_id}/arrival", response_model=AirJobResponse)
def record_air_arrival(job_id: uuid.UUID, arrival: AirArrival, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    job = get_air_or_404(db, job_id)
    old_status = job.status
    job.ata = arrival.ata
    job.status = "FLIGHT_ARRIVED"
    db.commit()
    db.refresh(job)
    log_air_activity(db, job_id, "FLIGHT_ARRIVED", f"Flight arrived: {arrival.ata}", old_status, "FLIGHT_ARRIVED", user.get("username"))
    return job

@router.put("/air/{job_id}/close", response_model=AirJobResponse)
def close_air_job(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    job = get_air_or_404(db, job_id)
    old_status = job.status
    job.status = "CLOSED"
    db.commit()
    db.refresh(job)
    log_air_activity(db, job_id, "CLOSE", "Air job closed", old_status, "CLOSED", user.get("username"))
    return job

@router.delete("/air/{job_id}")
def delete_air_job(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles("admin"))):
    job = get_air_or_404(db, job_id)
    db.delete(job)
    db.commit()
    return {"message": "Air job deleted"}

# ---- Air documents ----
@router.get("/air/{job_id}/documents", response_model=List[AirDocumentResponse])
def list_air_documents(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    get_air_or_404(db, job_id)
    return db.query(AirDocument).filter(AirDocument.job_id == job_id).order_by(AirDocument.created_at.desc()).all()

@router.post("/air/{job_id}/documents", response_model=AirDocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_air_document(job_id: uuid.UUID, doc: AirDocumentCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    get_air_or_404(db, job_id)
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
    db_doc = AirDocument(
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
    log_air_activity(db, job_id, "DOCUMENT_UPLOAD", f"Document uploaded: {safe_name}", None, safe_name, user.get("username"))
    return db_doc

@router.delete("/air-documents/{document_id}")
def delete_air_document(document_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    doc = db.query(AirDocument).filter(AirDocument.id == document_id).first()
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
