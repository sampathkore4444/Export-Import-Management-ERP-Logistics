import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.database import get_db
from database.security import get_current_user, require_roles
from models.models import Location, Vendor, Customer, Item, CompanySetting
from schemas.schemas import (
    LocationCreate, LocationUpdate, LocationResponse,
    VendorCreate, VendorUpdate, VendorResponse,
    CustomerCreate, CustomerUpdate, CustomerResponse,
    ItemCreate, ItemUpdate, ItemResponse,
    CompanySettingsUpdate
)

router = APIRouter(prefix="/api", tags=["master-data"])

MANAGER_ROLES = ["admin", "manager"]
SETTING_KEYS = [
    "company_name", "company_name_kh", "address", "phone",
    "email", "tax_id", "bank_name", "bank_account", "logo_url"
]
DEFAULT_SETTINGS = {
    "company_name": "CargoFlow Import Management",
    "company_name_kh": "",
    "address": "",
    "phone": "",
    "email": "",
    "tax_id": "",
    "bank_name": "",
    "bank_account": "",
    "logo_url": "",
}

# Location endpoints
@router.post("/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
def create_location(location: LocationCreate, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    db_location = Location(**location.model_dump())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

@router.get("/locations", response_model=List[LocationResponse])
def list_locations(skip: int = 0, limit: int = 100, search: str = None, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    query = db.query(Location)
    if search:
        query = query.filter(Location.name.ilike(f"%{search.lower()}%"))
    return query.offset(skip).limit(limit).all()

@router.get("/locations/{location_id}", response_model=LocationResponse)
def get_location(location_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location

@router.put("/locations/{location_id}", response_model=LocationResponse)
def update_location(location_id: uuid.UUID, location_update: LocationUpdate, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    for key, value in location_update.model_dump(exclude_unset=True).items():
        setattr(location, key, value)
    db.commit()
    db.refresh(location)
    return location

@router.delete("/locations/{location_id}")
def delete_location(location_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    db.delete(location)
    db.commit()
    return {"message": "Location deleted"}

# Vendor endpoints
@router.post("/vendors", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
def create_vendor(vendor: VendorCreate, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    db_vendor = Vendor(**vendor.model_dump())
    db.add(db_vendor)
    db.commit()
    db.refresh(db_vendor)
    return db_vendor

@router.get("/vendors", response_model=List[VendorResponse])
def list_vendors(skip: int = 0, limit: int = 100, search: str = None, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    query = db.query(Vendor)
    if search:
        like = f"%{search.lower()}%"
        query = query.filter(Vendor.name_eng.ilike(like) | Vendor.name_kh.ilike(like))
    return query.offset(skip).limit(limit).all()

@router.get("/vendors/{vendor_id}", response_model=VendorResponse)
def get_vendor(vendor_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor

@router.put("/vendors/{vendor_id}", response_model=VendorResponse)
def update_vendor(vendor_id: uuid.UUID, vendor_update: VendorUpdate, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    for key, value in vendor_update.model_dump(exclude_unset=True).items():
        setattr(vendor, key, value)
    db.commit()
    db.refresh(vendor)
    return vendor

@router.delete("/vendors/{vendor_id}")
def delete_vendor(vendor_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    db.delete(vendor)
    db.commit()
    return {"message": "Vendor deleted"}

# Customer endpoints
@router.post("/customers", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(customer: CustomerCreate, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    db_customer = Customer(**customer.model_dump())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

@router.get("/customers", response_model=List[CustomerResponse])
def list_customers(skip: int = 0, limit: int = 100, search: str = None, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    query = db.query(Customer)
    if search:
        like = f"%{search.lower()}%"
        query = query.filter(Customer.name_eng.ilike(like) | Customer.name_kh.ilike(like))
    return query.offset(skip).limit(limit).all()

@router.get("/customers/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@router.put("/customers/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: uuid.UUID, customer_update: CustomerUpdate, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    for key, value in customer_update.model_dump(exclude_unset=True).items():
        setattr(customer, key, value)
    db.commit()
    db.refresh(customer)
    return customer

@router.delete("/customers/{customer_id}")
def delete_customer(customer_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    db.delete(customer)
    db.commit()
    return {"message": "Customer deleted"}

# Item endpoints
@router.post("/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(item: ItemCreate, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    db_item = Item(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.get("/items", response_model=List[ItemResponse])
def list_items(skip: int = 0, limit: int = 100, search: str = None, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    query = db.query(Item)
    if search:
        query = query.filter(Item.name.ilike(f"%{search.lower()}%"))
    return query.offset(skip).limit(limit).all()

@router.get("/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.put("/items/{item_id}", response_model=ItemResponse)
def update_item(item_id: uuid.UUID, item_update: ItemUpdate, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    for key, value in item_update.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item

@router.delete("/items/{item_id}")
def delete_item(item_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"message": "Item deleted"}

# Company settings endpoints
@router.get("/settings")
def get_settings(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    stored = {s.key: s.value for s in db.query(CompanySetting).all()}
    result = dict(DEFAULT_SETTINGS)
    result.update(stored)
    return result

@router.put("/settings")
def update_settings(settings_update: CompanySettingsUpdate, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    data = settings_update.model_dump(exclude_unset=True)
    for key, value in data.items():
        if key not in SETTING_KEYS:
            continue
        setting = db.query(CompanySetting).filter(CompanySetting.key == key).first()
        if setting:
            setting.value = str(value) if value is not None else ""
        else:
            db.add(CompanySetting(key=key, value=str(value) if value is not None else ""))
    db.commit()
    stored = {s.key: s.value for s in db.query(CompanySetting).all()}
    result = dict(DEFAULT_SETTINGS)
    result.update(stored)
    return result
