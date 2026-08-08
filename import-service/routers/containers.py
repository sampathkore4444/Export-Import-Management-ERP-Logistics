import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.database import get_db
from database.security import get_current_user, require_roles
from models.models import Container, ContainerEvent
from schemas.schemas import (
    ContainerCreate, ContainerUpdate, ContainerResponse,
    ContainerEventCreate, ContainerEventResponse,
)

router = APIRouter(prefix="/api", tags=["containers"])

MANAGER_ROLES = ["admin", "manager"]

def get_container_or_404(db, container_id):
    container = db.query(Container).filter(Container.id == container_id).first()
    if not container:
        raise HTTPException(status_code=404, detail="Container not found")
    return container

def log_container_event(db, container_id, event_type, description, job_id=None, job_type=None):
    event = ContainerEvent(
        container_id=container_id,
        event_type=event_type,
        event_date=datetime.utcnow(),
        job_id=job_id,
        job_type=job_type,
        description=description,
    )
    db.add(event)
    container = db.query(Container).filter(Container.id == container_id).first()
    if container:
        container.last_event_at = datetime.utcnow()
    db.commit()

@router.post("/containers", response_model=ContainerResponse, status_code=status.HTTP_201_CREATED)
def create_container(container: ContainerCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    existing = db.query(Container).filter(Container.container_number == container.container_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Container number already exists")
    db_container = Container(
        container_number=container.container_number,
        size=container.size,
        type=container.type,
        status=container.status,
        current_location_id=container.current_location_id,
    )
    db.add(db_container)
    db.commit()
    db.refresh(db_container)
    log_container_event(db, db_container.id, "CREATED", "Container registered", None, None)
    return db_container

@router.get("/containers", response_model=List[ContainerResponse])
def list_containers(status_filter: str = None, search: str = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    query = db.query(Container)
    if status_filter:
        query = query.filter(Container.status == status_filter)
    if search:
        like = f"%{search.lower()}%"
        query = query.filter(Container.container_number.ilike(like))
    return query.order_by(Container.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/containers/in-transit", response_model=List[ContainerResponse])
def list_in_transit_containers(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return db.query(Container).filter(Container.status.in_(["LOADED", "IN_TRANSIT", "ARRIVED"])).all()

@router.get("/containers/{container_id}", response_model=ContainerResponse)
def get_container(container_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    return get_container_or_404(db, container_id)

@router.put("/containers/{container_id}", response_model=ContainerResponse)
def update_container(container_id: uuid.UUID, container_update: ContainerUpdate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    container = get_container_or_404(db, container_id)
    old_status = container.status
    for key, value in container_update.model_dump(exclude_unset=True).items():
        setattr(container, key, value)
    db.commit()
    db.refresh(container)
    if container_update.status and container_update.status != old_status:
        log_container_event(db, container_id, f"STATUS_{container_update.status}", f"Status changed from {old_status} to {container_update.status}", None, None)
    return container

@router.post("/containers/{container_id}/events", response_model=ContainerEventResponse, status_code=status.HTTP_201_CREATED)
def add_container_event(container_id: uuid.UUID, event: ContainerEventCreate, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    get_container_or_404(db, container_id)
    db_event = ContainerEvent(
        container_id=container_id,
        event_type=event.event_type,
        event_date=event.event_date or datetime.utcnow(),
        job_id=event.job_id,
        job_type=event.job_type,
        description=event.description,
    )
    db.add(db_event)
    container = get_container_or_404(db, container_id)
    container.last_event_at = db_event.event_date
    db.commit()
    db.refresh(db_event)
    return db_event

@router.get("/containers/{container_id}/events", response_model=List[ContainerEventResponse])
def list_container_events(container_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    get_container_or_404(db, container_id)
    return db.query(ContainerEvent).filter(ContainerEvent.container_id == container_id).order_by(ContainerEvent.event_date.desc()).all()

@router.delete("/containers/{container_id}")
def delete_container(container_id: uuid.UUID, db: Session = Depends(get_db), user: dict = Depends(require_roles(*MANAGER_ROLES))):
    container = get_container_or_404(db, container_id)
    db.delete(container)
    db.commit()
    return {"message": "Container deleted"}
