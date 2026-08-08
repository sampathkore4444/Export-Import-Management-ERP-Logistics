import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from database.database import engine, Base
from routers.fleet import router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Fleet Service", version="1.0.0")

app.include_router(router)

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "fleet"}
