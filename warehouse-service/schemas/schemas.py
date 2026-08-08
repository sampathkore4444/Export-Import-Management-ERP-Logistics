from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal

class WarehouseBase(BaseModel):
    name: str
    code: str
    location: Optional[str] = None
    manager: Optional[str] = None

class WarehouseCreate(WarehouseBase):
    pass

class WarehouseUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    location: Optional[str] = None
    manager: Optional[str] = None
    status: Optional[str] = None

class WarehouseResponse(WarehouseBase):
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class InventoryItemBase(BaseModel):
    sku: Optional[str] = None
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    quantity: Decimal = Decimal("0")
    unit: str = "unit"
    min_stock: Decimal = Decimal("0")

class InventoryItemCreate(InventoryItemBase):
    warehouse_id: UUID

class InventoryItemUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit: Optional[str] = None
    min_stock: Optional[Decimal] = None
    status: Optional[str] = None

class InventoryItemResponse(InventoryItemBase):
    id: UUID
    warehouse_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class StockMovementCreate(BaseModel):
    item_id: UUID
    warehouse_id: UUID
    movement_type: str
    quantity: Decimal
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None
    notes: Optional[str] = None

class StockMovementResponse(BaseModel):
    id: UUID
    item_id: UUID
    warehouse_id: UUID
    movement_type: str
    quantity: Decimal
    reference_type: Optional[str]
    reference_id: Optional[UUID]
    notes: Optional[str]
    created_by: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class InventorySummaryResponse(BaseModel):
    total_items: int
    total_quantity: float
    low_stock_items: int
    out_of_stock_items: int
    warehouses: int
