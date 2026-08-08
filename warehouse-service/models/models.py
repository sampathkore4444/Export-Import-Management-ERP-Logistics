import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from database.database import Base

class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    location = Column(String(255))
    manager = Column(String(255))
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    warehouse_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    sku = Column(String(100), index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    quantity = Column(Numeric(12, 2), default=0)
    unit = Column(String(50), default="unit")
    min_stock = Column(Numeric(12, 2), default=0)
    status = Column(String(50), default="IN_STOCK")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    warehouse_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    movement_type = Column(String(50), nullable=False)
    quantity = Column(Numeric(12, 2), nullable=False)
    reference_type = Column(String(100))
    reference_id = Column(UUID(as_uuid=True), nullable=True)
    notes = Column(String(255))
    created_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
