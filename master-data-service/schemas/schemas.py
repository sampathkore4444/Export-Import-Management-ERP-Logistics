from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal

class LocationBase(BaseModel):
    name: str
    coordinate_x: Optional[float] = None
    coordinate_y: Optional[float] = None

class LocationCreate(LocationBase):
    pass

class LocationResponse(LocationBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class LocationUpdate(BaseModel):
    name: Optional[str] = None
    coordinate_x: Optional[float] = None
    coordinate_y: Optional[float] = None

class VendorBase(BaseModel):
    name_kh: str
    name_eng: str
    address_1: Optional[str] = None
    contact_person_order: Optional[str] = None
    address_2: Optional[str] = None
    contact_person_complaint: Optional[str] = None
    tin: Optional[str] = None
    credit_term: Optional[int] = None
    credit_limit: Optional[Decimal] = None
    bank_name: Optional[str] = None
    account_name: Optional[str] = None
    account_number: Optional[str] = None

class VendorCreate(VendorBase):
    pass

class VendorUpdate(BaseModel):
    name_kh: Optional[str] = None
    name_eng: Optional[str] = None
    address_1: Optional[str] = None
    contact_person_order: Optional[str] = None
    address_2: Optional[str] = None
    contact_person_complaint: Optional[str] = None
    tin: Optional[str] = None
    credit_term: Optional[int] = None
    credit_limit: Optional[Decimal] = None
    bank_name: Optional[str] = None
    account_name: Optional[str] = None
    account_number: Optional[str] = None

class VendorResponse(VendorBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class CustomerBase(BaseModel):
    name_kh: str
    name_eng: str
    address_1: Optional[str] = None
    contact_person_order: Optional[str] = None
    address_2: Optional[str] = None
    contact_person_payment: Optional[str] = None
    tin: Optional[str] = None
    credit_term: Optional[int] = None
    credit_limit: Optional[Decimal] = None
    sales_person: Optional[str] = None
    bank_name: Optional[str] = None
    account_name: Optional[str] = None
    account_number: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name_kh: Optional[str] = None
    name_eng: Optional[str] = None
    address_1: Optional[str] = None
    contact_person_order: Optional[str] = None
    address_2: Optional[str] = None
    contact_person_payment: Optional[str] = None
    tin: Optional[str] = None
    credit_term: Optional[int] = None
    credit_limit: Optional[Decimal] = None
    sales_person: Optional[str] = None
    bank_name: Optional[str] = None
    account_name: Optional[str] = None
    account_number: Optional[str] = None

class CustomerResponse(CustomerBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class ItemBase(BaseModel):
    name: str
    type: str
    min_qty: Optional[Decimal] = None
    delivery_lead_time: Optional[int] = None
    purchase_coa: Optional[str] = None
    sale_coa: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    min_qty: Optional[Decimal] = None
    delivery_lead_time: Optional[int] = None
    purchase_coa: Optional[str] = None
    sale_coa: Optional[str] = None

class ItemResponse(ItemBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class CompanySettingsUpdate(BaseModel):
    company_name: Optional[str] = None
    company_name_kh: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    tax_id: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    logo_url: Optional[str] = None
