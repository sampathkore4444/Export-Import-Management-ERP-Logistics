import uuid
from decimal import Decimal
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.database import get_db
from database.security import get_current_user, require_roles
from models.models import Warehouse, InventoryItem, StockMovement
from schemas.schemas import (
    WarehouseCreate, WarehouseUpdate, WarehouseResponse,
    InventoryItemCreate, InventoryItemUpdate, InventoryItemResponse,
    StockMovementCreate, StockMovementResponse,
    InventorySummaryResponse,
)

router = APIRouter(prefix="/api", tags=["warehouse"])

MANAGER_ROLES = ["admin", "manager"]

def get_warehouse_or_404(db, warehouse_id):
    warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return warehouse

def get_item_or_404(db, item_id):
    item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return item

def refresh_item_status(db, item):
    qty = item.quantity or Decimal("0")
    min_stock = item.min_stock or Decimal("0")
    if qty <= 0:
        item.status = "OUT_OF_STOCK"
    elif qty <= min_stock:
        item.status = "LOW_STOCK"
    else:
        item.status = "IN_STOCK"
    db.commit()
    db.refresh(item)
    return item

# ---- Warehouses ----
@router.post("/warehouses", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
def create_warehouse(warehouse: WarehouseCreate, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    existing = db.query(Warehouse).filter(Warehouse.code == warehouse.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Warehouse code already exists")
    db_warehouse = Warehouse(**warehouse.model_dump())
    db.add(db_warehouse)
    db.commit()
    db.refresh(db_warehouse)
    return db_warehouse

@router.get("/warehouses", response_model=List[WarehouseResponse])
def list_warehouses(skip: int = 0, limit: int = 100, search: str = None, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    query = db.query(Warehouse)
    if search:
        like = f"%{search.lower()}%"
        query = query.filter(Warehouse.name.ilike(like) | Warehouse.code.ilike(like) | Warehouse.location.ilike(like))
    return query.order_by(Warehouse.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
def get_warehouse(warehouse_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return get_warehouse_or_404(db, warehouse_id)

@router.put("/warehouses/{warehouse_id}", response_model=WarehouseResponse)
def update_warehouse(warehouse_id: uuid.UUID, warehouse_update: WarehouseUpdate, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    warehouse = get_warehouse_or_404(db, warehouse_id)
    for key, value in warehouse_update.model_dump(exclude_unset=True).items():
        setattr(warehouse, key, value)
    db.commit()
    db.refresh(warehouse)
    return warehouse

@router.delete("/warehouses/{warehouse_id}")
def delete_warehouse(warehouse_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    warehouse = get_warehouse_or_404(db, warehouse_id)
    db.delete(warehouse)
    db.commit()
    return {"message": "Warehouse deleted"}

# ---- Inventory ----
@router.post("/inventory", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED)
def create_inventory_item(item: InventoryItemCreate, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    get_warehouse_or_404(db, item.warehouse_id)
    db_item = InventoryItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    refresh_item_status(db, db_item)
    if (db_item.quantity or Decimal("0")) > 0:
        db.add(StockMovement(
            item_id=db_item.id,
            warehouse_id=db_item.warehouse_id,
            movement_type="IN",
            quantity=db_item.quantity,
            notes="Initial stock",
            created_by=user.get("username"),
        ))
        db.commit()
    return db_item

@router.get("/inventory", response_model=List[InventoryItemResponse])
def list_inventory(warehouse_id: uuid.UUID = None, status_filter: str = None, search: str = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    query = db.query(InventoryItem)
    if warehouse_id:
        query = query.filter(InventoryItem.warehouse_id == warehouse_id)
    if status_filter:
        query = query.filter(InventoryItem.status == status_filter)
    if search:
        like = f"%{search.lower()}%"
        query = query.filter(InventoryItem.name.ilike(like) | InventoryItem.sku.ilike(like) | InventoryItem.category.ilike(like))
    return query.order_by(InventoryItem.updated_at.desc()).offset(skip).limit(limit).all()

@router.get("/inventory/{item_id}", response_model=InventoryItemResponse)
def get_inventory_item(item_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return get_item_or_404(db, item_id)

@router.put("/inventory/{item_id}", response_model=InventoryItemResponse)
def update_inventory_item(item_id: uuid.UUID, item_update: InventoryItemUpdate, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    item = get_item_or_404(db, item_id)
    for key, value in item_update.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    refresh_item_status(db, item)
    return item

@router.delete("/inventory/{item_id}")
def delete_inventory_item(item_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    item = get_item_or_404(db, item_id)
    db.delete(item)
    db.commit()
    return {"message": "Inventory item deleted"}

# ---- Stock movements ----
@router.post("/inventory/{item_id}/movements", response_model=StockMovementResponse, status_code=status.HTTP_201_CREATED)
def record_stock_movement(item_id: uuid.UUID, movement: StockMovementCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    item = get_item_or_404(db, item_id)
    if movement.warehouse_id != item.warehouse_id:
        get_warehouse_or_404(db, movement.warehouse_id)
    qty = movement.quantity or Decimal("0")
    if movement.movement_type.upper() in ("OUT", "ISSUE", "SOLD"):
        if item.quantity is None or item.quantity < qty:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        item.quantity -= qty
    else:
        item.quantity = (item.quantity or Decimal("0")) + qty
    db_movement = StockMovement(
        item_id=item_id,
        warehouse_id=movement.warehouse_id or item.warehouse_id,
        movement_type=movement.movement_type.upper(),
        quantity=qty,
        reference_type=movement.reference_type,
        reference_id=movement.reference_id,
        notes=movement.notes,
        created_by=user.get("username"),
    )
    db.add(db_movement)
    db.commit()
    db.refresh(db_movement)
    refresh_item_status(db, item)
    return db_movement

@router.get("/inventory/{item_id}/movements", response_model=List[StockMovementResponse])
def list_item_movements(item_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    get_item_or_404(db, item_id)
    return db.query(StockMovement).filter(StockMovement.item_id == item_id).order_by(StockMovement.created_at.desc()).all()

# ---- Summary ----
@router.get("/inventory/summary", response_model=InventorySummaryResponse)
def inventory_summary(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    items = db.query(InventoryItem).all()
    total_quantity = sum(float(i.quantity or 0) for i in items)
    low_stock = sum(1 for i in items if i.status == "LOW_STOCK")
    out_of_stock = sum(1 for i in items if i.status == "OUT_OF_STOCK")
    return InventorySummaryResponse(
        total_items=len(items),
        total_quantity=total_quantity,
        low_stock_items=low_stock,
        out_of_stock_items=out_of_stock,
        warehouses=db.query(Warehouse).count(),
    )
