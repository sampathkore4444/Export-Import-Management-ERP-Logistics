import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.database import get_db
from database.security import get_current_user, require_roles
from models.models import (
    Quotation, QuotationLine, VendorBill, BillLine, JobCost, Payment, Invoice, InvoiceLine, ImportJob, ExportJob
)
from schemas.schemas import (
    QuotationCreate, QuotationUpdate, QuotationResponse, QuotationLineCreate,
    BillCreate, BillUpdate, BillResponse, BillLineCreate,
    JobCostCreate, JobCostUpdate, JobCostResponse,
    PaymentCreate, PaymentResponse,
    ProfitabilityResponse, FinanceAnalyticsResponse,
)

router = APIRouter(prefix="/api", tags=["finance"])

MANAGER_ROLES = ["admin", "manager"]

def generate_number(prefix):
    return f"{prefix}-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

def recalculate_quotation(db, quotation):
    subtotal = sum(
        (line.quantity or Decimal("0")) * (line.unit_price or Decimal("0"))
        for line in quotation.lines
    )
    quotation.subtotal = subtotal
    quotation.tax = (subtotal * quotation.tax_rate) / Decimal("100")
    quotation.total = quotation.subtotal + quotation.tax
    db.commit()
    db.refresh(quotation)
    return quotation

def recalculate_bill(db, bill):
    subtotal = sum(
        (line.quantity or Decimal("0")) * (line.unit_price or Decimal("0"))
        for line in bill.lines
    )
    bill.subtotal = subtotal
    bill.tax = (subtotal * bill.tax_rate) / Decimal("100")
    bill.total = bill.subtotal + bill.tax
    db.commit()
    db.refresh(bill)
    return bill

def apply_payment_status(db, invoice_id):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        return
    paid = sum(
        (p.amount or Decimal("0"))
        for p in db.query(Payment).filter(Payment.invoice_id == invoice_id).all()
    )
    if paid >= (invoice.total or Decimal("0")) and invoice.total > 0:
        invoice.status = "PAID"
    elif paid > 0:
        invoice.status = "PARTIAL"
    db.commit()
    db.refresh(invoice)

# ---- Quotations ----
@router.post("/quotations", response_model=QuotationResponse, status_code=status.HTTP_201_CREATED)
def create_quotation(quote: QuotationCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_quote = Quotation(
        quote_number=generate_number("QUO"),
        job_id=quote.job_id,
        job_type=quote.job_type,
        customer_name=quote.customer_name,
        issue_date=quote.issue_date or datetime.utcnow(),
        valid_until=quote.valid_until,
        status=quote.status,
        tax_rate=quote.tax_rate,
        notes=quote.notes,
        created_by=user.get("username"),
    )
    db.add(db_quote)
    db.flush()
    for line in quote.lines:
        amount = (line.quantity or Decimal("1")) * (line.unit_price or Decimal("0"))
        db.add(QuotationLine(
            quotation_id=db_quote.id,
            description=line.description,
            quantity=line.quantity,
            unit_price=line.unit_price,
            amount=amount,
            coa=line.coa,
        ))
    db.commit()
    recalculate_quotation(db, db_quote)
    return db_quote

@router.get("/quotations", response_model=List[QuotationResponse])
def list_quotations(skip: int = 0, limit: int = 100, status_filter: str = None, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    query = db.query(Quotation)
    if status_filter:
        query = query.filter(Quotation.status == status_filter)
    return query.order_by(Quotation.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/quotations/{quote_id}", response_model=QuotationResponse)
def get_quotation(quote_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    quote = db.query(Quotation).filter(Quotation.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quotation not found")
    return quote

@router.put("/quotations/{quote_id}", response_model=QuotationResponse)
def update_quotation(quote_id: uuid.UUID, quote_update: QuotationUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    quote = db.query(Quotation).filter(Quotation.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quotation not found")
    for key, value in quote_update.model_dump(exclude_unset=True).items():
        setattr(quote, key, value)
    db.commit()
    recalculate_quotation(db, quote)
    return quote

@router.post("/quotations/{quote_id}/lines", response_model=QuotationResponse)
def add_quotation_line(quote_id: uuid.UUID, line: QuotationLineCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    quote = db.query(Quotation).filter(Quotation.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quotation not found")
    amount = (line.quantity or Decimal("1")) * (line.unit_price or Decimal("0"))
    db.add(QuotationLine(
        quotation_id=quote_id,
        description=line.description,
        quantity=line.quantity,
        unit_price=line.unit_price,
        amount=amount,
        coa=line.coa,
    ))
    db.commit()
    recalculate_quotation(db, quote)
    return quote

@router.post("/quotations/{quote_id}/convert", response_model=QuotationResponse)
def convert_quotation(quote_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    quote = db.query(Quotation).filter(Quotation.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quotation not found")
    if quote.status == "CONVERTED":
        raise HTTPException(status_code=400, detail="Quotation already converted")
    if quote.job_id:
        job = db.query(ImportJob).filter(ImportJob.id == quote.job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Linked job not found")
        db_invoice = Invoice(
            job_id=job.id,
            invoice_number=generate_number("INV"),
            customer_name=quote.customer_name or job.consignee,
            issue_date=datetime.utcnow(),
            status="DRAFT",
            tax_rate=quote.tax_rate,
            notes=f"Converted from quotation {quote.quote_number}",
            created_by=user.get("username"),
        )
    else:
        db_invoice = Invoice(
            job_id=uuid.uuid4(),
            invoice_number=generate_number("INV"),
            customer_name=quote.customer_name,
            issue_date=datetime.utcnow(),
            status="DRAFT",
            tax_rate=quote.tax_rate,
            notes=f"Converted from quotation {quote.quote_number}",
            created_by=user.get("username"),
        )
    db.add(db_invoice)
    db.flush()
    for line in quote.lines:
        db.add(InvoiceLine(
            invoice_id=db_invoice.id,
            description=line.description,
            quantity=line.quantity,
            unit_price=line.unit_price,
            amount=line.amount,
            coa=line.coa,
        ))
    quote.status = "CONVERTED"
    db.commit()
    db.refresh(quote)
    return quote

@router.delete("/quotations/{quote_id}/lines/{line_id}", response_model=QuotationResponse)
def delete_quotation_line(quote_id: uuid.UUID, line_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    quote = db.query(Quotation).filter(Quotation.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quotation not found")
    line = db.query(QuotationLine).filter(QuotationLine.id == line_id, QuotationLine.quotation_id == quote_id).first()
    if not line:
        raise HTTPException(status_code=404, detail="Line not found")
    db.delete(line)
    db.commit()
    recalculate_quotation(db, quote)
    return quote

@router.delete("/quotations/{quote_id}")
def delete_quotation(quote_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    quote = db.query(Quotation).filter(Quotation.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quotation not found")
    db.delete(quote)
    db.commit()
    return {"message": "Quotation deleted"}

# ---- Vendor bills ----
@router.post("/bills", response_model=BillResponse, status_code=status.HTTP_201_CREATED)
def create_bill(bill: BillCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_bill = VendorBill(
        bill_number=generate_number("BILL"),
        job_id=bill.job_id,
        job_type=bill.job_type,
        vendor_id=bill.vendor_id,
        vendor_name=bill.vendor_name,
        bill_date=bill.bill_date or datetime.utcnow(),
        due_date=bill.due_date,
        status=bill.status,
        tax_rate=bill.tax_rate,
        notes=bill.notes,
        created_by=user.get("username"),
    )
    db.add(db_bill)
    db.flush()
    for line in bill.lines:
        amount = (line.quantity or Decimal("1")) * (line.unit_price or Decimal("0"))
        db.add(BillLine(
            bill_id=db_bill.id,
            description=line.description,
            quantity=line.quantity,
            unit_price=line.unit_price,
            amount=amount,
            coa=line.coa,
        ))
    db.commit()
    recalculate_bill(db, db_bill)
    return db_bill

@router.get("/bills", response_model=List[BillResponse])
def list_bills(skip: int = 0, limit: int = 100, status_filter: str = None, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    query = db.query(VendorBill)
    if status_filter:
        query = query.filter(VendorBill.status == status_filter)
    return query.order_by(VendorBill.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/bills/{bill_id}", response_model=BillResponse)
def get_bill(bill_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    bill = db.query(VendorBill).filter(VendorBill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return bill

@router.put("/bills/{bill_id}", response_model=BillResponse)
def update_bill(bill_id: uuid.UUID, bill_update: BillUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    bill = db.query(VendorBill).filter(VendorBill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    for key, value in bill_update.model_dump(exclude_unset=True).items():
        setattr(bill, key, value)
    db.commit()
    recalculate_bill(db, bill)
    return bill

@router.post("/bills/{bill_id}/lines", response_model=BillResponse)
def add_bill_line(bill_id: uuid.UUID, line: BillLineCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    bill = db.query(VendorBill).filter(VendorBill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    amount = (line.quantity or Decimal("1")) * (line.unit_price or Decimal("0"))
    db.add(BillLine(
        bill_id=bill_id,
        description=line.description,
        quantity=line.quantity,
        unit_price=line.unit_price,
        amount=amount,
        coa=line.coa,
    ))
    db.commit()
    recalculate_bill(db, bill)
    return bill

@router.delete("/bills/{bill_id}/lines/{line_id}", response_model=BillResponse)
def delete_bill_line(bill_id: uuid.UUID, line_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    bill = db.query(VendorBill).filter(VendorBill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    line = db.query(BillLine).filter(BillLine.id == line_id, BillLine.bill_id == bill_id).first()
    if not line:
        raise HTTPException(status_code=404, detail="Line not found")
    db.delete(line)
    db.commit()
    recalculate_bill(db, bill)
    return bill

@router.delete("/bills/{bill_id}")
def delete_bill(bill_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    bill = db.query(VendorBill).filter(VendorBill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    db.delete(bill)
    db.commit()
    return {"message": "Bill deleted"}

# ---- Job costs ----
@router.get("/jobs/{job_id}/costs", response_model=List[JobCostResponse])
def list_job_costs(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return db.query(JobCost).filter(JobCost.job_id == job_id).order_by(JobCost.created_at.desc()).all()

@router.post("/jobs/{job_id}/costs", response_model=JobCostResponse, status_code=status.HTTP_201_CREATED)
def create_job_cost(job_id: uuid.UUID, cost: JobCostCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_cost = JobCost(
        job_id=job_id,
        job_type="import",
        cost_type=cost.cost_type,
        description=cost.description,
        amount=cost.amount,
        vendor_id=cost.vendor_id,
        bill_id=cost.bill_id,
        created_by=user.get("username"),
    )
    db.add(db_cost)
    db.commit()
    db.refresh(db_cost)
    return db_cost

@router.put("/jobs/{job_id}/costs/{cost_id}", response_model=JobCostResponse)
def update_job_cost(job_id: uuid.UUID, cost_id: uuid.UUID, cost_update: JobCostUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    cost = db.query(JobCost).filter(JobCost.id == cost_id, JobCost.job_id == job_id).first()
    if not cost:
        raise HTTPException(status_code=404, detail="Cost not found")
    for key, value in cost_update.model_dump(exclude_unset=True).items():
        setattr(cost, key, value)
    db.commit()
    db.refresh(cost)
    return cost

@router.delete("/jobs/{job_id}/costs/{cost_id}")
def delete_job_cost(job_id: uuid.UUID, cost_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    cost = db.query(JobCost).filter(JobCost.id == cost_id, JobCost.job_id == job_id).first()
    if not cost:
        raise HTTPException(status_code=404, detail="Cost not found")
    db.delete(cost)
    db.commit()
    return {"message": "Cost deleted"}

@router.get("/exports/{job_id}/costs", response_model=List[JobCostResponse])
def list_export_job_costs(job_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return db.query(JobCost).filter(JobCost.job_id == job_id).order_by(JobCost.created_at.desc()).all()

@router.post("/exports/{job_id}/costs", response_model=JobCostResponse, status_code=status.HTTP_201_CREATED)
def create_export_job_cost(job_id: uuid.UUID, cost: JobCostCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    db_cost = JobCost(
        job_id=job_id,
        job_type="export",
        cost_type=cost.cost_type,
        description=cost.description,
        amount=cost.amount,
        vendor_id=cost.vendor_id,
        bill_id=cost.bill_id,
        created_by=user.get("username"),
    )
    db.add(db_cost)
    db.commit()
    db.refresh(db_cost)
    return db_cost

# ---- Payments ----
@router.get("/invoices/{invoice_id}/payments", response_model=List[PaymentResponse])
def list_invoice_payments(invoice_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return db.query(Payment).filter(Payment.invoice_id == invoice_id).order_by(Payment.created_at.desc()).all()

@router.post("/payments", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(payment: PaymentCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    invoice = db.query(Invoice).filter(Invoice.id == payment.invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    db_payment = Payment(
        invoice_id=payment.invoice_id,
        amount=payment.amount,
        payment_date=payment.payment_date or datetime.utcnow(),
        method=payment.method,
        reference=payment.reference,
        created_by=user.get("username"),
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    apply_payment_status(db, invoice.id)
    return db_payment

@router.delete("/payments/{payment_id}")
def delete_payment(payment_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    invoice_id = payment.invoice_id
    db.delete(payment)
    db.commit()
    apply_payment_status(db, invoice_id)
    return {"message": "Payment deleted"}

# ---- Profitability ----
@router.get("/finance/profit/{job_id}", response_model=ProfitabilityResponse)
def job_profitability(job_id: uuid.UUID, job_type: str = "import", db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    invoices = db.query(Invoice).filter(Invoice.job_id == job_id).all()
    revenue = sum((i.total or Decimal("0")) for i in invoices)
    costs = sum(
        (c.amount or Decimal("0"))
        for c in db.query(JobCost).filter(JobCost.job_id == job_id).all()
    )
    profit = revenue - costs
    margin = float(profit / revenue) * 100 if revenue else 0.0
    return ProfitabilityResponse(job_id=job_id, job_type=job_type, revenue=revenue, costs=costs, profit=profit, margin=round(margin, 2))

@router.get("/finance/analytics", response_model=FinanceAnalyticsResponse)
def finance_analytics(days: int = 30, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    cutoff = datetime.utcnow() - timedelta(days=days)
    invoices = db.query(Invoice).filter(Invoice.created_at >= cutoff).all()
    revenue = sum((i.total or Decimal("0")) for i in invoices)
    costs = db.query(JobCost).filter(JobCost.created_at >= cutoff).all()
    expenses = sum((c.amount or Decimal("0")) for c in costs)
    outstanding = sum(
        (i.total or Decimal("0"))
        for i in db.query(Invoice).filter(Invoice.status.in_(["ISSUED", "PARTIAL"])).all()
    )
    unpaid_bills = sum(
        (b.total or Decimal("0"))
        for b in db.query(VendorBill).filter(VendorBill.status.in_(["UNPAID", "PARTIAL"])).all()
    )
    cust = defaultdict(lambda: {"revenue": Decimal("0"), "cost": Decimal("0"), "invoices": 0})
    costs_by_job = defaultdict(lambda: Decimal("0"))
    for c in db.query(JobCost).all():
        costs_by_job[str(c.job_id)] += c.amount or Decimal("0")
    for i in db.query(Invoice).all():
        name = i.customer_name or "Unknown"
        cust[name]["revenue"] += i.total or Decimal("0")
        cust[name]["invoices"] += 1
        if i.job_id:
            cust[name]["cost"] += costs_by_job.get(str(i.job_id), Decimal("0"))
    top_customers = [
        {
            "customer": name,
            "revenue": float(data["revenue"]),
            "cost": float(data["cost"]),
            "profit": float(data["revenue"] - data["cost"]),
            "invoices": data["invoices"],
        }
        for name, data in sorted(cust.items(), key=lambda kv: kv[1]["revenue"], reverse=True)[:10]
    ]
    return FinanceAnalyticsResponse(
        revenue_30d=revenue,
        expenses_30d=expenses,
        profit_30d=revenue - expenses,
        outstanding_invoices=outstanding,
        unpaid_bills=unpaid_bills,
        invoices_issued=len(invoices),
        bills_received=len(db.query(VendorBill).filter(VendorBill.created_at >= cutoff).all()),
        top_customers=top_customers,
    )
