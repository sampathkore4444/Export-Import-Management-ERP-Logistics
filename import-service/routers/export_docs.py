import uuid
from datetime import datetime
from decimal import Decimal
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.database import get_db
from database.security import get_current_user, require_roles
from models.models import ExportJob, ExportCommercialInvoice, ExportCommercialInvoiceLine, ExportPackingList, ExportPackingListLine
from schemas.schemas import (
    CommercialInvoiceCreate, CommercialInvoiceUpdate, CommercialInvoiceResponse,
    CommercialInvoiceLineCreate, CommercialInvoiceLineResponse,
    PackingListCreate, PackingListUpdate, PackingListResponse,
    PackingListLineCreate, PackingListLineResponse,
)

router = APIRouter(prefix="/api", tags=["export-docs"])

MANAGER_ROLES = ["admin", "manager"]

def get_export_or_404(db, job_id):
    job = db.query(ExportJob).filter(ExportJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")
    return job

def generate_ci_number():
    return f"CI-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

def generate_pl_number():
    return f"PL-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

def recalculate_ci(db, ci):
    subtotal = sum(
        (line.quantity or Decimal("0")) * (line.unit_price or Decimal("0"))
        for line in ci.lines
    )
    ci.subtotal = subtotal
    ci.tax = Decimal("0")
    ci.total = ci.subtotal + ci.tax
    db.commit()
    db.refresh(ci)
    return ci

# ---- Commercial invoices ----
@router.post("/exports/{job_id}/commercial-invoice", response_model=CommercialInvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_commercial_invoice(job_id: uuid.UUID, ci: CommercialInvoiceCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    job = get_export_or_404(db, job_id)
    db_ci = ExportCommercialInvoice(
        export_job_id=job_id,
        invoice_no=ci.invoice_no or generate_ci_number(),
        date=ci.date or datetime.utcnow(),
        terms=ci.terms,
        shipper=ci.shipper or job.shipper,
        consignee=ci.consignee or job.consignee,
    )
    db.add(db_ci)
    db.flush()
    for line in ci.lines:
        amount = (line.quantity or Decimal("0")) * (line.unit_price or Decimal("0"))
        db.add(ExportCommercialInvoiceLine(
            ci_id=db_ci.id,
            description=line.description,
            quantity=line.quantity,
            unit_price=line.unit_price,
            amount=amount,
            hs_code=line.hs_code,
        ))
    db.commit()
    recalculate_ci(db, db_ci)
    return db_ci

@router.get("/exports/{job_id}/commercial-invoice", response_model=CommercialInvoiceResponse)
def get_commercial_invoice(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    get_export_or_404(db, job_id)
    ci = db.query(ExportCommercialInvoice).filter(ExportCommercialInvoice.export_job_id == job_id).first()
    if not ci:
        raise HTTPException(status_code=404, detail="Commercial invoice not found for this job")
    return ci

@router.put("/exports/{job_id}/commercial-invoice", response_model=CommercialInvoiceResponse)
def update_commercial_invoice(job_id: uuid.UUID, ci_update: CommercialInvoiceUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    get_export_or_404(db, job_id)
    ci = db.query(ExportCommercialInvoice).filter(ExportCommercialInvoice.export_job_id == job_id).first()
    if not ci:
        raise HTTPException(status_code=404, detail="Commercial invoice not found for this job")
    for key, value in ci_update.model_dump(exclude_unset=True).items():
        setattr(ci, key, value)
    db.commit()
    db.refresh(ci)
    return ci

@router.post("/exports/{job_id}/commercial-invoice/lines", response_model=CommercialInvoiceResponse)
def add_commercial_invoice_line(job_id: uuid.UUID, line: CommercialInvoiceLineCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    get_export_or_404(db, job_id)
    ci = db.query(ExportCommercialInvoice).filter(ExportCommercialInvoice.export_job_id == job_id).first()
    if not ci:
        raise HTTPException(status_code=404, detail="Commercial invoice not found for this job")
    amount = (line.quantity or Decimal("0")) * (line.unit_price or Decimal("0"))
    db.add(ExportCommercialInvoiceLine(
        ci_id=ci.id,
        description=line.description,
        quantity=line.quantity,
        unit_price=line.unit_price,
        amount=amount,
        hs_code=line.hs_code,
    ))
    db.commit()
    recalculate_ci(db, ci)
    return ci

@router.delete("/exports/{job_id}/commercial-invoice/lines/{line_id}", response_model=CommercialInvoiceResponse)
def delete_commercial_invoice_line(job_id: uuid.UUID, line_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    get_export_or_404(db, job_id)
    ci = db.query(ExportCommercialInvoice).filter(ExportCommercialInvoice.export_job_id == job_id).first()
    if not ci:
        raise HTTPException(status_code=404, detail="Commercial invoice not found for this job")
    line = db.query(ExportCommercialInvoiceLine).filter(ExportCommercialInvoiceLine.id == line_id, ExportCommercialInvoiceLine.ci_id == ci.id).first()
    if not line:
        raise HTTPException(status_code=404, detail="Line not found")
    db.delete(line)
    db.commit()
    recalculate_ci(db, ci)
    return ci

@router.delete("/exports/{job_id}/commercial-invoice")
def delete_commercial_invoice(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    get_export_or_404(db, job_id)
    ci = db.query(ExportCommercialInvoice).filter(ExportCommercialInvoice.export_job_id == job_id).first()
    if not ci:
        raise HTTPException(status_code=404, detail="Commercial invoice not found for this job")
    db.delete(ci)
    db.commit()
    return {"message": "Commercial invoice deleted"}

# ---- Packing lists ----
@router.post("/exports/{job_id}/packing-list", response_model=PackingListResponse, status_code=status.HTTP_201_CREATED)
def create_packing_list(job_id: uuid.UUID, pl: PackingListCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    job = get_export_or_404(db, job_id)
    db_pl = ExportPackingList(
        export_job_id=job_id,
        pl_no=pl.pl_no or generate_pl_number(),
        date=pl.date or datetime.utcnow(),
        shipper=pl.shipper or job.shipper,
        consignee=pl.consignee or job.consignee,
    )
    db.add(db_pl)
    db.flush()
    for line in pl.lines:
        db.add(ExportPackingListLine(
            pl_id=db_pl.id,
            description=line.description,
            quantity=line.quantity,
            units=line.units,
            gross_weight=line.gross_weight,
            net_weight=line.net_weight,
            dimensions=line.dimensions,
            marks=line.marks,
        ))
    db.commit()
    db.refresh(db_pl)
    return db_pl

@router.get("/exports/{job_id}/packing-list", response_model=PackingListResponse)
def get_packing_list(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    get_export_or_404(db, job_id)
    pl = db.query(ExportPackingList).filter(ExportPackingList.export_job_id == job_id).first()
    if not pl:
        raise HTTPException(status_code=404, detail="Packing list not found for this job")
    return pl

@router.put("/exports/{job_id}/packing-list", response_model=PackingListResponse)
def update_packing_list(job_id: uuid.UUID, pl_update: PackingListUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    get_export_or_404(db, job_id)
    pl = db.query(ExportPackingList).filter(ExportPackingList.export_job_id == job_id).first()
    if not pl:
        raise HTTPException(status_code=404, detail="Packing list not found for this job")
    for key, value in pl_update.model_dump(exclude_unset=True).items():
        setattr(pl, key, value)
    db.commit()
    db.refresh(pl)
    return pl

@router.post("/exports/{job_id}/packing-list/lines", response_model=PackingListResponse)
def add_packing_list_line(job_id: uuid.UUID, line: PackingListLineCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    get_export_or_404(db, job_id)
    pl = db.query(ExportPackingList).filter(ExportPackingList.export_job_id == job_id).first()
    if not pl:
        raise HTTPException(status_code=404, detail="Packing list not found for this job")
    db.add(ExportPackingListLine(
        pl_id=pl.id,
        description=line.description,
        quantity=line.quantity,
        units=line.units,
        gross_weight=line.gross_weight,
        net_weight=line.net_weight,
        dimensions=line.dimensions,
        marks=line.marks,
    ))
    db.commit()
    db.refresh(pl)
    return pl

@router.delete("/exports/{job_id}/packing-list/lines/{line_id}", response_model=PackingListResponse)
def delete_packing_list_line(job_id: uuid.UUID, line_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    get_export_or_404(db, job_id)
    pl = db.query(ExportPackingList).filter(ExportPackingList.export_job_id == job_id).first()
    if not pl:
        raise HTTPException(status_code=404, detail="Packing list not found for this job")
    line = db.query(ExportPackingListLine).filter(ExportPackingListLine.id == line_id, ExportPackingListLine.pl_id == pl.id).first()
    if not line:
        raise HTTPException(status_code=404, detail="Line not found")
    db.delete(line)
    db.commit()
    db.refresh(pl)
    return pl

@router.delete("/exports/{job_id}/packing-list")
def delete_packing_list(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    get_export_or_404(db, job_id)
    pl = db.query(ExportPackingList).filter(ExportPackingList.export_job_id == job_id).first()
    if not pl:
        raise HTTPException(status_code=404, detail="Packing list not found for this job")
    db.delete(pl)
    db.commit()
    return {"message": "Packing list deleted"}
