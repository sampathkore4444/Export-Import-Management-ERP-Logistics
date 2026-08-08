import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.database import get_db
from database.security import get_current_user, require_roles
from models.models import Truck, Trailer, Driver
from schemas.schemas import (
    TruckCreate, TruckUpdate, TruckResponse,
    TrailerCreate, TrailerUpdate, TrailerResponse,
    DriverCreate, DriverUpdate, DriverResponse
)

router = APIRouter(prefix="/api", tags=["fleet"])

MANAGER_ROLES = ["admin", "manager"]

# Truck endpoints
@router.post("/trucks", response_model=TruckResponse, status_code=status.HTTP_201_CREATED)
def create_truck(truck: TruckCreate, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    db_truck = Truck(**truck.model_dump())
    db.add(db_truck)
    db.commit()
    db.refresh(db_truck)
    return db_truck

@router.get("/trucks", response_model=List[TruckResponse])
def list_trucks(skip: int = 0, limit: int = 100, search: str = None, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    query = db.query(Truck)
    if search:
        like = f"%{search.lower()}%"
        query = query.filter(Truck.plate_number.ilike(like) | Truck.driver_name.ilike(like))
    return query.offset(skip).limit(limit).all()

@router.get("/trucks/{truck_id}", response_model=TruckResponse)
def get_truck(truck_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    truck = db.query(Truck).filter(Truck.id == truck_id).first()
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    return truck

@router.put("/trucks/{truck_id}", response_model=TruckResponse)
def update_truck(truck_id: uuid.UUID, truck_update: TruckUpdate, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    truck = db.query(Truck).filter(Truck.id == truck_id).first()
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    for key, value in truck_update.model_dump(exclude_unset=True).items():
        setattr(truck, key, value)
    db.commit()
    db.refresh(truck)
    return truck

@router.delete("/trucks/{truck_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_truck(truck_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    truck = db.query(Truck).filter(Truck.id == truck_id).first()
    if not truck:
        raise HTTPException(status_code=404, detail="Truck not found")
    db.delete(truck)
    db.commit()

# Trailer endpoints
@router.post("/trailers", response_model=TrailerResponse, status_code=status.HTTP_201_CREATED)
def create_trailer(trailer: TrailerCreate, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    db_trailer = Trailer(**trailer.model_dump())
    db.add(db_trailer)
    db.commit()
    db.refresh(db_trailer)
    return db_trailer

@router.get("/trailers", response_model=List[TrailerResponse])
def list_trailers(skip: int = 0, limit: int = 100, search: str = None, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    query = db.query(Trailer)
    if search:
        like = f"%{search.lower()}%"
        query = query.filter(Trailer.trailer_number.ilike(like))
    return query.offset(skip).limit(limit).all()

@router.get("/trailers/{trailer_id}", response_model=TrailerResponse)
def get_trailer(trailer_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    trailer = db.query(Trailer).filter(Trailer.id == trailer_id).first()
    if not trailer:
        raise HTTPException(status_code=404, detail="Trailer not found")
    return trailer

@router.put("/trailers/{trailer_id}", response_model=TrailerResponse)
def update_trailer(trailer_id: uuid.UUID, trailer_update: TrailerUpdate, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    trailer = db.query(Trailer).filter(Trailer.id == trailer_id).first()
    if not trailer:
        raise HTTPException(status_code=404, detail="Trailer not found")
    for key, value in trailer_update.model_dump(exclude_unset=True).items():
        setattr(trailer, key, value)
    db.commit()
    db.refresh(trailer)
    return trailer

@router.delete("/trailers/{trailer_id}")
def delete_trailer(trailer_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    trailer = db.query(Trailer).filter(Trailer.id == trailer_id).first()
    if not trailer:
        raise HTTPException(status_code=404, detail="Trailer not found")
    db.delete(trailer)
    db.commit()
    return {"message": "Trailer deleted"}

# Driver endpoints
@router.post("/drivers", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
def create_driver(driver: DriverCreate, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    db_driver = Driver(**driver.model_dump())
    db.add(db_driver)
    db.commit()
    db.refresh(db_driver)
    return db_driver

@router.get("/drivers", response_model=List[DriverResponse])
def list_drivers(skip: int = 0, limit: int = 100, search: str = None, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    query = db.query(Driver)
    if search:
        like = f"%{search.lower()}%"
        query = query.filter(Driver.identification_card_number.ilike(like) | Driver.driving_license_number.ilike(like))
    return query.offset(skip).limit(limit).all()

@router.get("/drivers/{driver_id}", response_model=DriverResponse)
def get_driver(driver_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver

@router.put("/drivers/{driver_id}", response_model=DriverResponse)
def update_driver(driver_id: uuid.UUID, driver_update: DriverUpdate, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    for key, value in driver_update.model_dump(exclude_unset=True).items():
        setattr(driver, key, value)
    db.commit()
    db.refresh(driver)
    return driver

@router.delete("/drivers/{driver_id}")
def delete_driver(driver_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    db.delete(driver)
    db.commit()
    return {"message": "Driver deleted"}
