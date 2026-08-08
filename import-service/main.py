import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from sqlalchemy import text
from database.database import engine, Base
from routers.jobs import router
from routers.exports import router as exports_router

Base.metadata.create_all(bind=engine)

def run_migrations():
    try:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE import_jobs ADD COLUMN IF NOT EXISTS trailer_id UUID"))
    except Exception as e:
        print(f"[migration] Warning: could not apply trailer_id column: {e}")

run_migrations()

app = FastAPI(title="Import Service", version="1.0.0")

app.include_router(router)
app.include_router(exports_router)

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "import"}
