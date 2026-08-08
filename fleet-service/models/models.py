import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from database.database import Base

class Truck(Base):
    __tablename__ = "trucks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plate_number = Column(String(50), unique=True, nullable=False, index=True)
    driver_name = Column(String(255))
    brand = Column(String(100))
    model = Column(String(100))
    year_of_manufacture = Column(Integer)
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Trailer(Base):
    __tablename__ = "trailers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trailer_number = Column(String(50), unique=True, nullable=False, index=True)
    trailer_size = Column(String(50))
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Driver(Base):
    __tablename__ = "drivers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    identification_card_number = Column(String(50), unique=True, nullable=False)
    ic_issued_date = Column(DateTime)
    ic_expired_date = Column(DateTime)
    company_ic_number = Column(String(50))
    company_ic_issued_date = Column(DateTime)
    company_ic_expired_date = Column(DateTime)
    driving_license_number = Column(String(50), unique=True, nullable=False)
    license_type = Column(String(50))
    license_issued_date = Column(DateTime)
    license_expired_date = Column(DateTime)
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
