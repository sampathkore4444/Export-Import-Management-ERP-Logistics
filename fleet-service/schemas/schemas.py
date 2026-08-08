from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class TruckBase(BaseModel):
    plate_number: str
    driver_name: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    year_of_manufacture: Optional[int] = None

class TruckCreate(TruckBase):
    pass

class TruckUpdate(BaseModel):
    plate_number: Optional[str] = None
    driver_name: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    year_of_manufacture: Optional[int] = None
    status: Optional[str] = None

class TruckResponse(TruckBase):
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TrailerBase(BaseModel):
    trailer_number: str
    trailer_size: Optional[str] = None

class TrailerCreate(TrailerBase):
    pass

class TrailerUpdate(BaseModel):
    trailer_number: Optional[str] = None
    trailer_size: Optional[str] = None
    status: Optional[str] = None

class TrailerResponse(TrailerBase):
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DriverBase(BaseModel):
    identification_card_number: str
    ic_issued_date: Optional[datetime] = None
    ic_expired_date: Optional[datetime] = None
    company_ic_number: Optional[str] = None
    company_ic_issued_date: Optional[datetime] = None
    company_ic_expired_date: Optional[datetime] = None
    driving_license_number: str
    license_type: Optional[str] = None
    license_issued_date: Optional[datetime] = None
    license_expired_date: Optional[datetime] = None

class DriverCreate(DriverBase):
    pass

class DriverUpdate(BaseModel):
    identification_card_number: Optional[str] = None
    ic_issued_date: Optional[datetime] = None
    ic_expired_date: Optional[datetime] = None
    company_ic_number: Optional[str] = None
    company_ic_issued_date: Optional[datetime] = None
    company_ic_expired_date: Optional[datetime] = None
    driving_license_number: Optional[str] = None
    license_type: Optional[str] = None
    license_issued_date: Optional[datetime] = None
    license_expired_date: Optional[datetime] = None
    status: Optional[str] = None

class DriverResponse(DriverBase):
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
