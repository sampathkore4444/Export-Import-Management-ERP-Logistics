import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from database.database import Base

class Location(Base):
    __tablename__ = "locations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    coordinate_x = Column(Float)
    coordinate_y = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Vendor(Base):
    __tablename__ = "vendors"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_kh = Column(String(255), nullable=False)
    name_eng = Column(String(255), nullable=False)
    address_1 = Column(String(255))
    contact_person_order = Column(String(255))
    address_2 = Column(String(255))
    contact_person_complaint = Column(String(255))
    tin = Column(String(50))
    credit_term = Column(Integer)
    credit_limit = Column(Numeric(12, 2))
    bank_name = Column(String(255))
    account_name = Column(String(255))
    account_number = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Customer(Base):
    __tablename__ = "customers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_kh = Column(String(255), nullable=False)
    name_eng = Column(String(255), nullable=False)
    address_1 = Column(String(255))
    contact_person_order = Column(String(255))
    address_2 = Column(String(255))
    contact_person_payment = Column(String(255))
    tin = Column(String(50))
    credit_term = Column(Integer)
    credit_limit = Column(Numeric(12, 2))
    sales_person = Column(String(255))
    bank_name = Column(String(255))
    account_name = Column(String(255))
    account_number = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Item(Base):
    __tablename__ = "items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    min_qty = Column(Numeric(12, 2))
    delivery_lead_time = Column(Integer)
    purchase_coa = Column(String(50))
    sale_coa = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CompanySetting(Base):
    __tablename__ = "company_settings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
